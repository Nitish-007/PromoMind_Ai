#!/usr/bin/env python3
"""
PromoMind AI — Google Cloud Firestore Credentials Setup & Verification Tool
Checks system environment, tests Firestore connectivity, and provides step-by-step diagnostic feedback.
"""

import os
import sys
import json

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

def print_banner():
    print("=" * 72)
    print("   🛒 PromoMind AI — Google Cloud Firestore Verification Diagnostic   ")
    print("=" * 72)

def check_package():
    print("\n[Step 1/3] Checking Python Packages...")
    try:
        import google.cloud.firestore
        import google.auth
        print("  ✅ google-cloud-firestore and google-auth are installed.")
        return True
    except ImportError as e:
        print(f"  ❌ Missing library: {e}")
        print("  💡 Fix by running: pip install google-cloud-firestore google-auth")
        return False

def check_credentials_file():
    print("\n[Step 2/3] Checking Google Cloud Credentials...")
    from firestore_service import FirestoreService
    creds_path = FirestoreService._locate_credentials()

    if creds_path:
        print(f"  ✅ Located Credentials File: {creds_path}")
        try:
            with open(creds_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            cred_type = data.get("type", "unknown")
            project_id = data.get("project_id", "unknown")
            client_email = data.get("client_email", "unknown")
            print(f"  📄 Type: {cred_type}")
            print(f"  🏷️ Project ID: {project_id}")
            print(f"  📧 Service Account: {client_email}")
            return creds_path, project_id
        except Exception as e:
            print(f"  ⚠️ Credentials file exists but failed JSON parsing: {e}")
            return creds_path, None
    else:
        print("  🟡 No service_account.json credentials file found in project.")
        print("     Paths checked:")
        print(f"      - Environment: GOOGLE_APPLICATION_CREDENTIALS")
        print(f"      - Project Root: {os.path.join(PROJECT_ROOT, 'service_account.json')}")
        print(f"      - Backend: {os.path.join(CURRENT_DIR, 'service_account.json')}")
        return None, None

def test_firestore_connection(creds_path, project_id):
    print("\n[Step 3/3] Testing Live Firestore Connection...")
    try:
        from google.cloud import firestore

        if creds_path:
            client = firestore.Client()
        else:
            client = firestore.Client(project=project_id)

        print(f"  ✅ Successfully authenticated to Google Cloud Project: '{client.project}'")
        
        # Test write & read to healthcheck document
        test_col = client.collection("system_health")
        test_doc = test_col.document("ping")
        test_doc.set({"status": "OK", "agent": "PromoMind AI", "timestamp": firestore.SERVER_TIMESTAMP})
        print("  ✅ Write test passed (wrote to 'system_health/ping')")
        
        read_back = test_doc.get()
        if read_back.exists:
            print("  ✅ Read test passed (verified live document read)")
        
        print("\n🎉 Google Cloud Firestore is 100% OPERATIONAL & READY FOR PRODUCTION!")
        return True
    except Exception as e:
        print(f"  ❌ Firestore Connection Failed: {e}")
        print("\n💡 SETUP INSTRUCTIONS TO CONNECT GOOGLE CLOUD FIRESTORE:")
        print("  1. Go to Google Cloud Console (https://console.cloud.google.com/) or Firebase Console")
        print("  2. Create or select your project (e.g., 'promomind-ai')")
        print("  3. Go to IAM & Admin -> Service Accounts -> Create Service Account")
        print("  4. Grant role: 'Cloud Datastore User' or 'Firebase Admin SDK Administrator Service Agent'")
        print("  5. Click 'Manage Keys' -> 'Add Key' -> 'Create new key' (JSON format)")
        print(f"  6. Download and save the JSON file as:")
        print(f"     '{os.path.join(PROJECT_ROOT, 'service_account.json')}'")
        print("  7. Re-run this script: python backend/verify_gcp_creds.py\n")
        print("  ℹ️ Note: PromoMind AI will continue running smoothly in resilient LOCAL JSON mode until then.")
        return False

def main():
    print_banner()
    pkg_ok = check_package()
    if not pkg_ok:
        sys.exit(1)

    creds_path, project_id = check_credentials_file()
    if creds_path:
        test_firestore_connection(creds_path, project_id)
    else:
        print("\n💡 HOW TO ENABLE GOOGLE CLOUD FIRESTORE:")
        print("  1. Create a Firebase or GCP Project: https://console.firebase.google.com/")
        print("  2. Generate a Service Account Key (JSON)")
        print(f"  3. Place it at: {os.path.join(PROJECT_ROOT, 'service_account.json')}")
        print("  4. PromoMind AI will automatically detect and sync all inventory, profiles, and offers!\n")

if __name__ == "__main__":
    main()
