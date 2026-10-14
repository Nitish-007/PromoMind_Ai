# PromoMind AI (v2.5) — Autonomous Retail Demand Forecasting, Regional Festival Optimization & Capital Intelligence

> **Autonomous multi-agent demand forecasting, open-source price elasticity modeling, cultural festival planning horizons, and Dukan Capital ROI intelligence for Indian Kiranas & Supermarkets.**  
> *Architected for Google Cloud Platform (Cloud Run, Cloud Firestore, Vertex AI) & Google Material Design 3.*

---

## 🌟 Key Innovations & Phase 2 Advancements

### 1. 💰 Dukan Capital Investment & Returns / Profit Predictor
- **Real-Time Working Capital Health**: Computes total working capital invested in inventory, projected 30-day sales turnover, and net gross profit.
- **Dead Capital at Risk**: Automatically flags working capital trapped in slow-moving SKUs (>60 days shelf life) before products expire into dead loss.
- **Cash Unlocked via Smart Promos**: Tracks fresh liquidity freed up within 12 days through algorithmic clearance bundles.
- **🔮 Interactive "What-If" ROI Simulator**: Retailers adjust **Promotional Discount Depth %** (5% to 30%) and **Expected Volume Lift %** (10% to 80%) to simulate resulting net profit rupees, turnover velocity, and capital turnover acceleration in real time.

### 2. 🧠 Open-Source Math: Price Elasticity of Demand (PED) Engine
- Built on deterministic, open-source mathematical principles without black-box dependency:
  $$\% \Delta Q = -\epsilon \cdot \% \Delta P$$
- Category-specific elasticity coefficients ($\epsilon = 0.85$ for staples, $1.70$ for packaged snacks, $2.10$ for festive gifting).
- **4 Open-Source Promotional Strategy Archetypes**:
  - `ANCHOR_MARGIN_BOOSTER`: High-velocity staple lifts high-margin slow-mover.
  - `EXPIRY_RESCUE_CLEARANCE`: Progressive markdown before shelf expiry.
  - `FESTIVE_CELEBRATION_HAMPER`: Multi-category bundles maximizing festive basket size.
  - `VOLUME_TIER_SLAB`: Bulk multi-unit purchase incentives (Buy 2+, Save More).

### 3. 🪔 Deep Cultural Regional Festival Calendars & Multi-Horizon Deadlines
- Comprehensive coverage across Indian cultural regions: **Karnataka & South India**, **Maharashtra & West India**, **Delhi-NCR & North India**, and **West Bengal & East India**.
- **Three-Horizon Planning Timelines**:
  - **📦 T-14 Days Advance Procurement**: Restock bulk Diyas, Cow Ghee, and Sweets before wholesale mandi rates surge.
  - **🚀 T-7 Days Promo Launch**: Early-bird WhatsApp broadcast hampers and advance bookings.
  - **🧹 T+2 Days Post-Festival Clearance**: Rapid cost-price markdown on leftover seasonal items to prevent 100% loss.

### 4. 🗣️ Retailer Persona & POS Checkout Scripts
- **Cashier Counter Cheat-Sheet**: 10-second verbal pitch in local vernacular (*"Sir, Tea ke saath Britannia Cookies lene par flat ₹81 ki direct bachat hai!"*). Quoting exact Rupee savings converts 2.3x higher than percentage claims.
- **WhatsApp Broadcast Engine**: Single-click sharing with auto-formatted emojis, store details, and offer expiry dates.
- **In-Store Print Posters**: High-contrast, printable shelf signage with barcodes.

### 5. ☁️ Enterprise Dual-Mode Google Cloud Firestore
- **Live Cloud Sync**: Seamless synchronization across `stores/{id}/inventory`, `stores/{id}/offers`, and `stores/{id}/profile`.
- **Zero-Downtime Fallback**: Instant offline persistence with local JSON when disconnected or before credentials are provided.
- **Automated Verification Script**: `python backend/verify_gcp_creds.py` for diagnostic verification.

