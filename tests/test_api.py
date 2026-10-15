import os
import sys
import unittest
from fastapi.testclient import TestClient

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(TEST_DIR)
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from main import app

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
    res = client.get("/api/store/profile")
    assert res.status_code == 200
    profile = res.json()
    assert "store_name" in profile
    assert "customer_list" in profile

    payload = {
        "store_name": "Sharma Supermarket Koramangala",
        "owner_name": "Ramesh Sharma",
        "locality": "Koramangala 4th Block",
        "pin_code": "560048",
        "gstin": "29AAAAA9999A1Z9",
        "store_type": "Supermarket",
        "phone": "+91 98450 99999",
        "audience_size": 1850
    }
    update_res = client.post("/api/store/profile", json=payload)
    assert update_res.status_code == 200
    updated = update_res.json()
    assert updated["store_name"] == "Sharma Supermarket Koramangala"
    assert updated["audience_size"] == 1850


def test_api_login_region_festival_sync_and_store_management():
    # Login with store region & verify festivals are automatically discovered and persisted
    login_res = client.post("/api/auth/login", json={
        "store_id": "patel_fresh_mart_02",
        "owner_name": "Kiran Patel",
        "city": "Mumbai",
        "region": "Maharashtra & West India",
        "audience_size": 2400
    })
    assert login_res.status_code == 200
    login_data = login_res.json()
    assert login_data["authenticated"] is True
    assert login_data["store_id"] == "patel_fresh_mart_02"
    assert login_data["profile"]["city"] == "Mumbai"
    assert login_data["profile"]["whatsapp_audience_size"] == 2400
    assert isinstance(login_data.get("regional_festivals"), list)
    assert len(login_data["regional_festivals"]) >= 2

    # Switch back to default store
    client.post("/api/auth/login", json={
        "store_id": "sharma_supermarket_01",
        "city": "Bengaluru",
        "region": "Karnataka & South India"
    })


def test_api_smart_csv_structuring_and_deduplication_on_reupload():
    import uuid
    uid = uuid.uuid4().hex[:6]
    # Upload arbitrary POS CSV format (Item Name, Buy Rate, Retail Price, Closing Stock, Customer Phone)
    custom_csv = (
        "Item Name,Buy Rate,Retail Price,Closing Stock,Weekly Sales,Customer Name,Customer Phone\n"
        f"Coorg Filter Coffee Test {uid} (500g),210,290,75,32,Arjun Rao,+91 98450 77711\n"
        f"Mysore Sandal Soap Test {uid} (3x150g),140,195,90,40,Divya Hegde,+91 98450 77722\n"
    )
    res1 = client.post("/api/upload-csv", data={"raw_csv": custom_csv})
    assert res1.status_code == 200
    d1 = res1.json()
    assert d1["status"] == "SUCCESS"
    total_after_first = d1["total_skus"]
    assert d1["new_skus_added"] == 2

    # Re-upload the exact same CSV with updated stock -> must NOT duplicate SKUs!
    custom_csv_reupload = (
        "Item Name,Buy Rate,Retail Price,Closing Stock,Weekly Sales,Customer Name,Customer Phone\n"
        f"Coorg Filter Coffee Test {uid} (500g),210,295,120,36,Arjun Rao,+91 98450 77711\n"
        f"Mysore Sandal Soap Test {uid} (3x150g),140,195,110,42,Divya Hegde,+91 98450 77722\n"
    )
    res2 = client.post("/api/upload-csv", data={"raw_csv": custom_csv_reupload})
    assert res2.status_code == 200
    d2 = res2.json()
    assert d2["new_skus_added"] == 0
    assert d2["existing_skus_updated"] == 2
    assert d2["duplicates_prevented"] == 2
    assert d2["total_skus"] == total_after_first


def test_api_promotions_lifecycle_and_conflict_check():
    # Schedule a new offer
    publish_payload = {
        "combo_id": "COMBO_DIWALI_999",
        "title": "Diwali Ghee & Jamun Mega Saver",
        "anchor_id": "PROD_GHEE_01",
        "attached_id": "PROD_SWEET_01",
        "channels": ["WhatsApp Broadcast", "POS Barcode"],
        "price": 899.0,
        "discount_pct": 20.0,
        "event_theme": "Diwali Maha Utsav",
        "status": "SCHEDULED",
        "start_date": "2026-10-20",
        "end_date": "2026-10-30"
    }
    pub_res = client.post("/api/publish-offer", json=publish_payload)
    assert pub_res.status_code == 200
    pub_data = pub_res.json()
    assert pub_data["status"] == "SUCCESS"
    sched_id = pub_data["scheduled_id"]

    # Transition status from SCHEDULED to ACTIVE via PATCH /api/offers/{id}
    patch_res = client.patch(f"/api/offers/{sched_id}", json={"status": "ACTIVE"})
    assert patch_res.status_code == 200
    assert patch_res.json()["status"] == "ACTIVE"

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


class TestApiSuite(unittest.TestCase):
    def test_all_api_functions(self):
        test_api_health_endpoint()
        test_api_storage_status()
        test_api_store_profile_get_and_post()
        test_api_login_region_festival_sync_and_store_management()
        test_api_smart_csv_structuring_and_deduplication_on_reupload()
        test_api_promotions_lifecycle_and_conflict_check()
        test_api_inventory_and_instant_sync()


if __name__ == "__main__":
    unittest.main()
