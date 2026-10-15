from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class CompatBaseModel(BaseModel):
    """Pydantic v1 / v2 cross-compatible BaseModel."""

    if not hasattr(BaseModel, "model_dump"):
        def model_dump(self, **kwargs) -> Dict[str, Any]:
            return self.dict(**kwargs)


class Product(CompatBaseModel):
    id: str
    name: str
    category: str
    cost_price: float
    selling_price: float
    stock_quantity: int
    days_in_stock: int = 5
    expiry_days: Optional[int] = None
    velocity_status: str  # "FAST_MOVING", "MODERATE", "SLOW_MOVING", "DEAD_STOCK"
    weekly_sales_avg: int
    image_url: Optional[str] = None
    past_sales_weeks: Optional[List[int]] = None
    forecast_sales_weeks: Optional[List[int]] = None
    sell_through_verdict: Optional[str] = None
    verdict_badge: Optional[str] = None
    days_inventory_remaining: Optional[int] = None
    sell_through_rate_pct: Optional[float] = None
    reorder_recommendation: Optional[str] = None
    brand_comparison_insight: Optional[str] = None
    alternative_brands: Optional[List[str]] = None


class ProductCreate(CompatBaseModel):
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


class BrandSalesCurve(CompatBaseModel):
    brand_name: str
    mrp: float
    cost_price: float
    margin_pct: float
    weekly_sales_avg: int
    past_sales: List[int]
    forecast_sales: List[int]
    turnover_rating: str  # "HIGH", "MODERATE", "LOW"
    market_share_pct: float


class BrandComparisonResponse(CompatBaseModel):
    product_id: str
    product_name: str
    category: str
    brands: List[BrandSalesCurve]
    recommendation: str
    generation_source: Optional[str] = "LIVE_GEMINI_API"


class CustomerInfo(CompatBaseModel):
    name: str
    phone: str
    segment: Optional[str] = "General"
    preferred_channel: Optional[str] = "WhatsApp"


class StoreProfile(CompatBaseModel):
    store_id: str = "sharma_supermarket_01"
    store_name: str = "Sharma Supermarket & Kirana"
    owner_name: str = "Ramesh Sharma"
    email: Optional[str] = "ramesh@sharmamart.in"
    phone: str = "+91 98450 12345"
    gstin: Optional[str] = "29AAAAA0000A1Z5"
    store_type: Optional[str] = "Supermarket"
    store_format: Optional[str] = "Supermarket"
    audience_size: Optional[int] = 1420
    whatsapp_audience_size: Optional[int] = 1420
    region: str = "Karnataka & South India"
    city: str = "Bengaluru"
    country: Optional[str] = "India"
    locality: Optional[str] = "Koramangala 4th Block"
    pin_code: Optional[str] = "560034"
    default_min_margin_pct: Optional[float] = 18.0
    total_working_capital_inr: Optional[float] = 500000.0
    customer_list: Optional[List[Dict[str, Any]]] = None
    updated_at: Optional[str] = None


class StoreProfileUpdate(CompatBaseModel):
    store_id: Optional[str] = None
    store_name: Optional[str] = None
    owner_name: Optional[str] = None
    email: Optional[str] = None
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
    country: Optional[str] = None
    locality: Optional[str] = None
    pin_code: Optional[str] = None
    customer_list: Optional[List[Dict[str, Any]]] = None


class RegionalFestivalEvent(CompatBaseModel):
    id: str
    name: str
    region: str
    date_window: str
    status: Optional[str] = "UPCOMING"
    demand_lift_pct: Optional[float] = 80.0
    key_items: List[str]
    icon: Optional[str] = ""
    description: Optional[str] = "Significant regional shopping demand spike for retail grocery."
    tradition_notes: Optional[str] = None
    advance_procurement_window: Optional[str] = None
    promo_launch_window: Optional[str] = None
    clearance_window: Optional[str] = None
    recommended_promo_type: Optional[str] = None
    matched_inventory_items: Optional[List[Dict[str, Any]]] = None
    suggested_combo_title: Optional[str] = None
    country: Optional[str] = "India"
    city: Optional[str] = None
    generation_source: Optional[str] = "LIVE_GEMINI_API"
    synced_at: Optional[str] = None


class FestivalDiscoveryRequest(CompatBaseModel):
    region: Optional[str] = None
    country: Optional[str] = "India"
    city: Optional[str] = None
    force_refresh: Optional[bool] = True


class ScheduledOffer(CompatBaseModel):
    id: str
    combo_id: Optional[str] = "COMBO_DEFAULT"
    title: str
    anchor_id: str
    attached_id: str
    anchor_name: Optional[str] = None
    attached_name: Optional[str] = None
    start_date: Optional[str] = "2026-10-15"
    end_date: Optional[str] = "2026-10-25"
    discount_pct: float
    combo_price: float
    original_mrp: Optional[float] = None
    net_margin_pct: Optional[float] = 18.5
    event_theme: Optional[str] = "Active Campaign"
    status: Optional[str] = "ACTIVE"  # "ACTIVE", "SCHEDULED", "PAUSED", "COMPLETED"
    channels: Optional[List[str]] = ["WhatsApp Broadcast", "POS Barcode", "In-Store Poster"]
    target_segment: Optional[str] = "Store Customer Broadcast"
    whatsapp_copy: Optional[str] = None
    cashier_pitch: Optional[str] = None
    broadcast_reach: Optional[int] = None
    type: Optional[str] = "promotion"
    updated_at: Optional[str] = None


