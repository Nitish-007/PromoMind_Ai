import os
import sys
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from typing import List, Dict, Any, Optional

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

# Auto-load environment variables from .env if present
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
    FestivalDiscoveryRequest
)
from mock_data import (
    DEMAND_FORECASTS, CATEGORY_BRAND_COMPARISONS, 
    REGIONAL_FESTIVAL_CALENDAR, SCHEDULED_OFFERS
)
from agents import PromoMindEngine, RetailCopilotAgent, DynamicFestivalEngine
from storage import StoreDataManager
from forecasting import OpenSourceForecastingEngine, InvestmentROIEngine
from firestore_service import FirestoreService

app = FastAPI(
    title="PromoMind AI API",
    description="Intelligent Retail Promotion, Multi-Brand Forecasting & Regional Festival Calendar Engine",
    version="2.5.0"
)

# Enable CORS for local development and Cloud Run hosting
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize persistent knowledge base on boot
StoreDataManager.load_products()

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "PromoMind AI",
        "version": "2.5.0",
        "region": "asia-south1 (Google Cloud)",
        "model": "Gemini 1.5 Flash / Open-Source Holt-Winters Forecaster",
        "active_theme": "Google Material 3 Responsive Multi-Screen"
    }

@app.get("/api/system/cloud-status")
def get_cloud_storage_status():
    """Returns Google Cloud Firestore live synchronization status and credentials state."""
    return FirestoreService.get_status()

# ==============================================================================
# Store Profile, Regional Settings & Financial ROI Intelligence
# ==============================================================================

@app.get("/api/profile", response_model=StoreProfile)
def get_store_profile():
    """Retrieve retailer store profile, regional demographic settings, and working capital."""
    return StoreDataManager.load_profile()

@app.post("/api/profile", response_model=StoreProfile)
def update_store_profile(profile: StoreProfile):
    """Update store profile, cultural region, and immediately recompile store_knowledge.md."""
    return StoreDataManager.save_profile(profile)

@app.get("/api/store/financial-roi", response_model=InvestmentROISimulation)
def get_store_financial_roi():
    """
    Computes store-wide working capital invested, projected turnover revenue,
    net profit, dead capital trapped in slow movers, and cash unlocked via promotions.
    """
    products = StoreDataManager.load_products()
    profile = StoreDataManager.load_profile()
    roi = InvestmentROIEngine.compute_store_roi(products, store_capital_budget=profile.total_working_capital_inr)
    return InvestmentROISimulation(**roi)

@app.post("/api/store/simulate-roi")
def simulate_roi_scenario(payload: ROIScenarioRequest):
    """
    Simulates What-If scenario: Adjust discount depth and expected volume lift
    to predict resulting net profit Rupees and turnover days acceleration.
    """
    products = StoreDataManager.load_products()
    profile = StoreDataManager.load_profile()
    roi_base = InvestmentROIEngine.compute_store_roi(products, store_capital_budget=profile.total_working_capital_inr)
    
    sim = InvestmentROIEngine.simulate_scenario(
        base_invested=roi_base["total_inventory_invested_inr"],
        base_revenue=roi_base["projected_sales_revenue_inr"],
        proposed_discount_pct=payload.proposed_discount_depth_pct,
        expected_volume_lift_pct=payload.expected_volume_lift_pct
    )
    return sim

# ==============================================================================
# Regional Festival Calendar & Conflict Tracker
# ==============================================================================

@app.get("/api/calendar/events", response_model=List[RegionalFestivalEvent])
def get_festival_events(
    region: Optional[str] = None,
    country: Optional[str] = "India",
    city: Optional[str] = None,
    refresh: bool = False
):
    """Retrieve dynamic regional festival calendar with live AI discovery and matched store inventory."""
    profile = StoreDataManager.load_profile()
    active_region = region or profile.region or "Karnataka & South India"
    active_city = city or profile.city or "Bengaluru"
    active_country = country or "India"
    
    events = DynamicFestivalEngine.discover_festivals(
        region=active_region,
        country=active_country,
        city=active_city,
        force_refresh=refresh
    )
    return events

@app.post("/api/calendar/discover", response_model=List[RegionalFestivalEvent])
def discover_regional_festivals(payload: FestivalDiscoveryRequest):
    """Trigger AI search and discovery of regional festivals for any custom state, place, or country."""
    profile = StoreDataManager.load_profile()
    active_city = payload.city or profile.city or "Bengaluru"
    events = DynamicFestivalEngine.discover_festivals(
        region=payload.region,
        country=payload.country or "India",
        city=active_city,
        force_refresh=payload.force_refresh or False
    )
    return events

