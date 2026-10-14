"use client";

import { useState, useEffect } from "react";
import {
  fetchStoreProfile,
  saveStoreProfile,
  fetchStorageStatus,
} from "@/lib/api";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { CustomSelect } from "@/components/ui/custom-select";
import {
  Store,
  User,
  Phone,
  Building,
  MapPin,
  Coins,
  Percent,
  CheckCircle2,
  AlertCircle,
  AlertTriangle,
  Save,
  Loader2,
  Database,
  Moon,
  Sun,
  Server,
  Layers,
  RefreshCw,
} from "lucide-react";

const STORE_FORMAT_OPTIONS = [
  { value: "Supermarket", label: "Supermarket / Self-Service Mart" },
  { value: "Retail", label: "Neighborhood Retail Mart" },
  { value: "Departmental", label: "Departmental Grocery" },
  { value: "Organic", label: "Organic & Gourmet Store" },
];

const REGION_OPTIONS = [
  { value: "Karnataka & South India", label: "Karnataka & South India (Deepas, Ghee, Sweets)" },
  { value: "Maharashtra & West India", label: "Maharashtra & West India (Ganesh, Modak, Diwali)" },
  { value: "Delhi-NCR & North India", label: "Delhi-NCR & North India (Karwa Chauth, Diwali)" },
  { value: "West Bengal & East India", label: "West Bengal & East India (Durga Puja, Sweets)" },
];