class OfferStatusUpdate(CompatBaseModel):
    status: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    title: Optional[str] = None
    combo_price: Optional[float] = None
    discount_pct: Optional[float] = None


class LoginRequest(CompatBaseModel):
    store_id: Optional[str] = None
    owner_name: Optional[str] = None
    phone_or_email: Optional[str] = None
    password_or_pin: Optional[str] = None
    store_name: Optional[str] = None
    city: Optional[str] = None
    locality: Optional[str] = None
    region: Optional[str] = None
    country: Optional[str] = "India"
    audience_size: Optional[int] = None
    working_capital: Optional[float] = None
    min_margin_pct: Optional[float] = None
    gemini_api_key: Optional[str] = None


class LoginResponse(CompatBaseModel):
    status: str
    authenticated: bool
    store_id: str
    profile: StoreProfile
    available_stores: List[Dict[str, Any]]
    regional_festivals: Optional[List[RegionalFestivalEvent]] = None
    active_offers: Optional[List[ScheduledOffer]] = None
    gemini_configured: bool
    storage_mode: str


class ApiKeyConfigRequest(CompatBaseModel):
    gemini_api_key: str
    gemini_model: Optional[str] = "gemini-2.5-flash"


class ConflictCheckRequest(CompatBaseModel):
    anchor_id: str
    attached_id: str
    start_date: Optional[str] = "2026-10-15"
    end_date: Optional[str] = "2026-10-30"


class ConflictCheckResponse(CompatBaseModel):
    has_conflict: bool
    conflict_reason: Optional[str] = None
    conflicting_offers: List[ScheduledOffer] = []
    recommended_action: str


class DemandForecast(CompatBaseModel):
    product_id: str
    product_name: str
    current_trend: str
    projected_surge_pct: float
    driver_event: str
    confidence_score: float


class ComboQuery(CompatBaseModel):
    prompt: str
    min_margin_pct: Optional[float] = 18.0
    target_segment: Optional[str] = "General Customers"
    event_theme: Optional[str] = "Diwali Maha Utsav"
    offer_type: Optional[str] = "COMBO_DISCOUNT"
    region: Optional[str] = "Karnataka & South India"
    archetype: Optional[str] = "ANCHOR_MARGIN_BOOSTER"
    primary_product_id: Optional[str] = None
    secondary_product_id: Optional[str] = None


class CreativeAssets(CompatBaseModel):
    poster_headline: str
    poster_subheading: str
    poster_badge: str
    poster_body: str
    whatsapp_message: str
    pos_tagline: str
    cashier_counter_pitch: Optional[str] = None


class ROIMetrics(CompatBaseModel):
    baseline_units_10d: int
    projected_units_10d: int
    units_lift_pct: float
    projected_revenue_inr: float
    revenue_lift_inr: float
    dead_stock_cleared_pct: float
    projected_gross_margin_pct: float
    projected_net_profit_inr: float


class InvestmentROISimulation(CompatBaseModel):
    total_inventory_invested_inr: float
    projected_sales_revenue_inr: float
    projected_gross_profit_inr: float
    overall_roi_pct: float
    dead_capital_at_risk_inr: float
    unlocked_capital_from_promos_inr: float
    net_promo_profit_boost_inr: float
    capital_turnover_days: int
    recommendation_action: str


class ROIScenarioRequest(CompatBaseModel):
    proposed_discount_depth_pct: float = 16.0
    expected_volume_lift_pct: float = 35.0


class PromotionVariety(CompatBaseModel):
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


class ComboPlan(CompatBaseModel):
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
    generation_source: Optional[str] = "LIVE_GEMINI_API"


class ChatQuery(CompatBaseModel):
    message: str
    min_margin_pct: Optional[float] = None
    store_region: Optional[str] = None
    region: Optional[str] = None
    store_id: Optional[str] = None
    history: Optional[List[Dict[str, str]]] = []


class ChatResponse(CompatBaseModel):
    reply: str
    intent: str
    detected_margin_pct: float
    plan: Optional[ComboPlan] = None
    ideas: Optional[List[Dict[str, Any]]] = None
    roi_summary: Optional[Dict[str, Any]] = None
    sales_growth_plan: Optional[Dict[str, Any]] = None
    regional_festivals: Optional[List[RegionalFestivalEvent]] = None
    generation_source: Optional[str] = "LIVE_GEMINI_API"


class StorageStatusResponse(CompatBaseModel):
    mode: str
    firestore_connected: bool
    store_id: str
    collections: Dict[str, str]
    instant_sync_active: bool
    fallback_reason: Optional[str] = None
    last_sync_timestamp: Optional[str] = None
    local_cache_files: Dict[str, str]
    gemini_live_active: Optional[bool] = True