@app.get("/api/offers/active", response_model=List[ScheduledOffer])
def get_active_offers():
    """Retrieve currently active and scheduled offers across POS and WhatsApp channels."""
    return SCHEDULED_OFFERS

@app.post("/api/offers/check-conflict", response_model=ConflictCheckResponse)
def check_offer_conflict(payload: ConflictCheckRequest):
    """
    Detect overlapping promotional offers for the same anchor or attached products
    to prevent margin cannibalization and retailer discount fatigue.
    """
    conflicts = []
    for offer in SCHEDULED_OFFERS:
        if offer.get("status") in ["ACTIVE", "SCHEDULED"]:
            if payload.anchor_id in [offer["anchor_id"], offer["attached_id"]]:
                conflicts.append(offer)
            elif payload.attached_id in [offer["anchor_id"], offer["attached_id"]]:
                conflicts.append(offer)

    if conflicts:
        first = conflicts[0]
        return ConflictCheckResponse(
            has_conflict=True,
            conflict_reason=(
                f"Overlap detected with active offer '{first['title']}' (scheduled {first['start_date']} to {first['end_date']}). "
                f"Discounting the same SKU across two campaigns creates price confusion and eats profit margin."
            ),
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
# Inventory, Multi-Brand Curves & CSV Upload
# ==============================================================================

@app.get("/api/inventory", response_model=List[Product])
def get_inventory():
    """Retrieve retailer stock levels, velocities, and expiry windows from persistent store."""
    return StoreDataManager.load_products()

@app.get("/api/inventory/{product_id}/analytics", response_model=Product)
def get_product_analytics(product_id: str):
    """Retrieve SKU past sales curve, estimated demand, restock recommendation, and brand comparisons."""
    products = StoreDataManager.load_products()
    prod = next((p for p in products if p.id == product_id), None)
    if not prod:
        raise HTTPException(status_code=404, detail="Product not found")
    return prod

@app.get("/api/inventory/{product_id}/brand-comparison")
def get_brand_comparison(product_id: str):
    """
    Retrieve multi-brand sales curves for the same product category
    allowing the retailer to compare Amul vs Nandini vs Mother Dairy on the exact same graph.
    """
    comparison = CATEGORY_BRAND_COMPARISONS.get(product_id)
    if comparison:
        return comparison

    # Dynamic fallback comparison for custom products
    products = StoreDataManager.load_products()
    prod = next((p for p in products if p.id == product_id), None)
    if not prod:
        raise HTTPException(status_code=404, detail="Product not found")

    past = prod.past_sales_weeks or [20, 22, 24, 25, 26, 28]
    forecast = prod.forecast_sales_weeks or [30, 34, 38, 42]
    margin = round(((prod.selling_price - prod.cost_price) / max(1.0, prod.selling_price)) * 100, 1)

    return {
        "product_id": prod.id,
        "product_name": prod.name,
        "category": prod.category,
        "recommendation": f"Current store brand has {margin}% margin. Compare with wholesale alternative brands to optimize cash churn.",
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

@app.post("/api/products", response_model=List[Product])
def add_new_product(payload: ProductCreate):
    """
    Allow retailer to enter custom product/stock data.
    Automatically runs open-source demand forecasting and persists to inventory & AI knowledge base.
    """
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
            badge = "🟢 Strong Buy / Restock Now"
        elif days_rem >= 70 or velocity == "SLOW_MOVING":
            verdict = "DO_NOT_REORDER"
            badge = "🛑 Do Not Reorder / Capital Risk"
        else:
            verdict = "CAUTION_CHECK_BRANDS"
            badge = "🟡 Caution / Benchmark Brands"
            
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
    raw_csv: Optional[str] = Form(None)
):
    """
    Upload CSV file or paste raw CSV text.
    Parses inventory records, performs Holt's demand forecasting, and converts to store_knowledge.md.
    """
    content = ""
    if file:
        content_bytes = await file.read()
        content = content_bytes.decode("utf-8", errors="ignore")
    elif raw_csv:
        content = raw_csv
    else:
        raise HTTPException(status_code=400, detail="No CSV file or text provided")

    try:
        count, md = StoreDataManager.import_csv_data(content)
        return {
            "status": "SUCCESS",
            "imported_count": count,
            "message": f"Successfully parsed {count} SKUs and updated store_knowledge.md",
            "markdown_preview": md
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process CSV: {str(e)}")

@app.get("/api/knowledge-md")
def get_knowledge_markdown():
    """Retrieve the AI Store Knowledge Markdown catalog file generated for AI agents."""
    md_content = StoreDataManager.get_knowledge_markdown()
    return {
        "status": "SUCCESS",
        "file_name": "store_knowledge.md",
        "markdown": md_content
    }

@app.get("/api/forecasts", response_model=List[DemandForecast])
def get_demand_forecasts():
    """Retrieve forward-looking demand surge projections based on seasonal events."""
    return DEMAND_FORECASTS

# ==============================================================================
# Offer Generation & Channel Dispatch
# ==============================================================================

@app.get("/api/weekly-offer-ideas")
def get_weekly_offer_ideas(region: Optional[str] = None):
    """
    Returns autonomous weekly offer recommendations across multiple products in the store.
    No product selection is needed by the merchant.
    """
    try:
        ideas = PromoMindEngine.generate_weekly_recommendations(region=region)
        return {
            "status": "SUCCESS",
            "count": len(ideas),
            "ideas": ideas
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat", response_model=ChatResponse)
def copilot_chat(query: ChatQuery):
    """
    Conversational AI Copilot for Retailers.
    Processes natural language commands, extracts requested profit margin %,
    and runs backend econometric, pricing, and collateral tools silently.
    """
    try:
        response = RetailCopilotAgent.process_message(
            message=query.message,
            user_margin_pct=query.min_margin_pct,
            region=query.store_region
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate-combo", response_model=ComboPlan)
def generate_combo(query: ComboQuery):
    """
    Process retailer prompt, apply open-source time-series forecasting,
    evaluate co-purchase probability, optimize bundle pricing, and generate collateral.
    """
    try:
        plan = PromoMindEngine.generate_plan(
            query=query.prompt,
            min_margin_pct=query.min_margin_pct or 18.0,
            event_theme=query.event_theme or "Diwali Maha Utsav",
            offer_type=query.offer_type or "COMBO_DISCOUNT",
            primary_product_id=query.primary_product_id,
            secondary_product_id=query.secondary_product_id,
            region=query.region,
            archetype=query.archetype or "ANCHOR_MARGIN_BOOSTER"
        )
        return plan
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/publish-offer")
def publish_offer(payload: Dict[str, Any]):
    """Publish offer across retail channels and register in the Regional Scheduled Calendar."""
    combo_id = payload.get("combo_id", "COMBO_DEFAULT")
    title = payload.get("title", "Promotional Combo Offer")
    anchor_id = payload.get("anchor_id", "PROD_TEA_01")
    attached_id = payload.get("attached_id", "PROD_BISCUIT_01")
    channels = payload.get("channels", ["WhatsApp Broadcast", "POS Barcode", "In-Store Digital Display"])
    price = payload.get("price", 399.0)
    disc = payload.get("discount_pct", 17.5)
    theme = payload.get("event_theme", "Active Campaign")

    # Schedule into calendar
    new_offer = {
        "id": f"OFFER_LIVE_{len(SCHEDULED_OFFERS) + 1:02d}",
        "combo_id": combo_id,
        "title": title,
        "anchor_id": anchor_id,
        "attached_id": attached_id,
        "start_date": "2026-10-15",
        "end_date": "2026-10-25",
        "discount_pct": disc,
        "combo_price": price,
        "event_theme": theme,
        "status": "ACTIVE"
    }
    SCHEDULED_OFFERS.insert(0, new_offer)

    return {
        "status": "SUCCESS",
        "message": f"Combo {combo_id} successfully dispatched across retail channels.",
        "active_channels": channels,
        "scheduled_id": new_offer["id"],
        "live_at": "POS Terminal #1, #2, Sharma Store WhatsApp Broadcast List (1,420 customers)"
    }

# Mount frontend directory for single-container deployment on Cloud Run
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

    @app.get("/")
    def serve_ui():
        return FileResponse(os.path.join(frontend_dir, "index.html"))

    @app.get("/problem-statement")
    def serve_problem_statement():
        return FileResponse(os.path.join(frontend_dir, "problem_statement.html"))

    @app.get("/deck")
    @app.get("/presentation")
    def serve_pitch_deck():
        return FileResponse(os.path.join(frontend_dir, "presentation_deck.html"))

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
