# PromoMind AI — Setup, Usage & Google Cloud Integration Guide

> **Intelligent Retail Demand Forecasting, Multi-Brand Curves & Conflict-Aware Promotion Engine**  
> *Targeted for Independent Retailers, Supermarkets, and Local Commerce Stores.*

---

## 📌 Table of Contents
1. [System Overview & Architecture](#-system-overview--architecture)
2. [Prerequisites & Local Environment Setup](#-prerequisites--local-environment-setup)
3. [How to Use the Application (Screen-by-Screen Guide)](#-how-to-use-the-application-screen-by-screen-guide)
4. [Current Verification State (What Has Been Tested)](#-current-verification-state-what-has-been-tested)
5. [Next Step: Google Cloud Platform (GCP) Integration Blueprint](#-next-step-google-cloud-platform-gcp-integration-blueprint)
   - [Phase 1: Google Cloud Project & IAM Setup](#step-1-google-cloud-project--iam-setup)
   - [Phase 2: Vertex AI / Gemini 1.5 Pro Agent Migration](#step-2-vertex-ai--gemini-15-pro-agent-migration)
   - [Phase 3: Serverless Deployment to Google Cloud Run](#step-3-serverless-deployment-to-google-cloud-run)
   - [Phase 4: Cloud Storage (GCS) Data Lake & Knowledge Sync](#step-4-cloud-storage-gcs-data-lake--knowledge-sync)
   - [Phase 5: Secret Manager & BigQuery Telemetry Pipeline](#step-5-secret-manager--bigquery-telemetry-pipeline)
6. [Troubleshooting & Verification Commands](#-troubleshooting--verification-commands)

---

## 🏗️ System Overview & Architecture

PromoMind AI bridges the technology divide between independent retailers (Local Marts/Supermarkets) and modern algorithmic quick-commerce giants (Blinkit, Zepto, Instamart). It provides:

- **Open-Source Demand Forecasting:** Mathematical Holt-Winters Double Exponential Smoothing predicting weekly sales velocity without heavy cloud compute dependencies.
- **Multi-Brand Comparison Curves:** Direct side-by-side comparison of competing brands (e.g., Amul vs Nandini vs Mother Dairy) on the exact same sales axis.
- **Apriori Co-Purchase Smart-Pairing:** Association rule mining ($P(B|A)$, Support, and Lift) that pairs high-velocity anchors with high-margin or slow-moving stock.
- **Regional Festive Nuances:** Captures hyper-local seasonal demand spikes (e.g., Deepavali requiring Deepas/Diyas & Cow Ghee vs. minimal baseline demand on normal days).
- **Margin Safeguard & Conflict Prevention:** Automatically detects overlapping promotions on the same SKU to prevent margin cannibalization.
- **AI Knowledge Catalog Sync:** Automatically compiles retailer CSV data into structured `store_knowledge.md` for AI agent grounding.

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           Retailer Client Layer                                 │
│  React-Native Inspired Web App: Inventory | Promos | Calendar | CSV | Profile  │
└────────────────────────────────────────┬────────────────────────────────────────┘
                                         │ REST APIs (FastAPI)
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                       PromoMind AI Core Orchestration                           │
│  ┌────────────────────────┐  ┌───────────────────────┐  ┌────────────────────┐ │
│  │ Holt-Winters Time-     │  │ Apriori Co-Purchase   │  │ Offer Conflict     │ │
│  │ Series Engine          │  │ Association Mining    │  │ Detection Engine   │ │
│  └────────────────────────┘  └───────────────────────┘  └────────────────────┘ │
│  ┌────────────────────────┐  ┌───────────────────────┐  ┌────────────────────┐ │
│  │ Regional Calendar      │  │ Pricing & Margin      │  │ Gemini Copywriting │ │
│  │ Intelligence Engine    │  │ Safeguard Engine      │  │ Agent (Flash/Pro)  │ │
│  └────────────────────────┘  └───────────────────────┘  └────────────────────┘ │
└────────────────────────────────────────┬────────────────────────────────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         Persistence & Knowledge Store                           │
│     • data/inventory_store.json (Dynamic SKU Records & Historical Curves)       │
│     • data/store_knowledge.md   (Grounding Catalog for Multi-Agent Reasoning)   │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 💻 Prerequisites & Local Environment Setup

### 1. System Requirements
- **Python:** 3.10 or higher (Python 3.11 / 3.12 recommended)
- **Node.js:** 18.17 or higher (Node 20+ recommended)
- **Git:** Version 2.30+ installed
- **Operating System:** Windows 10/11, macOS, or Linux
- **Web Browser:** Modern browser (Chrome, Edge, Firefox, Safari)

### 2. Backend Setup (FastAPI)

```bash
# 1. Clone repository
git clone https://github.com/Nitish-007/PromoMind_Ai.git
cd promomind_ai

# 2. Create a virtual environment
python -m venv venv

# 3. Activate the virtual environment
# On Windows PowerShell:
.\venv\Scripts\Activate.ps1
# On Linux / macOS:
source venv/bin/activate

# 4. Install backend dependencies
pip install -r requirements.txt

# 5. Configure environment variables (.env)
# Provide your Google Cloud Service Account JSON and credentials:
# FIRESTORE_SA_JSON='{"type":"service_account","project_id":"your-project",...}'
# GEMINI_API_KEY=AIzaSy... (optional)

# 6. Start the FastAPI backend server
python backend/main.py
```

The FastAPI backend will start on: 👉 **`http://127.0.0.1:8080`**

### 3. Frontend Setup (Next.js 16 & Tailwind CSS v4)

In a separate terminal:

```bash
# 1. Navigate into frontend directory
cd frontend

# 2. Install Node dependencies
npm install

# 3. Configure frontend environment (.env.local)
echo "NEXT_PUBLIC_API_URL=http://127.0.0.1:8080" > .env.local

# 4. Start Next.js development server
npm run dev
```

The modern web application will launch on: 👉 **`http://localhost:3000`**

---

## 📱 How to Use the Application (Screen-by-Screen Guide)

The application provides dedicated interactive modules:

### 1. 📦 Stock & Inventory Profile (`InventoryScreen`)
1. **Explore Inventory Metrics:** Review Total SKUs, Inventory Valuation, High-Velocity Anchors, and Stockout Warnings at a glance.
2. **Search & Filter:** Search by SKU name, SKU ID, or category pill (Dairy, Beverages, Snacks, Staples, Dry Fruits, Puja).
3. **Inspect Margin & Velocity:** Check unit cost price, selling MRP, profit margin %, and average weekly sales.
4. **View Multi-Brand Sales Curves:**
   - Click the **"📊 Brand Curves"** button on any product (e.g. Pure Cow Ghee or Premium Tea).
   - An interactive drawer opens rendering a **Multi-Brand Comparative SVG Chart** (e.g., Amul vs Nandini vs Mother Dairy).
   - Inspect historical 8-week sales curves (solid) and 4-week Holt-Winters festive forecasts (dashed).
5. **Interactive "What-If" ROI Simulator:** Adjust discount depth % and expected volume lift % to simulate resulting net profit and cash velocity acceleration in real time.

### 2. 🤖 Dynamic AI Retail Sales Copilot (`CopilotScreen`)
1. **100% Dynamic Conversational Reasoning:** Chat with the retail copilot powered by Google Gemini 2.5 Flash Lite on Vertex AI.
2. **Inventory-Grounded Analysis:** Automatically detects slow-moving items, calculates dead capital at risk, and designs clearance combos.
3. **Margin-Protected Optimization:** Enforces your target net margin floor (e.g., minimum 22%) without sacrificing profitability.
4. **Cashier Checkout Script:** Auto-generates a 10-second verbal pitch for checkout staff in local vernacular.
5. **Collateral Studio:** Instantly preview and format WhatsApp customer broadcasts and print-ready high-contrast shelf posters.

### 3. 📅 Regional Festival Calendar & Worldwide AI Discovery (`CalendarScreen`)
1. **Regional Demographics Selector:** Choose regions across India (*Karnataka & South India*, *Maharashtra*, *Delhi-NCR*, *West Bengal*) or international destinations (*Australia*, *Spain*, *Japan*, *UK*, *US*).
2. **Live Vertex AI Discovery:** Click **"🔍 Live AI Search"** to query Vertex AI for upcoming festivals in real time.
3. **Transparent Source Badges:** Every festival card displays whether data came from `LIVE_VERTEX_SA_API` or `HYBRID_REGIONAL_SYNTHESIS`.
4. **Three-Horizon Planning Deadlines:**
   - **T-14 Days:** Advance procurement wholesale alerts before wholesale distributor price hikes.
   - **T-7 Days:** Early-bird WhatsApp broadcast hampers and pre-orders.
   - **T+2 Days:** Mandatory markdown window to liquidate leftover items at cost price.

### 4. 📁 Data Import & AI Knowledge Sync (`UploadScreen`)
1. **Smart POS CSV Intake:** Upload arbitrary POS formats; automatic column detection extracts Item Name, Buy Rate, Retail Price, and Stock.
2. **Intelligent Deduplication:** Re-uploading CSV updates existing SKU stock levels without creating duplicate items.
3. **Auto-Recompiled Grounding:** Automatically synchronizes and compiles `store_knowledge.md` for live Gemini context.
2. **Sample CSV:** Click "Download Sample CSV Template" to inspect the required columns (`product_id, name, category, brand, stock_quantity, cost_price, selling_price, past_sales_weeks`).
3. **Automatic Forecast & Parse:** Click "Process & Forecast". PromoMind AI updates product records, runs Holt-Winters smoothing, and updates `data/inventory_store.json`.
4. **Live Markdown Catalog Sync (`data/store_knowledge.md`):** Inspect the live rendered AI Knowledge Base. AI agents query this structured Markdown file for real stock grounding during prompt execution.

### Screen 5: 🏪 Store Profile & Regional Settings (`screen-profile`)
1. **Store Metadata:** Configure Store Name, Owner Name, WhatsApp Business Number, GSTIN, and Store Format.
2. **Cultural Region:** Select store location to customize festival rules and ticker notifications.
3. **Theme Customization:** Toggle between Google Material Light (Clean White) and Modern Dark Slate. Preferences persist across sessions via `localStorage`.

---

## 🧪 Current Verification State (What Has Been Tested)

To date, the core mathematical, agentic, and interface modules have been verified and validated locally:

| Capability / Module | Current Testing Status | Implementation Details |
|---|---|---|
| **App-Style Navigation** | ✅ Tested & Operational | 5 dedicated screens with smooth state switching and mobile bottom navigation. |
| **Holt-Winters Demand Forecasting** | ✅ Tested & Operational | Open-source double exponential smoothing ($L_t$, $T_t$) in `backend/forecasting.py` predicting 4-week sales surges. |
| **Multi-Brand Comparative Curves** | ✅ Tested & Operational | SVG multi-line charts rendering Amul, Nandini, and Mother Dairy on the exact same axis with hover data points. |
| **Apriori Co-Purchase Pairing** | ✅ Tested & Operational | Market basket probability engine computing $P(B|A)$, Support, and Lift metrics. |
| **Regional Festive Calendar** | ✅ Tested & Operational | Hyper-local calendar tracking Deepavali (Deepas/Ghee), Ayudha Puja (Ash Gourd), and Karthika Deepotsava. |
| **Offer Conflict Prevention** | ✅ Tested & Operational | Validation endpoint (`/api/offers/check-conflict`) flagging overlapping campaigns and margin cannibalization. |
| **CSV-to-Markdown Sync** | ✅ Tested & Operational | File uploader parsing CSVs and compiling structured `data/store_knowledge.md` for AI grounding. |
| **Local Mock Data Fallback** | ✅ Tested & Operational | Operates seamlessly offline with realistic retail and supermarket inventory datasets. |

---

## ☁️ Next Step: Google Cloud Platform (GCP) Integration Blueprint

The primary next milestone is to transition from local testing and mock fallback agents into a production-grade **Google Cloud architecture**. Follow this implementation roadmap:

```
                               ┌──────────────────────────────────────────────────────────┐
                               │                    Google Cloud Run                      │
                               │  Containerized FastAPI Server (Serverless, Auto-Scaling) │
                               └──────────┬─────────────────────────────┬─────────────────┘
                                          │                             │
                     ┌────────────────────┴──────────┐       ┌──────────┴─────────────────────┐
                     │                               │       │                                │
                     ▼                               ▼       ▼                                ▼
       ┌───────────────────────────┐   ┌───────────────────────────┐   ┌───────────────────────────┐
       │   Google Cloud Storage    │   │      Vertex AI Gemini     │   │   Secret Manager / SQL    │
       │  (Multi-Tenant CSV Data   │   │  (Gemini 1.5 Pro Live     │   │  (API Credentials & Cloud │
       │  Lake & Markdown Vault)   │   │  Multi-Agent Reasoning)   │   │  SQL Transaction Logs)    │
       └───────────────────────────┘   └───────────────────────────┘   └───────────────────────────┘
```

---

### Step 1: Google Cloud Project & IAM Setup

1. **Create / Select GCP Project:**
   ```bash
   gcloud projects create promomind-ai-prod --name="PromoMind AI"
   gcloud config set project promomind-ai-prod
   ```

2. **Enable Required Google Cloud APIs:**
   ```bash
   gcloud services enable \
     run.googleapis.com \
     artifactregistry.googleapis.com \
     aiplatform.googleapis.com \
     firestore.googleapis.com \
     storage.googleapis.com \
     secretmanager.googleapis.com \
     cloudbuild.googleapis.com
   ```

3. **Configure Service Account & Permissions:**
   ```bash
   # Create a runtime service account
   gcloud iam service-accounts create promomind-sa \
     --description="Runtime Service Account for PromoMind AI" \
     --display-name="PromoMind-SA"

   # Grant Vertex AI User, Firestore User, and Cloud Storage Object Admin
   gcloud projects add-iam-policy-binding promomind-ai-prod \
     --member="serviceAccount:promomind-sa@promomind-ai-prod.iam.gserviceaccount.com" \
     --role="roles/aiplatform.user"

   gcloud projects add-iam-policy-binding promomind-ai-prod \
     --member="serviceAccount:promomind-sa@promomind-ai-prod.iam.gserviceaccount.com" \
     --role="roles/datastore.user"

   gcloud projects add-iam-policy-binding promomind-ai-prod \
     --member="serviceAccount:promomind-sa@promomind-ai-prod.iam.gserviceaccount.com" \
     --role="roles/storage.objectAdmin"
   ```

---

### Step 2: Vertex AI / Gemini 1.5 Pro Agent Migration

Replace heuristic fallback copy with live **Vertex AI Gemini 1.5 Pro** multi-agent reasoning:

1. **Install Google GenAI SDK:**
   ```bash
   pip install google-genai google-cloud-aiplatform
   ```

2. **Update `backend/agents.py` to use Vertex AI:**
   ```python
   import os
   from google import genai
   from google.genai import types

   # Initialize Google GenAI client (Vertex AI mode in Google Cloud)
   client = genai.Client(
       vertexai=True,
       project=os.environ.get("GCP_PROJECT_ID", "promomind-ai-prod"),
       location=os.environ.get("GCP_REGION", "asia-south1")
   )

   def generate_gemini_pitch(prompt: str, context_md: str) -> str:
       system_instruction = f"""
       You are PromoMind AI, an elite retail strategist for independent retailers and commerce merchants.
       Ground your reasoning strictly in this store catalog:
       {context_md}
       """
       response = client.models.generate_content(
           model="gemini-1.5-pro",
           contents=prompt,
           config=types.GenerateContentConfig(
               system_instruction=system_instruction,
               temperature=0.2,
               max_output_tokens=800
           )
       )
       return response.text
   ```

---

### Step 3: Serverless Deployment to Google Cloud Run

Deploy PromoMind AI as a fully managed, auto-scaling serverless web service.

1. **Verify `Dockerfile` in Repository:**
   ```dockerfile
   FROM python:3.11-slim

   WORKDIR /app

   ENV PYTHONDONTWRITEBYTECODE=1
   ENV PYTHONUNBUFFERED=1
   ENV PORT=8080

   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt

   COPY . .

   EXPOSE 8080

   CMD exec uvicorn backend.main:app --host 0.0.0.0 --port ${PORT}
   ```

2. **Create Artifact Registry Repository:**
   ```bash
   gcloud artifacts repositories create promomind-repo \
     --repository-format=docker \
     --location=asia-south1 \
     --description="Docker repository for PromoMind AI"
   ```

3. **Build and Deploy with Cloud Build & Cloud Run:**
   ```bash
   # Build container image
   gcloud builds submit --tag asia-south1-docker.pkg.dev/promomind-ai-prod/promomind-repo/promomind-app:latest

   # Deploy to Cloud Run
   gcloud run deploy promomind-app \
     --image asia-south1-docker.pkg.dev/promomind-ai-prod/promomind-repo/promomind-app:latest \
     --platform managed \
     --region asia-south1 \
     --allow-unauthenticated \
     --service-account promomind-sa@promomind-ai-prod.iam.gserviceaccount.com \
     --set-env-vars GCP_PROJECT_ID=promomind-ai-prod,GCP_REGION=asia-south1 \
     --memory 1Gi \
     --cpu 1
   ```

---

### Step 4: Google Cloud Firestore Data Architecture & Instant AI Sync

PromoMind AI integrates directly with **Google Cloud Firestore** via the **Dual-Mode Hybrid Storage Adapter** (`backend/storage.py`), replacing local data mounts with enterprise cloud document collections while preserving 100% offline fallback capabilities.

1. **Firestore Collections Hierarchy:**
   All multi-tenant store assets are organized under the `stores/{store_id}/` root:

   | Firestore Collection Path | Document Schema & Contents | Instant Sync Behavior |
   |---|---|---|
   | `stores/{store_id}/inventory` | Real-time stock levels, MRP, cost price, velocity status, past 6-week curves, and 4-week forecasts. | Automatically triggers re-compilation of AI grounding catalog on write. |
   | `stores/{store_id}/promotions` | Active & scheduled bundle campaigns, pricing tiers, and conflict logs (`type: "conflict_log"`). | Checked during `/api/offers/check-conflict` to prevent cannibalization. |
   | `stores/{store_id}/calendar_events` | Regional festive event calendar (e.g. Deepavali Deepas, Ayudha Puja). | Dynamically referenced during AI combo grounding. |
   | `stores/{store_id}/store_profile` | Store metadata, owner name, locality, GSTIN, and active customer broadcast list. | Synced with retailer app profile screen. |
   | `stores/{store_id}/knowledge_catalog` | Compiled Markdown catalog (`store_knowledge.md`) snapshot with timestamps. | Dual-persisted to Firestore doc `current` and local `data/store_knowledge.md`. |

2. **Dual-Mode Operation:**
   - **Cloud Mode:** Activated automatically when Google Cloud credentials or `GCP_PROJECT_ID` / `FIRESTORE_PROJECT_ID` are configured. All reads and writes target Firestore collections directly.
   - **Offline / Local Fallback Mode:** Operates automatically when running without internet or credentials. All data safely persists to `data/*.json` and `data/store_knowledge.md`, guaranteeing zero downtime.
   - **Real-Time Snapshot Sync:** Real-time listeners on `stores/{store_id}/inventory` detect external updates in Firestore and instantly re-compile `data/store_knowledge.md` for AI agent grounding.

3. **Verify Firestore Connection:**
   Query the new storage diagnostic endpoint:
   ```bash
   curl http://localhost:8080/api/storage/status
   ```
   Example response:
   ```json
   {
     "mode": "CLOUD",
     "firestore_connected": true,
     "store_id": "sharma_supermarket_01",
     "collections": {
       "inventory": "stores/sharma_supermarket_01/inventory",
       "promotions": "stores/sharma_supermarket_01/promotions",
       "calendar_events": "stores/sharma_supermarket_01/calendar_events",
       "store_profile": "stores/sharma_supermarket_01/store_profile",
       "knowledge_catalog": "stores/sharma_supermarket_01/knowledge_catalog"
     },
     "instant_sync_active": true
   }
   ```

---

### Step 5: Secret Manager & BigQuery Telemetry Pipeline

1. **Google Secret Manager:** Store Gemini API keys and database credentials:
   ```bash
   echo -n "AIzaSy..." | gcloud secrets create gemini-api-key --data-file=-
   ```
2. **BigQuery Telemetry (Optional):** Stream POS sales data into BigQuery to continuously train Holt-Winters trend coefficients and Apriori association matrices across thousands of retail stores.

---

## 🔍 Troubleshooting & Verification Commands

### 1. Verify Local Server Health
```powershell
python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8080/').status)"
```

### 2. Verify Multi-Brand Comparison API
```powershell
python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8080/api/inventory/PROD_GHEE_01/brand-comparison').read().decode())"
```

### 3. Verify Regional Calendar & Conflicts
```powershell
python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8080/api/calendar/events').read().decode())"
```

---

*PromoMind AI — Empowering Neighborhood Retailers with Intelligent Forecasting & Google Cloud AI.*

