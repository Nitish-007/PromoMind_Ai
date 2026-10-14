import os
import sys
import math
import json
import urllib.request
from typing import Tuple, Dict, Any, Optional, List

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from models import Product, DemandForecast, ComboPlan, CreativeAssets, ROIMetrics, StoreProfile
from mock_data import AFFINITY_MATRIX, DEMAND_FORECASTS
from storage import StoreDataManager
from forecasting import OpenSourceForecastingEngine, PriceElasticityOptimizer

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
        
        # Detect explicit mentions
        if "tea" in prompt_lower and "biscuit" in prompt_lower:
            anchor = next((p for p in products if p.id == "PROD_TEA_01"), products[0])
            attached = next((p for p in products if p.id == "PROD_BISCUIT_01"), products[1])
            driver = "High affinity tea-time pairing with near-expiry stock clearance"
        elif "ghee" in prompt_lower or "almond" in prompt_lower or "diwali" in prompt_lower or "deepa" in prompt_lower:
            anchor = next((p for p in products if p.id == "PROD_GHEE_01"), products[2] if len(products) > 2 else products[0])
            attached = next((p for p in products if p.id == "PROD_ALMOND_01"), products[3] if len(products) > 3 else products[1])
            driver = "Festive sweet-making season surge + premium dry fruit clearance"
        elif "oil" in prompt_lower or "masala" in prompt_lower:
            anchor = next((p for p in products if p.id == "PROD_OIL_01"), products[4] if len(products) > 4 else products[0])
            attached = next((p for p in products if p.id == "PROD_MASALA_01"), products[5] if len(products) > 5 else products[1])
            driver = "Cooking staple basket driver + slow-moving spice turnover"
        else:
            for p in products:
                if p.name.lower().split()[0] in prompt_lower:
                    anchor = p
                    break
                    
            if not anchor:
                forecast = sorted(DEMAND_FORECASTS, key=lambda f: f.projected_surge_pct, reverse=True)[0]
                anchor = next((p for p in products if p.id == forecast.product_id), products[0])
            
            affinities = AFFINITY_MATRIX.get(anchor.id, {})
            slow_items = [p for p in products if p.velocity_status == "SLOW_MOVING" and p.id != anchor.id]
            slow_items.sort(key=lambda p: affinities.get(p.id, 0), reverse=True)
            attached = slow_items[0] if slow_items else (products[1] if len(products) > 1 else products[0])
            driver = f"Proactive surge hook paired with inventory clearance"
            
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
            fest_greeting = "Diwali Ki Hardik Shubhkamnayein!" if "diwali" in event_theme.lower() else "Kirana Super Dhamaka Deal!"
            vernacular_tag = "Maha Bachat Pack"
            cashier_script = f"Bhaiya/Bhabhi, {anchor.name.split('(')[0].strip()} ke saath {attached.name.split('(')[0].strip()} pack lene par ₹{int(discount_amount)} ki bachat hai, bill me add kar doon?"

        # Human readable offer format
        offer_headline_label = f"{archetype.replace('_', ' ').title()} — Save ₹{int(discount_amount)} ({discount_pct}% OFF)"
        
        # If API key is available in environment, make live Gemini request
        if gemini_api_key:
            try:
                prompt_content = f"""
                You are PromoMind AI, an elite retail copywriter for Indian Kirana & supermarkets.
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
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_api_key}"
                payload = json.dumps({
                    "contents": [{"parts": [{"text": prompt_content}]}],
                    "generationConfig": {"response_mime_type": "application/json"}
                }).encode("utf-8")
                
                req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=5) as response:
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
        
        tagline = f"{event_theme} Special | Save ₹{int(disc_amt)} ({disc_pct}% OFF) | Protects {net_margin}% Retail Margin"
        
        rationale = (
            f"Regional Signal for {store_profile.region}: '{event_theme}' accelerates demand on '{anchor.name}' "
            f"(Predicted growth: {forecast_result['expected_growth_pct']:+}% over next 4 weeks). "
            f"Paired with '{attached.name}' ({attached.velocity_status}, {attached.expiry_days or 90}d shelf life) "
            f"via Co-Purchase Confidence {prob_metrics['confidence_pct']}% (Lift: {prob_metrics['lift_score']}x). "
            f"Optimized via Open-Source Price Elasticity ({pricing_result['blended_elasticity']}) under archetype '{archetype}' at ₹{int(combo_price)} "
            f"to drive +{pricing_result['volume_lift_pct']}% volume lift while securing a {net_margin}% net profit margin."
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
            forecasting_summary=forecast_result
        )
