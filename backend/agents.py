import os
import sys
import math
import json
import re
import logging
import urllib.request
import urllib.error
from typing import Tuple, Dict, Any, Optional, List

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from models import (
    Product, DemandForecast, ComboPlan, CreativeAssets, ROIMetrics,
    StoreProfile, PromotionVariety, ChatQuery, ChatResponse, RegionalFestivalEvent
)
from mock_data import AFFINITY_MATRIX, DEMAND_FORECASTS, CATEGORY_BRAND_COMPARISONS
from storage import StoreDataManager, DualModeStorageAdapter
from forecasting import OpenSourceForecastingEngine, PriceElasticityOptimizer, InvestmentROIEngine

logger = logging.getLogger("PromoMind.Agents")


class GeminiLiveClient:
    """
    Universal Live Gemini API Client for Search-Time Generation.
    Supports:
    1. Google AI Studio API Keys (`AIza...`) via `generativelanguage.googleapis.com`
    2. Vertex AI Express API Keys (`AQ....`) via `aiplatform.googleapis.com` & `google-genai` SDK
    3. Google Cloud Service Account JSON (`FIRESTORE_SA_JSON` or `GOOGLE_APPLICATION_CREDENTIALS`) via Vertex AI
    4. Runtime API Key overrides from UI / HTTP headers
    """

    _RUNTIME_API_KEY: Optional[str] = None
    _RUNTIME_MODEL: Optional[str] = None
    _LAST_USED_SOURCE: str = "UNINITIALIZED"
    _WORKING_MODEL: Optional[str] = None

    VALID_MODELS = [
        "gemini-2.5-flash",
        "gemini-2.5-flash-lite",
        "gemini-2.0-flash",
        "gemini-1.5-flash",
    ]

    @classmethod
    def set_runtime_api_key(cls, api_key: str, model: Optional[str] = None):
        if api_key and api_key.strip():
            cls._RUNTIME_API_KEY = api_key.strip()
            os.environ["GEMINI_API_KEY"] = cls._RUNTIME_API_KEY
            cls._WORKING_MODEL = None
        if model and model.strip():
            cls._RUNTIME_MODEL = model.strip()
            os.environ["GEMINI_MODEL"] = cls._RUNTIME_MODEL
            cls._WORKING_MODEL = None

    @classmethod
    def get_active_api_key(cls, override_key: Optional[str] = None) -> Optional[str]:
        key = override_key or cls._RUNTIME_API_KEY or os.environ.get("GEMINI_API_KEY")
        if key:
            key = key.strip().strip('"').strip("'")
            if key and key != "your_gemini_api_key_here":
                return key
        return None

    @classmethod
    def is_configured(cls, override_key: Optional[str] = None) -> bool:
        if cls.get_active_api_key(override_key):
            return True
        if os.environ.get("FIRESTORE_SA_JSON") or os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
            return True
        return False

    @classmethod
    def _get_candidate_models(cls) -> List[str]:
        if cls._WORKING_MODEL:
            return [cls._WORKING_MODEL]
        env_model = (cls._RUNTIME_MODEL or os.environ.get("GEMINI_MODEL") or "").strip()
        normalized_env = env_model
        if "3.5-flash-lite" in env_model or "3-flash-lite" in env_model:
            normalized_env = "gemini-2.5-flash-lite"
        elif "3.5-flash" in env_model or "3-flash" in env_model:
            normalized_env = "gemini-2.5-flash"
        elif "3.5-pro" in env_model:
            normalized_env = "gemini-1.5-pro"

        candidates = []
        if normalized_env:
            candidates.append(normalized_env)
        for m in cls.VALID_MODELS:
            if m not in candidates:
                candidates.append(m)
        return candidates

    @staticmethod
    def _clean_json_text(raw_text: str) -> Any:
        text = raw_text.strip()
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
        try:
            return json.loads(text)
        except Exception:
            arr_match = re.search(r"(\[[\s\S]*\])", text)
            obj_match = re.search(r"(\{[\s\S]*\})", text)
            if arr_match and (not obj_match or arr_match.start() < obj_match.start()):
                return json.loads(arr_match.group(1))
            if obj_match:
                return json.loads(obj_match.group(1))
            raise

    @classmethod
    def generate_json(
        cls,
        prompt: str,
        override_api_key: Optional[str] = None,
        timeout: int = 6
    ) -> Optional[Any]:
        """
        Executes a live Gemini API call and parses the JSON response.
        Automatically tries:
        1. google-genai SDK Client (Vertex AI for `AQ.` keys, AI Studio for `AIza...` keys)
        2. Vertex AI Express / Google AI Studio REST endpoints with smart fast-fail on network/auth errors
        3. Service Account JSON (`FIRESTORE_SA_JSON` / `GOOGLE_APPLICATION_CREDENTIALS`) via Vertex AI
        """
        api_key = cls.get_active_api_key(override_api_key)
        candidate_models = cls._get_candidate_models()
        gcp_project = os.environ.get("GCP_PROJECT_ID") or os.environ.get("FIRESTORE_PROJECT_ID") or os.environ.get("GOOGLE_CLOUD_PROJECT")
        gcp_region = os.environ.get("GCP_REGION") or os.environ.get("VERTEX_AI_LOCATION") or "us-central1"

        payload_bytes = json.dumps({
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": 0.4
            }
        }).encode("utf-8")

        std_payload_bytes = json.dumps({
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "response_mime_type": "application/json",
                "temperature": 0.4
            }
        }).encode("utf-8")

        # ----------------------------------------------------------------------
        # Path 1: API Key Provided (`AQ....` Vertex Express key OR `AIza...` AI Studio key)
        # ----------------------------------------------------------------------
        if api_key:
            is_vertex_key = api_key.startswith("AQ.")

            # 1A: Try google-genai SDK if installed
            try:
                from google import genai
                for model_name in candidate_models[:2]:
                    try:
                        client = genai.Client(vertexai=is_vertex_key, api_key=api_key)
                        resp = client.models.generate_content(
                            model=model_name,
                            contents=prompt,
                            config={"response_mime_type": "application/json"}
                        )
                        if resp and resp.text:
                            parsed = cls._clean_json_text(resp.text)
                            cls._WORKING_MODEL = model_name
                            cls._LAST_USED_SOURCE = f"LIVE_GEMINI_SDK ({model_name})"
                            return parsed
                    except Exception as sdk_err:
                        err_str = str(sdk_err).lower()
                        if "404" not in err_str and "not found" not in err_str:
                            break
            except ImportError:
                pass

            # 1B: Try Vertex AI Express REST endpoints (for `AQ.` keys)
            if is_vertex_key:
                endpoint_templates = [
                    "https://aiplatform.googleapis.com/v1/publishers/google/models/{model}:generateContent?key={key}",
                    "https://aiplatform.googleapis.com/v1beta1/publishers/google/models/{model}:generateContent?key={key}",
                ]
                if gcp_project:
                    endpoint_templates.insert(
                        0,
                        f"https://{gcp_region}-aiplatform.googleapis.com/v1/projects/{gcp_project}/locations/{gcp_region}/publishers/google/models/{{model}}:generateContent?key={{key}}"
                    )
                for tmpl in endpoint_templates:
                    for model_name in candidate_models[:3]:
                        url = tmpl.format(model=model_name, key=api_key)
                        try:
                            req = urllib.request.Request(url, data=payload_bytes, headers={"Content-Type": "application/json"})
                            with urllib.request.urlopen(req, timeout=timeout) as response:
                                res_data = json.loads(response.read().decode("utf-8"))
                                text_out = res_data["candidates"][0]["content"]["parts"][0]["text"]
                                parsed = cls._clean_json_text(text_out)
                                cls._WORKING_MODEL = model_name
                                cls._LAST_USED_SOURCE = f"LIVE_VERTEX_EXPRESS_API ({model_name})"
                                return parsed
                        except urllib.error.HTTPError as he:
                            if he.code == 404:
                                continue
                            if he.code == 403:
                                endpoint_templates = []
                                break
                            break
                        except Exception:
                            break

            # 1C: Try Google AI Studio Generativelanguage REST endpoint (for `AIza...` or general keys)
            if not is_vertex_key:
                for model_name in candidate_models[:3]:
                    try:
                        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
                        req = urllib.request.Request(url, data=std_payload_bytes, headers={"Content-Type": "application/json"})
                        with urllib.request.urlopen(req, timeout=timeout) as response:
                            res_data = json.loads(response.read().decode("utf-8"))
                            text_out = res_data["candidates"][0]["content"]["parts"][0]["text"]
                            parsed = cls._clean_json_text(text_out)
                            cls._WORKING_MODEL = model_name
                            cls._LAST_USED_SOURCE = f"LIVE_GEMINI_REST_API ({model_name})"
                            return parsed
                    except urllib.error.HTTPError as he:
                        if he.code == 404:
                            continue
                        break
                    except Exception:
                        break

        # ----------------------------------------------------------------------
        # Path 2: Service Account JSON (`FIRESTORE_SA_JSON` or `GOOGLE_APPLICATION_CREDENTIALS`)
        # ----------------------------------------------------------------------
        sa_info = DualModeStorageAdapter.parse_inline_service_account(os.environ.get("FIRESTORE_SA_JSON"))
        if not sa_info:
            creds_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
            if creds_path and os.path.exists(creds_path):
                try:
                    with open(creds_path, "r", encoding="utf-8") as f:
                        sa_info = json.load(f)
                except Exception:
                    sa_info = None

        if sa_info:
            sa_project = sa_info.get("project_id") or gcp_project
            try:
                from google.oauth2 import service_account
                from google.auth.transport.requests import Request as GoogleAuthRequest

                creds = service_account.Credentials.from_service_account_info(
                    sa_info,
                    scopes=["https://www.googleapis.com/auth/cloud-platform"]
                )
                creds.refresh(GoogleAuthRequest())
                bearer_token = creds.token

                for region_candidate in list(dict.fromkeys(["us-central1", gcp_region, "asia-south1"])):
                    for model_name in list(dict.fromkeys(["gemini-2.5-flash-lite", "gemini-2.5-flash"] + candidate_models)):
                        try:
                            url = f"https://{region_candidate}-aiplatform.googleapis.com/v1/projects/{sa_project}/locations/{region_candidate}/publishers/google/models/{model_name}:generateContent"
                            req = urllib.request.Request(
                                url,
                                data=payload_bytes,
                                headers={
                                    "Content-Type": "application/json",
                                    "Authorization": f"Bearer {bearer_token}"
                                }
                            )
                            with urllib.request.urlopen(req, timeout=timeout) as response:
                                res_data = json.loads(response.read().decode("utf-8"))
                                text_out = res_data["candidates"][0]["content"]["parts"][0]["text"]
                                parsed = cls._clean_json_text(text_out)
                                cls._WORKING_MODEL = model_name
                                cls._LAST_USED_SOURCE = f"LIVE_VERTEX_SA_API ({model_name})"
                                return parsed
                        except urllib.error.HTTPError as he:
                            if he.code == 404:
                                continue
                            continue
                        except Exception:
                            continue
            except Exception:
                pass

        return None


class DemandAndInventoryAgent:
    """Identifies high-surge anchor items and pairs them with high-margin or slow-moving items using Live Gemini AI + inventory grounding."""

    @staticmethod
    def find_products_from_prompt(
        prompt: str,
        preferred_anchor_id: Optional[str] = None,
        preferred_attached_id: Optional[str] = None,
        api_key: Optional[str] = None
    ) -> Tuple[Product, Product, float, str]:
        products = StoreDataManager.load_products()
        prompt_lower = prompt.lower()

        # 1. Explicit user selection overrides
        if preferred_anchor_id:
            anchor = next((p for p in products if p.id == preferred_anchor_id), None)
            if anchor:
                if preferred_attached_id:
                    attached = next((p for p in products if p.id == preferred_attached_id and p.id != anchor.id), None)
                else:
                    affinities = AFFINITY_MATRIX.get(anchor.id, {})
                    candidates = [p for p in products if p.id != anchor.id]
                    candidates.sort(key=lambda p: affinities.get(p.id, 0), reverse=True)
                    attached = candidates[0] if candidates else products[0]

                if attached:
                    affinity = AFFINITY_MATRIX.get(anchor.id, {}).get(attached.id, 58.0)
                    driver = f"Retailer selection of {anchor.name} paired with {attached.name}"
                    return anchor, attached, affinity, driver

        # 2. Live Gemini Search-Time SKU Selection
        catalog_summary = [
            {
                "id": p.id,
                "name": p.name,
                "category": p.category,
                "mrp": p.selling_price,
                "cost": p.cost_price,
                "stock": p.stock_quantity,
                "velocity": p.velocity_status,
                "expiry_days": p.expiry_days
            }
            for p in products
        ]
        ai_prompt = f"""You are PromoMind AI's Inventory & Basket Pairing Agent.
Retailer Search Query: "{prompt}"

Available Store Inventory SKUs:
{json.dumps(catalog_summary, indent=2)}

Select the best 2 distinct products from the inventory to form a high-margin retail combo:
1. `anchor_id`: High-velocity or high-demand hook product matching the retailer's intent.
2. `attached_id`: Complementary high-margin or slow-moving/expiring product to bundle with the anchor.
3. `affinity_score`: Estimated basket co-purchase probability percentage (between 45.0 and 88.0).
4. `driver`: 1-sentence strategic explanation of why these two SKUs pair well for this query.

Return ONLY valid JSON with keys: anchor_id, attached_id, affinity_score, driver.
"""
        ai_selection = GeminiLiveClient.generate_json(ai_prompt, override_api_key=api_key, timeout=6)
        if isinstance(ai_selection, dict):
            a_id = ai_selection.get("anchor_id")
            b_id = ai_selection.get("attached_id")
            anchor_obj = next((p for p in products if p.id == a_id), None)
            attached_obj = next((p for p in products if p.id == b_id and p.id != a_id), None)
            if anchor_obj and attached_obj:
                aff = float(ai_selection.get("affinity_score", 62.5))
                drv = str(ai_selection.get("driver") or f"AI-matched {anchor_obj.name} with {attached_obj.name}")
                return anchor_obj, attached_obj, aff, drv

        # 3. Deterministic Inventory Token & Category Resolution Fallback
        anchor = None
        attached = None

        matched_from_inventory = []
        for p in products:
            p_name_lower = p.name.lower()
            if p_name_lower in prompt_lower:
                matched_from_inventory.append(p)
            else:
                tokens = [w.strip() for w in p_name_lower.replace('-', ' ').replace('/', ' ').replace('(', ' ').replace(')', ' ').split() if len(w.strip()) > 3]
                if any(t in prompt_lower for t in tokens):
                    matched_from_inventory.append(p)

        if len(matched_from_inventory) >= 2:
            anchor = matched_from_inventory[0]
            attached = matched_from_inventory[1]
        elif len(matched_from_inventory) == 1:
            anchor = matched_from_inventory[0]

        if not anchor:
            if "tea" in prompt_lower or "chai" in prompt_lower:
                anchor = next((p for p in products if "tea" in p.name.lower() or p.category == "Beverages"), products[0])
            elif "ghee" in prompt_lower or "diwali" in prompt_lower or "deepa" in prompt_lower or "festiv" in prompt_lower:
                anchor = next((p for p in products if "ghee" in p.name.lower() or "dairy" in p.category.lower()), products[0])
            elif "oil" in prompt_lower:
                anchor = next((p for p in products if "oil" in p.name.lower() or "staple" in p.category.lower()), products[0])
            else:
                forecast = sorted(DEMAND_FORECASTS, key=lambda f: f.projected_surge_pct, reverse=True)[0]
                anchor = next((p for p in products if p.id == forecast.product_id), products[0])

        if not attached:
            if "biscuit" in prompt_lower or "cookie" in prompt_lower or "snack" in prompt_lower:
                attached = next((p for p in products if ("biscuit" in p.name.lower() or "snack" in p.category.lower()) and p.id != anchor.id), None)
            elif "almond" in prompt_lower or "dry fruit" in prompt_lower or "sweet" in prompt_lower:
                attached = next((p for p in products if ("almond" in p.name.lower() or "dry fruit" in p.category.lower() or "sweet" in p.category.lower()) and p.id != anchor.id), None)
            elif "masala" in prompt_lower or "spice" in prompt_lower:
                attached = next((p for p in products if "masala" in p.name.lower() and p.id != anchor.id), None)

        if not attached:
            affinities = AFFINITY_MATRIX.get(anchor.id, {})
            candidates = [p for p in products if p.id != anchor.id]
            slow_candidates = [p for p in candidates if p.velocity_status == "SLOW_MOVING"]
            if slow_candidates:
                slow_candidates.sort(key=lambda p: affinities.get(p.id, 0), reverse=True)
                attached = slow_candidates[0]
            elif candidates:
                candidates.sort(key=lambda p: affinities.get(p.id, 0), reverse=True)
                attached = candidates[0]
            else:
                attached = anchor

        driver = f"High velocity {anchor.name} paired with {attached.name} for inventory acceleration"
        affinity = AFFINITY_MATRIX.get(anchor.id, {}).get(attached.id, 58.5)
        return anchor, attached, affinity, driver


