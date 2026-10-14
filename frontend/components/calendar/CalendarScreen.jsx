"use client";

import { useState, useEffect } from "react";
import {
  fetchCalendarEvents,
  fetchActiveOffers,
  checkOfferConflict,
  fetchInventory,
} from "@/lib/api";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { CustomSelect } from "@/components/ui/custom-select";
import {
  Calendar as CalendarIcon,
  Search,
  Sparkles,
  ShieldCheck,
  AlertTriangle,
  Flame,
  Package,
  Clock,
  ArrowRight,
  TrendingUp,
  Tag,
  Loader2,
  CheckCircle2,
} from "lucide-react";

function inferCountryFromRegionName(rawRegion) {
  if (!rawRegion) return "India";
  const low = rawRegion.toLowerCase();
  const usStates = [
    "california", "texas", "florida", "new york", "illinois", "pennsylvania", "ohio",
    "georgia", "north carolina", "michigan", "new jersey", "virginia", "washington",
    "arizona", "massachusetts", "tennessee", "indiana", "missouri", "maryland", "wisconsin",
    "colorado", "minnesota", "south carolina", "alabama", "louisiana", "kentucky", "oregon",
    "oklahoma", "connecticut", "utah", "iowa", "nevada", "arkansas", "mississippi", "kansas",
    "new mexico", "nebraska", "idaho", "west virginia", "hawaii", "new hampshire", "maine",
    "montana", "rhode island", "delaware", "south dakota", "north dakota", "alaska", "vermont",
    "wyoming", "usa", "united states",
  ];
  if (usStates.some((s) => low.includes(s))) return "USA";
  if (low.includes("uk") || low.includes("london") || low.includes("england") || low.includes("britain")) return "UK";
  if (low.includes("canada") || low.includes("ontario") || low.includes("toronto")) return "Canada";
  if (low.includes("australia") || low.includes("sydney")) return "Australia";
  return "India";
}

const QUICK_STATES = [
  { name: "Karnataka", label: "👑 Karnataka (Dasara, Ugadi, Deepavali)" },
  { name: "Maharashtra", label: "🐘 Maharashtra (Ganesh Utsav, Faral)" },
  { name: "West Bengal", label: "🌸 West Bengal (Durga Puja, Kali Puja)" },
  { name: "Tamil Nadu", label: "🌾 Tamil Nadu (Pongal, Karthigai)" },
  { name: "Gujarat", label: "💃 Gujarat (Navratri, Uttarayan)" },
  { name: "Kerala", label: "🌼 Kerala (Onam Sadya, Vishu)" },
  { name: "Delhi-NCR", label: "🪔 Delhi-NCR (Diwali, Holi)" },
];

