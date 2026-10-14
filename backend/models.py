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

class StoreProfile(BaseModel):
    store_name: str = "Sharma Supermarket & Kirana"
    owner_name: str = "Ramesh Sharma"
    region: str = "Karnataka & South India"
    city: str = "Bengaluru"
    locality: str = "Koramangala 4th Block"
    pin_code: str = "560034"
    phone: str = "+91 98450 12345"
    store_format: str = "Supermarket" # Supermarket, Kirana, Mart, Organic
    whatsapp_audience_size: int = 1420
    default_min_margin_pct: float = 18.0
    total_working_capital_inr: float = 350000.0

class RegionalFestivalEvent(BaseModel):
    id: str
    name: str
    region: str          # e.g. "Karnataka & South India", "Maharashtra & West India", etc.
    date_window: str     # e.g. "Oct 24 - Oct 29 (Peak Diwali)"
    status: Optional[str] = "UPCOMING"  # "UPCOMING", "ACTIVE", "PAST"
    demand_lift_pct: Optional[float] = 80.0
    key_items: List[str] # e.g. ["Diyas / Deepas", "Pure Cow Ghee", "Gulab Jamun", "Almonds"]
    icon: Optional[str] = "🪔"
    description: Optional[str] = "Significant regional shopping demand spike for retail grocery."
    tradition_notes: Optional[str] = None               # Cultural and traditional rationale
    advance_procurement_window: Optional[str] = None    # When retailer should buy from distributor (T-14d)
    promo_launch_window: Optional[str] = None           # When to run early-bird offers (T-7d)
    clearance_window: Optional[str] = None              # Post-festival clearance window (T+2d)
    recommended_promo_type: Optional[str] = None        # e.g. "Festive Gifting Hamper", "Advance Booking Combo"
    matched_inventory_items: Optional[List[Dict[str, Any]]] = None # Matched products from current store inventory
    suggested_combo_title: Optional[str] = None        # e.g. "Mysuru Dasara Ghee & Sweets Pack"
    country: Optional[str] = "India"
    city: Optional[str] = None

class FestivalDiscoveryRequest(BaseModel):
    region: str
    country: Optional[str] = "India"
    city: Optional[str] = None
    force_refresh: Optional[bool] = False

class ScheduledOffer(BaseModel):
    id: str
    combo_id: Optional[str] = "COMBO_DEFAULT"
    title: str
    anchor_id: str
    attached_id: str
    start_date: Optional[str] = "2026-10-15"
    end_date: Optional[str] = "2026-10-25"
    discount_pct: float
    combo_price: float
    event_theme: Optional[str] = "Active Campaign"
    status: Optional[str] = "ACTIVE"  # "ACTIVE", "SCHEDULED", "COMPLETED"
    type: Optional[str] = "promotion"
    updated_at: Optional[str] = None

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
    region: Optional[str] = "Karnataka & South India"
    archetype: Optional[str] = "ANCHOR_MARGIN_BOOSTER"
    primary_product_id: Optional[str] = None
    secondary_product_id: Optional[str] = None

class CreativeAssets(BaseModel):
    poster_headline: str
    poster_subheading: str
    poster_badge: str
    poster_body: str
    whatsapp_message: str
    pos_tagline: str
    cashier_counter_pitch: Optional[str] = None

class ROIMetrics(BaseModel):
    baseline_units_10d: int
    projected_units_10d: int
    units_lift_pct: float
    projected_revenue_inr: float
    revenue_lift_inr: float
    dead_stock_cleared_pct: float
    projected_gross_margin_pct: float
    projected_net_profit_inr: float

class InvestmentROISimulation(BaseModel):
    total_inventory_invested_inr: float
    projected_sales_revenue_inr: float
    projected_gross_profit_inr: float
    overall_roi_pct: float
    dead_capital_at_risk_inr: float
    unlocked_capital_from_promos_inr: float
    net_promo_profit_boost_inr: float
    capital_turnover_days: int
    recommendation_action: str

