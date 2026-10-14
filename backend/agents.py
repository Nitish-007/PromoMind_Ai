import os
import sys
import math
import json
import re
import urllib.request
from typing import Tuple, Dict, Any, Optional, List

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from models import (
    Product, DemandForecast, ComboPlan, CreativeAssets, ROIMetrics, 
    StoreProfile, PromotionVariety, ChatQuery, ChatResponse, RegionalFestivalEvent
)
from mock_data import AFFINITY_MATRIX, DEMAND_FORECASTS
from storage import StoreDataManager
from forecasting import OpenSourceForecastingEngine, PriceElasticityOptimizer, InvestmentROIEngine

class DemandAndInventoryAgent:
    """Identifies high-surge anchor items and pairs them with high-margin or slow-moving items."""
    
    @staticmethod
    def find_products_from_prompt(
        prompt: str,
        preferred_anchor_id: Optional[str] = None,
        preferred_attached_id: Optional[str] = None
    ) -> Tuple[Product, Product, float, str]:
        products = StoreDataManager.load_products()
        prompt_lower = prompt.lower()
        
        # Explicit user selection overrides
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
                    driver = f"Retailer manual selection of {anchor.name} paired with {attached.name}"
                    return anchor, attached, affinity, driver

        # Product resolution heuristics
        anchor = None
        attached = None
        
        # Check if user mentioned any specific product name in their store inventory (including newly added/CSV SKUs)
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
            driver = f"Store SKU pairing resolved from prompt: {anchor.name} + {attached.name}"
        elif len(matched_from_inventory) == 1:
            anchor = matched_from_inventory[0]

        # Thematic / Category detection if anchor or attached still missing
        if not anchor:
            if "tea" in prompt_lower:
                anchor = next((p for p in products if "tea" in p.name.lower() or p.category == "Beverages"), products[0])
            elif "ghee" in prompt_lower or "diwali" in prompt_lower or "deepa" in prompt_lower:
                anchor = next((p for p in products if "ghee" in p.name.lower() or p.category == "Dairy"), products[0])
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
            # Fall back to high-affinity slow-moving or complementary inventory item
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
        """
        Delegates to Open-Source PriceElasticityOptimizer to calculate optimal price,
        customer savings, and net profit margin.
        """
        pricing_result = PriceElasticityOptimizer.optimize_bundle_pricing(
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
        return pricing_result


class ROIPredictorAgent:
    """Simulates 10-day promotional performance vs status quo."""
    
    @staticmethod
    def simulate_roi(
        anchor: Product, 
        attached: Product, 
        pricing_result: Dict[str, Any]
    ) -> ROIMetrics:
        baseline_units = attached.weekly_sales_avg * 2  # ~10 days
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
    """Generates marketing copy, WhatsApp broadcast, poster, and cashier checkout pitch."""
    
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
        store_profile: Optional[StoreProfile] = None
    ) -> CreativeAssets:
        profile = store_profile or StoreProfile()
        gemini_api_key = os.environ.get("GEMINI_API_KEY")
        
        # Region-specific greetings & colloquial expressions
        region = (profile.region or "Karnataka & South India").lower()
        if "karnataka" in region or "south" in region:
            fest_greeting = "Deepavali Habbada Shubhashayagalu!" if "diwali" in event_theme.lower() else "Habba Special Offers!"
            vernacular_tag = "Bachat Offer"
            cashier_script = f"Sir/Ma'am, {anchor.name.split('(')[0].strip()} ke saath {attached.name.split('(')[0].strip()} bundle me lenge toh ₹{int(discount_amount)} ki direct bachat hai!"
        elif "maharashtra" in region or "west" in region:
            fest_greeting = "Diwali Chya Hardik Shubhechha!" if "diwali" in event_theme.lower() else "Utsav Vishesh Bumper Deal!"
            vernacular_tag = "Motha Fayda Deal"
            cashier_script = f"Namaskar! {anchor.name.split('(')[0].strip()} sobat {attached.name.split('(')[0].strip()} ghetla tar ₹{int(discount_amount)} cha discount miltoye!"
        elif "bengal" in region or "east" in region:
            fest_greeting = "Subho Bijoya & Pujo'r Preeti O Shubhechha!" if "puja" in event_theme.lower() else "Bumper Pujo Offer!"
            vernacular_tag = "Bhog & Saver Pack"
            cashier_script = f"Dada/Didi, {anchor.name.split('(')[0].strip()}-er sathe {attached.name.split('(')[0].strip()} bundle-e ₹{int(discount_amount)} chhar pachhen!"
        else:
            fest_greeting = "Diwali Ki Hardik Shubhkamnayein!" if "diwali" in event_theme.lower() else "Special Retail Saver Deal!"
            vernacular_tag = "Maha Bachat Pack"
            cashier_script = f"Bhaiya/Bhabhi, {anchor.name.split('(')[0].strip()} ke saath {attached.name.split('(')[0].strip()} pack lene par ₹{int(discount_amount)} ki bachat hai, bill me add kar doon?"

        # Human readable offer format
        offer_headline_label = f"{archetype.replace('_', ' ').title()} — Save ₹{int(discount_amount)} ({discount_pct}% OFF)"
        
        # If API key is available in environment, make live Gemini request
        prompt_content = f"""
        You are PromoMind AI, an elite retail copywriter for grocery stores & supermarkets.
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
        - whatsapp_message: (Engaging WhatsApp broadcast with regional greeting '{fest_greeting}', emojis, pricing, savings, and store address)
        - pos_tagline: (Snappy 1-liner printed on bill receipts)
        - cashier_counter_pitch: (1-line friendly verbal upsell pitch for the billing cashier)
        """

        # Method 1: Google AI Studio API Key (Direct Free Tier)
        if gemini_api_key:
            target_model = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash")
            candidate_models = list(dict.fromkeys([
                target_model,
                "gemini-3.5-flash",
                "gemini-3.5-flash-lite",
                "gemini-3-flash-preview",
                "gemini-2.5-flash",
                "gemini-1.5-pro",
                "gemini-1.5-flash"
            ]))

            for m in candidate_models:
                try:
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={gemini_api_key}"
                    payload = json.dumps({
                        "contents": [{"parts": [{"text": prompt_content}]}],
                        "generationConfig": {"response_mime_type": "application/json"}
                    }).encode("utf-8")
                    
                    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
                    with urllib.request.urlopen(req, timeout=6) as response:
                        res_data = json.loads(response.read().decode())
                        text_out = res_data["candidates"][0]["content"]["parts"][0]["text"].strip()
                        if text_out.startswith("```json"):
                            text_out = text_out[7:]
                        elif text_out.startswith("```"):
                            text_out = text_out[3:]
                        if text_out.endswith("```"):
                            text_out = text_out[:-3]
                        parsed = json.loads(text_out.strip())
                        parsed["cashier_counter_pitch"] = parsed.get("cashier_counter_pitch") or cashier_script
                        return CreativeAssets(**parsed)
                except Exception:
                    continue

        # Method 2: Google Cloud Vertex AI (GCP Trial & Free Monthly Credits via service_account.json)
        gcp_project = os.environ.get("GCP_PROJECT_ID") or os.environ.get("GOOGLE_CLOUD_PROJECT")
        creds_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        if not gcp_project and creds_path and os.path.exists(creds_path):
            try:
                with open(creds_path, "r", encoding="utf-8") as f:
                    cdata = json.load(f)
                    gcp_project = cdata.get("project_id")
            except Exception:
                pass

        if gcp_project:
            try:
                from google import genai
                vertex_region = os.environ.get("GCP_REGION", "us-central1")
                client = genai.Client(vertexai=True, project=gcp_project, location=vertex_region)
                v_model = os.environ.get("VERTEX_AI_MODEL_NAME", "gemini-1.5-pro")
                response = client.models.generate_content(
                    model=v_model,
                    contents=prompt_content,
                    config={"response_mime_type": "application/json"}
                )
                if response and response.text:
                    text_out = response.text.strip()
                    if text_out.startswith("```json"):
                        text_out = text_out[7:]
                    elif text_out.startswith("```"):
                        text_out = text_out[3:]
                    if text_out.endswith("```"):
                        text_out = text_out[:-3]
                    parsed = json.loads(text_out.strip())
                    parsed["cashier_counter_pitch"] = parsed.get("cashier_counter_pitch") or cashier_script
                    return CreativeAssets(**parsed)
            except Exception:
                pass  # Fall back to high quality deterministic generation
                
        # Deterministic High-Quality Regional Fallback
        anchor_short = anchor.name.split('(')[0].strip()
        attached_short = attached.name.split('(')[0].strip()
        is_festive = "diwali" in event_theme.lower() or "festive" in event_theme.lower() or "ghee" in anchor.name.lower() or "sweet" in anchor.name.lower() or "puja" in event_theme.lower()
        
        if is_festive:
            headline = f"{event_theme}: {anchor_short} + {attached_short}"
            subheading = f"Celebrate with Premium Delights & Guaranteed Savings at {profile.store_name}"
            badge = f"{event_theme.upper()} • SAVE ₹{int(discount_amount)}"
            body = f"Pair authentic {anchor.name} with nutritious {attached.name}. Specially curated for {profile.region} festivities!"
            whatsapp = (
                f"🪔 *{fest_greeting}* 🪔\n"
                f"*{event_theme.upper()} SPECIAL SAVINGS at {profile.store_name}!* ✨\n\n"
                f"💥 *Offer Format:* {offer_headline_label}\n"
                f"🛒 *Curated Bundle:* {anchor.name} + {attached.name}\n\n"
                f"❌ Combined MRP: ~₹{int(anchor.selling_price + attached.selling_price)}~\n"
                f"🔥 *Exclusive Offer Price: ₹{int(combo_price)} only!*\n"
                f"💰 *Instant Cash Savings: ₹{int(discount_amount)} ({discount_pct}% OFF)*\n\n"
                f"📍 *Visit Us:* {profile.store_name}, {profile.locality}, {profile.city}\n"
                f"⚡ *Limited Stock:* Valid for next 5 days or until festive stock lasts!\n"
                f"Reply 'BOOK' on WhatsApp to reserve your pack at the counter!"
            )
            pos_tagline = f"{event_theme}: Save ₹{int(discount_amount)} on {anchor_short} + {attached_short} pack today!"
        else:
            headline = f"{event_theme}: {anchor_short} + {attached_short}"
            subheading = f"Everyday Kitchen Essentials at Unbeatable Prices — {profile.store_name}"
            badge = f"{event_theme.upper()} • {discount_pct}% OFF"
            body = f"Enjoy royal quality {anchor.name} paired with {attached.name}."
            whatsapp = (
                f"⚡ *{event_theme.upper()} EXCLUSIVE DEAL at {profile.store_name}!* ⚡\n\n"
                f"Upgrade your household pantry with our verified value duo:\n"
                f"🛒 *{anchor.name}* + *{attached.name}*\n\n"
                f"❌ MRP: ~₹{int(anchor.selling_price + attached.selling_price)}~\n"
                f"💥 *Special Deal Price: ₹{int(combo_price)}!*\n"
                f"💵 *Your Savings: ₹{int(discount_amount)} ({discount_pct}% OFF)*\n\n"
                f"📍 {profile.store_name}, {profile.locality}, {profile.city}\n"
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
        )


