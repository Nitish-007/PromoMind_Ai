import os
import sys
import json
import time
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)

# Auto-load environment variables from backend/.env and project root .env
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(CURRENT_DIR, ".env"))
    load_dotenv(os.path.join(PROJECT_ROOT, ".env"))
except Exception:
    pass

DATA_DIR = os.environ.get("PROMOMIND_DATA_DIR") or os.path.join(PROJECT_ROOT, "data")

if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from models import Product, RegionalFestivalEvent, ScheduledOffer, StoreProfile
from mock_data import (
    INVENTORY_DATA, DEMAND_FORECASTS, 
    REGIONAL_FESTIVAL_CALENDAR, SCHEDULED_OFFERS
)
from forecasting import OpenSourceForecastingEngine

logger = logging.getLogger("PromoMind.Storage")

# Firestore Optional Import & Driver Handling
try:
    from google.cloud import firestore
    from google.oauth2 import service_account
    from google.auth.exceptions import DefaultCredentialsError
    from google.api_core.exceptions import GoogleAPICallError
    FIRESTORE_AVAILABLE = True
except Exception as e:
    firestore = None
    FIRESTORE_AVAILABLE = False
    logger.info(f"Google Cloud Firestore driver not active: {e}")

# Default Kirana / Supermarket Customer List
DEFAULT_CUSTOMER_LIST: List[Dict[str, Any]] = [
    {"name": "Ananya Rao", "phone": "+91 98451 22334", "segment": "Festive Gifting / High AOV", "preferred_channel": "WhatsApp"},
    {"name": "Vikram Patel", "phone": "+91 98452 33445", "segment": "Weekly Pantry Staples", "preferred_channel": "WhatsApp"},
    {"name": "Meera Iyer", "phone": "+91 98453 44556", "segment": "Dairy & Sweet Making", "preferred_channel": "WhatsApp"},
    {"name": "Karthik Reddy", "phone": "+91 98454 55667", "segment": "Evening Snacks & Tea", "preferred_channel": "POS"},
    {"name": "Sunita Jain", "phone": "+91 98455 66778", "segment": "Dry Fruits & Bulk Staples", "preferred_channel": "WhatsApp"}
]

# Baseline Store Profile for Sharma Supermarket
DEFAULT_STORE_PROFILE: Dict[str, Any] = {
    "store_id": "sharma_supermarket_01",
    "store_name": "Sharma Supermarket & Kirana",
    "owner_name": "Ramesh Sharma",
    "phone": "+91 98450 12345",
    "gstin": "29AAAAA0000A1Z5",
    "store_type": "Supermarket",
    "audience_size": 1420,
    "region": "Karnataka & South India",
    "city": "Bengaluru",
    "locality": "Koramangala 4th Block",
    "pin_code": "560034",
    "customer_list": DEFAULT_CUSTOMER_LIST,
    "updated_at": "2026-10-14T10:00:00Z"
}


