import os
import sys
import json
import pytest
from unittest.mock import MagicMock, patch

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(TEST_DIR)
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from storage import DualModeStorageAdapter, StoreDataManager, DEFAULT_STORE_PROFILE
from models import Product, ProductCreate
from mock_data import INVENTORY_DATA, SCHEDULED_OFFERS, REGIONAL_FESTIVAL_CALENDAR


class TestDualModeStorageOffline:
    """Test Offline / Local Fallback Mode (Zero Downtime)."""

    def test_offline_mode_initialization(self, tmp_path):
        adapter = DualModeStorageAdapter(
            store_id="test_store_01",
            force_mode="LOCAL"
        )
        assert adapter.mode == "LOCAL_FALLBACK"
        status = adapter.get_status()
        assert status["mode"] == "LOCAL_FALLBACK"
        assert status["firestore_connected"] is False
        assert status["store_id"] == "test_store_01"
        assert status["collections"]["inventory"] == "stores/test_store_01/inventory"
        assert status["collections"]["promotions"] == "stores/test_store_01/promotions"
        assert status["collections"]["calendar_events"] == "stores/test_store_01/calendar_events"
        assert status["collections"]["store_profile"] == "stores/test_store_01/store_profile"
        assert status["collections"]["knowledge_catalog"] == "stores/test_store_01/knowledge_catalog"

    def test_offline_inventory_operations(self):
        adapter = DualModeStorageAdapter(store_id="test_store_offline", force_mode="LOCAL")
        products = adapter.load_products()
        assert len(products) > 0
        assert isinstance(products[0], Product)

        # Add new product
        new_prod = Product(
            id="PROD_TEST_99",
            name="Test Basmati Rice (5kg)",
            category="Staples",
            cost_price=350.0,
            selling_price=450.0,
            stock_quantity=40,
            days_in_stock=3,
            expiry_days=365,
            velocity_status="FAST_MOVING",
            weekly_sales_avg=25
        )
        updated = adapter.add_or_update_product(new_prod)
        found = next((p for p in updated if p.id == "PROD_TEST_99"), None)
        assert found is not None
        assert found.name == "Test Basmati Rice (5kg)"

        # Instant sync check: store_knowledge.md must contain the new product
        md = adapter.get_knowledge_markdown()
        assert "PROD_TEST_99" in md
        assert "Test Basmati Rice" in md

    def test_offline_promotions_and_conflict_logging(self):
        adapter = DualModeStorageAdapter(store_id="test_store_offline", force_mode="LOCAL")
        promos = adapter.get_promotions()
        assert len(promos) > 0

        # Save promotion
        offer = {
            "id": "OFFER_TEST_101",
            "title": "Chai & Rusk Saver",
            "anchor_id": "PROD_TEA_01",
            "attached_id": "PROD_BISCUIT_01",
            "combo_price": 299.0,
            "discount_pct": 15.0,
            "status": "ACTIVE"
        }
        saved = adapter.save_promotion(offer)
        assert saved["id"] == "OFFER_TEST_101"

        all_promos = adapter.get_promotions()
        assert any(p["id"] == "OFFER_TEST_101" for p in all_promos)

        # Log conflict
        conflict = adapter.log_conflict({
            "anchor_id": "PROD_TEA_01",
            "attached_id": "PROD_BISCUIT_01",
            "conflict_reason": "Overlap with active test offer"
        })
        assert conflict["type"] == "conflict_log"
        logs = adapter.get_conflict_logs()
        assert len(logs) > 0
        assert logs[0]["anchor_id"] == "PROD_TEA_01"

    def test_offline_calendar_and_store_profile(self):
        adapter = DualModeStorageAdapter(store_id="test_store_offline", force_mode="LOCAL")
        events = adapter.get_calendar_events()
        assert len(events) > 0

        filtered = adapter.get_calendar_events(region="Karnataka")
        assert len(filtered) > 0

        # Store Profile
        profile = adapter.get_store_profile()
        assert "store_name" in profile
        assert "customer_list" in profile
        assert len(profile["customer_list"]) > 0

        # Update profile
        profile["store_name"] = "Sharma Mega Supermarket"
        saved = adapter.save_store_profile(profile)
        assert saved["store_name"] == "Sharma Mega Supermarket"


