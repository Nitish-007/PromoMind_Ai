from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class Product(BaseModel):
    id: str
    name: str
    category: str
    cost_price: float
    selling_price: float
    stock_quantity: int
    days_in_stock: int
    expiry_days: Optional[int] = None
    velocity_status: str  # "FAST_MOVING", "MODERATE", "SLOW_MOVING", "DEAD_STOCK"
    weekly_sales_avg: int
    image_url: Optional[str] = None
    # Historical Sales & Predictive Procurement Intelligence
    past_sales_weeks: Optional[List[int]] = None           # e.g., [42, 45, 48, 50, 52, 55] (past 6 weeks)
    forecast_sales_weeks: Optional[List[int]] = None       # e.g., [58, 64, 72, 78] (next 4 weeks)
    sell_through_verdict: Optional[str] = None             # "STRONG_INVEST_BUY", "DO_NOT_REORDER", "CAUTION_CHECK_BRANDS"
    verdict_badge: Optional[str] = None                    # "🟢 Strong Buy / Restock", "🛑 Do Not Reorder", "🟡 Check Alternate Brands"
    days_inventory_remaining: Optional[int] = None         # Estimated days until stockout
    sell_through_rate_pct: Optional[float] = None          # % of stock sold every 30 days
    reorder_recommendation: Optional[str] = None          # Actionable plain-English investment/reorder verdict
    brand_comparison_insight: Optional[str] = None        # Advice comparing this brand vs competitor brands
    alternative_brands: Optional[List[str]] = None         # Competing brands with margin/turnover notes

class ProductCreate(BaseModel):
    name: str
    category: str
    cost_price: float
    selling_price: float
    stock_quantity: int
    expiry_days: Optional[int] = 300
    weekly_sales_avg: Optional[int] = 20
    past_sales_weeks: Optional[List[int]] = None
    brand_comparison_insight: Optional[str] = None
    alternative_brands: Optional[List[str]] = None

class BrandSalesCurve(BaseModel):
    brand_name: str
    mrp: float
    cost_price: float
    margin_pct: float
    weekly_sales_avg: int
    past_sales: List[int]
    forecast_sales: List[int]
    turnover_rating: str  # "HIGH", "MODERATE", "LOW"
    market_share_pct: float

class BrandComparisonResponse(BaseModel):
    product_id: str
    product_name: str
    category: str
    brands: List[BrandSalesCurve]
    recommendation: str

class RegionalFestivalEvent(BaseModel):
    id: str
    name: str
    region: str          # e.g. "Karnataka / South India", "Pan-India", "Maharashtra"
    date_window: str     # e.g. "Oct 24 - Oct 29 (Peak Diwali)"
    status: str          # "UPCOMING", "ACTIVE", "PAST"
    key_items: List[str] # e.g. ["Diyas / Deepas", "Pure Cow Ghee", "Gulab Jamun", "Almonds"]
    demand_lift_pct: float
    icon: str
    description: str

class ScheduledOffer(BaseModel):
    id: str
    combo_id: str
    title: str
    anchor_id: str
    attached_id: str
    start_date: str
    end_date: str
    discount_pct: float
    combo_price: float
    event_theme: str
    status: str  # "ACTIVE", "SCHEDULED", "COMPLETED"

class ConflictCheckRequest(BaseModel):
    anchor_id: str
    attached_id: str
    start_date: Optional[str] = "2026-10-15"
    end_date: Optional[str] = "2026-10-30"

class ConflictCheckResponse(BaseModel):
    has_conflict: bool
    conflict_reason: Optional[str] = None
    conflicting_offers: List[ScheduledOffer] = []
    recommended_action: str

class DemandForecast(BaseModel):
    product_id: str
    product_name: str
    current_trend: str
    projected_surge_pct: float
    driver_event: str
    confidence_score: float

class ComboQuery(BaseModel):
    prompt: str
    min_margin_pct: Optional[float] = 18.0
    target_segment: Optional[str] = "General Customers"
    event_theme: Optional[str] = "Diwali Maha Utsav"
    offer_type: Optional[str] = "COMBO_DISCOUNT"

class CreativeAssets(BaseModel):
    poster_headline: str
    poster_subheading: str
    poster_badge: str
    poster_body: str
    whatsapp_message: str
    pos_tagline: str

class ROIMetrics(BaseModel):
    baseline_units_10d: int
    projected_units_10d: int
    units_lift_pct: float
    projected_revenue_inr: float
    revenue_lift_inr: float
    dead_stock_cleared_pct: float
    projected_gross_margin_pct: float
    projected_net_profit_inr: float

class ComboPlan(BaseModel):
    combo_id: str
    title: str
    tagline: str
    anchor_product: Product
    attached_product: Product
    affinity_score_pct: float
    demand_driver: str
    original_combined_mrp: float
    recommended_combo_price: float
    discount_amount: float
    discount_pct: float
    net_margin_pct: float
    target_customer_segment: str
    strategic_rationale: str
    creative_assets: CreativeAssets
    roi_prediction: ROIMetrics
    event_theme: Optional[str] = "Diwali Maha Utsav"
    offer_type: Optional[str] = "COMBO_DISCOUNT"
    co_purchase_probability: Optional[Dict[str, Any]] = None
    forecasting_summary: Optional[Dict[str, Any]] = None
