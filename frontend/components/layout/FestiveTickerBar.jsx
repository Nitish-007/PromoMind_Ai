"use client";

import { ChevronRight } from "lucide-react";

export function FestiveTickerBar({ region, onOpenCalendar }) {
  let festivalTitle = "Diwali / Deepavali (South India)";
  let surgeText = "Clay Deepas/Diyas & Cow Ghee Demand: +85% to +140%";

  const r = (region || "").toLowerCase();
  if (r.includes("maharashtra") || r.includes("west")) {
    festivalTitle = "Diwali Lakshmi Pujan & Gudi Padwa";
    surgeText = "Faral, Poha, Sweets & Besan Demand: +75% to +120%";
  } else if (r.includes("bengal") || r.includes("east")) {
    festivalTitle = "Kali Puja & Durga Mahotsav";
    surgeText = "Sweets, Mustard Oil & Ghee Demand: +90% to +150%";
  } else if (r.includes("delhi") || r.includes("north")) {
    festivalTitle = "Diwali Maha Utsav & Karwa Chauth";
    surgeText = "Dry Fruits, Sweets & Pooja Items Demand: +80% to +135%";
  }

  return (
    <div className="w-full bg-muted/40 border-b border-border px-4 py-2 text-sm transition-colors">
      <div className="mx-auto flex max-w-7xl items-center justify-between gap-3">
        <div className="flex items-center gap-2 overflow-hidden text-ellipsis whitespace-nowrap">
          <span className="text-xs font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-foreground text-background">
            Regional Surge
          </span>
          <span className="font-semibold text-foreground">
            {festivalTitle}
          </span>
          <span className="text-muted-foreground hidden sm:inline">•</span>
          <span className="text-muted-foreground hidden sm:inline text-sm">{surgeText}</span>
        </div>
        <button
          onClick={onOpenCalendar}
          className="group flex shrink-0 items-center gap-1 font-medium text-xs text-muted-foreground hover:text-foreground transition-colors"
        >
          <span>View Regional Festivals</span>
          <ChevronRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
        </button>
      </div>
    </div>
  );
}
