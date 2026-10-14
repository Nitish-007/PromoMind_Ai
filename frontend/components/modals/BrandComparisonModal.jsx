"use client";

import React, { useState } from "react";
import { BarChart3, X, Sparkles, TrendingUp, DollarSign } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

export function BrandComparisonModal({
  isOpen,
  onClose,
  product,
  brandData,
  onUseInPromo,
}) {
  const [viewMode, setViewMode] = useState("ALL_BRANDS"); // 'ALL_BRANDS' or 'SINGLE_SKU'

  if (!isOpen || !product) return null;

  const brands = brandData?.brands || [
    {
      brand_name: `${product.name} (Current Store Brand)`,
      mrp: product.selling_price,
      cost_price: product.cost_price,
      margin_pct: (
        ((product.selling_price - product.cost_price) / Math.max(1, product.selling_price)) *
        100
      ).toFixed(1),
      weekly_sales_avg: product.weekly_sales_avg || 35,
      past_sales: product.past_sales_weeks || [24, 26, 28, 30, 32, 35],
      forecast_sales: product.forecast_sales_weeks || [38, 42, 45, 50],
      turnover_rating: "HIGH",
      market_share_pct: 60,
    },
    {
      brand_name: "Regional APMC / Wholesale Alternative",
      mrp: Math.round(product.selling_price * 0.92),
      cost_price: Math.round(product.cost_price * 0.85),
      margin_pct: (
        ((product.selling_price * 0.92 - product.cost_price * 0.85) /
          Math.max(1, product.selling_price * 0.92)) *
        100
      ).toFixed(1),
      weekly_sales_avg: Math.round((product.weekly_sales_avg || 35) * 0.75),
      past_sales: [18, 20, 21, 23, 24, 26],
      forecast_sales: [28, 30, 32, 35],
      turnover_rating: "MODERATE",
      market_share_pct: 25,
    },
    {
      brand_name: "Premium Tier Competitor",
      mrp: Math.round(product.selling_price * 1.15),
      cost_price: Math.round(product.cost_price * 1.1),
      margin_pct: (
        ((product.selling_price * 1.15 - product.cost_price * 1.1) /
          Math.max(1, product.selling_price * 1.15)) *
        100
      ).toFixed(1),
      weekly_sales_avg: Math.round((product.weekly_sales_avg || 35) * 0.5),
      past_sales: [12, 13, 14, 15, 15, 16],
      forecast_sales: [18, 19, 20, 22],
      turnover_rating: "LOW",
      market_share_pct: 15,
    },
  ];

  const colors = [
    { stroke: "#2563eb", fill: "rgba(37, 99, 235, 0.15)", dot: "bg-blue-600" },
    { stroke: "#16a34a", fill: "rgba(22, 163, 74, 0.15)", dot: "bg-emerald-600" },
    { stroke: "#9333ea", fill: "rgba(147, 51, 234, 0.15)", dot: "bg-purple-600" },
  ];

  // SVG Chart Dimensions
  const W = 680;
  const H = 220;
  const padL = 40;
  const padR = 20;
  const padT = 20;
  const padB = 30;

  const activeBrands = viewMode === "SINGLE_SKU" ? [brands[0]] : brands;

  // Find max value across active brands
  let maxVal = 10;
  activeBrands.forEach((b) => {
    const all = [...(b.past_sales || []), ...(b.forecast_sales || [])];
    all.forEach((v) => {
      if (v > maxVal) maxVal = v;
    });
  });
  maxVal = Math.ceil(maxVal * 1.15);

  const totalPoints = 10; // 6 past + 4 forecast
  const stepX = (W - padL - padR) / (totalPoints - 1);

  const getY = (val) => H - padB - (val / maxVal) * (H - padT - padB);
  const getX = (idx) => padL + idx * stepX;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4 animate-in fade-in duration-150">
      <div className="relative w-full max-w-3xl rounded-2xl border bg-card shadow-2xl overflow-hidden max-h-[92vh] flex flex-col">
        {/* Modal Header */}
        <div className="flex items-center justify-between border-b px-5 py-4">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-blue-500/10 text-blue-600 dark:text-blue-400">
              <BarChart3 className="h-5 w-5" />
            </div>
            <div>
              <h3 className="font-heading font-bold text-base sm:text-lg text-foreground">
                Multi-Brand Sales & Margin Comparison
              </h3>
              <p className="text-xs text-muted-foreground">
                Comparing {product.name} against competing category brands on the exact same graph
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-1.5 text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Modal Content */}
        <div className="overflow-y-auto p-5 space-y-5">
          {/* View Toggles & Legend */}
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 bg-muted/40 p-2.5 rounded-xl border">
            <div className="flex gap-1.5">
              <button
                onClick={() => setViewMode("ALL_BRANDS")}
                className={`rounded-lg px-3 py-1 text-xs font-medium transition-all ${
                  viewMode === "ALL_BRANDS"
                    ? "bg-card text-foreground shadow-xs border"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                📊 Compare All Category Brands
              </button>
              <button
                onClick={() => setViewMode("SINGLE_SKU")}
                className={`rounded-lg px-3 py-1 text-xs font-medium transition-all ${
                  viewMode === "SINGLE_SKU"
                    ? "bg-card text-foreground shadow-xs border"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                📈 Selected SKU Only
              </button>
            </div>

            {/* Legend */}
            <div className="flex flex-wrap gap-3 text-xs">
              {activeBrands.map((b, idx) => (
                <div key={idx} className="flex items-center gap-1.5">
                  <span className={`h-2.5 w-2.5 rounded-full ${colors[idx % colors.length].dot}`} />
                  <span className="text-[11px] font-medium text-foreground truncate max-w-[150px]">
                    {b.brand_name.split("(")[0].trim()}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* SVG Comparative Graph */}
          <div className="rounded-xl border bg-background p-4 relative overflow-hidden">
            <div className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider mb-2 flex justify-between">
              <span>Weekly Units Sold (Past 6 Weeks)</span>
              <span className="text-primary font-bold">🔮 4-Week Holt-Winters Forecast</span>
            </div>

            <div className="w-full overflow-x-auto">
              <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-44 sm:h-52 overflow-visible select-none">
                {/* Horizontal grid lines */}
                {[0, 0.25, 0.5, 0.75, 1].map((pct, i) => {
                  const y = padT + (H - padT - padB) * (1 - pct);
                  const val = Math.round(maxVal * pct);
                  return (
                    <g key={i}>
                      <line x1={padL} y1={y} x2={W - padR} y2={y} stroke="currentColor" strokeOpacity="0.08" strokeDasharray="3 3" />
                      <text x={padL - 8} y={y + 3} textAnchor="end" fontSize="9" fill="currentColor" opacity="0.45">
                        {val}
                      </text>
                    </g>
                  );
                })}

                {/* Divider between past & forecast */}
                <line
                  x1={getX(5)}
                  y1={padT}
                  x2={getX(5)}
                  y2={H - padB}
                  stroke="#f59e0b"
                  strokeWidth="1.5"
                  strokeDasharray="4 4"
                />
                <text x={getX(5) + 6} y={padT + 12} fontSize="9" fill="#f59e0b" fontWeight="600">
                  Forecast Line
                </text>

                {/* Render Brand Curves */}
                {activeBrands.map((b, bIdx) => {
                  const past = b.past_sales || [];
                  const future = b.forecast_sales || [];
                  const series = [...past, ...future];
                  const c = colors[bIdx % colors.length];

                  const points = series.map((val, idx) => `${getX(idx)},${getY(val)}`).join(" ");

                  return (
                    <g key={bIdx}>
                      {/* Line */}
                      <polyline
                        points={points}
                        fill="none"
                        stroke={c.stroke}
                        strokeWidth="2.5"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      />

                      {/* Dots */}
                      {series.map((val, idx) => (
                        <circle
                          key={idx}
                          cx={getX(idx)}
                          cy={getY(val)}
                          r={idx >= 6 ? "3.5" : "3"}
                          fill={idx >= 6 ? "#ffffff" : c.stroke}
                          stroke={c.stroke}
                          strokeWidth="2"
                        />
                      ))}
                    </g>
                  );
                })}

                {/* X Axis Labels */}
                {["W1", "W2", "W3", "W4", "W5", "W6", "F1", "F2", "F3", "F4"].map((lbl, idx) => (
                  <text
                    key={idx}
                    x={getX(idx)}
                    y={H - padB + 16}
                    textAnchor="middle"
                    fontSize="10"
                    fill={idx >= 6 ? "#f59e0b" : "currentColor"}
                    fontWeight={idx >= 6 ? "650" : "500"}
                    opacity={idx >= 6 ? "1" : "0.55"}
                  >
                    {lbl}
                  </text>
                ))}
              </svg>
            </div>
          </div>

          {/* Metrics Comparison Table */}
          <div className="rounded-xl border overflow-hidden">
            <table className="w-full text-left text-xs">
              <thead className="bg-muted/40 text-muted-foreground text-[10px] uppercase font-semibold border-b">
                <tr>
                  <th className="px-3.5 py-2.5">Brand</th>
                  <th className="px-3.5 py-2.5">MRP</th>
                  <th className="px-3.5 py-2.5">Cost</th>
                  <th className="px-3.5 py-2.5">Margin %</th>
                  <th className="px-3.5 py-2.5">Weekly Units</th>
                  <th className="px-3.5 py-2.5">Market Share</th>
                  <th className="px-3.5 py-2.5 text-right">Rating</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/60">
                {brands.map((b, idx) => (
                  <tr key={idx} className="hover:bg-muted/30">
                    <td className="px-3.5 py-2.5 font-medium text-foreground flex items-center gap-2">
                      <span className={`h-2 w-2 rounded-full ${colors[idx % colors.length].dot}`} />
                      <span>{b.brand_name}</span>
                    </td>
                    <td className="px-3.5 py-2.5">₹{b.mrp}</td>
                    <td className="px-3.5 py-2.5 text-muted-foreground">₹{b.cost_price}</td>
                    <td className="px-3.5 py-2.5 font-semibold text-emerald-600 dark:text-emerald-400">
                      {b.margin_pct}%
                    </td>
                    <td className="px-3.5 py-2.5 font-medium">{b.weekly_sales_avg} / wk</td>
                    <td className="px-3.5 py-2.5 text-muted-foreground">{b.market_share_pct}%</td>
                    <td className="px-3.5 py-2.5 text-right">
                      <Badge
                        variant="outline"
                        className={`text-[10px] ${
                          b.turnover_rating === "HIGH"
                            ? "bg-emerald-500/10 text-emerald-600 border-emerald-500/30"
                            : b.turnover_rating === "MODERATE"
                            ? "bg-blue-500/10 text-blue-600 border-blue-500/30"
                            : "bg-muted text-muted-foreground"
                        }`}
                      >
                        {b.turnover_rating}
                      </Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* AI Recommendation Box */}
          <div className="rounded-xl border border-amber-500/20 bg-amber-500/5 p-3.5 flex items-start gap-3">
            <Sparkles className="h-4 w-4 text-amber-500 mt-0.5 shrink-0" />
            <div className="text-xs">
              <span className="font-semibold text-amber-800 dark:text-amber-300">
                AI Stocking & Brand Switch Recommendation:
              </span>
              <p className="text-muted-foreground mt-0.5 leading-relaxed">
                {brandData?.recommendation ||
                  `Current brand maintains healthy ${brands[0]?.margin_pct}% margins with dominant market share. Consider bundling with the wholesale alternative brand during festive weeks to preserve higher cash margins.`}
              </p>
            </div>
          </div>
        </div>

        {/* Modal Footer */}
        <div className="border-t px-5 py-3.5 flex items-center justify-between bg-muted/20">
          <Button variant="outline" size="sm" onClick={onClose} className="text-xs">
            Close
          </Button>
          <Button
            size="sm"
            onClick={() => {
              onClose();
              if (onUseInPromo) onUseInPromo(product);
            }}
            className="text-xs gap-1.5 shadow-xs"
          >
            <Sparkles className="h-3.5 w-3.5" />
            <span>Create Promo with this SKU</span>
          </Button>
        </div>
      </div>
    </div>
  );
}

