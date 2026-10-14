"use client";

import React, { useState, useMemo } from "react";
import { Search, BarChart3, TrendingUp, AlertCircle, ArrowUpRight } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";

const CATEGORIES = [
  "ALL",
  "Dairy",
  "Beverages",
  "Snacks",
  "Staples & Oils",
  "Dry Fruits",
  "Puja & Festive",
];

export function InventoryTable({
  products,
  isLoading,
  onOpenBrandModal,
  onCreatePromoForProduct,
}) {
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("ALL");

  const filteredProducts = useMemo(() => {
    return products.filter((p) => {
      const matchesSearch =
        !searchTerm ||
        p.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        p.id?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        p.category?.toLowerCase().includes(searchTerm.toLowerCase());

      const matchesCat =
        selectedCategory === "ALL" ||
        (p.category && p.category.toLowerCase().includes(selectedCategory.toLowerCase()));

      return matchesSearch && matchesCat;
    });
  }, [products, searchTerm, selectedCategory]);

  return (
    <div className="space-y-3">
      {/* Search and Category Filters */}
      <div className="flex flex-col sm:flex-row gap-3 items-stretch sm:items-center justify-between">
        <div className="relative w-full sm:w-72">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            type="text"
            placeholder="Search SKU, name, or category..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-9 h-9 text-xs"
          />
        </div>

        {/* Category Pills */}
        <div className="flex gap-1.5 overflow-x-auto no-scrollbar py-0.5">
          {CATEGORIES.map((cat) => {
            const isSelected = selectedCategory === cat;
            return (
              <button
                key={cat}
                onClick={() => setSelectedCategory(cat)}
                className={`rounded-md px-2.5 py-1 text-xs font-medium whitespace-nowrap transition-colors border ${
                  isSelected
                    ? "bg-foreground text-background border-foreground font-semibold"
                    : "bg-transparent text-muted-foreground border-border hover:bg-muted hover:text-foreground"
                }`}
              >
                {cat === "ALL" ? "All Items" : cat}
              </button>
            );
          })}
        </div>
      </div>

      {/* Modern Responsive Table */}
      <div className="rounded-xl border bg-card overflow-hidden shadow-xs">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-muted/40 text-muted-foreground uppercase tracking-wider text-xs font-semibold border-b">
              <tr>
                <th className="px-4 py-3.5">Product / SKU</th>
                <th className="px-4 py-3.5">Category</th>
                <th className="px-4 py-3.5">Stock Status</th>
                <th className="px-4 py-3.5">Cost / MRP</th>
                <th className="px-4 py-3.5">Margin</th>
                <th className="px-4 py-3.5">Weekly Velocity</th>
                <th className="px-4 py-3.5">AI Restock Verdict</th>
                <th className="px-4 py-3.5 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/60">
              {isLoading ? (
                [...Array(5)].map((_, i) => (
                  <tr key={i} className="animate-pulse">
                    <td className="px-4 py-3.5">
                      <Skeleton className="h-4 w-40 rounded mb-1" />
                      <Skeleton className="h-3 w-20 rounded" />
                    </td>
                    <td className="px-4 py-3.5">
                      <Skeleton className="h-5 w-20 rounded-full" />
                    </td>
                    <td className="px-4 py-3.5">
                      <Skeleton className="h-4 w-16 rounded mb-1" />
                      <Skeleton className="h-3 w-24 rounded" />
                    </td>
                    <td className="px-4 py-3.5">
                      <Skeleton className="h-4 w-20 rounded mb-1" />
                      <Skeleton className="h-3 w-16 rounded" />
                    </td>
                    <td className="px-4 py-3.5">
                      <Skeleton className="h-4 w-12 rounded" />
                    </td>
                    <td className="px-4 py-3.5">
                      <Skeleton className="h-4 w-16 rounded" />
                    </td>
                    <td className="px-4 py-3.5">
                      <Skeleton className="h-6 w-28 rounded-md" />
                    </td>
                    <td className="px-4 py-3.5 text-right">
                      <div className="flex justify-end gap-1.5">
                        <Skeleton className="h-8 w-16 rounded-md" />
                        <Skeleton className="h-8 w-24 rounded-md" />
                      </div>
                    </td>
                  </tr>
                ))
              ) : filteredProducts.length === 0 ? (
                <tr>
                  <td colSpan={8} className="py-14 text-center text-muted-foreground text-sm">
                    No products found matching your search.
                  </td>
                </tr>
              ) : (
                filteredProducts.map((p) => {
                  const marginPct = (
                    ((p.selling_price - p.cost_price) / Math.max(1, p.selling_price)) *
                    100
                  ).toFixed(1);

                  const isLowStock =
                    (p.days_inventory_remaining || 99) <= 18 ||
                    p.sell_through_verdict === "STRONG_INVEST_BUY";

                  return (
                    <tr
                      key={p.id}
                      className="group hover:bg-muted/30 transition-colors"
                    >
                      {/* Product Name & SKU */}
                      <td className="px-4 py-3.5">
                        <div className="font-semibold text-foreground group-hover:text-primary transition-colors text-sm">
                          {p.name}
                        </div>
                        <div className="text-xs font-mono text-muted-foreground mt-0.5">
                          {p.id}
                        </div>
                      </td>

                      {/* Category */}
                      <td className="px-4 py-3.5">
                        <Badge variant="outline" className="text-xs font-normal">
                          {p.category}
                        </Badge>
                      </td>

                      {/* Stock Quantity */}
                      <td className="px-4 py-3.5">
                        <div className="font-medium text-foreground text-sm">
                          {p.stock_quantity} units
                        </div>
                        <div
                          className={`text-xs mt-0.5 ${
                            isLowStock ? "text-rose-600 dark:text-rose-400 font-semibold" : "text-muted-foreground"
                          }`}
                        >
                          {p.days_inventory_remaining ?? 14}d stock left
                        </div>
                      </td>

                      {/* Cost / MRP */}
                      <td className="px-4 py-3.5">
                        <div className="font-medium text-foreground text-sm">
                          ₹{p.selling_price} <span className="text-muted-foreground text-xs font-normal">MRP</span>
                        </div>
                        <div className="text-xs text-muted-foreground mt-0.5">
                          Cost: ₹{p.cost_price}
                        </div>
                      </td>

                      {/* Margin % */}
                      <td className="px-4 py-3.5">
                        <span
                          className={`font-semibold text-sm ${
                            parseFloat(marginPct) >= 20
                              ? "text-emerald-600 dark:text-emerald-400"
                              : "text-amber-600 dark:text-amber-400"
                          }`}
                        >
                          {marginPct}%
                        </span>
                      </td>

                      {/* Velocity */}
                      <td className="px-4 py-3.5">
                        <div className="font-medium text-foreground text-sm flex items-center gap-1.5">
                          <span>{p.weekly_sales_avg} / wk</span>
                          {p.velocity_status === "FAST_MOVING" && (
                            <TrendingUp className="h-3.5 w-3.5 text-emerald-500" />
                          )}
                        </div>
                        <div className="text-xs text-muted-foreground mt-0.5">
                          {p.velocity_status}
                        </div>
                      </td>

                      {/* AI Verdict */}
                      <td className="px-4 py-3.5">
                        <div className="inline-flex">
                          {p.sell_through_verdict === "STRONG_INVEST_BUY" ? (
                            <Badge variant="outline" className="border-emerald-600/30 text-emerald-600 dark:text-emerald-400 text-xs font-medium bg-emerald-500/5 px-2 py-0.5">
                              Strong Buy
                            </Badge>
                          ) : p.sell_through_verdict === "DO_NOT_REORDER" ? (
                            <Badge variant="outline" className="border-rose-600/30 text-rose-600 dark:text-rose-400 text-xs font-medium bg-rose-500/5 px-2 py-0.5">
                              Capital Risk
                            </Badge>
                          ) : (
                            <Badge variant="outline" className="border-border text-muted-foreground text-xs font-medium px-2 py-0.5">
                              Monitor
                            </Badge>
                          )}
                        </div>
                      </td>

                      {/* Actions */}
                      <td className="px-4 py-3.5 text-right">
                        <div className="flex items-center justify-end gap-2">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => onOpenBrandModal(p)}
                            className="gap-1.5 text-xs h-8 px-2.5 border-border text-foreground hover:bg-muted"
                            title="Compare Brands on same curve"
                          >
                            <BarChart3 className="h-3.5 w-3.5 text-muted-foreground" />
                            <span>Brands</span>
                          </Button>
                          <Button
                            variant="secondary"
                            size="sm"
                            onClick={() => onCreatePromoForProduct(p)}
                            className="text-xs h-8 px-2.5 gap-1.5"
                            title="Create bundle offer with this SKU"
                          >
                            <span>Promo</span>
                            <ArrowUpRight className="h-3.5 w-3.5 opacity-60" />
                          </Button>
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

