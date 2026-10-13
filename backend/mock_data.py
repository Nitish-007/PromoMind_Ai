import os
import sys
from typing import List, Dict, Any, Optional

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from models import Product, DemandForecast

# Realistic Inventory Dataset for an Urban Kirana / Supermarket
INVENTORY_DATA: List[Product] = [
    Product(
        id="PROD_TEA_01",
        name="Taj Mahal Premium Gold Tea (500g)",
        category="Beverages",
        cost_price=240.0,
        selling_price=310.0,
        stock_quantity=140,
        days_in_stock=12,
        expiry_days=360,
        velocity_status="FAST_MOVING",
        weekly_sales_avg=52,
        image_url="tea.png",
        past_sales_weeks=[42, 45, 48, 50, 52, 55],
        forecast_sales_weeks=[58, 64, 72, 78],
        sell_through_verdict="STRONG_INVEST_BUY",
        verdict_badge="🟢 Strong Buy / Restock Now",
        days_inventory_remaining=18,
        sell_through_rate_pct=89.2,
        reorder_recommendation="High Velocity Anchor (+35% monsoon/weekend surge): Current stock of 140 units will exhaust in ~18 days. Invest in a 50kg wholesale replenishment immediately to secure dealer discount.",
        brand_comparison_insight="Taj Mahal dominates local chai consumption (74% brand retention in Indiranagar). While Brooke Bond Red Label offers ~2% higher retailer margins, Taj Mahal sells 35% faster. Do not switch away; retain as prime anchor.",
        alternative_brands=[
            "Tata Tea Gold (500g) — 26% margin, +15% pull",
            "Brooke Bond Red Label (500g) — 24% margin, steady volume",
            "Wagh Bakri Premium (500g) — 28% margin, regional favorite"
        ]
    ),
    Product(
        id="PROD_BISCUIT_01",
        name="Britannia Good Day Butter Cookies (Pack of 6)",
        category="Bakery & Snacks",
        cost_price=110.0,
        selling_price=160.0,
        stock_quantity=195,
        days_in_stock=48,
        expiry_days=24,  # Expiring soon! Needs clearance
        velocity_status="SLOW_MOVING",
        weekly_sales_avg=14,
        image_url="biscuits.png",
        past_sales_weeks=[24, 21, 18, 16, 14, 12],
        forecast_sales_weeks=[11, 10, 8, 7],
        sell_through_verdict="DO_NOT_REORDER",
        verdict_badge="🛑 Do Not Reorder / Dead Stock Risk",
        days_inventory_remaining=98,
        sell_through_rate_pct=21.5,
        reorder_recommendation="DO NOT COMMIT FRESH CAPITAL: 195 units sitting on shelves with only 24 days shelf life. Sales volume dropped 50% over the last 6 weeks. ₹21,450 in working capital is trapped. Clear via bundle promotion.",
        brand_comparison_insight="Consumers are resisting the large ₹160 pack, opting for ₹10-₹30 single-serve pouches or Sunfeast Mom's Magic. Consider switching shelf space to Sunfeast Mom's Magic or Parle 20-20 which clear 2.8x faster.",
        alternative_brands=[
            "Sunfeast Mom's Magic Butter (300g) — 34% margin, 2.5x turnover",
            "Parle 20-20 Butter Cookies (Pack of 4) — 32% margin, lower ticket price",
            "Unibic Butter Cookies (250g) — 38% margin, premium positioning"
        ]
    ),
    Product(
        id="PROD_GHEE_01",
        name="Amul Pure Cow Ghee Tin (1 Litre)",
        category="Dairy & Oils",
        cost_price=530.0,
        selling_price=640.0,
        stock_quantity=85,
        days_in_stock=15,
        expiry_days=270,
        velocity_status="FAST_MOVING",
        weekly_sales_avg=38,
        image_url="ghee.png",
        past_sales_weeks=[30, 32, 35, 36, 38, 42],
        forecast_sales_weeks=[52, 65, 74, 82],
        sell_through_verdict="STRONG_INVEST_BUY",
        verdict_badge="🟢 Strong Buy / Festive Stockout Risk",
        days_inventory_remaining=14,
        sell_through_rate_pct=94.0,
        reorder_recommendation="Critical Festive Surge (+75%): Stockout imminent in 14 days before peak Diwali sweet-making week. Allocate ₹45,000 to reorder 5 cartons immediately.",
        brand_comparison_insight="Amul Cow Ghee has 82% consumer recall. Nandini Pure Ghee offers ₹18 cheaper distributor rate, but Amul guarantees zero unsold returns during festivals. Recommend holding 85% Amul and 15% Nandini.",
        alternative_brands=[
            "Nandini Pure Cow Ghee (1L) — 19% margin, ₹20 cheaper",
            "Mother Dairy Cow Ghee (1L) — 17.5% margin, stable demand",
            "Aashirvaad Svasti Ghee (1L) — 21% margin, higher brand push"
        ]
    ),
    Product(
        id="PROD_ALMOND_01",
        name="Nutraj California Premium Almonds (500g)",
        category="Dry Fruits",
        cost_price=330.0,
        selling_price=470.0,
        stock_quantity=110,
        days_in_stock=62,
        expiry_days=180,
        velocity_status="SLOW_MOVING",
        weekly_sales_avg=11,
        image_url="almonds.png",
        past_sales_weeks=[14, 13, 12, 11, 11, 10],
        forecast_sales_weeks=[12, 16, 22, 28],
        sell_through_verdict="CAUTION_CHECK_BRANDS",
        verdict_badge="🟡 Caution / Check Unbranded APMC",
        days_inventory_remaining=70,
        sell_through_rate_pct=30.0,
        reorder_recommendation="Hold off on Nutraj branded reorders: 110 units will cover the next 70 days. Let the Diwali surge clear existing packs in bundles before restocking.",
        brand_comparison_insight="Nutraj branded MRP of ₹470 meets consumer price resistance. Local APMC loose/pouch almonds sell for ₹390 with a 38% retailer margin vs Nutraj's 29.8%. Switching to local grade-A pouches yields higher net cash.",
        alternative_brands=[
            "APMC Mandi Loose Grade-A Almonds (500g pouch) — 38% margin, ₹390 price",
            "Happilo California Almonds (500g) — 31% margin, attractive tin pack",
            "Tata Sampann California Almonds (500g) — 27% margin, high trust"
        ]
    ),
    Product(
        id="PROD_OIL_01",
        name="Fortune Sunlite Refined Sunflower Oil (1 Litre)",
        category="Staples & Oils",
        cost_price=125.0,
        selling_price=148.0,
        stock_quantity=220,
        days_in_stock=8,
        expiry_days=300,
        velocity_status="FAST_MOVING",
        weekly_sales_avg=95,
        image_url="oil.png",
        past_sales_weeks=[88, 90, 92, 94, 95, 98],
        forecast_sales_weeks=[105, 115, 125, 130],
        sell_through_verdict="STRONG_INVEST_BUY",
        verdict_badge="🟢 Strong Buy / Core Fast Mover",
        days_inventory_remaining=16,
        sell_through_rate_pct=96.5,
        reorder_recommendation="High Velocity Anchor: Sells 95+ pouches weekly. Capital turns over every 16 days. Restock 15 cartons to capture festive bulk frying demand.",
        brand_comparison_insight="Fortune is the #1 household staple. However, Gemini and Sunpure are currently running a 'Buy 10 cartons get 1 free' trade scheme. Check with your local wholesaler to negotiate a matching rebate on Fortune.",
        alternative_brands=[
            "Gemini Refined Sunflower Oil (1L) — 18% margin, trade scheme active",
            "Sunpure Refined Sunflower Oil (1L) — 17.5% margin, popular in South India",
            "Dhara Refined Sunflower Oil (1L) — 15% margin, standard"
        ]
    ),
    Product(
        id="PROD_MASALA_01",
        name="Everest Shahi Garam Masala (100g)",
        category="Spices",
        cost_price=58.0,
        selling_price=88.0,
        stock_quantity=90,
        days_in_stock=55,
        expiry_days=90,
        velocity_status="SLOW_MOVING",
        weekly_sales_avg=12,
        image_url="masala.png",
        past_sales_weeks=[15, 14, 13, 12, 12, 11],
        forecast_sales_weeks=[12, 14, 15, 16],
        sell_through_verdict="CAUTION_CHECK_BRANDS",
        verdict_badge="🟡 Caution / Compare With MDH",
        days_inventory_remaining=52,
        sell_through_rate_pct=40.0,
        reorder_recommendation="Maintain stock level: 90 packs in inventory are sufficient for 7+ weeks. Avoid tying up working capital until inventory drops below 30 units.",
        brand_comparison_insight="In Indiranagar/Bengaluru kiranas, MDH Garam Masala records 1.6x higher repeat purchases than Everest. Everest offers 34% margin, but MDH generates higher cumulative rupee profits due to faster churn.",
        alternative_brands=[
            "MDH Garam Masala (100g) — 31% margin, 1.6x faster churn",
            "Catch Super Garam Masala (100g) — 33% margin, table-top sprinkler pack",
            "Eastern Garam Masala (100g) — 36% margin, budget alternative"
        ]
    ),
    Product(
        id="PROD_SWEET_01",
        name="Haldiram's Gulab Jamun Traditional Tin (1kg)",
        category="Sweets & Confectionery",
        cost_price=190.0,
        selling_price=260.0,
        stock_quantity=120,
        days_in_stock=10,
        expiry_days=120,
        velocity_status="FAST_MOVING",
        weekly_sales_avg=45,
        image_url="sweets.png",
        past_sales_weeks=[35, 38, 40, 42, 45, 52],
        forecast_sales_weeks=[65, 85, 98, 105],
        sell_through_verdict="STRONG_INVEST_BUY",
        verdict_badge="🟢 Strong Buy / Festive Peak (+110%)",
        days_inventory_remaining=18,
        sell_through_rate_pct=91.0,
        reorder_recommendation="Massive Gifting Surge (+110%): 120 units will sell out before Diwali weekend. Reorder 10 cases today to avoid losing customers to modern retail.",
        brand_comparison_insight="Haldiram's is the undisputed gifting gold standard. Bikaji offers 4% higher margins but lower gift appeal. Keep 80% Haldiram's on front display and 20% Bikaji for price-sensitive buyers.",
        alternative_brands=[
            "Bikaji Traditional Gulab Jamun (1kg) — 31% margin, ₹30 lower MRP",
            "Bikanervala Tin Sweets (1kg) — 28% margin, comparable brand",
            "Gits Instant Gulab Jamun Mix (500g) — 35% margin, DIY segment"
        ]
    )
]

