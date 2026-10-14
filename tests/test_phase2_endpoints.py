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
        
        deepavali_event = next((e for e in events if "Deepavali" in e["name"] or "Diwali" in e["name"]), None)
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
        self.assertTrue(any(w in plan1["creative_assets"]["cashier_counter_pitch"].lower() for w in ["bachat", "save", "combo", "deal", "festive", "discount"]))
        self.assertIn("hybrid_architecture", plan1)
        self.assertEqual(plan1["hybrid_architecture"]["engine_type"], "NEURO_SYMBOLIC_HYBRID")
        self.assertTrue(plan1["hybrid_architecture"]["math_layer"]["margin_floor_protected"])

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

    def test_08_multi_variety_promotions(self):
        """Verify that promotion generation is never static and produces 5 distinct demographic varieties."""
        req = {
            "prompt": "Diwali sweets and ghee combo with dry fruits",
            "min_margin_pct": 18.0,
            "event_theme": "Diwali Maha Utsav",
            "offer_type": "COMBO_DISCOUNT",
            "region": "Karnataka & South India",
            "archetype": "ANCHOR_MARGIN_BOOSTER"
        }
        res = self.client.post("/api/generate-combo", json=req)
        self.assertEqual(res.status_code, 200)
        plan = res.json()

        self.assertIn("varieties", plan)
        varieties = plan["varieties"]
        self.assertEqual(len(varieties), 5)

        variety_types = [v["variety_type"] for v in varieties]
        self.assertIn("MARGIN_BOOSTER", variety_types)
        self.assertIn("EXPIRY_CLEARANCE", variety_types)
        self.assertIn("VOLUME_SLAB", variety_types)
        self.assertIn("FESTIVE_HAMPER", variety_types)
        self.assertIn("BILL_BUSTER", variety_types)

        # Check non-static variety attributes
        discounts = set(v["discount_pct"] for v in varieties)
        self.assertGreaterEqual(len(discounts), 3, "Discounts must be diverse and non-static across varieties")

        recommended_count = sum(1 for v in varieties if v["is_recommended"])
        self.assertEqual(recommended_count, 1, "Exactly one variety should be marked as recommended")

        for v in varieties:
            self.assertIsNotNone(v["cashier_counter_pitch"])
            self.assertIsNotNone(v["whatsapp_copy"])
            self.assertIsNotNone(v["poster_headline"])
            self.assertGreater(v["projected_volume_lift_pct"], 0)
            self.assertGreater(v["capital_turnover_days"], 0)
            self.assertGreater(v["net_margin_pct"], 0)
            self.assertIsNotNone(v["customer_target"])

    def test_09_autonomous_weekly_offer_ideas(self):
        """Verify that weekly offer ideas can be retrieved autonomously without manual product selection."""
        res = self.client.get("/api/weekly-offer-ideas?region=Karnataka%20%26%20South%20India")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "SUCCESS")
        self.assertGreaterEqual(data["count"], 2)

        ideas = data["ideas"]
        for idea in ideas:
            self.assertIn("anchor_id", idea)
            self.assertIn("attached_id", idea)
            self.assertIn("combo_price", idea)
            self.assertIn("savings_amount", idea)
            self.assertIn("net_margin_pct", idea)
            self.assertIn("why_recommended", idea)
            self.assertGreater(idea["original_mrp"], idea["combo_price"])
            self.assertGreater(idea["net_margin_pct"], 14.0)

    def test_10_copilot_chatbot_margin_intent(self):
        """Verify the conversational chatbot copilot parses requested margin and triggers tools."""
        # Test 1: Direct margin command in prompt
        chat_req = {
            "message": "Create a tea and biscuit bundle with 21% profit margin for this weekend",
            "store_region": "Karnataka & South India"
        }
        res = self.client.post("/api/chat", json=chat_req)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["intent"], "PROMOTION_GENERATED")
        self.assertEqual(data["detected_margin_pct"], 21.0)
        self.assertIsNotNone(data["plan"])
        self.assertIn("reply", data)
        self.assertGreaterEqual(data["plan"]["net_margin_pct"], 18.0)

        # Test 2: Weekly offer ideas query
        ideas_req = {
            "message": "What offer ideas can I run this week with 16% margin?",
            "store_region": "Karnataka & South India"
        }
        res2 = self.client.post("/api/chat", json=ideas_req)
        self.assertEqual(res2.status_code, 200)
        data2 = res2.json()
        self.assertEqual(data2["intent"], "WEEKLY_IDEAS")
        self.assertEqual(data2["detected_margin_pct"], 16.0)
        self.assertGreaterEqual(len(data2["ideas"]), 2)

        # Test 3: Dead capital audit query
        roi_req = {
            "message": "How much dead capital is trapped in my inventory right now?",
            "store_region": "Karnataka & South India"
        }
        res3 = self.client.post("/api/chat", json=roi_req)
        self.assertEqual(res3.status_code, 200)
        data3 = res3.json()
        self.assertEqual(data3["intent"], "ROI_INSIGHT")
        self.assertIsNotNone(data3["roi_summary"])
        # Test 4: Dynamic regional festivals and cultural demand spikes
        fest_req = {
            "message": "What festivals are coming up in Karnataka and what should I sell?",
            "region": "Karnataka & South India"
        }
        res4 = self.client.post("/api/chat", json=fest_req)
        self.assertEqual(res4.status_code, 200)
        data4 = res4.json()
        self.assertEqual(data4["intent"], "FESTIVAL_CALENDAR_INSIGHT")
        self.assertIsNotNone(data4["plan"])
        self.assertIn("festiv", data4["reply"].lower())

    def test_11_dynamic_regional_festival_discovery(self):
        """Verify dynamic AI regional festival discovery and matched inventory."""
        # Test GET /api/calendar/events with region
        res = self.client.get("/api/calendar/events?region=Karnataka&country=India")
        self.assertEqual(res.status_code, 200)
        events = res.json()
        self.assertGreaterEqual(len(events), 3)
        for ev in events:
            self.assertIn("name", ev)
            self.assertIn("date_window", ev)
            self.assertIn("key_items", ev)
            self.assertIn("demand_lift_pct", ev)
            self.assertGreater(ev["demand_lift_pct"], 30.0)
            self.assertIn("matched_inventory_items", ev)

        # Test POST /api/calendar/discover for custom region
        disc_req = {
            "region": "West Bengal",
            "country": "India"
        }
        res2 = self.client.post("/api/calendar/discover", json=disc_req)
        self.assertEqual(res2.status_code, 200)
        wb_events = res2.json()
        self.assertGreaterEqual(len(wb_events), 2)
        event_names = [e["name"].lower() for e in wb_events]
        self.assertTrue(any("durga" in name or "puja" in name or "pujo" in name or "kali" in name or "bengali" in name for name in event_names))

if __name__ == "__main__":
    unittest.main()



