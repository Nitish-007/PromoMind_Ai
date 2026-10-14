import os
import sys
import unittest

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from fastapi.testclient import TestClient
from main import app
from models import StoreProfile
from storage import StoreDataManager
from firestore_service import FirestoreService

class TestPromoMindPhase2(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_01_health_check(self):
        res = self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["service"], "PromoMind AI")

    def test_02_cloud_status(self):
        res = self.client.get("/api/system/cloud-status")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("is_connected", data)
        self.assertIn("mode", data)
        self.assertIn("credentials_found", data)

    def test_03_store_profile_and_knowledge_sync(self):
        test_prof = {
            "store_name": "Test Bangalore Mart",
            "owner_name": "Suresh Kumar",
            "region": "Karnataka & South India",
            "city": "Bengaluru",
            "locality": "Indiranagar",
            "pin_code": "560038",
            "phone": "+91 99887 76655",
            "store_format": "Supermarket",
            "whatsapp_audience_size": 2500,
            "default_min_margin_pct": 16.5,
            "total_working_capital_inr": 650000.0
        }
        res_post = self.client.post("/api/profile", json=test_prof)
        self.assertEqual(res_post.status_code, 200)
        prof_data = res_post.json()
        self.assertEqual(prof_data["store_name"], "Test Bangalore Mart")
        self.assertEqual(prof_data["total_working_capital_inr"], 650000.0)

        # Check knowledge base markdown contains the updated profile & target margin
        res_md = self.client.get("/api/knowledge-md")
        self.assertEqual(res_md.status_code, 200)
        md_text = res_md.json()["markdown"]
        self.assertIn("Test Bangalore Mart", md_text)
        self.assertIn("Karnataka & South India", md_text)
        self.assertIn("16.5%", md_text)

    def test_04_financial_roi_prediction(self):
        res = self.client.get("/api/store/financial-roi")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertGreater(data["total_inventory_invested_inr"], 0)
        self.assertGreater(data["projected_sales_revenue_inr"], 0)
        self.assertGreater(data["projected_gross_profit_inr"], 0)
        self.assertGreaterEqual(data["overall_roi_pct"], 0)
        self.assertGreaterEqual(data["dead_capital_at_risk_inr"], 0)
        self.assertGreaterEqual(data["unlocked_capital_from_promos_inr"], 0)

    def test_05_interactive_roi_simulation(self):
        sim_req = {
            "proposed_discount_depth_pct": 18.0,
            "expected_volume_lift_pct": 40.0
        }
        res = self.client.post("/api/store/simulate-roi", json=sim_req)
        self.assertEqual(res.status_code, 200)
        sim = res.json()
        self.assertGreater(sim["simulated_revenue_inr"], 0)
        self.assertGreater(sim["simulated_profit_inr"], 0)
        self.assertIn("turnover_speedup_days", sim)
        self.assertEqual(sim["net_verdict"], "PROFIT_POSITIVE")

    def test_06_regional_calendar_multi_horizon(self):
        res = self.client.get("/api/calendar/events?region=Karnataka%20%26%20South%20India")
        self.assertEqual(res.status_code, 200)
        events = res.json()
        self.assertGreaterEqual(len(events), 2)
        
        deepavali_event = next((e for e in events if "Deepavali" in e["name"]), None)
        self.assertIsNotNone(deepavali_event)
        self.assertIsNotNone(deepavali_event["advance_procurement_window"])
        self.assertIsNotNone(deepavali_event["promo_launch_window"])
        self.assertIsNotNone(deepavali_event["clearance_window"])
        self.assertIsNotNone(deepavali_event["tradition_notes"])

    def test_07_dynamic_combo_generation_with_archetypes(self):
        # Test Anchor Margin Booster
        req1 = {
            "prompt": "Festive tea and biscuit basket",
            "min_margin_pct": 18.0,
            "event_theme": "Diwali Maha Utsav",
            "offer_type": "COMBO_DISCOUNT",
            "region": "Karnataka & South India",
            "archetype": "ANCHOR_MARGIN_BOOSTER"
        }
        res1 = self.client.post("/api/generate-combo", json=req1)
        self.assertEqual(res1.status_code, 200)
        plan1 = res1.json()
        self.assertEqual(plan1["archetype"], "ANCHOR_MARGIN_BOOSTER")
        self.assertGreaterEqual(plan1["net_margin_pct"], 15.0)
        self.assertIn("creative_assets", plan1)
        self.assertIsNotNone(plan1["creative_assets"]["cashier_counter_pitch"])
        self.assertIn("bachat", plan1["creative_assets"]["cashier_counter_pitch"].lower())

        # Test Expiry Rescue Clearance
        req2 = {
            "prompt": "Clear expiring items immediately before date",
            "min_margin_pct": 12.0,
            "event_theme": "Clearance Rush",
            "offer_type": "BOGO",
            "region": "Karnataka & South India",
            "archetype": "EXPIRY_RESCUE_CLEARANCE"
        }
        res2 = self.client.post("/api/generate-combo", json=req2)
        self.assertEqual(res2.status_code, 200)
        plan2 = res2.json()
        self.assertEqual(plan2["archetype"], "EXPIRY_RESCUE_CLEARANCE")
        self.assertGreater(plan2["discount_pct"], 15.0)

if __name__ == "__main__":
    unittest.main()
