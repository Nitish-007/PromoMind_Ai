import os
import sys
import math
import json
import urllib.request
from typing import Tuple, Dict, Any, Optional, List

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from models import Product, DemandForecast, ComboPlan, CreativeAssets, ROIMetrics
from mock_data import AFFINITY_MATRIX, DEMAND_FORECASTS
from storage import StoreDataManager
from forecasting import OpenSourceForecastingEngine

class DemandAndInventoryAgent:
    """Identifies high-surge anchor items and pairs them with high-margin or slow-moving items."""
    
    @staticmethod
    def find_products_from_prompt(prompt: str) -> Tuple[Product, Product, float, str]:
        prompt_lower = prompt.lower()
        products = StoreDataManager.load_products()
        
        # Product resolution heuristics
        anchor = None
        attached = None
        
        # Detect explicit mentions
        if "tea" in prompt_lower and "biscuit" in prompt_lower:
            anchor = next((p for p in products if p.id == "PROD_TEA_01"), products[0])
            attached = next((p for p in products if p.id == "PROD_BISCUIT_01"), products[1])
            driver = "High affinity tea-time pairing with near-expiry stock clearance"
        elif "ghee" in prompt_lower or "almond" in prompt_lower or "diwali" in prompt_lower:
            anchor = next((p for p in products if p.id == "PROD_GHEE_01"), products[2] if len(products) > 2 else products[0])
            attached = next((p for p in products if p.id == "PROD_ALMOND_01"), products[3] if len(products) > 3 else products[1])
            driver = "Festive sweet-making season surge + premium dry fruit clearance"
        elif "oil" in prompt_lower or "masala" in prompt_lower:
            anchor = next((p for p in products if p.id == "PROD_OIL_01"), products[4] if len(products) > 4 else products[0])
            attached = next((p for p in products if p.id == "PROD_MASALA_01"), products[5] if len(products) > 5 else products[1])
            driver = "Cooking staple basket driver + slow-moving spice turnover"
        else:
            # Check if any product name is explicitly mentioned in prompt
            for p in products:
                if p.name.lower().split()[0] in prompt_lower:
                    anchor = p
                    break
                    
            if not anchor:
                # Default proactive strategy: pick highest forecasted demand surge as anchor
                forecast = sorted(DEMAND_FORECASTS, key=lambda f: f.projected_surge_pct, reverse=True)[0]
                anchor = next((p for p in products if p.id == forecast.product_id), products[0])
            
            # Pick attached slow-moving item with highest affinity
            affinities = AFFINITY_MATRIX.get(anchor.id, {})
            slow_items = [p for p in products if p.velocity_status == "SLOW_MOVING" and p.id != anchor.id]
            slow_items.sort(key=lambda p: affinities.get(p.id, 0), reverse=True)
            attached = slow_items[0] if slow_items else (products[1] if len(products) > 1 else products[0])
            driver = f"Proactive surge hook paired with inventory clearance"
            
        # Get affinity score
        affinity = AFFINITY_MATRIX.get(anchor.id, {}).get(attached.id, 58.5)
        return anchor, attached, affinity, driver


class PricingAndMarginAgent:
    """Calculates consumer-attractive price points across diverse offer formats while protecting margins."""
    
    @staticmethod
    def optimize_price(
        anchor: Product, 
        attached: Product, 
        min_margin_pct: float = 18.0,
        offer_type: str = "COMBO_DISCOUNT"
    ) -> Tuple[float, float, float, float, float]:
        combined_mrp = anchor.selling_price + attached.selling_price
        combined_cost = anchor.cost_price + attached.cost_price
        
        # Calculate tentative price according to offer structure
        if offer_type == "BOGO_50_OFF":
            # Buy anchor at regular price, get attached at 50% discount
            tentative_price = anchor.selling_price + (attached.selling_price * 0.50)
        elif offer_type == "FESTIVAL_MEGA_SAVER":
            # Aggressive festival rush discount (~22% off)
            tentative_price = combined_mrp * 0.78
        elif offer_type == "CLEARANCE_CROSS_SELL":
            # Anchor at regular price + attached heavily discounted to clear dead stock
            tentative_price = anchor.selling_price + (attached.selling_price * 0.65)
        else: # Standard COMBO_DISCOUNT
            target_discount_pct = 0.17
            tentative_price = combined_mrp * (1.0 - target_discount_pct)
        
        # Round to nearest psychological retail number ending in 9 (e.g., 249, 389, 799, 899)
        rounded_price = math.floor(tentative_price / 10) * 10 + 9
        
        # Margin Check
        margin = (rounded_price - combined_cost) / max(1.0, rounded_price) * 100.0
        
        if margin < min_margin_pct:
            # Adjust price upwards to satisfy minimum margin
            required_price = combined_cost / (1.0 - (min_margin_pct / 100.0))
            rounded_price = math.ceil(required_price / 10) * 10 + 9
            margin = (rounded_price - combined_cost) / max(1.0, rounded_price) * 100.0

        # Retail safeguard: Combo price should never exceed combined individual MRP
        if rounded_price > combined_mrp:
            rounded_price = combined_mrp
            margin = (rounded_price - combined_cost) / max(1.0, rounded_price) * 100.0
            
        discount_amount = max(0.0, round(combined_mrp - rounded_price, 2))
        discount_pct = round((discount_amount / combined_mrp) * 100.0, 1) if combined_mrp > 0 else 0.0
        
        return combined_mrp, rounded_price, discount_amount, discount_pct, round(margin, 1)


