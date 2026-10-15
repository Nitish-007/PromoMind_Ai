"use client";

import React, { useState, useEffect } from "react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { CopilotQuickPrompts } from "./CopilotQuickPrompts";
import { CopilotChatThread } from "./CopilotChatThread";
import { CollateralStudio } from "./CollateralStudio";
import {
  sendChatMessage,
  publishOffer,
  fetchCalendarEvents,
  generateComboOffer,
} from "@/lib/api";

export function CopilotScreen({
  storeProfile,
  onOfferActivated,
  initialPrompt,
  onClearInitialPrompt,
}) {
  const [messages, setMessages] = useState([
    {
      sender: "bot",
      text: "Namaskara / Namaste! I am your AI Retail Copilot & Sales Growth Advisor.\n\nAsk me in plain language to diagnose slow-moving stock, design high-margin bundles, or plan regional festival campaigns:\n• \"Which product is failing or stuck on my shelves?\"\n• \"Suggest 3 best offers for this week\"\n• \"How can I increase this weekend's sales by 25%?\"\n• \"Create a Diwali sweet & dry fruit gift pack\"",
      time: "Just now",
      generation_source: "LIVE_GEMINI_API",
    },
  ]);
  const [isLoading, setIsLoading] = useState(false);
  const [activePlan, setActivePlan] = useState(null);
  const [regionalFestivals, setRegionalFestivals] = useState([]);

  useEffect(() => {
    loadRegionalFestivals();
  }, [storeProfile?.store_id, storeProfile?.region]);

  useEffect(() => {
    if (initialPrompt && initialPrompt.trim()) {
      handleSendMessage(initialPrompt.trim());
      if (onClearInitialPrompt) onClearInitialPrompt();
    }
  }, [initialPrompt]);

  const loadRegionalFestivals = async () => {
    try {
      const reg = storeProfile?.region ? storeProfile.region.split("&")[0].trim() : "Karnataka";
      const events = await fetchCalendarEvents(reg, false, storeProfile?.country || "India", storeProfile?.city || "");
      if (Array.isArray(events)) {
        setRegionalFestivals(events.slice(0, 3));
      }
    } catch (e) {
      console.warn("Could not load regional festivals for Copilot:", e);
    }
  };

  const formatTime = () => {
    const d = new Date();
    let hours = d.getHours();
    const minutes = d.getMinutes().toString().padStart(2, "0");
    const ampm = hours >= 12 ? "PM" : "AM";
    hours = hours % 12 || 12;
    return `${hours}:${minutes} ${ampm}`;
  };

  const handleSendMessage = async (userText) => {
    setMessages((prev) => [
      ...prev,
      { sender: "user", text: userText, time: formatTime() },
    ]);

    setIsLoading(true);
    try {
      const data = await sendChatMessage(userText, storeProfile?.region);

      if (Array.isArray(data.regional_festivals) && data.regional_festivals.length > 0) {
        setRegionalFestivals(data.regional_festivals.slice(0, 3));
      }

      setMessages((prev) => [
        ...prev,
        {
          sender: "bot",
          text: data.reply || "I analyzed your request and computed store metrics.",
          plan: data.plan,
          ideas: data.ideas,
          sales_growth_plan: data.sales_growth_plan,
          regional_festivals: data.regional_festivals,
          generation_source: data.generation_source || "LIVE_GEMINI_API",
          time: formatTime(),
        },
      ]);

      if (data.plan) {
        setActivePlan(data.plan);
      }
    } catch (err) {
      console.error("Copilot error:", err);
      setMessages((prev) => [
        ...prev,
        {
          sender: "bot",
          text: "Sorry, I encountered an issue connecting to the store engine. Please try again.",
          time: formatTime(),
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleLoadIdeaIntoStudio = async (idea) => {
    setIsLoading(true);
    try {
      const plan = await generateComboOffer({
        prompt: `${idea.title}: ${idea.anchor_name} + ${idea.attached_name}`,
        min_margin_pct: idea.net_margin_pct || 18.0,
        event_theme: idea.event_theme || "Weekly Retail Deal",
        archetype: idea.archetype || "ANCHOR_MARGIN_BOOSTER",
        primary_product_id: idea.anchor_id,
        secondary_product_id: idea.attached_id,
        region: storeProfile?.region,
      });
      if (plan) {
        setActivePlan(plan);
      }
    } catch (e) {
      console.error("Failed to load idea plan:", e);
    } finally {
      setIsLoading(false);
    }
  };

  const handleClearHistory = () => {
    setMessages([
      {
        sender: "bot",
        text: "Namaskara / Namaste! Conversation reset. How can I assist your store today?",
        time: formatTime(),
      },
    ]);
    setActivePlan(null);
  };

  const handleScheduleOffer = async (variety) => {
    try {
      await publishOffer({
        combo_id: variety.id || variety.variety_id || "COMBO_COPILOT",
        title: variety.title,
        anchor_id: activePlan?.anchor_product?.id || "PROD_TEA_01",
        attached_id: activePlan?.attached_product?.id || "PROD_BISCUIT_01",
        anchor_name: activePlan?.anchor_product?.name,
        attached_name: activePlan?.attached_product?.name,
        price: variety.combo_price,
        original_mrp: variety.original_mrp || activePlan?.original_combined_mrp,
        discount_pct: variety.discount_pct,
        net_margin_pct: variety.net_margin_pct,
        event_theme: activePlan?.event_theme || "Active Campaign",
        status: variety.status || "ACTIVE",
        start_date: variety.start_date || "2026-10-15",
        end_date: variety.end_date || "2026-10-25",
        whatsapp_copy: variety.whatsapp_copy,
        cashier_pitch: variety.cashier_pitch,
      });
      if (onOfferActivated) onOfferActivated();
    } catch (e) {
      console.error("Failed to publish offer:", e);
      alert("Failed to save offer. Please try again.");
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-foreground">
            AI Retail Copilot &amp; Sales Growth Advisor
          </h2>
          <p className="text-xs sm:text-sm text-muted-foreground mt-0.5">
            Live Gemini AI reasoning integrated with your store&apos;s Regional Festivals, Price Elasticity, and Working Capital ROI.
          </p>
        </div>

        <Badge variant="outline" className="text-xs py-1 px-3 font-medium border-border w-fit">
          {storeProfile?.store_name || "Store"} • {storeProfile?.city || "Bengaluru"} ({storeProfile?.region?.split("&")[0]?.trim() || "Karnataka"})
        </Badge>
      </div>

      {/* Regional Festivals Integration Strip inside Copilot */}
      {regionalFestivals.length > 0 && (
        <Card className="border border-border bg-muted/20">
          <CardContent className="p-3.5 sm:p-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-2.5">
              <div>
                <span className="text-xs font-bold uppercase tracking-wider text-foreground">
                  Stored Regional Festival Triggers ({storeProfile?.region?.split("&")[0]?.trim() || "Active Region"}):
                </span>
                <span className="text-xs text-muted-foreground ml-2">
                  Click any upcoming festival to generate a targeted store bundle
                </span>
              </div>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-2.5">
              {regionalFestivals.map((fest, idx) => (
                <button
                  key={fest.id || idx}
                  type="button"
                  disabled={isLoading}
                  onClick={() =>
                    handleSendMessage(
                      `Create a high-margin festival combo offer for ${fest.name} (${fest.suggested_combo_title || "Festive Special"})`
                    )
                  }
                  className="text-left p-3 rounded-lg border border-border bg-card hover:bg-muted/60 hover:border-foreground/40 transition-colors flex flex-col justify-between gap-1.5"
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-xs font-bold text-foreground truncate">
                      {fest.name.split("(")[0].trim()}
                    </span>
                    <Badge variant="outline" className="text-[10px] px-1.5 py-0 font-semibold shrink-0">
                      +{Math.round(fest.demand_lift_pct)}% Surge
                    </Badge>
                  </div>
                  <div className="text-[11px] text-muted-foreground truncate">
                    {fest.date_window} • {fest.key_items?.slice(0, 2).join(", ")}
                  </div>
                </button>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* 1-Click Quick Prompts Strip */}
      <CopilotQuickPrompts
        onSelectPrompt={handleSendMessage}
        disabled={isLoading}
      />

      {/* Two-Pane Workspace: Chat Thread on Left, Collateral Studio on Right */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">
        <CopilotChatThread
          messages={messages}
          isLoading={isLoading}
          onSendMessage={handleSendMessage}
          onClearHistory={handleClearHistory}
          onLoadPlanDirect={(plan) => setActivePlan(plan)}
          onLoadIdeaDirect={handleLoadIdeaIntoStudio}
        />

        <CollateralStudio
          plan={activePlan}
          storeProfile={storeProfile}
          onScheduleOffer={handleScheduleOffer}
        />
      </div>
    </div>
  );
}