# Basket Co-Purchase Affinity Matrix (Percentage of baskets where both co-occur)
AFFINITY_MATRIX: Dict[str, Dict[str, float]] = {
    "PROD_TEA_01": {
        "PROD_BISCUIT_01": 64.5,
        "PROD_ALMOND_01": 18.2,
        "PROD_MASALA_01": 12.0
    },
    "PROD_GHEE_01": {
        "PROD_ALMOND_01": 56.8,
        "PROD_SWEET_01": 48.0,
        "PROD_MASALA_01": 28.5
    },
    "PROD_OIL_01": {
        "PROD_MASALA_01": 46.2,
        "PROD_BISCUIT_01": 14.0
    },
    "PROD_SWEET_01": {
        "PROD_ALMOND_01": 51.5,
        "PROD_TEA_01": 29.0
    }
}

# Seasonal & Event-Driven Demand Forecasts
DEMAND_FORECASTS: List[DemandForecast] = [
    DemandForecast(
        product_id="PROD_GHEE_01",
        product_name="Amul Pure Cow Ghee Tin (1 Litre)",
        current_trend="RISING",
        projected_surge_pct=75.0,
        driver_event="Diwali Festive Season Prep & Homemade Sweets",
        confidence_score=0.92
    ),
    DemandForecast(
        product_id="PROD_SWEET_01",
        product_name="Haldiram's Gulab Jamun Traditional Tin (1kg)",
        current_trend="RISING",
        projected_surge_pct=110.0,
        driver_event="Upcoming Festive Gifting & Family Celebrations",
        confidence_score=0.95
    ),
    DemandForecast(
        product_id="PROD_TEA_01",
        product_name="Taj Mahal Premium Gold Tea (500g)",
        current_trend="RISING",
        projected_surge_pct=35.0,
        driver_event="Monsoon Weather & Extended Weekend Evenings",
        confidence_score=0.88
    ),
    DemandForecast(
        product_id="PROD_OIL_01",
        product_name="Fortune Sunlite Refined Sunflower Oil (1 Litre)",
        current_trend="RISING",
        projected_surge_pct=45.0,
        driver_event="Pre-festival bulk frying & cooking restocking",
        confidence_score=0.84
    )
]

