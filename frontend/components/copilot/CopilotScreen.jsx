"use client";

import React, { useState, useEffect } from "react";
import { Sparkles } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { CopilotQuickPrompts } from "./CopilotQuickPrompts";
import { CopilotChatThread } from "./CopilotChatThread";
import { CollateralStudio } from "./CollateralStudio";
import { sendChatMessage, publishOffer } from "@/lib/api";

export function CopilotScreen({ storeProfile, onOfferActivated, initialPrompt, onClearInitialPrompt }) {
  const [messages, setMessages] = useState([
    {
      sender: "bot",
      text: "Namaskara / Namaste! 👋 I am your AI Retail Sales Copilot.\n\nNo complicated forms or marketing jargon! Think of me as your personal retail growth advisor. Just ask me naturally:\n• \"Which product is failing or stuck on my shelves?\"\n• \"Suggest 3 best offers for this week\"\n• \"How can I increase this weekend's sales?\"\n• \"Create a Diwali sweet & dry fruit gift pack\"",
      time: "Just now",
    },
  ]);
  const [isLoading, setIsLoading] = useState(false);
  const [activePlan, setActivePlan] = useState(null);

  useEffect(() => {
    if (initialPrompt && initialPrompt.trim()) {
      handleSendMessage(initialPrompt.trim());
      if (onClearInitialPrompt) onClearInitialPrompt();
    }
  }, [initialPrompt]);

  const formatTime = () => {
    const d = new Date();
    let hours = d.getHours();
    const minutes = d.getMinutes().toString().padStart(2, "0");
    const ampm = hours >= 12 ? "PM" : "AM";
    hours = hours % 12 || 12;
    return `${hours}:${minutes} ${ampm}`;
  };

  const handleSendMessage = async (userText) => {
    // Append user message
    setMessages((prev) => [
      ...prev,
      { sender: "user", text: userText, time: formatTime() },
    ]);

    setIsLoading(true);
    try {
      const data = await sendChatMessage(userText);

      // Append bot reply
      setMessages((prev) => [
        ...prev,
        {
          sender: "bot",
          text: data.reply || "I analyzed your request and computed store metrics.",
          plan: data.plan,
          ideas: data.ideas,
          time: formatTime(),
        },
      ]);

      // If a plan was returned, auto-load it into Collateral Studio
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
        combo_id: variety.variety_id || "COMBO_COPILOT",
        title: variety.title,
        price: variety.combo_price,
        discount_pct: variety.discount_pct,
        event_theme: activePlan?.event_theme || "Active Campaign",
      });
      alert(`Offer "${variety.title}" has been scheduled into your store calendar!`);
      if (onOfferActivated) onOfferActivated();
    } catch (e) {
      console.error("Failed to publish offer:", e);
      alert("Failed to schedule offer. Please try again.");
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
            <span>AI Retail Copilot & Sales Growth Advisor</span>
          </h2>
          <p className="text-xs sm:text-sm text-muted-foreground mt-0.5">
            Zero jargon, zero complicated forms. Ask in plain words how to increase sales, diagnose failing products, and launch customer-ready promotions.
          </p>
        </div>

        <Badge variant="outline" className="text-xs py-1 px-3 font-medium border-border w-fit">
          📍 {storeProfile?.city || "Bengaluru"} • Active Copilot
        </Badge>
      </div>

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
        />

        <CollateralStudio
          plan={activePlan}
          onScheduleOffer={handleScheduleOffer}
        />
      </div>
    </div>
  );
}