class TestDualModeStorageCloudWithMockFirestore:
    """Test Cloud Mode with Google Cloud Firestore collections and Instant Sync."""

    @pytest.fixture
    def mock_firestore(self):
        """Create an in-memory mock Firestore client mimicking Firestore collection/document hierarchy."""
        store_db: Dict[str, Dict[str, Any]] = {}

        class MockDocumentSnapshot:
            def __init__(self, doc_id, data):
                self.id = doc_id
                self._data = data

            @property
            def exists(self):
                return self._data is not None

            def to_dict(self):
                return dict(self._data) if self._data else {}

        class MockDocumentReference:
            def __init__(self, path):
                self.path = path
                self._subcollections = {}

            def collection(self, name):
                sub_path = f"{self.path}/{name}"
                if sub_path not in self._subcollections:
                    self._subcollections[sub_path] = MockCollectionReference(sub_path)
                return self._subcollections[sub_path]

            def get(self):
                data = store_db.get(self.path)
                return MockDocumentSnapshot(self.path.split("/")[-1], data)

            def set(self, data):
                store_db[self.path] = dict(data)

            def update(self, data):
                if self.path not in store_db:
                    store_db[self.path] = {}
                store_db[self.path].update(data)

        class MockCollectionReference:
            def __init__(self, path):
                self.path = path

            def document(self, doc_id):
                doc_path = f"{self.path}/{doc_id}"
                return MockDocumentReference(doc_path)

            def stream(self):
                prefix = f"{self.path}/"
                docs = []
                for p, d in store_db.items():
                    if p.startswith(prefix) and "/" not in p[len(prefix):]:
                        doc_id = p[len(prefix):]
                        docs.append(MockDocumentSnapshot(doc_id, d))
                return docs

            def where(self, field, op, val):
                # Simple filtering mock
                prefix = f"{self.path}/"
                docs = []
                for p, d in store_db.items():
                    if p.startswith(prefix) and "/" not in p[len(prefix):]:
                        doc_id = p[len(prefix):]
                        if op == "==" and d.get(field) == val:
                            docs.append(MockDocumentSnapshot(doc_id, d))
                m = MagicMock()
                m.stream.return_value = docs
                return m

            def on_snapshot(self, callback):
                m = MagicMock()
                m.unsubscribe = MagicMock()
                return m

        class MockBatch:
            def __init__(self):
                self.ops = []

            def set(self, doc_ref, data):
                self.ops.append((doc_ref, data))

            def commit(self):
                for doc_ref, data in self.ops:
                    doc_ref.set(data)

        class MockClient:
            def collection(self, name):
                return MockCollectionReference(name)

            def batch(self):
                return MockBatch()

        client = MockClient()
        return client, store_db

    def test_cloud_mode_inventory_write_and_instant_sync(self, mock_firestore):
        client, store_db = mock_firestore
        adapter = DualModeStorageAdapter(
            store_id="sharma_kirana_cloud",
            firestore_client=client
        )
        assert adapter.mode == "CLOUD"
        assert adapter.client is not None

        # Verify initial save seeds stores/{store_id}/inventory
        products = adapter.load_products()
        assert len(products) > 0
        inv_key = "stores/sharma_kirana_cloud/inventory/PROD_TEA_01"
        assert inv_key in store_db
        assert store_db[inv_key]["name"] == "Taj Mahal Premium Gold Tea (500g)"

        # Verify Instant Sync: stores/{store_id}/knowledge_catalog
        catalog_key = "stores/sharma_kirana_cloud/knowledge_catalog/current"
        assert catalog_key in store_db
        assert "PROD_TEA_01" in store_db[catalog_key]["markdown"]
        assert store_db[catalog_key]["sku_count"] == len(products)

    def test_cloud_mode_promotions_and_calendar_events(self, mock_firestore):
        client, store_db = mock_firestore
        adapter = DualModeStorageAdapter(
            store_id="sharma_kirana_cloud",
            firestore_client=client
        )

        # Save promo to stores/{store_id}/promotions
        promo_data = {
            "id": "OFFER_CLOUD_01",
            "title": "Festive Mega Deal",
            "anchor_id": "PROD_GHEE_01",
            "attached_id": "PROD_SWEET_01",
            "combo_price": 799.0,
            "discount_pct": 20.0
        }
        adapter.save_promotion(promo_data)
        promo_key = "stores/sharma_kirana_cloud/promotions/OFFER_CLOUD_01"
        assert promo_key in store_db
        assert store_db[promo_key]["type"] == "promotion"

        # Save calendar event to stores/{store_id}/calendar_events
        evt_data = {
            "id": "EVT_UGADI_2026",
            "name": "Ugadi New Year",
            "region": "Karnataka",
            "date_window": "March 2026",
            "demand_lift_pct": 50.0,
            "key_items": ["Jaggery", "Neem", "Raw Mango"]
        }
        adapter.save_calendar_event(evt_data)
        evt_key = "stores/sharma_kirana_cloud/calendar_events/EVT_UGADI_2026"
        assert evt_key in store_db
        assert store_db[evt_key]["demand_lift_pct"] == 50.0

    def test_cloud_mode_store_profile(self, mock_firestore):
        client, store_db = mock_firestore
        adapter = DualModeStorageAdapter(
            store_id="sharma_kirana_cloud",
            firestore_client=client
        )

        profile = adapter.get_store_profile()
        profile_key = "stores/sharma_kirana_cloud/store_profile/profile"
        assert profile_key in store_db
        assert store_db[profile_key]["store_name"] == "Sharma Supermarket & Kirana"
        assert len(store_db[profile_key]["customer_list"]) > 0

    def test_cloud_mode_resilient_fallback_on_error(self, mock_firestore):
        client, _ = mock_firestore
        adapter = DualModeStorageAdapter(
            store_id="sharma_kirana_cloud",
            firestore_client=client
        )

        # Simulate Firestore stream error on inventory query
        with patch.object(adapter, "_inventory_coll", side_effect=Exception("Firestore network timeout")):
            products = adapter.load_products()
            # Must not crash; cleanly return cached/local fallback
            assert len(products) > 0