### 6. 📊 Interactive Slide Presentation Deck & Demo Walkthrough
- **Pitch Deck**: Accessible in-browser at [`/deck`](http://localhost:8080/deck) or [`frontend/presentation_deck.html`](frontend/presentation_deck.html).
- **Pitch Script**: 3-minute hackathon and investor presentation guide in [`DEMO_SCRIPT.md`](DEMO_SCRIPT.md).
- **Whitepaper**: Problem statement and market impact analysis at [`/problem-statement`](http://localhost:8080/problem-statement).

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           Retailer Client Layer                                 │
│  React-Native Inspired Web App: Inventory | Promos | Calendar | CSV | Profile  │
│            [ What-If ROI Simulator ]  |  [ Cashier Checkout Script ]            │
└────────────────────────────────────────┬────────────────────────────────────────┘
                                         │ REST APIs (FastAPI)
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                       PromoMind AI Core Orchestration                           │
│  ┌────────────────────────┐  ┌───────────────────────┐  ┌────────────────────┐ │
│  │ Holt-Winters Double    │  │ Price Elasticity of   │  │ Dukan Capital      │ │
│  │ Exponential Smoothing  │  │ Demand (PED) Engine   │  │ ROI Engine         │ │
│  └────────────────────────┘  └───────────────────────┘  └────────────────────┘ │
│  ┌────────────────────────┐  ┌───────────────────────┐  ┌────────────────────┐ │
│  │ Multi-Horizon Regional │  │ Apriori Co-Purchase   │  │ Gemini 1.5 Creative│ │
│  │ Festival Calendars     │  │ Association Mining    │  │ Copywriting Agent  │ │
│  └────────────────────────┘  └───────────────────────┘  └────────────────────┘ │
└────────────────────────────────────────┬────────────────────────────────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                     Dual-Mode Data & Cloud Storage Layer                        │
│   • Google Cloud Firestore: Live Cloud Sync (stores/{id}/inventory, offers)     │
│   • Local JSON Storage: data/inventory_store.json, store_profile.json (Fallback)│
│   • Grounded Catalog: data/store_knowledge.md (Synced for AI Agent Reasoning)   │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 📂 Project Structure

```
promomind_ai/
├── backend/
│   ├── main.py               # FastAPI server (CORS, REST routes, UI static mount)
│   ├── agents.py             # Multi-agent orchestrator (PED pricing, Gemini copy, grounding)
│   ├── forecasting.py        # Holt-Winters smoothing, PED optimization & Investment ROI engine
│   ├── firestore_service.py  # Dual-mode Google Cloud Firestore service with local fallback
│   ├── verify_gcp_creds.py   # Diagnostic verification tool for Google Cloud credentials
│   ├── storage.py            # Persistent store manager, CSV importer & store_knowledge.md builder
│   ├── models.py             # Pydantic models (StoreProfile, InvestmentROI, RegionalEvent, etc.)
│   └── mock_data.py          # Category brand curves, regional calendars, & active offers
├── data/
│   ├── inventory_store.json  # Persistent JSON inventory database
│   ├── store_profile.json    # Store profile, regional demographic settings & capital budget
│   └── store_knowledge.md    # Auto-compiled AI Knowledge Base catalog
├── frontend/
│   ├── index.html            # App-style multi-screen interface (5 dedicated screens)
│   ├── style.css             # Google Material 3 tokens, ROI card, simulator drawer & charts
│   ├── app.js                # State engine, ROI simulator, archetype selector & SVG charts
│   ├── presentation_deck.html# Interactive slide presentation deck (9 slides, keyboard nav)
│   └── problem_statement.html# Executive presentation whitepaper on retail problem/solution
├── tests/
│   └── test_phase2_endpoints.py # Automated integration tests (7 tests, 100% pass)
├── DEMO_SCRIPT.md            # 3-Minute Hackathon & Investor Pitch Walkthrough Script
├── SETUP_AND_CLOUD_GUIDE.md  # Detailed setup, usage, & Google Cloud integration guide
├── Dockerfile                # Google Cloud Run container configuration
├── requirements.txt          # Python dependencies
└── README.md                 # Project documentation
```

---

## 🚀 Quick Start (Local Run)

```bash
# 1. Clone repository
git clone https://github.com/Nitish-007/PromoMind_Ai.git
cd promomind_ai

# 2. Setup Virtual Environment
python -m venv venv
# Windows:
.\venv\Scripts\Activate.ps1
# macOS/Linux:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. (Optional) Verify Google Cloud Firestore Setup
python backend/verify_gcp_creds.py

# 5. Run Integration Tests
python tests/test_phase2_endpoints.py

# 6. Start the Server
python backend/main.py
```

Open your browser at:
- **PromoMind AI App:** 👉 `http://localhost:8080/`
- **Interactive Pitch Deck:** 👉 `http://localhost:8080/deck`
- **Problem Statement Whitepaper:** 👉 `http://localhost:8080/problem-statement`
- **AI Knowledge Catalog (.md):** 👉 `http://localhost:8080/api/knowledge-md`

---

## ☁️ Google Cloud Firestore Setup Guide

PromoMind AI operates in **Dual-Mode**: It runs out-of-the-box in local offline mode and automatically enables live Google Cloud Firestore synchronization the moment credentials are placed.

### Connecting Your Google Cloud Firestore:
1. Open the [Firebase Console](https://console.firebase.google.com/) or [Google Cloud Console](https://console.cloud.google.com/).
2. Create or select a project (e.g., `promomind-ai`).
3. Navigate to **Firestore Database** and create a database in production or test mode.
4. Go to **Project Settings** → **Service Accounts** → Click **Generate new private key**.
5. Save the downloaded JSON file as `service_account.json` in the project root directory.
6. Verify connectivity:
   ```bash
   python backend/verify_gcp_creds.py
   ```
7. PromoMind AI will immediately log: `[PromoMind Firestore] [ONLINE] Connected to Google Cloud Firestore`.

---

## 🔌 API Endpoints Summary

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Responsive React-Native inspired 5-screen web app |
| `GET` | `/deck` | Interactive slide presentation deck for investors & judges |
| `GET` | `/problem-statement` | Problem statement, retail solution & impact whitepaper |
| `GET` | `/api/health` | Service health status and active configuration |
| `GET` | `/api/system/cloud-status` | Google Cloud Firestore connection status & credentials state |
| `GET` | `/api/profile` | Retailer profile, working capital budget & regional settings |
| `POST` | `/api/profile` | Update retailer profile and recompile `store_knowledge.md` |
| `GET` | `/api/store/financial-roi` | Dukan Capital ROI metrics (turnover, net profit, dead capital risk) |
| `POST` | `/api/store/simulate-roi` | "What-If" ROI simulation (adjust discount depth & volume lift) |
| `GET` | `/api/inventory` | Retailer inventory, velocities, cost, MRP, and stock status |
| `GET` | `/api/inventory/{id}/brand-comparison` | Multi-brand sales curves (e.g., Amul vs Nandini vs Mother Dairy) |
| `GET` | `/api/calendar/events` | Multi-horizon regional festival events (`?region=...`) |
| `GET` | `/api/offers/active` | Currently scheduled and active in-store promotional offers |
| `POST` | `/api/offers/check-conflict` | Prevents margin cannibalization and overlapping promotions |
| `POST` | `/api/upload-csv` | Parses retailer CSV, runs Holt's models, and compiles `store_knowledge.md` |
| `GET` | `/api/knowledge-md` | View or download the auto-compiled AI knowledge markdown file |
| `POST` | `/api/generate-combo` | Dynamic promo generation with strategy archetypes & cashier pitch |
| `POST` | `/api/publish-offer` | Dispatches offer to POS and schedules in store calendar |

---

## 🧪 Automated Test Suite

Run the full end-to-end integration test suite:
```bash
python tests/test_phase2_endpoints.py
```
**Results:** `7 tests passed in 0.10s (100% OK)`.

---

*PromoMind AI — Empowering Neighborhood Retailers with Intelligent Demand Forecasting & Google Cloud AI.*
