"use client";

import React, { useState } from "react";
import { Plus, Upload, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { FinancialRoiCard } from "./FinancialRoiCard";
import { InventoryKpiGrid } from "./InventoryKpiGrid";
import { InventoryTable } from "./InventoryTable";

const PERSONAS = [
  {
    id: "owner",
    label: "Store Owner (Capital & ROI)",
    desc: "Focuses on working capital recovery, net store profit, and unlocking cash from slow movers.",
  },
  {
    id: "procurement",
    label: "Procurement Buyer (Brands & Restock)",
    desc: "Focuses on Holt-Winters 4-week demand forecasts, stockout alerts, and multi-brand margin curves.",
  },
  {
    id: "floor",
    label: "Floor & POS Manager (Quick Promos)",
    desc: "Focuses on launching instant combos, clearing near-expiry shelf stock, and cashier upsell scripts.",
  },
];

export function InventoryScreen({
  products,
  roiData,
  isLoading,
  onRefresh,
  onOpenAddSku,
  onOpenImportCsv,
  onOpenBrandModal,
  onCreatePromoForProduct,
  onSimulateRoi,
}) {
  const [activePersona, setActivePersona] = useState("owner");

  return (
    <div className="space-y-6">
      {/* Screen Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
            <span>Retail Inventory &amp; Multi-Brand Curves</span>
          </h2>
          <p className="text-xs sm:text-sm text-muted-foreground mt-0.5">
            Track stock health, Holt-Winters demand velocity, and compare competing FMCG brands on the exact same graph.
          </p>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <Button
            variant="outline"
            size="sm"
            onClick={onRefresh}
            disabled={isLoading}
            className="gap-2 text-sm h-9 px-3"
            title="Refresh inventory"
          >
            <RefreshCw className={`h-4 w-4 ${isLoading ? "animate-spin" : ""}`} />
            <span className="hidden sm:inline">Refresh</span>
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={onOpenAddSku}
            className="gap-2 text-sm h-9 px-3 border-border hover:bg-muted"
          >
            <Plus className="h-4 w-4 text-foreground" />
            <span>Add SKU</span>
          </Button>

          <Button
            size="sm"
            onClick={onOpenImportCsv}
            className="gap-2 text-sm h-9 px-3 shadow-xs font-medium"
          >
            <Upload className="h-4 w-4" />
            <span>Firestore CSV Sync</span>
          </Button>
        </div>
      </div>

      {/* Retailer Persona View Switcher (Issue #2) */}
      <div className="rounded-xl border border-border bg-card p-3 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-1.5">
          <span className="text-xs font-bold uppercase tracking-wider text-muted-foreground mr-2">
            Retailer Persona View:
          </span>
          {PERSONAS.map((p) => {
            const isSel = activePersona === p.id;
            return (
              <button
                key={p.id}
                type="button"
                onClick={() => setActivePersona(p.id)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors border ${
                  isSel
                    ? "bg-foreground text-background border-foreground font-semibold"
                    : "bg-muted/40 text-foreground border-border hover:bg-muted"
                }`}
              >
                {p.label}
              </button>
            );
          })}
        </div>
        <Badge variant="outline" className="text-[11px] font-normal text-muted-foreground border-border w-fit">
          {PERSONAS.find((p) => p.id === activePersona)?.desc}
        </Badge>
      </div>

      {/* Financial ROI Predictor Card with What-If Simulator */}
      {activePersona !== "procurement" && (
        <FinancialRoiCard roiData={roiData} onSimulate={onSimulateRoi} />
      )}

      {/* Quick KPI Stat Tiles */}
      <InventoryKpiGrid products={products} />

      {/* Inventory Search, Category Filters and Table */}
      <InventoryTable
        products={products}
        isLoading={isLoading}
        onOpenBrandModal={onOpenBrandModal}
        onCreatePromoForProduct={onCreatePromoForProduct}
      />
    </div>
  );
}
