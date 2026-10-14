"use client";

import { AlertTriangle, Lightbulb, Flame, TrendingUp } from "lucide-react";

export function CopilotQuickPrompts({ onSelectPrompt, disabled }) {
  const prompts = [
    {
      title: "Which products are failing or stuck?",
      desc: "Identify slow movers & recover trapped cash",
      icon: AlertTriangle,
      text: "Which products are failing or stuck in my store?",
    },
    {
      title: "Suggest 3 best offers for this week",
      desc: "AI curated high-margin bundles",
      icon: Lightbulb,
      text: "Suggest 3 best offers for this week",
    },
    {
      title: "Diwali Festive Gift Hamper",
      desc: "Ghee & dry fruits bundle with WhatsApp copy",
      icon: Flame,
      text: "Create a festive gift hamper for Diwali",
    },
    {
      title: "How can I increase sales by 20%?",
      desc: "Actionable strategies to boost basket sizes",
      icon: TrendingUp,
      text: "How can I increase my sales by 20%?",
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2.5">
      {prompts.map((p, i) => {
        const Icon = p.icon;
        return (
          <button
            key={i}
            type="button"
            disabled={disabled}
            onClick={() => onSelectPrompt(p.text)}
            className="flex items-start gap-3 rounded-xl border border-border bg-card p-3 text-left transition-colors hover:bg-muted/50 hover:border-foreground/20 disabled:opacity-50"
          >
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-muted text-foreground border border-border mt-0.5">
              <Icon className="h-4 w-4 text-muted-foreground" />
            </div>
            <div className="overflow-hidden">
              <div className="text-sm font-semibold text-foreground truncate">
                {p.title}
              </div>
              <div className="text-xs text-muted-foreground truncate mt-0.5">
                {p.desc}
              </div>
            </div>
          </button>
        );
      })}
    </div>
  );
}