class ROIScenarioRequest(BaseModel):
    proposed_discount_depth_pct: float = 16.0
    expected_volume_lift_pct: float = 35.0

class PromotionVariety(BaseModel):
    id: str
    variety_type: str
    title: str
    tagline: str
    badge: str
    badge_class: str
    icon: str
    combo_price: float
    original_mrp: float
    discount_amount: float
    discount_pct: float
    net_margin_pct: float
    projected_volume_lift_pct: float
    capital_turnover_days: int
    customer_target: str
    cashier_counter_pitch: str
    whatsapp_copy: str
    poster_headline: str
    poster_savings: str
    is_recommended: bool = False

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
    combo_price: Optional[float] = None
    original_total_mrp: Optional[float] = None
    discount_amount: float
    discount_pct: float
    net_margin_pct: float
    target_customer_segment: str
    strategic_rationale: str
    creative_assets: CreativeAssets
    roi_prediction: ROIMetrics
    event_theme: Optional[str] = "Diwali Maha Utsav"
    offer_type: Optional[str] = "COMBO_DISCOUNT"
    archetype: Optional[str] = "ANCHOR_MARGIN_BOOSTER"
    region: Optional[str] = "Karnataka & South India"
    co_purchase_probability: Optional[Dict[str, Any]] = None
    forecasting_summary: Optional[Dict[str, Any]] = None
    varieties: Optional[List[PromotionVariety]] = None
    hybrid_architecture: Optional[Dict[str, Any]] = None

class ChatQuery(BaseModel):
    message: str
    min_margin_pct: Optional[float] = None
    store_region: Optional[str] = None
    history: Optional[List[Dict[str, str]]] = []

class ChatResponse(BaseModel):
    reply: str
    intent: str  # "PROMOTION_GENERATED", "WEEKLY_IDEAS", "ROI_INSIGHT", "GENERAL_ASSISTANCE"
    detected_margin_pct: float
    plan: Optional[ComboPlan] = None
    ideas: Optional[List[Dict[str, Any]]] = None
    roi_summary: Optional[Dict[str, Any]] = None

class CustomerInfo(BaseModel):
    name: str
    phone: str
    segment: Optional[str] = "General"
    preferred_channel: Optional[str] = "WhatsApp"

class StoreProfile(BaseModel):
    store_id: str = "store_bengaluru_01"
    store_name: str = "Metro Supermarket & Retail Mart"
    owner_name: str = "Ramesh Sharma"
    phone: str = "+91 98450 12345"
    gstin: Optional[str] = "29AAAAA0000A1Z5"
    store_type: Optional[str] = "Supermarket"
    store_format: Optional[str] = "Supermarket"
    audience_size: Optional[int] = 1420
    whatsapp_audience_size: Optional[int] = 1420
    region: str = "Karnataka & South India"
    city: str = "Bengaluru"
    locality: Optional[str] = "Koramangala 4th Block"
    pin_code: Optional[str] = "560034"
    default_min_margin_pct: Optional[float] = 16.5
    total_working_capital_inr: Optional[float] = 500000.0
    customer_list: Optional[List[Dict[str, Any]]] = None
    updated_at: Optional[str] = None

class StoreProfileUpdate(BaseModel):
    store_name: Optional[str] = None
    owner_name: Optional[str] = None
    phone: Optional[str] = None
    gstin: Optional[str] = None
    store_type: Optional[str] = None
    store_format: Optional[str] = None
    audience_size: Optional[int] = None
    whatsapp_audience_size: Optional[int] = None
    default_min_margin_pct: Optional[float] = None
    total_working_capital_inr: Optional[float] = None
    region: Optional[str] = None
    city: Optional[str] = None
    locality: Optional[str] = None
    pin_code: Optional[str] = None
    customer_list: Optional[List[Dict[str, Any]]] = None

class StorageStatusResponse(BaseModel):
    mode: str
    firestore_connected: bool
    store_id: str
    collections: Dict[str, str]
    instant_sync_active: bool
    fallback_reason: Optional[str] = None
    last_sync_timestamp: Optional[str] = None
    local_cache_files: Dict[str, str]

