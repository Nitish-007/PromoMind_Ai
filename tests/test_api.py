import os
import sys
import pytest
from fastapi.testclient import TestClient

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(TEST_DIR)
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from main import app
from storage import StoreDataManager, DualModeStorageAdapter

client = TestClient(app)


def test_api_health_endpoint():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert "storage_mode" in data
    assert "firestore_connected" in data
    assert "store_id" in data


def test_api_storage_status():
    res = client.get("/api/storage/status")
    assert res.status_code == 200
    data = res.json()
    assert "mode" in data
    assert "collections" in data
    assert "stores/" in data["collections"]["inventory"]
    assert "stores/" in data["collections"]["promotions"]
    assert "stores/" in data["collections"]["calendar_events"]
    assert "stores/" in data["collections"]["store_profile"]
    assert "stores/" in data["collections"]["knowledge_catalog"]
    assert data["instant_sync_active"] is True


def test_api_store_profile_get_and_post():
    # GET profile
    res = client.get("/api/store/profile")
    assert res.status_code == 200
    profile = res.json()
    assert "store_name" in profile
    assert "customer_list" in profile

    # Update profile
    payload = {
        "store_name": "Sharma Supermarket Koramangala",
        "owner_name": "Ramesh Sharma",
        "audience_size": 1850
    }
    update_res = client.post("/api/store/profile", json=payload)
    assert update_res.status_code == 200
    updated = update_res.json()
    assert updated["store_name"] == "Sharma Supermarket Koramangala"
    assert updated["audience_size"] == 1850


def test_api_calendar_events():
    res = client.get("/api/calendar/events")
    assert res.status_code == 200
    events = res.json()
    assert len(events) > 0
    assert any("Diwali" in ev["name"] for ev in events)


def test_api_promotions_and_conflict_check():
    # Get active offers
    res = client.get("/api/offers/active")
    assert res.status_code == 200
    offers = res.json()
    assert len(offers) > 0

    # Publish new offer
    publish_payload = {
        "combo_id": "COMBO_DIWALI_999",
        "title": "Diwali Ghee & Jamun Mega Saver",
        "anchor_id": "PROD_GHEE_01",
        "attached_id": "PROD_SWEET_01",
        "channels": ["WhatsApp Broadcast", "POS Barcode"],
        "price": 899.0,
        "discount_pct": 20.0,
        "event_theme": "Diwali Maha Utsav"
    }
    pub_res = client.post("/api/publish-offer", json=publish_payload)
    assert pub_res.status_code == 200
    pub_data = pub_res.json()
    assert pub_data["status"] == "SUCCESS"

    # Check conflict detection
    conflict_payload = {
        "anchor_id": "PROD_GHEE_01",
        "attached_id": "PROD_SWEET_01"
    }
    conf_res = client.post("/api/offers/check-conflict", json=conflict_payload)
    assert conf_res.status_code == 200
    conf_data = conf_res.json()
    assert conf_data["has_conflict"] is True
    assert "Overlap detected" in conf_data["conflict_reason"]


def test_api_inventory_and_instant_sync():
    res = client.get("/api/inventory")
    assert res.status_code == 200
    products = res.json()
    assert len(products) > 0

    # Add new product
    sku_payload = {
        "name": "Tata Salt Vacuum Evaporated (1kg)",
        "category": "Staples",
        "cost_price": 20.0,
        "selling_price": 28.0,
        "stock_quantity": 200,
        "weekly_sales_avg": 50
    }
    post_res = client.post("/api/products", json=sku_payload)
    assert post_res.status_code == 200
    updated_products = post_res.json()
    assert any("Tata Salt" in p["name"] for p in updated_products)

    # Verify Instant Sync: store_knowledge.md must contain the new SKU
    md_res = client.get("/api/knowledge-md")
    assert md_res.status_code == 200
    md_content = md_res.json()["markdown"]
    assert "Tata Salt" in md_content

