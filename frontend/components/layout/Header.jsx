"use client";

import {
  Moon,
  Sun,
  Store,
  FileText,
  LogIn,
  User,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import Link from "next/link";

export function Header({
  storeProfile,
  currentUser,
  theme,
  onToggleTheme,
  onOpenProfile,
  onOpenLoginModal,
}) {
  return (
    <header className="sticky top-0 z-40 w-full border-b bg-card/95 backdrop-blur-md transition-colors">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        {/* Brand Logo & Tagline */}
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-foreground text-background font-bold text-lg tracking-tight">
            PM
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-heading text-lg sm:text-xl font-bold tracking-tight text-foreground">
                PromoMind{" "}
                <span className="text-muted-foreground font-medium">
                  AI
                </span>
              </span>
              <Badge
                variant="outline"
                className="text-xs font-medium tracking-wide uppercase px-2 py-0.5 rounded border-border text-muted-foreground"
              >
                v3.0
              </Badge>
            </div>
            <p className="text-sm text-muted-foreground hidden sm:block">
              Demand Forecasting &amp; Profit Optimization for Retail &amp; Commerce
            </p>
          </div>
        </div>

        {/* Center/Right Actions */}
        <div className="flex items-center gap-2">
          {/* Active Store Pill */}
          <button
            onClick={onOpenProfile}
            className="group flex items-center gap-2 rounded-md border border-border bg-transparent px-3 py-1.5 text-left text-sm transition-colors hover:bg-muted"
            title="Manage Stores & Profile Settings"
          >
            <Store className="h-4 w-4 text-muted-foreground group-hover:text-foreground" />
            <div className="hidden xs:block sm:block" suppressHydrationWarning>
              <span className="font-medium text-foreground text-sm" suppressHydrationWarning>
                {storeProfile?.store_name || "Sharma Supermarket"}
              </span>
              <span className="text-xs text-muted-foreground ml-2 border-l pl-2" suppressHydrationWarning>
                {storeProfile?.city || "Bengaluru"}
              </span>
            </div>
          </button>

          {/* User Account / Sign In Button */}
          {currentUser ? (
            <button
              onClick={onOpenProfile}
              className="flex items-center gap-1.5 rounded-md border border-border bg-muted/40 px-3 py-1.5 text-xs font-semibold hover:bg-muted transition-colors text-foreground"
              title={`Logged in as ${currentUser.email || currentUser.full_name}`}
            >
              <User className="h-3.5 w-3.5 text-muted-foreground" />
              <span className="max-w-[120px] truncate hidden sm:inline">
                {currentUser.full_name || currentUser.email?.split("@")[0] || "Account"}
              </span>
            </button>
          ) : (
            onOpenLoginModal && (
              <Button
                variant="outline"
                size="sm"
                onClick={onOpenLoginModal}
                className="gap-1.5 text-xs h-9 px-3 border-border font-semibold"
                title="Sign In or Create Account"
              >
                <LogIn className="h-3.5 w-3.5" />
                <span>Sign In / Sign Up</span>
              </Button>
            )
          )}

          {/* Whitepaper & Architecture Link */}
          <Button
            render={
              <Link
                href="/problem-statement"
                target="_blank"
                rel="noopener noreferrer"
              />
            }
            variant="outline"
            size="sm"
            className="hidden md:inline-flex gap-1.5 text-xs font-semibold h-9 px-3 border-border hover:bg-muted text-foreground"
          >
            <FileText className="h-3.5 w-3.5 text-emerald-500" />
            <span>Whitepaper &amp; Architecture</span>
          </Button>

          {/* Theme Toggle */}
          <Button
            variant="ghost"
            size="icon"
            onClick={onToggleTheme}
            className="h-8 w-8 rounded-lg"
            title="Toggle theme"
          >
            {theme === "dark" ? (
              <Sun className="h-4 w-4 text-amber-400" />
            ) : (
              <Moon className="h-4 w-4 text-muted-foreground" />
            )}
          </Button>
        </div>
      </div>
    </header>
  );
}
