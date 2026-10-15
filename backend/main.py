import os
import sys
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from typing import List, Dict, Any, Optional

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(CURRENT_DIR, ".env"))
    load_dotenv(os.path.join(PROJECT_ROOT, ".env"))
except Exception:
    pass

if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

dotenv_file = os.path.join(PROJECT_ROOT, ".env")
if os.path.exists(dotenv_file):
    try:
        with open(dotenv_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip('"').strip("'")
                    if k and k not in os.environ:
                        os.environ[k] = v
    except Exception:
        pass

from models import (
    Product, ProductCreate, DemandForecast, ComboQuery, ComboPlan,
    BrandComparisonResponse, RegionalFestivalEvent, ScheduledOffer,
    ConflictCheckRequest, ConflictCheckResponse, StoreProfile,
    InvestmentROISimulation, ROIScenarioRequest, ChatQuery, ChatResponse,
    FestivalDiscoveryRequest, StoreProfileUpdate, StorageStatusResponse,
    LoginRequest, LoginResponse, ApiKeyConfigRequest, OfferStatusUpdate
)
from mock_data import DEMAND_FORECASTS
from agents import PromoMindEngine, RetailCopilotAgent, DynamicFestivalEngine, GeminiLiveClient
from storage import StoreDataManager
from forecasting import OpenSourceForecastingEngine, InvestmentROIEngine

app = FastAPI(
    title="PromoMind AI API",
    description="Intelligent Retail Promotion, Multi-Brand Forecasting & Regional Festival Calendar Engine",
    version="3.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "*",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

StoreDataManager.load_products()


def _apply_request_context(x_gemini_api_key: Optional[str] = None, x_store_id: Optional[str] = None):
    if x_gemini_api_key and x_gemini_api_key.strip():
        GeminiLiveClient.set_runtime_api_key(x_gemini_api_key.strip())
    if x_store_id and x_store_id.strip():
        StoreDataManager.switch_store(x_store_id.strip())


@app.get("/api/health")
def health_check():
    status = StoreDataManager.get_storage_status()
    return {
        "status": "healthy",
        "service": "PromoMind AI",
        "version": "3.1.0",
        "region": "asia-south1 (Google Cloud)",
        "model": os.environ.get("GEMINI_MODEL", "gemini-2.5-flash"),
        "gemini_live_configured": GeminiLiveClient.is_configured(),
        "storage_mode": status["mode"],
        "firestore_connected": status["firestore_connected"],
        "store_id": status["store_id"],
        "active_theme": "Google Material 3 Responsive Multi-Screen"
    }


@app.get("/api/storage/status", response_model=StorageStatusResponse)
def get_storage_status():
    return StoreDataManager.get_storage_status()


@app.get("/api/system/cloud-status")
def get_cloud_storage_status():
    status = dict(StoreDataManager.get_storage_status())
    status["is_connected"] = status.get("firestore_connected", False)
    status["credentials_found"] = (
        status.get("firestore_connected", False)
        or bool(os.getenv("FIRESTORE_SA_JSON") or os.getenv("GCP_SERVICE_ACCOUNT_KEY") or os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))
    )
    status["gemini_configured"] = GeminiLiveClient.is_configured()
    return status


# ==============================================================================
# One-Time Login, Store Setup & Auto Regional Festival Persistence
# ==============================================================================

@app.post("/api/auth/login", response_model=LoginResponse)
def login_or_switch_store(payload: LoginRequest):
    """
    One-Time Retailer Login & Store Region Setup:
    1. Persists store profile & region in Firestore (`stores/{store_id}/store_profile`).
    2. Automatically discovers & persists regional festivals for the store's region in `stores/{store_id}/calendar_events`.
    3. Loads active and scheduled offers from `stores/{store_id}/promotions`.
    """
    if payload.gemini_api_key:
        GeminiLiveClient.set_runtime_api_key(payload.gemini_api_key)

    target_store_id = payload.store_id
    if not target_store_id and payload.store_name:
        target_store_id = payload.store_name.strip().lower().replace(" ", "_")
    if not target_store_id:
        target_store_id = StoreDataManager.get_adapter().store_id or "sharma_supermarket_01"

    prof_dict = StoreDataManager.switch_store(target_store_id)

    updates: Dict[str, Any] = {}
    if payload.store_name:
        updates["store_name"] = payload.store_name.strip()
    if payload.owner_name:
        updates["owner_name"] = payload.owner_name.strip()
    if payload.phone_or_email:
        if "@" in payload.phone_or_email:
            updates["email"] = payload.phone_or_email.strip()
        else:
            updates["phone"] = payload.phone_or_email.strip()
    if payload.city:
        updates["city"] = payload.city.strip()
    if payload.locality:
        updates["locality"] = payload.locality.strip()
    if payload.region:
        updates["region"] = payload.region.strip()
    if payload.country:
        updates["country"] = payload.country.strip()
    if payload.audience_size is not None:
        updates["audience_size"] = int(payload.audience_size)
        updates["whatsapp_audience_size"] = int(payload.audience_size)
    if payload.working_capital is not None:
        updates["total_working_capital_inr"] = float(payload.working_capital)
    if payload.min_margin_pct is not None:
        updates["default_min_margin_pct"] = float(payload.min_margin_pct)

    if updates:
        prof_dict.update(updates)
        prof_dict = StoreDataManager.save_store_profile(prof_dict)

    profile_model = StoreProfile(**prof_dict)

    # Discover and persist Regional Festivals (fast cache reuse so login completes instantly)
    festivals = DynamicFestivalEngine.discover_festivals(
        region=profile_model.region,
        country=profile_model.country or "India",
        city=profile_model.city,
        force_refresh=False,
        api_key=payload.gemini_api_key
    )

    offers_raw = StoreDataManager.get_promotions()
    active_offers = [ScheduledOffer(**o) for o in offers_raw]

    status = StoreDataManager.get_storage_status()
    return LoginResponse(
        status="SUCCESS",
        authenticated=True,
        store_id=target_store_id,
        profile=profile_model,
        available_stores=StoreDataManager.list_stores(),
        regional_festivals=festivals,
        active_offers=active_offers,
        gemini_configured=GeminiLiveClient.is_configured(),
        storage_mode=status["mode"]
    )


@app.get("/api/stores")
def list_available_stores():
    return {
        "status": "SUCCESS",
        "active_store_id": StoreDataManager.get_adapter().store_id,
        "stores": StoreDataManager.list_stores()
    }


@app.post("/api/stores")
def create_or_switch_store(payload: StoreProfileUpdate, x_gemini_api_key: Optional[str] = Header(None)):
    _apply_request_context(x_gemini_api_key=x_gemini_api_key)
    updates = payload.model_dump(exclude_unset=True)
    store_id = updates.get("store_id")
    if not store_id and updates.get("store_name"):
        store_id = updates["store_name"].strip().lower().replace(" ", "_")
    if not store_id:
        store_id = f"store_branch_{len(StoreDataManager.list_stores()) + 1:02d}"

    current = StoreDataManager.switch_store(store_id)
    current.update(updates)
    current["store_id"] = store_id
    saved = StoreDataManager.save_store_profile(current)

    # Sync regional festivals for the newly created/switched store
    festivals = DynamicFestivalEngine.discover_festivals(
        region=saved.get("region", "Karnataka & South India"),
        country=saved.get("country", "India"),
        city=saved.get("city", "Bengaluru"),
        force_refresh=True,
        api_key=x_gemini_api_key
    )

    return {
        "status": "SUCCESS",
        "active_store_id": store_id,
        "profile": saved,
        "regional_festivals": [f.model_dump() for f in festivals],
        "stores": StoreDataManager.list_stores()
    }


@app.post("/api/config/api-key")
def configure_gemini_api_key(payload: ApiKeyConfigRequest):
    GeminiLiveClient.set_runtime_api_key(payload.gemini_api_key, payload.gemini_model)
    return {
        "status": "SUCCESS",
        "gemini_configured": GeminiLiveClient.is_configured(),
        "active_model": os.environ.get("GEMINI_MODEL", "gemini-2.5-flash"),
        "message": "Live Gemini API key configured."
    }


# ==============================================================================
# Store Profile, Regional Settings & Financial ROI Intelligence
# ==============================================================================

@app.get("/api/profile", response_model=StoreProfile)
def get_profile_compat(x_store_id: Optional[str] = Header(None)):
    _apply_request_context(x_store_id=x_store_id)
    return StoreDataManager.load_profile()


@app.post("/api/profile", response_model=StoreProfile)
def update_profile_compat(
    profile: StoreProfile,
    x_gemini_api_key: Optional[str] = Header(None),
    x_store_id: Optional[str] = Header(None)
):
    _apply_request_context(x_gemini_api_key, x_store_id)
    saved = StoreDataManager.save_profile(profile)
    # Sync festivals for the updated store region
    DynamicFestivalEngine.discover_festivals(
        region=saved.region,
        country=saved.country or "India",
        city=saved.city,
        force_refresh=False,
        api_key=x_gemini_api_key
    )
    return saved


@app.get("/api/store/profile", response_model=Dict[str, Any])
def get_store_profile(x_store_id: Optional[str] = Header(None)):
    _apply_request_context(x_store_id=x_store_id)
    return StoreDataManager.get_store_profile()


@app.post("/api/store/profile", response_model=Dict[str, Any])
def update_store_profile(
    payload: StoreProfileUpdate,
    x_gemini_api_key: Optional[str] = Header(None),
    x_store_id: Optional[str] = Header(None)
):
    _apply_request_context(x_gemini_api_key, x_store_id)
    current = StoreDataManager.get_store_profile()
    old_region = current.get("region")
    updates = payload.model_dump(exclude_unset=True)
    current.update(updates)
    saved = StoreDataManager.save_store_profile(current)

    # If region changed, auto-sync regional festivals into Firestore
    if updates.get("region") and updates.get("region") != old_region:
        DynamicFestivalEngine.discover_festivals(
            region=saved.get("region", "Karnataka & South India"),
            country=saved.get("country", "India"),
            city=saved.get("city", "Bengaluru"),
            force_refresh=True,
            api_key=x_gemini_api_key
        )
    return saved


@app.get("/api/store/financial-roi", response_model=InvestmentROISimulation)
def get_store_financial_roi(x_store_id: Optional[str] = Header(None)):
    _apply_request_context(x_store_id=x_store_id)
    products = StoreDataManager.load_products()
    profile = StoreDataManager.load_profile()
    budget = profile.total_working_capital_inr if hasattr(profile, "total_working_capital_inr") and profile.total_working_capital_inr else 500000.0
    roi = InvestmentROIEngine.compute_store_roi(products, store_capital_budget=budget)
    return InvestmentROISimulation(**roi)


@app.post("/api/store/simulate-roi")
def simulate_roi_scenario(payload: ROIScenarioRequest, x_store_id: Optional[str] = Header(None)):
    _apply_request_context(x_store_id=x_store_id)
    products = StoreDataManager.load_products()
    profile = StoreDataManager.load_profile()
    budget = profile.total_working_capital_inr if hasattr(profile, "total_working_capital_inr") and profile.total_working_capital_inr else 500000.0
    roi_base = InvestmentROIEngine.compute_store_roi(products, store_capital_budget=budget)

    sim = InvestmentROIEngine.simulate_scenario(
        base_invested=roi_base["total_inventory_invested_inr"],
        base_revenue=roi_base["projected_sales_revenue_inr"],
        proposed_discount_pct=payload.proposed_discount_depth_pct,
        expected_volume_lift_pct=payload.expected_volume_lift_pct
    )
    return sim


# ==============================================================================
# Regional Festival Calendar & Sync Engine (Bound to Logged-In Store Region)
# ==============================================================================

@app.get("/api/calendar/events", response_model=List[RegionalFestivalEvent])
def get_festival_events(
    region: Optional[str] = None,
    country: Optional[str] = None,
    city: Optional[str] = None,
    refresh: bool = False,
    x_gemini_api_key: Optional[str] = Header(None),
    x_store_id: Optional[str] = Header(None)
):
    """
    Loads the store's regional festivals from Firestore (`stores/{store_id}/calendar_events`) based on the
    logged-in store's region, or refreshes from Live Gemini AI when `refresh=True`.
    """
    _apply_request_context(x_gemini_api_key, x_store_id)
    profile = StoreDataManager.load_profile()
    active_region = region or profile.region or "Karnataka & South India"
    active_city = city or profile.city or "Bengaluru"
    active_country = country or getattr(profile, "country", "India")

    events = DynamicFestivalEngine.discover_festivals(
        region=active_region,
        country=active_country,
        city=active_city,
        force_refresh=refresh,
        api_key=x_gemini_api_key
    )
    return events


@app.post("/api/calendar/discover", response_model=List[RegionalFestivalEvent])
def discover_regional_festivals(
    payload: FestivalDiscoveryRequest,
    x_gemini_api_key: Optional[str] = Header(None),
    x_store_id: Optional[str] = Header(None)
):
    """
    Sync / Update Regional Festivals for the logged-in store (or an optional custom region)
    via Live Gemini AI and persist into Firestore (`stores/{store_id}/calendar_events`).
    """
    _apply_request_context(x_gemini_api_key, x_store_id)
    profile = StoreDataManager.load_profile()
    active_region = payload.region or profile.region or "Karnataka & South India"
    active_city = payload.city or profile.city or "Bengaluru"
    active_country = payload.country or getattr(profile, "country", "India")

    events = DynamicFestivalEngine.discover_festivals(
        region=active_region,
        country=active_country,
        city=active_city,
        force_refresh=bool(payload.force_refresh),
        api_key=x_gemini_api_key
    )
    return events


# ==============================================================================
# Active & Scheduled Store Offers Lifecycle Manager (`stores/{store_id}/promotions`)
# ==============================================================================

@app.get("/api/offers/active", response_model=List[ScheduledOffer])
def get_active_offers(x_store_id: Optional[str] = Header(None)):
    """Retrieve all active, scheduled, paused, and completed offers stored in Firestore."""
    _apply_request_context(x_store_id=x_store_id)
    return StoreDataManager.get_promotions()


@app.patch("/api/offers/{offer_id}", response_model=ScheduledOffer)
def update_offer_lifecycle(
    offer_id: str,
    payload: OfferStatusUpdate,
    x_store_id: Optional[str] = Header(None)
):
    """Update offer status (ACTIVE, SCHEDULED, PAUSED, COMPLETED), dates, or price in Firestore."""
    _apply_request_context(x_store_id=x_store_id)
    updates = payload.model_dump(exclude_unset=True)
    updated = StoreDataManager.update_promotion(offer_id, updates)
    if not updated:
        raise HTTPException(status_code=404, detail=f"Offer {offer_id} not found")
    return ScheduledOffer(**updated)


@app.delete("/api/offers/{offer_id}")
def delete_store_offer(offer_id: str, x_store_id: Optional[str] = Header(None)):
    """Remove an offer from Firestore (`stores/{store_id}/promotions`)."""
    _apply_request_context(x_store_id=x_store_id)
    deleted = StoreDataManager.delete_promotion(offer_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Offer {offer_id} not found")
    return {
        "status": "SUCCESS",
        "deleted_id": offer_id,
        "offers": StoreDataManager.get_promotions()
    }


@app.post("/api/offers/check-conflict", response_model=ConflictCheckResponse)
def check_offer_conflict(payload: ConflictCheckRequest, x_store_id: Optional[str] = Header(None)):
    _apply_request_context(x_store_id=x_store_id)
    offers = StoreDataManager.get_promotions()
    conflicts = []
    for offer in offers:
        if offer.get("status") in ["ACTIVE", "SCHEDULED"]:
            if payload.anchor_id in [offer.get("anchor_id"), offer.get("attached_id")]:
                conflicts.append(offer)
            elif payload.attached_id in [offer.get("anchor_id"), offer.get("attached_id")]:
                conflicts.append(offer)

    if conflicts:
        first = conflicts[0]
        reason = (
            f"Overlap detected with active offer '{first.get('title')}' (scheduled {first.get('start_date')} to {first.get('end_date')}). "
            f"Discounting the same SKU across two campaigns creates price confusion and eats profit margin."
        )
        StoreDataManager.log_conflict({
            "anchor_id": payload.anchor_id,
            "attached_id": payload.attached_id,
            "conflict_reason": reason,
            "conflicting_offers": conflicts
        })
        return ConflictCheckResponse(
            has_conflict=True,
            conflict_reason=reason,
            conflicting_offers=conflicts,
            recommended_action="Stagger campaign start date until existing promotion finishes or select an alternative attached SKU."
        )

    return ConflictCheckResponse(
        has_conflict=False,
        conflict_reason=None,
        conflicting_offers=[],
        recommended_action="Clear to schedule. No conflicting promotions active for selected SKUs."
    )


# ==============================================================================
# Inventory, Multi-Brand Curves & Smart Deduplicating Firestore CSV Upload
# ==============================================================================

@app.get("/api/inventory", response_model=List[Product])
def get_inventory(x_store_id: Optional[str] = Header(None)):
    _apply_request_context(x_store_id=x_store_id)
    return StoreDataManager.load_products()


@app.get("/api/inventory/{product_id}/analytics", response_model=Product)
def get_product_analytics(product_id: str, x_store_id: Optional[str] = Header(None)):
    _apply_request_context(x_store_id=x_store_id)
    products = StoreDataManager.load_products()
    prod = next((p for p in products if p.id == product_id), None)
    if not prod:
        raise HTTPException(status_code=404, detail="Product not found")
    return prod


@app.get("/api/inventory/{product_id}/brand-comparison")
def get_brand_comparison(
    product_id: str,
    x_gemini_api_key: Optional[str] = Header(None),
    x_store_id: Optional[str] = Header(None)
):
    _apply_request_context(x_gemini_api_key, x_store_id)
    products = StoreDataManager.load_products()
    prod = next((p for p in products if p.id == product_id), None)
    if not prod:
        raise HTTPException(status_code=404, detail="Product not found")
    profile = StoreDataManager.load_profile()
    return PromoMindEngine.generate_brand_comparison(prod, region=profile.region, api_key=x_gemini_api_key)


@app.post("/api/products", response_model=List[Product])
def add_new_product(payload: ProductCreate, x_store_id: Optional[str] = Header(None)):
    _apply_request_context(x_store_id=x_store_id)
    try:
        products = StoreDataManager.load_products()
        sku_id = f"PROD_CUSTOM_{len(products) + 1:02d}"

        base_avg = payload.weekly_sales_avg or 20
        past_sales = payload.past_sales_weeks or [
            int(base_avg * 0.85), int(base_avg * 0.90),
            int(base_avg * 0.95), int(base_avg * 1.00),
            int(base_avg * 1.05), base_avg
        ]

        forecast_result = OpenSourceForecastingEngine.predict_demand_surge(
            past_sales=past_sales,
            event_surge_pct=30.0,
            forecast_weeks=4
        )

        velocity = "FAST_MOVING" if base_avg >= 35 else ("SLOW_MOVING" if base_avg <= 15 else "MODERATE")
        days_rem = int((payload.stock_quantity / max(1, base_avg)) * 7)

        if forecast_result["expected_growth_pct"] >= 25.0 or days_rem <= 18:
            verdict = "STRONG_INVEST_BUY"
            badge = "Strong Buy / Restock Now"
        elif days_rem >= 70 or velocity == "SLOW_MOVING":
            verdict = "DO_NOT_REORDER"
            badge = "Do Not Reorder / Capital Risk"
        else:
            verdict = "CAUTION_CHECK_BRANDS"
            badge = "Caution / Benchmark Brands"

        new_prod = Product(
            id=sku_id,
            name=payload.name,
            category=payload.category,
            cost_price=payload.cost_price,
            selling_price=payload.selling_price,
            stock_quantity=payload.stock_quantity,
            days_in_stock=5,
            expiry_days=payload.expiry_days or 300,
            velocity_status=velocity,
            weekly_sales_avg=base_avg,
            image_url="product_default.png",
            past_sales_weeks=past_sales,
            forecast_sales_weeks=forecast_result["forecast_sales"],
            sell_through_verdict=verdict,
            verdict_badge=badge,
            days_inventory_remaining=days_rem,
            sell_through_rate_pct=min(100.0, round((base_avg * 4 / max(1, payload.stock_quantity)) * 100, 1)),
            reorder_recommendation=forecast_result["forecast_recommendation"],
            brand_comparison_insight=payload.brand_comparison_insight or f"Custom retailer SKU with expected growth of {forecast_result['expected_growth_pct']:+}%.",
            alternative_brands=payload.alternative_brands or ["Local Wholesaler Grade-A", "National Market Alternative"]
        )

        updated_list = StoreDataManager.add_or_update_product(new_prod)
        return updated_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add product: {str(e)}")


@app.post("/api/upload-csv")
async def upload_csv_data(
    file: Optional[UploadFile] = File(None),
    raw_csv: Optional[str] = Form(None),
    replace_existing: bool = Form(False),
    x_store_id: Optional[str] = Header(None)
):
    """
    Smart Multi-Format CSV Structurizer & De-Duplicating Firestore Ingestion.
    Normalizes arbitrary CSV columns, prevents duplicates on re-upload (upserting existing SKUs),
    syncs customer broadcast reach if present, and persists to Firestore `stores/{store_id}/inventory`.
    """
    _apply_request_context(x_store_id=x_store_id)
    content = ""
    if file:
        content_bytes = await file.read()
        content = content_bytes.decode("utf-8", errors="ignore")
    elif raw_csv:
        content = raw_csv
    else:
        raise HTTPException(status_code=400, detail="No CSV file provided")

    try:
        stats = StoreDataManager.import_csv_data_with_stats(content, replace_existing=replace_existing)
        status = StoreDataManager.get_storage_status()
        products = StoreDataManager.load_products()
        prof = StoreDataManager.get_store_profile()
        return {
            "status": "SUCCESS",
            "imported_count": stats["imported_count"],
            "new_skus_added": stats["new_skus_added"],
            "existing_skus_updated": stats["existing_skus_updated"],
            "duplicates_prevented": stats["duplicates_prevented"],
            "broadcast_contacts_synced": stats["broadcast_contacts_synced"],
            "active_broadcast_reach": stats["active_broadcast_reach"],
            "columns_mapped": stats["columns_mapped"],
            "total_skus": len(products),
            "storage_mode": status["mode"],
            "firestore_collection": status["collections"]["inventory"],
            "message": (
                f"Structured & synced {stats['imported_count']} rows to Firestore ({status['collections']['inventory']}): "
                f"{stats['new_skus_added']} new SKUs added, {stats['existing_skus_updated']} existing SKUs updated "
                f"({stats['duplicates_prevented']} duplicates prevented)."
            ),
            "products": [p.model_dump() for p in products],
            "store_profile": prof,
            "markdown_preview": stats["markdown"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process CSV: {str(e)}")


@app.get("/api/knowledge-md")
def get_knowledge_markdown(x_store_id: Optional[str] = Header(None)):
    _apply_request_context(x_store_id=x_store_id)
    md_content = StoreDataManager.get_knowledge_markdown()
    return {
        "status": "SUCCESS",
        "file_name": "store_knowledge.md",
        "markdown": md_content
    }


@app.get("/api/forecasts", response_model=List[DemandForecast])
def get_demand_forecasts():
    return DEMAND_FORECASTS


# ==============================================================================
# Live Offer Generation, AI Retail Copilot & Channel Dispatch
# ==============================================================================

@app.get("/api/weekly-offer-ideas")
def get_weekly_offer_ideas(
    region: Optional[str] = None,
    x_gemini_api_key: Optional[str] = Header(None),
    x_store_id: Optional[str] = Header(None)
):
    _apply_request_context(x_gemini_api_key, x_store_id)
    try:
        ideas = PromoMindEngine.generate_weekly_recommendations(region=region, api_key=x_gemini_api_key)
        return {
            "status": "SUCCESS",
            "count": len(ideas),
            "ideas": ideas
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat", response_model=ChatResponse)
def copilot_chat(
    query: ChatQuery,
    x_gemini_api_key: Optional[str] = Header(None),
    x_store_id: Optional[str] = Header(None)
):
    _apply_request_context(x_gemini_api_key, query.store_id or x_store_id)
    try:
        response = RetailCopilotAgent.process_message(
            message=query.message,
            user_margin_pct=query.min_margin_pct,
            region=query.region or query.store_region,
            api_key=x_gemini_api_key
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/generate-combo", response_model=ComboPlan)
def generate_combo(
    query: ComboQuery,
    x_gemini_api_key: Optional[str] = Header(None),
    x_store_id: Optional[str] = Header(None)
):
    _apply_request_context(x_gemini_api_key, x_store_id)
    try:
        plan = PromoMindEngine.generate_plan(
            query=query.prompt,
            min_margin_pct=query.min_margin_pct or 18.0,
            event_theme=query.event_theme or "Diwali Maha Utsav",
            offer_type=query.offer_type or "COMBO_DISCOUNT",
            primary_product_id=query.primary_product_id,
            secondary_product_id=query.secondary_product_id,
            region=query.region,
            archetype=query.archetype or "ANCHOR_MARGIN_BOOSTER",
            api_key=x_gemini_api_key
        )
        return plan
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/publish-offer")
def publish_offer(payload: Dict[str, Any], x_store_id: Optional[str] = Header(None)):
    """
    Publish or schedule an offer across retail channels and persist in Firestore (`stores/{store_id}/promotions`).
    Supports both immediate activation (`ACTIVE`) and future scheduling (`SCHEDULED`).
    """
    _apply_request_context(x_store_id=x_store_id)
    prof = StoreDataManager.load_profile()
    products = StoreDataManager.load_products()

    combo_id = payload.get("combo_id", "COMBO_DEFAULT")
    title = payload.get("title", "Promotional Combo Offer")
    anchor_id = payload.get("anchor_id", "PROD_TEA_01")
    attached_id = payload.get("attached_id", "PROD_BISCUIT_01")

    anchor_prod = next((p for p in products if p.id == anchor_id), None)
    attached_prod = next((p for p in products if p.id == attached_id), None)

    channels = payload.get("channels", ["WhatsApp Broadcast", "POS Barcode", "In-Store Digital Display"])
    price = float(payload.get("price") or payload.get("combo_price") or 399.0)
    orig_mrp = float(payload.get("original_mrp") or ((anchor_prod.selling_price if anchor_prod else 250) + (attached_prod.selling_price if attached_prod else 200)))
    disc = float(payload.get("discount_pct", 17.5))
    margin = float(payload.get("net_margin_pct", 18.5))
    theme = payload.get("event_theme", "Active Campaign")
    status = payload.get("status", "ACTIVE")
    start_date = payload.get("start_date", "2026-10-15")
    end_date = payload.get("end_date", "2026-10-25")

    current_offers = StoreDataManager.get_promotions()
    new_offer = {
        "id": payload.get("id") or f"OFFER_LIVE_{len(current_offers) + 1:02d}_{int(price)}",
        "combo_id": combo_id,
        "title": title,
        "anchor_id": anchor_id,
        "attached_id": attached_id,
        "anchor_name": payload.get("anchor_name") or (anchor_prod.name if anchor_prod else anchor_id),
        "attached_name": payload.get("attached_name") or (attached_prod.name if attached_prod else attached_id),
        "start_date": start_date,
        "end_date": end_date,
        "discount_pct": disc,
        "combo_price": price,
        "original_mrp": orig_mrp,
        "net_margin_pct": margin,
        "event_theme": theme,
        "status": status,
        "channels": channels,
        "target_segment": payload.get("target_segment") or f"{prof.city} Shoppers",
        "whatsapp_copy": payload.get("whatsapp_copy"),
        "cashier_pitch": payload.get("cashier_pitch"),
        "broadcast_reach": prof.whatsapp_audience_size or prof.audience_size or 1420
    }
    saved = StoreDataManager.save_promotion(new_offer)

    return {
        "status": "SUCCESS",
        "message": f"Campaign '{title}' ({status}) saved to Firestore & dispatched across channels.",
        "active_channels": channels,
        "scheduled_id": saved["id"],
        "offer": saved,
        "live_at": f"POS Terminal #1, #2 & {prof.store_name} WhatsApp Broadcast ({prof.whatsapp_audience_size} customers in {prof.city})"
    }


frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
public_dir = os.path.join(frontend_dir, "public")


@app.get("/deck")
def serve_pitch_deck():
    deck_path = os.path.join(public_dir, "presentation_deck.html")
    if os.path.exists(deck_path):
        return FileResponse(deck_path)
    alt_path = os.path.join(frontend_dir, "presentation_deck.html")
    if os.path.exists(alt_path):
        return FileResponse(alt_path)
    raise HTTPException(status_code=404, detail="Pitch deck not found")


@app.get("/problem-statement")
def serve_problem_statement():
    wp_path = os.path.join(public_dir, "problem_statement.html")
    if os.path.exists(wp_path):
        return FileResponse(wp_path)
    alt_path = os.path.join(frontend_dir, "problem_statement.html")
    if os.path.exists(alt_path):
        return FileResponse(alt_path)
    raise HTTPException(status_code=404, detail="Problem statement whitepaper not found")


if os.path.exists(frontend_dir) and os.path.exists(os.path.join(frontend_dir, "index.html")):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

    @app.get("/")
    def serve_ui():
        return FileResponse(os.path.join(frontend_dir, "index.html"))
else:
    @app.get("/", response_class=HTMLResponse)
    def serve_backend_portal():
        return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>PromoMind AI v3.1 — Backend API Active</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #09090b; color: #fafafa; display: flex; align-items: center; justify-content: center; min-height: 100vh; margin: 0; padding: 24px; }
    .card { max-width: 620px; width: 100%; background: #18181b; border: 1px solid #27272a; border-radius: 16px; padding: 32px; box-shadow: 0 20px 40px rgba(0,0,0,0.4); }
    .badge { display: inline-block; background: #10b98120; color: #34d399; border: 1px solid #10b98140; font-size: 12px; font-weight: 700; padding: 4px 10px; border-radius: 999px; margin-bottom: 12px; }
    h1 { margin: 0 0 8px; font-size: 24px; }
    p { color: #a1a1aa; font-size: 14px; line-height: 1.6; margin: 0 0 20px; }
    .links { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 20px; }
    a.btn { display: block; text-decoration: none; padding: 12px 16px; border-radius: 10px; font-size: 13px; font-weight: 600; text-align: center; border: 1px solid #3f3f46; color: #fafafa; background: #27272a; transition: 0.15s; }
    a.btn:hover { background: #3f3f46; }
    a.btn.primary { background: #fafafa; color: #09090b; border-color: #fafafa; grid-column: span 2; font-size: 14px; }
    code { background: #09090b; padding: 2px 6px; border-radius: 4px; color: #e4e4e7; font-size: 12px; }
  </style>
</head>
<body>
  <div class="card">
    <span class="badge">● PromoMind AI Backend v3.1 Online (Port 8080)</span>
    <h1>PromoMind AI Engine is Running</h1>
    <p>The FastAPI backend server and Firestore / Gemini AI agents are active on port <code>8080</code>. To open the full Next.js Retailer OS interface, run <code>cd frontend &amp;&amp; npm run dev</code> and open port <code>3000</code>.</p>
    <div class="links">
      <a class="btn primary" href="http://localhost:3000">Open Next.js Retailer UI (http://localhost:3000) →</a>
      <a class="btn" href="/docs">Interactive Swagger API Docs (/docs)</a>
      <a class="btn" href="/api/health">System Health JSON (/api/health)</a>
      <a class="btn" href="/deck">Competition Pitch Deck (/deck)</a>
      <a class="btn" href="/problem-statement">Problem Whitepaper (/problem-statement)</a>
    </div>
  </div>
</body>
</html>"""


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
