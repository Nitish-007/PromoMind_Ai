# 🎤 PromoMind AI — 3-Minute Live Hackathon & Investor Demo Script

> **Product**: PromoMind AI (v2.5)  
> **Tagline**: Autonomous Open-Source Demand Forecasting, Regional Festival Optimization & Capital Intelligence for 13M+ Indian Kiranas.  
> **Target Audience**: Hackathon Judges, Angel Investors, Google Cloud / Gemini Evaluators.  
> **Time Limit**: 3 Minutes (180 Seconds).

---

## ⏱️ Timeline & Pitch Flow

| Time | Phase | Focus Screen / Action | Key Speaking Line |
|---|---|---|---|
| **0:00 - 0:35** | **The Hook & Problem** | Presentation Deck / Problem Statement (`/deck` or `/problem-statement`) | *"13 million Kiranas in India power 85% of retail, yet lose ₹2.8 Lakh each year to dead inventory and blind festival discounts."* |
| **0:35 - 1:15** | **Screen 1: Capital ROI & Inventory** | App Main Dashboard (`/` Screen 1) | *"Meet our Dukan Capital ROI Predictor — predicting turnover rupees, dead capital risk, and running live 'What-If' discount simulations."* |
| **1:15 - 1:55** | **Screen 2: Dynamic Promo & Archetypes** | Promo Generator (`/` Screen 2) | *"Open-source Price Elasticity of Demand (PED) pairs high-velocity anchors with expiring slow-movers, generating instant Cashier verbal checkout scripts."* |
| **1:55 - 2:30** | **Screen 3: Cultural Regional Calendars** | Regional Festivals (`/` Screen 3) | *"Festivals can't be served at T-0. PromoMind AI gives T-14d advance procurement alerts so Kiranas buy before wholesale price hikes."* |
| **2:30 - 3:00** | **Cloud & Architecture Close** | Profile / Cloud Status (`/` Screen 5 & Terminal) | *"Dual-mode architecture: Runs offline with local JSON and synchronizes live with Google Cloud Firestore. 100% test-verified."* |

---

## 🎬 Minute-by-Minute Script

### Part 1: The Hook & Indian Retail Crisis (0:00 - 0:35)
- **Visual**: Open `http://localhost:8080/deck` (Slide 1 & 2).
- **Spoken**:
  > *"Good afternoon, Judges! India's $800 Billion retail market is driven by 13 Million local Kirana stores. But while quick-commerce giants deploy algorithmic dynamic pricing, local shopkeepers run blind discounts that destroy their margins.*
  > *Kiranas face three lethal problems: First, ₹2.8 Lakh trapped in slow-moving stock. Second, T-0 festival shocks where wholesalers jack up prices right before Diwali. Third, blind 20% discounts that bleed profits without moving volume.*
  > *We built **PromoMind AI** — an autonomous multi-agent platform combining open-source mathematical demand forecasting, regional cultural calendars, and Dukan Capital ROI intelligence."*

---

### Part 2: Screen 1 — Dukan Capital Investment & What-If ROI Simulator (0:35 - 1:15)
- **Visual**: Switch to `http://localhost:8080/` (Screen 1: Stock & Brands).
- **Actions**:
  1. Point to the **Dukan Capital Investment & Returns / Profit Predictor** banner at the top.
  2. Click **"Open 'What-If' ROI Simulator"**.
  3. Drag the **Discount Depth Slider** to 18% and **Volume Lift** to 40%.
- **Spoken**:
  > *"Here is the retailer's live command center. Rather than generic graphs, we show the shopkeeper their exact financial health: **₹1.91 Lakh total capital invested**, **₹4.68 Lakh projected monthly turnover**, and **₹62,970 in dead capital trapped** in slow movers like biscuits with 24 days shelf life.*
  > *Watch this: The retailer opens our interactive **'What-If' ROI Simulator**. If they run an 18% festival discount expecting a 40% volume lift, the open-source Price Elasticity engine instantly computes: simulated turnover of ₹3.56 Lakh, ₹1.54 Lakh net profit, and accelerates capital turnover by **6 days faster** with a green **'PROFIT POSITIVE'** verdict!"*

