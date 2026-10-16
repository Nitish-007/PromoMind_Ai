"use client";

import React, { useState } from "react";
import { 
  DollarSign, 
  TrendingUp, 
  AlertTriangle, 
  Zap, 
  Sparkles, 
  SlidersHorizontal,
  ChevronDown,
  ChevronUp
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

export function FinancialRoiCard({ roiData, onSimulate, isSimulating }) {
  const [showSim, setShowSim] = useState(false);
  const [discountPct, setDiscountPct] = useState(16);
  const [volumeLiftPct, setVolumeLiftPct] = useState(35);
  const [simResult, setSimResult] = useState(null);

  const handleSliderChange = async (newDiscount, newVolume) => {
    setDiscountPct(newDiscount);
    setVolumeLiftPct(newVolume);
    if (onSimulate) {
      const res = await onSimulate(newDiscount, newVolume);
      setSimResult(res);
    }
  };

  const invested = roiData?.capital_invested_inr ?? 245000;
  const projectedTurnover = roiData?.projected_30d_turnover_inr ?? 318000;
  const projectedProfit = roiData?.projected_net_profit_inr ?? 58400;
  const netRoiPct = roiData?.net_return_pct ?? 23.8;
  const deadCapital = roiData?.dead_capital_at_risk_inr ?? 18500;
  const unlockedCash = roiData?.unlocked_cash_via_promos_inr ?? 34200;

  return (
    <Card className="border border-border shadow-xs bg-card">
      <CardHeader className="pb-3 border-b border-border">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-start gap-3">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md bg-muted text-foreground border border-border">
              <DollarSign className="h-5 w-5" />
            </div>
            <div>
              <CardTitle className="text-base sm:text-lg font-bold flex items-center gap-2">
                <span>Store Capital Investment & Returns</span>
                <Badge variant="outline" className="text-xs font-medium border-border text-muted-foreground">
                  Financial Intel
                </Badge>
              </CardTitle>
              <CardDescription className="text-xs sm:text-sm text-muted-foreground mt-0.5">
                Holt-Winters forecasting: Turnover, net gross profit, dead capital risk, and unlocked promo cash.
              </CardDescription>
            </div>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              const next = !showSim;
              setShowSim(next);
              if (next && !simResult) {
                handleSliderChange(discountPct, volumeLiftPct);
              }
            }}
            className="shrink-0 gap-1.5 text-xs sm:text-sm h-9 px-3"
          >
            <SlidersHorizontal className="h-4 w-4" />
            <span>{showSim ? "Hide Simulator" : 'ROI Simulator'}</span>
            {showSim ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
          </Button>
        </div>
      </CardHeader>

      <CardContent className="pt-4">
        {/* Key Metric Tiles */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          {/* Capital Invested */}
          <div className="rounded-lg border border-border bg-card p-3.5 transition-colors hover:bg-muted/40">
            <div className="text-xs font-medium text-muted-foreground">Total Invested</div>
            <div className="text-lg sm:text-xl font-bold tracking-tight text-foreground mt-1">
              ₹{invested.toLocaleString("en-IN")}
            </div>
            <div className="text-xs text-muted-foreground mt-0.5">Store Inventory</div>
          </div>

          {/* 30-Day Turnover */}
          <div className="rounded-lg border border-border bg-card p-3.5 transition-colors hover:bg-muted/40">
            <div className="text-xs font-medium text-muted-foreground">30-Day Turnover</div>
            <div className="text-lg sm:text-xl font-bold tracking-tight text-foreground mt-1">
              ₹{projectedTurnover.toLocaleString("en-IN")}
            </div>
            <div className="text-xs text-muted-foreground mt-0.5">Projected</div>
          </div>

          {/* Net Profit */}
          <div className="rounded-lg border border-border bg-card p-3.5 transition-colors hover:bg-muted/40">
            <div className="text-xs font-medium text-muted-foreground">Net Store Profit</div>
            <div className="text-lg sm:text-xl font-bold tracking-tight text-foreground mt-1">
              ₹{projectedProfit.toLocaleString("en-IN")}
            </div>
            <div className="text-xs font-semibold text-emerald-600 dark:text-emerald-400 mt-0.5">
              +{netRoiPct}% ROI
            </div>
          </div>

          {/* Dead Capital at Risk */}
          <div className="rounded-lg border border-border bg-card p-3.5 transition-colors hover:bg-muted/40">
            <div className="text-xs font-medium text-muted-foreground">Dead Capital Risk</div>
            <div className="text-lg sm:text-xl font-bold tracking-tight text-foreground mt-1">
              ₹{deadCapital.toLocaleString("en-IN")}
            </div>
            <div className="text-xs text-muted-foreground mt-0.5">Slow movers (&gt;60d)</div>
          </div>

          {/* Cash Unlocked */}
          <div className="rounded-lg border border-border bg-card p-3.5 transition-colors hover:bg-muted/40 col-span-2 md:col-span-1">
            <div className="text-xs font-medium text-muted-foreground">Unlocked via Promos</div>
            <div className="text-lg sm:text-xl font-bold tracking-tight text-foreground mt-1">
              ₹{unlockedCash.toLocaleString("en-IN")}
            </div>
            <div className="text-xs text-muted-foreground mt-0.5">Net Promo Boost</div>
          </div>
        </div>

        {/* What-If Simulator Drawer */}
        {showSim && (
          <div className="mt-4 rounded-xl border border-primary/20 bg-muted/40 p-4 animate-in fade-in slide-in-from-top-2 duration-200">
            <div className="mb-3">
              <h4 className="text-xs sm:text-sm font-semibold flex items-center gap-1.5 text-foreground">
                <Sparkles className="h-4 w-4 text-amber-500" />
                <span>Interactive &quot;What-If&quot; Retail ROI Scenario Simulator</span>
              </h4>
              <p className="text-xs text-muted-foreground mt-0.5">
                Simulate how adjusting promotional discount depth and expected sales volume changes your net profit rupees and cash turnover cycle:
              </p>
            </div>

            {/* Slider Controls */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 my-3">
              <div className="space-y-1.5 bg-background p-3 rounded-lg border">
                <div className="flex justify-between items-center text-xs">
                  <span className="font-medium text-foreground">Proposed Promotional Discount Depth:</span>
                  <Badge variant="secondary" className="font-bold text-primary">
                    {discountPct}% OFF
                  </Badge>
                </div>
                <input
                  type="range"
                  min="5"
                  max="30"
                  step="1"
                  value={discountPct}
                  onChange={(e) => handleSliderChange(parseInt(e.target.value), volumeLiftPct)}
                  className="w-full accent-primary h-1.5 bg-muted rounded-lg cursor-pointer"
                />
                <div className="flex justify-between text-[10px] text-muted-foreground">
                  <span>5% (Conservative)</span>
                  <span>15% (Balanced)</span>
                  <span>30% (Aggressive Clearance)</span>
                </div>
              </div>

              <div className="space-y-1.5 bg-background p-3 rounded-lg border">
                <div className="flex justify-between items-center text-xs">
                  <span className="font-medium text-foreground">Expected Sales Volume Lift:</span>
                  <Badge variant="secondary" className="font-bold text-emerald-600 dark:text-emerald-400">
                    +{volumeLiftPct}% Units
                  </Badge>
                </div>
                <input
                  type="range"
                  min="10"
                  max="80"
                  step="5"
                  value={volumeLiftPct}
                  onChange={(e) => handleSliderChange(discountPct, parseInt(e.target.value))}
                  className="w-full accent-emerald-500 h-1.5 bg-muted rounded-lg cursor-pointer"
                />
                <div className="flex justify-between text-[10px] text-muted-foreground">
                  <span>+10%</span>
                  <span>+40%</span>
                  <span>+80%</span>
                </div>
              </div>
            </div>

            {/* Simulation Results Strip */}
            <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 pt-2 border-t border-border/60">
              <div className="bg-background/80 p-2.5 rounded-lg border text-center">
                <div className="text-[10px] text-muted-foreground font-medium">Simulated Turnover</div>
                <div className="text-sm font-bold text-foreground mt-0.5">
                  ₹{(simResult?.simulated_turnover_inr ?? (projectedTurnover * (1 + volumeLiftPct / 100) * (1 - discountPct / 100))).toLocaleString("en-IN", { maximumFractionDigits: 0 })}
                </div>
              </div>

              <div className="bg-background/80 p-2.5 rounded-lg border text-center">
                <div className="text-[10px] text-muted-foreground font-medium">Simulated Net Profit</div>
                <div className="text-sm font-bold text-emerald-600 dark:text-emerald-400 mt-0.5">
                  ₹{(simResult?.simulated_net_profit_inr ?? (projectedProfit * (1 + (volumeLiftPct * 0.7 - discountPct * 0.9) / 100))).toLocaleString("en-IN", { maximumFractionDigits: 0 })}
                </div>
              </div>

              <div className="bg-background/80 p-2.5 rounded-lg border text-center">
                <div className="text-[10px] text-muted-foreground font-medium">Effective ROI</div>
                <div className="text-sm font-bold text-foreground mt-0.5">
                  {(simResult?.effective_roi_pct ?? (netRoiPct + (volumeLiftPct * 0.2 - discountPct * 0.25))).toFixed(1)}%
                </div>
              </div>

              <div className="bg-background/80 p-2.5 rounded-lg border text-center">
                <div className="text-[10px] text-muted-foreground font-medium">Capital Speedup</div>
                <div className="text-sm font-bold text-blue-600 dark:text-blue-400 mt-0.5">
                  {simResult?.turnover_speedup_days ?? Math.round(volumeLiftPct * 0.22)} Days Faster
                </div>
              </div>

              <div className="bg-background/80 p-2.5 rounded-lg border text-center col-span-2 sm:col-span-1 flex flex-col justify-center items-center">
                <div className="text-[10px] text-muted-foreground font-medium">Verdict</div>
                <Badge variant="outline" className="mt-0.5 text-[10px] bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/30">
                  PROFIT POSITIVE
                </Badge>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

