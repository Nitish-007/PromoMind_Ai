"use client";

import React, { useState } from "react";
import {
    Sparkles,
    MessageSquare,
    Printer,
    Copy,
    Send,
    Check,
    ShieldCheck,
    TrendingUp,
    Brain,
    Layers,
    ChevronRight,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

export function CollateralStudio({ plan, onScheduleOffer }) {
    const [activeTab, setActiveTab] = useState("whatsapp"); // 'whatsapp' | 'poster' | 'cashier'
    const [copiedType, setCopiedType] = useState(null);
    const [selectedVarietyIdx, setSelectedVarietyIdx] = useState(0);

    if (!plan) {
        return (
            <div className="flex flex-col items-center justify-center h-[600px] rounded-2xl border border-dashed border-border bg-card/50 p-8 text-center space-y-3">
                <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-muted text-muted-foreground">
                    <MessageSquare className="h-6 w-6" />
                </div>
                <h3 className="font-heading font-bold text-base sm:text-lg text-foreground">
                    Campaign Collateral Studio
                </h3>
                <p className="max-w-md text-xs sm:text-sm text-muted-foreground leading-relaxed">
                    Ask the AI Copilot on the left to suggest an offer or rescue
                    stuck stock. Your{" "}
                    <strong>
                        customer-ready WhatsApp broadcasts, in-store posters,
                        and cashier upsell scripts
                    </strong>{" "}
                    will materialize here instantly.
                </p>
            </div>
        );
    }

    const varieties = plan.varieties || [];
    const currentVariety = varieties[selectedVarietyIdx] || {
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
            plan.creative_assets?.poster_subheading || "Special Deal",
        poster_badge:
            plan.creative_assets?.poster_badge ||
            plan.event_theme ||
            "FESTIVE COMBO",
        poster_savings: `YOU SAVE ₹${Math.round(plan.discount_amount || 0)} (${plan.discount_pct || 15}% OFF)`,
        cashier_script:
            plan.creative_assets?.pos_tagline ||
            `Sir, get flat savings on this combo!`,
    };

    const handleCopy = (text, type) => {
        navigator.clipboard.writeText(text);
        setCopiedType(type);
        setTimeout(() => setCopiedType(null), 2000);
    };

    return (
        <div className="flex flex-col h-[600px] rounded-2xl border border-border bg-card shadow-xs overflow-hidden">
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
                {/* Dynamic Varieties Selector if multiple */}
                {varieties.length > 1 && (
                    <div className="space-y-1.5">
                        <span className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">
                            AI Dynamic Elasticity Matrix ({varieties.length}{" "}
                            Variations):
                        </span>
                        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
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
                                    <div className="truncate font-medium text-foreground">
                                        {v.title}
                                    </div>
                                    <div className="text-[11px] mt-0.5">
                                        ₹{Math.round(v.combo_price)} •{" "}
                                        {v.net_margin_pct}% margin
                                    </div>
                                </button>
                            ))}
                        </div>
                    </div>
                )}

                {/* Tab 1: WhatsApp Broadcast */}
                {activeTab === "whatsapp" && (
                    <div className="space-y-3">
                        <div className="rounded-xl border border-border bg-muted/20 p-4 space-y-3">
                            <div className="flex items-center justify-between text-xs text-muted-foreground border-b pb-2">
                                <span className="font-medium text-foreground">
                                    WhatsApp Broadcast Preview
                                </span>
                                <span>
                                    Sharma Store Customer List (1,420 Retail
                                    Customers)
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
                                    handleCopy(
                                        currentVariety.whatsapp_copy,
                                        "whatsapp",
                                    )
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
                                size="sm"
                                className="gap-1.5 text-xs h-9 flex-1 bg-emerald-600 hover:bg-emerald-700 text-white font-medium"
                            >
                                <Link
                                    href={`https://api.whatsapp.com/send?text=${encodeURIComponent(currentVariety.whatsapp_copy)}`}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                />

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
                                {currentVariety.poster_badge}
                            </Badge>
                            <h2 className="text-xl sm:text-2xl font-black tracking-tight text-foreground uppercase">
                                {currentVariety.poster_headline}
                            </h2>
                            <p className="text-xs sm:text-sm text-muted-foreground font-medium">
                                {currentVariety.poster_subheading}
                            </p>
                            <div className="py-2 flex items-baseline justify-center gap-3">
                                <span className="text-3xl font-black text-foreground">
                                    ₹{Math.round(currentVariety.combo_price)}
                                </span>
                                <span className="text-sm font-semibold text-muted-foreground line-through">
                                    MRP ₹
                                    {Math.round(
                                        plan.original_combined_mrp || 0,
                                    )}
                                </span>
                            </div>
                            <div className="text-xs font-bold uppercase tracking-wider text-emerald-600 dark:text-emerald-400">
                                {currentVariety.poster_savings}
                            </div>
                            <div className="pt-3 border-t text-[11px] text-muted-foreground flex justify-between items-center font-mono">
                                <span>Sharma Supermarket • Bengaluru</span>
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
                                &ldquo;{currentVariety.cashier_script}&rdquo;
                            </div>
                            <p className="text-[11px] text-muted-foreground">
                                💡 <strong>Rupee Savings Anchor:</strong>{" "}
                                Speaking precise rupee savings (&ldquo;Save flat
                                ₹{Math.round(currentVariety.discount_amount)}
                                &rdquo;) boosts Indian POS conversion by up to
                                2.3x compared to percentage claims.
                            </p>
                        </div>

                        <Button
                            variant="outline"
                            size="sm"
                            onClick={() =>
                                handleCopy(
                                    currentVariety.cashier_script,
                                    "cashier",
                                )
                            }
                            className="w-full text-xs h-9 gap-1.5"
                        >
                            {copiedType === "cashier" ? (
                                <Check className="h-4 w-4 text-emerald-500" />
                            ) : (
                                <Copy className="h-4 w-4" />
                            )}
                            <span>
                                {copiedType === "cashier"
                                    ? "Copied!"
                                    : "Copy Cashier Script"}
                            </span>
                        </Button>
                    </div>
                )}

                {/* Neuro-Symbolic Hybrid Architecture Card */}
                <div className="rounded-xl border border-border bg-muted/30 p-3.5 space-y-2 text-xs">
                    <div className="flex items-center gap-2">
                        <Brain className="h-4 w-4 text-muted-foreground" />
                        <span className="font-semibold text-foreground">
                            Neuro-Symbolic Hybrid Guardrails
                        </span>
                    </div>
                    <div className="grid grid-cols-2 gap-2 text-[11px] text-muted-foreground">
                        <div className="rounded-lg border bg-card p-2 space-y-1">
                            <span className="font-medium text-foreground block">
                                1. Generative AI (Gemini)
                            </span>
                            <span>
                                Regional festive context, colloquial phrasing &
                                psychology
                            </span>
                        </div>
                        <div className="rounded-lg border bg-card p-2 space-y-1">
                            <span className="font-medium text-foreground block">
                                2. Math Optimization
                            </span>
                            <span>
                                Price Elasticity: -1.45 • Margin preserved:{" "}
                                {currentVariety.net_margin_pct}%
                            </span>
                        </div>
                    </div>
                </div>
            </div>

            {/* Studio Dispatch Footer */}
            <div className="border-t border-border p-3 bg-card">
                <Button
                    size="sm"
                    onClick={() => onScheduleOffer(currentVariety)}
                    className="w-full h-10 text-sm font-semibold gap-2 shadow-xs"
                >
                    <span>Schedule & Activate Offer in Calendar</span>
                    <ChevronRight className="h-4 w-4" />
                </Button>
            </div>
        </div>
    );
}