export function ProfileScreen({ onProfileUpdated }) {
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState(false);
  const [isFallback, setIsFallback] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  // Form fields
  const [storeName, setStoreName] = useState("");
  const [ownerName, setOwnerName] = useState("");
  const [phone, setPhone] = useState("");
  const [gstin, setGstin] = useState("");
  const [storeType, setStoreType] = useState("Supermarket");
  const [audienceSize, setAudienceSize] = useState(1420);
  const [workingCapital, setWorkingCapital] = useState(500000);
  const [minMargin, setMinMargin] = useState(15.0);

  // Regional Demographics
  const [stateRegion, setStateRegion] = useState("Karnataka & South India");
  const [city, setCity] = useState("");
  const [locality, setLocality] = useState("");
  const [pinCode, setPinCode] = useState("");

  // Theme selection
  const [themeMode, setThemeMode] = useState("dark");

  // Live Storage metrics
  const [storageInfo, setStorageInfo] = useState({
    mode: "CLOUD",
    firestore_connected: true,
    store_id: "store_blr_001",
  });

  useEffect(() => {
    loadProfileData();
    loadStorageData();

    if (typeof document !== "undefined") {
      const isDark = document.documentElement.classList.contains("dark");
      setThemeMode(isDark ? "dark" : "light");
    }
  }, []);

  async function loadStorageData() {
    try {
      const st = await fetchStorageStatus();
      if (st) setStorageInfo(st);
    } catch (e) {
      console.warn("Could not query storage status:", e);
    }
  }

  async function loadProfileData() {
    setLoading(true);
    setLoadError(false);
    setIsFallback(false);

    try {
      // 1. Try remote API first
      const prof = await fetchStoreProfile();
      if (prof && (prof.store_name || prof.owner_name)) {
        populateFields(prof);
        setLoading(false);
        return;
      }
      throw new Error("Empty remote profile received");
    } catch (e) {
      console.warn("Remote profile fetch failed, checking local cache:", e);
      // Fallback to localStorage
      if (typeof window !== "undefined") {
        const cachedStore = localStorage.getItem("promomind_store_name");
        if (cachedStore) {
          const fallbackProf = {
            store_name: cachedStore,
            owner_name: localStorage.getItem("promomind_owner_name") || "Ramesh Sharma",
            phone: localStorage.getItem("promomind_phone") || "+91 98450 12345",
            gstin: localStorage.getItem("promomind_gstin") || "29AAAAA0000A1Z5",
            store_type: localStorage.getItem("promomind_store_type") || "Supermarket",
            audience_size: parseInt(localStorage.getItem("promomind_audience") || "1420", 10),
            region: localStorage.getItem("promomind_region") || "Karnataka & South India",
            city: localStorage.getItem("promomind_city") || "Bengaluru",
            locality: localStorage.getItem("promomind_locality") || "Koramangala 4th Block",
            pin_code: localStorage.getItem("promomind_pin") || "560034",
            working_capital: parseFloat(localStorage.getItem("promomind_capital") || "500000"),
            min_gross_margin_target_pct: parseFloat(localStorage.getItem("promomind_margin") || "15.0"),
          };
          populateFields(fallbackProf);
          setIsFallback(true);
          setLoading(false);
          return;
        }
      }

      // If no remote and no local cache, set default and mark error
      setLoadError(true);
      populateFields({
        store_name: "Metro Supermarket & Retail Mart",
        owner_name: "Ramesh Sharma",
        phone: "+91 98450 12345",
        gstin: "29AAAAA0000A1Z5",
        store_type: "Supermarket",
        audience_size: 1420,
        region: "Karnataka & South India",
        city: "Bengaluru",
        locality: "Koramangala 4th Block",
        pin_code: "560034",
        working_capital: 500000,
        min_gross_margin_target_pct: 15.0,
      });
      setLoading(false);
    }
  }

  function populateFields(prof) {
    setStoreName(prof.store_name || "Metro Supermarket & Retail Mart");
    setOwnerName(prof.owner_name || "Ramesh Sharma");
    setPhone(prof.phone || "+91 98450 12345");
    setGstin(prof.gstin || "29AAAAA0000A1Z5");
    setStoreType(prof.store_type || "Supermarket");

    const aud = prof.audience_size !== undefined ? prof.audience_size : prof.audience_reach;
    setAudienceSize(aud !== undefined && aud !== null ? aud : 1420);

    const reg = prof.region || prof.state_region || "Karnataka & South India";
    setStateRegion(reg);

    setCity(prof.city || "Bengaluru");
    setLocality(prof.locality || "Koramangala 4th Block");

    const pin = prof.pin_code || prof.pincode;
    setPinCode(pin || "560034");

    const cap = prof.total_working_capital_inr || prof.working_capital;
    setWorkingCapital(cap || 500000);

    const margin = prof.default_min_margin_pct || prof.min_gross_margin_target_pct;
    setMinMargin(margin || 15.0);
  }

  function handleThemeChange(mode) {
    setThemeMode(mode);
    if (typeof document !== "undefined") {
      if (mode === "dark") {
        document.documentElement.classList.add("dark");
        localStorage.setItem("promomind_theme", "dark");
      } else {
        document.documentElement.classList.remove("dark");
        localStorage.setItem("promomind_theme", "light");
      }
    }
  }

  async function handleSave() {
    setSaving(true);
    setSaveSuccess(false);

    const payload = {
      store_name: storeName.trim(),
      owner_name: ownerName.trim(),
      phone: phone.trim(),
      gstin: gstin.trim(),
      store_type: storeType,
      audience_size: Number(audienceSize),
      audience_reach: Number(audienceSize),
      working_capital: Number(workingCapital),
      total_working_capital_inr: Number(workingCapital),
      min_gross_margin_target_pct: Number(minMargin),
      default_min_margin_pct: Number(minMargin),
      region: stateRegion,
      state_region: stateRegion,
      city: city.trim(),
      locality: locality.trim(),
      pin_code: pinCode.trim(),
      pincode: pinCode.trim(),
    };

    // Cache in localStorage
    if (typeof window !== "undefined") {
      localStorage.setItem("promomind_store_name", payload.store_name);
      localStorage.setItem("promomind_owner_name", payload.owner_name);
      localStorage.setItem("promomind_phone", payload.phone);
      localStorage.setItem("promomind_gstin", payload.gstin);
      localStorage.setItem("promomind_store_type", payload.store_type);
      localStorage.setItem("promomind_audience", String(payload.audience_size));
      localStorage.setItem("promomind_region", payload.region);
      localStorage.setItem("promomind_city", payload.city);
      localStorage.setItem("promomind_locality", payload.locality);
      localStorage.setItem("promomind_pin", payload.pin_code);
      localStorage.setItem("promomind_capital", String(payload.working_capital));
      localStorage.setItem("promomind_margin", String(payload.min_gross_margin_target_pct));
    }

    try {
      await saveStoreProfile(payload);
      try {
        await fetch("/api/profile", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
      } catch (e) {}

      setSaveSuccess(true);
      setIsFallback(false);
      setLoadError(false);

      if (onProfileUpdated) {
        onProfileUpdated(payload);
      }
      setTimeout(() => setSaveSuccess(false), 3500);
    } catch (e) {
      console.error("Failed to save store profile:", e);
      alert("Error saving profile to backend. Saved locally in browser.");
    } finally {
      setSaving(false);
    }
  }

  // SKELETON LOADER STATE
  if (loading) {
    return (
      <div className="space-y-6 animate-pulse">
        {/* Header Skeleton */}
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between border-b border-border pb-4">
          <div className="space-y-2">
            <Skeleton className="h-8 w-64 rounded-md" />
            <Skeleton className="h-4 w-96 rounded-md" />
          </div>
          <Skeleton className="h-10 w-32 rounded-md" />
        </div>

        {/* 4 Cards Grid Skeleton */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Card 1 Skeleton */}
          <Card className="border border-border bg-card p-5 space-y-5">
            <div className="flex items-center justify-between pb-3 border-b border-border">
              <Skeleton className="h-5 w-40 rounded" />
              <Skeleton className="h-5 w-24 rounded-full" />
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Skeleton className="h-3 w-20 rounded" />
                <Skeleton className="h-10 w-full rounded-md" />
              </div>
              <div className="space-y-2">
                <Skeleton className="h-3 w-28 rounded" />
                <Skeleton className="h-10 w-full rounded-md" />
              </div>
              <div className="space-y-2">
                <Skeleton className="h-3 w-32 rounded" />
                <Skeleton className="h-10 w-full rounded-md" />
              </div>
              <div className="space-y-2">
                <Skeleton className="h-3 w-28 rounded" />
                <Skeleton className="h-10 w-full rounded-md" />
              </div>
              <div className="space-y-2">
                <Skeleton className="h-3 w-24 rounded" />
                <Skeleton className="h-10 w-full rounded-md" />
              </div>
              <div className="space-y-2">
                <Skeleton className="h-3 w-32 rounded" />
                <Skeleton className="h-10 w-full rounded-md" />
              </div>
              <div className="space-y-2">
                <Skeleton className="h-3 w-36 rounded" />
                <Skeleton className="h-10 w-full rounded-md" />
              </div>
              <div className="space-y-2">
                <Skeleton className="h-3 w-32 rounded" />
                <Skeleton className="h-10 w-full rounded-md" />
              </div>
            </div>
          </Card>

          {/* Card 2 Skeleton */}
          <Card className="border border-border bg-card p-5 space-y-5">
            <div className="flex items-center justify-between pb-3 border-b border-border">
              <Skeleton className="h-5 w-44 rounded" />
              <Skeleton className="h-5 w-28 rounded-full" />
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Skeleton className="h-3 w-32 rounded" />
                <Skeleton className="h-10 w-full rounded-md" />
              </div>
              <div className="space-y-2">
                <Skeleton className="h-3 w-24 rounded" />
                <Skeleton className="h-10 w-full rounded-md" />
              </div>
              <div className="space-y-2">
                <Skeleton className="h-3 w-24 rounded" />
                <Skeleton className="h-10 w-full rounded-md" />
              </div>
              <div className="space-y-2">
                <Skeleton className="h-3 w-24 rounded" />
                <Skeleton className="h-10 w-full rounded-md" />
              </div>
            </div>
            <Skeleton className="h-16 w-full rounded-lg" />
          </Card>

          {/* Card 3 Skeleton */}
          <Card className="border border-border bg-card p-5 space-y-5">
            <div className="flex items-center justify-between pb-3 border-b border-border">
              <Skeleton className="h-5 w-32 rounded" />
              <Skeleton className="h-5 w-24 rounded-full" />
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <Skeleton className="h-20 w-full rounded-xl" />
              <Skeleton className="h-20 w-full rounded-xl" />
            </div>
          </Card>

          {/* Card 4 Skeleton */}
          <Card className="border border-border bg-card p-5 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-border">
              <Skeleton className="h-5 w-52 rounded" />
              <Skeleton className="h-5 w-28 rounded-full" />
            </div>
            <div className="space-y-3">
              {[...Array(6)].map((_, i) => (
                <div key={i} className="flex items-center justify-between py-1.5 border-b border-border/40">
                  <Skeleton className="h-4 w-40 rounded" />
                  <Skeleton className="h-4 w-48 rounded" />
                </div>
              ))}
            </div>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Screen Header */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between border-b border-border pb-4">
        <div>
          <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
            <Store className="h-6 w-6 text-foreground" />
            Retailer Profile &amp; Regional Settings
          </h2>
          <p className="text-sm text-muted-foreground mt-1">
            Manage store identity, regional location, customer demographics, and appearance preferences.
          </p>
        </div>
        <div className="flex items-center gap-2">
          {saveSuccess && (
            <span className="text-xs font-semibold text-emerald-500 flex items-center gap-1.5 mr-2">
              <CheckCircle2 className="h-4 w-4" /> Profile Saved!
            </span>
          )}
          <Button
            onClick={handleSave}
            disabled={saving || loading}
            className="h-10 px-5 font-semibold bg-primary text-primary-foreground hover:bg-primary/90 flex items-center gap-2"
          >
            {saving ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Saving...
              </>
            ) : (
              <>
                <Save className="h-4 w-4" />
                Save Changes
              </>
            )}
          </Button>
        </div>
      </div>

      {/* Fallback or Error Notification Banner */}
      {isFallback && (
        <div className="p-3.5 rounded-lg border border-amber-500/40 bg-amber-500/10 text-foreground flex items-center justify-between text-xs sm:text-sm">
          <div className="flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 text-amber-500 shrink-0" />
            <span>
              <strong>Offline Cached Profile:</strong> Cloud server was temporarily unreachable. Displaying your last saved local settings.
            </span>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={loadProfileData}
            className="h-8 text-xs font-medium border-border hover:bg-muted ml-3 shrink-0"
          >
            <RefreshCw className="h-3 w-3 mr-1" /> Retry Cloud Sync
          </Button>
        </div>
      )}

      {loadError && (
        <div className="p-3.5 rounded-lg border border-destructive/40 bg-destructive/10 text-foreground flex items-center justify-between text-xs sm:text-sm">
          <div className="flex items-center gap-2">
            <AlertCircle className="h-4 w-4 text-destructive shrink-0" />
            <span>
              <strong>Failed to reach cloud profile server.</strong> Default settings loaded. You can still edit and save changes.
            </span>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={loadProfileData}
            className="h-8 text-xs font-medium border-border hover:bg-muted ml-3 shrink-0"
          >
            <RefreshCw className="h-3 w-3 mr-1" /> Retry
          </Button>
        </div>
      )}

      {/* Profile Form Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Card 1: Store Identity & Contact */}
        <Card className="border border-border bg-card shadow-xs">
          <CardHeader className="pb-3 border-b border-border">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base font-bold text-foreground">
                Store Identity &amp; Contact
              </CardTitle>
              <Badge variant="outline" className="border-border bg-muted/60 text-xs font-semibold text-foreground">
                Active Business
              </Badge>
            </div>
          </CardHeader>
          <CardContent className="p-5 space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-foreground">Store Name:</label>
                <Input
                  value={storeName}
                  onChange={(e) => setStoreName(e.target.value)}
                  className="h-10 text-sm bg-background border-border"
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-foreground">Retailer Owner / Manager:</label>
                <Input
                  value={ownerName}
                  onChange={(e) => setOwnerName(e.target.value)}
                  className="h-10 text-sm bg-background border-border"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-foreground">WhatsApp Business Number:</label>
                <Input
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  className="h-10 text-sm bg-background border-border"
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-foreground">GSTIN / Trade License:</label>
                <Input
                  value={gstin}
                  onChange={(e) => setGstin(e.target.value)}
                  className="h-10 text-sm bg-background border-border font-mono"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-foreground">Store Format:</label>
                <CustomSelect
                  value={storeType}
                  onChange={setStoreType}
                  options={STORE_FORMAT_OPTIONS}
                  placeholder="Select store format..."
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-foreground">Active WhatsApp Customer List:</label>
                <Input
                  type="number"
                  value={audienceSize}
                  onChange={(e) => setAudienceSize(Number(e.target.value))}
                  className="h-10 text-sm bg-background border-border"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-foreground">Total Working Capital Budget (₹):</label>
                <Input
                  type="number"
                  step="25000"
                  value={workingCapital}
                  onChange={(e) => setWorkingCapital(Number(e.target.value))}
                  className="h-10 text-sm bg-background border-border"
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-foreground">Store Margin Threshold (%):</label>
                <Input
                  type="number"
                  step="0.5"
                  value={minMargin}
                  onChange={(e) => setMinMargin(Number(e.target.value))}
                  className="h-10 text-sm bg-background border-border"
                />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Card 2: Regional Demographics */}
        <Card className="border border-border bg-card shadow-xs">
          <CardHeader className="pb-3 border-b border-border">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base font-bold text-foreground">
                Regional Demographics
              </CardTitle>
              <Badge variant="outline" className="border-border bg-muted/60 text-xs font-semibold text-foreground">
                Affects Demand Signals
              </Badge>
            </div>
          </CardHeader>
          <CardContent className="p-5 space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-foreground">State &amp; Cultural Region:</label>
                <CustomSelect
                  value={stateRegion}
                  onChange={setStateRegion}
                  options={REGION_OPTIONS}
                  placeholder="Select state & cultural region..."
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-foreground">City / District:</label>
                <Input
                  value={city}
                  onChange={(e) => setCity(e.target.value)}
                  className="h-10 text-sm bg-background border-border"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-foreground">Locality / Area:</label>
                <Input
                  value={locality}
                  onChange={(e) => setLocality(e.target.value)}
                  className="h-10 text-sm bg-background border-border"
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-foreground">Postal Pin Code:</label>
                <Input
                  value={pinCode}
                  onChange={(e) => setPinCode(e.target.value)}
                  className="h-10 text-sm bg-background border-border font-mono"
                />
              </div>
            </div>

            <div className="p-3.5 rounded-lg border border-border bg-muted/20 text-xs text-muted-foreground leading-relaxed mt-4">
              💡 <strong>Geographic Grounding:</strong> Regional Demographics feed into the Gemini Demand Surge engine and localize vernacular messaging scripts across POS cashier cards and WhatsApp broadcasts.
            </div>
          </CardContent>
        </Card>

        {/* Card 3: Theme & Display */}
        <Card className="border border-border bg-card shadow-xs">
          <CardHeader className="pb-3 border-b border-border">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base font-bold text-foreground">
                Theme &amp; Display
              </CardTitle>
              <Badge variant="outline" className="border-border bg-muted/60 text-xs font-semibold text-foreground">
                Customization
              </Badge>
            </div>
          </CardHeader>
          <CardContent className="p-5 space-y-3">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {/* Dark Slate Option */}
              <div
                onClick={() => handleThemeChange("dark")}
                className={`p-4 rounded-xl border cursor-pointer transition-all ${
                  themeMode === "dark"
                    ? "border-foreground bg-muted/60 ring-1 ring-foreground"
                    : "border-border bg-card hover:bg-muted/30"
                }`}
              >
                <div className="flex items-center gap-2 mb-1.5">
                  <Moon className="h-4 w-4 text-foreground" />
                  <strong className="text-sm font-semibold text-foreground">Modern Dark Slate</strong>
                </div>
                <p className="text-xs text-muted-foreground">
                  Minimalist high-contrast monochrome design inspired by X.com and shadcn UI.
                </p>
              </div>

              {/* Light Option */}
              <div
                onClick={() => handleThemeChange("light")}
                className={`p-4 rounded-xl border cursor-pointer transition-all ${
                  themeMode === "light"
                    ? "border-foreground bg-muted/60 ring-1 ring-foreground"
                    : "border-border bg-card hover:bg-muted/30"
                }`}
              >
                <div className="flex items-center gap-2 mb-1.5">
                  <Sun className="h-4 w-4 text-foreground" />
                  <strong className="text-sm font-semibold text-foreground">Clean Light Mode</strong>
                </div>
                <p className="text-xs text-muted-foreground">
                  Neutral daylight surfaces with sharp typography and high readability.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Card 4: Store Health Summary Card */}
        <Card className="border border-border bg-card shadow-xs">
          <CardHeader className="pb-3 border-b border-border">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base font-bold text-foreground">
                Store Health &amp; Capital Allocation
              </CardTitle>
              <Badge variant="outline" className="border-border bg-muted/60 text-xs font-semibold text-foreground">
                Live System Metrics
              </Badge>
            </div>
          </CardHeader>
          <CardContent className="p-5 space-y-3 text-xs sm:text-sm">
            <div className="flex items-center justify-between py-1.5 border-b border-border/50">
              <span className="text-muted-foreground font-medium">Dual-Mode Storage Adapter:</span>
              <span className="font-semibold text-foreground">
                {storageInfo?.mode === "CLOUD" && storageInfo?.firestore_connected
                  ? "🟢 Cloud Mode (Firestore Live)"
                  : "🟡 Local Fallback Mode (Zero Downtime)"}
              </span>
            </div>

            <div className="flex items-center justify-between py-1.5 border-b border-border/50">
              <span className="text-muted-foreground font-medium">Firestore Collections:</span>
              <span className="font-mono text-xs text-foreground bg-muted/60 px-2 py-0.5 rounded border border-border">
                stores/{storageInfo?.store_id || "store_blr_001"}/...
              </span>
            </div>

            <div className="flex items-center justify-between py-1.5 border-b border-border/50">
              <span className="text-muted-foreground font-medium">Google Cloud Firestore:</span>
              <span className="font-semibold text-foreground">
                {storageInfo?.firestore_connected ? "🟢 Dual-Mode Sync Active" : "🟡 Offline Buffer Active"}
              </span>
            </div>

            <div className="flex items-center justify-between py-1.5 border-b border-border/50">
              <span className="text-muted-foreground font-medium">Open-Source Forecasting Engine:</span>
              <span className="font-semibold text-foreground">Holt-Winters Double Exponential Smoothing</span>
            </div>

            <div className="flex items-center justify-between py-1.5 border-b border-border/50">
              <span className="text-muted-foreground font-medium">Smart Pairing Algorithm:</span>
              <span className="font-semibold text-foreground">Apriori Market Basket Probability (Support/Lift)</span>
            </div>

            <div className="flex items-center justify-between py-1.5">
              <span className="text-muted-foreground font-medium">AI Knowledge Base Sync:</span>
              <span className="font-semibold text-foreground">
                ⚡ Instant Re-compilation Grounded in <code className="font-mono text-xs">store_knowledge.md</code>
              </span>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