class TestStoreDataManagerFacade:
    """Verify StoreDataManager facade methods."""

    def test_facade_methods(self):
        adapter = DualModeStorageAdapter(store_id="sharma_facade_test", force_mode="LOCAL")
        StoreDataManager.set_adapter(adapter)

        # Load and save products
        products = StoreDataManager.load_products()
        assert len(products) > 0

        # Knowledge markdown
        md = StoreDataManager.get_knowledge_markdown()
        assert "# 🏪 PromoMind AI" in md

        # Status
        status = StoreDataManager.get_storage_status()
        assert status["mode"] == "LOCAL_FALLBACK"
        assert status["store_id"] == "sharma_facade_test"

        # Profile
        profile = StoreDataManager.get_store_profile()
        assert "store_name" in profile


class TestInlineServiceAccountCredentials:
    """Test inline Service Account JSON detection, decoding, and parsing."""

    def test_parse_inline_service_account_variations(self):
        sample_dict = {
            "type": "service_account",
            "project_id": "inline-project-999",
            "client_email": "test-sa@inline-project-999.iam.gserviceaccount.com",
            "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQC...\n-----END PRIVATE KEY-----\n"
        }
        json_str = json.dumps(sample_dict)

        # 1. Plain JSON string
        parsed1 = DualModeStorageAdapter.parse_inline_service_account(json_str)
        assert parsed1 is not None
        assert parsed1["project_id"] == "inline-project-999"

        # 2. Single-quoted JSON string (as stored in .env)
        parsed2 = DualModeStorageAdapter.parse_inline_service_account(f"'{json_str}'")
        assert parsed2 is not None
        assert parsed2["project_id"] == "inline-project-999"

        # 3. Base64 encoded JSON
        import base64
        b64_str = base64.b64encode(json_str.encode("utf-8")).decode("utf-8")
        parsed3 = DualModeStorageAdapter.parse_inline_service_account(b64_str)
        assert parsed3 is not None
        assert parsed3["client_email"] == "test-sa@inline-project-999.iam.gserviceaccount.com"

        # 4. Invalid input returns None
        assert DualModeStorageAdapter.parse_inline_service_account("") is None
        assert DualModeStorageAdapter.parse_inline_service_account(None) is None
        assert DualModeStorageAdapter.parse_inline_service_account("not a json") is None

    def test_inline_sa_env_var_detection(self, monkeypatch):
        fake_sa = {
            "type": "service_account",
            "project_id": "auto-detected-project-123",
            "client_email": "test@auto-detected-project-123.iam.gserviceaccount.com",
            "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvgIBAQ...\n-----END PRIVATE KEY-----\n"
        }
        monkeypatch.setenv("FIRESTORE_SA_JSON", json.dumps(fake_sa))

        with patch("storage.service_account.Credentials.from_service_account_info") as mock_sa_creds, \
             patch("storage.firestore.Client") as mock_fs_client:
            
            mock_creds_instance = MagicMock()
            mock_creds_instance.project_id = "auto-detected-project-123"
            mock_sa_creds.return_value = mock_creds_instance

            mock_client_instance = MagicMock()
            mock_fs_client.return_value = mock_client_instance

            adapter = DualModeStorageAdapter(store_id="test_inline_sa")
            assert adapter.project_id == "auto-detected-project-123"
            mock_sa_creds.assert_called_once()
            called_info = mock_sa_creds.call_args[0][0]
            assert called_info["client_email"] == "test@auto-detected-project-123.iam.gserviceaccount.com"


