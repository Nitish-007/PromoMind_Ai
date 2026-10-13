import os
import sys
import json
from typing import List, Dict, Any, Optional

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
DATA_DIR = os.path.join(PROJECT_ROOT, "data")

if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from models import Product
from mock_data import INVENTORY_DATA, DEMAND_FORECASTS
from forecasting import OpenSourceForecastingEngine

STORE_JSON_FILE = os.path.join(DATA_DIR, "inventory_store.json")
KNOWLEDGE_MD_FILE = os.path.join(DATA_DIR, "store_knowledge.md")

class StoreDataManager:
    """Manages persistent inventory storage and builds markdown knowledge files for AI."""

    @classmethod
    def ensure_data_directory(cls):
        os.makedirs(DATA_DIR, exist_ok=True)

    @classmethod
    def load_products(cls) -> List[Product]:
        cls.ensure_data_directory()
        if not os.path.exists(STORE_JSON_FILE):
            # Seed with baseline inventory data
            cls.save_products(INVENTORY_DATA)
            return INVENTORY_DATA

        try:
            with open(STORE_JSON_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return [Product(**item) for item in data]
        except Exception:
            return INVENTORY_DATA

    @classmethod
    def save_products(cls, products: List[Product]):
        cls.ensure_data_directory()
        data = [p.model_dump() for p in products]
        with open(STORE_JSON_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        cls.rebuild_knowledge_markdown(products)

    @classmethod
    def add_or_update_product(cls, product: Product) -> List[Product]:
        products = cls.load_products()
        # Check if ID exists, update or append
        existing_idx = next((i for i, p in enumerate(products) if p.id == product.id), None)
        if existing_idx is not None:
            products[existing_idx] = product
        else:
            products.append(product)

        cls.save_products(products)
        return products

    @classmethod
    def import_csv_data(cls, csv_content: str):
        import csv
        import io
        cls.ensure_data_directory()
        reader = csv.DictReader(io.StringIO(csv_content.strip()))
        imported = 0
        products = cls.load_products()
        
        for row in reader:
            # Flexible field resolution
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

        cls.save_products(products)
        return imported, cls.get_knowledge_markdown()

    @classmethod
    def rebuild_knowledge_markdown(cls, products: Optional[List[Product]] = None) -> str:
        cls.ensure_data_directory()
        if products is None:
            products = cls.load_products()

        lines = [
            "# 🏪 PromoMind AI — Retail Store Knowledge & Catalog Base",
            "> *Persistent AI Knowledge Catalog for Sharma Supermarket (Bengaluru)*",
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
            "|---|---|---|---|",
            "| **Diwali Maha Utsav (Big Festive Days)** | Pure Ghee, Dry Fruits, Gulab Jamun, Cooking Oil | **+75% to +110%** | Bundle high-margin dry fruits with fast-selling cow ghee for festive gifting. |",
            "| **Monsoon Refresh Bonanza** | Premium Teas, Biscuits, Spices, Hot Snacks | **+35% to +45%** | Pair evening chai with near-expiry cookies at 17% discount. |",
            "| **Great Indian Grocery Super Saver** | Staples, Sunflower Oil, Garam Masala | **+40% to +50%** | Volume tier pricing / Buy cooking oil & get spice pack at 50% off. |",
            "| **Super Weekend Kirana Rush** | All Kitchen Staples & Snacks | **+25% to +35%** | Run fast-moving basket driver offers with clear POS receipt taglines. |\n",
            "---",
            "## 🤖 4. Guidelines for Multi-Agent Combo Generation",
            "1. **Anchor Selection**: Identify items with positive growth momentum (>+30%) or seasonal surge.",
            "2. **Attached Selection**: Pair anchors with items that have high co-purchase affinity (>50%) or slow velocity to clear near-expiry capital.",
            "3. **Margin Floor**: Never breach retailer minimum margin (18% by default).",
            "4. **Copy Persona**: Punchy Indian retail phrasing with WhatsApp emojis and clear rupee savings."
        ])

        md_content = "\n".join(lines)
        with open(KNOWLEDGE_MD_FILE, "w", encoding="utf-8") as f:
            f.write(md_content)

        return md_content

    @classmethod
    def get_knowledge_markdown(cls) -> str:
        cls.ensure_data_directory()
        if not os.path.exists(KNOWLEDGE_MD_FILE):
            return cls.rebuild_knowledge_markdown()
        with open(KNOWLEDGE_MD_FILE, "r", encoding="utf-8") as f:
            return f.read()