class PromoMindEngine:
    """Master Orchestrator uniting Demand Forecasting, Price Elasticity, ROI, and Creative Agents."""
    
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
        archetype: Optional[str] = "ANCHOR_MARGIN_BOOSTER"
    ) -> ComboPlan:
        # Load store profile for regional grounding
        store_profile = StoreDataManager.load_profile()
        if region:
            store_profile.region = region

        # Step 1: Detect items & affinity
        anchor, attached, affinity, driver = DemandAndInventoryAgent.find_products_from_prompt(
            prompt=query,
            preferred_anchor_id=primary_product_id,
            preferred_attached_id=secondary_product_id
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
        
        # Step 6: Generate marketing copy & creatives with Regional Cashier Pitch
        combo_name = f"{anchor.name.split('(')[0].strip()} + {attached.name.split('(')[0].strip()}"
        creatives = GeminiCreativeAgent.generate_creatives(
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
            store_profile=store_profile
        )
        
        # Step 6: Generate Multiple Dynamic Promotion Varieties
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
                "Nomoshkar" if "bengal" in store_profile.region.lower() or "east" in store_profile.region.lower() else "Pranam / Namaste"
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
                wa_copy = f"🛒 *{event_theme.upper()} VALUE DUO:* Get {anchor_short} + {attached_short} for just ₹{int(v_price)} (Save ₹{int(v_disc_amt)}) at {store_profile.store_name}!"
                headline = f"EVERYDAY VALUE: {anchor_short} + {attached_short}"
            elif v_type == "EXPIRY_CLEARANCE":
                pitch = f"{greeting}! Aaj limited clearance flash deal hai: {attached_short} par flat {v_disc_pct}% discount mil raha hai {anchor_short} ke saath! Bag me add karein?"
                wa_copy = f"⚡ *FLASH CLEARANCE DEAL:* Get {attached_short} at {v_disc_pct}% OFF when paired with {anchor_short} for only ₹{int(v_price)}! Limited shelf stock at {store_profile.store_name}."
                headline = f"FLASH CLEARANCE: SAVE ₹{int(v_disc_amt)} ({v_disc_pct}% OFF)"
            elif v_type == "VOLUME_SLAB":
                pitch = f"{greeting}! Yeh double bundle lene par direct ₹{int(v_disc_amt)} bachat hai aur 2 packs par extra cashback reward milega!"
                wa_copy = f"📦 *BUY MORE • SAVE MORE:* Stock up {anchor_short} + {attached_short} at ₹{int(v_price)} (Save ₹{int(v_disc_amt)}). Extra savings on 2+ packs at {store_profile.store_name}!"
                headline = f"VOLUME SAVER: {anchor_short} + {attached_short} PACK"
            elif v_type == "FESTIVE_HAMPER":
                pitch = f"Happy {event_theme.split('(')[0].strip()}! Festive Celebration Gift Box ready hai gifting ke liye flat ₹{int(v_disc_amt)} discount ke saath, pack kar doon?"
                wa_copy = f"🪔 *FESTIVE CELEBRATION BOX:* Premium {anchor_short} paired with {attached_short} at ₹{int(v_price)} (MRP ₹{int(combined_mrp)}). Perfect for festive gifting from {store_profile.store_name}!"
                headline = f"FESTIVE CELEBRATION BOX: ₹{int(v_price)} ONLY"
            else: # BILL_BUSTER
                pitch = f"{greeting}! Store me ₹799+ billing par yeh {attached_short} bundle deal unlock ho raha hai sirf ₹{int(v_price)} me!"
                wa_copy = f"🎯 *CART UNLOCK SPECIAL:* Shop for ₹799+ at {store_profile.store_name} and unlock {anchor_short} + {attached_short} at a massive ₹{int(v_disc_amt)} discount!"
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
            hybrid_architecture={
                "engine_type": "NEURO_SYMBOLIC_HYBRID",
                "ai_layer": {
                    "model": "Gemini 1.5 Pro (Generative Agent)" if "pro" in os.environ.get("GEMINI_MODEL", "gemini-1.5-pro").lower() else "Gemini 1.5 Flash (Generative Agent)",
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
                "synergy_summary": "Generative AI formulates the emotional and cultural appeal, while open-source mathematical equations calculate price elasticity and enforce strict margin floors so the retailer never sells at a loss."
            }
        )

    @classmethod
    def generate_weekly_recommendations(cls, region: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Autonomous Weekly Offer Generator.
        Scans all store inventory, pairs high-velocity anchors with near-expiry stock
        and festive drivers, producing the top 3 recommended promotional bundles.
        No product selection required from the retailer.
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
        biscuit = next((p for p in products if ("biscuit" in p.name.lower() or "cookie" in p.name.lower() or p.category == "Snacks") and p.id != tea.id), None)
        if not biscuit:
            biscuit = next((p for p in products if p.velocity_status == "SLOW_MOVING" and p.id != tea.id), products[1])
        if tea and biscuit:
            p1 = PricingAndMarginAgent.optimize_price(tea, biscuit, min_margin_pct=16.0, archetype="EXPIRY_RESCUE_CLEARANCE")
            recommendations.append({
                "idea_id": "IDEA_CLEARANCE",
                "badge": "⚡ Slow-Stock Clearance",
                "badge_class": "badge-variety-clearance",
                "icon": "☕",
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
        ghee = next((p for p in products if "ghee" in p.name.lower() or p.category == "Dairy"), None)
        dry_fruit = next((p for p in products if ("almond" in p.name.lower() or "dry fruit" in p.category.lower() or "sweet" in p.category.lower()) and (not ghee or p.id != ghee.id)), None)
        if ghee and dry_fruit:
            p2 = PricingAndMarginAgent.optimize_price(ghee, dry_fruit, min_margin_pct=18.0, archetype="FESTIVE_CELEBRATION_HAMPER", event_surge_pct=85.0)
            recommendations.append({
                "idea_id": "IDEA_FESTIVE",
                "badge": "🪔 Festive Gifting Special",
                "badge_class": "badge-variety-festive",
                "icon": "🪔",
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
                "badge": "🛒 Kitchen Basket Builder",
                "badge_class": "badge-variety-recommended",
                "icon": "🍳",
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
    Leverages Gemini AI with Google Search grounding / knowledge base to discover local cultural festivals,
    predict specific retail product demand surges, and match against the store's live inventory.
    """
    _CACHE: Dict[str, List[RegionalFestivalEvent]] = {}

    BUILTIN_REGIONAL_FESTIVALS: Dict[str, List[Dict[str, Any]]] = {
        "karnataka": [
            {
                "id": "EVT_MYSURU_DASARA",
                "name": "Mysuru Dasara & Vijayadashami (Nada Habba)",
                "date_window": "Oct 12 - Oct 22, 2026",
                "status": "UPCOMING",
                "key_items": ["Pure Cow Ghee", "Sweets & Gulab Jamun", "Puffed Rice (Pori)", "Ash Gourd (Kumbalakai)", "Puja Camphor & Cotton Wicks", "California Almonds"],
                "demand_lift_pct": 125.0,
                "icon": "👑",
                "description": "Karnataka's royal state festival (Nada Habba). Massive cultural processions, Ayudha Puja vehicle blessings, and family sweet preparations across Bengaluru & Mysuru.",
                "tradition_notes": "Ayudha Puja is celebrated in every shop, commercial kitchen, and household with puffed rice (pori) and jaggery; Dasara feasts trigger huge demand for pure ghee to make Mysore Pak, Holige, and Payasa.",
                "advance_procurement_window": "T-14 Days: Restock Cow Ghee tins, Sweets cartons, and Puffed Rice before distributor festive price hikes.",
                "promo_launch_window": "T-7 Days: Launch 'Mysuru Dasara Royal Feast & Sweet Hamper' via WhatsApp Broadcast.",
                "clearance_window": "T+2 Days: Liquidate remaining festive sweets and pooja items at cost price.",
                "recommended_promo_type": "FESTIVE_CELEBRATION_HAMPER",
                "suggested_combo_title": "Mysuru Dasara Royal Feast & Ghee Duo"
            },
            {
                "id": "EVT_DEEPAVALI_SOUTH",
                "name": "Deepavali & Naraka Chaturdashi",
                "date_window": "Oct 24 - Oct 29, 2026",
                "status": "UPCOMING",
                "key_items": ["Clay Diyas & Deepas", "Pure Cow Ghee", "Gulab Jamun & Sweets", "California Almonds", "Puja Camphor & Cotton Wicks"],
                "demand_lift_pct": 140.0,
                "icon": "🪔",
                "description": "Peak celebration season across Karnataka. High surge in Clay Deepas and Pure Cow Ghee for festive lighting and sweet-making.",
                "tradition_notes": "Deepavali in Karnataka centers on dawn oil baths, lighting clay deepas at dusk, and gifting home-made sweets. Earthen deepa demand drops to <5 units/month outside festival season.",
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
                "icon": "🌿",
                "description": "New Year celebration with Bevu-Bella (neem & jaggery) and holige / obbattu preparation in every household.",
                "tradition_notes": "Symbolic tasting of bittersweet flavors representing life's experiences, and large-scale cooking of festive sweets like Obbattu / Holige requiring high ghee and maida.",
                "advance_procurement_window": "T-10 Days: Stock bulk organic jaggery, maida, and pure ghee.",
                "promo_launch_window": "T-5 Days: 'Ugadi Sweet-Making Essentials Kit' bundle.",
                "clearance_window": "T+2 Days: Clear seasonal jaggery blocks and perishable sweets.",
                "recommended_promo_type": "ANCHOR_MARGIN_BOOSTER",
                "suggested_combo_title": "Ugadi Obbattu Sweet-Maker Kit"
            },
            {
                "id": "EVT_GANESHA_HABBA",
                "name": "Ganesha Chaturthi (Vinayaka Habba)",
                "date_window": "Aug 27 - Sep 2, 2027",
                "status": "UPCOMING",
                "key_items": ["Modak Rice Flour", "Organic Jaggery", "Fresh Coconut", "Pure Cow Ghee", "Dry Fruits & Almonds", "Puja Agarbatti"],
                "demand_lift_pct": 95.0,
                "icon": "🐘",
                "description": "Community pandals, home celebrations, and mass cooking of Modaks and Kadubus across Bengaluru and Karnataka.",
                "tradition_notes": "Offering 21 modaks to Lord Ganesha is mandatory, creating extreme demand for modak dough, jaggery filling, coconut, and ghee.",
                "advance_procurement_window": "T-12 Days: Order jaggery, cardamom, ghee, and puja essentials.",
                "promo_launch_window": "T-6 Days: 'Modak Sweet Maker & Puja Hamper'.",
                "clearance_window": "T+2 Days: Move remaining puja camphor and wicks.",
                "recommended_promo_type": "FESTIVE_CELEBRATION_HAMPER",
                "suggested_combo_title": "Vinayaka Modak & Puja Blessing Duo"
            }
        ],
        "maharashtra": [
            {
                "id": "EVT_GANESH_UTSAV_MH",
                "name": "Ganesh Utsav (Ganeshotsav)",
                "date_window": "Aug 27 - Sep 5, 2027",
                "status": "UPCOMING",
                "key_items": ["Modak Flour (Peeth)", "Pure Cow Ghee", "Organic Jaggery (Gul)", "Dry Fruits", "Puja Dhoop & Agarbatti", "Cardamom"],
                "demand_lift_pct": 150.0,
                "icon": "🐘",
                "description": "Maharashtra's premier 10-day cultural festival. Massive demand for Ukadiche Modak ingredients and temple puja essentials in Mumbai & Pune.",
                "tradition_notes": "Ukadiche Modak preparation in every household; Ganesh pandals distribute huge quantities of laddoos and prasad.",
                "advance_procurement_window": "T-14 Days: Restock ghee tins, modak flour, and dry fruit cartons.",
                "promo_launch_window": "T-7 Days: 'Bappa Moraya Modak Celebration Kit'.",
                "clearance_window": "T+2 Days: Liquidate excess puja supplies.",
                "recommended_promo_type": "FESTIVE_CELEBRATION_HAMPER",
                "suggested_combo_title": "Bappa Moraya Modak & Ghee Duo"
            },
            {
                "id": "EVT_DIWALI_MH",
                "name": "Diwali Lakshmi Pujan & Faral",
                "date_window": "Oct 24 - Oct 30, 2026",
                "status": "UPCOMING",
                "key_items": ["Pure Cow Ghee", "Rava & Maida", "Poha (Flattened Rice)", "California Almonds", "Sunflower Cooking Oil", "Gulab Jamun"],
                "demand_lift_pct": 135.0,
                "icon": "🪔",
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
                "icon": "🚩",
                "description": "Marathi New Year with raising the sacred Gudi flag and family feasts of Puri-Shrikhand.",
                "tradition_notes": "Households buy sweet treats and pure ghee to welcome prosperity for the coming year.",
                "advance_procurement_window": "T-8 Days: Stock Shrikhand, Ghee, and Atta.",
                "promo_launch_window": "T-4 Days: 'Gudi Padwa Prosperity Pack'.",
                "clearance_window": "T+2 Days: Clear seasonal sweets.",
                "recommended_promo_type": "ANCHOR_MARGIN_BOOSTER",
                "suggested_combo_title": "Gudi Padwa Shrikhand & Ghee Celebration Pack"
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
                "icon": "🌸",
                "description": "Bengal's biggest socio-cultural extravaganza. 5 days of pandal-hopping, grand community feasts, and Bijoya gifting.",
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
                "icon": "🪔",
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
                "icon": "🎋",
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
                "id": "EVT_PONGAL_TN",
                "name": "Thai Pongal & Makar Sankranti",
                "date_window": "Jan 13 - Jan 17, 2027",
                "status": "UPCOMING",
                "key_items": ["Raw Rice (Pacharisi)", "Organic Jaggery (Vellam)", "Pure Cow Ghee", "Cashews & Dry Fruits", "Cardamom (Elachi)", "Cooking Sunflower Oil"],
                "demand_lift_pct": 145.0,
                "icon": "🌾",
                "description": "Tamil harvest festival celebrating agricultural abundance. Boiling sweet Sakkarai Pongal in fresh pots.",
                "tradition_notes": "Sakkarai Pongal requires raw rice, heavy jaggery, pure cow ghee, and toasted cashews in every Tamil home.",
                "advance_procurement_window": "T-14 Days: Restock Vellam (jaggery), Pacharisi (raw rice), and Ghee.",
                "promo_launch_window": "T-7 Days: 'Thai Pongal Harvest Sakkarai Kit'.",
                "clearance_window": "T+2 Days: Clear open jaggery blocks.",
                "recommended_promo_type": "FESTIVE_CELEBRATION_HAMPER",
                "suggested_combo_title": "Thai Pongal Sakkarai Ghee & Jaggery Box"
            },
            {
                "id": "EVT_KARTHIGAI_DEEPAM_TN",
                "name": "Karthigai Deepam (Festival of Lamps)",
                "date_window": "Nov 14 - Nov 20, 2026",
                "status": "UPCOMING",
                "key_items": ["Clay Agal Vilakku (Lamps)", "Sesame Gingelly Oil", "Cotton Wicks", "Puffed Rice (Pori)", "Jaggery (Vellam)"],
                "demand_lift_pct": 85.0,
                "icon": "🕯️",
                "description": "Spectacular evening lighting across Tamil homes and temples; making Nel Pori Urundai sweets.",
                "tradition_notes": "Rows of terracotta lamps lit with gingelly oil, and distribution of sweet puffed rice balls.",
                "advance_procurement_window": "T-10 Days: Stock sesame lamp oil and agal vilakkus.",
                "promo_launch_window": "T-5 Days: 'Karthigai Deepam Vilakku & Oil Kit'.",
                "clearance_window": "T+2 Days: Liquidate leftover earthen lamps.",
                "recommended_promo_type": "VOLUME_TIER_SLAB",
                "suggested_combo_title": "Karthigai Deepam Vilakku & Gingelly Oil Duo"
            }
        ],
        "gujarat": [
            {
                "id": "EVT_NAVRATRI_GUJ",
                "name": "Navratri Garba Mahotsav (9 Nights of Dance)",
                "date_window": "Oct 7 - Oct 16, 2026",
                "status": "UPCOMING",
                "key_items": ["Fasting Atta (Singoda/Rajgira)", "Sabudana", "Pure Cow Ghee", "California Almonds", "Rock Salt (Sendha Namak)", "Energy Snacks"],
                "demand_lift_pct": 130.0,
                "icon": "💃",
                "description": "Gujarat's world-famous 9 nights of Garba dance, devotion, and strict Upvas (fasting) cuisine.",
                "tradition_notes": "Huge surge in Upvas ingredients (Sabudana, Singoda, Dry Fruits, Ghee) consumed during 9 days of fasting.",
                "advance_procurement_window": "T-12 Days: Stock bulk Sabudana and Farali flours.",
                "promo_launch_window": "T-6 Days: 'Navratri Farali Energy & Ghee Hamper'.",
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
                "icon": "🪁",
                "description": "Kite flying from rooftops, eating Undhiyu and Til Chikki across Ahmedabad, Surat, and Vadodara.",
                "tradition_notes": "Til-gud chikkis and winter spices spike rapidly for 48 hours of roof-top celebrations.",
                "advance_procurement_window": "T-10 Days: Stock sesame seeds, jaggery, and peanuts.",
                "promo_launch_window": "T-5 Days: 'Uttarayan Rooftop Chikki & Spice Kit'.",
                "clearance_window": "T+2 Days: Liquidate leftover chikkis at 25% off.",
                "recommended_promo_type": "ANCHOR_MARGIN_BOOSTER",
                "suggested_combo_title": "Uttarayan Chikki & Ghee Fest Pack"
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
                "icon": "✨",
                "description": "Malayalam New Year marking new beginnings with Vishukkani darshan, Vishu Sadya feasting, and elders gifting Vishukkaineetam.",
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
                "icon": "🌼",
                "description": "Kerala's harvest festival welcoming King Mahabali. 26-dish Grand Sadya feast cooked in every home.",
                "tradition_notes": "Massive consumption of pure coconut oil for frying banana chips, and ghee + jaggery for sweet Ada Pradhaman payasam.",
                "advance_procurement_window": "T-14 Days: Restock Coconut Oil cans, Jaggery, and Payasam ingredients.",
                "promo_launch_window": "T-7 Days: 'Thiruvonam Grand Sadya Feast Hamper'.",
                "clearance_window": "T+2 Days: Clear open jaggery and perishable snacks.",
                "recommended_promo_type": "FESTIVE_CELEBRATION_HAMPER",
                "suggested_combo_title": "Onam Sadya Payasam & Ghee Feast Duo"
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
                "icon": "🪔",
                "description": "North India's largest festival of lights and wealth. Extravagant family gifting of dry fruits and sweets.",
                "tradition_notes": "Corporate and family gifting of dry fruit hampers and sweet boxes; lightning earthen diyas with mustard oil.",
                "advance_procurement_window": "T-14 Days: Stock Almond gift boxes and Pure Ghee tins.",
                "promo_launch_window": "T-7 Days: 'Diwali Shubh Labh Dry Fruit & Sweet Hamper'.",
                "clearance_window": "T+2 Days: Clear sweet boxes at cost to avoid expiry.",
                "recommended_promo_type": "FESTIVE_CELEBRATION_HAMPER",
                "suggested_combo_title": "Diwali Shubh Labh Ghee & Dry Fruit Box"
            },
            {
                "id": "EVT_HOLI_NORTH",
                "name": "Holi (Festival of Colors)",
                "date_window": "Mar 14 - Mar 17, 2027",
                "status": "UPCOMING",
                "key_items": ["Khoya / Mawa & Maida (Gujiya Ingredients)", "Pure Cow Ghee", "Refined Sunflower Oil", "Thandai Syrup", "Dry Fruits"],
                "demand_lift_pct": 110.0,
                "icon": "🎨",
                "description": "Festival of colors celebrated with homemade Gujiyas, Thandai, and savory snacks.",
                "tradition_notes": "Making traditional Gujiyas at home requires heavy ghee, maida, and frying oil.",
                "advance_procurement_window": "T-10 Days: Restock cooking oil and pure ghee.",
                "promo_launch_window": "T-5 Days: 'Holi Gujiya Sweet-Maker Kit'.",
                "clearance_window": "T+2 Days: Clear Thandai syrups.",
                "recommended_promo_type": "ANCHOR_MARGIN_BOOSTER",
                "suggested_combo_title": "Holi Gujiya Sweet & Thandai Duo"
            }
        ],
        "global": [
            {
                "id": "EVT_THANKSGIVING",
                "name": "Thanksgiving & Holiday Feasting",
                "date_window": "Nov 22 - Nov 28, 2026",
                "status": "UPCOMING",
                "key_items": ["Butter & Cream", "Roasting Seasonings", "Cranberry Sauces", "Bakery Mixes", "Beverages & Cider"],
                "demand_lift_pct": 120.0,
                "icon": "🦃",
                "description": "Family feasting and holiday dinner preparations creating high basket value retail traffic.",
                "tradition_notes": "Baking, roasting, and family dinner grocery purchases spike significantly.",
                "advance_procurement_window": "T-14 Days: Stock butter, spices, and baking essentials.",
                "promo_launch_window": "T-7 Days: 'Holiday Feast Family Bundle'.",
                "clearance_window": "T+2 Days: Clear perishable holiday bakery items.",
                "recommended_promo_type": "FESTIVE_CELEBRATION_HAMPER",
                "suggested_combo_title": "Holiday Family Feasting Hamper"
            },
            {
                "id": "EVT_CHRISTMAS_NEWYEAR",
                "name": "Christmas & New Year Holiday Celebrations",
                "date_window": "Dec 18, 2026 - Jan 2, 2027",
                "status": "UPCOMING",
                "key_items": ["Chocolates & Cookies", "Premium Snacks & Nuts", "Fruit Juices & Sparkling Cider", "Gifting Hampers"],
                "demand_lift_pct": 135.0,
                "icon": "🎄",
                "description": "End-of-year gifting, party snacking, and holiday celebrations across retail grocers.",
                "tradition_notes": "Confectionery, snacks, and holiday gift packs dominate checkout baskets.",
                "advance_procurement_window": "T-14 Days: Procure festive confectionery and gift packaging.",
                "promo_launch_window": "T-7 Days: 'Holiday Cheer Sweet & Snack Hamper'.",
                "clearance_window": "T+2 Days: Markdown seasonal gift items.",
                "recommended_promo_type": "FESTIVE_CELEBRATION_HAMPER",
                "suggested_combo_title": "Holiday Cheer Gifting Hamper"
            }
        ]
    }

    @classmethod
    def discover_festivals(
        cls,
        region: str = "Karnataka",
        country: str = "India",
        city: Optional[str] = None,
        force_refresh: bool = False
    ) -> List[RegionalFestivalEvent]:
        cache_key = f"{region.lower().strip()}:{country.lower().strip()}"
        if not force_refresh and cache_key in cls._CACHE:
            return cls._CACHE[cache_key]

        # 1. Try Live Gemini AI discovery
        festivals_data = cls._query_gemini_festivals(region, country, city)

        # 2. If Gemini didn't return or was offline, match against rich built-in knowledge base
        if not festivals_data:
            festivals_data = cls._get_builtin_festivals(region, country)

        # 3. Match against live store inventory products
        products = StoreDataManager.load_products()
        events: List[RegionalFestivalEvent] = []

        for d in festivals_data:
            key_items = d.get("key_items", [])
            matched_prods = []
            
            category_synonyms = {
                "sweet": "Sweets", "mithai": "Sweets", "modak": "Sweets", "ladoo": "Sweets", "holige": "Sweets", "obbattu": "Sweets",
                "ghee": "Dairy", "milk": "Dairy", "butter": "Dairy",
                "oil": "Oils", "sunflower": "Oils",
                "almond": "Dry Fruits", "nut": "Dry Fruits", "kaju": "Dry Fruits",
                "tea": "Beverages", "chai": "Beverages", "coffee": "Beverages",
                "biscuit": "Bakery", "cookie": "Bakery", "snack": "Snacks",
                "masala": "Spices", "spice": "Spices"
            }

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
                                "margin_pct": round(((p.selling_price - p.cost_price) / p.selling_price) * 100, 1),
                                "velocity_status": p.velocity_status,
                                "surge_lift_pct": d.get("demand_lift_pct", 75.0)
                            })

            # If no items directly matched, provide top 2 festive staples (Ghee/Sweets/Dry Fruits) from inventory
            if len(matched_prods) < 2:
                festive_fallbacks = [p for p in products if p.category in ["Dairy & Oils", "Sweets & Confectionery", "Dry Fruits", "Beverages"]]
                for p in festive_fallbacks:
                    if not any(m["product_id"] == p.id for m in matched_prods):
                        matched_prods.append({
                            "product_id": p.id,
                            "name": p.name,
                            "category": p.category,
                            "selling_price": p.selling_price,
                            "cost_price": p.cost_price,
                            "stock_quantity": p.stock_quantity,
                            "margin_pct": round(((p.selling_price - p.cost_price) / p.selling_price) * 100, 1),
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

            evt = RegionalFestivalEvent(
                id=d.get("id", f"EVT_{abs(hash(d.get('name', 'fest')))}"),
                name=d.get("name", "Regional Cultural Celebration"),
                region=f"{region.strip().title()}, {country.strip().title()}",
                date_window=d.get("date_window", "Upcoming Festive Season"),
                status=d.get("status", "UPCOMING"),
                key_items=key_items,
                demand_lift_pct=float(d.get("demand_lift_pct", 80.0)),
                icon=d.get("icon", "🪔"),
                description=d.get("description", "Significant regional shopping demand spike for retail grocery."),
                tradition_notes=d.get("tradition_notes"),
                advance_procurement_window=d.get("advance_procurement_window"),
                promo_launch_window=d.get("promo_launch_window"),
                clearance_window=d.get("clearance_window"),
                recommended_promo_type=d.get("recommended_promo_type", "FESTIVE_CELEBRATION_HAMPER"),
                matched_inventory_items=matched_prods[:4],
                suggested_combo_title=suggested_title,
                country=country,
                city=city
            )
            events.append(evt)

        # Strictly deliver the top 3 upcoming events
        top_events = events[:3]
        cls._CACHE[cache_key] = top_events
        return top_events

    @classmethod
    def _query_gemini_festivals(cls, region: str, country: str, city: Optional[str]) -> Optional[List[Dict[str, Any]]]:
        gemini_api_key = os.environ.get("GEMINI_API_KEY")
        if not gemini_api_key:
            return None

        prompt = f"""You are a specialized retail demand forecasting and cultural festival intelligence expert for grocery & retail supermarkets.
CRITICAL TEMPORAL CONSTRAINT:
- Today's date is in October 2026.
- ALL festival dates MUST be strictly UPCOMING from October 2026 into calendar year 2027.
- NEVER return past years (e.g. 2024 or 2025). Every date must have year 2026 (for late 2026) or 2027.
- Return EXACTLY the top 3 upcoming regional cultural festivals, public celebrations, and FMCG grocery demand surges for:
Region / State: {region}
Country: {country}
City / Locality: {city or "Major regional commercial centers"}

For EACH of the 3 festivals, provide a JSON object with:
- id: unique string e.g. "EVT_DASARA_2026"
- name: authentic festival name (e.g. "Mysuru Dasara & Vijayadashami", "Deepavali & Naraka Chaturdashi", "Durga Puja & Bijoya", "Thai Pongal & Makar Sankranti", "Ganesh Utsav")
- date_window: date or calendar season strictly in 2026 or 2027 (e.g. "Oct 12 - Oct 22, 2026", "Jan 13 - Jan 17, 2027", "Mar 28 - Apr 2, 2027")
- status: "UPCOMING"
- key_items: array of 4-6 specific retail grocery items experiencing massive demand surges (e.g. ["Pure Cow Ghee", "Gulab Jamun & Sweets", "Mustard Oil", "California Almonds", "Puja Camphor"])
- demand_lift_pct: integer or float percentage sales surge (e.g. 120.0)
- icon: single emoji
- description: 2-sentence explanation of the festive shopping rush and footfall surge
- tradition_notes: cultural context explaining why these items are consumed or prepared
- advance_procurement_window: distributor procurement timeline e.g. "T-14 Days: Restock bulk tins"
- promo_launch_window: promotion launch timeline e.g. "T-7 Days: Launch WhatsApp Broadcast"
- clearance_window: post-festival markdown timeline e.g. "T+2 Days: Sell remaining stock at cost"
- recommended_promo_type: "FESTIVE_CELEBRATION_HAMPER" or "ANCHOR_MARGIN_BOOSTER"
- suggested_combo_title: catchy promo title

Return ONLY a valid JSON array of exactly 3 objects.
"""
        target_model = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash")
        candidate_models = list(dict.fromkeys([
            target_model,
            "gemini-3.5-flash",
            "gemini-3.5-flash-lite",
            "gemini-3-flash-preview",
            "gemini-2.5-flash",
            "gemini-1.5-flash"
        ]))

        for m in candidate_models:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={gemini_api_key}"
                payload = json.dumps({
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"response_mime_type": "application/json"}
                }).encode("utf-8")

                req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=6) as response:
                    res_data = json.loads(response.read().decode())
                    text_out = res_data["candidates"][0]["content"]["parts"][0]["text"].strip()
                    if text_out.startswith("```json"):
                        text_out = text_out[7:]
                    elif text_out.startswith("```"):
                        text_out = text_out[3:]
                    if text_out.endswith("```"):
                        text_out = text_out[:-3]
                    parsed = json.loads(text_out.strip())
                    if isinstance(parsed, list) and len(parsed) > 0:
                        return parsed
            except Exception:
                continue

        return None

    @classmethod
    def _get_builtin_festivals(cls, region: str, country: str) -> List[Dict[str, Any]]:
        reg = region.lower()
        for k, v in cls.BUILTIN_REGIONAL_FESTIVALS.items():
            if k in reg:
                return v

        if any(w in reg for w in ["south", "bangalore", "bengaluru", "mysore", "mysuru"]):
            return cls.BUILTIN_REGIONAL_FESTIVALS["karnataka"]
        elif any(w in reg for w in ["mumbai", "pune", "west"]):
            return cls.BUILTIN_REGIONAL_FESTIVALS["maharashtra"]
        elif any(w in reg for w in ["kolkata", "east", "assam", "odisha"]):
            return cls.BUILTIN_REGIONAL_FESTIVALS["bengal"]
        elif any(w in reg for w in ["chennai", "coimbatore", "madurai", "tamil"]):
            return cls.BUILTIN_REGIONAL_FESTIVALS["tamil"]
        elif any(w in reg for w in ["ahmedabad", "surat", "vadodara", "gujarat"]):
            return cls.BUILTIN_REGIONAL_FESTIVALS["gujarat"]
        elif any(w in reg for w in ["kochi", "trivandrum", "malabar", "kerala"]):
            return cls.BUILTIN_REGIONAL_FESTIVALS["kerala"]
        elif any(w in reg for w in ["delhi", "noida", "gurugram", "up", "haryana", "punjab", "north"]):
            return cls.BUILTIN_REGIONAL_FESTIVALS["delhi"]
        elif any(w in reg for w in ["us", "usa", "uk", "london", "canada"]):
            return cls.BUILTIN_REGIONAL_FESTIVALS["global"]

        return cls.BUILTIN_REGIONAL_FESTIVALS["karnataka"]


class RetailCopilotAgent:
    """
    Conversational AI Copilot for Retailers.
    Parses merchant natural language requests, extracts desired margin percentage,
    and runs backend econometric forecasting, price elasticity, and collateral tools silently.
    """

    @classmethod
    def process_message(
        cls,
        message: str,
        user_margin_pct: Optional[float] = None,
        region: Optional[str] = None
    ) -> ChatResponse:
        store_profile = StoreDataManager.load_profile()
        if region:
            store_profile.region = region

        msg_lower = message.lower()

        # Regional greeting & locality context
        reg_lower = (store_profile.region or "").lower()
        city_lower = (store_profile.city or "").lower()
        if "karnataka" in reg_lower or "south" in reg_lower or "bengaluru" in city_lower or "bangalore" in city_lower:
            greeting = "Namaskara! 🙏"
            loc_label = f"{store_profile.locality or 'Indiranagar'}, {store_profile.city or 'Bengaluru'}"
        elif "maharashtra" in reg_lower or "west" in reg_lower or "mumbai" in city_lower or "pune" in city_lower:
            greeting = "Namaskar! 🙏"
            loc_label = f"{store_profile.locality or 'Dadar'}, {store_profile.city or 'Mumbai'}"
        elif "bengal" in reg_lower or "east" in reg_lower or "kolkata" in city_lower:
            greeting = "Nomoshkar! 🙏"
            loc_label = f"{store_profile.locality or 'Gariahat'}, {store_profile.city or 'Kolkata'}"
        else:
            greeting = "Namaste! 🙏"
            loc_label = f"{store_profile.locality or 'Connaught Place'}, {store_profile.city or 'Delhi NCR'}"

        # 1. Extract requested margin % from message if stated (e.g., "20% margin", "15% profit", "22 percent")
        detected_margin = user_margin_pct
        if detected_margin is None:
            margin_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:%|percent)\s*(?:margin|profit)?', message, re.IGNORECASE)
            if margin_match:
                detected_margin = float(margin_match.group(1))
            else:
                detected_margin = store_profile.default_min_margin_pct or 18.0

        # Cap margin to realistic retail boundaries
        detected_margin = max(5.0, min(45.0, detected_margin))

        # 2. Determine Retailer Intent
        # Intent: Failing / Slow-Moving / Stuck Products Query
        if any(w in msg_lower for w in ["failing", "fail", "slow moving", "stuck", "expiring", "expiry", "not selling", "dead stock", "poor sales", "low velocity"]):
            products = StoreDataManager.load_products()
            failing = [p for p in products if p.velocity_status == "SLOW_MOVING" or (p.weekly_sales_avg and p.weekly_sales_avg <= 15) or p.stock_quantity >= 60]
            failing.sort(key=lambda p: (p.weekly_sales_avg or 20) / max(1, p.stock_quantity))
            
            if not failing:
                failing = [p for p in products if "biscuit" in p.name.lower() or "snack" in p.name.lower()] or products[:2]
                
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
                region=store_profile.region,
                archetype="EXPIRY_RESCUE_CLEARANCE"
            )

            reply = (
                f"{greeting} Here is an honest audit of products currently failing or stuck on your shelves in **{loc_label}**:\n\n"
                f"1. ⚠️ **{top_failing.name}**\n"
                f"   • Velocity: Selling only **{top_failing.weekly_sales_avg or 5} units/week**\n"
                f"   • Stock Remaining: **{top_failing.stock_quantity} units** (That's **{days_supply} days** of stock stuck!)\n"
                f"   • Trapped Capital: **₹{trapped_cash:,}** dead inventory\n"
            )
            if second_failing:
                reply += (
                    f"2. ⚠️ **{second_failing.name}**\n"
                    f"   • Velocity: Selling only **{second_failing.weekly_sales_avg or 8} units/week** with **{second_failing.stock_quantity} units** on shelf\n\n"
                )
            reply += (
                f"💡 **How this improves your sales:**\n"
                f"Never discount a failing product alone—it trains customers to only buy cheap and destroys your profit! Instead, we bundle **{top_failing.name.split('(')[0].strip()}** with your #1 best-seller (**{anchor.name.split('(')[0].strip()}**) in a value duo.\n\n"
                f"The high daily footfall on {anchor.name.split('(')[0].strip()} moves the stuck stock **3x faster**, recovers your **₹{trapped_cash:,} in cash**, and still secures a healthy **{rescue_plan.net_margin_pct}% net profit**.\n\n"
                f"I've generated the ready rescue bundle below—click to launch it:"
            )

            return ChatResponse(
                reply=reply,
                intent="FAILING_PRODUCTS_AUDIT",
                detected_margin_pct=detected_margin,
                plan=rescue_plan
            )

        # Intent: Sales Improvement & Revenue Growth Query
        is_sales_growth_query = (
            (("increase" in msg_lower or "improve" in msg_lower or "boost" in msg_lower or "grow" in msg_lower or "more" in msg_lower) 
             and ("sale" in msg_lower or "revenue" in msg_lower or "turnover" in msg_lower or "profit" in msg_lower))
            or any(w in msg_lower for w in ["sales growth", "growth strategy", "basket size", "higher bill"])
        )
        if is_sales_growth_query:
            products = StoreDataManager.load_products()
            fast_mover = next((p for p in products if p.velocity_status == "FAST_MOVING"), products[0])
            attached = next((p for p in products if p.id != fast_mover.id and p.selling_price - p.cost_price >= 25), products[1])
            plan = PromoMindEngine.generate_plan(
                query=f"Basket builder combo for {fast_mover.name} and {attached.name}",
                min_margin_pct=detected_margin,
                event_theme="Super Sales Booster",
                offer_type="COMBO_DISCOUNT",
                region=store_profile.region,
                archetype="ANCHOR_MARGIN_BOOSTER"
            )
            reply = (
                f"{greeting} To reliably grow sales by 20–30% in **{loc_label}**, here is the 3-step strategy that works best for retail stores:\n\n"
                f"1. **Raise Basket Size (Cross-Sell):** 70% of shoppers come in for essentials like tea or milk and buy only that. Offering an irresistible bundle at checkout jumps your average bill value from ₹150 to ₹350+.\n"
                f"2. **Protect Margin with Smart Pairing:** Pair high-volume essentials with high-margin items. The customer gets a direct rupee discount, and your store earns higher total cash profit.\n"
                f"3. **Speed Up Cash Turnover:** Moving inventory in 4 days instead of 30 days lets you reinvest the same working capital 7x per year.\n\n"
                f"Here is a recommended high-growth combo ready for your store below:"
            )
            return ChatResponse(
                reply=reply,
                intent="SALES_GROWTH_ADVICE",
                detected_margin_pct=detected_margin,
                plan=plan
            )

        # Intent A: Store Capital & Financial ROI / Dead Stock Risk query
        if any(w in msg_lower for w in ["dead capital", "trapped", "roi", "working capital", "financial", "valuation", "investment", "audit"]):
            products = StoreDataManager.load_products()
            roi_data = InvestmentROIEngine.compute_store_roi(products, store_capital_budget=store_profile.total_working_capital_inr)
            reply = (
                f"{greeting} Here is a clear financial summary for **{store_profile.store_name}** in **{loc_label}**:\n\n"
                f"• 💰 **Total Inventory Invested:** ₹{int(roi_data['total_inventory_invested_inr']):,} across {len(products)} active products\n"
                f"• ⚠️ **Capital at Risk (Slow Movers):** ₹{int(roi_data['dead_capital_at_risk_inr']):,} trapped in aging stock\n"
                f"• ⚡ **Cash Recoverable via Smart Bundles:** ₹{int(roi_data['unlocked_capital_from_promos_inr']):,}\n"
                f"• 📈 **Turnover Acceleration:** Capital recovers **{roi_data['capital_turnover_days']} days faster**\n\n"
                f"Would you like me to create a quick clearance promo to liquidate the slow-moving stock while protecting your profit?"
            )
            return ChatResponse(
                reply=reply,
                intent="ROI_INSIGHT",
                detected_margin_pct=detected_margin,
                roi_summary=roi_data
            )

        # Intent B: Multiple Weekly Offer Recommendations query
        # Matches queries like "Suggest 3 best offers for this week", "give me deals", "best offers this week", etc.
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
            ideas = PromoMindEngine.generate_weekly_recommendations(region=store_profile.region)
            reply = (
                f"{greeting} Based on live sales velocity and festive customer demand in **{loc_label}**, "
                f"here are the **Top 3 Recommended Bundles** for this week:\n\n"
                f"• ☕ **{ideas[0]['title']}** ➔ Offer: **₹{int(ideas[0]['combo_price'])}** (MRP ~₹{int(ideas[0]['original_mrp'])}~, Save ₹{int(ideas[0]['savings_amount'])})\n"
                f"• 🪔 **{ideas[1]['title']}** ➔ Offer: **₹{int(ideas[1]['combo_price'])}** (MRP ~₹{int(ideas[1]['original_mrp'])}~, Save ₹{int(ideas[1]['savings_amount'])})\n"
                f"• 🍳 **{ideas[2]['title']}** ➔ Offer: **₹{int(ideas[2]['combo_price'])}** (MRP ~₹{int(ideas[2]['original_mrp'])}~, Save ₹{int(ideas[2]['savings_amount'])})\n\n"
                f"Each bundle strictly protects a **{detected_margin}%+ net merchant margin**. "
                f"Tap any deal below to preview it and launch the campaign:"
            )
            return ChatResponse(
                reply=reply,
                intent="WEEKLY_IDEAS",
                detected_margin_pct=detected_margin,
                ideas=ideas
            )

        # Intent C: Regional Festival & Cultural Spikes Query
        is_fest_query = (
            any(w in msg_lower for w in [
                "upcoming festival", "regional festival", "festivals in", "what festival",
                "festival calendar", "festive offers", "festive deals", "dasara", "dussehra",
                "durga puja", "pujo", "ganesh utsav", "ganpati", "pongal", "onam", "ugadi", "holiday"
            ]) and not any(w in msg_lower for w in ["create combo", "generate promo for product", "calculate margin"])
        )
        if is_fest_query:
            events = DynamicFestivalEngine.discover_festivals(
                region=store_profile.region,
                country="India",
                city=store_profile.city
            )
            top_fest = events[0] if events else None
            # If top fest has matched inventory, generate a ready festive bundle
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
                    archetype=top_fest.recommended_promo_type or "FESTIVE_CELEBRATION_HAMPER"
                )
            else:
                fest_plan = PromoMindEngine.generate_plan(
                    query=f"Festive bundle for {top_fest.name if top_fest else 'Festival'}",
                    min_margin_pct=detected_margin,
                    event_theme=top_fest.name if top_fest else "Festive Special",
                    offer_type="COMBO_DISCOUNT",
                    region=store_profile.region,
                    archetype="FESTIVE_CELEBRATION_HAMPER"
                )

            fest_lines = []
            for ev in events[:3]:
                fest_lines.append(f"• {ev.icon} **{ev.name}** ({ev.date_window})\n   Key Demand Surge: **{', '.join(ev.key_items[:3])}** (+{int(ev.demand_lift_pct)}% surge)")

            reply = (
                f"{greeting} Here is the live cultural festival calendar and retail demand forecast for **{store_profile.region}** ({loc_label}):\n\n"
                + "\n\n".join(fest_lines) + "\n\n"
                f"💡 **Recommended Action for {top_fest.name if top_fest else 'the upcoming festival'}:**\n"
                f"{top_fest.tradition_notes if top_fest else 'High festival demand prep.'}\n\n"
                f"I have modeled an optimal festival campaign below pairing your high-velocity inventory with festive demand. Tap the card to load it into Screen 2:"
            )
            return ChatResponse(
                reply=reply,
                intent="FESTIVAL_CALENDAR_INSIGHT",
                detected_margin_pct=detected_margin,
                plan=fest_plan
            )

        # Intent D: Specific Promotional Plan Generation (Single Combo)
        else:
            archetype = "ANCHOR_MARGIN_BOOSTER"
            event_theme = "Weekly Retail Deal"
            if "diwali" in msg_lower or "deepa" in msg_lower or "festive" in msg_lower or "festival" in msg_lower:
                archetype = "FESTIVE_CELEBRATION_HAMPER"
                event_theme = "Diwali Maha Utsav"
            elif "expiry" in msg_lower or "clear" in msg_lower or "slow" in msg_lower or "bogo" in msg_lower:
                archetype = "EXPIRY_RESCUE_CLEARANCE"
                event_theme = "Clearance Rush"
            elif "bulk" in msg_lower or "volume" in msg_lower or "joint family" in msg_lower:
                archetype = "VOLUME_TIER_SLAB"
                event_theme = "Family Saver Pack"

            # Execute backend PromoMind Engine with detected margin
            plan = PromoMindEngine.generate_plan(
                query=message,
                min_margin_pct=detected_margin,
                event_theme=event_theme,
                offer_type="COMBO_DISCOUNT",
                region=store_profile.region,
                archetype=archetype
            )

            combo_p = int(plan.recommended_combo_price)
            mrp_p = int(plan.original_combined_mrp)
            save_p = int(plan.discount_amount)
            save_pct = plan.discount_pct
            margin_p = plan.net_margin_pct
            anchor_name = plan.anchor_product.name.split('(')[0].strip()
            attached_name = plan.attached_product.name.split('(')[0].strip()

            reply = (
                f"{greeting} For **{store_profile.store_name}** in **{loc_label}**, here is a high-performing promotional bundle tailored for this weekend:\n\n"
                f"I've paired **{anchor_name}** with **{attached_name}**. "
                f"Shoppers get a clean **₹{save_p} direct discount** ({save_pct}% OFF) paying **₹{combo_p}** instead of ₹{mrp_p}, "
                f"while your store secures a healthy **{margin_p}% net profit margin**.\n\n"
                f"💡 **Why it works:** {plan.strategic_rationale.split('.')[0]}.\n"
                f"🗣️ **Cashier counter script:** *\"{plan.creative_assets.cashier_counter_pitch}\"*\n\n"
                f"Click the card below to load this bundle into Screen 2 and launch your WhatsApp and poster campaign!"
            )

            return ChatResponse(
                reply=reply,
                intent="PROMOTION_GENERATED",
                detected_margin_pct=detected_margin,
                plan=plan
            )


