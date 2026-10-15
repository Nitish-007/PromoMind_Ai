import os
import re
import sys
import json
import time
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)

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
from forecasting import OpenSourceForecastingEngine, InvestmentROIEngine

logger = logging.getLogger("PromoMind.Storage")

try:
    from google.cloud import firestore
    from google.oauth2 import service_account
    from google.auth.exceptions import DefaultCredentialsError
    from google.api_core.exceptions import GoogleAPICallError
    FIRESTORE_AVAILABLE = True
except Exception as e:
    firestore = None
    service_account = None
    FIRESTORE_AVAILABLE = False
    logger.info(f"Google Cloud Firestore driver not active: {e}")


DEFAULT_CUSTOMER_LIST: List[Dict[str, Any]] = [
    {"name": "Ananya Rao", "phone": "+91 98451 22334", "segment": "Festive Gifting / High AOV", "preferred_channel": "WhatsApp"},
    {"name": "Vikram Patel", "phone": "+91 98452 33445", "segment": "Weekly Pantry Staples", "preferred_channel": "WhatsApp"},
    {"name": "Meera Iyer", "phone": "+91 98453 44556", "segment": "Dairy & Sweet Making", "preferred_channel": "WhatsApp"},
    {"name": "Karthik Reddy", "phone": "+91 98454 55667", "segment": "Evening Snacks & Tea", "preferred_channel": "POS"},
    {"name": "Sunita Jain", "phone": "+91 98455 66778", "segment": "Dry Fruits & Bulk Staples", "preferred_channel": "WhatsApp"}
]

DEFAULT_STORE_PROFILE: Dict[str, Any] = {
    "store_id": "sharma_supermarket_01",
    "store_name": "Sharma Supermarket & Kirana",
    "owner_name": "Ramesh Sharma",
    "email": "ramesh@sharmamart.in",
    "phone": "+91 98450 12345",
    "gstin": "29AAAAA0000A1Z5",
    "store_type": "Supermarket",
    "store_format": "Supermarket",
    "audience_size": 1420,
    "whatsapp_audience_size": 1420,
    "region": "Karnataka & South India",
    "city": "Bengaluru",
    "country": "India",
    "locality": "Koramangala 4th Block",
    "pin_code": "560034",
    "default_min_margin_pct": 18.0,
    "total_working_capital_inr": 500000.0,
    "customer_list": DEFAULT_CUSTOMER_LIST,
    "updated_at": "2026-10-15T10:00:00Z"
}

PRESET_STORES_REGISTRY: Dict[str, Dict[str, Any]] = {
    "sharma_supermarket_01": dict(DEFAULT_STORE_PROFILE),
    "patel_fresh_mart_02": {
        "store_id": "patel_fresh_mart_02",
        "store_name": "Patel Fresh Mart & Provision Store",
        "owner_name": "Kiran Patel",
        "email": "kiran@patelfresh.in",
        "phone": "+91 98201 55667",
        "gstin": "27BBBBB1111B1Z2",
        "store_type": "Supermarket",
        "store_format": "Supermarket",
        "audience_size": 2150,
        "whatsapp_audience_size": 2150,
        "region": "Maharashtra & West India",
        "city": "Mumbai",
        "country": "India",
        "locality": "Dadar West",
        "pin_code": "400028",
        "default_min_margin_pct": 17.5,
        "total_working_capital_inr": 750000.0,
        "customer_list": DEFAULT_CUSTOMER_LIST,
        "updated_at": "2026-10-15T10:00:00Z"
    },
    "sen_bazar_03": {
        "store_id": "sen_bazar_03",
        "store_name": "Sen Family Department Store",
        "owner_name": "Subrata Sen",
        "email": "subrata@senbazar.in",
        "phone": "+91 98300 77889",
        "gstin": "19CCCCC2222C1Z8",
        "store_type": "Departmental",
        "store_format": "Departmental",
        "audience_size": 1680,
        "whatsapp_audience_size": 1680,
        "region": "West Bengal & East India",
        "city": "Kolkata",
        "country": "India",
        "locality": "Gariahat",
        "pin_code": "700019",
        "default_min_margin_pct": 16.5,
        "total_working_capital_inr": 600000.0,
        "customer_list": DEFAULT_CUSTOMER_LIST,
        "updated_at": "2026-10-15T10:00:00Z"
    }
}


def _dump_model(obj: Any) -> Dict[str, Any]:
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if hasattr(obj, "dict"):
        return obj.dict()
    return dict(obj)


def _normalize_product_key(name: str) -> str:
    """Create canonical key for deduplicating SKUs across re-uploads."""
    if not name:
        return ""
    return re.sub(r"[^a-z0-9]+", "", name.strip().lower())


def _infer_category_from_name(name: str) -> str:
    low = (name or "").lower()
    if any(w in low for w in ["ghee", "milk", "butter", "paneer", "curd", "cheese", "dairy"]):
        return "Dairy"
    if any(w in low for w in ["tea", "chai", "coffee", "juice", "drink", "soda", "beverage", "cider"]):
        return "Beverages"
    if any(w in low for w in ["almond", "cashew", "kaju", "pistachio", "pista", "raisin", "walnut", "dry fruit", "nut"]):
        return "Dry Fruits"
    if any(w in low for w in ["biscuit", "cookie", "chip", "namkeen", "bhujia", "snack", "noodle", "chocolate"]):
        return "Snacks"
    if any(w in low for w in ["sweet", "jamun", "rasgulla", "ladoo", "barfi", "mithai", "soan", "payasam"]):
        return "Sweets & Confectionery"
    if any(w in low for w in ["masala", "spice", "turmeric", "chilli", "cumin", "pepper", "cardamom"]):
        return "Spices"
    if any(w in low for w in ["diya", "deepa", "camphor", "agarbatti", "wick", "puja", "pooja", "dhoop"]):
        return "Puja & Festive"
    return "Staples & Oils"


