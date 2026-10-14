"use client";

import { Package, DollarSign, Zap, AlertTriangle } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";

export function InventoryKpiGrid({ products }) {
  const totalSkus = products.length;
  const totalValuation = products.reduce(
    (acc, p) => acc + (p.stock_quantity || 0) * (p.cost_price || 0),
    0
  );
  const fastMovers = products.filter(
    (p) => p.velocity_status === "FAST_MOVING" || (p.weekly_sales_avg || 0) >= 30
  ).length;
  const stockoutAlerts = products.filter(
    (p) =>
      p.sell_through_verdict === "STRONG_INVEST_BUY" ||
      (p.days_inventory_remaining || 99) <= 18
  ).length;

  const cards = [
    {
      label: "Active SKUs",
      value: totalSkus || "--",
      icon: Package,
    },
    {
      label: "Inventory Valuation",
      value: `₹${totalValuation.toLocaleString("en-IN", { maximumFractionDigits: 0 })}`,
      icon: DollarSign,
    },
    {
      label: "High Velocity Anchors",
      value: fastMovers || "--",
      icon: Zap,
    },
    {
      label: "Stockout Warnings",
      value: stockoutAlerts || "--",
      icon: AlertTriangle,
    },
  ];

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
      {cards.map((c, i) => {
        const Icon = c.icon;
        return (
          <Card key={i} className="border border-border shadow-xs bg-card hover:bg-muted/30 transition-colors">
            <CardContent className="p-3.5 flex items-center gap-3">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-md bg-muted text-foreground border border-border">
                <Icon className="h-5 w-5 text-muted-foreground" />
              </div>
              <div className="overflow-hidden">
                <div className="text-lg sm:text-xl font-bold tracking-tight text-foreground truncate">
                  {c.value}
                </div>
                <div className="text-xs sm:text-sm text-muted-foreground truncate font-medium">
                  {c.label}
                </div>
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}

