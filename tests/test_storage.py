import os
import sys
import json
import unittest
from typing import Dict, Any
from unittest.mock import MagicMock, patch

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(TEST_DIR)
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from storage import DualModeStorageAdapter, StoreDataManager, DEFAULT_STORE_PROFILE
from models import Product, ProductCreate
from mock_data import INVENTORY_DATA, SCHEDULED_OFFERS, REGIONAL_FESTIVAL_CALENDAR


def build_mock_firestore():
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

    return MockClient(), store_db


class TestStorageUnittest(unittest.TestCase):
    def test_01_offline_mode_and_inventory(self):
        adapter = DualModeStorageAdapter(store_id="test_store_01", force_mode="LOCAL")
        self.assertEqual(adapter.mode, "LOCAL_FALLBACK")
        status = adapter.get_status()
        self.assertEqual(status["store_id"], "test_store_01")

        products = adapter.load_products()
        self.assertGreater(len(products), 0)

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
        self.assertIsNotNone(found)
        self.assertEqual(found.name, "Test Basmati Rice (5kg)")

    def test_02_cloud_mode_with_mock_firestore(self):
        client, store_db = build_mock_firestore()
        adapter = DualModeStorageAdapter(
            store_id="sharma_kirana_cloud",
            firestore_client=client
        )
        self.assertEqual(adapter.mode, "CLOUD")
        products = adapter.load_products()
        self.assertGreater(len(products), 0)
        inv_key = "stores/sharma_kirana_cloud/inventory/PROD_TEA_01"
        self.assertIn(inv_key, store_db)

        # Test single-stage CSV import to Firestore
        csv_text = "product_id,name,category,cost_price,selling_price,stock_quantity,weekly_sales_avg\nSKU_FS_01,Firestore Test Almond (500g),Dry Fruits,300,420,55,28"
        imported_count, _ = adapter.import_csv_data(csv_text)
        self.assertEqual(imported_count, 1)
        self.assertIn("stores/sharma_kirana_cloud/inventory/SKU_FS_01", store_db)

    def test_03_inline_service_account_parser(self):
        sample_dict = {
            "type": "service_account",
            "project_id": "inline-project-999",
            "client_email": "test-sa@inline-project-999.iam.gserviceaccount.com",
            "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQC...\n-----END PRIVATE KEY-----\n"
        }
        json_str = json.dumps(sample_dict)
        parsed = DualModeStorageAdapter.parse_inline_service_account(f"'{json_str}'")
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed["project_id"], "inline-project-999")


if __name__ == "__main__":
    unittest.main()
