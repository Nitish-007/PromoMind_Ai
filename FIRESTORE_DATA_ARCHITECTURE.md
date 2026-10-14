# ☁️ PromoMind AI — Firestore & Data Architecture Documentation

This document explains **where and how CSV files, Markdown catalogs, and application records are stored**, how the **Dual-Mode Hybrid Storage Adapter** handles data in Firestore and local fallback mode, and the exact **document schemas** for all 5 collections.

---

## 1. Where Are CSV Files & Markdown Files Stored?

### 📄 What Happens to Uploaded CSV Files?
When a user uploads a CSV file (via `POST /api/upload-csv` or through the **Quick CSV Upload** modal):
1. **The raw CSV file itself is NOT saved as a static file** (Firestore is a NoSQL document database, not a blob/object store like Google Cloud Storage).
2. **What happens instead:**
   - The CSV is streamed into memory.
   - Each row is parsed, validated, and normalized into a structured `Product` object.
   - The system executes **Holt's Double Exponential Smoothing & demand forecasting** on each SKU's sales series.
   - Calculated fields (gross margin %, days of stock remaining, sell-through velocity, and restock verdict) are attached to each item.
   - The resulting structured records are **written directly to Firestore** as individual documents in `stores/{store_id}/inventory/{sku_id}` using a batch write.
   - In addition, they are cached locally in `data/store_inventory.json` for offline fallback.

### 📝 What Happens to the Markdown (`store_knowledge.md`) File?
The Markdown catalog is **stored in BOTH Firestore and local disk**:
1. **In Google Cloud Firestore:**
   - Stored in the collection `stores/{store_id}/knowledge_catalog` under the document ID `current`.
   - Document field `markdown` contains the entire compiled Markdown text, alongside `updated_at`, `sku_count`, and `mode`.
2. **On Local Disk:**
   - Saved at `data/store_knowledge.md` in the application root.
   - Kept in sync automatically whenever Firestore inventory changes via a real-time snapshot listener.
3. **Purpose:**
   - This compiled Markdown serves as the system prompt grounding for the **AI Copilot** (Gemini agent) to generate combo bundles, WhatsApp copy, and margin-protected pricing.

---

## 2. Dual-Mode Storage Architecture

```
                  ┌──────────────────────────────────────────────┐
                  │          PromoMind AI Backend API           │
                  └──────────────────────┬───────────────────────┘
                                         │
                         Dual-Mode Hybrid Storage Adapter
                                         │
                 ┌───────────────────────┴───────────────────────┐
                 │                                               │
          [CLOUD MODE]                                  [LOCAL FALLBACK MODE]
     Google Cloud Firestore                        Local JSON Files & Markdown
 (stores/{store_id}/...)                                (data/ directory)
                 │                                               │
   ├── inventory/                                  ├── store_inventory.json
   ├── promotions/                                 ├── store_promotions.json
   ├── calendar_events/                            ├── festival_calendar.json
   ├── store_profile/                              ├── store_profile.json
   └── knowledge_catalog/                          └── store_knowledge.md
```

- **Cloud Mode (`CLOUD`)**: Enabled when `FIRESTORE_SA_JSON` (or `FIRESTORE_PROJECT_ID`) is provided. All read and write operations go directly to Firestore with sub-second latency.
- **Local Fallback Mode (`LOCAL_FALLBACK`)**: If running offline, without network access, or without Google Cloud credentials, the adapter automatically reads and writes to local JSON files in `data/`, ensuring **zero downtime**.
- **Instant AI Sync**: Every time an inventory write occurs (manual SKU addition, CSV batch import, or background Firestore update), the adapter triggers `rebuild_knowledge_markdown()`, re-compiling `store_knowledge.md` and syncing `stores/{store_id}/knowledge_catalog/current`.

---

## 3. Firestore Collections & Document Schemas

All collections are scoped under the multi-tenant root document:
```
stores/{store_id}/
```
Default `store_id`: `sharma_supermarket_01` (configurable via `STORE_ID` in `.env`).

---

### Collection 1: `stores/{store_id}/inventory`
- **Document ID:** Product SKU ID (e.g. `PROD_TEA_01`, `PROD_GHEE_01`)
- **Description:** Real-time stock levels, MRP, cost price, historical sales, forecast curves, and velocity ratings.

#### Document Schema:
```json
{
  "id": "PROD_TEA_01",
  "name": "Tata Tea Gold Leaf 500g",
  "category": "Beverages",
  "cost_price": 280.0,
  "selling_price": 340.0,
  "stock_quantity": 42,
  "days_in_stock": 14,
  "expiry_days": 180,
  "velocity_status": "FAST_MOVING",
  "weekly_sales_avg": 38,
  "image_url": "product_default.png",
  "past_sales_weeks": [32, 34, 37, 39, 41, 44],
  "forecast_sales_weeks": [48, 52, 57, 62],
  "sell_through_verdict": "STRONG_INVEST_BUY",
  "verdict_badge": "🟢 Strong Buy / Restock Now",
  "days_inventory_remaining": 7,
  "sell_through_rate_pct": 90.5,
  "reorder_recommendation": "Surge incoming (+40%). Order 45 units immediately.",
  "brand_comparison_insight": "Tata Tea holds 58% Kirana category share with 17.6% margin.",
  "alternative_brands": ["Wagh Bakri Premium Leaf Tea", "Red Label Natural Care"]
}
```

