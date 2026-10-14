import os
import sys
import json
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("promomind.firestore")

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)

class FirestoreService:
    """
    Enterprise-grade Dual-Mode Cloud Storage Service for PromoMind AI.
    - Cloud Mode: Synchronizes data with Google Cloud Firestore collections.
    - Fallback Mode: Local JSON persistence when GCP credentials are not yet supplied or offline.
    Zero-crash resilient architecture designed for retail POS reliability.
    """

    _client = None
    _is_connected = False
    _project_id = None
    _init_attempted = False
    _connection_message = "Not initialized"

    @classmethod
    def _locate_credentials(cls) -> Optional[str]:
        """Locates Google Service Account JSON credentials across common paths."""
        # 1. Environment variable
        env_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        if env_path and os.path.exists(env_path):
            return os.path.abspath(env_path)

        # 2. Check project root and backend directory for common names
        search_dirs = [PROJECT_ROOT, CURRENT_DIR, os.path.join(PROJECT_ROOT, "config")]
        candidate_names = [
            "service_account.json",
            "gcp_credentials.json",
            "credentials.json",
            "google_credentials.json",
            "firebase_credentials.json"
        ]

        for d in search_dirs:
            for name in candidate_names:
                full_path = os.path.join(d, name)
                if os.path.exists(full_path):
                    # Set into environment for google-auth library
                    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = full_path
                    return full_path

        # 3. Check .env file for GOOGLE_APPLICATION_CREDENTIALS
        dotenv_path = os.path.join(PROJECT_ROOT, ".env")
        if os.path.exists(dotenv_path):
            try:
                with open(dotenv_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("GOOGLE_APPLICATION_CREDENTIALS="):
                            val = line.split("=", 1)[1].strip().strip('"').strip("'")
                            if os.path.exists(val):
                                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.abspath(val)
                                return os.path.abspath(val)
            except Exception:
                pass

        return None

    @classmethod
    def initialize(cls):
        """Initializes Google Cloud Firestore client or sets up graceful fallback."""
        if cls._init_attempted:
            return

        cls._init_attempted = True
        creds_path = cls._locate_credentials()

        try:
            from google.cloud import firestore
            from google.auth.exceptions import DefaultCredentialsError

            project_env = os.environ.get("GOOGLE_CLOUD_PROJECT") or os.environ.get("GCP_PROJECT")

            if creds_path:
                logger.info(f"Connecting to Google Cloud Firestore with creds: {creds_path}")
                cls._client = firestore.Client(project=project_env)
                cls._is_connected = True
                cls._project_id = cls._client.project
                cls._connection_message = f"[ONLINE] Connected to Google Cloud Firestore (Project: {cls._project_id})"
                print(f"[PromoMind Firestore] {cls._connection_message}")
            else:
                # Try ADC (Application Default Credentials)
                try:
                    cls._client = firestore.Client(project=project_env)
                    cls._is_connected = True
                    cls._project_id = cls._client.project
                    cls._connection_message = f"[ONLINE] Connected to Google Cloud Firestore via ADC (Project: {cls._project_id})"
                    print(f"[PromoMind Firestore] {cls._connection_message}")
                except Exception as adc_err:
                    cls._is_connected = False
                    cls._connection_message = (
                        "[STANDBY] Local JSON Storage Mode (Active). To connect Google Cloud Firestore, "
                        "place 'service_account.json' in the project directory or set GOOGLE_APPLICATION_CREDENTIALS."
                    )
                    print(f"[PromoMind Firestore] {cls._connection_message}")
        except ImportError:
            cls._is_connected = False
            cls._connection_message = "[STANDBY] 'google-cloud-firestore' package not installed; running in local storage mode."
            print(f"[PromoMind Firestore] {cls._connection_message}")
        except Exception as e:
            cls._is_connected = False
            cls._connection_message = f"[STANDBY] Local Storage Mode (Firestore notice: {str(e)})"
            print(f"[PromoMind Firestore] {cls._connection_message}")

    @classmethod
    def is_connected(cls) -> bool:
        if not cls._init_attempted:
            cls.initialize()
        return cls._is_connected

    @classmethod
    def get_status(cls) -> Dict[str, Any]:
        if not cls._init_attempted:
            cls.initialize()
        creds_path = cls._locate_credentials()
        return {
            "is_connected": cls._is_connected,
            "mode": "FIRESTORE_CLOUD" if cls._is_connected else "LOCAL_JSON_FALLBACK",
            "project_id": cls._project_id or "local-store-offline",
            "credentials_found": creds_path is not None,
            "credentials_path": creds_path if creds_path else "None (place service_account.json in project root)",
            "message": cls._connection_message
        }

    # ==========================================================================
    # Firestore CRUD Operations (with Dual-Mode Fallback)
    # ==========================================================================

    @classmethod
    def save_profile(cls, profile_dict: Dict[str, Any], store_id: str = "default_store") -> bool:
        if not cls.is_connected():
            return False
        try:
            doc_ref = cls._client.collection("stores").document(store_id).collection("config").document("profile")
            doc_ref.set(profile_dict, merge=True)
            return True
        except Exception as e:
            logger.error(f"Firestore save_profile error: {e}")
            return False

    @classmethod
    def load_profile(cls, store_id: str = "default_store") -> Optional[Dict[str, Any]]:
        if not cls.is_connected():
            return None
        try:
            doc_ref = cls._client.collection("stores").document(store_id).collection("config").document("profile")
            doc = doc_ref.get()
            if doc.exists:
                return doc.to_dict()
            return None
        except Exception as e:
            logger.error(f"Firestore load_profile error: {e}")
            return None

    @classmethod
    def save_product(cls, product_dict: Dict[str, Any], store_id: str = "default_store") -> bool:
        if not cls.is_connected():
            return False
        try:
            prod_id = product_dict.get("id")
            if not prod_id:
                return False
            doc_ref = cls._client.collection("stores").document(store_id).collection("inventory").document(prod_id)
            doc_ref.set(product_dict, merge=True)
            return True
        except Exception as e:
            logger.error(f"Firestore save_product error: {e}")
            return False

    @classmethod
    def save_products_batch(cls, products: List[Dict[str, Any]], store_id: str = "default_store") -> bool:
        if not cls.is_connected():
            return False
        try:
            batch = cls._client.batch()
            inv_col = cls._client.collection("stores").document(store_id).collection("inventory")
            for prod in products:
                prod_id = prod.get("id")
                if prod_id:
                    doc_ref = inv_col.document(prod_id)
                    batch.set(doc_ref, prod, merge=True)
            batch.commit()
            return True
        except Exception as e:
            logger.error(f"Firestore save_products_batch error: {e}")
            return False

    @classmethod
    def load_products(cls, store_id: str = "default_store") -> Optional[List[Dict[str, Any]]]:
        if not cls.is_connected():
            return None
        try:
            inv_col = cls._client.collection("stores").document(store_id).collection("inventory")
            docs = inv_col.stream()
            results = [doc.to_dict() for doc in docs]
            return results if results else None
        except Exception as e:
            logger.error(f"Firestore load_products error: {e}")
            return None

    @classmethod
    def save_offer(cls, offer_dict: Dict[str, Any], store_id: str = "default_store") -> bool:
        if not cls.is_connected():
            return False
        try:
            offer_id = offer_dict.get("id") or offer_dict.get("combo_id") or "OFFER_01"
            doc_ref = cls._client.collection("stores").document(store_id).collection("offers").document(offer_id)
            doc_ref.set(offer_dict, merge=True)
            return True
        except Exception as e:
            logger.error(f"Firestore save_offer error: {e}")
            return False

    @classmethod
    def load_offers(cls, store_id: str = "default_store") -> Optional[List[Dict[str, Any]]]:
        if not cls.is_connected():
            return None
        try:
            offers_col = cls._client.collection("stores").document(store_id).collection("offers")
            docs = offers_col.stream()
            results = [doc.to_dict() for doc in docs]
            return results if results else None
        except Exception as e:
            logger.error(f"Firestore load_offers error: {e}")
            return None