class PricingAndMarginAgent:
    """Calculates consumer-attractive price points using Open-Source Price Elasticity of Demand (PED)."""

    @staticmethod
    def optimize_price(
        anchor: Product,
        attached: Product,
        min_margin_pct: float = 18.0,
        offer_type: str = "COMBO_DISCOUNT",
        archetype: str = "ANCHOR_MARGIN_BOOSTER",
        event_surge_pct: float = 0.0
    ) -> Dict[str, Any]:
        return PriceElasticityOptimizer.optimize_bundle_pricing(
            anchor_mrp=anchor.selling_price,
            anchor_cost=anchor.cost_price,
            anchor_category=anchor.category,
            attached_mrp=attached.selling_price,
            attached_cost=attached.cost_price,
            attached_category=attached.category,
            attached_expiry_days=attached.expiry_days,
            attached_stock=attached.stock_quantity,
            min_margin_pct=min_margin_pct,
            archetype=archetype,
            event_surge_pct=event_surge_pct
        )


class ROIPredictorAgent:
    """Simulates 10-day promotional performance vs status quo."""

    @staticmethod
    def simulate_roi(
        anchor: Product,
        attached: Product,
        pricing_result: Dict[str, Any]
    ) -> ROIMetrics:
        baseline_units = attached.weekly_sales_avg * 2
        projected_units = pricing_result.get("projected_units_10d", int(baseline_units * 2.5))
        combo_price = pricing_result["bundle_price"]
        net_margin_pct = pricing_result["net_margin_pct"]

        baseline_rev = (anchor.selling_price * anchor.weekly_sales_avg * 1.5) + (attached.selling_price * baseline_units)
        projected_rev = projected_units * combo_price
        revenue_lift = round(projected_rev - baseline_rev, 2)

        stock_cleared_pct = min(100.0, round((projected_units / max(attached.stock_quantity, 1)) * 100.0, 1))
        profit_inr = round(projected_rev * (net_margin_pct / 100.0), 2)

        return ROIMetrics(
            baseline_units_10d=baseline_units,
            projected_units_10d=projected_units,
            units_lift_pct=pricing_result.get("volume_lift_pct", 35.0),
            projected_revenue_inr=projected_rev,
            revenue_lift_inr=revenue_lift,
            dead_stock_cleared_pct=stock_cleared_pct,
            projected_gross_margin_pct=net_margin_pct,
            projected_net_profit_inr=profit_inr
        )


class GeminiCreativeAgent:
    """Generates marketing copy, WhatsApp broadcast, poster, and cashier checkout pitch dynamically at search time."""

    @staticmethod
    def generate_creatives(
        combo_name: str,
        anchor: Product,
        attached: Product,
        combo_price: float,
        discount_amount: float,
        discount_pct: float,
        driver: str,
        event_theme: str = "Diwali Maha Utsav",
        offer_type: str = "COMBO_DISCOUNT",
        archetype: str = "ANCHOR_MARGIN_BOOSTER",
        store_profile: Optional[StoreProfile] = None,
        api_key: Optional[str] = None
    ) -> Tuple[CreativeAssets, str]:
        profile = store_profile or StoreProfile()

        region = (profile.region or "Karnataka & South India").lower()
        if "karnataka" in region or "south" in region:
            fest_greeting = "Deepavali Habbada Shubhashayagalu!" if "diwali" in event_theme.lower() else "Habba Special Offers!"
            cashier_script = f"Sir/Ma'am, {anchor.name.split('(')[0].strip()} ke saath {attached.name.split('(')[0].strip()} bundle me lenge toh ₹{int(discount_amount)} ki direct bachat hai!"
        elif "maharashtra" in region or "west" in region:
            fest_greeting = "Diwali Chya Hardik Shubhechha!" if "diwali" in event_theme.lower() else "Utsav Vishesh Bumper Deal!"
            cashier_script = f"Namaskar! {anchor.name.split('(')[0].strip()} sobat {attached.name.split('(')[0].strip()} ghetla tar ₹{int(discount_amount)} cha discount miltoye!"
        elif "bengal" in region or "east" in region:
            fest_greeting = "Subho Bijoya & Pujo'r Preeti O Shubhechha!" if "puja" in event_theme.lower() else "Bumper Pujo Offer!"
            cashier_script = f"Dada/Didi, {anchor.name.split('(')[0].strip()}-er sathe {attached.name.split('(')[0].strip()} bundle-e ₹{int(discount_amount)} chhar pachhen!"
        else:
            fest_greeting = "Diwali Ki Hardik Shubhkamnayein!" if "diwali" in event_theme.lower() else "Special Retail Saver Deal!"
            cashier_script = f"Bhaiya/Bhabhi, {anchor.name.split('(')[0].strip()} ke saath {attached.name.split('(')[0].strip()} pack lene par ₹{int(discount_amount)} ki bachat hai, bill me add kar doon?"

        offer_headline_label = f"{archetype.replace('_', ' ').title()} — Save ₹{int(discount_amount)} ({discount_pct}% OFF)"

        prompt_content = f"""You are PromoMind AI, an elite retail copywriter for grocery stores & supermarkets.
Store Name: {profile.store_name} ({profile.locality}, {profile.city}, {profile.region})
Festival / Event Theme: {event_theme}
Regional Greeting: {fest_greeting}
Offer Format / Archetype: {archetype}
Combo Items: {anchor.name} + {attached.name}
Combo Price: Rs. {combo_price} (Save Rs. {discount_amount} / {discount_pct}% OFF)
Theme Occasion: {driver}

Respond in valid JSON format with exactly these keys:
- poster_headline: (Punchy 4-6 word headline incorporating the event {event_theme})
- poster_subheading: (Short subtitle emphasizing savings and store {profile.store_name})
- poster_badge: (e.g., '{event_theme.upper()} • SAVE ₹{int(discount_amount)}')
- poster_body: (2 lines highlighting the pairing, festival tradition, and consumer benefit)
- whatsapp_message: (Engaging WhatsApp broadcast with regional greeting '{fest_greeting}', pricing, savings, and store address)
- pos_tagline: (Snappy 1-liner printed on bill receipts)
- cashier_counter_pitch: (1-line friendly verbal upsell pitch for the billing cashier including the word 'save' or 'bachat' or 'discount')
"""
        parsed = GeminiLiveClient.generate_json(prompt_content, override_api_key=api_key, timeout=7)
        if isinstance(parsed, dict) and parsed.get("poster_headline") and parsed.get("whatsapp_message"):
            pitch_val = parsed.get("cashier_counter_pitch") or cashier_script
            if not any(w in pitch_val.lower() for w in ["bachat", "save", "combo", "deal", "festive", "discount"]):
                pitch_val = f"{pitch_val} (Save ₹{int(discount_amount)} discount deal!)"
            parsed["cashier_counter_pitch"] = pitch_val
            return CreativeAssets(**parsed), GeminiLiveClient._LAST_USED_SOURCE

        # High-Quality Regional Synthesis Fallback
        anchor_short = anchor.name.split('(')[0].strip()
        attached_short = attached.name.split('(')[0].strip()
        is_festive = any(w in event_theme.lower() for w in ["diwali", "festive", "puja", "dasara", "pongal", "onam", "ugadi"]) or "ghee" in anchor.name.lower()

        if is_festive:
            headline = f"{event_theme}: {anchor_short} + {attached_short}"
            subheading = f"Celebrate with Premium Delights & Guaranteed Savings at {profile.store_name}"
            badge = f"{event_theme.upper()} • SAVE ₹{int(discount_amount)}"
            body = f"Pair authentic {anchor.name} with nutritious {attached.name}. Specially curated for {profile.region} festivities!"
            whatsapp = (
                f"*{fest_greeting}*\n"
                f"*{event_theme.upper()} SPECIAL SAVINGS at {profile.store_name}!*\n\n"
                f"*Offer Format:* {offer_headline_label}\n"
                f"*Curated Bundle:* {anchor.name} + {attached.name}\n\n"
                f"Combined MRP: ~₹{int(anchor.selling_price + attached.selling_price)}~\n"
                f"*Exclusive Offer Price: ₹{int(combo_price)} only!*\n"
                f"*Instant Cash Savings: ₹{int(discount_amount)} ({discount_pct}% OFF)*\n\n"
                f"*Visit Us:* {profile.store_name}, {profile.locality}, {profile.city}\n"
                f"*Limited Stock:* Valid for next 5 days or until festive stock lasts!\n"
                f"Reply 'BOOK' on WhatsApp to reserve your pack at the counter!"
            )
            pos_tagline = f"{event_theme}: Save ₹{int(discount_amount)} on {anchor_short} + {attached_short} pack today!"
        else:
            headline = f"{event_theme}: {anchor_short} + {attached_short}"
            subheading = f"Everyday Kitchen Essentials at Unbeatable Prices — {profile.store_name}"
            badge = f"{event_theme.upper()} • {discount_pct}% OFF"
            body = f"Enjoy quality {anchor.name} paired with {attached.name}."
            whatsapp = (
                f"*{event_theme.upper()} EXCLUSIVE DEAL at {profile.store_name}!*\n\n"
                f"Upgrade your household pantry with our verified value duo:\n"
                f"*{anchor.name}* + *{attached.name}*\n\n"
                f"MRP: ~₹{int(anchor.selling_price + attached.selling_price)}~\n"
                f"*Special Deal Price: ₹{int(combo_price)}!*\n"
                f"*Your Savings: ₹{int(discount_amount)} ({discount_pct}% OFF)*\n\n"
                f"{profile.store_name}, {profile.locality}, {profile.city}\n"
                f"Grab yours today at the counter before stock runs out!"
            )
            pos_tagline = f"{event_theme}: Save ₹{int(discount_amount)} on {anchor_short} + {attached_short} at checkout!"

        return CreativeAssets(
            poster_headline=headline,
            poster_subheading=subheading,
            poster_badge=badge,
            poster_body=body,
            whatsapp_message=whatsapp,
            pos_tagline=pos_tagline,
            cashier_counter_pitch=cashier_script
        ), "HYBRID_LOCAL_SYNTHESIS"


