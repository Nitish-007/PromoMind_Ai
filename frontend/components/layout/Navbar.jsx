"use client";

import { Package, Sparkles, Calendar, FileUp, Store } from "lucide-react";
import { cn } from "@/lib/utils";

const NAV_TABS = [
  { id: "inventory", label: "Stock & Brands", icon: Package },
  { id: "promos", label: "AI Sales Copilot", icon: Sparkles, highlight: true },
  { id: "calendar", label: "Regional Festivals", icon: Calendar },
  { id: "upload", label: "CSV & AI Sync", icon: FileUp },
  { id: "profile", label: "Store Profile", icon: Store },
];

export function Navbar({ activeTab, onSelectTab }) {
  return (
    <nav className="w-full border-b border-border bg-card">
      <div className="mx-auto flex max-w-7xl items-center px-4 sm:px-6 lg:px-8">
        <div className="flex w-full space-x-1 sm:space-x-1 overflow-x-auto py-1.5 no-scrollbar">
          {NAV_TABS.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => onSelectTab(tab.id)}
                className={cn(
                  "flex items-center gap-2 rounded-md px-3.5 py-2 text-sm font-medium transition-colors shrink-0 select-none",
                  isActive
                    ? "bg-foreground text-background font-semibold"
                    : "text-muted-foreground hover:bg-muted hover:text-foreground"
                )}
              >
                <Icon className="h-4 w-4" />
                <span>{tab.label}</span>
                {tab.id === "calendar" && (
                  <span className="h-2 w-2 rounded-full bg-foreground opacity-60" />
                )}
              </button>
            );
          })}
        </div>
      </div>
    </nav>
  );
}

