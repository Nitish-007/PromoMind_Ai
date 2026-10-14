"use client";

import React, { useState } from "react";
import { Plus, Upload, Sparkles, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { FinancialRoiCard } from "./FinancialRoiCard";
import { InventoryKpiGrid } from "./InventoryKpiGrid";
import { InventoryTable } from "./InventoryTable";

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
  return (
    <div className="space-y-6">
      {/* Screen Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
            <span>Retail Inventory & Multi-Brand Curves</span>
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
            <span>Import CSV</span>
          </Button>
        </div>
      </div>

      {/* Financial ROI Predictor Card with What-If Simulator */}
      <FinancialRoiCard roiData={roiData} onSimulate={onSimulateRoi} />

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