class ROIPredictorAgent:
    """Simulates 10-day promotional performance vs status quo."""
    
    @staticmethod
    def simulate_roi(anchor: Product, attached: Product, combo_price: float, margin_pct: float) -> ROIMetrics:
        baseline_units = attached.weekly_sales_avg * 2  # ~10 days
        
        # Uplift factor driven by combo discount & anchor velocity
        lift_factor = 3.8 if attached.velocity_status == "SLOW_MOVING" else 2.2
        projected_units = int(baseline_units * lift_factor)
        
        baseline_rev = (anchor.selling_price * anchor.weekly_sales_avg * 1.5) + (attached.selling_price * baseline_units)
        projected_rev = projected_units * combo_price
        revenue_lift = round(projected_rev - baseline_rev, 2)
        
        # Dead stock clearance %
        stock_cleared_pct = min(100.0, round((projected_units / max(attached.stock_quantity, 1)) * 100.0, 1))
        
        profit_inr = round(projected_rev * (margin_pct / 100.0), 2)
        
        return ROIMetrics(
            baseline_units_10d=baseline_units,
            projected_units_10d=projected_units,
            units_lift_pct=round(((projected_units - baseline_units) / max(baseline_units, 1)) * 100.0, 1),
            projected_revenue_inr=projected_rev,
            revenue_lift_inr=revenue_lift,
            dead_stock_cleared_pct=stock_cleared_pct,
            projected_gross_margin_pct=margin_pct,
            projected_net_profit_inr=profit_inr
        )