# Multi-Brand Competitive Sales Curves for Product Profiles
CATEGORY_BRAND_COMPARISONS: Dict[str, Dict[str, Any]] = {
    "PROD_GHEE_01": {
        "product_id": "PROD_GHEE_01",
        "product_name": "Pure Cow Ghee (1 Litre)",
        "category": "Dairy & Oils",
        "recommendation": "Amul commands 65% market share in Indiranagar. Nandini provides 1.8% higher margin with steady local pull. Recommend holding 70% Amul & 30% Nandini during Diwali.",
        "brands": [
            {
                "brand_name": "Amul Pure Cow Ghee",
                "mrp": 640.0,
                "cost_price": 530.0,
                "margin_pct": 17.2,
                "weekly_sales_avg": 38,
                "past_sales": [30, 32, 35, 36, 38, 42],
                "forecast_sales": [52, 65, 74, 82],
                "turnover_rating": "HIGH",
                "market_share_pct": 65.0
            },
            {
                "brand_name": "Nandini Pure Cow Ghee",
                "mrp": 620.0,
                "cost_price": 502.0,
                "margin_pct": 19.0,
                "weekly_sales_avg": 28,
                "past_sales": [22, 24, 25, 26, 28, 30],
                "forecast_sales": [36, 44, 52, 58],
                "turnover_rating": "MODERATE",
                "market_share_pct": 25.0
            },
            {
                "brand_name": "Mother Dairy Cow Ghee",
                "mrp": 630.0,
                "cost_price": 520.0,
                "margin_pct": 17.5,
                "weekly_sales_avg": 16,
                "past_sales": [14, 15, 15, 16, 16, 17],
                "forecast_sales": [20, 24, 28, 32],
                "turnover_rating": "LOW",
                "market_share_pct": 10.0
            }
        ]
    },
    "PROD_TEA_01": {
        "product_id": "PROD_TEA_01",
        "product_name": "Premium Gold Tea (500g)",
        "category": "Beverages",
        "recommendation": "Taj Mahal has the fastest churn (52 units/wk). Tata Tea Gold offers 3.4% higher retailer margin. Stock Taj Mahal on prime shelf and bundle Red Label with snacks.",
        "brands": [
            {
                "brand_name": "Taj Mahal Premium Gold",
                "mrp": 310.0,
                "cost_price": 240.0,
                "margin_pct": 22.6,
                "weekly_sales_avg": 52,
                "past_sales": [42, 45, 48, 50, 52, 55],
                "forecast_sales": [58, 64, 72, 78],
                "turnover_rating": "HIGH",
                "market_share_pct": 55.0
            },
            {
                "brand_name": "Brooke Bond Red Label",
                "mrp": 290.0,
                "cost_price": 220.0,
                "margin_pct": 24.1,
                "weekly_sales_avg": 36,
                "past_sales": [32, 33, 34, 35, 36, 37],
                "forecast_sales": [40, 44, 48, 52],
                "turnover_rating": "MODERATE",
                "market_share_pct": 28.0
            },
            {
                "brand_name": "Tata Tea Gold",
                "mrp": 300.0,
                "cost_price": 222.0,
                "margin_pct": 26.0,
                "weekly_sales_avg": 30,
                "past_sales": [25, 27, 28, 29, 30, 32],
                "forecast_sales": [35, 38, 42, 46],
                "turnover_rating": "MODERATE",
                "market_share_pct": 17.0
            }
        ]
    },
    "PROD_BISCUIT_01": {
        "product_id": "PROD_BISCUIT_01",
        "product_name": "Butter Cookies & Snacks",
        "category": "Bakery & Snacks",
        "recommendation": "Britannia 6-packs have high price resistance (₹160). Sunfeast Mom's Magic and Parle 20-20 sell 2.5x to 3x faster with higher margins (34%). Switch shelf focus to Sunfeast.",
        "brands": [
            {
                "brand_name": "Sunfeast Mom's Magic",
                "mrp": 140.0,
                "cost_price": 92.0,
                "margin_pct": 34.3,
                "weekly_sales_avg": 38,
                "past_sales": [28, 30, 32, 33, 35, 38],
                "forecast_sales": [42, 46, 50, 55],
                "turnover_rating": "HIGH",
                "market_share_pct": 45.0
            },
            {
                "brand_name": "Parle 20-20 Cookies",
                "mrp": 120.0,
                "cost_price": 81.0,
                "margin_pct": 32.5,
                "weekly_sales_avg": 42,
                "past_sales": [36, 38, 40, 41, 42, 44],
                "forecast_sales": [46, 50, 52, 56],
                "turnover_rating": "HIGH",
                "market_share_pct": 33.0
            },
            {
                "brand_name": "Britannia Good Day (Pack 6)",
                "mrp": 160.0,
                "cost_price": 110.0,
                "margin_pct": 31.2,
                "weekly_sales_avg": 14,
                "past_sales": [24, 21, 18, 16, 14, 12],
                "forecast_sales": [11, 10, 8, 7],
                "turnover_rating": "LOW",
                "market_share_pct": 22.0
            }
        ]
    },
    "PROD_OIL_01": {
        "product_id": "PROD_OIL_01",
        "product_name": "Refined Sunflower Oil (1 Litre)",
        "category": "Staples & Oils",
        "recommendation": "Fortune is #1 in volume (95 units/wk). Sunpure offers 2.1% higher retailer margin in Karnataka with local brand affinity. Leverage Sunpure distributor scheme.",
        "brands": [
            {
                "brand_name": "Fortune Sunlite Refined",
                "mrp": 148.0,
                "cost_price": 125.0,
                "margin_pct": 15.5,
                "weekly_sales_avg": 95,
                "past_sales": [88, 90, 92, 94, 95, 98],
                "forecast_sales": [105, 115, 125, 130],
                "turnover_rating": "HIGH",
                "market_share_pct": 52.0
            },
            {
                "brand_name": "Sunpure Sunflower Oil",
                "mrp": 142.0,
                "cost_price": 117.0,
                "margin_pct": 17.6,
                "weekly_sales_avg": 62,
                "past_sales": [55, 57, 58, 60, 62, 65],
                "forecast_sales": [72, 80, 88, 94],
                "turnover_rating": "HIGH",
                "market_share_pct": 30.0
            },
            {
                "brand_name": "Gemini Refined Sunflower",
                "mrp": 145.0,
                "cost_price": 119.0,
                "margin_pct": 17.9,
                "weekly_sales_avg": 45,
                "past_sales": [40, 42, 43, 44, 45, 47],
                "forecast_sales": [52, 58, 64, 70],
                "turnover_rating": "MODERATE",
                "market_share_pct": 18.0
            }
        ]
    }
}

