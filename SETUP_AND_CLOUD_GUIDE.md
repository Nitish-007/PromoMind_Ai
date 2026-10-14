# PromoMind AI — Setup, Usage & Google Cloud Integration Guide

> **Intelligent Retail Demand Forecasting, Multi-Brand Curves & Conflict-Aware Promotion Engine**  
> *Targeted for Urban & Rural Indian Kiranas, Supermarkets, and Independent Retailers.*

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

PromoMind AI bridges the technology divide between small independent retailers (Kiranas/Supermarkets) and modern algorithmic quick-commerce giants (Blinkit, Zepto, Instamart). It provides:

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
- **Python:** 3.9 or higher (Python 3.11 / 3.12 recommended)
- **Git:** Version 2.30+ installed
- **Operating System:** Windows 10/11, macOS, or Linux
- **Web Browser:** Modern browser (Chrome, Edge, Firefox, Safari)

### 2. Clone and Setup Environment

```bash
# 1. Clone repository (or navigate to existing directory)
cd promomind_ai

# 2. Create a virtual environment
python -m venv venv

# 3. Activate the virtual environment
# On Windows PowerShell:
.\venv\Scripts\Activate.ps1
# On Linux / macOS:
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt
```

### 3. Environment Variables Configuration

Copy the example environment template:

```bash
# On Windows PowerShell:
Copy-Item .env.example .env

# On Linux / macOS:
cp .env.example .env
```

Edit `.env` if you have a Google Gemini API Key from [Google AI Studio](https://aistudio.google.com/):

```env
PORT=8080
ENVIRONMENT=development
GEMINI_API_KEY=your_gemini_api_key_here
```

*(Note: If no API key is provided, PromoMind AI gracefully falls back to deterministic rule-based algorithms with realistic retail marketing copy so you can test all features offline.)*

### 4. Start the Local Server

```bash
python backend/main.py
```

The application will launch on:
👉 **`http://localhost:8080`**

---

## 📱 How to Use the Application (Screen-by-Screen Guide)

The application is structured into 5 single-purpose app screens:

### Screen 1: 📦 Stock & Inventory Profile (`screen-inventory`)
1. **Explore Inventory Metrics:** Review Total SKUs, Inventory Valuation, High-Velocity Anchors, and Stockout Warnings at a glance.
2. **Search & Filter:** Search by SKU name, SKU ID, or category pill (Dairy, Beverages, Snacks, Staples, Dry Fruits, Puja).
3. **Inspect Margin & Velocity:** Check unit cost price, selling MRP, profit margin %, and average weekly sales.
4. **View Multi-Brand Sales Curves:**
   - Click the **"📊 Brand Curves"** button on any product (e.g. Pure Cow Ghee or Premium Tea).
   - A modal drawer opens rendering an interactive **Multi-Brand Comparative SVG Chart**.
   - Compare competing brands (e.g., **Amul Pure Cow Ghee** in Blue, **Nandini Pure Cow Ghee** in Green, and **Mother Dairy Cow Ghee** in Red) on the exact same axis.
   - Inspect the historical 8-week sales line (solid) and the 4-week Holt-Winters festive forecast surge (dashed).
   - Review the AI stocking recommendation: reveals whether to stock for brand pull or higher profit margin.

### Screen 2: ⚡ Promo Generator (`screen-promos`)
1. **Choose a Goal Preset:** Select *Diwali Festive Saver*, *Clear Slow Movers (BOGO)*, *High Margin Basket*, or *Weekend Kirana Rush*.
2. **Select Anchor Product:** Choose a core traffic driver (e.g., Pure Cow Ghee or Premium Tea).
3. **Select Smart Pair:** Review Apriori affinity recommendations calculated with probability $P(B|A)$ and Lift (e.g., Biscuits or Almonds).
4. **Set Margin Guard:** Move the Target Margin Slider (e.g. 18%).
5. **Live Conflict Pre-Check:** The system queries the conflict engine. If the SKU already has an active discount, a high-visibility warning banner alerts you before you run the campaign!
6. **Generate Plan:** Click **"✨ Generate AI Promotional Plan"**.
   - Inspect bundle economics (Combined MRP, Deal Price, Savings, Net Retailer Margin %).
   - Read the Gemini retail strategy pitch.
   - **WhatsApp Broadcast:** Preview customer message, 1-click copy text, or click "Share on WhatsApp".
   - **In-Store Poster:** Switch to the Poster tab for a printable, high-contrast store shelf banner.
7. **Schedule & Activate:** Click **"🚀 Schedule & Activate Offer in Calendar"** to push the promotion directly into active store operations.

### Screen 3: 📅 Regional Festival Calendar & Conflict Tracker (`screen-calendar`)
1. **Regional Demographics Selector:** Choose your region (*Karnataka & South India*, *Maharashtra*, *Delhi-NCR*, *West Bengal*).
2. **Regional Demand Rules:** Review hyper-local demand behaviors:
   - **Deepavali (Karnataka):** Demand for Clay Deepas/Diyas, Pure Cow Ghee, and Cotton Wicks surges by **+140%**, while returning to near zero (<5 units/month) during non-festival periods.
   - **Ayudha Puja:** Local demand surges for Ash Gourd (Kumbalakai), Puffed Rice (Pori), Lemons, and Jaggery.
3. **Active Scheduled Offers:** View all currently running promotional offers in the store with date windows and discount percentages.
4. **Interactive Conflict Sandbox:** Test any prospective SKU and proposed discount against scheduled offers. The engine validates date and SKU overlap to guarantee retail margins aren't eroded.

### Screen 4: 📁 Data Import & AI Knowledge Sync (`screen-upload`)
1. **Drag-and-Drop CSV Intake:** Drag any retail CSV file into the dropzone or click "Browse".
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
| **Local Mock Data Fallback** | ✅ Tested & Operational | Operates seamlessly offline with realistic Kirana and supermarket inventory datasets. |

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

   # Grant Vertex AI User and Cloud Storage Object Admin
   gcloud projects add-iam-policy-binding promomind-ai-prod \
     --member="serviceAccount:promomind-sa@promomind-ai-prod.iam.gserviceaccount.com" \
     --role="roles/aiplatform.user"

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
       You are PromoMind AI, an elite retail strategist for Indian Kiranas.
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

### Step 4: Cloud Storage (GCS) Data Lake & Knowledge Sync

For multi-tenant retail deployments, store uploaded distributor CSVs and compiled `store_knowledge.md` files in Google Cloud Storage:

1. **Create GCS Bucket:**
   ```bash
   gcloud storage buckets create gs://promomind-store-vault-prod \
     --location=asia-south1 \
     --uniform-bucket-level-access
   ```

2. **Connect `backend/storage.py` to GCS:**
   ```python
   from google.cloud import storage

   def upload_knowledge_to_gcs(store_id: str, markdown_content: str):
       client = storage.Client()
       bucket = client.bucket("promomind-store-vault-prod")
       blob = bucket.blob(f"tenants/{store_id}/store_knowledge.md")
       blob.upload_from_string(markdown_content, content_type="text/markdown")
   ```

---

### Step 5: Secret Manager & BigQuery Telemetry Pipeline

1. **Google Secret Manager:** Store Gemini API keys and database credentials:
   ```bash
   echo -n "AIzaSy..." | gcloud secrets create gemini-api-key --data-file=-
   ```
2. **BigQuery Telemetry (Optional):** Stream POS sales data into BigQuery to continuously train Holt-Winters trend coefficients and Apriori association matrices across thousands of Kirana stores.

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