class PromoMindEngine:
    """Master Orchestrator uniting Live Gemini Reasoning, Demand Forecasting, Price Elasticity, ROI, and Creative Agents."""

    @classmethod
    def generate_plan(
        cls,
        query: str,
        min_margin_pct: float = 18.0,
        event_theme: str = "Diwali Maha Utsav",
        offer_type: str = "COMBO_DISCOUNT",
        primary_product_id: Optional[str] = None,
        secondary_product_id: Optional[str] = None,
        region: Optional[str] = None,
        archetype: Optional[str] = "ANCHOR_MARGIN_BOOSTER",
        api_key: Optional[str] = None
    ) -> ComboPlan:
        store_profile = StoreDataManager.load_profile()
        if region:
            store_profile.region = region

        # Step 1: Detect items & affinity (Live Gemini + Inventory Grounded)
        anchor, attached, affinity, driver = DemandAndInventoryAgent.find_products_from_prompt(
            prompt=query,
            preferred_anchor_id=primary_product_id,
            preferred_attached_id=secondary_product_id,
            api_key=api_key
        )

        # Step 2: Compute Association Probability (Apriori Mining)
        prob_metrics = OpenSourceForecastingEngine.calculate_co_purchase_probability(
            anchor.id, attached.id, affinity
        )

        # Step 3: Run Open-Source Holt-Winters Demand Forecasting on Anchor SKU
        past_sales = anchor.past_sales_weeks or [30, 32, 35, 38, 42, 45]
        event_surge = 85.0 if "diwali" in event_theme.lower() else (45.0 if "monsoon" in event_theme.lower() else 30.0)
        forecast_result = OpenSourceForecastingEngine.predict_demand_surge(
            past_sales, event_surge_pct=event_surge
        )

        # Step 4: Calculate Dynamic Price Elasticity & Optimized Margin
        pricing_result = PricingAndMarginAgent.optimize_price(
            anchor=anchor,
            attached=attached,
            min_margin_pct=min_margin_pct,
            offer_type=offer_type,
            archetype=archetype or "ANCHOR_MARGIN_BOOSTER",
            event_surge_pct=event_surge
        )

        combined_mrp = pricing_result["original_mrp"]
        combo_price = pricing_result["bundle_price"]
        disc_amt = pricing_result["discount_amount"]
        disc_pct = pricing_result["discount_pct"]
        net_margin = pricing_result["net_margin_pct"]

        # Step 5: Simulate ROI metrics
        roi = ROIPredictorAgent.simulate_roi(anchor, attached, pricing_result)

        # Step 6: Generate marketing copy & creatives via Live Gemini API
        combo_name = f"{anchor.name.split('(')[0].strip()} + {attached.name.split('(')[0].strip()}"
        creatives, gen_source = GeminiCreativeAgent.generate_creatives(
            combo_name=combo_name,
            anchor=anchor,
            attached=attached,
            combo_price=combo_price,
            discount_amount=disc_amt,
            discount_pct=disc_pct,
            driver=driver,
            event_theme=event_theme,
            offer_type=offer_type,
            archetype=archetype or "ANCHOR_MARGIN_BOOSTER",
            store_profile=store_profile,
            api_key=api_key
        )

        # Step 7: Generate 5 Dynamic Promotion Varieties
        raw_varieties = PriceElasticityOptimizer.generate_all_varieties(
            anchor_mrp=anchor.selling_price,
            anchor_cost=anchor.cost_price,
            anchor_category=anchor.category,
            attached_mrp=attached.selling_price,
            attached_cost=attached.cost_price,
            attached_category=attached.category,
            attached_expiry_days=attached.expiry_days,
            attached_stock=attached.stock_quantity,
            min_margin_pct=min_margin_pct,
            event_surge_pct=event_surge,
            chosen_archetype=archetype or "ANCHOR_MARGIN_BOOSTER"
        )

        greeting = "Namaskara" if "karnataka" in store_profile.region.lower() or "south" in store_profile.region.lower() else (
            "Namaste" if "north" in store_profile.region.lower() or "delhi" in store_profile.region.lower() else (
                "Nomoshkar" if "bengal" in store_profile.region.lower() or "east" in store_profile.region.lower() else "Namaste"
            )
        )

        variety_models: List[PromotionVariety] = []
        for v in raw_varieties:
            v_type = v["variety_type"]
            v_price = v["combo_price"]
            v_disc_amt = v["discount_amount"]
            v_disc_pct = v["discount_pct"]
            v_title = v["title"]
            anchor_short = anchor.name.split('(')[0].strip()
            attached_short = attached.name.split('(')[0].strip()

            if v_type == "MARGIN_BOOSTER":
                pitch = f"{greeting}! {anchor_short} ke saath {attached_short} bundle me lene par flat ₹{int(v_disc_amt)} ki direct bachat hai, bill me add kar doon?"
                wa_copy = f"*{event_theme.upper()} VALUE DUO:* Get {anchor_short} + {attached_short} for just ₹{int(v_price)} (Save ₹{int(v_disc_amt)}) at {store_profile.store_name}!"
                headline = f"EVERYDAY VALUE: {anchor_short} + {attached_short}"
            elif v_type == "EXPIRY_CLEARANCE":
                pitch = f"{greeting}! Aaj limited clearance flash deal hai: {attached_short} par flat {v_disc_pct}% discount mil raha hai {anchor_short} ke saath! Bag me add karein?"
                wa_copy = f"*FLASH CLEARANCE DEAL:* Get {attached_short} at {v_disc_pct}% OFF when paired with {anchor_short} for only ₹{int(v_price)}! Limited shelf stock at {store_profile.store_name}."
                headline = f"FLASH CLEARANCE: SAVE ₹{int(v_disc_amt)} ({v_disc_pct}% OFF)"
            elif v_type == "VOLUME_SLAB":
                pitch = f"{greeting}! Yeh double bundle lene par direct ₹{int(v_disc_amt)} bachat hai aur 2 packs par extra cashback reward milega!"
                wa_copy = f"*BUY MORE • SAVE MORE:* Stock up {anchor_short} + {attached_short} at ₹{int(v_price)} (Save ₹{int(v_disc_amt)}). Extra savings on 2+ packs at {store_profile.store_name}!"
                headline = f"VOLUME SAVER: {anchor_short} + {attached_short} PACK"
            elif v_type == "FESTIVE_HAMPER":
                pitch = f"Happy {event_theme.split('(')[0].strip()}! Festive Celebration Gift Box ready hai gifting ke liye flat ₹{int(v_disc_amt)} discount ke saath, pack kar doon?"
                wa_copy = f"*FESTIVE CELEBRATION BOX:* Premium {anchor_short} paired with {attached_short} at ₹{int(v_price)} (MRP ₹{int(combined_mrp)}). Perfect for festive gifting from {store_profile.store_name}!"
                headline = f"FESTIVE CELEBRATION BOX: ₹{int(v_price)} ONLY"
            else:
                pitch = f"{greeting}! Store me ₹799+ billing par yeh {attached_short} bundle deal unlock ho raha hai sirf ₹{int(v_price)} me!"
                wa_copy = f"*CART UNLOCK SPECIAL:* Shop for ₹799+ at {store_profile.store_name} and unlock {anchor_short} + {attached_short} at a ₹{int(v_disc_amt)} discount!"
                headline = f"SPEND ₹799+ & UNLOCK AT ₹{int(v_price)}"

            variety_models.append(PromotionVariety(
                id=v["id"],
                variety_type=v_type,
                title=v_title,
                tagline=v["tagline"],
                badge=v["badge"],
                badge_class=v["badge_class"],
                icon=v["icon"],
                combo_price=v_price,
                original_mrp=combined_mrp,
                discount_amount=v_disc_amt,
                discount_pct=v_disc_pct,
                net_margin_pct=v["net_margin_pct"],
                projected_volume_lift_pct=v["projected_volume_lift_pct"],
                capital_turnover_days=v["capital_turnover_days"],
                customer_target=v["customer_target"],
                cashier_counter_pitch=pitch,
                whatsapp_copy=wa_copy,
                poster_headline=headline,
                poster_savings=f"YOU SAVE ₹{int(v_disc_amt)} ({v_disc_pct}% OFF)",
                is_recommended=v["is_recommended"]
            ))

        tagline = f"{event_theme} Special | Save ₹{int(disc_amt)} ({disc_pct}% OFF) | Protects {net_margin}% Retail Margin"

        rationale = (
            f"Regional Signal for {store_profile.region}: '{event_theme}' accelerates demand on '{anchor.name}' "
            f"(Predicted growth: {forecast_result['expected_growth_pct']:+}% over next 4 weeks). "
            f"Paired with '{attached.name}' ({attached.velocity_status}, {attached.expiry_days or 90}d shelf life) "
            f"via Co-Purchase Confidence {prob_metrics['confidence_pct']}% (Lift: {prob_metrics['lift_score']}x). "
            f"Optimized via Open-Source Price Elasticity ({pricing_result['blended_elasticity']}) under archetype '{archetype}' at ₹{int(combo_price)} "
            f"to drive +{pricing_result['volume_lift_pct']}% volume lift while securing a {net_margin}% net profit margin. "
            f"Generated {len(variety_models)} distinct promotional variety tiers for diverse customer demographics."
        )

        return ComboPlan(
            combo_id="COMBO_" + str(int(combo_price)),
            title=combo_name,
            tagline=tagline,
            anchor_product=anchor,
            attached_product=attached,
            affinity_score_pct=affinity,
            demand_driver=driver,
            original_combined_mrp=combined_mrp,
            recommended_combo_price=combo_price,
            combo_price=combo_price,
            original_total_mrp=combined_mrp,
            discount_amount=disc_amt,
            discount_pct=disc_pct,
            net_margin_pct=net_margin,
            target_customer_segment=f"{event_theme} Shoppers ({store_profile.locality})",
            strategic_rationale=rationale,
            creative_assets=creatives,
            roi_prediction=roi,
            event_theme=event_theme,
            offer_type=offer_type,
            archetype=archetype,
            region=store_profile.region,
            co_purchase_probability=prob_metrics,
            forecasting_summary=forecast_result,
            varieties=variety_models,
            generation_source=gen_source,
            hybrid_architecture={
                "engine_type": "NEURO_SYMBOLIC_HYBRID",
                "ai_layer": {
                    "model": "Gemini 2.5 Flash (Live Generative Agent)",
                    "source": gen_source,
                    "role": "Cultural Context, Regional Vernacular & Omnichannel Persuasion",
                    "regional_grounding": store_profile.region,
                    "festive_driver": driver,
                    "psychological_hook": "Direct Rupee Savings Framing (Converts 2.3x higher than %)"
                },
                "math_layer": {
                    "model": "Open-Source Econometric & Statistical Optimization",
                    "role": "Price Elasticity of Demand (PED), Apriori Mining & Margin Floors",
                    "blended_elasticity": pricing_result["blended_elasticity"],
                    "apriori_confidence_pct": prob_metrics["confidence_pct"],
                    "apriori_lift": prob_metrics["lift_score"],
                    "projected_volume_lift_pct": pricing_result["volume_lift_pct"],
                    "net_margin_pct": net_margin,
                    "margin_floor_protected": True
                },
                "synergy_summary": "Generative AI formulates the emotional and cultural appeal at search time, while open-source mathematical equations calculate price elasticity and enforce strict margin floors."
            }
        )

    @classmethod
    def generate_brand_comparison(cls, prod: Product, region: str = "Karnataka & South India", api_key: Optional[str] = None) -> Dict[str, Any]:
        """Dynamically compares a store SKU against competing regional and national brands using Live Gemini AI."""
        past = prod.past_sales_weeks or [20, 22, 24, 25, 26, 28]
        forecast = prod.forecast_sales_weeks or [30, 34, 38, 42]
        margin = round(((prod.selling_price - prod.cost_price) / max(1.0, prod.selling_price)) * 100, 1)

        prompt = f"""You are an FMCG Retail Procurement & Brand Intelligence Analyst for {region}.
Analyze this store SKU and generate a multi-brand comparison against 2 authentic competing brands in {region}:
Store SKU: {prod.name} (Category: {prod.category}, MRP: ₹{prod.selling_price}, Cost: ₹{prod.cost_price}, Margin: {margin}%, Weekly Sales: {prod.weekly_sales_avg} units)

Return ONLY valid JSON with:
- recommendation: 2-sentence procurement & brand switching advice for the retailer.
- competitor_brands: array of 2 objects, each with:
  - brand_name: Authentic regional or national competitor brand name for {prod.category} in {region}
  - mrp: float
  - cost_price: float
  - margin_pct: float
  - weekly_sales_avg: int
  - turnover_rating: "HIGH", "MODERATE", or "LOW"
  - market_share_pct: float
"""
        ai_res = GeminiLiveClient.generate_json(prompt, override_api_key=api_key, timeout=6)
        if isinstance(ai_res, dict) and isinstance(ai_res.get("competitor_brands"), list) and len(ai_res["competitor_brands"]) >= 2:
            brands_out = [
                {
                    "brand_name": f"{prod.name.split('(')[0].strip()} (Current Store Brand)",
                    "mrp": prod.selling_price,
                    "cost_price": prod.cost_price,
                    "margin_pct": margin,
                    "weekly_sales_avg": prod.weekly_sales_avg,
                    "past_sales": past,
                    "forecast_sales": forecast,
                    "turnover_rating": "HIGH" if prod.weekly_sales_avg >= 35 else "MODERATE",
                    "market_share_pct": 55.0
                }
            ]
            for idx, cb in enumerate(ai_res["competitor_brands"][:2]):
                scale = 0.8 if idx == 0 else 0.55
                brands_out.append({
                    "brand_name": str(cb.get("brand_name", f"Alternative Brand {idx+1}")),
                    "mrp": float(cb.get("mrp", round(prod.selling_price * 0.95, 1))),
                    "cost_price": float(cb.get("cost_price", round(prod.cost_price * 0.88, 1))),
                    "margin_pct": float(cb.get("margin_pct", round(margin + 3.0, 1))),
                    "weekly_sales_avg": int(cb.get("weekly_sales_avg", max(5, int(prod.weekly_sales_avg * scale)))),
                    "past_sales": [max(2, int(x * scale)) for x in past],
                    "forecast_sales": [max(3, int(x * scale)) for x in forecast],
                    "turnover_rating": str(cb.get("turnover_rating", "MODERATE")),
                    "market_share_pct": float(cb.get("market_share_pct", 25.0 if idx == 0 else 20.0))
                })
            return {
                "product_id": prod.id,
                "product_name": prod.name,
                "category": prod.category,
                "recommendation": str(ai_res.get("recommendation", f"Current store brand yields {margin}% margin.")),
                "brands": brands_out,
                "generation_source": GeminiLiveClient._LAST_USED_SOURCE
            }

        comparison = CATEGORY_BRAND_COMPARISONS.get(prod.id)
        if comparison:
            out = dict(comparison)
            out["generation_source"] = "HYBRID_LOCAL_SYNTHESIS"
            return out

        return {
            "product_id": prod.id,
            "product_name": prod.name,
            "category": prod.category,
            "recommendation": f"Current store brand has {margin}% margin. Compare with wholesale alternative brands to optimize cash churn.",
            "generation_source": "HYBRID_LOCAL_SYNTHESIS",
            "brands": [
                {
                    "brand_name": f"{prod.name.split('(')[0].strip()} (Current Brand)",
                    "mrp": prod.selling_price,
                    "cost_price": prod.cost_price,
                    "margin_pct": margin,
                    "weekly_sales_avg": prod.weekly_sales_avg,
                    "past_sales": past,
                    "forecast_sales": forecast,
                    "turnover_rating": "HIGH" if prod.weekly_sales_avg >= 35 else "MODERATE",
                    "market_share_pct": 60.0
                },
                {
                    "brand_name": "Regional APMC / Wholesale Alternative",
                    "mrp": round(prod.selling_price * 0.92, 1),
                    "cost_price": round(prod.cost_price * 0.85, 1),
                    "margin_pct": round(margin + 4.5, 1),
                    "weekly_sales_avg": int(prod.weekly_sales_avg * 0.75),
                    "past_sales": [int(x * 0.75) for x in past],
                    "forecast_sales": [int(x * 0.75) for x in forecast],
                    "turnover_rating": "MODERATE",
                    "market_share_pct": 25.0
                },
                {
                    "brand_name": "Premium Tier Competitor",
                    "mrp": round(prod.selling_price * 1.15, 1),
                    "cost_price": round(prod.cost_price * 1.10, 1),
                    "margin_pct": round(margin - 2.0, 1),
                    "weekly_sales_avg": int(prod.weekly_sales_avg * 0.5),
                    "past_sales": [int(x * 0.5) for x in past],
                    "forecast_sales": [int(x * 0.5) for x in forecast],
                    "turnover_rating": "LOW",
                    "market_share_pct": 15.0
                }
            ]
        }

    @classmethod
    def generate_weekly_recommendations(cls, region: Optional[str] = None, api_key: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Autonomous Weekly Offer Generator.
        Scans store inventory and uses Live Gemini + Price Elasticity to curate top 3 bundles.
        """
        store_profile = StoreDataManager.load_profile()
        if region:
            store_profile.region = region
        products = StoreDataManager.load_products()
        if len(products) < 2:
            return []

        recommendations = []

        # Idea 1: Expiry Rescue / Tea-Time Clearance
        tea = next((p for p in products if "tea" in p.name.lower() or p.category == "Beverages"), products[0])
        biscuit = next((p for p in products if ("biscuit" in p.name.lower() or "cookie" in p.name.lower() or "snack" in p.category.lower()) and p.id != tea.id), None)
        if not biscuit:
            biscuit = next((p for p in products if p.velocity_status == "SLOW_MOVING" and p.id != tea.id), products[1])
        if tea and biscuit:
            p1 = PricingAndMarginAgent.optimize_price(tea, biscuit, min_margin_pct=16.0, archetype="EXPIRY_RESCUE_CLEARANCE")
            recommendations.append({
                "idea_id": "IDEA_CLEARANCE",
                "badge": "Slow-Stock Clearance",
                "badge_class": "badge-variety-clearance",
                "icon": "",
                "title": "Morning Chai & Biscuit Saver Duo",
                "tagline": "Liquidates slow-moving biscuits before expiry using high-velocity tea",
                "anchor_id": tea.id,
                "anchor_name": tea.name,
                "anchor_mrp": tea.selling_price,
                "attached_id": biscuit.id,
                "attached_name": biscuit.name,
                "attached_mrp": biscuit.selling_price,
                "original_mrp": p1["original_mrp"],
                "combo_price": p1["bundle_price"],
                "discount_pct": p1["discount_pct"],
                "savings_amount": p1["discount_amount"],
                "net_margin_pct": p1["net_margin_pct"],
                "volume_lift_pct": p1["volume_lift_pct"],
                "archetype": "EXPIRY_RESCUE_CLEARANCE",
                "event_theme": "Super Weekend Retail Rush",
                "why_recommended": f"Pairs high-velocity {tea.name.split('(')[0].strip()} with near-expiry {biscuit.name.split('(')[0].strip()} ({biscuit.expiry_days or 24}d shelf life). Recovers dead capital in under 6 days with a {p1['net_margin_pct']}% net margin."
            })

        # Idea 2: Festive Celebration & Gifting Box
        ghee = next((p for p in products if "ghee" in p.name.lower() or "dairy" in p.category.lower()), None)
        dry_fruit = next((p for p in products if ("almond" in p.name.lower() or "dry fruit" in p.category.lower() or "sweet" in p.category.lower()) and (not ghee or p.id != ghee.id)), None)
        if ghee and dry_fruit:
            p2 = PricingAndMarginAgent.optimize_price(ghee, dry_fruit, min_margin_pct=18.0, archetype="FESTIVE_CELEBRATION_HAMPER", event_surge_pct=85.0)
            recommendations.append({
                "idea_id": "IDEA_FESTIVE",
                "badge": "Festive Gifting Special",
                "badge_class": "badge-variety-festive",
                "icon": "",
                "title": "Diwali Pure Ghee & Dry Fruit Box",
                "tagline": "Captures peak festival sweet-making demand and family gifting spend",
                "anchor_id": ghee.id,
                "anchor_name": ghee.name,
                "anchor_mrp": ghee.selling_price,
                "attached_id": dry_fruit.id,
                "attached_name": dry_fruit.name,
                "attached_mrp": dry_fruit.selling_price,
                "original_mrp": p2["original_mrp"],
                "combo_price": p2["bundle_price"],
                "discount_pct": p2["discount_pct"],
                "savings_amount": p2["discount_amount"],
                "net_margin_pct": p2["net_margin_pct"],
                "volume_lift_pct": p2["volume_lift_pct"],
                "archetype": "FESTIVE_CELEBRATION_HAMPER",
                "event_theme": "Diwali Maha Utsav",
                "why_recommended": f"Demand for {ghee.name.split('(')[0].strip()} surges +85% during Diwali in {store_profile.region}. Bundling with premium {dry_fruit.name.split('(')[0].strip()} drives gifting basket value at ₹{int(p2['bundle_price'])}."
            })

        # Idea 3: Everyday Cooking Staples Duo
        oil = next((p for p in products if "oil" in p.name.lower() or "staple" in p.category.lower()), None)
        spice = next((p for p in products if ("masala" in p.name.lower() or "spice" in p.category.lower()) and (not oil or p.id != oil.id)), None)
        if oil and spice:
            p3 = PricingAndMarginAgent.optimize_price(oil, spice, min_margin_pct=16.0, archetype="ANCHOR_MARGIN_BOOSTER")
            recommendations.append({
                "idea_id": "IDEA_STAPLES",
                "badge": "Kitchen Basket Builder",
                "badge_class": "badge-variety-recommended",
                "icon": "",
                "title": "Cooking Oil & Pure Spices Value Basket",
                "tagline": "Drives daily grocery checkout basket size with guaranteed 22%+ net profit",
                "anchor_id": oil.id,
                "anchor_name": oil.name,
                "anchor_mrp": oil.selling_price,
                "attached_id": spice.id,
                "attached_name": spice.name,
                "attached_mrp": spice.selling_price,
                "original_mrp": p3["original_mrp"],
                "combo_price": p3["bundle_price"],
                "discount_pct": p3["discount_pct"],
                "savings_amount": p3["discount_amount"],
                "net_margin_pct": p3["net_margin_pct"],
                "volume_lift_pct": p3["volume_lift_pct"],
                "archetype": "ANCHOR_MARGIN_BOOSTER",
                "event_theme": "Everyday Retail Value",
                "why_recommended": f"Essential grocery basket builder. High-velocity {oil.name.split('(')[0].strip()} pulls {spice.name.split('(')[0].strip()}, safeguarding a strong {p3['net_margin_pct']}% net profit."
            })

        return recommendations


class DynamicFestivalEngine:
    """
    Dynamic Regional Festival & FMCG Demand Surge Discovery Engine.
    Generates upcoming cultural festivals at the exact time of search using Live Gemini AI
    and matches them against the store's live Firestore inventory.
    """
    _CACHE: Dict[str, List[RegionalFestivalEvent]] = {}

    BUILTIN_REGIONAL_FESTIVALS: Dict[str, List[Dict[str, Any]]] = {
        "karnataka": [
            {
                "id": "EVT_MYSURU_DASARA",
                "name": "Mysuru Dasara & Vijayadashami (Nada Habba)",
                "date_window": "Oct 16 - Oct 22, 2026",
                "status": "UPCOMING",
                "key_items": ["Pure Cow Ghee", "Sweets & Gulab Jamun", "Puffed Rice (Pori)", "Ash Gourd (Kumbalakai)", "Puja Camphor & Cotton Wicks", "California Almonds"],
                "demand_lift_pct": 125.0,
                "icon": "",
                "description": "Karnataka's state festival (Nada Habba). Cultural processions, Ayudha Puja vehicle blessings, and family sweet preparations across Bengaluru and Mysuru.",
                "tradition_notes": "Ayudha Puja is celebrated in every shop, commercial kitchen, and household with puffed rice (pori) and jaggery; Dasara feasts trigger huge demand for pure ghee to make Mysore Pak, Holige, and Payasa.",
                "advance_procurement_window": "T-14 Days: Restock Cow Ghee tins, Sweets cartons, and Puffed Rice before distributor festive price hikes.",
                "promo_launch_window": "T-7 Days: Launch 'Mysuru Dasara Royal Feast & Sweet Hamper' via WhatsApp Broadcast.",
                "clearance_window": "T+2 Days: Liquidate remaining festive sweets and pooja items at cost price.",
                "recommended_promo_type": "FESTIVE_CELEBRATION_HAMPER",
                "suggested_combo_title": "Mysuru Dasara Royal Feast & Ghee Duo"
            },
            {
                "id": "EVT_DEEPAVALI_SOUTH",
                "name": "Diwali / Deepavali & Naraka Chaturdashi",
                "date_window": "Oct 24 - Oct 29, 2026",
                "status": "UPCOMING",
                "key_items": ["Clay Diyas & Deepas", "Pure Cow Ghee", "Gulab Jamun & Sweets", "California Almonds", "Puja Camphor & Cotton Wicks"],
                "demand_lift_pct": 140.0,
                "icon": "",
                "description": "Peak celebration season across Karnataka. High surge in Clay Deepas and Pure Cow Ghee for festive lighting and sweet-making.",
                "tradition_notes": "Deepavali in Karnataka centers on dawn oil baths, lighting clay deepas at dusk, and gifting home-made sweets.",
                "advance_procurement_window": "T-14 Days: Order Clay Diyas and Cow Ghee cartons before distributor festival price hikes.",
                "promo_launch_window": "T-7 Days: Early-Bird Festive Gift Hamper (Ghee + Dry Fruits + Sweets) via WhatsApp.",
                "clearance_window": "T+2 Days: Clear remaining earthen diyas and sweet boxes at cost price to prevent 100% loss.",
                "recommended_promo_type": "FESTIVE_CELEBRATION_HAMPER",
                "suggested_combo_title": "Deepavali Shubh Deepam & Sweet Hamper"
            },
            {
                "id": "EVT_UGADI_KANNADA",
                "name": "Ugadi (Kannada New Year)",
                "date_window": "Mar 28 - Apr 2, 2027",
                "status": "UPCOMING",
                "key_items": ["Organic Jaggery (Bella)", "Raw Mangoes", "Sunflower Oil", "Pure Cow Ghee", "Semolina (Rava/Maida)", "Puja Camphor"],
                "demand_lift_pct": 75.0,
                "icon": "",
                "description": "New Year celebration with Bevu-Bella (neem & jaggery) and holige / obbattu preparation in every household.",
                "tradition_notes": "Symbolic tasting of bittersweet flavors representing life's experiences, and large-scale cooking of festive sweets like Obbattu / Holige requiring high ghee and maida.",
                "advance_procurement_window": "T-10 Days: Stock bulk organic jaggery, maida, and pure ghee.",
                "promo_launch_window": "T-5 Days: 'Ugadi Sweet-Making Essentials Kit' bundle.",
                "clearance_window": "T+2 Days: Clear seasonal jaggery blocks and perishable sweets.",
                "recommended_promo_type": "ANCHOR_MARGIN_BOOSTER",
                "suggested_combo_title": "Ugadi Obbattu Sweet-Maker Kit"
            }
        ],
        "maharashtra": [
            {
                "id": "EVT_DIWALI_MH",
                "name": "Diwali Lakshmi Pujan & Faral",
                "date_window": "Oct 24 - Oct 30, 2026",
                "status": "UPCOMING",
                "key_items": ["Pure Cow Ghee", "Rava & Maida", "Poha (Flattened Rice)", "California Almonds", "Sunflower Cooking Oil", "Gulab Jamun"],
                "demand_lift_pct": 135.0,
                "icon": "",
                "description": "Traditional preparation of Diwali Faral (Chakli, Karanji, Ladoo, Shankarpali) across Maharashtra homes.",
                "tradition_notes": "Making home Faral requires large quantities of oil for deep frying and ghee for rich festive sweets.",
                "advance_procurement_window": "T-14 Days: Stock high-capacity Sunflower Oil cans and Pure Ghee tins.",
                "promo_launch_window": "T-7 Days: 'Diwali Faral Sweet & Savory Kit' via WhatsApp.",
                "clearance_window": "T+2 Days: Clear remaining sweet packs.",
                "recommended_promo_type": "FESTIVE_CELEBRATION_HAMPER",
                "suggested_combo_title": "Maha Diwali Faral Sweet & Ghee Hamper"
            },
            {
                "id": "EVT_GUDI_PADWA",
                "name": "Gudi Padwa (Marathi New Year)",
                "date_window": "Mar 29 - Apr 1, 2027",
                "status": "UPCOMING",
                "key_items": ["Pure Cow Ghee", "Shrikhand", "Puri Atta", "Organic Jaggery", "Puja Camphor"],
                "demand_lift_pct": 80.0,
                "icon": "",
                "description": "Marathi New Year with raising the sacred Gudi flag and family feasts of Puri-Shrikhand and Puran Poli.",
                "tradition_notes": "Every household prepares Puran Poli or buys Shrikhand with pure ghee and jaggery.",
                "advance_procurement_window": "T-10 Days: Stock Shrikhand tubs, chana dal, jaggery, and ghee.",
                "promo_launch_window": "T-4 Days: 'Gudi Padwa Prosperity Pack'.",
                "clearance_window": "T+2 Days: Clear seasonal sweets.",
                "recommended_promo_type": "ANCHOR_MARGIN_BOOSTER",
                "suggested_combo_title": "Gudi Padwa Shrikhand & Ghee Celebration Pack"
            },
            {
                "id": "EVT_GANESH_UTSAV_MH",
                "name": "Ganesh Utsav (Ganeshotsav)",
                "date_window": "Aug 27 - Sep 5, 2027",
                "status": "UPCOMING",
                "key_items": ["Modak Flour (Peeth)", "Pure Cow Ghee", "Organic Jaggery (Gul)", "Dry Fruits", "Puja Dhoop & Agarbatti", "Cardamom"],
                "demand_lift_pct": 150.0,
                "icon": "",
                "description": "Maharashtra's premier 10-day cultural festival. Massive demand for Ukadiche Modak ingredients and temple puja essentials in Mumbai & Pune.",
                "tradition_notes": "Ukadiche Modak preparation in every household; Ganesh pandals distribute huge quantities of laddoos and prasad.",
                "advance_procurement_window": "T-14 Days: Restock ghee tins, modak flour, and dry fruit cartons.",
                "promo_launch_window": "T-7 Days: 'Bappa Moraya Modak Celebration Kit'.",
                "clearance_window": "T+2 Days: Liquidate excess puja supplies.",
                "recommended_promo_type": "FESTIVE_CELEBRATION_HAMPER",
                "suggested_combo_title": "Bappa Moraya Modak & Ghee Duo"
            }
        ],
        "bengal": [
            {
                "id": "EVT_DURGA_PUJA",
                "name": "Durga Puja & Bijoya Dashami (Pujo'r Maha Utsav)",
                "date_window": "Oct 15 - Oct 20, 2026",
                "status": "UPCOMING",
                "key_items": ["Mustard Oil (Kachi Ghani)", "Basmati Rice", "Traditional Sweets (Rasgulla & Sandesh)", "Pure Cow Ghee", "California Almonds", "Spices & Panch Phoron"],
                "demand_lift_pct": 160.0,
                "icon": "",
                "description": "Bengal's biggest socio-cultural festival. 5 days of pandal-hopping, grand community feasts, and Bijoya gifting.",
                "tradition_notes": "Bhog offerings, grand family meals, and Bijoya Dashami sweet exchange where every guest is served mishti.",
                "advance_procurement_window": "T-15 Days: Heavy stocking of Mustard Oil tins, Basmati rice, and Ghee.",
                "promo_launch_window": "T-7 Days: 'Pujo Maha Bhog & Sweet Gifting Box'.",
                "clearance_window": "T+2 Days: Post-Bijoya markdown of perishable sweet tins.",
                "recommended_promo_type": "FESTIVE_CELEBRATION_HAMPER",
                "suggested_combo_title": "Sharod Utsav Bhog & Sweet Box"
            },
            {
                "id": "EVT_KALI_PUJA",
                "name": "Kali Puja & Shyama Puja",
                "date_window": "Oct 25 - Oct 29, 2026",
                "status": "UPCOMING",
                "key_items": ["Earthen Pradips (Diyas)", "Mustard Oil for Lamps", "Pure Cow Ghee", "Sweets & Gulab Jamun", "Puja Camphor & Dhoop"],
                "demand_lift_pct": 120.0,
                "icon": "",
                "description": "Illumination of homes with pradips and midnight puja rituals across Kolkata and West Bengal.",
                "tradition_notes": "14 earthen lamps (Choddo Saak & Choddo Pradip) lit before Kali Puja; high consumption of mustard oil for clay pradips.",
                "advance_procurement_window": "T-10 Days: Stock clay pradips and lamp oil.",
                "promo_launch_window": "T-5 Days: 'Kali Puja Pradip & Sweet Lighting Duo'.",
                "clearance_window": "T+2 Days: Liquidate leftover terracotta lamps.",
                "recommended_promo_type": "FESTIVE_CELEBRATION_HAMPER",
                "suggested_combo_title": "Kali Puja Pradip & Pure Ghee Saver"
            },
            {
                "id": "EVT_POILA_BOISHAKH",
                "name": "Poila Boishakh (Noboborsho & Haal Khata)",
                "date_window": "Apr 14 - Apr 16, 2027",
                "status": "UPCOMING",
                "key_items": ["Traditional Sweets", "Beverages & Cold Drinks", "Premium Tea", "Cooking Oil", "Gifting Dry Fruits"],
                "demand_lift_pct": 70.0,
                "icon": "",
                "description": "Bengali New Year and Haal Khata opening day in commercial retail and residential areas.",
                "tradition_notes": "Shoppers visit local retail stores to clear annual accounts and receive sweet boxes and cold drinks as goodwill.",
                "advance_procurement_window": "T-7 Days: Procure sweet gift boxes and beverage crates.",
                "promo_launch_window": "T-3 Days: 'Noboborsho Haal Khata Greeting Box'.",
                "clearance_window": "T+2 Days: Clear open beverage inventory.",
                "recommended_promo_type": "ANCHOR_MARGIN_BOOSTER",
                "suggested_combo_title": "Noboborsho Sweet & Tea Hospitality Pack"
            }
        ],
        "tamil": [
            {
                "id": "EVT_KARTHIGAI_DEEPAM_TN",
                "name": "Karthigai Deepam (Festival of Lamps)",
                "date_window": "Nov 22 - Nov 25, 2026",
                "status": "UPCOMING",
                "key_items": ["Clay Agal Vilakku (Lamps)", "Sesame Gingelly Oil", "Cotton Wicks", "Puffed Rice (Pori)", "Jaggery (Vellam)"],
                "demand_lift_pct": 85.0,
                "icon": "",
                "description": "Evening lighting across Tamil homes and temples; making Nel Pori Urundai sweets.",
                "tradition_notes": "Rows of terracotta lamps lit with gingelly oil, and distribution of sweet puffed rice balls.",
                "advance_procurement_window": "T-10 Days: Stock sesame lamp oil and agal vilakkus.",
                "promo_launch_window": "T-5 Days: 'Karthigai Deepam Vilakku & Oil Kit'.",
                "clearance_window": "T+2 Days: Liquidate leftover earthen lamps.",
                "recommended_promo_type": "VOLUME_TIER_SLAB",
                "suggested_combo_title": "Karthigai Deepam Vilakku & Gingelly Oil Duo"
            },
            {
                "id": "EVT_PONGAL_TN",
                "name": "Thai Pongal & Makar Sankranti",
                "date_window": "Jan 13 - Jan 17, 2027",
                "status": "UPCOMING",
                "key_items": ["Raw Rice (Pacharisi)", "Organic Jaggery (Vellam)", "Pure Cow Ghee", "Cashews & Dry Fruits", "Cardamom (Elachi)", "Cooking Sunflower Oil"],
                "demand_lift_pct": 145.0,
                "icon": "",
                "description": "Tamil harvest festival celebrating agricultural abundance. Boiling sweet Sakkarai Pongal in fresh pots.",
                "tradition_notes": "Sakkarai Pongal requires raw rice, heavy jaggery, pure cow ghee, and toasted cashews in every Tamil home.",
                "advance_procurement_window": "T-14 Days: Restock Vellam (jaggery), Pacharisi (raw rice), and Ghee.",
                "promo_launch_window": "T-7 Days: 'Thai Pongal Harvest Sakkarai Kit'.",
                "clearance_window": "T+2 Days: Clear open jaggery blocks.",
                "recommended_promo_type": "FESTIVE_CELEBRATION_HAMPER",
                "suggested_combo_title": "Thai Pongal Sakkarai Ghee & Jaggery Box"
            },
            {
                "id": "EVT_TAMIL_PUTHANDU",
                "name": "Puthandu (Tamil New Year)",
                "date_window": "Apr 13 - Apr 15, 2027",
                "status": "UPCOMING",
                "key_items": ["Raw Mangoes", "Organic Jaggery", "Pure Cow Ghee", "Payasam Vermicelli", "Cashews & Raisins"],
                "demand_lift_pct": 90.0,
                "icon": "",
                "description": "Tamil New Year celebrated with Manga Pachadi and festive family feasts.",
                "tradition_notes": "Households prepare sweet, sour, and bitter Manga Pachadi alongside rich ghee payasam.",
                "advance_procurement_window": "T-10 Days: Stock jaggery, vermicelli, cashews, and ghee.",
                "promo_launch_window": "T-5 Days: 'Puthandu Prosperity Payasam Kit'.",
                "clearance_window": "T+2 Days: Clear remaining festive sweet packs.",
                "recommended_promo_type": "ANCHOR_MARGIN_BOOSTER",
                "suggested_combo_title": "Puthandu Payasam & Pure Ghee Pack"
            }
        ],
        "gujarat": [
            {
                "id": "EVT_NAVRATRI_GUJ",
                "name": "Sharad Navratri & Bestu Varas",
                "date_window": "Oct 15 - Oct 29, 2026",
                "status": "UPCOMING",
                "key_items": ["Fasting Atta (Singoda/Rajgira)", "Sabudana", "Pure Cow Ghee", "California Almonds", "Rock Salt (Sendha Namak)", "Energy Snacks"],
                "demand_lift_pct": 130.0,
                "icon": "",
                "description": "Gujarat's Garba festivities and Gujarati New Year (Bestu Varas) family gifting.",
                "tradition_notes": "High demand for Upvas ingredients (Sabudana, Singoda, Dry Fruits, Ghee) and New Year dry fruit boxes.",
                "advance_procurement_window": "T-12 Days: Stock bulk Sabudana, dry fruits, and Farali flours.",
                "promo_launch_window": "T-6 Days: 'Navratri & Bestu Varas Ghee & Dry Fruit Hamper'.",
                "clearance_window": "T+2 Days: Markdown excess fasting flour.",
                "recommended_promo_type": "FESTIVE_CELEBRATION_HAMPER",
                "suggested_combo_title": "Navratri Farali Ghee & Dry Fruit Pack"
            },
            {
                "id": "EVT_UTTARAYAN_GUJ",
                "name": "Uttarayan (Makar Sankranti & Kite Festival)",
                "date_window": "Jan 13 - Jan 15, 2027",
                "status": "UPCOMING",
                "key_items": ["Sesame Seeds (Til)", "Organic Jaggery (Gur)", "Peanuts", "Undhiyu Spices", "Pure Cow Ghee", "Chikki Snacks"],
                "demand_lift_pct": 110.0,
                "icon": "",
                "description": "Kite flying from rooftops, eating Undhiyu and Til Chikki across Ahmedabad, Surat, and Vadodara.",
                "tradition_notes": "Til-gud chikkis and winter spices spike rapidly for 48 hours of rooftop celebrations.",
                "advance_procurement_window": "T-10 Days: Stock sesame seeds, jaggery, and peanuts.",
                "promo_launch_window": "T-5 Days: 'Uttarayan Rooftop Chikki & Spice Kit'.",
                "clearance_window": "T+2 Days: Liquidate leftover chikkis at 25% off.",
                "recommended_promo_type": "ANCHOR_MARGIN_BOOSTER",
                "suggested_combo_title": "Uttarayan Chikki & Ghee Fest Pack"
            },
            {
                "id": "EVT_JANMASHTAMI_GUJ",
                "name": "Janmashtami Lok Mela & Farali Feast",
                "date_window": "Aug 24 - Aug 26, 2027",
                "status": "UPCOMING",
                "key_items": ["Pure Cow Ghee", "Makhan & Dairy", "Dry Fruits & Almonds", "Poha", "Sugar & Sweets"],
                "demand_lift_pct": 95.0,
                "icon": "",
                "description": "Grand Janmashtami celebrations across Saurashtra and Gujarat with Panjiri and sweet preparation.",
                "tradition_notes": "Households prepare dairy-rich prasad, Gopalkala, and dry-fruit sweets.",
                "advance_procurement_window": "T-10 Days: Stock pure cow ghee and almonds.",
                "promo_launch_window": "T-5 Days: 'Janmashtami Prasad & Ghee Combo'.",
                "clearance_window": "T+2 Days: Clear perishable dairy sweets.",
                "recommended_promo_type": "FESTIVE_CELEBRATION_HAMPER",
                "suggested_combo_title": "Janmashtami Pure Ghee & Almond Box"
            }
        ],
        "kerala": [
            {
                "id": "EVT_VISHU_KERALA",
                "name": "Vishu (Malayalam New Year & Kani Feast)",
                "date_window": "Apr 14 - Apr 16, 2027",
                "status": "UPCOMING",
                "key_items": ["Matta Rice", "Pure Coconut Oil", "Organic Jaggery", "Pure Cow Ghee", "Payasam Mix", "Puja Camphor"],
                "demand_lift_pct": 85.0,
                "icon": "",
                "description": "Malayalam New Year marking new beginnings with Vishukkani darshan and Vishu Sadya feasting.",
                "tradition_notes": "Every home prepares Vishu Sadya including sweet Vishu Kanji and Payasam requiring pure ghee, jaggery, and coconut oil.",
                "advance_procurement_window": "T-8 Days: Restock Coconut Oil cans, Matta Rice, and Pure Ghee.",
                "promo_launch_window": "T-4 Days: 'Vishu Shubh Kani Sadya Hamper'.",
                "clearance_window": "T+2 Days: Liquidate leftover festival sweets.",
                "recommended_promo_type": "ANCHOR_MARGIN_BOOSTER",
                "suggested_combo_title": "Vishu Shubh Kani Sadya Hamper"
            },
            {
                "id": "EVT_ONAM_KERALA",
                "name": "Onam (Thiruvonam & Grand Sadya Feast)",
                "date_window": "Aug 28 - Sep 5, 2027",
                "status": "UPCOMING",
                "key_items": ["Pure Coconut Oil", "Banana Chips (Nendran)", "Matta Rice", "Organic Jaggery (Sharkkara)", "Payasam Mix", "Pure Cow Ghee", "Cashews"],
                "demand_lift_pct": 150.0,
                "icon": "",
                "description": "Kerala's harvest festival welcoming King Mahabali. 26-dish Grand Sadya feast cooked in every home.",
                "tradition_notes": "Massive consumption of pure coconut oil for frying banana chips, and ghee + jaggery for sweet Ada Pradhaman payasam.",
                "advance_procurement_window": "T-14 Days: Restock Coconut Oil cans, Jaggery, and Payasam ingredients.",
                "promo_launch_window": "T-7 Days: 'Thiruvonam Grand Sadya Feast Hamper'.",
                "clearance_window": "T+2 Days: Clear open jaggery and perishable snacks.",
                "recommended_promo_type": "FESTIVE_CELEBRATION_HAMPER",
                "suggested_combo_title": "Onam Sadya Payasam & Ghee Feast Duo"
            },
            {
                "id": "EVT_CHRISTMAS_KERALA",
                "name": "Kerala Christmas & Plum Cake Season",
                "date_window": "Dec 18 - Dec 31, 2026",
                "status": "UPCOMING",
                "key_items": ["Plum Cakes & Bakery", "Cashews & Almonds", "Spices (Cinnamon & Cloves)", "Pure Cow Ghee", "Beverages & Tea"],
                "demand_lift_pct": 115.0,
                "icon": "",
                "description": "Year-end baking, plum cake gifting, and family feasts across Kochi, Trivandrum, and Kozhikode.",
                "tradition_notes": "Rich fruit cakes, dry fruits, spices, and festive breakfast stews drive high grocery basket values.",
                "advance_procurement_window": "T-14 Days: Stock bakery tins, dry fruits, and spices.",
                "promo_launch_window": "T-7 Days: 'Christmas Baking & Dry Fruit Hamper'.",
                "clearance_window": "T+3 Days: Clear seasonal cake boxes.",
                "recommended_promo_type": "FESTIVE_CELEBRATION_HAMPER",
                "suggested_combo_title": "Festive Bakery & Dry Fruit Celebration Pack"
            }
        ],
        "delhi": [
            {
                "id": "EVT_DIWALI_NORTH",
                "name": "Diwali & Dhanteras (Maha Utsav)",
                "date_window": "Oct 24 - Oct 29, 2026",
                "status": "UPCOMING",
                "key_items": ["Pure Cow Ghee", "Sweets & Gulab Jamun", "California Almonds", "Mustard Cooking Oil", "Puja Camphor & Diyas"],
                "demand_lift_pct": 140.0,
                "icon": "",
                "description": "North India's largest festival of lights and wealth. Extravagant family gifting of dry fruits and sweets.",
                "tradition_notes": "Corporate and family gifting of dry fruit hampers and sweet boxes; lighting earthen diyas with mustard oil.",
                "advance_procurement_window": "T-14 Days: Stock Almond gift boxes and Pure Ghee tins.",
                "promo_launch_window": "T-7 Days: 'Diwali Shubh Labh Dry Fruit & Sweet Hamper'.",
                "clearance_window": "T+2 Days: Clear sweet boxes at cost to avoid expiry.",
                "recommended_promo_type": "FESTIVE_CELEBRATION_HAMPER",
                "suggested_combo_title": "Diwali Shubh Labh Ghee & Dry Fruit Box"
            },
            {
                "id": "EVT_LOHRI_NORTH",
                "name": "Lohri & Makar Sankranti Winter Harvest",
                "date_window": "Jan 11 - Jan 15, 2027",
                "status": "UPCOMING",
                "key_items": ["Sesame & Gur Rewari", "Peanuts & Dry Fruits", "Pure Cow Ghee", "Makki Atta", "Premium Tea"],
                "demand_lift_pct": 105.0,
                "icon": "",
                "description": "Winter bonfire festival across Delhi-NCR, Punjab, and Haryana driving massive demand for dry fruits, jaggery, and winter staples.",
                "tradition_notes": "Families gather around Lohri bonfires sharing Til-Rewari, Gajak, peanuts, and festive winter meals.",
                "advance_procurement_window": "T-10 Days: Stock jaggery, dry fruits, and winter tea packs.",
                "promo_launch_window": "T-5 Days: 'Lohri Winter Warmth Tea & Dry Fruit Duo'.",
                "clearance_window": "T+2 Days: Clear seasonal Gajak boxes.",
                "recommended_promo_type": "ANCHOR_MARGIN_BOOSTER",
                "suggested_combo_title": "Lohri Winter Dry Fruit & Tea Saver"
            },
            {
                "id": "EVT_HOLI_NORTH",
                "name": "Holi (Festival of Colors)",
                "date_window": "Mar 14 - Mar 17, 2027",
                "status": "UPCOMING",
                "key_items": ["Khoya / Mawa & Maida (Gujiya Ingredients)", "Pure Cow Ghee", "Refined Sunflower Oil", "Thandai Syrup", "Dry Fruits"],
                "demand_lift_pct": 110.0,
                "icon": "",
                "description": "Festival of colors celebrated with homemade Gujiyas, Thandai, and savory snacks.",
                "tradition_notes": "Making traditional Gujiyas at home requires heavy ghee, maida, and frying oil.",
                "advance_procurement_window": "T-10 Days: Restock cooking oil and pure ghee.",
                "promo_launch_window": "T-5 Days: 'Holi Gujiya Sweet-Maker Kit'.",
                "clearance_window": "T+2 Days: Clear Thandai syrups.",
                "recommended_promo_type": "ANCHOR_MARGIN_BOOSTER",
                "suggested_combo_title": "Holi Gujiya Sweet & Thandai Duo"
            }
        ],
        "california": [
            {
                "id": "EVT_CA_THANKSGIVING_2026",
                "name": "Thanksgiving & Holiday Feasting",
                "date_window": "Nov 19 - Nov 26, 2026",
                "status": "UPCOMING",
                "key_items": ["Whole Turkeys & Poultry", "Baking Mixes & Butter", "Cranberry Sauces & Jams", "Sweet Potatoes", "Sparkling Cider & Drinks", "California Almonds"],
                "demand_lift_pct": 215.0,
                "icon": "",
                "description": "Major family feasting holiday driving retail volume across center-store baking goods, fresh produce, and poultry in California supermarkets.",
                "tradition_notes": "California consumers incorporate fresh local produce, sweet potatoes, and stuffing with high baking butter and nut demand.",
                "advance_procurement_window": "T-21 Days: Lock in poultry contracts, bulk butter, and roasting seasonings.",
                "promo_launch_window": "T-10 Days: Launch 'Thanksgiving Family Feast Essentials' end-cap bundle.",
                "clearance_window": "T+2 Days: Liquidate remaining fresh poultry and holiday bakery items.",
                "recommended_promo_type": "FESTIVE_CELEBRATION_HAMPER",
                "suggested_combo_title": "Golden State Thanksgiving Feast Pack"
            },
            {
                "id": "EVT_CA_CHRISTMAS_2026",
                "name": "Christmas & Holiday Gifting Season",
                "date_window": "Dec 18, 2026 - Jan 2, 2027",
                "status": "UPCOMING",
                "key_items": ["Chocolates & Cookies", "California Premium Almonds & Nuts", "Fruit Juices & Sparkling Cider", "Gifting Hampers", "Artisanal Cheese & Butter"],
                "demand_lift_pct": 190.0,
                "icon": "",
                "description": "High-volume corporate and family gifting, holiday party snacking, and celebratory entertaining across California retail stores.",
                "tradition_notes": "Shoppers prepare holiday charcuterie boards, gift hampers of premium nuts and confectionery, and family holiday breakfasts.",
                "advance_procurement_window": "T-18 Days: Stock holiday confection packaging, premium nuts, and festive beverages.",
                "promo_launch_window": "T-10 Days: Launch 'Holiday Cheer Gifting Hamper' digital catalog.",
                "clearance_window": "T+3 Days: Markdown post-Christmas seasonal gift sets at 30% off.",
                "recommended_promo_type": "FESTIVE_CELEBRATION_HAMPER",
                "suggested_combo_title": "Holiday Cheer & Gifting Hamper"
            },
            {
                "id": "EVT_CA_SUPERBOWL_2027",
                "name": "Super Bowl & Game Day Weekend",
                "date_window": "Feb 7 - Feb 14, 2027",
                "status": "UPCOMING",
                "key_items": ["Tortilla Chips & Snacks", "Dipping Sauces & Salsas", "Cold Beverages & Soda", "Pretzels & Mixed Nuts", "Party Packs"],
                "demand_lift_pct": 175.0,
                "icon": "",
                "description": "Largest weekend snack and beverage shopping peak. High velocity on party-size snacks, chips, and refreshing beverages.",
                "tradition_notes": "Game Day gatherings demand shareable finger foods, salty snacks, dipping platters, and convenient party bundles.",
                "advance_procurement_window": "T-14 Days: Build bulk floor displays of chips, snacks, and beverage cases.",
                "promo_launch_window": "T-7 Days: Launch 'Game Day Ultimate Snacking Pack' promotion.",
                "clearance_window": "T+2 Days: Clear single-serve overflow snacks.",
                "recommended_promo_type": "ANCHOR_MARGIN_BOOSTER",
                "suggested_combo_title": "Touchdown Game Day Snacking Duo"
            }
        ],
        "australia": [
            {
                "id": "EVT_AU_CHRISTMAS_SUMMER_2026",
                "name": "Christmas & Boxing Day Summer Feasting",
                "date_window": "Dec 18 - Dec 28, 2026",
                "status": "UPCOMING",
                "key_items": ["Glazed Ham", "Fresh Prawns & Seafood", "Pavlova Ingredients", "Sparkling Drinks & Wine", "California Almonds", "Summer Fruits"],
                "demand_lift_pct": 195.0,
                "icon": "",
                "description": "Peak warm-weather holiday feasting across Sydney, Melbourne, and Brisbane, centered on Christmas seafood lunches, ham platters, and Boxing Day cricket celebrations.",
                "tradition_notes": "Aussie households celebrate Christmas in mid-summer with cold prawns, BBQ meats, pavlova with fresh fruit, and premium confectionery.",
                "advance_procurement_window": "T-21 Days: Lock in seafood and poultry allocations, bulk beverages, and festive confectionery.",
                "promo_launch_window": "T-10 Days: Launch 'Aussie Summer Christmas Seafood & Hamper' catalog.",
                "clearance_window": "T+2 Days: Liquidate remaining seasonal gift sets.",
                "recommended_promo_type": "FESTIVE_CELEBRATION_HAMPER",
                "suggested_combo_title": "Aussie Summer Holiday Feast & Pavlova Pack"
            },
            {
                "id": "EVT_AU_AUSTRALIA_DAY_2027",
                "name": "Australia Day Long Weekend & Great Aussie BBQ",
                "date_window": "Jan 22 - Jan 27, 2027",
                "status": "UPCOMING",
                "key_items": ["BBQ Sausages & Snags", "Burger Patties", "Potato Chips & Dips", "Cold Soft Drinks & Beer", "California Almonds", "Baking Buns"],
                "demand_lift_pct": 170.0,
                "icon": "",
                "description": "Nationwide summer celebration with backyard barbecues, beach gatherings, and community events driving high supermarket basket sizes in snacks and meat.",
                "tradition_notes": "Backyard barbecues are an iconic Australian ritual, triggering surges in burger buns, seasonings, dips, crisps, and refreshing beverages.",
                "advance_procurement_window": "T-14 Days: Build bulk end-cap displays of soft drinks, crisps, and BBQ grilling essentials.",
                "promo_launch_window": "T-7 Days: Launch 'Great Aussie BBQ & Thirst Quencher' bundle.",
                "clearance_window": "T+2 Days: Markdown excess perishable party snacks.",
                "recommended_promo_type": "ANCHOR_MARGIN_BOOSTER",
                "suggested_combo_title": "Great Aussie BBQ & Snack Sizzler Pack"
            },
            {
                "id": "EVT_AU_EASTER_2027",
                "name": "Easter Long Weekend & Autumn Feasting",
                "date_window": "Mar 25 - Mar 30, 2027",
                "status": "UPCOMING",
                "key_items": ["Hot Cross Buns", "Easter Chocolates", "Roast Lamb Essentials", "Butter & Bakery Goods", "Coffee & Tea"],
                "demand_lift_pct": 160.0,
                "icon": "",
                "description": "Autumn 4-day long weekend holiday driving major household grocery shopping in traditional hot cross buns, chocolates, and family roast dinners.",
                "tradition_notes": "Families gather for hot cross bun breakfasts with butter, chocolate gifting for children, and Sunday roast lamb dinners.",
                "advance_procurement_window": "T-18 Days: Restock premium confectionery, baking goods, and roasting ingredients.",
                "promo_launch_window": "T-10 Days: Launch 'Easter Morning Buns & Chocolate Hamper'.",
                "clearance_window": "T+1 Day: Rapid markdown of seasonal Easter eggs.",
                "recommended_promo_type": "FESTIVE_CELEBRATION_HAMPER",
                "suggested_combo_title": "Easter Morning Hot Cross Buns & Choco Box"
            }
        ]
    }

    @classmethod
    def _normalize_region_and_country(cls, region: str, country: Optional[str] = None) -> Tuple[str, str]:
        r = (region or "Karnataka").strip()
        c = (country or "").strip()

        if "," in r:
            parts = r.split(",", 1)
            r = parts[0].strip()
            c = parts[1].strip()

        r_lower = r.lower()
        c_lower = c.lower()

        words = set(re.findall(r'\b[a-zA-Z]+\b', r_lower))

        # 1. Explicit Australia check
        if any(w in r_lower for w in ["australia", "sydney", "melbourne", "brisbane", "perth", "adelaide", "queensland", "victoria"]) or c_lower in ["australia", "au"]:
            clean_au = re.sub(r'\b(australia)\b', '', r, flags=re.IGNORECASE).strip()
            return (clean_au.title() if clean_au else "Australia"), "Australia"

        # 2. Explicit UK check
        if any(w in r_lower for w in ["united kingdom", "london", "england", "scotland", "wales"]) or "uk" in words or c_lower in ["uk", "united kingdom", "great britain", "gb"]:
            clean_uk = re.sub(r'\b(uk|united kingdom|england)\b', '', r, flags=re.IGNORECASE).strip()
            return (clean_uk.title() if clean_uk else "United Kingdom"), "United Kingdom"

        # 3. Explicit Canada check
        if any(w in r_lower for w in ["canada", "toronto", "vancouver", "montreal", "ontario", "quebec", "alberta", "calgary"]) or c_lower in ["canada", "ca"]:
            clean_ca = re.sub(r'\b(canada)\b', '', r, flags=re.IGNORECASE).strip()
            return (clean_ca.title() if clean_ca else "Canada"), "Canada"

        # 4. Explicit US check (Word-boundary safe, avoiding substring 'us' inside 'australia'!)
        us_state_names = [
            "california", "texas", "florida", "new york", "illinois", "pennsylvania", "ohio",
            "georgia", "north carolina", "michigan", "new jersey", "virginia", "washington",
            "arizona", "massachusetts", "tennessee", "indiana", "missouri", "maryland", "wisconsin",
            "colorado", "minnesota", "south carolina", "alabama", "louisiana", "kentucky", "oregon",
            "oklahoma", "connecticut", "utah", "iowa", "nevada", "arkansas", "mississippi", "kansas",
            "new mexico", "nebraska", "idaho", "west virginia", "hawaii", "new hampshire", "maine",
            "montana", "rhode island", "delaware", "south dakota", "north dakota", "alaska", "vermont",
            "wyoming", "united states", "los angeles", "san francisco", "bay area",
            "san diego", "seattle", "chicago", "boston", "miami"
        ]
        is_us = (
            any(w in r_lower for w in us_state_names)
            or bool({"us", "usa", "america"}.intersection(words))
            or c_lower in ["usa", "us", "america", "united states"]
        )
        if is_us:
            clean_us = re.sub(r'\b(usa|us|united states|america)\b', '', r, flags=re.IGNORECASE).strip()
            return (clean_us.title() if clean_us else "United States"), "United States"

        # 5. Global countries (anywhere around the world)
        global_countries = {
            "germany": "Germany", "france": "France", "japan": "Japan", "singapore": "Singapore",
            "new zealand": "New Zealand", "uae": "United Arab Emirates", "dubai": "United Arab Emirates",
            "italy": "Italy", "spain": "Spain", "brazil": "Brazil", "mexico": "Mexico",
            "south africa": "South Africa", "ireland": "Ireland", "netherlands": "Netherlands",
            "switzerland": "Switzerland", "sweden": "Sweden", "norway": "Norway"
        }
        for kw, country_name in global_countries.items():
            if kw in r_lower or kw in c_lower:
                clean_name = re.sub(rf'\b({kw})\b', '', r, flags=re.IGNORECASE).strip()
                return (clean_name.title() if clean_name else country_name), country_name

        # 6. Indian regions
        indian_regions = [
            "karnataka", "maharashtra", "bengal", "tamil", "gujarat", "kerala", "delhi", "punjab",
            "rajasthan", "haryana", "uttar pradesh", "bihar", "odisha", "assam", "bengaluru", "mumbai",
            "delhi", "kolkata", "chennai", "hyderabad", "pune", "ahmedabad", "jaipur"
        ]
        if any(w in r_lower for w in indian_regions) or c_lower in ["india", "in", "bharat"]:
            return r, "India"

        # 7. Fallback for any other custom region/country around the world
        if c:
            return r.title(), c.title()
        return r.title(), r.title()

    @classmethod
    def discover_festivals(
        cls,
        region: str = "Karnataka",
        country: str = "India",
        city: Optional[str] = None,
        force_refresh: bool = True,
        api_key: Optional[str] = None
    ) -> List[RegionalFestivalEvent]:
        """
        Generates upcoming regional festivals dynamically at the time of search using Live Gemini AI
        and matches them against the store's live inventory SKUs (without reading/storing static JSON files).
        """
        norm_region, norm_country = cls._normalize_region_and_country(region, country)
        region = norm_region
        country = norm_country

        products = StoreDataManager.load_products()
        gen_source = "LIVE_GEMINI_API"
        festivals_data = None

        # 1. If not force_refresh, only reuse stored festivals if they were generated by LIVE Gemini AI for this region
        if not force_refresh:
            stored_events = StoreDataManager.get_calendar_events(region=region)
            valid_stored = [
                e for e in stored_events
                if e.get("tradition_notes") and e.get("advance_procurement_window")
                and region.lower().split("&")[0].strip() in e.get("region", "").lower()
                and (
                    str(e.get("generation_source", "")).startswith("LIVE_")
                    or not GeminiLiveClient.is_configured(api_key)
                )
            ]
            if len(valid_stored) >= 2:
                festivals_data = valid_stored[:3]
                gen_source = valid_stored[0].get("generation_source") or "LIVE_GEMINI_API (FIRESTORE_SYNCED)"
                print(f"[DynamicFestivalEngine] [CACHE_HIT] Serving {len(festivals_data)} cached festivals for '{region}' from Firestore ({gen_source})", flush=True)

        # 2. If force_refresh (Login / Sync button / new region) or not yet stored, query Live Gemini AI
        if not festivals_data:
            print(f"[DynamicFestivalEngine] [SEARCHING_LIVE_AI] Querying Gemini Vertex AI for upcoming festivals in: Region='{region}', City='{city}', Country='{country}'...", flush=True)
            festivals_data = cls._query_gemini_festivals(region, country, city, products=products, api_key=api_key)
            if festivals_data:
                gen_source = GeminiLiveClient._LAST_USED_SOURCE
                print(f"[DynamicFestivalEngine] [LIVE_SEARCH_SUCCESS] Received {len(festivals_data)} upcoming festivals via {gen_source}", flush=True)
            else:
                festivals_data = cls._get_builtin_festivals(region, country, city)
                gen_source = "HYBRID_REGIONAL_SYNTHESIS"
                print(f"[DynamicFestivalEngine] [FALLBACK] Live AI search returned empty, used fallback: {gen_source}", flush=True)

        events: List[RegionalFestivalEvent] = []
        category_synonyms = {
            "sweet": "Sweets", "mithai": "Sweets", "modak": "Sweets", "ladoo": "Sweets", "holige": "Sweets", "obbattu": "Sweets",
            "ghee": "Dairy", "milk": "Dairy", "butter": "Dairy", "cream": "Dairy",
            "oil": "Oils", "sunflower": "Oils",
            "almond": "Dry Fruits", "nut": "Dry Fruits", "kaju": "Dry Fruits", "pistachio": "Dry Fruits",
            "tea": "Beverages", "chai": "Beverages", "coffee": "Beverages", "cider": "Beverages", "soda": "Beverages", "drink": "Beverages",
            "biscuit": "Bakery", "cookie": "Bakery", "snack": "Snacks", "chip": "Snacks", "pretzel": "Snacks",
            "masala": "Spices", "spice": "Spices", "seasoning": "Spices", "sauce": "Spices"
        }

        for d in festivals_data:
            key_items = d.get("key_items", [])
            matched_prods = []

            for item in key_items:
                item_lower = item.lower()
                tokens = [w for w in item_lower.replace("(", " ").replace(")", " ").replace("/", " ").replace("-", " ").split() if len(w) >= 3]
                for p in products:
                    p_name = p.name.lower()
                    p_cat = (p.category or "").lower()
                    direct_match = any(t in p_name or t in p_cat for t in tokens)
                    syn_match = any(k in item_lower and (k in p_name or k in p_cat or v.lower() in p_cat) for k, v in category_synonyms.items())
                    if direct_match or syn_match:
                        if not any(m["product_id"] == p.id for m in matched_prods):
                            matched_prods.append({
                                "product_id": p.id,
                                "name": p.name,
                                "category": p.category,
                                "selling_price": p.selling_price,
                                "cost_price": p.cost_price,
                                "stock_quantity": p.stock_quantity,
                                "margin_pct": round(((p.selling_price - p.cost_price) / max(1.0, p.selling_price)) * 100, 1),
                                "velocity_status": p.velocity_status,
                                "surge_lift_pct": d.get("demand_lift_pct", 75.0)
                            })

            if len(matched_prods) < 2:
                for p in products:
                    if not any(m["product_id"] == p.id for m in matched_prods):
                        matched_prods.append({
                            "product_id": p.id,
                            "name": p.name,
                            "category": p.category,
                            "selling_price": p.selling_price,
                            "cost_price": p.cost_price,
                            "stock_quantity": p.stock_quantity,
                            "margin_pct": round(((p.selling_price - p.cost_price) / max(1.0, p.selling_price)) * 100, 1),
                            "velocity_status": p.velocity_status,
                            "surge_lift_pct": d.get("demand_lift_pct", 75.0)
                        })
                    if len(matched_prods) >= 3:
                        break

            suggested_title = d.get("suggested_combo_title")
            if not suggested_title and len(matched_prods) >= 2:
                suggested_title = f"{d.get('name', 'Festive').split('(')[0].strip()} Duo: {matched_prods[0]['name'].split('(')[0].strip()} + {matched_prods[1]['name'].split('(')[0].strip()}"
            elif not suggested_title:
                suggested_title = f"{d.get('name', 'Festive').split('(')[0].strip()} Special Saver Pack"

            date_win = str(d.get("date_window", "Upcoming Festive Season")).strip()
            date_win = date_win.replace("2024", "2026").replace("2025", "2026")
            if not any(yr in date_win for yr in ["2026", "2027"]):
                early_months = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep"]
                if any(m in date_win.lower() for m in early_months):
                    date_win = f"{date_win}, 2027"
                else:
                    date_win = f"{date_win}, 2026"

            evt = RegionalFestivalEvent(
                id=d.get("id", f"EVT_{abs(hash(d.get('name', 'fest')))}"),
                name=d.get("name", "Regional Cultural Celebration"),
                region=f"{region.strip().title()}, {country.strip().title()}",
                date_window=date_win,
                status=d.get("status", "UPCOMING"),
                key_items=key_items,
                demand_lift_pct=float(d.get("demand_lift_pct", 80.0)),
                icon="",
                description=d.get("description", "Significant regional shopping demand spike for retail grocery."),
                tradition_notes=d.get("tradition_notes"),
                advance_procurement_window=d.get("advance_procurement_window"),
                promo_launch_window=d.get("promo_launch_window"),
                clearance_window=d.get("clearance_window"),
                recommended_promo_type=d.get("recommended_promo_type", "FESTIVE_CELEBRATION_HAMPER"),
                matched_inventory_items=matched_prods[:4],
                suggested_combo_title=suggested_title,
                country=country,
                city=city,
                generation_source=gen_source
            )
            events.append(evt)

        top_three = events[:3]
        try:
            StoreDataManager.save_calendar_events_batch([e.model_dump() for e in top_three])
        except Exception:
            pass
        return top_three

    @classmethod
    def _query_gemini_festivals(
        cls,
        region: str,
        country: str,
        city: Optional[str],
        products: Optional[List[Product]] = None,
        api_key: Optional[str] = None
    ) -> Optional[List[Dict[str, Any]]]:
        inv_names = [f"{p.name} ({p.category})" for p in (products or [])[:12]]
        prompt = f"""You are a specialized retail demand forecasting and cultural festival intelligence expert for grocery & retail supermarkets.
CRITICAL TEMPORAL CONSTRAINT:
- Today's date is October 15, 2026.
- ALL festival dates MUST be strictly UPCOMING from late October 2026 into calendar year 2027.
- NEVER return past years (2024 or 2025). Every `date_window` MUST explicitly include the 4-digit year 2026 or 2027.

Store Inventory Context:
{json.dumps(inv_names)}

Return EXACTLY the top 3 upcoming regional cultural festivals, public celebrations, and FMCG grocery demand surges specifically celebrated in:
Region / State / Place: {region}
Country: {country}
City / Locality: {city or region}

For EACH of the 3 festivals, provide a JSON object with:
- id: unique string e.g. "EVT_CUSTOM_01"
- name: authentic regional festival or celebration name specific to {region} (if in India in Oct/Nov, include Diwali / Deepavali or the top regional festival)
- date_window: date string in 2026 or 2027 with explicit 4-digit year (e.g. "Oct 24 - Oct 29, 2026", "Jan 13 - Jan 16, 2027")
- status: "UPCOMING"
- key_items: array of 4-6 specific retail grocery items experiencing demand surges
- demand_lift_pct: float percentage sales surge (e.g. 135.0)
- icon: "" (leave empty string for clean UI)
- description: 2-sentence explanation of the festive shopping rush in {region}
- tradition_notes: cultural context explaining why these items are consumed in {region}
- advance_procurement_window: distributor procurement timeline e.g. "T-14 Days: Restock bulk tins"
- promo_launch_window: promotion launch timeline e.g. "T-7 Days: Launch WhatsApp Broadcast"
- clearance_window: post-festival markdown timeline e.g. "T+2 Days: Sell remaining stock at cost"
- recommended_promo_type: "FESTIVE_CELEBRATION_HAMPER" or "ANCHOR_MARGIN_BOOSTER"
- suggested_combo_title: catchy promo title pairing store inventory items for {region}

Return ONLY a valid JSON array of 3 objects.
"""
        parsed = GeminiLiveClient.generate_json(prompt, override_api_key=api_key, timeout=12)
        if isinstance(parsed, list) and len(parsed) > 0:
            for item in parsed:
                n = item.get("name", "")
                if "diwali" in n.lower() and "deepavali" not in n.lower():
                    item["name"] = n.replace("Diwali", "Deepavali / Diwali")
                elif "deepavali" in n.lower() and "diwali" not in n.lower():
                    item["name"] = n.replace("Deepavali", "Deepavali / Diwali")
                dw = str(item.get("date_window", "")).strip()
                dw = dw.replace("2024", "2026").replace("2025", "2026")
                if not any(yr in dw for yr in ["2026", "2027"]):
                    early_months = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep"]
                    if any(m in dw.lower() for m in early_months):
                        dw = f"{dw}, 2027"
                    else:
                        dw = f"{dw}, 2026"
                item["date_window"] = dw
                item["icon"] = ""
            return parsed
        return None

    @classmethod
    def _get_builtin_festivals(cls, region: str, country: str, city: Optional[str] = None) -> List[Dict[str, Any]]:
        reg = region.lower()
        cntry = (country or "").lower()

        if "australia" in reg or "sydney" in reg or "melbourne" in reg or "brisbane" in reg or cntry == "australia":
            return cls.BUILTIN_REGIONAL_FESTIVALS["australia"]

        if any(w in reg for w in ["california", "los angeles", "san francisco", "bay area"]) or cntry in ["united states", "usa"]:
            return cls.BUILTIN_REGIONAL_FESTIVALS["california"]

        for k, v in cls.BUILTIN_REGIONAL_FESTIVALS.items():
            if k in reg:
                return v

        if any(w in reg for w in ["south", "bangalore", "bengaluru", "mysore", "mysuru", "karnataka"]):
            return cls.BUILTIN_REGIONAL_FESTIVALS["karnataka"]
        elif any(w in reg for w in ["mumbai", "pune", "nagpur", "nashik", "maharashtra", "west"]):
            return cls.BUILTIN_REGIONAL_FESTIVALS["maharashtra"]
        elif any(w in reg for w in ["kolkata", "bengal", "assam", "odisha", "east"]):
            return cls.BUILTIN_REGIONAL_FESTIVALS["bengal"]
        elif any(w in reg for w in ["chennai", "coimbatore", "madurai", "tamil"]):
            return cls.BUILTIN_REGIONAL_FESTIVALS["tamil"]
        elif any(w in reg for w in ["ahmedabad", "surat", "vadodara", "rajkot", "gujarat"]):
            return cls.BUILTIN_REGIONAL_FESTIVALS["gujarat"]
        elif any(w in reg for w in ["kochi", "trivandrum", "kerala", "malabar"]):
            return cls.BUILTIN_REGIONAL_FESTIVALS["kerala"]
        elif any(w in reg for w in ["delhi", "noida", "gurugram", "up", "haryana", "punjab", "rajasthan", "north"]):
            return cls.BUILTIN_REGIONAL_FESTIVALS["delhi"]

        # Dynamic custom region synthesizer for any other searched city/state/country
        place_title = region.strip().title()
        return [
            {
                "id": f"EVT_{place_title.upper().replace(' ', '_')}_DIWALI_2026",
                "name": f"{place_title} Deepavali / Diwali & Festive Shopping Rush",
                "date_window": "Oct 24 - Oct 30, 2026",
                "status": "UPCOMING",
                "key_items": ["Pure Cow Ghee", "Festive Sweets & Gulab Jamun", "California Almonds", "Sunflower Cooking Oil"],
                "demand_lift_pct": 135.0,
                "icon": "",
                "description": f"Peak annual festive grocery and gifting surge across {place_title}, driving high basket values in dairy, dry fruits, and confectionery.",
                "tradition_notes": f"Households and businesses across {place_title} stock up on pure ghee, dry fruit hampers, and sweets for family celebrations and gifting.",
                "advance_procurement_window": f"T-14 Days: Secure bulk Ghee tins and Dry Fruit cartons from {place_title} wholesale distributors.",
                "promo_launch_window": f"T-7 Days: Broadcast '{place_title} Festive Super Saver Hamper' to customer list.",
                "clearance_window": "T+2 Days: Clear remaining seasonal gift boxes at cost price.",
                "recommended_promo_type": "FESTIVE_CELEBRATION_HAMPER",
                "suggested_combo_title": f"{place_title} Festive Ghee & Dry Fruit Celebration Pack"
            },
            {
                "id": f"EVT_{place_title.upper().replace(' ', '_')}_HARVEST_2027",
                "name": f"{place_title} Winter Harvest & New Year Celebration",
                "date_window": "Jan 12 - Jan 17, 2027",
                "status": "UPCOMING",
                "key_items": ["Premium Tea", "Organic Jaggery", "Pure Cow Ghee", "Bakery Cookies & Snacks"],
                "demand_lift_pct": 95.0,
                "icon": "",
                "description": f"Regional harvest and winter family gathering week in {place_title} with elevated consumption of hot beverages, jaggery sweets, and snacks.",
                "tradition_notes": f"Winter hospitality in {place_title} centers on serving hot tea paired with cookies, dry fruits, and traditional harvest sweets.",
                "advance_procurement_window": "T-10 Days: Build buffer stock of Premium Tea and Bakery Cookies.",
                "promo_launch_window": "T-5 Days: Launch 'Winter Harvest Hospitality Duo' at checkout.",
                "clearance_window": "T+2 Days: Liquidate slow-moving snack packs via bundle discount.",
                "recommended_promo_type": "ANCHOR_MARGIN_BOOSTER",
                "suggested_combo_title": f"{place_title} Winter Tea & Cookie Value Duo"
            },
            {
                "id": f"EVT_{place_title.upper().replace(' ', '_')}_SPRING_2027",
                "name": f"{place_title} Spring Festive & Family Feast Season",
                "date_window": "Mar 14 - Mar 22, 2027",
                "status": "UPCOMING",
                "key_items": ["Refined Sunflower Oil", "Garam Masala & Spices", "Pure Cow Ghee", "Sweets"],
                "demand_lift_pct": 110.0,
                "icon": "",
                "description": f"Spring festive cooking and community gatherings across {place_title} trigger bulk pantry restocking of cooking oils, spices, and sweets.",
                "tradition_notes": f"Traditional festive feasts in {place_title} require high volumes of cooking oil, aromatic spices, and pure ghee.",
                "advance_procurement_window": "T-12 Days: Lock in wholesale rates on cooking oil and spice cartons.",
                "promo_launch_window": "T-6 Days: Launch 'Spring Kitchen Staples Saver Bundle'.",
                "clearance_window": "T+2 Days: Bundle slow-moving spices with fast-moving cooking oil.",
                "recommended_promo_type": "ANCHOR_MARGIN_BOOSTER",
                "suggested_combo_title": f"{place_title} Festive Cooking Oil & Spice Basket"
            }
        ]


class RetailCopilotAgent:
    """
    Conversational AI Copilot & Sales Growth Advisor for Retailers (Issue #8).
    Uses Live Gemini API at query time alongside econometric forecasting, price elasticity,
    and regional festival integration.
    """

    @classmethod
    def process_message(
        cls,
        message: str,
        user_margin_pct: Optional[float] = None,
        region: Optional[str] = None,
        api_key: Optional[str] = None
    ) -> ChatResponse:
        store_profile = StoreDataManager.load_profile()
        if region:
            store_profile.region = region

        msg_lower = message.lower()

        potential_regions = [
            "california", "texas", "florida", "new york", "washington", "illinois", "london", "uk", "canada", "australia",
            "karnataka", "maharashtra", "west bengal", "tamil nadu", "gujarat", "kerala", "delhi", "bengaluru", "mumbai",
            "hyderabad", "telangana", "punjab", "rajasthan", "chennai", "kolkata", "pune"
        ]
        for pr in potential_regions:
            if re.search(rf'\b{pr}\b', msg_lower):
                store_profile.region = pr.title()
                break

        norm_reg, norm_cntry = DynamicFestivalEngine._normalize_region_and_country(
            store_profile.region,
            getattr(store_profile, "country", None)
        )
        store_profile.region = norm_reg
        store_profile.country = norm_cntry

        reg_lower = (store_profile.region or "").lower()
        city_lower = (store_profile.city or "").lower()
        if "california" in reg_lower or "usa" in reg_lower or "united states" in reg_lower:
            greeting = "Hello!"
            loc_label = f"{store_profile.locality or 'Bay Area'}, California"
        elif "karnataka" in reg_lower or "south" in reg_lower or "bengaluru" in city_lower:
            greeting = "Namaskara!"
            loc_label = f"{store_profile.locality or 'Indiranagar'}, {store_profile.city or 'Bengaluru'}"
        elif "maharashtra" in reg_lower or "west" in reg_lower or "mumbai" in city_lower:
            greeting = "Namaskar!"
            loc_label = f"{store_profile.locality or 'Dadar'}, {store_profile.city or 'Mumbai'}"
        elif "bengal" in reg_lower or "east" in reg_lower or "kolkata" in city_lower:
            greeting = "Nomoshkar!"
            loc_label = f"{store_profile.locality or 'Gariahat'}, {store_profile.city or 'Kolkata'}"
        else:
            greeting = "Namaste!"
            loc_label = f"{store_profile.locality or 'Main Market'}, {store_profile.city or 'Store'}"

        # 1. Extract requested margin % from message if stated
        detected_margin = user_margin_pct
        if detected_margin is None:
            margin_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:%|percent)\s*(?:margin|profit)?', message, re.IGNORECASE)
            if margin_match:
                detected_margin = float(margin_match.group(1))
            else:
                detected_margin = store_profile.default_min_margin_pct or 18.0

        detected_margin = max(5.0, min(45.0, detected_margin))

        products = StoreDataManager.load_products()
        roi_data = InvestmentROIEngine.compute_store_roi(products, store_capital_budget=store_profile.total_working_capital_inr or 500000.0)
        regional_events = DynamicFestivalEngine.discover_festivals(
            region=store_profile.region,
            country=store_profile.country,
            city=store_profile.city,
            force_refresh=False,
            api_key=api_key
        )

        # Build structured Sales Growth Advisor summary (Issue #8)
        sales_growth_plan = {
            "region": f"{store_profile.region}, {store_profile.country}",
            "target_margin_pct": detected_margin,
            "projected_monthly_lift_inr": int(roi_data["unlocked_capital_from_promos_inr"] + roi_data["net_promo_profit_boost_inr"]),
            "dead_capital_recoverable_inr": int(roi_data["dead_capital_at_risk_inr"]),
            "turnover_acceleration_days": roi_data["capital_turnover_days"],
            "pillars": [
                {
                    "title": "Demand-Hook Cross-Selling",
                    "impact": "+24% Basket Value",
                    "action": f"Anchor offers on high-velocity staples ({products[0].name.split('(')[0].strip()}) to pull slow-moving higher-margin SKUs."
                },
                {
                    "title": "Regional Festival Surge Capture",
                    "impact": f"+{int(regional_events[0].demand_lift_pct)}% Footfall Surge" if regional_events else "+85% Footfall Surge",
                    "action": f"Align end-cap and WhatsApp promos with {regional_events[0].name if regional_events else 'upcoming festivals'}."
                },
                {
                    "title": "Hard Margin Floor Protection",
                    "impact": f"{detected_margin}%+ Net Margin",
                    "action": "Enforce Price Elasticity optimization so discounts never cannibalize baseline store profitability."
                }
            ]
        }

        # 2. Classify Retailer Intent (Preserving deterministic intent tags while enriching reply via Live Gemini)
        if any(w in msg_lower for w in ["failing", "fail", "slow moving", "stuck", "expiring", "expiry", "not selling", "dead stock", "poor sales", "low velocity"]):
            failing = [p for p in products if p.velocity_status == "SLOW_MOVING" or (p.weekly_sales_avg and p.weekly_sales_avg <= 15) or p.stock_quantity >= 60]
            failing.sort(key=lambda p: (p.weekly_sales_avg or 20) / max(1, p.stock_quantity))
            if not failing:
                failing = products[:2]

            top_failing = failing[0]
            second_failing = failing[1] if len(failing) > 1 else None
            trapped_cash = int(top_failing.stock_quantity * top_failing.cost_price)
            days_supply = int((top_failing.stock_quantity / max(1, top_failing.weekly_sales_avg or 10)) * 7)

            fast_anchors = [p for p in products if p.velocity_status == "FAST_MOVING" and p.id != top_failing.id]
            anchor = fast_anchors[0] if fast_anchors else products[0]

            rescue_plan = PromoMindEngine.generate_plan(
                query=f"Rescue failing {top_failing.name} paired with fast moving {anchor.name}",
                min_margin_pct=detected_margin,
                event_theme="Clearance & Fast Turnaround",
                offer_type="COMBO_DISCOUNT",
                primary_product_id=anchor.id,
                secondary_product_id=top_failing.id,
                region=store_profile.region,
                archetype="EXPIRY_RESCUE_CLEARANCE",
                api_key=api_key
            )

            ai_reply = cls._generate_live_copilot_reply(
                user_message=message,
                intent="FAILING_PRODUCTS_AUDIT",
                store_profile=store_profile,
                plan=rescue_plan,
                extra_context=f"Failing SKU: {top_failing.name} ({top_failing.stock_quantity} units, ₹{trapped_cash} trapped cash, {days_supply} days supply).",
                api_key=api_key
            )

            reply = ai_reply or (
                f"{greeting} Here is an audit of products currently stuck on your shelves in **{loc_label}**:\n\n"
                f"1. **{top_failing.name}**\n"
                f"   • Velocity: Selling only **{top_failing.weekly_sales_avg or 5} units/week**\n"
                f"   • Stock Remaining: **{top_failing.stock_quantity} units** (**{days_supply} days** of stock stuck)\n"
                f"   • Trapped Capital: **₹{trapped_cash:,}** dead inventory\n"
                + (f"2. **{second_failing.name}** — **{second_failing.weekly_sales_avg or 8} units/week** ({second_failing.stock_quantity} units on shelf)\n\n" if second_failing else "\n")
                + f"**Sales Growth Action:** Bundle **{top_failing.name.split('(')[0].strip()}** with your best-seller (**{anchor.name.split('(')[0].strip()}**) at **₹{int(rescue_plan.recommended_combo_price)}** to recover **₹{trapped_cash:,}** while protecting a **{rescue_plan.net_margin_pct}% net profit margin**."
            )

            return ChatResponse(
                reply=reply,
                intent="FAILING_PRODUCTS_AUDIT",
                detected_margin_pct=detected_margin,
                plan=rescue_plan,
                sales_growth_plan=sales_growth_plan,
                regional_festivals=regional_events,
                generation_source=rescue_plan.generation_source
            )

        is_sales_growth_query = (
            (("increase" in msg_lower or "improve" in msg_lower or "boost" in msg_lower or "grow" in msg_lower or "more" in msg_lower)
             and ("sale" in msg_lower or "revenue" in msg_lower or "turnover" in msg_lower or "profit" in msg_lower))
            or any(w in msg_lower for w in ["sales growth", "growth strategy", "basket size", "higher bill"])
        )
        if is_sales_growth_query:
            fast_mover = next((p for p in products if p.velocity_status == "FAST_MOVING"), products[0])
            attached = next((p for p in products if p.id != fast_mover.id and p.selling_price - p.cost_price >= 25), products[1])
            plan = PromoMindEngine.generate_plan(
                query=f"Basket builder combo for {fast_mover.name} and {attached.name}",
                min_margin_pct=detected_margin,
                event_theme=regional_events[0].name if regional_events else "Super Sales Booster",
                offer_type="COMBO_DISCOUNT",
                region=store_profile.region,
                archetype="ANCHOR_MARGIN_BOOSTER",
                api_key=api_key
            )
            ai_reply = cls._generate_live_copilot_reply(
                user_message=message,
                intent="SALES_GROWTH_ADVICE",
                store_profile=store_profile,
                plan=plan,
                extra_context=f"Upcoming festival: {regional_events[0].name if regional_events else 'Diwali'}. Unlocked promo cash: ₹{int(roi_data['unlocked_capital_from_promos_inr']):,}.",
                api_key=api_key
            )
            reply = ai_reply or (
                f"{greeting} To grow sales by 20–30% in **{loc_label}**, here is your tailored 3-pillar strategy:\n\n"
                f"1. **Raise Basket Size (Cross-Sell):** Pair high-footfall staples (**{plan.anchor_product.name.split('(')[0].strip()}**) with high-margin attachments (**{plan.attached_product.name.split('(')[0].strip()}**) at **₹{int(plan.recommended_combo_price)}**.\n"
                f"2. **Capitalize on Regional Festival Demand:** **{regional_events[0].name if regional_events else 'Festive Season'}** drives a **+{int(regional_events[0].demand_lift_pct) if regional_events else 85}%** demand surge in {store_profile.region}.\n"
                f"3. **Accelerate Working Capital Turnover:** Recover **₹{int(roi_data['unlocked_capital_from_promos_inr']):,}** in cash every **{roi_data['capital_turnover_days']} days** while protecting a **{plan.net_margin_pct}%** net margin."
            )
            return ChatResponse(
                reply=reply,
                intent="SALES_GROWTH_ADVICE",
                detected_margin_pct=detected_margin,
                plan=plan,
                sales_growth_plan=sales_growth_plan,
                regional_festivals=regional_events,
                generation_source=plan.generation_source
            )

        if any(w in msg_lower for w in ["dead capital", "trapped", "roi", "working capital", "financial", "valuation", "investment", "audit"]):
            ai_reply = cls._generate_live_copilot_reply(
                user_message=message,
                intent="ROI_INSIGHT",
                store_profile=store_profile,
                plan=None,
                extra_context=json.dumps(roi_data),
                api_key=api_key
            )
            reply = ai_reply or (
                f"{greeting} Here is the live financial & working capital audit for **{store_profile.store_name}** in **{loc_label}**:\n\n"
                f"• **Total Inventory Invested:** ₹{int(roi_data['total_inventory_invested_inr']):,} across {len(products)} active SKUs\n"
                f"• **Capital at Risk (Slow Movers):** ₹{int(roi_data['dead_capital_at_risk_inr']):,} trapped in aging stock\n"
                f"• **Cash Recoverable via Smart Bundles:** ₹{int(roi_data['unlocked_capital_from_promos_inr']):,}\n"
                f"• **Turnover Acceleration:** Capital recovers **{roi_data['capital_turnover_days']} days faster**"
            )
            return ChatResponse(
                reply=reply,
                intent="ROI_INSIGHT",
                detected_margin_pct=detected_margin,
                roi_summary=roi_data,
                sales_growth_plan=sales_growth_plan,
                regional_festivals=regional_events,
                generation_source=GeminiLiveClient._LAST_USED_SOURCE if ai_reply else "HYBRID_LOCAL_SYNTHESIS"
            )

        is_weekly_request = (
            any(w in msg_lower for w in [
                "offer ideas", "weekly offers", "suggest offers", "recommend offers",
                "deal ideas", "best offers", "top offers", "offer recommendations",
                "deals for this week", "offers for this week", "few products", "three offers", "3 offers"
            ]) or
            bool(re.search(r'\b(?:suggest|give|show|recommend|tell|what)\b.*?\b(?:3|three|top|best|few|some|weekly)?\s*(?:offers?|deals?|ideas?|combos?|promos?)\b', msg_lower)) or
            bool(re.search(r'\b(?:top|best|3|three)\b.*?\b(?:offers?|deals?|combos?)\b', msg_lower))
        )

        if is_weekly_request:
            ideas = PromoMindEngine.generate_weekly_recommendations(region=store_profile.region, api_key=api_key)
            top_plan = PromoMindEngine.generate_plan(
                query=f"{ideas[0]['anchor_name']} and {ideas[0]['attached_name']}",
                min_margin_pct=detected_margin,
                event_theme=ideas[0]["event_theme"],
                primary_product_id=ideas[0]["anchor_id"],
                secondary_product_id=ideas[0]["attached_id"],
                region=store_profile.region,
                archetype=ideas[0]["archetype"],
                api_key=api_key
            ) if ideas else None

            reply = (
                f"{greeting} Based on live sales velocity and regional demand in **{loc_label}**, "
                f"here are the **Top {len(ideas)} Curated Offer Bundles** for this week:\n\n"
                + "\n".join([
                    f"• **{idea['title']}** — Offer: **₹{int(idea['combo_price'])}** (MRP ~₹{int(idea['original_mrp'])}~, Save ₹{int(idea['savings_amount'])} | {idea['net_margin_pct']}% Margin)"
                    for idea in ideas
                ])
                + f"\n\nEach bundle protects your **{detected_margin}%+ target margin**. Select any deal below to load it into the Campaign Collateral Studio:"
            )
            return ChatResponse(
                reply=reply,
                intent="WEEKLY_IDEAS",
                detected_margin_pct=detected_margin,
                plan=top_plan,
                ideas=ideas,
                sales_growth_plan=sales_growth_plan,
                regional_festivals=regional_events,
                generation_source=top_plan.generation_source if top_plan else "LIVE_GEMINI_API"
            )

        is_fest_query = (
            any(w in msg_lower for w in [
                "upcoming festival", "regional festival", "festivals in", "what festival",
                "festival calendar", "festive offers", "festive deals", "dasara", "dussehra",
                "durga puja", "pujo", "ganesh utsav", "ganpati", "pongal", "onam", "ugadi", "holiday"
            ]) and not any(w in msg_lower for w in ["create combo", "generate promo for product", "calculate margin"])
        )
        if is_fest_query:
            events = regional_events
            top_fest = events[0] if events else None
            if top_fest and top_fest.matched_inventory_items and len(top_fest.matched_inventory_items) >= 2:
                p1_id = top_fest.matched_inventory_items[0]["product_id"]
                p2_id = top_fest.matched_inventory_items[1]["product_id"]
                fest_plan = PromoMindEngine.generate_plan(
                    query=f"Festive bundle for {top_fest.name}",
                    min_margin_pct=detected_margin,
                    event_theme=top_fest.name,
                    offer_type="COMBO_DISCOUNT",
                    primary_product_id=p1_id,
                    secondary_product_id=p2_id,
                    region=store_profile.region,
                    archetype=top_fest.recommended_promo_type or "FESTIVE_CELEBRATION_HAMPER",
                    api_key=api_key
                )
            else:
                fest_plan = PromoMindEngine.generate_plan(
                    query=f"Festive bundle for {top_fest.name if top_fest else 'Festival'}",
                    min_margin_pct=detected_margin,
                    event_theme=top_fest.name if top_fest else "Festive Special",
                    offer_type="COMBO_DISCOUNT",
                    region=store_profile.region,
                    archetype="FESTIVE_CELEBRATION_HAMPER",
                    api_key=api_key
                )

            fest_lines = []
            for ev in events[:3]:
                fest_lines.append(f"• **{ev.name}** ({ev.date_window})\n   Key Demand Surge: **{', '.join(ev.key_items[:3])}** (+{int(ev.demand_lift_pct)}% surge)")

            reg_display = f"{store_profile.region}, {store_profile.country}" if getattr(store_profile, "country", None) else store_profile.region
            reply = (
                f"{greeting} Here is the live cultural festival calendar and retail demand forecast for **{reg_display}** ({loc_label}):\n\n"
                + "\n\n".join(fest_lines) + "\n\n"
                f"**Recommended Action for {top_fest.name if top_fest else 'the upcoming festival'}:**\n"
                f"{top_fest.tradition_notes if top_fest else 'High festival demand prep.'}\n\n"
                f"I have modeled an optimal festival campaign below pairing your high-velocity inventory with festive demand:"
            )
            return ChatResponse(
                reply=reply,
                intent="FESTIVAL_CALENDAR_INSIGHT",
                detected_margin_pct=detected_margin,
                plan=fest_plan,
                sales_growth_plan=sales_growth_plan,
                regional_festivals=events,
                generation_source=fest_plan.generation_source
            )

        # Specific Promotional Plan Generation (Single Combo)
        archetype = "ANCHOR_MARGIN_BOOSTER"
        event_theme = regional_events[0].name if regional_events else "Weekly Retail Deal"
        if "diwali" in msg_lower or "deepa" in msg_lower or "festive" in msg_lower or "festival" in msg_lower:
            archetype = "FESTIVE_CELEBRATION_HAMPER"
            event_theme = "Diwali Maha Utsav"
        elif "expiry" in msg_lower or "clear" in msg_lower or "slow" in msg_lower or "bogo" in msg_lower:
            archetype = "EXPIRY_RESCUE_CLEARANCE"
            event_theme = "Clearance Rush"
        elif "bulk" in msg_lower or "volume" in msg_lower or "joint family" in msg_lower:
            archetype = "VOLUME_TIER_SLAB"
            event_theme = "Family Saver Pack"

        plan = PromoMindEngine.generate_plan(
            query=message,
            min_margin_pct=detected_margin,
            event_theme=event_theme,
            offer_type="COMBO_DISCOUNT",
            region=store_profile.region,
            archetype=archetype,
            api_key=api_key
        )

        ai_reply = cls._generate_live_copilot_reply(
            user_message=message,
            intent="PROMOTION_GENERATED",
            store_profile=store_profile,
            plan=plan,
            extra_context=f"Event theme: {event_theme}",
            api_key=api_key
        )

        combo_p = int(plan.recommended_combo_price)
        mrp_p = int(plan.original_combined_mrp)
        save_p = int(plan.discount_amount)
        save_pct = plan.discount_pct
        margin_p = plan.net_margin_pct
        anchor_name = plan.anchor_product.name.split('(')[0].strip()
        attached_name = plan.attached_product.name.split('(')[0].strip()

        reply = ai_reply or (
            f"{greeting} For **{store_profile.store_name}** in **{loc_label}**, here is a live-generated promotional bundle:\n\n"
            f"Paired **{anchor_name}** with **{attached_name}**. "
            f"Shoppers get a **₹{save_p} direct discount** ({save_pct}% OFF) paying **₹{combo_p}** instead of ₹{mrp_p}, "
            f"while your store secures a **{margin_p}% net profit margin**.\n\n"
            f"**Why it works:** {plan.strategic_rationale.split('.')[0]}.\n"
            f"**Cashier counter script:** *\"{plan.creative_assets.cashier_counter_pitch}\"*"
        )

        return ChatResponse(
            reply=reply,
            intent="PROMOTION_GENERATED",
            detected_margin_pct=detected_margin,
            plan=plan,
            sales_growth_plan=sales_growth_plan,
            regional_festivals=regional_events,
            generation_source=plan.generation_source
        )

    @classmethod
    def _generate_live_copilot_reply(
        cls,
        user_message: str,
        intent: str,
        store_profile: StoreProfile,
        plan: Optional[ComboPlan],
        extra_context: str = "",
        api_key: Optional[str] = None
    ) -> Optional[str]:
        plan_info = ""
        if plan:
            plan_info = (
                f"Generated Combo: {plan.title} | Combo Price: ₹{int(plan.recommended_combo_price)} "
                f"(MRP ₹{int(plan.original_combined_mrp)}, Save ₹{int(plan.discount_amount)} / {plan.discount_pct}% OFF) | "
                f"Protected Net Margin: {plan.net_margin_pct}% | Cashier Pitch: {plan.creative_assets.cashier_counter_pitch}"
            )
        prompt = f"""You are PromoMind AI Retail Copilot & Sales Growth Advisor for {store_profile.store_name} in {store_profile.locality}, {store_profile.city} ({store_profile.region}).
Retailer Query: "{user_message}"
Detected Intent: {intent}
Store Context: {extra_context}
{plan_info}

Write a concise, practical, jargon-free advisor response (3-5 short bullet points or paragraphs) directly answering the retailer's query with exact Rupee numbers and margins.
Return ONLY valid JSON: {{"reply": "your markdown formatted reply string"}}
"""
        res = GeminiLiveClient.generate_json(prompt, override_api_key=api_key, timeout=6)
        if isinstance(res, dict) and res.get("reply"):
            return str(res["reply"]).strip()
        return None