export function CalendarScreen({ onLaunchPromo }) {
  const [regionInput, setRegionInput] = useState("Karnataka");
  const [activeRegion, setActiveRegion] = useState("Karnataka");
  const [activeCountry, setActiveCountry] = useState("India");
  const [events, setEvents] = useState([]);
  const [loadingEvents, setLoadingEvents] = useState(true);

  const [activeOffers, setActiveOffers] = useState([]);
  const [loadingOffers, setLoadingOffers] = useState(true);

  const [inventoryItems, setInventoryItems] = useState([]);
  const [conflictSku, setConflictSku] = useState("");
  const [conflictDiscount, setConflictDiscount] = useState(20);
  const [checkingConflict, setCheckingConflict] = useState(false);
  const [conflictResult, setConflictResult] = useState(null);

  useEffect(() => {
    // Initial fetch from stored region or fallback
    const savedRegion = typeof window !== "undefined" ? localStorage.getItem("promomind_region") : null;
    const initialRegion = savedRegion ? savedRegion.split("&")[0].trim() : "Karnataka";
    setRegionInput(initialRegion);
    handleDiscoverRegion(initialRegion, false);
    loadOffers();
    loadInventory();
  }, []);

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

  async function loadInventory() {
    try {
      const data = await fetchInventory();
      setInventoryItems(data || []);
    } catch (e) {
      console.error("Failed to load inventory for conflict test:", e);
    }
  }

  async function handleDiscoverRegion(targetRegion, isRefresh = true) {
    const reg = (targetRegion || regionInput || "Karnataka").trim();
    const ctry = inferCountryFromRegionName(reg);
    setActiveRegion(reg);
    setActiveCountry(ctry);
    setLoadingEvents(true);

    try {
      const data = await fetchCalendarEvents(reg, isRefresh, ctry);
      setEvents(data || []);
    } catch (e) {
      console.error("Failed to load calendar events:", e);
    } finally {
      setLoadingEvents(false);
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

  return (
    <div className="space-y-6">
      {/* Screen Header */}
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between border-b border-border pb-4">
        <div>
          <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
            <CalendarIcon className="h-6 w-6 text-foreground" />
            Regional Festival Calendar & FMCG Demand Surge Engine
          </h2>
          <p className="text-sm text-muted-foreground mt-1">
            Type your State or City. Gemini AI dynamically discovers top upcoming regional festivals and predicts FMCG inventory demand surges.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="px-3 py-1.5 text-xs font-medium border-border bg-muted/60 text-foreground">
            📍 Active: {activeRegion} ({activeCountry})
          </Badge>
        </div>
      </div>

      {/* Dynamic Regional AI Discovery Bar */}
      <Card className="border border-border bg-card">
        <CardContent className="p-4 sm:p-5 space-y-4">
          <div className="flex flex-col sm:flex-row gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
              <Input
                type="text"
                placeholder="Type your State, Province or Region (e.g. Karnataka, Maharashtra, California, London...)"
                value={regionInput}
                onChange={(e) => setRegionInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleDiscoverRegion(regionInput, true)}
                className="pl-9 h-11 text-base bg-background border-border"
              />
            </div>
            <Button
              onClick={() => handleDiscoverRegion(regionInput, true)}
              disabled={loadingEvents}
              className="h-11 px-5 font-semibold bg-primary text-primary-foreground hover:bg-primary/90"
            >
              {loadingEvents ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Discovering...
                </>
              ) : (
                <>
                  <Sparkles className="h-4 w-4 mr-2" />
                  AI Festival Discovery
                </>
              )}
            </Button>
          </div>

          {/* Quick State Pills */}
          <div className="flex flex-wrap items-center gap-2 pt-1 border-t border-border/40">
            <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mr-1">
              Quick States:
            </span>
            {QUICK_STATES.map((st) => {
              const isActive = activeRegion.toLowerCase() === st.name.toLowerCase();
              return (
                <button
                  key={st.name}
                  type="button"
                  onClick={() => {
                    setRegionInput(st.name);
                    handleDiscoverRegion(st.name, true);
                  }}
                  className={`text-xs px-3 py-1.5 rounded-full transition-colors border font-medium ${
                    isActive
                      ? "bg-foreground text-background border-foreground font-semibold"
                      : "bg-muted/50 text-foreground border-border hover:bg-muted hover:border-foreground/40"
                  }`}
                >
                  {st.label}
                </button>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Regional Demand Intelligence Banner */}
      <Card className="border border-border bg-muted/20">
        <CardContent className="p-4 sm:p-5">
          <div className="flex items-start gap-3 mb-4">
            <div className="h-8 w-8 rounded-lg bg-muted flex items-center justify-center text-foreground shrink-0 text-base">
              📍
            </div>
            <div>
              <h3 className="text-base sm:text-lg font-bold text-foreground">
                AI Cultural Retail Intelligence for {activeRegion}, {activeCountry}
              </h3>
              <p className="text-xs sm:text-sm text-muted-foreground mt-0.5">
                Festive demand in retail is heavily localized. Demand for specific SKUs fluctuates dramatically by calendar dates.
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {events.slice(0, 2).map((ev, idx) => (
              <div key={idx} className="p-3.5 rounded-lg border border-border bg-card flex items-start gap-3">
                <span className="text-2xl">{ev.icon || "🪔"}</span>
                <div className="text-xs sm:text-sm space-y-1">
                  <div className="font-semibold text-foreground">{ev.name}</div>
                  <p className="text-muted-foreground leading-relaxed">
                    Demand for <strong className="text-foreground">{ev.key_items?.slice(0, 3).join(", ")}</strong> surges by{" "}
                    <strong className="text-foreground">+{Math.round(ev.demand_lift_pct)}%</strong>.
                  </p>
                </div>
              </div>
            ))}
            <div className="p-3.5 rounded-lg border border-border bg-card flex items-start gap-3">
              <span className="text-2xl">🛡️</span>
              <div className="text-xs sm:text-sm space-y-1">
                <div className="font-semibold text-foreground">Offer Conflict Prevention</div>
                <p className="text-muted-foreground leading-relaxed">
                  Running simultaneous discounts on the same SKU causes retailer margin dilution. PromoMind AI flags overlapping dates before promotions go live.
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Two-Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Upcoming Regional Festivals */}
        <div className="lg:col-span-7 space-y-4">
          <div className="flex items-center justify-between pb-1">
            <h3 className="text-lg font-semibold text-foreground">Upcoming Regional Festivals & Spikes</h3>
            <Badge variant="outline" className="text-xs px-2.5 py-1 font-semibold">
              {events.length} Upcoming Festivals
            </Badge>
          </div>

          {loadingEvents ? (
            <div className="space-y-4">
              {[...Array(3)].map((_, i) => (
                <Card key={i} className="border border-border bg-card p-5 space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <Skeleton className="h-10 w-10 rounded-lg" />
                      <div className="space-y-2">
                        <Skeleton className="h-5 w-48 rounded" />
                        <Skeleton className="h-3 w-32 rounded" />
                      </div>
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
              No festival events found for this region. Click &quot;AI Festival Discovery&quot; above to search.
            </Card>
          ) : (
            <div className="space-y-4">
              {events.map((evt, idx) => {
                const matched = evt.matched_inventory_items || [];
                return (
                  <Card key={idx} className="border border-border bg-card shadow-xs overflow-hidden">
                    <CardContent className="p-5 space-y-4">
                      {/* Festival Top Row */}
                      <div className="flex items-start justify-between gap-3">
                        <div className="flex items-center gap-3">
                          <span className="text-3xl">{evt.icon || "🪔"}</span>
                          <div>
                            <h4 className="text-base sm:text-lg font-bold text-foreground">{evt.name}</h4>
                            <p className="text-xs sm:text-sm text-muted-foreground">
                              {evt.date_window} • <span className="font-semibold text-foreground">{evt.region}</span>
                            </p>
                          </div>
                        </div>
                        <Badge variant="outline" className="border-border bg-muted/60 text-foreground font-semibold text-xs px-2.5 py-1 shrink-0">
                          <Flame className="h-3.5 w-3.5 mr-1 text-foreground" />
                          +{Math.round(evt.demand_lift_pct)}% Surge
                        </Badge>
                      </div>

                      {/* Description */}
                      <p className="text-sm text-muted-foreground leading-relaxed">{evt.description}</p>

                      {/* Cultural Tradition Note */}
                      {evt.tradition_notes && (
                        <div className="p-3 rounded-lg bg-muted/40 border border-border/70 text-xs sm:text-sm text-foreground">
                          <span className="font-semibold">✨ Cultural Retail Tradition:</span> {evt.tradition_notes}
                        </div>
                      )}

                      {/* Live Store SKUs Matching Demand */}
                      {matched.length > 0 && (
                        <div className="p-3.5 rounded-lg border border-border bg-muted/20 space-y-2">
                          <div className="flex items-center justify-between text-xs font-semibold">
                            <span className="text-foreground flex items-center gap-1.5">
                              <Package className="h-3.5 w-3.5" />
                              Live Store SKUs Matching Demand ({matched.length}):
                            </span>
                            <span className="text-foreground flex items-center gap-1">
                              <CheckCircle2 className="h-3.5 w-3.5" /> High Margin &amp; Ready
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
                            <div className="font-semibold text-foreground flex items-center gap-1 mb-1">
                              <Clock className="h-3.5 w-3.5" /> T-14d Procurement:
                            </div>
                            <div className="text-muted-foreground">{evt.advance_procurement_window}</div>
                          </div>
                        )}
                        {evt.promo_launch_window && (
                          <div className="p-2.5 rounded-md border border-border bg-muted/20">
                            <div className="font-semibold text-foreground flex items-center gap-1 mb-1">
                              <Flame className="h-3.5 w-3.5" /> T-7d Promo Launch:
                            </div>
                            <div className="text-muted-foreground">{evt.promo_launch_window}</div>
                          </div>
                        )}
                        {evt.clearance_window && (
                          <div className="p-2.5 rounded-md border border-border bg-muted/20">
                            <div className="font-semibold text-foreground flex items-center gap-1 mb-1">
                              <TrendingUp className="h-3.5 w-3.5" /> T+2d Clearance:
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
                              🏷️ {item}
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
                        className="w-full font-semibold h-11 bg-primary text-primary-foreground hover:bg-primary/90 flex items-center justify-center gap-2"
                      >
                        <Sparkles className="h-4 w-4" />
                        Generate AI Promo Offer for {evt.name.split("(")[0].trim()}
                      </Button>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          )}
        </div>

        {/* Right Column: Scheduled Offers & Conflict Sandbox */}
        <div className="lg:col-span-5 space-y-6">
          {/* Active Store Offers */}
          <div className="space-y-4">
            <div className="flex items-center justify-between pb-1">
              <h3 className="text-lg font-semibold text-foreground">Active &amp; Scheduled Store Offers</h3>
              <Badge variant="outline" className="text-xs px-2.5 py-1 font-semibold">
                {activeOffers.length} Active
              </Badge>
            </div>

            {loadingOffers ? (
              <div className="space-y-3">
                {[...Array(2)].map((_, i) => (
                  <Card key={i} className="border border-border bg-card p-4 space-y-2">
                    <div className="flex items-center justify-between">
                      <Skeleton className="h-4 w-36 rounded" />
                      <Skeleton className="h-4 w-16 rounded-full" />
                    </div>
                    <Skeleton className="h-3 w-48 rounded" />
                    <Skeleton className="h-3 w-32 rounded" />
                  </Card>
                ))}
              </div>
            ) : activeOffers.length === 0 ? (
              <Card className="border border-border p-6 text-center text-sm text-muted-foreground">
                No active scheduled promotions currently running.
              </Card>
            ) : (
              <div className="space-y-3">
                {activeOffers.map((off, idx) => (
                  <Card key={idx} className="border border-border bg-card shadow-xs">
                    <CardContent className="p-4 flex items-start justify-between gap-3">
                      <div className="space-y-1">
                        <div className="font-semibold text-foreground text-sm">{off.title}</div>
                        <p className="text-xs text-muted-foreground">
                          📅 {off.start_date} to {off.end_date} •{" "}
                          <strong className="text-foreground">{off.discount_pct}% OFF (₹{off.combo_price})</strong>
                        </p>
                        <p className="text-xs text-muted-foreground font-mono">
                          SKUs: {off.anchor_id} + {off.attached_id}
                        </p>
                      </div>
                      <Badge variant="outline" className="bg-muted text-foreground border-border text-xs shrink-0 font-medium">
                        {off.status}
                      </Badge>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </div>

          {/* Interactive Conflict Check Sandbox */}
          <Card className="border border-border bg-card shadow-xs">
            <CardHeader className="pb-3">
              <div className="flex items-center gap-2">
                <ShieldCheck className="h-5 w-5 text-foreground" />
                <CardTitle className="text-base font-bold">Test New Proposed Offer for Conflicts</CardTitle>
              </div>
              <CardDescription className="text-xs text-muted-foreground leading-relaxed">
                Simulate a prospective offer to check if it overlaps with an active promotion on the same SKU, preventing margin cannibalization.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-foreground">Check SKU:</label>
                <CustomSelect
                  value={conflictSku}
                  onChange={setConflictSku}
                  options={inventoryItems.map((item) => ({
                    value: item.id,
                    label: `${item.name} (${item.id})`,
                    sublabel: `₹${Math.round(item.selling_price)} • Stock: ${item.stock_quantity}`,
                  }))}
                  placeholder="Select SKU to test for conflicts..."
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-foreground">Proposed Discount %:</label>
                  <Input
                    type="number"
                    min="5"
                    max="50"
                    value={conflictDiscount}
                    onChange={(e) => setConflictDiscount(Number(e.target.value))}
                    className="h-10 text-sm bg-background border-border"
                  />
                </div>
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-foreground">Simulation Window:</label>
                  <Input
                    type="text"
                    value="Oct 20 - Oct 30, 2026"
                    readOnly
                    className="h-10 text-sm bg-muted/40 border-border text-muted-foreground"
                  />
                </div>
              </div>

              <Button
                onClick={handleConflictCheck}
                disabled={!conflictSku || checkingConflict}
                variant="outline"
                className="w-full font-semibold h-10 border-border bg-secondary text-secondary-foreground hover:bg-secondary/80 flex items-center justify-center gap-2"
              >
                {checkingConflict ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Simulating Collision Engine...
                  </>
                ) : (
                  <>
                    <ShieldCheck className="h-4 w-4" />
                    Check for Overlap &amp; Cannibalization
                  </>
                )}
              </Button>

              {/* Sandbox Result */}
              {conflictResult && (
                <div
                  className={`p-3.5 rounded-lg border text-xs sm:text-sm space-y-1.5 ${
                    conflictResult.has_conflict
                      ? "border-amber-600/40 bg-amber-500/10 text-foreground"
                      : "border-border bg-muted/40 text-foreground"
                  }`}
                >
                  <div className="font-bold flex items-center gap-1.5">
                    {conflictResult.has_conflict ? (
                      <>
                        <AlertTriangle className="h-4 w-4 text-amber-500" />
                        OFFER CONFLICT DETECTED!
                      </>
                    ) : (
                      <>
                        <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                        NO OVERLAPPING CONFLICTS!
                      </>
                    )}
                  </div>
                  {conflictResult.conflict_reason && (
                    <p className="text-muted-foreground">{conflictResult.conflict_reason}</p>
                  )}
                  <p className="text-foreground font-medium pt-1">
                    <strong>Strategy:</strong> {conflictResult.recommended_action}
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