# Regional Festival Calendar with Specific Regional SKU Demands
REGIONAL_FESTIVAL_CALENDAR: List[Dict[str, Any]] = [
    {
        "id": "EVT_DIWALI_2026",
        "name": "Diwali / Deepavali (Deepa & Lakshmi Puja)",
        "region": "Karnataka & South India",
        "date_window": "Oct 24 - Oct 29, 2026",
        "status": "UPCOMING",
        "key_items": ["Clay Diyas & Deepas", "Pure Cow Ghee", "Gulab Jamun & Sweets", "California Almonds", "Puja Camphor & Wicks"],
        "demand_lift_pct": 85.0,
        "icon": "🪔",
        "description": "Peak festive season in Bengaluru. Deepas and Cow Ghee require 3x normal stock. Non-festive days require only minimal puja stock."
    },
    {
        "id": "EVT_AYUDHA_PUJA_2026",
        "name": "Ayudha Puja & Vijayadashami",
        "region": "Karnataka",
        "date_window": "Oct 10 - Oct 13, 2026",
        "status": "UPCOMING",
        "key_items": ["Puffed Rice (Pori)", "Jaggery (Bella)", "Sunflower Oil", "Ash Gourd", "Flowers & Lemon"],
        "demand_lift_pct": 60.0,
        "icon": "🌾",
        "description": "Massive corporate and vehicle puja demand. Bulk restocking of sweets and sunflower oil for frying."
    },
    {
        "id": "EVT_KARTHIKA_DEEPAM_2026",
        "name": "Karthika Deepotsava",
        "region": "Karnataka & Tamil Nadu",
        "date_window": "Nov 14 - Nov 20, 2026",
        "status": "UPCOMING",
        "key_items": ["Earthen Deepas (Clay Lamps)", "Sesame Gingelly Oil", "Cotton Wicks", "Cow Ghee"],
        "demand_lift_pct": 45.0,
        "icon": "🕯️",
        "description": "Month of lights across temples and households. Heavy surge in clay deepas and lighting oils."
    },
    {
        "id": "EVT_MONSOON_BONANZA_2026",
        "name": "Monsoon Refresh Bonanza",
        "region": "Karnataka Urban",
        "date_window": "Jul 15 - Aug 30, 2026",
        "status": "COMPLETED",
        "key_items": ["Premium Tea", "Biscuits", "Garam Masala", "Ginger", "Snacks"],
        "demand_lift_pct": 35.0,
        "icon": "🌧️",
        "description": "Cool monsoon evenings trigger evening chai & biscuit combo demand."
    }
]

# Currently Scheduled & Active Offers (For Conflict Prevention)
SCHEDULED_OFFERS: List[Dict[str, Any]] = [
    {
        "id": "OFFER_ACTIVE_01",
        "combo_id": "COMBO_389",
        "title": "Chai-Time Clearance Duo (Tea + Biscuits)",
        "anchor_id": "PROD_TEA_01",
        "attached_id": "PROD_BISCUIT_01",
        "start_date": "2026-10-10",
        "end_date": "2026-10-22",
        "discount_pct": 17.2,
        "combo_price": 389.0,
        "event_theme": "Super Weekend Kirana Rush",
        "status": "ACTIVE"
    },
    {
        "id": "OFFER_ACTIVE_02",
        "combo_id": "COMBO_1059",
        "title": "Diwali Pure Ghee & Almonds Festive Pack",
        "anchor_id": "PROD_GHEE_01",
        "attached_id": "PROD_ALMOND_01",
        "start_date": "2026-10-23",
        "end_date": "2026-10-30",
        "discount_pct": 18.0,
        "combo_price": 1059.0,
        "event_theme": "Diwali Maha Utsav",
        "status": "SCHEDULED"
    }
]

