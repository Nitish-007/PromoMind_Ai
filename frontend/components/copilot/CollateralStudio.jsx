"use client";

import React, { useState } from "react";
import {
  MessageSquare,
  Printer,
  Copy,
  Send,
  Check,
  Brain,
  ChevronRight,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";

export function CollateralStudio({ plan, storeProfile, onScheduleOffer }) {
  const [activeTab, setActiveTab] = useState("whatsapp");
  const [copiedType, setCopiedType] = useState(null);
  const [selectedVarietyIdx, setSelectedVarietyIdx] = useState(0);

  // Campaign Schedule & Status Configurator
  const [campaignStatus, setCampaignStatus] = useState("ACTIVE"); // "ACTIVE" | "SCHEDULED"
  const [startDate, setStartDate] = useState("2026-10-15");
  const [endDate, setEndDate] = useState("2026-10-25");
  const [dispatching, setDispatching] = useState(false);

  if (!plan) {
    return (
      <div className="flex flex-col items-center justify-center h-[620px] rounded-2xl border border-dashed border-border bg-card/50 p-8 text-center space-y-3">
        <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-muted text-muted-foreground">
          <MessageSquare className="h-6 w-6" />
        </div>
        <h3 className="font-heading font-bold text-base sm:text-lg text-foreground">
          Campaign Collateral Studio &amp; Offer Scheduler
        </h3>
        <p className="max-w-md text-xs sm:text-sm text-muted-foreground leading-relaxed">
          Ask the AI Copilot on the left to suggest an offer or click a regional festival trigger above. Your{" "}
          <strong>
            customer-ready WhatsApp broadcasts, in-store posters, cashier scripts, and campaign scheduling controls
          </strong>{" "}
          will materialize here.
        </p>
      </div>
    );
  }

  const storeName = storeProfile?.store_name || "Sharma Supermarket & Kirana";
  const storeCity = storeProfile?.city || "Bengaluru";
  const broadcastReach =
    storeProfile?.whatsapp_audience_size || storeProfile?.audience_size || 1420;

  const varieties = plan.varieties || [];
  const currentVariety = varieties[selectedVarietyIdx] || {
    id: plan.combo_id || "COMBO_DEFAULT",
    title: plan.title,
    combo_price: plan.recommended_combo_price || plan.combo_price,
    discount_amount: plan.discount_amount || 0,
    discount_pct: plan.discount_pct || 15,
    net_margin_pct: plan.net_margin_pct || 18,
    projected_volume_lift_pct: plan.roi_prediction?.units_lift_pct || 25,
    capital_turnover_days: plan.capital_turnover_days || 4,
    customer_target: plan.target_customer_segment || "Everyday Shoppers",
    whatsapp_copy:
      plan.creative_assets?.whatsapp_message ||
      "Festive offer available now!",
    poster_headline: plan.creative_assets?.poster_headline || plan.title,
    poster_subheading:
      plan.creative_assets?.poster_subheading || `Special Deal at ${storeName}`,
    poster_badge:
      plan.creative_assets?.poster_badge ||
      plan.event_theme ||
      "FESTIVE COMBO",
    poster_savings: `YOU SAVE ₹${Math.round(plan.discount_amount || 0)} (${plan.discount_pct || 15}% OFF)`,
    cashier_counter_pitch:
      plan.creative_assets?.cashier_counter_pitch ||
      plan.creative_assets?.pos_tagline ||
      "Sir, get flat savings on this combo!",
  };

  const cashierText =
    currentVariety.cashier_counter_pitch ||
    currentVariety.cashier_script ||
    plan.creative_assets?.cashier_counter_pitch ||
    plan.creative_assets?.pos_tagline;

  const handleCopy = (text, type) => {
    navigator.clipboard.writeText(text);
    setCopiedType(type);
    setTimeout(() => setCopiedType(null), 2000);
  };

  const handleDispatch = async () => {
    if (!onScheduleOffer) return;
    setDispatching(true);
    try {
      await onScheduleOffer({
        ...currentVariety,
        status: campaignStatus,
        start_date: startDate,
        end_date: endDate,
        whatsapp_copy: currentVariety.whatsapp_copy,
        cashier_pitch: cashierText,
      });
    } finally {
      setDispatching(false);
    }
  };

  return (
    <div className="flex flex-col h-[620px] rounded-2xl border border-border bg-card shadow-xs overflow-hidden">
      {/* Studio Header */}
      <div className="border-b border-border px-4 py-3 bg-card flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-sm sm:text-base font-bold text-foreground">
              {currentVariety.title}
            </h3>
            <Badge
              variant="outline"
              className="text-xs font-semibold text-emerald-600 dark:text-emerald-400 border-border"
            >
              {currentVariety.net_margin_pct}% Margin
            </Badge>
          </div>
          <p className="text-xs text-muted-foreground mt-0.5">
            Target: {currentVariety.customer_target} • Unlocked in{" "}
            {currentVariety.capital_turnover_days} days
          </p>
        </div>

        {/* Omnichannel View Tabs */}
        <div className="flex gap-1 bg-muted p-1 rounded-lg border border-border text-xs">
          <button
            onClick={() => setActiveTab("whatsapp")}
            className={`rounded-md px-2.5 py-1 font-medium transition-colors ${
              activeTab === "whatsapp"
                ? "bg-card text-foreground shadow-xs"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            WhatsApp
          </button>
          <button
            onClick={() => setActiveTab("poster")}
            className={`rounded-md px-2.5 py-1 font-medium transition-colors ${
              activeTab === "poster"
                ? "bg-card text-foreground shadow-xs"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            In-Store Poster
          </button>
          <button
            onClick={() => setActiveTab("cashier")}
            className={`rounded-md px-2.5 py-1 font-medium transition-colors ${
              activeTab === "cashier"
                ? "bg-card text-foreground shadow-xs"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            Cashier Script
          </button>
        </div>
      </div>

      {/* Main Studio Body */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* Dynamic Varieties Selector */}
        {varieties.length > 1 && (
          <div className="space-y-1.5">
            <span className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">
              AI Dynamic Elasticity Matrix ({varieties.length} Variations):
            </span>
            <div className="grid grid-cols-2 sm:grid-cols-5 gap-1.5">
              {varieties.map((v, i) => (
                <button
                  key={i}
                  type="button"
                  onClick={() => setSelectedVarietyIdx(i)}
                  className={`rounded-lg border p-2 text-left text-xs transition-colors ${
                    i === selectedVarietyIdx
                      ? "border-foreground bg-muted font-semibold"
                      : "border-border bg-card hover:bg-muted/40 text-muted-foreground"
                  }`}
                >
                  <div className="truncate font-medium text-foreground text-[11px]">
                    {v.title}
                  </div>
                  <div className="text-[10px] mt-0.5">
                    ₹{Math.round(v.combo_price)} • {v.net_margin_pct}%
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Tab 1: WhatsApp Broadcast (Dynamically Grounded in Store Profile & CSV Broadcast Reach) */}
        {activeTab === "whatsapp" && (
          <div className="space-y-3">
            <div className="rounded-xl border border-border bg-muted/20 p-4 space-y-3">
              <div className="flex items-center justify-between text-xs text-muted-foreground border-b pb-2">
                <span className="font-medium text-foreground">
                  WhatsApp Broadcast Preview
                </span>
                <span>
                  {storeName} ({broadcastReach.toLocaleString("en-IN")} Verified Customers)
                </span>
              </div>
              <div className="rounded-lg bg-card border border-border p-3.5 text-xs sm:text-sm font-sans leading-relaxed whitespace-pre-wrap">
                {currentVariety.whatsapp_copy}
              </div>
            </div>

            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() =>
                  handleCopy(currentVariety.whatsapp_copy, "whatsapp")
                }
                className="gap-1.5 text-xs h-9 flex-1"
              >
                {copiedType === "whatsapp" ? (
                  <Check className="h-4 w-4 text-emerald-500" />
                ) : (
                  <Copy className="h-4 w-4" />
                )}
                <span>
                  {copiedType === "whatsapp"
                    ? "Copied!"
                    : "Copy Broadcast Text"}
                </span>
              </Button>
              <Button
                render={
                  <a
                    href={`https://api.whatsapp.com/send?text=${encodeURIComponent(currentVariety.whatsapp_copy)}`}
                    target="_blank"
                    rel="noopener noreferrer"
                  />
                }
                size="sm"
                className="gap-1.5 text-xs h-9 flex-1 bg-emerald-600 hover:bg-emerald-700 text-white font-medium"
              >
                <Send className="h-4 w-4" />
                <span>Share via WhatsApp</span>
              </Button>
            </div>
          </div>
        )}

        {/* Tab 2: In-Store Printable Poster */}
        {activeTab === "poster" && (
          <div className="space-y-3">
            <div className="rounded-xl border border-border bg-card p-6 text-center space-y-3 shadow-xs">
              <Badge
                variant="outline"
                className="text-xs uppercase tracking-widest px-3 py-1 font-bold"
              >
                {currentVariety.poster_badge || plan.event_theme}
              </Badge>
              <h2 className="text-xl sm:text-2xl font-black tracking-tight text-foreground uppercase">
                {currentVariety.poster_headline}
              </h2>
              <p className="text-xs sm:text-sm text-muted-foreground font-medium">
                {currentVariety.poster_subheading || `${storeName}, ${storeCity}`}
              </p>
              <div className="py-2 flex items-baseline justify-center gap-3">
                <span className="text-3xl font-black text-foreground">
                  ₹{Math.round(currentVariety.combo_price)}
                </span>
                <span className="text-sm font-semibold text-muted-foreground line-through">
                  MRP ₹{Math.round(plan.original_combined_mrp || 0)}
                </span>
              </div>
              <div className="text-xs font-bold uppercase tracking-wider text-emerald-600 dark:text-emerald-400">
                {currentVariety.poster_savings}
              </div>
              <div className="pt-3 border-t text-[11px] text-muted-foreground flex justify-between items-center font-mono">
                <span>{storeName} • {storeCity}</span>
                <span>POS BARCODE ||||||||||||</span>
              </div>
            </div>

            <Button
              variant="outline"
              size="sm"
              onClick={() => window.print()}
              className="w-full text-xs h-9 gap-1.5"
            >
              <Printer className="h-4 w-4" />
              <span>Print Counter Poster</span>
            </Button>
          </div>
        )}

        {/* Tab 3: Cashier Script */}
        {activeTab === "cashier" && (
          <div className="space-y-3">
            <div className="rounded-xl border border-border bg-muted/20 p-4 space-y-3">
              <div className="text-xs font-medium text-foreground">
                Cashier Counter Script (POS Upsell Script)
              </div>
              <div className="rounded-lg bg-card border border-border p-3.5 text-xs sm:text-sm italic leading-relaxed text-foreground">
                &ldquo;{cashierText}&rdquo;
              </div>
              <p className="text-[11px] text-muted-foreground">
                <strong>Rupee Savings Anchor:</strong> Speaking precise rupee savings (&ldquo;Save flat ₹{Math.round(currentVariety.discount_amount)}&rdquo;) boosts POS conversion by up to 2.3x compared to percentage claims.
              </p>
            </div>

            <Button
              variant="outline"
              size="sm"
              onClick={() => handleCopy(cashierText, "cashier")}
              className="w-full text-xs h-9 gap-1.5"
            >
              {copiedType === "cashier" ? (
                <Check className="h-4 w-4 text-emerald-500" />
              ) : (
                <Copy className="h-4 w-4" />
              )}
              <span>
                {copiedType === "cashier" ? "Copied!" : "Copy Cashier Script"}
              </span>
            </Button>
          </div>
        )}

        {/* Campaign Launch Mode & Schedule Window Selector */}
        <div className="rounded-xl border border-border bg-muted/30 p-3.5 space-y-3 text-xs">
          <div className="flex items-center justify-between">
            <span className="font-semibold text-foreground">
              Store Campaign Schedule &amp; Persistence (Firestore):
            </span>
            <div className="flex gap-1 bg-card p-0.5 rounded-md border border-border">
              <button
                type="button"
                onClick={() => setCampaignStatus("ACTIVE")}
                className={`px-2 py-1 rounded text-[11px] font-semibold transition-colors ${
                  campaignStatus === "ACTIVE"
                    ? "bg-foreground text-background"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                Launch Active Now
              </button>
              <button
                type="button"
                onClick={() => {
                  setCampaignStatus("SCHEDULED");
                  setStartDate("2026-10-22");
                  setEndDate("2026-10-30");
                }}
                className={`px-2 py-1 rounded text-[11px] font-semibold transition-colors ${
                  campaignStatus === "SCHEDULED"
                    ? "bg-foreground text-background"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                Schedule for Later
              </button>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-2.5">
            <div className="space-y-1">
              <label className="text-[11px] text-muted-foreground">Start Date:</label>
              <Input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="h-8 text-xs bg-card"
              />
            </div>
            <div className="space-y-1">
              <label className="text-[11px] text-muted-foreground">End Date:</label>
              <Input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="h-8 text-xs bg-card"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Studio Dispatch Footer */}
      <div className="border-t border-border p-3 bg-card">
        <Button
          size="sm"
          disabled={dispatching}
          onClick={handleDispatch}
          className="w-full h-10 text-sm font-semibold gap-2 shadow-xs"
        >
          <span>
            {dispatching
              ? "Saving Campaign to Firestore..."
              : campaignStatus === "ACTIVE"
              ? `Activate Offer Now & Broadcast (${broadcastReach.toLocaleString("en-IN")} Customers)`
              : `Save as Scheduled Offer (${startDate} to ${endDate})`}
          </span>
          <ChevronRight className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}