---

### Part 3: Screen 2 — Dynamic Promo Generator, Archetypes & Cashier Pitch (1:15 - 1:55)
- **Visual**: Click top tab **"⚡ Promo Generator"** (Screen 2).
- **Actions**:
  1. Click **"🚀 Anchor Booster"** or **"⏳ Expiry Rescue"** archetype chip.
  2. Anchor: Select *Taj Mahal Tea*, Co-Purchase: Select *Britannia Good Day Butter Cookies*.
  3. Click **"✨ Generate AI Promotional Plan"**.
  4. Show the plan result, WhatsApp chat preview, and switch to **"🗣️ Cashier Counter Script"** tab.
- **Spoken**:
  > *"In Screen 2, we don't just ask an LLM to guess. We use 4 open-source strategy archetypes based on mathematical Price Elasticity of Demand.*
  > *Selecting **'Anchor Booster'** pairs our fast-moving Taj Mahal Tea with our slow-moving Britannia Cookies. The Apriori basket model calculates affinity lift, while the pricing agent preserves a 20.4% net margin.*
  > *Notice the Omnichannel output: In addition to automated WhatsApp broadcast copy and print-ready posters, we provide the **Cashier Counter Script** — a 10-second verbal pitch in local vernacular: 'Sir/Ma'am, Tea ke saath Britannia Cookies lene par flat ₹81 ki direct bachat hai!' Quoting exact Rupee savings converts 2.3x higher at Indian counters than abstract percentages!"*

---

### Part 4: Screen 3 — Multi-Horizon Cultural Regional Festivals (1:55 - 2:30)
- **Visual**: Click top tab **"📅 Regional Festivals"** (Screen 3).
- **Actions**:
  1. Switch region dropdown between **"Karnataka & South India"** and **"Maharashtra & West India"**.
  2. Point out the **3-Horizon Planning Badges**:
     - `📦 T-14d Advance Procurement Window`
     - `🚀 T-7d Customer Promo Launch`
     - `🧹 T+2d Clearance Deadline`
- **Spoken**:
  > *"Festive commerce in India is hyper-localized. For Deepavali in Karnataka, demand for Earthen Diyas and Pure Cow Ghee surges by **+140%**, while on regular days clay deepa sales drop to zero.*
  > *PromoMind AI introduces **Multi-Horizon Planning**:*
  > *1. **T-14 Days**: Tells the merchant to buy Diyas and Cow Ghee wholesale before mandi rates spike.*
  > *2. **T-7 Days**: Launches early-bird WhatsApp pre-orders to lock in customer budgets.*
  > *3. **T+2 Days**: Mandatory clearance deadline to liquidate unsold seasonal stock at cost price before it turns into a 100% loss."*

---

### Part 5: Google Cloud Firestore & Production Scalability (2:30 - 3:00)
- **Visual**: Click top tab **"🏪 Store Profile"** (Screen 5) showing **🟢 Google Cloud Firestore Live** badge, then show terminal with `python tests/test_phase2_endpoints.py` output (`OK`).
- **Spoken**:
  > *"Under the hood, PromoMind AI is built for enterprise resilience with a **Dual-Mode Google Cloud Firestore** service. It runs completely offline with local JSON fallbacks if store internet drops, and auto-syncs to Google Cloud Firestore collections the moment credentials are connected.*
  > *We built a self-diagnostic tool `verify_gcp_creds.py` and have a **100% pass rate** across all 7 comprehensive integration tests.*
  > *PromoMind AI turns traditional Indian Kiranas into high-margin, predictive retail powerhouses. Thank you, and we welcome your questions!"*

---

## 🛠️ Quick Commands for Presenter

```bash
# 1. Run Verification Diagnostic Tool
python backend/verify_gcp_creds.py

# 2. Run Test Suite (7 tests, 100% OK)
python tests/test_phase2_endpoints.py

# 3. Start Production Server (Port 8080)
uvicorn backend.main:app --host 0.0.0.0 --port 8080 --reload
```