def _pick_col(row_lower: Dict[str, str], candidates: List[str], default: Any = None) -> Any:
    for c in candidates:
        if c in row_lower and row_lower[c] is not None and str(row_lower[c]).strip() != "":
            return str(row_lower[c]).strip()
    return default


def _parse_number(val: Any, default: float = 0.0) -> float:
    if val is None:
        return default
    cleaned = re.sub(r"[^\d.-]", "", str(val))
    try:
        return float(cleaned) if cleaned else default
    except Exception:
        return default


class DualModeStorageAdapter:
    """
    Firestore-First Storage Adapter with Multi-Store Isolation, Smart CSV Normalization,
    Strict De-Duplication, and Login-Driven Regional Festival Persistence.
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

        # Per-store memory state
        self._memory_inventory: Dict[str, List[Product]] = {}
        self._memory_promotions: Dict[str, List[Dict[str, Any]]] = {}
        self._memory_calendar: Dict[str, List[Dict[str, Any]]] = {}
        self._memory_profiles: Dict[str, Dict[str, Any]] = {
            k: dict(v) for k, v in PRESET_STORES_REGISTRY.items()
        }

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

    @staticmethod
    def parse_inline_service_account(raw_val: Optional[str]) -> Optional[Dict[str, Any]]:
        if not raw_val or not isinstance(raw_val, str):
            return None

        cleaned = raw_val.strip()
        if not cleaned:
            return None

        if (cleaned.startswith("'") and cleaned.endswith("'")) or (cleaned.startswith('"') and cleaned.endswith('"')):
            cleaned = cleaned[1:-1].strip()

        try:
            data = json.loads(cleaned)
            if isinstance(data, dict) and ("type" in data or "client_email" in data or "private_key" in data):
                return data
        except Exception:
            pass

        try:
            import base64
            decoded = base64.b64decode(cleaned).decode("utf-8")
            data = json.loads(decoded)
            if isinstance(data, dict) and ("type" in data or "client_email" in data or "private_key" in data):
                return data
        except Exception:
            pass

        try:
            normalized = cleaned.replace("\\n", "\n").replace('\\"', '"').replace("\\'", "'")
            data = json.loads(normalized)
            if isinstance(data, dict) and ("type" in data or "client_email" in data or "private_key" in data):
                return data
        except Exception:
            pass

        return None

    def _init_connection(self, force_mode: Optional[str] = None):
        requested_mode = (force_mode or os.environ.get("STORAGE_MODE", "AUTO")).upper()
        if requested_mode == "LOCAL":
            self.mode = "LOCAL_FALLBACK"
            self.fallback_reason = "Manually forced to LOCAL_FALLBACK via STORAGE_MODE configuration."
            return

        if self.client is not None:
            self.mode = "CLOUD"
            self.fallback_reason = None
            self._start_realtime_sync_listener()
            return

        if not FIRESTORE_AVAILABLE:
            self.mode = "LOCAL_FALLBACK"
            self.fallback_reason = "google-cloud-firestore library is not installed in the current environment."
            return

        try:
            sa_json = os.environ.get("FIRESTORE_SA_JSON")
            parsed_sa = self.parse_inline_service_account(sa_json)
            if parsed_sa and service_account is not None:
                sa_proj = parsed_sa.get("project_id")
                if sa_proj:
                    self.project_id = sa_proj
                creds = service_account.Credentials.from_service_account_info(parsed_sa)
                self.client = firestore.Client(project=self.project_id or creds.project_id, credentials=creds)
            else:
                emulator_host = os.environ.get("FIRESTORE_EMULATOR_HOST")
                if emulator_host:
                    self.client = firestore.Client(project=self.project_id or "demo-promomind")
                elif self.project_id:
                    self.client = firestore.Client(project=self.project_id)
                else:
                    raise ValueError("No Google Cloud credentials or project configured.")

            _ = self.client.collection("stores").document(self.store_id).get(timeout=3.0)
            self.mode = "CLOUD"
            self.fallback_reason = None
            self._start_realtime_sync_listener()
        except Exception as e:
            self.mode = "LOCAL_FALLBACK"
            self.client = None
            self.fallback_reason = f"Cloud connection unavailable: {str(e)}"

    # ==========================================================================
    # Multi-Store Management
    # ==========================================================================

    def switch_store(self, store_id: str) -> Dict[str, Any]:
        clean_id = (store_id or "sharma_supermarket_01").strip().lower().replace(" ", "_")
        self.store_id = clean_id
        return self.get_store_profile()

    def list_stores(self) -> List[Dict[str, Any]]:
        stores_map: Dict[str, Dict[str, Any]] = {
            k: dict(v) for k, v in self._memory_profiles.items()
        }
        if self.mode == "CLOUD" and self.client:
            try:
                for doc in self.client.collection("stores").stream():
                    prof_doc = doc.reference.collection("store_profile").document("profile").get()
                    if prof_doc.exists:
                        p_data = prof_doc.to_dict()
                        p_data["store_id"] = doc.id
                        stores_map[doc.id] = p_data
            except Exception as e:
                logger.warning(f"Failed listing stores from Firestore: {e}")

        curr = self.get_store_profile()
        stores_map[self.store_id] = curr
        return list(stores_map.values())

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
    # 1. Inventory Collection & Smart Deduplicating CSV Ingestion
    # ==========================================================================

    def load_products(self) -> List[Product]:
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
                    self._memory_inventory[self.store_id] = products
                    self._save_local_products_cache(products)
                    return products
                else:
                    self.save_products(list(INVENTORY_DATA))
                    return list(INVENTORY_DATA)
            except Exception as e:
                logger.warning(f"Failed to read from Firestore inventory, falling back: {e}")

        if self.store_id in self._memory_inventory and self._memory_inventory[self.store_id]:
            return list(self._memory_inventory[self.store_id])

        return self._load_local_products()

    def save_products(self, products: List[Product]):
        self._memory_inventory[self.store_id] = list(products)
        if self.mode == "CLOUD" and self.client:
            try:
                batch = self.client.batch()
                coll = self._inventory_coll()
                for p in products:
                    doc_ref = coll.document(p.id)
                    batch.set(doc_ref, _dump_model(p))
                batch.commit()
            except Exception as e:
                logger.warning(f"Error persisting products to Firestore: {e}")

        self._save_local_products_cache(products)
        self.rebuild_knowledge_markdown(products)

    def add_or_update_product(self, product: Product) -> List[Product]:
        """Add or update an individual product SKU with automatic name/ID deduplication."""
        products = self.load_products()
        incoming_key = _normalize_product_key(product.name)
        idx = next(
            (
                i for i, p in enumerate(products)
                if p.id.lower() == product.id.lower() or (incoming_key and _normalize_product_key(p.name) == incoming_key)
            ),
            None
        )
        if idx is not None:
            # Preserve existing canonical ID when updating by name match
            product.id = products[idx].id
            products[idx] = product
        else:
            products.append(product)

        self._memory_inventory[self.store_id] = list(products)

        if self.mode == "CLOUD" and self.client:
            try:
                self._inventory_coll().document(product.id).set(_dump_model(product))
            except Exception as e:
                logger.warning(f"Error writing product {product.id} to Firestore: {e}")

        self._save_local_products_cache(products)
        self.rebuild_knowledge_markdown(products)
        return products

    def import_csv_data_with_stats(self, csv_content: str, replace_existing: bool = False) -> Dict[str, Any]:
        """
        Smart Multi-Format CSV Structurizer & De-Duplicating Ingestion Engine:
        1. Auto-maps arbitrary distributor/POS column headers into canonical PromoMind schema.
        2. Deduplicates by both SKU ID and normalized Product Name (re-uploading the same CSV updates in-place with zero duplicates).
        3. Extracts & deduplicates customer broadcast contacts / WhatsApp audience numbers if present in CSV.
        4. Runs Holt-Winters demand forecasting and syncs directly to Firestore (`stores/{store_id}/inventory`).
        """
        import csv
        import io

        cleaned_csv = (csv_content or "").strip()
        if not cleaned_csv:
            return {
                "imported_count": 0,
                "new_skus_added": 0,
                "existing_skus_updated": 0,
                "duplicates_prevented": 0,
                "broadcast_contacts_synced": 0,
                "columns_mapped": [],
                "markdown": self.get_knowledge_markdown()
            }

        reader = csv.DictReader(io.StringIO(cleaned_csv))
        raw_headers = reader.fieldnames or []
        products = [] if replace_existing else self.load_products()

        new_added = 0
        existing_updated = 0
        duplicates_prevented = 0
        imported = 0

        # Track customer broadcast contacts if CSV includes customer/WhatsApp columns
        profile = self.get_store_profile()
        customer_list = list(profile.get("customer_list") or DEFAULT_CUSTOMER_LIST)
        existing_phones = {re.sub(r"[^\d+]", "", c.get("phone", "")) for c in customer_list if c.get("phone")}
        broadcast_contacts_added = 0
        explicit_audience_reach = None

        for raw_row in reader:
            if not raw_row:
                continue
            row_lower = {str(k).strip().lower().replace(" ", "_"): v for k, v in raw_row.items() if k is not None}

            # Check if row has customer / broadcast contact fields
            cust_phone = _pick_col(row_lower, ["customer_phone", "whatsapp", "whatsapp_number", "mobile", "phone", "contact_phone"])
            cust_name = _pick_col(row_lower, ["customer_name", "buyer_name", "client_name", "member_name"])
            cust_seg = _pick_col(row_lower, ["customer_segment", "segment", "buyer_tier"], "Store Broadcast List")
            aud_col = _pick_col(row_lower, ["audience_size", "whatsapp_audience_size", "broadcast_reach", "subscribers"])
            if aud_col:
                parsed_aud = int(_parse_number(aud_col, 0))
                if parsed_aud > 0:
                    explicit_audience_reach = parsed_aud

            if cust_phone:
                norm_phone = re.sub(r"[^\d+]", "", cust_phone)
                if len(norm_phone) >= 8 and norm_phone not in existing_phones:
                    existing_phones.add(norm_phone)
                    customer_list.append({
                        "name": cust_name or f"Customer {len(customer_list) + 1}",
                        "phone": cust_phone,
                        "segment": cust_seg,
                        "preferred_channel": "WhatsApp"
                    })
                    broadcast_contacts_added += 1

            # Extract Product SKU fields using flexible multi-header aliases
            name = _pick_col(row_lower, [
                "name", "product_name", "product", "item_name", "item", "title",
                "sku_name", "description", "particulars", "brand_item"
            ])
            if not name:
                continue

            brand_col = _pick_col(row_lower, ["brand", "brand_name", "manufacturer", "company"])
            if brand_col and brand_col.lower() not in name.lower():
                name = f"{brand_col} {name}".strip()

            cat = _pick_col(row_lower, ["category", "cat", "department", "group", "product_category", "section"])
            if not cat:
                cat = _infer_category_from_name(name)

            raw_cost = _pick_col(row_lower, ["cost_price", "cost", "buy_price", "purchase_price", "wholesale_price", "cp", "rate", "unit_cost"])
            raw_mrp = _pick_col(row_lower, ["selling_price", "mrp", "price", "retail_price", "sp", "sale_price", "unit_price"])

            cost = _parse_number(raw_cost, 0.0)
            mrp = _parse_number(raw_mrp, 0.0)
            if cost <= 0 and mrp > 0:
                cost = round(mrp * 0.78, 1)
            elif mrp <= 0 and cost > 0:
                mrp = round(cost * 1.28, 1)
            elif cost <= 0 and mrp <= 0:
                cost, mrp = 100.0, 130.0

            if mrp <= cost:
                mrp = round(cost * 1.22, 1)

            raw_stock = _pick_col(row_lower, ["stock_quantity", "stock", "qty", "quantity", "closing_stock", "inventory", "units", "available_stock"], "50")
            stock = max(0, int(_parse_number(raw_stock, 50)))

            raw_weekly = _pick_col(row_lower, ["weekly_sales_avg", "sales_avg", "velocity", "weekly_sales", "units_sold", "sales_per_week"])
            raw_monthly = _pick_col(row_lower, ["monthly_sales", "monthly_units", "sales_30d"])
            if raw_weekly is not None:
                weekly_avg = max(1, int(_parse_number(raw_weekly, 20)))
            elif raw_monthly is not None:
                weekly_avg = max(1, int(_parse_number(raw_monthly, 80) / 4.0))
            else:
                weekly_avg = 22

            raw_expiry = _pick_col(row_lower, ["expiry_days", "expiry", "shelf_life", "days_to_expiry", "best_before_days"], "180")
            expiry = max(1, int(_parse_number(raw_expiry, 180)))

            raw_past = _pick_col(row_lower, ["past_sales_weeks", "past_sales", "history"])
            base_sales = None
            if raw_past:
                nums = [int(float(x)) for x in re.findall(r"\d+(?:\.\d+)?", str(raw_past))]
                if len(nums) >= 3:
                    base_sales = nums[:6]
            if not base_sales:
                base_sales = [
                    max(1, int(weekly_avg * 0.85)), max(1, int(weekly_avg * 0.90)),
                    max(1, int(weekly_avg * 0.95)), max(1, int(weekly_avg * 1.00)),
                    max(1, int(weekly_avg * 1.05)), max(1, weekly_avg)
                ]

            incoming_id = _pick_col(row_lower, ["product_id", "id", "sku_id", "sku", "barcode", "item_code", "code"])
            norm_name_key = _normalize_product_key(name)

            # Strict De-Duplication Lookup (match by ID OR by normalized product name)
            existing_idx = next(
                (
                    i for i, ep in enumerate(products)
                    if (incoming_id and ep.id.strip().lower() == incoming_id.strip().lower())
                    or (norm_name_key and _normalize_product_key(ep.name) == norm_name_key)
                ),
                None
            )

            if existing_idx is not None:
                sku_id = products[existing_idx].id
            else:
                if incoming_id:
                    sku_id = incoming_id.strip().upper().replace(" ", "_")
                else:
                    slug = re.sub(r"[^A-Z0-9]+", "_", name.upper()).strip("_")[:14]
                    sku_id = f"SKU_{slug}_{len(products) + 1:02d}"

            forecast = OpenSourceForecastingEngine.predict_demand_surge(base_sales, event_surge_pct=35.0)
            velocity = "FAST_MOVING" if weekly_avg >= 35 else ("SLOW_MOVING" if weekly_avg <= 15 else "MODERATE")
            days_rem = int((stock / max(1, weekly_avg)) * 7)
            verdict = "STRONG_INVEST_BUY" if forecast["expected_growth_pct"] >= 25 else ("DO_NOT_REORDER" if days_rem >= 70 else "CAUTION_CHECK_BRANDS")
            badge = "Strong Buy / Restock Now" if verdict == "STRONG_INVEST_BUY" else ("Do Not Reorder" if verdict == "DO_NOT_REORDER" else "Check Brands")
            brand_notes = _pick_col(row_lower, ["brand_comparison_insight", "brand_notes", "notes"], f"Structured & forecasted SKU in {cat}.")

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

            if existing_idx is not None:
                products[existing_idx] = p
                existing_updated += 1
                duplicates_prevented += 1
            else:
                products.append(p)
                new_added += 1
            imported += 1

        # Update broadcast customer list / audience reach if discovered in CSV
        if broadcast_contacts_added > 0 or explicit_audience_reach:
            profile["customer_list"] = customer_list
            if explicit_audience_reach:
                profile["audience_size"] = explicit_audience_reach
                profile["whatsapp_audience_size"] = explicit_audience_reach
            else:
                base_aud = int(profile.get("whatsapp_audience_size") or profile.get("audience_size") or 1420)
                profile["audience_size"] = base_aud + broadcast_contacts_added
                profile["whatsapp_audience_size"] = base_aud + broadcast_contacts_added
            self.save_store_profile(profile)

        self.save_products(products)
        return {
            "imported_count": imported,
            "new_skus_added": new_added,
            "existing_skus_updated": existing_updated,
            "duplicates_prevented": duplicates_prevented,
            "broadcast_contacts_synced": broadcast_contacts_added,
            "active_broadcast_reach": profile.get("whatsapp_audience_size") or profile.get("audience_size") or 1420,
            "columns_mapped": raw_headers,
            "markdown": self.get_knowledge_markdown()
        }

    def import_csv_data(self, csv_content: str, replace_existing: bool = False) -> Tuple[int, str]:
        stats = self.import_csv_data_with_stats(csv_content, replace_existing=replace_existing)
        return stats["imported_count"], stats["markdown"]

    def _load_local_products(self) -> List[Product]:
        if not os.path.exists(self.store_json_file):
            self._save_local_products_cache(INVENTORY_DATA)
            self._memory_inventory[self.store_id] = list(INVENTORY_DATA)
            return list(INVENTORY_DATA)
        try:
            with open(self.store_json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                prods = [Product(**item) for item in data]
                self._memory_inventory[self.store_id] = prods
                return prods
        except Exception as e:
            logger.warning(f"Could not parse local inventory: {e}. Returning INVENTORY_DATA.")
            return list(INVENTORY_DATA)

    def _save_local_products_cache(self, products: List[Product]):
        self._ensure_local_data_dir()
        data = [_dump_model(p) for p in products]
        with open(self.store_json_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    # ==========================================================================
    # 2. Promotions Collection: stores/{store_id}/promotions (Active & Scheduled)
    # ==========================================================================

    def get_promotions(self) -> List[Dict[str, Any]]:
        if self.mode == "CLOUD" and self.client:
            try:
                docs = list(self._promotions_coll().stream())
                promos = [
                    d.to_dict() for d in docs
                    if d.to_dict().get("type") != "conflict_log"
                ]
                if promos:
                    self._memory_promotions[self.store_id] = promos
                    self._save_local_promotions_cache(promos)
                    return promos
                else:
                    for offer in SCHEDULED_OFFERS:
                        self.save_promotion(offer)
                    return list(SCHEDULED_OFFERS)
            except Exception as e:
                logger.warning(f"Firestore promotions query failed: {e}. Falling back.")

        if self.store_id in self._memory_promotions and self._memory_promotions[self.store_id]:
            return list(self._memory_promotions[self.store_id])

        return self._load_local_promotions()

    def save_promotion(self, offer: Dict[str, Any]) -> Dict[str, Any]:
        """Save or upsert a promotional offer into stores/{store_id}/promotions."""
        offer_id = offer.get("id") or f"OFFER_LIVE_{int(time.time() * 1000) % 100000}"
        offer_data = dict(offer)
        offer_data["id"] = offer_id
        offer_data["type"] = "promotion"
        offer_data.setdefault("combo_id", f"COMBO_{int(offer_data.get('combo_price', 0))}")
        offer_data.setdefault("start_date", "2026-10-15")
        offer_data.setdefault("end_date", "2026-10-25")
        offer_data.setdefault("event_theme", "Active Campaign")
        offer_data.setdefault("status", "ACTIVE")
        offer_data.setdefault("channels", ["WhatsApp Broadcast", "POS Barcode", "In-Store Poster"])
        offer_data["updated_at"] = datetime.now(timezone.utc).isoformat()

        if self.mode == "CLOUD" and self.client:
            try:
                self._promotions_coll().document(offer_id).set(offer_data)
            except Exception as e:
                logger.warning(f"Failed to write promotion {offer_id} to Firestore: {e}")

        current = self.get_promotions()
        existing_idx = next(
            (
                i for i, o in enumerate(current)
                if o.get("id") == offer_id or (o.get("title") == offer_data.get("title") and o.get("start_date") == offer_data.get("start_date"))
            ),
            None
        )
        if existing_idx is not None:
            offer_data["id"] = current[existing_idx].get("id", offer_id)
            current[existing_idx] = offer_data
        else:
            current.insert(0, offer_data)
        self._memory_promotions[self.store_id] = current
        self._save_local_promotions_cache(current)
        return offer_data

    def update_promotion(self, offer_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update status, dates, or pricing of an existing offer in stores/{store_id}/promotions."""
        current = self.get_promotions()
        idx = next((i for i, o in enumerate(current) if o.get("id") == offer_id), None)
        if idx is None:
            return None

        updated = dict(current[idx])
        for k, v in updates.items():
            if v is not None:
                updated[k] = v
        updated["updated_at"] = datetime.now(timezone.utc).isoformat()
        current[idx] = updated

        if self.mode == "CLOUD" and self.client:
            try:
                self._promotions_coll().document(offer_id).set(updated)
            except Exception as e:
                logger.warning(f"Failed to update promotion {offer_id} in Firestore: {e}")

        self._memory_promotions[self.store_id] = current
        self._save_local_promotions_cache(current)
        return updated

    def delete_promotion(self, offer_id: str) -> bool:
        """Delete an offer from stores/{store_id}/promotions."""
        current = self.get_promotions()
        new_list = [o for o in current if o.get("id") != offer_id]
        if len(new_list) == len(current):
            return False

        if self.mode == "CLOUD" and self.client:
            try:
                self._promotions_coll().document(offer_id).delete()
            except Exception as e:
                logger.warning(f"Failed to delete promotion {offer_id} from Firestore: {e}")

        self._memory_promotions[self.store_id] = new_list
        self._save_local_promotions_cache(new_list)
        return True

    def log_conflict(self, conflict_data: Dict[str, Any]) -> Dict[str, Any]:
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
            return list(SCHEDULED_OFFERS)
        try:
            with open(self.promotions_json_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return list(SCHEDULED_OFFERS)

    def _save_local_promotions_cache(self, promos: List[Dict[str, Any]]):
        self._ensure_local_data_dir()
        with open(self.promotions_json_file, "w", encoding="utf-8") as f:
            json.dump(promos, f, indent=2, ensure_ascii=False)

    # ==========================================================================
    # 3. Calendar Events Collection: stores/{store_id}/calendar_events
    # ==========================================================================

    def get_calendar_events(self, region: Optional[str] = None) -> List[Dict[str, Any]]:
        events = []
        if self.mode == "CLOUD" and self.client:
            try:
                docs = list(self._calendar_coll().stream())
                if docs:
                    events = [d.to_dict() for d in docs]
                    self._memory_calendar[self.store_id] = events
                else:
                    for ev in REGIONAL_FESTIVAL_CALENDAR:
                        self.save_calendar_event(ev)
                    events = list(REGIONAL_FESTIVAL_CALENDAR)
            except Exception as e:
                logger.warning(f"Error fetching calendar from Firestore: {e}")

        if not events and self.store_id in self._memory_calendar:
            events = list(self._memory_calendar[self.store_id])

        if not events:
            events = self._load_local_calendar()

        if region:
            reg_key = region.lower().split("&")[0].split(",")[0].strip()
            filtered = [e for e in events if reg_key in e.get("region", "").lower()]
            if filtered:
                return filtered
        return events

    def save_calendar_events_batch(self, events_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Persist a full batch of regional festivals for the current store into stores/{store_id}/calendar_events."""
        now_iso = datetime.now(timezone.utc).isoformat()
        cleaned_list = []
        for ev in events_list:
            d = _dump_model(ev) if not isinstance(ev, dict) else dict(ev)
            d["id"] = d.get("id") or f"EVT_{int(time.time() * 1000)}"
            d["synced_at"] = d.get("synced_at") or now_iso
            cleaned_list.append(d)

        self._memory_calendar[self.store_id] = cleaned_list

        if self.mode == "CLOUD" and self.client:
            try:
                batch = self.client.batch()
                coll = self._calendar_coll()
                for d in cleaned_list:
                    batch.set(coll.document(d["id"]), d)
                batch.commit()
            except Exception as e:
                logger.warning(f"Error writing festival batch to Firestore: {e}")

        self._save_local_calendar_cache(cleaned_list)
        return cleaned_list

    def save_calendar_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        event_id = event_data.get("id") or f"EVT_{int(time.time())}"
        data = dict(event_data)
        data["id"] = event_id
        data.setdefault("date_window", "Oct 2026")
        data.setdefault("status", "UPCOMING")
        data.setdefault("key_items", [])
        data.setdefault("demand_lift_pct", 30.0)
        data.setdefault("icon", "")
        data.setdefault("description", "")
        data["synced_at"] = datetime.now(timezone.utc).isoformat()

        if self.mode == "CLOUD" and self.client:
            try:
                self._calendar_coll().document(event_id).set(data)
            except Exception as e:
                logger.warning(f"Error writing calendar event to Firestore: {e}")

        current = self._memory_calendar.get(self.store_id) or self._load_local_calendar()
        idx = next((i for i, ev in enumerate(current) if ev.get("id") == event_id), None)
        if idx is not None:
            current[idx] = data
        else:
            current.append(data)
        self._memory_calendar[self.store_id] = current
        self._save_local_calendar_cache(current)
        return data

    def _load_local_calendar(self) -> List[Dict[str, Any]]:
        if not os.path.exists(self.calendar_json_file):
            self._save_local_calendar_cache(REGIONAL_FESTIVAL_CALENDAR)
            return list(REGIONAL_FESTIVAL_CALENDAR)
        try:
            with open(self.calendar_json_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return list(REGIONAL_FESTIVAL_CALENDAR)

    def _save_local_calendar_cache(self, events: List[Dict[str, Any]]):
        self._ensure_local_data_dir()
        with open(self.calendar_json_file, "w", encoding="utf-8") as f:
            json.dump(events, f, indent=2, ensure_ascii=False)

    # ==========================================================================
    # 4. Store Profile Collection: stores/{store_id}/store_profile
    # ==========================================================================

    def get_store_profile(self) -> Dict[str, Any]:
        if self.mode == "CLOUD" and self.client:
            try:
                doc = self._profile_coll().document("profile").get()
                if doc.exists:
                    profile = doc.to_dict()
                    profile["store_id"] = self.store_id
                    self._memory_profiles[self.store_id] = profile
                    self._save_local_profile_cache(profile)
                    return profile
                else:
                    seed = dict(self._memory_profiles.get(self.store_id, DEFAULT_STORE_PROFILE))
                    seed["store_id"] = self.store_id
                    self.save_store_profile(seed)
                    return seed
            except Exception as e:
                logger.warning(f"Error reading store profile from Firestore: {e}")

        if self.store_id in self._memory_profiles:
            return dict(self._memory_profiles[self.store_id])

        return self._load_local_profile()

    def save_store_profile(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        data = dict(profile_data)
        target_store_id = data.get("store_id") or self.store_id
        self.store_id = target_store_id
        data["store_id"] = self.store_id
        data["updated_at"] = datetime.now(timezone.utc).isoformat()
        if "customer_list" not in data or not data["customer_list"]:
            data["customer_list"] = DEFAULT_CUSTOMER_LIST
        if "audience_size" in data and not data.get("whatsapp_audience_size"):
            data["whatsapp_audience_size"] = data["audience_size"]
        elif "whatsapp_audience_size" in data and not data.get("audience_size"):
            data["audience_size"] = data["whatsapp_audience_size"]

        self._memory_profiles[self.store_id] = dict(data)

        if self.mode == "CLOUD" and self.client:
            try:
                self._profile_coll().document("profile").set(data)
            except Exception as e:
                logger.warning(f"Failed to write store profile to Firestore: {e}")

        self._save_local_profile_cache(data)
        try:
            self.rebuild_knowledge_markdown()
        except Exception as e:
            logger.warning(f"Failed to recompile knowledge markdown on profile save: {e}")
        return data

    def _load_local_profile(self) -> Dict[str, Any]:
        if not os.path.exists(self.profile_json_file):
            self._save_local_profile_cache(DEFAULT_STORE_PROFILE)
            return dict(DEFAULT_STORE_PROFILE)
        try:
            with open(self.profile_json_file, "r", encoding="utf-8") as f:
                prof = json.load(f)
                self._memory_profiles[self.store_id] = prof
                return prof
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
        self._ensure_local_data_dir()
        if products is None:
            products = self.load_products()

        prof_dict = self.get_store_profile()
        profile = StoreProfile(**prof_dict)
        roi_stats = InvestmentROIEngine.compute_store_roi(
            products,
            store_capital_budget=profile.total_working_capital_inr or 500000.0
        )

        lines = [
            "# 🏪 PromoMind AI — Retail Store Knowledge & Catalog Base",
            f"> *Store Name*: **{profile.store_name}** | *Owner*: **{profile.owner_name}**",
            f"> *Cultural Region*: **{profile.region}** ({profile.city}, {profile.pin_code})",
            f"> *Store Format*: **{profile.store_format}** | *WhatsApp Broadcast Reach*: **{profile.whatsapp_audience_size} Families**",
            f"> *Working Capital Invested*: **₹{int(roi_stats['total_inventory_invested_inr']):,}** | *Target Net Margin*: **{profile.default_min_margin_pct}%**",
            f"> *Storage Mode: **{self.mode}** | Synchronized: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}*",
            "> *Auto-generated from retail inventory data & open-source demand forecasting engine.*\n",
            "---",
            "## 💰 1. Working Capital Investment & Return on Capital (ROI) Intelligence\n",
            f"- **Total Inventory Capital Invested**: ₹{int(roi_stats['total_inventory_invested_inr']):,}",
            f"- **Projected 30-Day Sales Turnover**: ₹{int(roi_stats['projected_sales_revenue_inr']):,}",
            f"- **Projected Net Dukan Profit**: ₹{int(roi_stats['projected_gross_profit_inr']):,} (**{roi_stats['overall_roi_pct']}% Net Return on Capital**)",
            f"- **Dead Working Capital Trapped in Slow Movers**: ₹{int(roi_stats['dead_capital_at_risk_inr']):,} ({roi_stats['slow_mover_skus_count']} at-risk SKUs)",
            f"- **Capital Unlocked via Smart Promo Bundles**: **₹{int(roi_stats['unlocked_capital_from_promos_inr']):,}** cash freed within 12 days (+₹{int(roi_stats['net_promo_profit_boost_inr']):,} net promo profit)",
            f"- **Cash Turnover Velocity**: Every **{roi_stats['capital_turnover_days']} days**",
            f"- **System Capital Status**: {roi_stats['recommendation_action']}\n",
            "---",
            "## 📦 2. Tracked SKU Inventory & Predictive Velocity Status\n",
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

        md_content = "\n".join(lines)

        with open(self.knowledge_md_file, "w", encoding="utf-8") as f:
            f.write(md_content)

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
        if self.mode == "CLOUD" and self.client:
            try:
                doc = self._catalog_coll().document("current").get()
                if doc.exists:
                    data = doc.to_dict()
                    md = data.get("markdown", "")
                    if md:
                        with open(self.knowledge_md_file, "w", encoding="utf-8") as f:
                            f.write(md)
                        return md
            except Exception as e:
                logger.warning(f"Failed to fetch knowledge catalog from Firestore: {e}")

        if not os.path.exists(self.knowledge_md_file):
            return self.rebuild_knowledge_markdown()

        with open(self.knowledge_md_file, "r", encoding="utf-8") as f:
            return f.read()

    def _start_realtime_sync_listener(self):
        if not self.client or self.mode != "CLOUD":
            return

        try:
            def on_inventory_snapshot(col_snapshot, changes, read_time):
                try:
                    updated_prods = []
                    for doc in col_snapshot:
                        d = doc.to_dict()
                        if "id" not in d:
                            d["id"] = doc.id
                        updated_prods.append(Product(**d))
                    if updated_prods:
                        self._memory_inventory[self.store_id] = updated_prods
                        self._save_local_products_cache(updated_prods)
                        self.rebuild_knowledge_markdown(updated_prods)
                except Exception as ex:
                    logger.warning(f"Error during real-time inventory sync: {ex}")

            self._listener_unsubscribe = self._inventory_coll().on_snapshot(on_inventory_snapshot)
        except Exception:
            pass

    def close(self):
        if self._listener_unsubscribe:
            try:
                self._listener_unsubscribe.unsubscribe()
            except Exception:
                pass
            self._listener_unsubscribe = None

    def get_status(self) -> Dict[str, Any]:
        gemini_configured = bool(
            os.environ.get("GEMINI_API_KEY")
            or os.environ.get("FIRESTORE_SA_JSON")
            or os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        )
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
            },
            "gemini_live_active": gemini_configured
        }


_DEFAULT_ADAPTER = DualModeStorageAdapter()


class StoreDataManager:
    @classmethod
    def get_adapter(cls) -> DualModeStorageAdapter:
        return _DEFAULT_ADAPTER

    @classmethod
    def set_adapter(cls, adapter: DualModeStorageAdapter):
        global _DEFAULT_ADAPTER
        _DEFAULT_ADAPTER = adapter

    @classmethod
    def switch_store(cls, store_id: str) -> Dict[str, Any]:
        return _DEFAULT_ADAPTER.switch_store(store_id)

    @classmethod
    def list_stores(cls) -> List[Dict[str, Any]]:
        return _DEFAULT_ADAPTER.list_stores()

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
    def import_csv_data(cls, csv_content: str, replace_existing: bool = False) -> Tuple[int, str]:
        return _DEFAULT_ADAPTER.import_csv_data(csv_content, replace_existing=replace_existing)

    @classmethod
    def import_csv_data_with_stats(cls, csv_content: str, replace_existing: bool = False) -> Dict[str, Any]:
        return _DEFAULT_ADAPTER.import_csv_data_with_stats(csv_content, replace_existing=replace_existing)

    @classmethod
    def rebuild_knowledge_markdown(cls, products: Optional[List[Product]] = None) -> str:
        return _DEFAULT_ADAPTER.rebuild_knowledge_markdown(products)

    @classmethod
    def get_knowledge_markdown(cls) -> str:
        return _DEFAULT_ADAPTER.get_knowledge_markdown()

    @classmethod
    def get_promotions(cls) -> List[Dict[str, Any]]:
        return _DEFAULT_ADAPTER.get_promotions()

    @classmethod
    def save_promotion(cls, offer: Dict[str, Any]) -> Dict[str, Any]:
        return _DEFAULT_ADAPTER.save_promotion(offer)

    @classmethod
    def update_promotion(cls, offer_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return _DEFAULT_ADAPTER.update_promotion(offer_id, updates)

    @classmethod
    def delete_promotion(cls, offer_id: str) -> bool:
        return _DEFAULT_ADAPTER.delete_promotion(offer_id)

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
    def save_calendar_events_batch(cls, events_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return _DEFAULT_ADAPTER.save_calendar_events_batch(events_list)

    @classmethod
    def get_store_profile(cls) -> Dict[str, Any]:
        return _DEFAULT_ADAPTER.get_store_profile()

    @classmethod
    def save_store_profile(cls, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        return _DEFAULT_ADAPTER.save_store_profile(profile_data)

    @classmethod
    def get_storage_status(cls) -> Dict[str, Any]:
        return _DEFAULT_ADAPTER.get_status()

    @classmethod
    def load_profile(cls) -> StoreProfile:
        prof_dict = _DEFAULT_ADAPTER.get_store_profile()
        return StoreProfile(**prof_dict)

    @classmethod
    def save_profile(cls, profile: StoreProfile) -> StoreProfile:
        saved_dict = _DEFAULT_ADAPTER.save_store_profile(_dump_model(profile))
        return StoreProfile(**saved_dict)

    @classmethod
    def upsert_product(cls, product: Product) -> List[Product]:
        return _DEFAULT_ADAPTER.add_or_update_product(product)

    @classmethod
    def get_dukan_capital_roi(cls, min_margin_pct: float = 16.0) -> Dict[str, Any]:
        products = cls.load_products()
        prof = cls.load_profile()
        budget = prof.total_working_capital_inr if hasattr(prof, "total_working_capital_inr") and prof.total_working_capital_inr else 500000.0
        return InvestmentROIEngine.compute_store_roi(products, store_capital_budget=budget)