---

### Collection 2: `stores/{store_id}/promotions`
- **Document ID:** Offer ID (e.g. `OFFER_LIVE_01`, `CONFLICT_LOG_01`)
- **Description:** Active and scheduled promotional bundles, co-purchase combinations, and detected margin cannibalization conflict logs.

#### Document Schema (Active Offer):
```json
{
  "id": "OFFER_LIVE_01",
  "combo_id": "COMBO_DIWALI_TEA_01",
  "title": "Diwali Chai & Biscuit Festive Anand Bundle",
  "anchor_id": "PROD_TEA_01",
  "attached_id": "PROD_BISCUIT_01",
  "start_date": "2026-10-15",
  "end_date": "2026-10-25",
  "discount_pct": 17.5,
  "combo_price": 399.0,
  "event_theme": "Diwali Maha Utsav",
  "status": "ACTIVE",
  "type": "promotion",
  "updated_at": "2026-10-14T18:00:00.000Z"
}
```

#### Document Schema (Conflict Log):
```json
{
  "type": "conflict_log",
  "logged_at": "2026-10-14T18:00:00.000Z",
  "anchor_id": "PROD_TEA_01",
  "attached_id": "PROD_BISCUIT_01",
  "conflict_reason": "Overlap detected with active offer 'Diwali Chai & Biscuit Festive Anand Bundle'...",
  "conflicting_offers": [ ... ]
}
```

---

### Collection 3: `stores/{store_id}/calendar_events`
- **Document ID:** Event ID (e.g. `diwali_2026`, `dussehra_2026`, `karwa_chauth_2026`)
- **Description:** Regional festival calendar with category demand surge items.

#### Document Schema:
```json
{
  "id": "diwali_2026",
  "name": "Diwali & Deepavali Maha Utsav",
  "region": "Pan-India",
  "date_window": "Oct 24 - Oct 29, 2026",
  "status": "ACTIVE",
  "demand_lift_pct": 65.0,
  "key_items": [
    "Diyas / Clay Deepas",
    "Pure Cow Ghee",
    "Gulab Jamun Mix",
    "Premium Dry Fruits & Almonds",
    "Pooja Camphor"
  ],
  "icon": "🪔",
  "description": "Peak festive shopping window across all regions."
}
```

---

### Collection 4: `stores/{store_id}/store_profile`
- **Document ID:** `profile`
- **Description:** Store identity, regional location, contact coordinates, WhatsApp broadcast size, and customer loyalty records.

#### Document Schema:
```json
{
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
  "updated_at": "2026-10-14T18:00:00.000Z",
  "customer_list": [
    {
      "name": "Priya Nair",
      "phone": "+91 98451 11111",
      "segment": "Frequent Festive Shopper",
      "preferred_channel": "WhatsApp"
    },
    {
      "name": "Rajesh Hegde",
      "phone": "+91 98452 22222",
      "segment": "Bulk Monthly Groceries",
      "preferred_channel": "WhatsApp"
    }
  ]
}
```

---

### Collection 5: `stores/{store_id}/knowledge_catalog`
- **Document ID:** `current`
- **Description:** The compiled Markdown catalog (`store_knowledge.md`) synced to Firestore for AI grounding.

#### Document Schema:
```json
{
  "store_id": "sharma_supermarket_01",
  "markdown": "# 🏪 PromoMind AI — Retail Store Knowledge & Catalog Base\n...",
  "sku_count": 8,
  "mode": "CLOUD",
  "updated_at": "2026-10-14T18:00:00.000Z"
}
```

---

## 4. Summary Table

| Data Asset | Uploaded / Input Format | Stored in Firestore? | Stored on Local Disk? | Firestore Path | Local File Path |
| :--- | :--- | :---: | :---: | :--- | :--- |
| **Inventory Records** | CSV upload or manual form | ✅ Yes (Documents per SKU) | ✅ Yes (JSON cache) | `stores/{store_id}/inventory/{sku_id}` | `data/store_inventory.json` |
| **Raw CSV File** | `.csv` binary stream | ❌ No (Parsed to documents) | ❌ No (Processed in memory) | *N/A* | *N/A* |
| **Store Knowledge Base**| Auto-generated Markdown | ✅ Yes (Full markdown string) | ✅ Yes (`.md` file) | `stores/{store_id}/knowledge_catalog/current` | `data/store_knowledge.md` |
| **Promotions & Combos** | AI plan or UI form | ✅ Yes (Documents per offer) | ✅ Yes (JSON cache) | `stores/{store_id}/promotions/{offer_id}` | `data/store_promotions.json` |
| **Festival Calendar** | Pre-seeded or API update | ✅ Yes (Documents per event) | ✅ Yes (JSON cache) | `stores/{store_id}/calendar_events/{event_id}` | `data/festival_calendar.json` |
| **Store Profile** | Settings UI form | ✅ Yes (Single doc: `profile`) | ✅ Yes (JSON cache) | `stores/{store_id}/store_profile/profile` | `data/store_profile.json` |