class DualModeStorageAdapter:
    """
    Dual-Mode Hybrid Storage Adapter:
    
    1. Cloud Mode:
       When Google Cloud credentials are provided, reads and writes directly to Firestore collections:
         - stores/{store_id}/inventory: Real-time stock levels, MRP, cost, and velocities.
         - stores/{store_id}/promotions: Active/scheduled campaigns, pricing tiers, and conflict logs.
         - stores/{store_id}/calendar_events: Regional festive event calendar.
         - stores/{store_id}/store_profile: Store metadata, location, and customer list.
         - stores/{store_id}/knowledge_catalog: Compiled Markdown catalog (store_knowledge.md).
    
    2. Offline / Local Fallback Mode:
       Automatically falls back to local JSON + Markdown when running without internet or credentials,
       ensuring 100% zero downtime.
       
    3. Instant Sync with AI Knowledge Base:
       Any update to Firestore triggers an automatic re-compilation of data/store_knowledge.md
       for AI agent grounding, and writes the snapshot to stores/{store_id}/knowledge_catalog.
    """

    def __init__(
        self,
        store_id: Optional[str] = None,
        project_id: Optional[str] = None,
        force_mode: Optional[str] = None,
        firestore_client: Optional[Any] = None,
        data_dir: Optional[str] = None
    ):
        self.store_id = store_id or os.environ.get("STORE_ID", "sharma_supermarket_01")
        self.project_id = project_id or os.environ.get("FIRESTORE_PROJECT_ID") or os.environ.get("GCP_PROJECT_ID")
        self.mode = "LOCAL_FALLBACK"
        self.client = firestore_client
        self.fallback_reason: Optional[str] = None
        self.last_sync_timestamp: Optional[str] = None
        self.instant_sync_active: bool = True
        self._listener_unsubscribe = None

        self.data_dir = data_dir or os.environ.get("PROMOMIND_DATA_DIR") or DATA_DIR
        self.store_json_file = os.path.join(self.data_dir, "inventory_store.json")
        self.knowledge_md_file = os.path.join(self.data_dir, "store_knowledge.md")
        self.promotions_json_file = os.path.join(self.data_dir, "promotions_store.json")
        self.calendar_json_file = os.path.join(self.data_dir, "calendar_events.json")
        self.profile_json_file = os.path.join(self.data_dir, "store_profile.json")
        self.conflict_logs_file = os.path.join(self.data_dir, "conflict_logs.json")

        self._ensure_local_data_dir()
        self._init_connection(force_mode)

    def _ensure_local_data_dir(self):
        os.makedirs(self.data_dir, exist_ok=True)

    def _init_connection(self, force_mode: Optional[str] = None):
        """Attempt to establish Cloud Mode via Firestore client or fall back cleanly."""
        requested_mode = (force_mode or os.environ.get("STORAGE_MODE", "AUTO")).upper()
        if requested_mode == "LOCAL":
            self.mode = "LOCAL_FALLBACK"
            self.fallback_reason = "Manually forced to LOCAL_FALLBACK via STORAGE_MODE configuration."
            logger.info("Storage Adapter initialized in LOCAL_FALLBACK mode (forced).")
            return

        if self.client is not None:
            self.mode = "CLOUD"
            self.fallback_reason = None
            logger.info(f"Storage Adapter initialized in CLOUD mode with provided Firestore client for store: {self.store_id}")
            self._start_realtime_sync_listener()
            return

        if not FIRESTORE_AVAILABLE:
            self.mode = "LOCAL_FALLBACK"
            self.fallback_reason = "google-cloud-firestore library is not installed in the current environment."
            logger.warning("google-cloud-firestore not available. Operating in LOCAL_FALLBACK mode.")
            return

    @staticmethod
    def parse_inline_service_account(raw_val: Optional[str]) -> Optional[Dict[str, Any]]:
        """
        Parse raw inline service account string (JSON, single-quoted JSON, or base64 encoded JSON).
        Returns parsed dict containing service account keys, or None if invalid.
        """
        if not raw_val or not isinstance(raw_val, str):
            return None

        cleaned = raw_val.strip()
        if not cleaned:
            return None

        # Strip outer quotes if enclosed in single or double quotes
        if (cleaned.startswith("'") and cleaned.endswith("'")) or (cleaned.startswith('"') and cleaned.endswith('"')):
            cleaned = cleaned[1:-1].strip()

        # 1. Direct JSON parse
        try:
            data = json.loads(cleaned)
            if isinstance(data, dict) and ("type" in data or "client_email" in data or "private_key" in data):
                return data
        except Exception:
            pass

        # 2. Try base64 decoding (useful for single-line base64 env vars)
        try:
            import base64
            decoded = base64.b64decode(cleaned).decode("utf-8")
            data = json.loads(decoded)
            if isinstance(data, dict) and ("type" in data or "client_email" in data or "private_key" in data):
                return data
        except Exception:
            pass

        # 3. Clean escaped newlines/characters if unescaped in .env or multiline paste
        try:
            normalized = cleaned.replace("\\n", "\n").replace('\\"', '"').replace("\\'", "'")
            data = json.loads(normalized)
            if isinstance(data, dict) and ("type" in data or "client_email" in data or "private_key" in data):
                return data
        except Exception:
            pass

        return None

    def _init_connection(self, force_mode: Optional[str] = None):
        """Attempt to establish Cloud Mode via Firestore client or fall back cleanly."""
        requested_mode = (force_mode or os.environ.get("STORAGE_MODE", "AUTO")).upper()
        if requested_mode == "LOCAL":
            self.mode = "LOCAL_FALLBACK"
            self.fallback_reason = "Manually forced to LOCAL_FALLBACK via STORAGE_MODE configuration."
            logger.info("Storage Adapter initialized in LOCAL_FALLBACK mode (forced).")
            return

        if self.client is not None:
            self.mode = "CLOUD"
            self.fallback_reason = None
            logger.info(f"Storage Adapter initialized in CLOUD mode with provided Firestore client for store: {self.store_id}")
            self._start_realtime_sync_listener()
            return

        if not FIRESTORE_AVAILABLE:
            self.mode = "LOCAL_FALLBACK"
            self.fallback_reason = "google-cloud-firestore library is not installed in the current environment."
            logger.warning("google-cloud-firestore not available. Operating in LOCAL_FALLBACK mode.")
            return

        try:
            # 1. Check for Inline Service Account JSON across common environment variables
            inline_candidates = [
                os.environ.get("FIRESTORE_SA_JSON"),
                os.environ.get("GCP_SA_KEY"),
                os.environ.get("FIRESTORE_CREDENTIALS_JSON"),
                os.environ.get("GCP_SERVICE_ACCOUNT_JSON"),
                os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_JSON"),
                os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")  # In case user pasted raw JSON directly here
            ]

            parsed_sa = None
            for candidate in inline_candidates:
                if candidate and (candidate.strip().startswith("{") or "client_email" in candidate):
                    parsed_sa = self.parse_inline_service_account(candidate)
                    if parsed_sa:
                        break

            if parsed_sa:
                # Auto-extract and prioritize project_id from inline SA JSON
                sa_proj = parsed_sa.get("project_id")
                if sa_proj:
                    self.project_id = sa_proj
                    logger.info(f"Using project_id '{self.project_id}' from inline Service Account JSON.")

                creds = service_account.Credentials.from_service_account_info(parsed_sa)
                self.client = firestore.Client(project=self.project_id or creds.project_id, credentials=creds)
                logger.info("Initialized Firestore client using inline Service Account JSON.")

            elif os.environ.get("GOOGLE_APPLICATION_CREDENTIALS") and os.path.exists(os.environ["GOOGLE_APPLICATION_CREDENTIALS"]):
                creds_file = os.environ["GOOGLE_APPLICATION_CREDENTIALS"]
                self.client = firestore.Client.from_service_account_json(creds_file, project=self.project_id)
                logger.info(f"Initialized Firestore client using credentials file: {creds_file}")

            else:
                # Attempt Application Default Credentials (ADC) or Emulator
                emulator_host = os.environ.get("FIRESTORE_EMULATOR_HOST")
                if emulator_host:
                    self.client = firestore.Client(project=self.project_id or "demo-promomind")
                elif self.project_id:
                    self.client = firestore.Client(project=self.project_id)
                else:
                    raise ValueError(
                        "No Google Cloud credentials or project configured. "
                        "Set FIRESTORE_SA_JSON (inline JSON) or FIRESTORE_PROJECT_ID."
                    )

            # Test connection probe with a shallow read
            _ = self.client.collection("stores").document(self.store_id).get()
            self.mode = "CLOUD"
            self.fallback_reason = None
            logger.info(f"Storage Adapter successfully connected to Google Cloud Firestore in CLOUD mode (store: {self.store_id}).")
            self._start_realtime_sync_listener()

        except Exception as e:
            self.mode = "LOCAL_FALLBACK"
            self.client = None
            self.fallback_reason = f"Cloud connection unavailable: {str(e)}"
            logger.info(f"Storage Adapter operating in LOCAL_FALLBACK mode: {self.fallback_reason}")

    # ==========================================================================
    # Firestore Collection References (stores/{store_id}/...)
    # ==========================================================================

    def _store_doc_ref(self):
        if not self.client:
            raise RuntimeError("Firestore client not connected.")
        return self.client.collection("stores").document(self.store_id)

    def _inventory_coll(self):
        return self._store_doc_ref().collection("inventory")

    def _promotions_coll(self):
        return self._store_doc_ref().collection("promotions")

    def _calendar_coll(self):
        return self._store_doc_ref().collection("calendar_events")

    def _profile_coll(self):
        return self._store_doc_ref().collection("store_profile")

    def _catalog_coll(self):
        return self._store_doc_ref().collection("knowledge_catalog")

    # ==========================================================================
    # 1. Inventory Collection: stores/{store_id}/inventory
    # ==========================================================================

    def load_products(self) -> List[Product]:
        """Load inventory from Firestore collection stores/{store_id}/inventory, with local fallback."""
        if self.mode == "CLOUD" and self.client:
            try:
                docs = list(self._inventory_coll().stream())
                if docs:
                    products = []
                    for doc in docs:
                        data = doc.to_dict()
                        if "id" not in data:
                            data["id"] = doc.id
                        products.append(Product(**data))
                    # Sync local cache
                    self._save_local_products_cache(products)
                    return products
                else:
                    # Seed cloud collection with baseline inventory
                    logger.info("Firestore inventory empty. Seeding baseline products...")
                    self.save_products(INVENTORY_DATA)
                    return INVENTORY_DATA
            except Exception as e:
                logger.warning(f"Failed to read from Firestore inventory, falling back to local: {e}")

        # Local Fallback
        return self._load_local_products()

    def save_products(self, products: List[Product]):
        """Persist inventory to stores/{store_id}/inventory and trigger instant sync."""
        if self.mode == "CLOUD" and self.client:
            try:
                batch = self.client.batch()
                coll = self._inventory_coll()
                for p in products:
                    doc_ref = coll.document(p.id)
                    batch.set(doc_ref, p.model_dump())
                batch.commit()
            except Exception as e:
                logger.warning(f"Error persisting products to Firestore: {e}")

        # Local persistence & Instant Sync
        self._save_local_products_cache(products)
        self.rebuild_knowledge_markdown(products)

    def add_or_update_product(self, product: Product) -> List[Product]:
        """Add or update an individual product SKU, sync to Firestore and AI Knowledge Base."""
        products = self.load_products()
        idx = next((i for i, p in enumerate(products) if p.id == product.id), None)
        if idx is not None:
            products[idx] = product
        else:
            products.append(product)

        if self.mode == "CLOUD" and self.client:
            try:
                self._inventory_coll().document(product.id).set(product.model_dump())
            except Exception as e:
                logger.warning(f"Error writing product {product.id} to Firestore: {e}")

        self._save_local_products_cache(products)
        self.rebuild_knowledge_markdown(products)
        return products

    def import_csv_data(self, csv_content: str) -> Tuple[int, str]:
        """Parse CSV rows, compute Holt-Winters curves, persist to Firestore, and sync AI Knowledge Base."""
        import csv
        import io

        reader = csv.DictReader(io.StringIO(csv_content.strip()))
        imported = 0
        products = self.load_products()

        for row in reader:
            name = row.get("name") or row.get("product_name") or row.get("Product")
            if not name:
                continue
            cat = row.get("category") or row.get("Category") or "General Staples"
            cost = float(row.get("cost_price") or row.get("cost") or row.get("Cost") or 100.0)
            mrp = float(row.get("selling_price") or row.get("mrp") or row.get("MRP") or cost * 1.25)
            stock = int(row.get("stock_quantity") or row.get("stock") or row.get("Stock") or 50)
            weekly_avg = int(row.get("weekly_sales_avg") or row.get("sales_avg") or row.get("Velocity") or 20)
            expiry = int(row.get("expiry_days") or row.get("expiry") or row.get("Expiry") or 300)
            brand_notes = row.get("brand_comparison_insight") or row.get("brand_notes") or f"Imported SKU for {cat}."

            sku_id = f"PROD_CSV_{len(products) + 1:02d}"
            base_sales = [
                int(weekly_avg * 0.85), int(weekly_avg * 0.90),
                int(weekly_avg * 0.95), int(weekly_avg * 1.00),
                int(weekly_avg * 1.05), weekly_avg
            ]
            forecast = OpenSourceForecastingEngine.predict_demand_surge(base_sales, event_surge_pct=35.0)
            velocity = "FAST_MOVING" if weekly_avg >= 35 else ("SLOW_MOVING" if weekly_avg <= 15 else "MODERATE")
            days_rem = int((stock / max(1, weekly_avg)) * 7)
            verdict = "STRONG_INVEST_BUY" if forecast["expected_growth_pct"] >= 25 else ("DO_NOT_REORDER" if days_rem >= 70 else "CAUTION_CHECK_BRANDS")
            badge = "🟢 Strong Buy / Restock Now" if verdict == "STRONG_INVEST_BUY" else ("🛑 Do Not Reorder" if verdict == "DO_NOT_REORDER" else "🟡 Check Brands")

            p = Product(
                id=sku_id,
                name=name,
                category=cat,
                cost_price=cost,
                selling_price=mrp,
                stock_quantity=stock,
                days_in_stock=5,
                expiry_days=expiry,
                velocity_status=velocity,
                weekly_sales_avg=weekly_avg,
                image_url="product_default.png",
                past_sales_weeks=base_sales,
                forecast_sales_weeks=forecast["forecast_sales"],
                sell_through_verdict=verdict,
                verdict_badge=badge,
                days_inventory_remaining=days_rem,
                sell_through_rate_pct=min(100.0, round((weekly_avg * 4 / max(1, stock)) * 100, 1)),
                reorder_recommendation=forecast["forecast_recommendation"],
                brand_comparison_insight=brand_notes,
                alternative_brands=["Local Wholesaler Grade-A", "National Market Alternative"]
            )
            products.append(p)
            imported += 1

        self.save_products(products)
        return imported, self.get_knowledge_markdown()

    def _load_local_products(self) -> List[Product]:
        if not os.path.exists(self.store_json_file):
            self._save_local_products_cache(INVENTORY_DATA)
            return INVENTORY_DATA
        try:
            with open(self.store_json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return [Product(**item) for item in data]
        except Exception as e:
            logger.warning(f"Could not parse local JSON inventory: {e}. Returning INVENTORY_DATA.")
            return INVENTORY_DATA

    def _save_local_products_cache(self, products: List[Product]):
        self._ensure_local_data_dir()
        data = [p.model_dump() for p in products]
        with open(self.store_json_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    # ==========================================================================
    # 2. Promotions Collection: stores/{store_id}/promotions
    # ==========================================================================

    def get_promotions(self) -> List[Dict[str, Any]]:
        """Retrieve active and scheduled campaigns from stores/{store_id}/promotions."""
        if self.mode == "CLOUD" and self.client:
            try:
                docs = list(self._promotions_coll().stream())
                promos = [
                    d.to_dict() for d in docs
                    if d.to_dict().get("type") != "conflict_log"
                ]
                if promos:
                    self._save_local_promotions_cache(promos)
                    return promos
                else:
                    # Seed with default SCHEDULED_OFFERS
                    for offer in SCHEDULED_OFFERS:
                        self.save_promotion(offer)
                    return SCHEDULED_OFFERS
            except Exception as e:
                logger.warning(f"Firestore promotions query failed: {e}. Falling back to local.")

        return self._load_local_promotions()

    def save_promotion(self, offer: Dict[str, Any]) -> Dict[str, Any]:
        """Save a promotional offer to stores/{store_id}/promotions."""
        offer_id = offer.get("id") or f"OFFER_LIVE_{int(time.time())}"
        offer_data = dict(offer)
        offer_data["id"] = offer_id
        offer_data["type"] = "promotion"
        offer_data.setdefault("combo_id", f"COMBO_{int(offer_data.get('combo_price', 0))}")
        offer_data.setdefault("start_date", "2026-10-15")
        offer_data.setdefault("end_date", "2026-10-25")
        offer_data.setdefault("event_theme", "Active Campaign")
        offer_data.setdefault("status", "ACTIVE")
        offer_data["updated_at"] = datetime.now(timezone.utc).isoformat()

        if self.mode == "CLOUD" and self.client:
            try:
                self._promotions_coll().document(offer_id).set(offer_data)
            except Exception as e:
                logger.warning(f"Failed to write promotion {offer_id} to Firestore: {e}")

        # Update local cache
        current = self._load_local_promotions()
        existing_idx = next((i for i, o in enumerate(current) if o.get("id") == offer_id), None)
        if existing_idx is not None:
            current[existing_idx] = offer_data
        else:
            current.insert(0, offer_data)
        self._save_local_promotions_cache(current)
        return offer_data

    def log_conflict(self, conflict_data: Dict[str, Any]) -> Dict[str, Any]:
        """Log detected promotion conflict to stores/{store_id}/promotions."""
        log_id = f"CONFLICT_{int(time.time() * 1000)}"
        entry = dict(conflict_data)
        entry["id"] = log_id
        entry["type"] = "conflict_log"
        entry["timestamp"] = datetime.now(timezone.utc).isoformat()

        if self.mode == "CLOUD" and self.client:
            try:
                self._promotions_coll().document(log_id).set(entry)
            except Exception as e:
                logger.warning(f"Failed to log conflict to Firestore: {e}")

        # Update local conflict log
        self._ensure_local_data_dir()
        logs = []
        if os.path.exists(self.conflict_logs_file):
            try:
                with open(self.conflict_logs_file, "r", encoding="utf-8") as f:
                    logs = json.load(f)
            except Exception:
                logs = []
        logs.insert(0, entry)
        with open(self.conflict_logs_file, "w", encoding="utf-8") as f:
            json.dump(logs[:50], f, indent=2)
        return entry

    def get_conflict_logs(self) -> List[Dict[str, Any]]:
        """Retrieve recent conflict detection logs."""
        if self.mode == "CLOUD" and self.client:
            try:
                docs = list(self._promotions_coll().where("type", "==", "conflict_log").stream())
                if docs:
                    return [d.to_dict() for d in docs]
            except Exception as e:
                logger.warning(f"Error querying conflict logs from Firestore: {e}")

        if os.path.exists(self.conflict_logs_file):
            try:
                with open(self.conflict_logs_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def _load_local_promotions(self) -> List[Dict[str, Any]]:
        if not os.path.exists(self.promotions_json_file):
            self._save_local_promotions_cache(SCHEDULED_OFFERS)
            return SCHEDULED_OFFERS
        try:
            with open(self.promotions_json_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return SCHEDULED_OFFERS

    def _save_local_promotions_cache(self, promos: List[Dict[str, Any]]):
        self._ensure_local_data_dir()
        with open(self.promotions_json_file, "w", encoding="utf-8") as f:
            json.dump(promos, f, indent=2, ensure_ascii=False)

    # ==========================================================================
    # 3. Calendar Events Collection: stores/{store_id}/calendar_events
    # ==========================================================================

    def get_calendar_events(self, region: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve regional festive event calendar from stores/{store_id}/calendar_events."""
        events = []
        if self.mode == "CLOUD" and self.client:
            try:
                docs = list(self._calendar_coll().stream())
                if docs:
                    events = [d.to_dict() for d in docs]
                    self._save_local_calendar_cache(events)
                else:
                    # Seed with default events
                    for ev in REGIONAL_FESTIVAL_CALENDAR:
                        self.save_calendar_event(ev)
                    events = REGIONAL_FESTIVAL_CALENDAR
            except Exception as e:
                logger.warning(f"Error fetching calendar from Firestore: {e}")

        if not events:
            events = self._load_local_calendar()

        if region:
            filtered = [e for e in events if region.lower() in e.get("region", "").lower()]
            if filtered:
                return filtered
        return events

    def save_calendar_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Save festival event into stores/{store_id}/calendar_events."""
        event_id = event_data.get("id") or f"EVT_{int(time.time())}"
        data = dict(event_data)
        data["id"] = event_id
        data.setdefault("date_window", "Oct 2026")
        data.setdefault("status", "UPCOMING")
        data.setdefault("key_items", [])
        data.setdefault("demand_lift_pct", 30.0)
        data.setdefault("icon", "🪔")
        data.setdefault("description", "")

        if self.mode == "CLOUD" and self.client:
            try:
                self._calendar_coll().document(event_id).set(data)
            except Exception as e:
                logger.warning(f"Error writing calendar event to Firestore: {e}")

        current = self._load_local_calendar()
        idx = next((i for i, ev in enumerate(current) if ev.get("id") == event_id), None)
        if idx is not None:
            current[idx] = data
        else:
            current.append(data)
        self._save_local_calendar_cache(current)
        return data

    def _load_local_calendar(self) -> List[Dict[str, Any]]:
        if not os.path.exists(self.calendar_json_file):
            self._save_local_calendar_cache(REGIONAL_FESTIVAL_CALENDAR)
            return REGIONAL_FESTIVAL_CALENDAR
        try:
            with open(self.calendar_json_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return REGIONAL_FESTIVAL_CALENDAR

    def _save_local_calendar_cache(self, events: List[Dict[str, Any]]):
        self._ensure_local_data_dir()
        with open(self.calendar_json_file, "w", encoding="utf-8") as f:
            json.dump(events, f, indent=2, ensure_ascii=False)

    # ==========================================================================
    # 4. Store Profile Collection: stores/{store_id}/store_profile
    # ==========================================================================

    def get_store_profile(self) -> Dict[str, Any]:
        """Retrieve store metadata, location, and customer list from stores/{store_id}/store_profile."""
        if self.mode == "CLOUD" and self.client:
            try:
                doc = self._profile_coll().document("profile").get()
                if doc.exists:
                    profile = doc.to_dict()
                    self._save_local_profile_cache(profile)
                    return profile
                else:
                    # Seed default store profile for this cloud store
                    self.save_store_profile(DEFAULT_STORE_PROFILE)
                    return dict(DEFAULT_STORE_PROFILE)
            except Exception as e:
                logger.warning(f"Error reading store profile from Firestore: {e}")

        return self._load_local_profile()

    def save_store_profile(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """Save store metadata, location, and customer list to stores/{store_id}/store_profile."""
        data = dict(profile_data)
        data["store_id"] = self.store_id
        data["updated_at"] = datetime.now(timezone.utc).isoformat()
        if "customer_list" not in data or not data["customer_list"]:
            data["customer_list"] = DEFAULT_CUSTOMER_LIST

        if self.mode == "CLOUD" and self.client:
            try:
                self._profile_coll().document("profile").set(data)
            except Exception as e:
                logger.warning(f"Failed to write store profile to Firestore: {e}")

        self._save_local_profile_cache(data)
        return data

    def _load_local_profile(self) -> Dict[str, Any]:
        if not os.path.exists(self.profile_json_file):
            self._save_local_profile_cache(DEFAULT_STORE_PROFILE)
            return dict(DEFAULT_STORE_PROFILE)
        try:
            with open(self.profile_json_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return dict(DEFAULT_STORE_PROFILE)

    def _save_local_profile_cache(self, profile: Dict[str, Any]):
        self._ensure_local_data_dir()
        with open(self.profile_json_file, "w", encoding="utf-8") as f:
            json.dump(profile, f, indent=2, ensure_ascii=False)

    # ==========================================================================
    # 5. Knowledge Catalog: stores/{store_id}/knowledge_catalog
    # ==========================================================================

    def rebuild_knowledge_markdown(self, products: Optional[List[Product]] = None) -> str:
        """
        Instant Sync with AI Knowledge Base:
        Any update to Firestore triggers an automatic re-compilation of data/store_knowledge.md
        for AI agent grounding, and synchronizes the catalog to stores/{store_id}/knowledge_catalog.
        """
        self._ensure_local_data_dir()
        if products is None:
            products = self.load_products()

        lines = [
            "# 🏪 PromoMind AI — Retail Store Knowledge & Catalog Base",
            f"> *Persistent AI Knowledge Catalog for Store ID: `{self.store_id}`*",
            f"> *Storage Mode: **{self.mode}** | Synchronized: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}*",
            "> *Auto-generated from retail inventory data & open-source demand forecasting engine.*\n",
            "---",
            "## 📦 1. Tracked Inventory & Predictive Velocity Status\n",
            "| SKU ID | Product Name | Category | Stock | Cost (₹) | MRP (₹) | Margin (%) | Velocity | Days Left | Reorder Verdict |",
            "|---|---|---|---|---|---|---|---|---|---|"
        ]

        for p in products:
            margin = round(((p.selling_price - p.cost_price) / max(0.1, p.selling_price)) * 100, 1)
            days_left = p.days_inventory_remaining or int((p.stock_quantity / max(1, p.weekly_sales_avg)) * 7)
            verdict = p.verdict_badge or p.sell_through_verdict or "MONITOR"
            lines.append(
                f"| `{p.id}` | {p.name} | {p.category} | {p.stock_quantity} | ₹{p.cost_price} | ₹{p.selling_price} | {margin}% | {p.velocity_status} | {days_left}d | {verdict} |"
            )

        lines.extend([
            "\n---",
            "## 📈 2. Demand Velocity & 10-Week Growth Trajectories\n"
        ])

        for p in products:
            past = p.past_sales_weeks or [30, 32, 35, 38, 40, 45]
            forecast = p.forecast_sales_weeks or [48, 52, 58, 62]
            past_str = ", ".join(str(x) for x in past)
            forecast_str = ", ".join(str(x) for x in forecast)
            past_avg = round(sum(past) / len(past), 1)
            fut_avg = round(sum(forecast) / len(forecast), 1)
            growth = round(((fut_avg - past_avg) / max(0.1, past_avg)) * 100, 1)
            growth_icon = "📈" if growth > 0 else "📉"

            lines.append(f"### {p.name} (`{p.id}`)")
            lines.append(f"- **Past 6-Week Sales Units**: `[{past_str}]` (Weekly Avg: **{past_avg}**)")
            lines.append(f"- **Forecast 4-Week Demand**: `[{forecast_str}]` (Weekly Projected: **{fut_avg}**)")
            lines.append(f"- **Growth Momentum**: {growth_icon} **{growth:+}% expected demand shift**")
            lines.append(f"- **Procurement Advice**: {p.reorder_recommendation or 'Maintain standard stock.'}")
            if p.brand_comparison_insight:
                lines.append(f"- **Brand Intelligence**: {p.brand_comparison_insight}")
            if p.alternative_brands:
                lines.append(f"- **Market Alternatives**: {'; '.join(p.alternative_brands)}")
            lines.append("")

        lines.extend([
            "---",
            "## 🪔 3. Active Festival Events & Demand Surge Calendar\n",
            "| Event Name | Focus Categories | Projected Demand Lift | Strategic Recommendation |",
            "|---|---|---|---|"
        ])

        # Dynamic Calendar grounding from storage
        events = self.get_calendar_events()
        for ev in events:
            items_str = ", ".join(ev.get("key_items", []))
            lift = f"+{ev.get('demand_lift_pct', 0)}%"
            desc = ev.get("description", "Seasonal retail surge window.")
            lines.append(f"| **{ev.get('name')}** | {items_str} | **{lift}** | {desc} |")

        lines.extend([
            "\n---",
            "## 🤖 4. Guidelines for Multi-Agent Combo Generation",
            "1. **Anchor Selection**: Identify items with positive growth momentum (>+30%) or seasonal surge.",
            "2. **Attached Selection**: Pair anchors with items that have high co-purchase affinity (>50%) or slow velocity to clear near-expiry capital.",
            "3. **Margin Floor**: Never breach retailer minimum margin (18% by default).",
            "4. **Copy Persona**: Punchy Indian retail phrasing with WhatsApp emojis and clear rupee savings."
        ])

        md_content = "\n".join(lines)

        # 1. Write locally to data/store_knowledge.md for AI agent grounding
        with open(self.knowledge_md_file, "w", encoding="utf-8") as f:
            f.write(md_content)

        # 2. Write to Firestore collection stores/{store_id}/knowledge_catalog
        if self.mode == "CLOUD" and self.client:
            try:
                catalog_payload = {
                    "store_id": self.store_id,
                    "markdown": md_content,
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                    "sku_count": len(products),
                    "mode": "CLOUD"
                }
                self._catalog_coll().document("current").set(catalog_payload)
            except Exception as e:
                logger.warning(f"Error persisting knowledge catalog to Firestore: {e}")

        self.last_sync_timestamp = datetime.now(timezone.utc).isoformat()
        return md_content

    def get_knowledge_markdown(self) -> str:
        """Retrieve current AI Store Knowledge Markdown catalog."""
        if self.mode == "CLOUD" and self.client:
            try:
                doc = self._catalog_coll().document("current").get()
                if doc.exists:
                    data = doc.to_dict()
                    md = data.get("markdown", "")
                    if md:
                        # Keep local file in sync
                        with open(self.knowledge_md_file, "w", encoding="utf-8") as f:
                            f.write(md)
                        return md
            except Exception as e:
                logger.warning(f"Failed to fetch knowledge catalog from Firestore: {e}")

        if not os.path.exists(self.knowledge_md_file):
            return self.rebuild_knowledge_markdown()

        with open(self.knowledge_md_file, "r", encoding="utf-8") as f:
            return f.read()

    # ==========================================================================
    # Real-Time Firestore Synchronization Listener
    # ==========================================================================

    def _start_realtime_sync_listener(self):
        """
        Start Firestore snapshot listener on stores/{store_id}/inventory.
        Any external update to Firestore automatically triggers re-compilation of data/store_knowledge.md.
        """
        if not self.client or self.mode != "CLOUD":
            return

        try:
            def on_inventory_snapshot(col_snapshot, changes, read_time):
                logger.info(f"Firestore inventory snapshot update detected ({len(col_snapshot)} docs). Rebuilding knowledge catalog...")
                try:
                    updated_prods = []
                    for doc in col_snapshot:
                        d = doc.to_dict()
                        if "id" not in d:
                            d["id"] = doc.id
                        updated_prods.append(Product(**d))
                    if updated_prods:
                        self._save_local_products_cache(updated_prods)
                        # Rebuild local knowledge markdown
                        self.rebuild_knowledge_markdown(updated_prods)
                except Exception as ex:
                    logger.warning(f"Error during real-time inventory sync: {ex}")

            self._listener_unsubscribe = self._inventory_coll().on_snapshot(on_inventory_snapshot)
            logger.info(f"Real-time Firestore sync listener attached to stores/{self.store_id}/inventory.")
        except Exception as e:
            logger.info(f"Real-time listener could not be registered (standard in serverless/offline environments): {e}")

    def close(self):
        """Cleanup listeners and connections."""
        if self._listener_unsubscribe:
            try:
                self._listener_unsubscribe.unsubscribe()
            except Exception:
                pass
            self._listener_unsubscribe = None

    # ==========================================================================
    # System Status & Diagnostic Telemetry
    # ==========================================================================

    def get_status(self) -> Dict[str, Any]:
        """Returns health and connection status of the hybrid storage adapter."""
        return {
            "mode": self.mode,
            "firestore_connected": self.mode == "CLOUD",
            "store_id": self.store_id,
            "collections": {
                "inventory": f"stores/{self.store_id}/inventory",
                "promotions": f"stores/{self.store_id}/promotions",
                "calendar_events": f"stores/{self.store_id}/calendar_events",
                "store_profile": f"stores/{self.store_id}/store_profile",
                "knowledge_catalog": f"stores/{self.store_id}/knowledge_catalog"
            },
            "instant_sync_active": self.instant_sync_active,
            "fallback_reason": self.fallback_reason,
            "last_sync_timestamp": self.last_sync_timestamp or datetime.now(timezone.utc).isoformat(),
            "local_cache_files": {
                "inventory": self.store_json_file,
                "knowledge_markdown": self.knowledge_md_file,
                "promotions": self.promotions_json_file,
                "calendar_events": self.calendar_json_file,
                "store_profile": self.profile_json_file,
                "conflict_logs": self.conflict_logs_file
            }
        }


# Singleton Default Storage Adapter Instance
_DEFAULT_ADAPTER = DualModeStorageAdapter()


class StoreDataManager:
    """
    Facade maintaining 100% backward compatibility for all existing API endpoints
    and multi-agent reasoning orchestrators, while delegating to DualModeStorageAdapter.
    """

    @classmethod
    def get_adapter(cls) -> DualModeStorageAdapter:
        return _DEFAULT_ADAPTER

    @classmethod
    def set_adapter(cls, adapter: DualModeStorageAdapter):
        global _DEFAULT_ADAPTER
        _DEFAULT_ADAPTER = adapter

    @classmethod
    def ensure_data_directory(cls):
        _DEFAULT_ADAPTER._ensure_local_data_dir()

    @classmethod
    def load_products(cls) -> List[Product]:
        return _DEFAULT_ADAPTER.load_products()

    @classmethod
    def save_products(cls, products: List[Product]):
        _DEFAULT_ADAPTER.save_products(products)

    @classmethod
    def add_or_update_product(cls, product: Product) -> List[Product]:
        return _DEFAULT_ADAPTER.add_or_update_product(product)

    @classmethod
    def import_csv_data(cls, csv_content: str) -> Tuple[int, str]:
        return _DEFAULT_ADAPTER.import_csv_data(csv_content)

    @classmethod
    def rebuild_knowledge_markdown(cls, products: Optional[List[Product]] = None) -> str:
        return _DEFAULT_ADAPTER.rebuild_knowledge_markdown(products)

    @classmethod
    def get_knowledge_markdown(cls) -> str:
        return _DEFAULT_ADAPTER.get_knowledge_markdown()

    # Extended Collections Support
    @classmethod
    def get_promotions(cls) -> List[Dict[str, Any]]:
        return _DEFAULT_ADAPTER.get_promotions()

    @classmethod
    def save_promotion(cls, offer: Dict[str, Any]) -> Dict[str, Any]:
        return _DEFAULT_ADAPTER.save_promotion(offer)

    @classmethod
    def log_conflict(cls, conflict_data: Dict[str, Any]) -> Dict[str, Any]:
        return _DEFAULT_ADAPTER.log_conflict(conflict_data)

    @classmethod
    def get_conflict_logs(cls) -> List[Dict[str, Any]]:
        return _DEFAULT_ADAPTER.get_conflict_logs()

    @classmethod
    def get_calendar_events(cls, region: Optional[str] = None) -> List[Dict[str, Any]]:
        return _DEFAULT_ADAPTER.get_calendar_events(region)

    @classmethod
    def save_calendar_event(cls, event_data: Dict[str, Any]) -> Dict[str, Any]:
        return _DEFAULT_ADAPTER.save_calendar_event(event_data)

    @classmethod
    def get_store_profile(cls) -> Dict[str, Any]:
        return _DEFAULT_ADAPTER.get_store_profile()

    @classmethod
    def save_store_profile(cls, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        return _DEFAULT_ADAPTER.save_store_profile(profile_data)

    @classmethod
    def get_storage_status(cls) -> Dict[str, Any]:
        return _DEFAULT_ADAPTER.get_status()
