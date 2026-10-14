"use client";

import {
    Sparkles,
    Moon,
    Sun,
    Store,
    FileText,
    Presentation,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import Link from "next/link";

export function Header({ storeProfile, theme, onToggleTheme, onOpenProfile }) {
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
                                v2.5
                            </Badge>
                        </div>
                        <p className="text-sm text-muted-foreground hidden sm:block">
                            Demand Forecasting & Multi-Brand Retailer OS
                        </p>
                    </div>
                </div>

                {/* Center/Right Actions */}
                <div className="flex items-center gap-2.5">
                    {/* Store & Regional Location Pill */}
                    <button
                        onClick={onOpenProfile}
                        className="group flex items-center gap-2.5 rounded-md border border-border bg-transparent px-3 py-1.5 text-left text-sm transition-colors hover:bg-muted"
                        title="Edit Store Profile & Regional Demographics"
                    >
                        <Store className="h-4 w-4 text-muted-foreground group-hover:text-foreground" />
                        <div className="hidden xs:block sm:block" suppressHydrationWarning>
                            <span className="font-medium text-foreground text-sm" suppressHydrationWarning>
                                {storeProfile.store_name ||
                                    "Metro Supermarket"}
                            </span>
                            <span className="text-xs text-muted-foreground ml-2 border-l pl-2" suppressHydrationWarning>
                                {storeProfile.city || "Bengaluru"}
                            </span>
                        </div>
                    </button>

                    {/* Whitepaper Link */}
                    <Button
                        render={
                            <Link
                                href="/problem-statement"
                                target="_blank"
                                rel="noopener noreferrer"
                            />
                        }
                        variant="ghost"
                        size="sm"
                        className="hidden md:inline-flex gap-1.5 text-sm text-muted-foreground hover:text-foreground h-9 px-3"
                    >
                        <FileText className="h-4 w-4" />
                        <span>Whitepaper</span>
                    </Button>

                    {/* Pitch Deck Link */}
                    <Button
                        render={
                            <Link
                                href="/deck"
                                target="_blank"
                                rel="noopener noreferrer"
                            />
                        }
                        variant="ghost"
                        size="sm"
                        className="hidden lg:inline-flex gap-1.5 text-sm text-muted-foreground hover:text-foreground h-9 px-3"
                    >
                        <Presentation className="h-4 w-4" />
                        <span>Pitch Deck</span>
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