class GeminiCreativeAgent:
    """Generates marketing copy and poster assets via Gemini API or intelligent offline template."""
    
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
        offer_type: str = "COMBO_DISCOUNT"
    ) -> CreativeAssets:
        gemini_api_key = os.environ.get("GEMINI_API_KEY")
        
        # Human readable offer format
        offer_type_labels = {
            "BOGO_50_OFF": f"Buy {anchor.name.split('(')[0].strip()}, Get {attached.name.split('(')[0].strip()} at 50% OFF!",
            "FESTIVAL_MEGA_SAVER": f"Festival Mega Savings Pack — Save ₹{int(discount_amount)}",
            "CLEARANCE_CROSS_SELL": f"Exclusive Stock Clearance Duo — {discount_pct}% OFF",
            "COMBO_DISCOUNT": f"Special Combo Saver — Save ₹{int(discount_amount)}"
        }
        offer_headline_label = offer_type_labels.get(offer_type, "Special Combo Deal")
        
        # If API key is available in environment, make live Gemini request
        if gemini_api_key:
            try:
                prompt_content = f"""
                You are PromoMind AI, an elite retail copywriter for Indian Kirana & supermarkets.
                Create high-converting promotional copy for a retail offer:
                Festival / Event Theme: {event_theme}
                Offer Format: {offer_headline_label}
                Combo: {anchor.name} + {attached.name}
                Combo Price: Rs. {combo_price} (Save Rs. {discount_amount} / {discount_pct}% OFF)
                Theme / Occasion: {driver}
                
                Respond in valid JSON format with exactly these keys:
                - poster_headline: (Punchy 4-6 word headline incorporating the event {event_theme})
                - poster_subheading: (Short context subtitle emphasizing savings or occasion)
                - poster_badge: (e.g., '{event_theme.upper()} SPECIAL • SAVE ₹{int(discount_amount)}')
                - poster_body: (2 lines highlighting the pairing, festival benefits, and value)
                - whatsapp_message: (Engaging WhatsApp broadcast with festive emojis, pricing, savings, and call to action)
                - pos_tagline: (Snappy 1-liner printed on bill receipts)
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
                    return CreativeAssets(**parsed)
            except Exception:
                pass  # Fall back to high quality deterministic generation
                
        # Deterministic High-Quality Fallback (Guarantees 100% uptime for demo/offline execution)
        anchor_short = anchor.name.split('(')[0].strip()
        attached_short = attached.name.split('(')[0].strip()
        is_festive = "diwali" in event_theme.lower() or "festive" in event_theme.lower() or "ghee" in anchor.name.lower() or "sweet" in anchor.name.lower()
        
        if is_festive:
            headline = f"{event_theme}: {anchor_short} + {attached_short}"
            subheading = f"Celebrate with Premium Delights & Guaranteed Savings"
            badge = f"{event_theme.upper()} • SAVE ₹{int(discount_amount)}"
            body = f"Pair authentic {anchor.name} with nutritious {attached.name}. Perfect for festive sweet-making & gifting!"
            whatsapp = (
                f"🪔 *{event_theme.upper()} SPECIAL SAVINGS at Sharma General Store!* 🪔\n\n"
                f"💥 *Offer:* {offer_headline_label}\n"
                f"✨ *Combo Items:* {anchor.name} + {attached.name}\n\n"
                f"❌ Combined MRP: ~₹{int(anchor.selling_price + attached.selling_price)}~\n"
                f"🔥 *Exclusive Offer Price: ₹{int(combo_price)} only!*\n"
                f"💰 *Instant Cash Savings: ₹{int(discount_amount)} ({discount_pct}% OFF)*\n\n"
                f"📍 *Available at:* Sharma Supermarket, Indiranagar, Bengaluru\n"
                f"⚡ *Limited Stock:* Valid during {event_theme} or while stock lasts!\n"
                f"Reply 'BOOK' on WhatsApp to reserve your pack today!"
            )
            pos_tagline = f"{event_theme}: Save ₹{int(discount_amount)} on {anchor_short} + {attached_short} pack today!"
        else:
            headline = f"{event_theme}: Daily Super Duo Pack"
            subheading = f"Everyday Kitchen Essentials at Unbeatable Prices"
            badge = f"{event_theme.upper()} • {discount_pct}% OFF"
            body = f"Enjoy royal quality {anchor.name} paired with {attached.name}."
            whatsapp = (
                f"⚡ *{event_theme.upper()} EXCLUSIVE DEAL!* ⚡\n\n"
                f"Upgrade your household pantry with our verified value duo:\n"
                f"🛒 *{anchor.name}* + *{attached.name}*\n\n"
                f"❌ MRP: ~₹{int(anchor.selling_price + attached.selling_price)}~\n"
                f"💥 *Special Deal Price: ₹{int(combo_price)}!*\n"
                f"💵 *Your Savings: ₹{int(discount_amount)} ({discount_pct}% OFF)*\n\n"
                f"📍 Sharma Kirana, 12th Main Road, Bengaluru\n"
                f"Grab yours today before stock runs out!"
            )
            pos_tagline = f"{event_theme}: Save ₹{int(discount_amount)} on {anchor_short} + {attached_short} at checkout!"
            
        return CreativeAssets(
            poster_headline=headline,
            poster_subheading=subheading,
            poster_badge=badge,
            poster_body=body,
            whatsapp_message=whatsapp,
            pos_tagline=pos_tagline
        )


class PromoMindEngine:
    """Master Orchestrator uniting Demand Forecasting, Pricing, ROI, and Creative Agents."""
    
    @classmethod
    def generate_plan(
        cls, 
        query: str, 
        min_margin_pct: float = 18.0,
        event_theme: str = "Diwali Maha Utsav",
        offer_type: str = "COMBO_DISCOUNT"
    ) -> ComboPlan:
        # Step 1: Detect items & affinity
        anchor, attached, affinity, driver = DemandAndInventoryAgent.find_products_from_prompt(query)
        
        # Step 2: Compute Association Probability (Apriori Mining)
        prob_metrics = OpenSourceForecastingEngine.calculate_co_purchase_probability(
            anchor.id, attached.id, affinity
        )
        
        # Step 3: Run Open-Source Holt-Winters Demand Forecasting on Anchor SKU
        past_sales = anchor.past_sales_weeks or [30, 32, 35, 38, 42, 45]
        event_surge = 75.0 if "diwali" in event_theme.lower() else (40.0 if "monsoon" in event_theme.lower() else 25.0)
        forecast_result = OpenSourceForecastingEngine.predict_demand_surge(
            past_sales, event_surge_pct=event_surge
        )
        
        # Step 4: Calculate pricing & margin based on offer format
        combined_mrp, combo_price, disc_amt, disc_pct, net_margin = PricingAndMarginAgent.optimize_price(
            anchor, attached, min_margin_pct, offer_type
        )
        
        # Step 5: Simulate ROI metrics
        roi = ROIPredictorAgent.simulate_roi(anchor, attached, combo_price, net_margin)
        
        # Step 6: Generate marketing copy & creatives
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
            offer_type=offer_type
        )
        
        tagline = f"{event_theme} Special | Save ₹{int(disc_amt)} ({disc_pct}% OFF) | Protects {net_margin}% Retail Margin"
        
        rationale = (
            f"Event Signal: '{event_theme}' drives high demand on '{anchor.name}' "
            f"(Predicted growth: {forecast_result['expected_growth_pct']:+}% over next 4 weeks). "
            f"Paired with '{attached.name}' ({attached.velocity_status}, {attached.expiry_days or 90}d shelf life remaining) "
            f"via Co-Purchase Confidence {prob_metrics['confidence_pct']}% (Lift: {prob_metrics['lift_score']}x). "
            f"Structured as '{offer_type.replace('_', ' ')}' at ₹{int(combo_price)} to accelerate clearance by {roi.dead_stock_cleared_pct}% "
            f"while preserving a secure {net_margin}% net margin."
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
            target_customer_segment=f"{event_theme} Shoppers & Value Seekers",
            strategic_rationale=rationale,
            creative_assets=creatives,
            roi_prediction=roi,
            event_theme=event_theme,
            offer_type=offer_type,
            co_purchase_probability=prob_metrics,
            forecasting_summary=forecast_result
        )
