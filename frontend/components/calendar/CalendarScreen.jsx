"use client";

import { useState, useEffect } from "react";
import {
  fetchCalendarEvents,
  fetchActiveOffers,
  updateOfferStatus,
  deleteOffer,
  checkOfferConflict,
  fetchInventory,
} from "@/lib/api";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { CustomSelect } from "@/components/ui/custom-select";
import { Loader2, RefreshCw } from "lucide-react";

function inferCountryFromRegionName(rawRegion) {
  if (!rawRegion) return "India";
  const low = rawRegion.toLowerCase();

  // 1. Australia
  if (
    low.includes("australia") ||
    low.includes("sydney") ||
    low.includes("melbourne") ||
    low.includes("brisbane") ||
    low.includes("perth") ||
    low.includes("adelaide")
  ) {
    return "Australia";
  }

  // 2. UK
  if (low.includes("uk") || low.includes("united kingdom") || low.includes("london") || low.includes("england") || low.includes("scotland")) {
    return "United Kingdom";
  }

  // 3. Canada
  if (low.includes("canada") || low.includes("ontario") || low.includes("toronto") || low.includes("vancouver") || low.includes("montreal")) {
    return "Canada";
  }

  // 4. Global Countries
  if (low.includes("germany") || low.includes("berlin") || low.includes("munich")) return "Germany";
  if (low.includes("france") || low.includes("paris")) return "France";
  if (low.includes("japan") || low.includes("tokyo")) return "Japan";
  if (low.includes("singapore")) return "Singapore";
  if (low.includes("uae") || low.includes("dubai") || low.includes("abu dhabi")) return "United Arab Emirates";
  if (low.includes("new zealand") || low.includes("auckland")) return "New Zealand";

  // 5. United States
  const usStates = [
    "california", "texas", "florida", "new york", "illinois", "pennsylvania", "ohio",
    "georgia", "north carolina", "michigan", "new jersey", "virginia", "washington",
    "arizona", "massachusetts", "colorado", "nevada", "usa", "united states",
  ];
  if (usStates.some((s) => low.includes(s))) return "USA";

  // 6. India
  const indiaRegions = [
    "karnataka", "maharashtra", "bengal", "tamil", "gujarat", "kerala", "delhi", "punjab",
    "rajasthan", "haryana", "uttar pradesh", "bihar", "odisha", "assam", "bengaluru", "mumbai",
    "delhi", "kolkata", "chennai", "hyderabad", "pune", "ahmedabad", "jaipur", "india"
  ];
  if (indiaRegions.some((s) => low.includes(s))) return "India";

  return rawRegion.trim();
}

