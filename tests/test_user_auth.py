import os
import sys
import unittest
import time

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from fastapi.testclient import TestClient
from main import app
from storage import StoreDataManager

class TestUserAuthAndStoreCreation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.unique_suffix = int(time.time())

    def test_01_signin_default_admin(self):
        """Test default admin demo account sign in"""
        res = self.client.post("/api/auth/signin", json={
            "email": "admin@promomind.ai",
            "password": "password123"
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "SUCCESS")
        self.assertTrue(data["authenticated"])
        self.assertIn("user", data)
        self.assertEqual(data["user"]["email"], "admin@promomind.ai")
        self.assertTrue(len(data["available_stores"]) >= 1)

    def test_02_signup_new_user(self):
        """Test brand new user signup with zero store clutter"""
        test_email = f"retailer_{self.unique_suffix}@storemail.com"
        res = self.client.post("/api/auth/signup", json={
            "email": test_email,
            "password": "SecurePassword123",
            "full_name": "Vikram Sethi",
            "phone": "+91 98765 43210"
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "SUCCESS")
        self.assertTrue(data["authenticated"])
        self.assertEqual(data["user"]["email"], test_email)
        self.assertEqual(data["user"]["full_name"], "Vikram Sethi")
        self.assertTrue(len(data["user"]["store_ids"]) >= 1)
        active_store = data["active_store_id"]
        self.assertIsNotNone(active_store)

    def test_03_signin_newly_registered_user(self):
        """Test signing in with the user created in test_02"""
        test_email = f"retailer_{self.unique_suffix}@storemail.com"
        res = self.client.post("/api/auth/signin", json={
            "email": test_email,
            "password": "SecurePassword123"
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "SUCCESS")
        self.assertEqual(data["user"]["email"], test_email)

    def test_04_create_store_under_user(self):
        """Test creating a second store branch under the user via profile management"""
        test_email = f"retailer_{self.unique_suffix}@storemail.com"
        # First signin to get user_id
        sign_res = self.client.post("/api/auth/signin", json={
            "email": test_email,
            "password": "SecurePassword123"
        })
        user_id = sign_res.json()["user"]["user_id"]

        new_store_payload = {
            "store_name": "Sethi Gourmet Mart Indiranagar",
            "store_type": "Organic",
            "city": "Bengaluru",
            "region": "Karnataka & South India",
            "total_working_capital_inr": 750000.0,
            "default_min_margin_pct": 22.5
        }
        res = self.client.post(
            "/api/stores",
            json=new_store_payload,
            headers={"X-User-Id": user_id}
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "SUCCESS")
        self.assertEqual(data["profile"]["store_name"], "Sethi Gourmet Mart Indiranagar")

        # Verify the user now has multiple stores
        me_res = self.client.get(f"/api/auth/me?user_id={user_id}")
        self.assertEqual(me_res.status_code, 200)
        user_data = me_res.json()["user"]
        self.assertTrue(len(user_data["store_ids"]) >= 2)

    def test_05_switch_store_under_user(self):
        """Test switching active store branch under a user"""
        test_email = f"retailer_{self.unique_suffix}@storemail.com"
        sign_res = self.client.post("/api/auth/signin", json={
            "email": test_email,
            "password": "SecurePassword123"
        })
        user_id = sign_res.json()["user"]["user_id"]
        store_ids = sign_res.json()["user"]["store_ids"]

        if len(store_ids) >= 2:
            target_store = store_ids[0]
            switch_res = self.client.post("/api/auth/switch-store", json={
                "user_id": user_id,
                "store_id": target_store
            })
            self.assertEqual(switch_res.status_code, 200)
            data = switch_res.json()
            self.assertEqual(data["active_store_id"], target_store)

if __name__ == "__main__":
    unittest.main()

