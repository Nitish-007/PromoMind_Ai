# PromoMind AI (v2.5) — Intelligent Retail Demand Forecasting & Multi-Brand Optimization Engine

> **Autonomous multi-agent demand forecasting, probability bundle optimizer, multi-brand curves, and conflict-aware promotion engine for Indian Kiranas & Supermarkets.**  
> *Architected for Google Cloud Platform (Cloud Run, Vertex AI, GCS, BigQuery) & Material Design 3.*

---

## 🌟 Key Innovations

1. **📱 App-Style (React Native-Inspired) Multi-Screen Interface:**
   - **Screen 1: 📦 Stock & Inventory Profile:** Clean stock metrics, cost/MRP margins, and inline velocity indicators.
   - **Screen 2: ⚡ Promo Generator:** Apriori-paired bundle creator, margin protector, WhatsApp simulator, and printable shelf poster generator.
   - **Screen 3: 📅 Regional Festival Calendar & Conflict Tracker:** Tracks hyper-local festival spikes (e.g., Deepavali requiring Deepas/Diyas and Cow Ghee) and prevents overlapping offer cannibalization.
   - **Screen 4: 📁 CSV Data Import & AI Markdown Sync:** Drag-and-drop CSV importer that parses retail data, executes Holt's demand forecasting, and compiles `data/store_knowledge.md`.
   - **Screen 5: 🏪 Store Profile & Regional Settings:** Manages store identity, regional demographics (Karnataka, Maharashtra, etc.), and Google Light/Dark theme.

2. **📊 Multi-Brand Comparative Sales Curves on the Exact Same Graph:**
   - Compares competing brands in the same category (e.g., **Amul Pure Cow Ghee** vs. **Nandini Pure Cow Ghee** vs. **Mother Dairy Cow Ghee**) on the exact same axis.
   - Plots historical 8-week sales (solid lines) and 4-week Holt-Winters festive surges (dashed lines).
   - Compares margin % vs. market share % with AI advice on optimal brand stocking.

3. **🛡️ Offer Conflict Prevention Engine:**
   - Real-time detection (`POST /api/offers/check-conflict`) that flags if a proposed discount overlaps with an active campaign on the same SKU, preventing double discounting and margin erosion.

4. **🪔 Hyper-Local Cultural & Regional Nuance:**
   - Deepavali in South India models a **+140% surge in Clay Deepas/Diyas, Pure Cow Ghee, and Cotton Wicks**, while dropping back to baseline (<5 units/month) during non-festival periods.
   - Tracks Ayudha Puja (Ash Gourd, Puffed Rice, Lemons) and Karthika Deepotsava.

5. **📄 AI Knowledge Catalog Base (`data/store_knowledge.md`):**
   - Automatically synchronizes all inventory records, time-series velocities, and Apriori matrices into a structured Markdown catalog that AI agents consult for grounding.

6. **💡 Executive Problem Statement & Whitepaper:**
   - Visit `/problem-statement` or open [`frontend/problem_statement.html`](frontend/problem_statement.html) for a complete analysis of retail challenges, solutions, and multi-stakeholder impact.

---

## 🏗️ Architecture Diagram

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

## 📂 Project Structure

```
promomind_ai/
├── backend/
│   ├── main.py               # FastAPI server (CORS, REST routes, UI static mount)
│   ├── agents.py             # Multi-agent orchestrator (Forecasting, Pairing, Pricing, Gemini)
│   ├── forecasting.py        # Open-source Holt-Winters smoothing & Apriori probability engine
│   ├── storage.py            # Persistent store, CSV importer, & store_knowledge.md compiler
│   ├── models.py             # Pydantic schemas (Product, BrandComparison, Festival, Conflicts)
│   └── mock_data.py          # Category brand curves, regional calendar, & active offers
├── data/
│   ├── inventory_store.json  # Persistent JSON inventory database
│   └── store_knowledge.md    # Auto-compiled AI Knowledge Base catalog
├── frontend/
│   ├── index.html            # App-style multi-screen interface (5 dedicated tabs)
│   ├── style.css             # Google Material 3 tokens, mobile bottom navigation & charts
│   ├── app.js                # State engine, SVG multi-brand charts, & conflict checking
│   └── problem_statement.html# Executive presentation whitepaper on retail problem/solution
├── .env.example              # Environment variables template
├── .gitignore                # Git ignore configuration
├── Dockerfile                # Google Cloud Run optimized container configuration
├── deploy.sh                 # Cloud Run deployment script
├── requirements.txt          # Python dependencies
├── SETUP_AND_CLOUD_GUIDE.md  # Detailed setup, usage, & Google Cloud integration guide
└── README.md                 # Project overview
```

---

## 🚀 Quick Start (Local Run)

```bash
# 1. Clone repository
git clone https://github.com/<your-username>/promomind_ai.git
cd promomind_ai

# 2. Setup Virtual Environment
python -m venv venv

# Windows:
.\venv\Scripts\Activate.ps1
# macOS/Linux:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy Environment Template
cp .env.example .env

# 5. Start the Server
python backend/main.py
```

Open your browser at:
- **PromoMind AI App:** 👉 `http://localhost:8080/`
- **Retail Problem Statement Whitepaper:** 👉 `http://localhost:8080/problem-statement`
- **AI Knowledge Catalog (.md):** 👉 `http://localhost:8080/api/knowledge-md`

---

## ☁️ Google Cloud Platform (GCP) Integration Roadmap

For a step-by-step guide on taking PromoMind AI from local testing to Google Cloud, read our comprehensive guide:

👉 **[SETUP_AND_CLOUD_GUIDE.md](SETUP_AND_CLOUD_GUIDE.md)**

Key integration stages:
1. **Google Cloud Run:** Serverless, auto-scaling containerized deployment via Cloud Build.
2. **Vertex AI / Gemini 1.5 Pro:** Multi-agent reasoning grounded directly in `store_knowledge.md`.
3. **Cloud Storage (GCS):** Multi-tenant CSV data lake and synced markdown vaults.
4. **Secret Manager:** Enterprise credential and API key storage.
5. **BigQuery:** Real-time Kirana POS transaction telemetry and automated model retraining.

---

## 🔌 API Endpoints Summary

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Responsive React-Native inspired 5-screen web app |
| `GET` | `/problem-statement` | Problem statement, retail solution & impact whitepaper |
| `GET` | `/api/inventory` | Retailer inventory, velocities, cost, MRP, and stock status |
| `GET` | `/api/inventory/{id}/brand-comparison` | Multi-brand sales curves (e.g., Amul vs Nandini vs Mother Dairy) |
| `GET` | `/api/calendar/events` | Regional festival events (Deepavali Deepas, Ayudha Puja, etc.) |
| `GET` | `/api/offers/active` | Currently scheduled and active in-store promotional offers |
| `POST` | `/api/offers/check-conflict` | Prevents margin cannibalization and overlapping promotions |
| `POST` | `/api/upload-csv` | Parses retailer CSV, runs Holt's models, and compiles `store_knowledge.md` |
| `GET` | `/api/knowledge-md` | View or download the auto-compiled AI knowledge markdown file |
| `POST` | `/api/generate-combo` | Apriori smart-pairing, margin calculation & Gemini collateral generation |
| `POST` | `/api/publish-offer` | Dispatches offer to POS and schedules in store calendar |

---

*PromoMind AI — Empowering Neighborhood Retailers with Intelligent Demand Forecasting & Google Cloud AI.*