export function CalendarScreen({ storeProfile, onLaunchPromo }) {
  const storeRegionClean = storeProfile?.region
    ? storeProfile.region.split("&")[0].trim()
    : "Karnataka";
  const storeCityClean = storeProfile?.city || "Bengaluru";

  const [activeRegion, setActiveRegion] = useState(storeRegionClean);
  const [activeCity, setActiveCity] = useState(storeCityClean);
  const [activeCountry, setActiveCountry] = useState(
    storeProfile?.country || inferCountryFromRegionName(storeRegionClean)
  );

  const [customRegionOpen, setCustomRegionOpen] = useState(false);
  const [customRegionInput, setCustomRegionInput] = useState("");

  const [events, setEvents] = useState([]);
  const [loadingEvents, setLoadingEvents] = useState(true);
  const [syncingEvents, setSyncingEvents] = useState(false);
  const [lastSyncedAt, setLastSyncedAt] = useState(null);

  // Active & Scheduled Store Offers state
  const [activeOffers, setActiveOffers] = useState([]);
  const [loadingOffers, setLoadingOffers] = useState(true);
  const [offerFilter, setOfferFilter] = useState("ALL"); // "ALL" | "ACTIVE" | "SCHEDULED" | "PAUSED"

  // Conflict Check state
  const [inventoryItems, setInventoryItems] = useState([]);
  const [conflictSku, setConflictSku] = useState("");
  const [conflictDiscount, setConflictDiscount] = useState(20);
  const [checkingConflict, setCheckingConflict] = useState(false);
  const [conflictResult, setConflictResult] = useState(null);

  // Automatically load festivals from the logged-in store's saved region
  useEffect(() => {
    const reg = storeProfile?.region
      ? storeProfile.region.split("&")[0].trim()
      : (typeof window !== "undefined" && localStorage.getItem("promomind_region")?.split("&")[0]?.trim()) || "Karnataka";
    const cty = storeProfile?.city || (typeof window !== "undefined" && localStorage.getItem("promomind_city")) || "Bengaluru";
    const ctry = storeProfile?.country || inferCountryFromRegionName(reg);

    setActiveRegion(reg);
    setActiveCity(cty);
    setActiveCountry(ctry);

    loadStoredFestivals(reg, ctry, cty);
    loadOffers();
    loadInventory();
  }, [storeProfile?.store_id, storeProfile?.region, storeProfile?.city]);

  async function loadStoredFestivals(reg, ctry, cty) {
    setLoadingEvents(true);
    try {
      const data = await fetchCalendarEvents(reg, false, ctry, cty);
      setEvents(data || []);
      if (data && data[0]?.synced_at) {
        setLastSyncedAt(new Date(data[0].synced_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }));
      }
    } catch (e) {
      console.error("Failed to load stored calendar events:", e);
    } finally {
      setLoadingEvents(false);
    }
  }

  async function handleSyncNewFestivals(overrideRegion = null) {
    const reg = (overrideRegion || activeRegion || storeRegionClean).trim();
    const ctry = inferCountryFromRegionName(reg);
    const cty = overrideRegion ? reg : activeCity;

    setActiveRegion(reg);
    setActiveCountry(ctry);
    setSyncingEvents(true);

    try {
      const data = await fetchCalendarEvents(reg, true, ctry, cty);
      setEvents(data || []);
      setLastSyncedAt(new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }));
    } catch (e) {
      console.error("Failed to sync festivals from Gemini AI:", e);
    } finally {
      setSyncingEvents(false);
    }
  }

  async function loadOffers() {
    setLoadingOffers(true);
    try {
      const data = await fetchActiveOffers();
      setActiveOffers(data || []);
    } catch (e) {
      console.error("Failed to load offers:", e);
    } finally {
      setLoadingOffers(false);
    }
  }

  async function handleToggleOfferStatus(offer, nextStatus) {
    try {
      await updateOfferStatus(offer.id, { status: nextStatus });
      await loadOffers();
    } catch (e) {
      console.error("Failed to update offer status:", e);
    }
  }

  async function handleDeleteOffer(offerId) {
    try {
      await deleteOffer(offerId);
      await loadOffers();
    } catch (e) {
      console.error("Failed to delete offer:", e);
    }
  }

  async function loadInventory() {
    try {
      const data = await fetchInventory();
      setInventoryItems(data || []);
    } catch (e) {
      console.error("Failed to load inventory for conflict test:", e);
    }
  }

  async function handleConflictCheck() {
    if (!conflictSku) return;
    setCheckingConflict(true);
    setConflictResult(null);

    try {
      const res = await checkOfferConflict(conflictSku, "NONE", "2026-10-20", "2026-10-30");
      setConflictResult(res);
    } catch (e) {
      console.error("Conflict check error:", e);
      setConflictResult({
        has_conflict: false,
        recommended_action: "Error running simulation. Verify backend connectivity.",
      });
    } finally {
      setCheckingConflict(false);
    }
  }

  const filteredOffers = activeOffers.filter((off) => {
    if (offerFilter === "ALL") return true;
    if (offerFilter === "PAUSED") return off.status === "PAUSED" || off.status === "COMPLETED";
    return off.status === offerFilter;
  });

  const activeCount = activeOffers.filter((o) => o.status === "ACTIVE").length;
  const scheduledCount = activeOffers.filter((o) => o.status === "SCHEDULED").length;

  return (
    <div className="space-y-6">
      {/* Screen Header — Bound to Logged-In Store Region with 1-Click Sync */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between border-b border-border pb-4">
        <div>
          <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-foreground">
            Regional Festival Calendar &amp; Campaign Schedule
          </h2>
          <p className="text-sm text-muted-foreground mt-1">
            Automatically synced to your logged-in store location (<strong className="text-foreground">{activeCity}, {activeRegion}</strong>) and persisted in Firestore (<code className="font-mono text-xs bg-muted px-1.5 py-0.5 rounded border border-border">stores/{storeProfile?.store_id || "sharma_supermarket_01"}/calendar_events</code>).
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setCustomRegionOpen(!customRegionOpen)}
            className="h-10 px-3 text-xs font-medium border-border"
          >
            {customRegionOpen ? "Hide Region Override" : "Preview Another Region"}
          </Button>
          <Button
            onClick={() => handleSyncNewFestivals()}
            disabled={syncingEvents || loadingEvents}
            className="h-10 px-4 text-xs sm:text-sm font-semibold bg-primary text-primary-foreground hover:bg-primary/90 flex items-center gap-2"
          >
            <RefreshCw className={`h-4 w-4 ${syncingEvents ? "animate-spin" : ""}`} />
            <span>{syncingEvents ? "Syncing via Gemini AI..." : "Sync / Update Upcoming Festivals"}</span>
          </Button>
        </div>
      </div>

      {/* Optional Region Override Drawer (Only shown if retailer wants to preview another region) */}
      {customRegionOpen && (
        <Card className="border border-border bg-card">
          <CardContent className="p-4 space-y-3">
            <div className="flex flex-col sm:flex-row gap-2">
              <Input
                type="text"
                placeholder="Enter another State, City, or Country to preview (e.g. Maharashtra, Kerala, Punjab, Hyderabad...)"
                value={customRegionInput}
                onChange={(e) => setCustomRegionInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && customRegionInput.trim() && handleSyncNewFestivals(customRegionInput)}
                className="h-10 text-sm bg-background border-border flex-1"
              />
              <Button
                onClick={() => customRegionInput.trim() && handleSyncNewFestivals(customRegionInput)}
                disabled={syncingEvents || !customRegionInput.trim()}
                className="h-10 px-4 text-xs font-semibold"
              >
                Sync Custom Region
              </Button>
              <Button
                variant="outline"
                onClick={() => {
                  setCustomRegionInput("");
                  handleSyncNewFestivals(storeRegionClean);
                }}
                className="h-10 px-3 text-xs"
              >
                Reset to Store Region ({storeRegionClean})
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Store Location & Demand Intelligence Summary Strip */}
      <Card className="border border-border bg-muted/20">
        <CardContent className="p-4 sm:p-5">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-4">
            <div>
              <h3 className="text-base sm:text-lg font-bold text-foreground">
                Persisted Regional Demand Signals for {storeProfile?.store_name || "Your Store"} ({activeCity}, {activeRegion})
              </h3>
              <p className="text-xs sm:text-sm text-muted-foreground mt-0.5">
                Festivals are automatically matched against your store&apos;s live Firestore inventory SKUs.
              </p>
            </div>
            {lastSyncedAt && (
              <Badge variant="outline" className="text-xs font-mono border-border bg-card w-fit">
                Synced at {lastSyncedAt}
              </Badge>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {events.slice(0, 2).map((ev, idx) => (
              <div key={idx} className="p-3.5 rounded-lg border border-border bg-card space-y-1">
                <div className="text-xs sm:text-sm font-semibold text-foreground">{ev.name}</div>
                <p className="text-xs sm:text-sm text-muted-foreground leading-relaxed">
                  Demand for <strong className="text-foreground">{ev.key_items?.slice(0, 3).join(", ")}</strong> surges by{" "}
                  <strong className="text-foreground">+{Math.round(ev.demand_lift_pct)}%</strong>.
                </p>
              </div>
            ))}
            <div className="p-3.5 rounded-lg border border-border bg-card space-y-1">
              <div className="text-xs sm:text-sm font-semibold text-foreground">
                Active &amp; Scheduled Campaigns ({activeOffers.length})
              </div>
              <p className="text-xs sm:text-sm text-muted-foreground leading-relaxed">
                <strong className="text-foreground">{activeCount} Active</strong> running now and{" "}
                <strong className="text-foreground">{scheduledCount} Scheduled</strong> for upcoming festival windows in Firestore.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Two-Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Persisted Regional Festivals */}
        <div className="lg:col-span-7 space-y-4">
          <div className="flex items-center justify-between pb-1">
            <h3 className="text-lg font-semibold text-foreground">
              Upcoming Regional Festivals ({activeRegion})
            </h3>
            <Badge variant="outline" className="text-xs px-2.5 py-1 font-semibold">
              {events.length} Stored Events
            </Badge>
          </div>

          {loadingEvents || syncingEvents ? (
            <div className="space-y-4">
              {[...Array(3)].map((_, i) => (
                <Card key={i} className="border border-border bg-card p-5 space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="space-y-2">
                      <Skeleton className="h-5 w-48 rounded" />
                      <Skeleton className="h-3 w-32 rounded" />
                    </div>
                    <Skeleton className="h-6 w-24 rounded-full" />
                  </div>
                  <Skeleton className="h-12 w-full rounded" />
                  <div className="grid grid-cols-3 gap-2">
                    <Skeleton className="h-12 w-full rounded-md" />
                    <Skeleton className="h-12 w-full rounded-md" />
                    <Skeleton className="h-12 w-full rounded-md" />
                  </div>
                  <Skeleton className="h-10 w-full rounded-lg" />
                </Card>
              ))}
            </div>
          ) : events.length === 0 ? (
            <Card className="border border-border p-8 text-center text-sm text-muted-foreground">
              No festival events stored yet. Click &quot;Sync / Update Upcoming Festivals&quot; above.
            </Card>
          ) : (
            <div className="space-y-4">
              {events.map((evt, idx) => {
                const matched = evt.matched_inventory_items || [];
                return (
                  <Card key={idx} className="border border-border bg-card shadow-xs overflow-hidden">
                    <CardContent className="p-5 space-y-4">
                      {/* Festival Header */}
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <h4 className="text-base sm:text-lg font-bold text-foreground">{evt.name}</h4>
                          <p className="text-xs sm:text-sm text-muted-foreground mt-0.5">
                            {evt.date_window} • <span className="font-semibold text-foreground">{evt.region}</span>
                          </p>
                        </div>
                        <div className="flex flex-col items-end gap-1.5 shrink-0">
                          <Badge variant="outline" className="border-border bg-muted/60 text-foreground font-semibold text-xs px-2.5 py-1">
                            +{Math.round(evt.demand_lift_pct)}% Surge
                          </Badge>
                          {evt.generation_source && (
                            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-muted/80 text-muted-foreground border border-border">
                              {evt.generation_source.startsWith("LIVE_") ? "● Live AI: " : "● "}{evt.generation_source}
                            </span>
                          )}
                        </div>
                      </div>

                      {/* Description */}
                      <p className="text-sm text-muted-foreground leading-relaxed">{evt.description}</p>

                      {/* Cultural Tradition Note */}
                      {evt.tradition_notes && (
                        <div className="p-3 rounded-lg bg-muted/40 border border-border/70 text-xs sm:text-sm text-foreground">
                          <span className="font-semibold">Cultural Retail Tradition:</span> {evt.tradition_notes}
                        </div>
                      )}

                      {/* Live Store SKUs Matching Demand */}
                      {matched.length > 0 && (
                        <div className="p-3.5 rounded-lg border border-border bg-muted/20 space-y-2">
                          <div className="flex items-center justify-between text-xs font-semibold">
                            <span className="text-foreground">
                              Matched Store Inventory SKUs ({matched.length}):
                            </span>
                            <span className="text-emerald-600 dark:text-emerald-400">
                              In Stock &amp; Ready
                            </span>
                          </div>
                          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-1">
                            {matched.map((m, mIdx) => (
                              <div
                                key={mIdx}
                                className="p-2.5 rounded-md border border-border bg-card text-xs flex flex-col justify-between"
                              >
                                <span className="font-semibold text-foreground truncate">{m.name}</span>
                                <span className="text-muted-foreground mt-1">
                                  Stock: <strong className="text-foreground">{m.stock_quantity}</strong> • ₹{Math.round(m.selling_price)} ({m.margin_pct}% margin)
                                </span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Multi-Horizon Planning Deadlines */}
                      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-xs">
                        {evt.advance_procurement_window && (
                          <div className="p-2.5 rounded-md border border-border bg-muted/20">
                            <div className="font-semibold text-foreground mb-1">
                              T-14d Procurement:
                            </div>
                            <div className="text-muted-foreground">{evt.advance_procurement_window}</div>
                          </div>
                        )}
                        {evt.promo_launch_window && (
                          <div className="p-2.5 rounded-md border border-border bg-muted/20">
                            <div className="font-semibold text-foreground mb-1">
                              T-7d Promo Launch:
                            </div>
                            <div className="text-muted-foreground">{evt.promo_launch_window}</div>
                          </div>
                        )}
                        {evt.clearance_window && (
                          <div className="p-2.5 rounded-md border border-border bg-muted/20">
                            <div className="font-semibold text-foreground mb-1">
                              T+2d Clearance:
                            </div>
                            <div className="text-muted-foreground">{evt.clearance_window}</div>
                          </div>
                        )}
                      </div>

                      {/* Key SKUs */}
                      {evt.key_items && evt.key_items.length > 0 && (
                        <div className="flex flex-wrap gap-1.5 pt-1">
                          {evt.key_items.map((item, i) => (
                            <Badge key={i} variant="outline" className="text-xs bg-muted/30 border-border text-foreground font-normal">
                              {item}
                            </Badge>
                          ))}
                        </div>
                      )}

                      {/* Generate AI Promo CTA */}
                      <Button
                        onClick={() => {
                          if (onLaunchPromo) {
                            onLaunchPromo(
                              evt.name,
                              evt.suggested_combo_title || "",
                              evt.recommended_promo_type || ""
                            );
                          }
                        }}
                        className="w-full font-semibold h-11 bg-primary text-primary-foreground hover:bg-primary/90"
                      >
                        Generate AI Promo Offer for {evt.name.split("(")[0].trim()}
                      </Button>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          )}
        </div>

        {/* Right Column: Advanced Store Offers Lifecycle Manager & Conflict Sandbox */}
        <div className="lg:col-span-5 space-y-6">
          {/* Active & Scheduled Store Offers Manager */}
          <Card className="border border-border bg-card shadow-xs">
            <CardHeader className="pb-3 border-b border-border space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-base font-bold text-foreground">
                    Current &amp; Scheduled Store Offers
                  </CardTitle>
                  <CardDescription className="text-xs text-muted-foreground font-mono mt-0.5">
                    stores/{storeProfile?.store_id || "sharma_supermarket_01"}/promotions
                  </CardDescription>
                </div>
                <Badge variant="outline" className="text-xs px-2.5 py-1 font-semibold">
                  {activeOffers.length} Total
                </Badge>
              </div>

              {/* Filter Tabs */}
              <div className="grid grid-cols-4 gap-1 bg-muted/50 p-1 rounded-lg border border-border text-xs font-medium">
                {[
                  { id: "ALL", label: `All (${activeOffers.length})` },
                  { id: "ACTIVE", label: `Active (${activeCount})` },
                  { id: "SCHEDULED", label: `Scheduled (${scheduledCount})` },
                  { id: "PAUSED", label: "Paused" },
                ].map((tab) => (
                  <button
                    key={tab.id}
                    type="button"
                    onClick={() => setOfferFilter(tab.id)}
                    className={`py-1.5 rounded-md transition-colors text-center ${
                      offerFilter === tab.id
                        ? "bg-card text-foreground font-semibold shadow-xs"
                        : "text-muted-foreground hover:text-foreground"
                    }`}
                  >
                    {tab.label}
                  </button>
                ))}
              </div>
            </CardHeader>

            <CardContent className="p-4 space-y-3 max-h-[540px] overflow-y-auto">
              {loadingOffers ? (
                <div className="space-y-3">
                  {[...Array(2)].map((_, i) => (
                    <div key={i} className="border border-border rounded-lg p-4 space-y-2">
                      <Skeleton className="h-4 w-40 rounded" />
                      <Skeleton className="h-3 w-52 rounded" />
                      <Skeleton className="h-8 w-full rounded" />
                    </div>
                  ))}
                </div>
              ) : filteredOffers.length === 0 ? (
                <div className="p-6 text-center text-xs sm:text-sm text-muted-foreground">
                  No campaigns in this view. Generate an offer in the AI Sales Copilot to activate or schedule it.
                </div>
              ) : (
                filteredOffers.map((off, idx) => {
                  const isActive = off.status === "ACTIVE";
                  const isScheduled = off.status === "SCHEDULED";
                  return (
                    <div
                      key={off.id || idx}
                      className="rounded-xl border border-border bg-background p-4 space-y-2.5 transition-colors hover:bg-muted/20"
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div>
                          <div className="font-bold text-foreground text-sm">{off.title}</div>
                          <div className="text-[11px] text-muted-foreground mt-0.5">
                            Theme: <strong className="text-foreground">{off.event_theme || "Store Promo"}</strong>
                          </div>
                        </div>
                        <Badge
                          variant="outline"
                          className={`text-[10px] font-semibold px-2 py-0.5 shrink-0 ${
                            isActive
                              ? "border-emerald-500/40 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400"
                              : isScheduled
                              ? "border-amber-500/40 bg-amber-500/10 text-amber-600 dark:text-amber-400"
                              : "border-border bg-muted text-muted-foreground"
                          }`}
                        >
                          {off.status}
                        </Badge>
                      </div>

                      <div className="text-xs text-muted-foreground">
                        SKUs: <span className="font-medium text-foreground">{off.anchor_name || off.anchor_id}</span> +{" "}
                        <span className="font-medium text-foreground">{off.attached_name || off.attached_id}</span>
                      </div>

                      <div className="flex flex-wrap items-center justify-between gap-2 text-xs pt-1 border-t border-border/50">
                        <div>
                          <span className="font-bold text-foreground text-sm">₹{Math.round(off.combo_price)}</span>
                          {off.original_mrp && (
                            <span className="text-muted-foreground line-through ml-1.5">
                              ₹{Math.round(off.original_mrp)}
                            </span>
                          )}
                          <span className="text-emerald-600 dark:text-emerald-400 font-semibold ml-2">
                            {off.discount_pct}% OFF
                          </span>
                        </div>
                        <div className="text-[11px] text-muted-foreground font-mono">
                          {off.start_date} → {off.end_date}
                        </div>
                      </div>

                      <div className="flex items-center justify-between gap-2 pt-2 border-t border-border/50">
                        <span className="text-[11px] text-muted-foreground">
                          Broadcast Reach: <strong>{off.broadcast_reach || storeProfile?.whatsapp_audience_size || 1420}</strong> customers
                        </span>
                        <div className="flex items-center gap-1.5">
                          {isScheduled && (
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => handleToggleOfferStatus(off, "ACTIVE")}
                              className="h-7 px-2.5 text-[11px] font-semibold"
                            >
                              Activate Now
                            </Button>
                          )}
                          {isActive && (
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => handleToggleOfferStatus(off, "PAUSED")}
                              className="h-7 px-2.5 text-[11px]"
                            >
                              Pause
                            </Button>
                          )}
                          {off.status === "PAUSED" && (
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => handleToggleOfferStatus(off, "ACTIVE")}
                              className="h-7 px-2.5 text-[11px] font-semibold"
                            >
                              Resume
                            </Button>
                          )}
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleDeleteOffer(off.id)}
                            className="h-7 px-2 text-[11px] text-muted-foreground hover:text-destructive"
                          >
                            Remove
                          </Button>
                        </div>
                      </div>
                    </div>
                  );
                })
              )}
            </CardContent>
          </Card>

          {/* Interactive Conflict Check Sandbox */}
          <Card className="border border-border bg-card shadow-xs">
            <CardHeader className="pb-3">
              <CardTitle className="text-base font-bold">Test New Proposed Offer for Conflicts</CardTitle>
              <CardDescription className="text-xs text-muted-foreground leading-relaxed">
                Simulate a prospective offer to check if it overlaps with an active or scheduled promotion on the same SKU.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-foreground">Select Anchor Product SKU:</label>
                <CustomSelect
                  value={conflictSku}
                  onChange={setConflictSku}
                  options={inventoryItems.map((item) => ({
                    value: item.id,
                    label: `${item.name} (${item.id}) — ₹${item.selling_price}`,
                  }))}
                  placeholder="Choose SKU to check..."
                />
              </div>

              <div className="space-y-1.5">
                <div className="flex justify-between text-xs">
                  <span className="font-semibold text-foreground">Proposed Discount Depth:</span>
                  <span className="font-bold text-foreground">{conflictDiscount}% OFF</span>
                </div>
                <input
                  type="range"
                  min="5"
                  max="35"
                  value={conflictDiscount}
                  onChange={(e) => setConflictDiscount(Number(e.target.value))}
                  className="w-full accent-primary h-1.5 bg-muted rounded-lg cursor-pointer"
                />
              </div>

              <Button
                onClick={handleConflictCheck}
                disabled={!conflictSku || checkingConflict}
                variant="outline"
                className="w-full h-10 text-xs font-semibold border-border bg-secondary text-secondary-foreground hover:bg-secondary/80"
              >
                {checkingConflict ? "Checking Active Campaigns..." : "Run Conflict & Margin Audit"}
              </Button>

              {conflictResult && (
                <div
                  className={`p-3.5 rounded-lg border text-xs space-y-1.5 ${
                    conflictResult.has_conflict
                      ? "border-amber-500/40 bg-amber-500/10 text-foreground"
                      : "border-emerald-500/40 bg-emerald-500/10 text-foreground"
                  }`}
                >
                  <div className="font-bold">
                    {conflictResult.has_conflict
                      ? "Conflict Detected — Margin Cannibalization Risk"
                      : "No Conflict Detected — Safe to Launch"}
                  </div>
                  {conflictResult.conflict_reason && (
                    <p className="text-muted-foreground leading-relaxed">{conflictResult.conflict_reason}</p>
                  )}
                  <p className="font-medium text-foreground pt-1">
                    Recommendation: {conflictResult.recommended_action}
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
