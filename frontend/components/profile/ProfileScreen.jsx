"use client";

import { useState, useEffect } from "react";
import {
  fetchStoreProfile,
  saveStoreProfile,
  fetchStorageStatus,
  fetchStores,
  loginStore,
  createOrSwitchStore,
  switchUserStore,
  configureGeminiApiKey,
} from "@/lib/api";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { CustomSelect } from "@/components/ui/custom-select";
import {
  Store,
  CheckCircle2,
  AlertCircle,
  AlertTriangle,
  Save,
  Loader2,
  Moon,
  Sun,
  RefreshCw,
  KeyRound,
  LogIn,
  User,
  Plus,
  Building2,
  LogOut,
  Sparkles,
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
  { value: "Tamil Nadu & South India", label: "Tamil Nadu & South India (Pongal, Karthigai)" },
  { value: "Gujarat & West India", label: "Gujarat & West India (Navratri, Uttarayan)" },
  { value: "Kerala & South India", label: "Kerala & South India (Onam, Vishu)" },
];

export function ProfileScreen({
  currentUser,
  onProfileUpdated,
  onOpenLoginModal,
  onUserSignOut,
}) {
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState(false);
  const [isFallback, setIsFallback] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  // Store Management state
  const [availableStores, setAvailableStores] = useState([]);
  const [activeStoreId, setActiveStoreId] = useState("sharma_supermarket_01");
  const [geminiApiKey, setGeminiApiKey] = useState("");
  const [apiKeySaved, setApiKeySaved] = useState(false);

  // Create New Store under User state
  const [isCreatingStore, setIsCreatingStore] = useState(false);
  const [newStoreName, setNewStoreName] = useState("");
  const [newStoreFormat, setNewStoreFormat] = useState("Supermarket");
  const [newStoreCity, setNewStoreCity] = useState("Bengaluru");
  const [newStoreRegion, setNewStoreRegion] = useState("Karnataka & South India");
  const [newStoreCapital, setNewStoreCapital] = useState(500000);
  const [newStoreMargin, setNewStoreMargin] = useState(18.0);
  const [creatingStoreLoading, setCreatingStoreLoading] = useState(false);
  const [createStoreError, setCreateStoreError] = useState("");

  // Form fields
  const [storeName, setStoreName] = useState("");
  const [ownerName, setOwnerName] = useState("");
  const [phone, setPhone] = useState("");
  const [gstin, setGstin] = useState("");
  const [storeType, setStoreType] = useState("Supermarket");
  const [audienceSize, setAudienceSize] = useState(1420);
  const [workingCapital, setWorkingCapital] = useState(500000);
  const [minMargin, setMinMargin] = useState(18.0);

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
    store_id: "sharma_supermarket_01",
    gemini_live_active: true,
  });

  useEffect(() => {
    loadProfileData();
    loadStorageData();
    loadStoresRegistry();

    if (typeof window !== "undefined") {
      setGeminiApiKey(localStorage.getItem("promomind_gemini_api_key") || "");
    }
    if (typeof document !== "undefined") {
      const isDark = document.documentElement.classList.contains("dark");
      setThemeMode(isDark ? "dark" : "light");
    }
  }, [currentUser?.user_id]);

  async function loadStoresRegistry() {
    try {
      const uid = currentUser?.user_id;
      const res = await fetchStores(uid);
      if (res && Array.isArray(res.stores)) {
        setAvailableStores(res.stores);
        if (res.active_store_id) setActiveStoreId(res.active_store_id);
      }
    } catch (e) {
      console.warn("Could not query stores registry:", e);
    }
  }

  async function loadStorageData() {
    try {
      const st = await fetchStorageStatus();
      if (st) {
        setStorageInfo(st);
        if (st.store_id) setActiveStoreId(st.store_id);
      }
    } catch (e) {
      console.warn("Could not query storage status:", e);
    }
  }

  async function handleQuickSwitchStore(targetId) {
    setActiveStoreId(targetId);
    if (typeof window !== "undefined") {
      localStorage.setItem("promomind_store_id", targetId);
    }
    try {
      let res;
      if (currentUser?.user_id) {
        res = await switchUserStore(targetId, currentUser.user_id);
      } else {
        res = await loginStore({ store_id: targetId });
      }
      if (res && res.profile) {
        populateFields(res.profile);
        if (onProfileUpdated) onProfileUpdated(res.profile);
        await loadStorageData();
      }
    } catch (e) {
      console.warn("Store switch attempt 1 failed, trying fallback:", e);
      try {
        const fallbackRes = await loginStore({ store_id: targetId });
        if (fallbackRes && fallbackRes.profile) {
          populateFields(fallbackRes.profile);
          if (onProfileUpdated) onProfileUpdated(fallbackRes.profile);
          await loadStorageData();
        }
      } catch (err2) {
        console.error("Store switch fallback failed:", err2);
      }
    }
  }

  async function handleCreateNewStore(e) {
    if (e) e.preventDefault();
    if (!newStoreName.trim()) {
      setCreateStoreError("Please enter a valid store branch name.");
      return;
    }
    setCreatingStoreLoading(true);
    setCreateStoreError("");

    const payload = {
      store_name: newStoreName.trim(),
      store_type: newStoreFormat,
      city: newStoreCity.trim() || "Bengaluru",
      region: newStoreRegion,
      total_working_capital_inr: Number(newStoreCapital) || 500000,
      default_min_margin_pct: Number(newStoreMargin) || 18.0,
      owner_name: currentUser?.full_name || ownerName || "Store Owner",
      phone: currentUser?.phone || phone || "+91 98450 12345",
    };

    try {
      const res = await createOrSwitchStore(payload);
      if (res && res.profile) {
        populateFields(res.profile);
        if (res.active_store_id) {
          setActiveStoreId(res.active_store_id);
          if (typeof window !== "undefined") {
            localStorage.setItem("promomind_store_id", res.active_store_id);
          }
        }
        if (res.stores && Array.isArray(res.stores)) {
          setAvailableStores(res.stores);
        } else {
          await loadStoresRegistry();
        }
        await loadStorageData();
        if (onProfileUpdated) {
          onProfileUpdated(res.profile);
        }
        setIsCreatingStore(false);
        setNewStoreName("");
        setSaveSuccess(true);
        setTimeout(() => setSaveSuccess(false), 3500);
      }
    } catch (err) {
      console.error("Failed creating store:", err);
      setCreateStoreError(err.message || "Failed to create store branch under this user.");
    } finally {
      setCreatingStoreLoading(false);
    }
  }

  async function handleSaveApiKey() {
    if (!geminiApiKey.trim()) return;
    if (typeof window !== "undefined") {
      localStorage.setItem("promomind_gemini_api_key", geminiApiKey.trim());
    }
    try {
      await configureGeminiApiKey(geminiApiKey.trim());
      setApiKeySaved(true);
      await loadStorageData();
      setTimeout(() => setApiKeySaved(false), 3000);
    } catch (e) {
      console.error("Failed configuring API key:", e);
    }
  }

  async function loadProfileData() {
    setLoading(true);
    setLoadError(false);
    setIsFallback(false);

    try {
      const prof = await fetchStoreProfile();
      if (prof && (prof.store_name || prof.owner_name)) {
        populateFields(prof);
        setLoading(false);
        return;
      }
      throw new Error("Empty remote profile received");
    } catch (e) {
      console.warn("Remote profile fetch failed, checking local cache:", e);
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
            min_gross_margin_target_pct: parseFloat(localStorage.getItem("promomind_margin") || "18.0"),
          };
          populateFields(fallbackProf);
          setIsFallback(true);
          setLoading(false);
          return;
        }
      }

      setLoadError(true);
      populateFields({
        store_name: "Sharma Supermarket & Provisions",
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
        min_gross_margin_target_pct: 18.0,
      });
      setLoading(false);
    }
  }

  function populateFields(prof) {
    if (prof.store_id) setActiveStoreId(prof.store_id);
    setStoreName(prof.store_name || "Sharma Supermarket & Provisions");
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
    setMinMargin(margin || 18.0);
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
      store_id: activeStoreId,
      store_name: storeName.trim(),
      owner_name: ownerName.trim(),
      phone: phone.trim(),
      gstin: gstin.trim(),
      store_type: storeType,
      audience_size: Number(audienceSize),
      whatsapp_audience_size: Number(audienceSize),
      total_working_capital_inr: Number(workingCapital),
      default_min_margin_pct: Number(minMargin),
      region: stateRegion,
      city: city.trim(),
      locality: locality.trim(),
      pin_code: pinCode.trim(),
    };

    if (typeof window !== "undefined") {
      localStorage.setItem("promomind_store_id", payload.store_id);
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
      localStorage.setItem("promomind_capital", String(payload.total_working_capital_inr));
      localStorage.setItem("promomind_margin", String(payload.default_min_margin_pct));
    }

    try {
      await saveStoreProfile(payload);
      setSaveSuccess(true);
      setIsFallback(false);
      setLoadError(false);
      await loadStoresRegistry();

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

  if (loading) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between border-b border-border pb-4">
          <div className="space-y-2">
            <Skeleton className="h-8 w-64 rounded-md" />
            <Skeleton className="h-4 w-96 rounded-md" />
          </div>
          <Skeleton className="h-10 w-32 rounded-md" />
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card className="border border-border bg-card p-5 space-y-5">
            <Skeleton className="h-5 w-40 rounded" />
            <Skeleton className="h-32 w-full rounded" />
          </Card>
          <Card className="border border-border bg-card p-5 space-y-5">
            <Skeleton className="h-5 w-44 rounded" />
            <Skeleton className="h-32 w-full rounded" />
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
            Store Management, Login &amp; Regional Settings
          </h2>
          <p className="text-sm text-muted-foreground mt-1">
            Manage multi-store Firestore profiles, regional demographics, and live Gemini API credentials.
          </p>
        </div>
        <div className="flex items-center gap-2">
          {saveSuccess && (
            <span className="text-xs font-semibold text-emerald-500 flex items-center gap-1.5 mr-2">
              <CheckCircle2 className="h-4 w-4" /> Profile Saved!
            </span>
          )}
          {onOpenLoginModal && (
            <Button
              variant="outline"
              onClick={onOpenLoginModal}
              className="h-10 px-4 text-xs font-semibold border-border flex items-center gap-1.5"
            >
              <LogIn className="h-4 w-4" />
              Switch / Add Store
            </Button>
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

      {/* 1. User Account Profile Banner */}
      <Card className="border border-border bg-card shadow-xs overflow-hidden">
        <div className="p-5 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div className="flex items-center gap-3.5">
            <div className="h-12 w-12 rounded-full bg-foreground/10 text-foreground flex items-center justify-center font-bold text-lg border border-border shrink-0">
              {currentUser?.full_name ? (
                currentUser.full_name.charAt(0).toUpperCase()
              ) : (
                <User className="h-6 w-6" />
              )}
            </div>
            <div>
              <div className="flex items-center gap-2 flex-wrap">
                <h3 className="text-base font-bold text-foreground">
                  {currentUser?.full_name || "Merchant Account"}
                </h3>
                <Badge
                  variant="outline"
                  className="border-border bg-muted/60 text-[11px] font-semibold text-foreground"
                >
                  {currentUser ? "Registered User" : "Retailer Session"}
                </Badge>
              </div>
              <div className="text-xs text-muted-foreground flex items-center gap-3 mt-1 flex-wrap">
                <span>{currentUser?.email || "No email linked"}</span>
                {currentUser?.phone && (
                  <>
                    <span>•</span>
                    <span>{currentUser.phone}</span>
                  </>
                )}
                <span>•</span>
                <span>
                  Active Branch: <strong className="text-foreground">{activeStoreId}</strong>
                </span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2 shrink-0">
            {onOpenLoginModal && (
              <Button
                variant="outline"
                size="sm"
                onClick={onOpenLoginModal}
                className="h-9 px-3 text-xs font-semibold border-border gap-1.5"
              >
                <LogIn className="h-3.5 w-3.5" />
                {currentUser ? "Switch Account" : "Sign In / Sign Up"}
              </Button>
            )}
            {currentUser && onUserSignOut && (
              <Button
                variant="outline"
                size="sm"
                onClick={onUserSignOut}
                className="h-9 px-3 text-xs font-semibold border-destructive/40 text-destructive hover:bg-destructive/10 gap-1.5"
              >
                <LogOut className="h-3.5 w-3.5" />
                Sign Out
              </Button>
            )}
          </div>
        </div>
      </Card>

      {/* 2. Stores Under Your User Account (Multi-Store Management & Inline Creation) */}
      <Card className="border border-border bg-card shadow-xs">
        <CardHeader className="pb-3 border-b border-border">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
            <div>
              <CardTitle className="text-base font-bold text-foreground flex items-center gap-2">
                <Building2 className="h-4 w-4 text-foreground" />
                Stores Under Your User Account
                <Badge variant="secondary" className="ml-1 text-[11px] font-semibold">
                  {availableStores.length} {availableStores.length === 1 ? "Store" : "Stores"}
                </Badge>
              </CardTitle>
              <CardDescription className="text-xs text-muted-foreground mt-0.5">
                Select an active store branch to manage inventory &amp; promotions, or create a new store.
              </CardDescription>
            </div>
            <Button
              variant={isCreatingStore ? "secondary" : "outline"}
              size="sm"
              onClick={() => setIsCreatingStore(!isCreatingStore)}
              className="h-8 px-3 text-xs font-semibold gap-1.5 self-start sm:self-auto"
            >
              <Plus className={`h-3.5 w-3.5 transition-transform ${isCreatingStore ? "rotate-45" : ""}`} />
              {isCreatingStore ? "Close Form" : "Create New Store"}
            </Button>
          </div>
        </CardHeader>
        <CardContent className="p-5 space-y-5">
          {/* List of Store Branches */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {availableStores.map((st) => {
              const isCurr = st.store_id === activeStoreId;
              return (
                <div
                  key={st.store_id}
                  onClick={() => handleQuickSwitchStore(st.store_id)}
                  className={`p-3.5 rounded-xl border text-left cursor-pointer transition-all ${
                    isCurr
                      ? "border-foreground bg-muted/60 ring-1 ring-foreground"
                      : "border-border bg-card hover:bg-muted/30"
                  }`}
                >
                  <div className="flex items-start justify-between gap-2 mb-1.5">
                    <span className="font-semibold text-sm text-foreground truncate">
                      {st.store_name}
                    </span>
                    {isCurr ? (
                      <Badge className="bg-foreground text-background text-[10px] px-1.5 py-0 font-bold shrink-0">
                        Active
                      </Badge>
                    ) : (
                      <span className="text-[10px] text-muted-foreground border border-border px-1.5 py-0.5 rounded shrink-0">
                        Switch
                      </span>
                    )}
                  </div>
                  <div className="text-xs text-muted-foreground flex items-center gap-1.5">
                    <span>{st.city || "India"}</span>
                    <span>•</span>
                    <span>{st.store_type || "Retail"}</span>
                  </div>
                  <div className="text-[11px] text-muted-foreground/80 mt-1 font-mono">
                    ID: {st.store_id}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Inline Create New Store Form */}
          {isCreatingStore && (
            <div className="p-4 sm:p-5 rounded-xl border border-border bg-muted/20 space-y-4">
              <div className="flex items-center justify-between border-b border-border pb-3">
                <div>
                  <h4 className="text-sm font-bold text-foreground flex items-center gap-2">
                    <Store className="h-4 w-4" />
                    Create New Store Branch
                  </h4>
                  <p className="text-xs text-muted-foreground mt-0.5">
                    Set up a new physical or cloud store profile under your user account.
                  </p>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setIsCreatingStore(false)}
                  className="h-7 w-7 p-0 text-muted-foreground hover:text-foreground"
                >
                  ✕
                </Button>
              </div>

              {createStoreError && (
                <div className="p-2.5 rounded-lg border border-destructive/40 bg-destructive/10 text-xs text-destructive flex items-center gap-2">
                  <AlertCircle className="h-3.5 w-3.5 shrink-0" />
                  <span>{createStoreError}</span>
                </div>
              )}

              <form onSubmit={handleCreateNewStore} className="space-y-4">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold text-foreground">
                      Store Name <span className="text-destructive">*</span>
                    </label>
                    <Input
                      placeholder="e.g. Sharma Organic Mart"
                      value={newStoreName}
                      onChange={(e) => setNewStoreName(e.target.value)}
                      className="h-9 text-xs bg-background"
                      required
                    />
                  </div>
                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold text-foreground">Store Format</label>
                    <CustomSelect
                      value={newStoreFormat}
                      onChange={setNewStoreFormat}
                      options={STORE_FORMAT_OPTIONS}
                      placeholder="Select format..."
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold text-foreground">City / District</label>
                    <Input
                      placeholder="e.g. Bengaluru"
                      value={newStoreCity}
                      onChange={(e) => setNewStoreCity(e.target.value)}
                      className="h-9 text-xs bg-background"
                    />
                  </div>
                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold text-foreground">Region / Demographics</label>
                    <CustomSelect
                      value={newStoreRegion}
                      onChange={setNewStoreRegion}
                      options={REGION_OPTIONS}
                      placeholder="Select region..."
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold text-foreground">Initial Working Capital (₹)</label>
                    <Input
                      type="number"
                      step="25000"
                      value={newStoreCapital}
                      onChange={(e) => setNewStoreCapital(Number(e.target.value))}
                      className="h-9 text-xs bg-background"
                    />
                  </div>
                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold text-foreground">Target Margin (%)</label>
                    <Input
                      type="number"
                      step="0.5"
                      value={newStoreMargin}
                      onChange={(e) => setNewStoreMargin(Number(e.target.value))}
                      className="h-9 text-xs bg-background"
                    />
                  </div>
                </div>

                <div className="flex justify-end gap-2 pt-2">
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => setIsCreatingStore(false)}
                    className="h-9 px-4 text-xs"
                  >
                    Cancel
                  </Button>
                  <Button
                    type="submit"
                    size="sm"
                    disabled={creatingStoreLoading || !newStoreName.trim()}
                    className="h-9 px-4 text-xs font-semibold bg-primary text-primary-foreground hover:bg-primary/90 gap-1.5"
                  >
                    {creatingStoreLoading ? (
                      <>
                        <Loader2 className="h-3.5 w-3.5 animate-spin" />
                        Creating Store...
                      </>
                    ) : (
                      <>
                        <Sparkles className="h-3.5 w-3.5" />
                        Create Store &amp; Activate
                      </>
                    )}
                  </Button>
                </div>
              </form>
            </div>
          )}

          {/* Live Gemini API Key Bar */}
          <div className="pt-2 border-t border-border">
            <label className="text-xs font-bold uppercase tracking-wider text-foreground flex items-center gap-1.5 mb-2">
              <KeyRound className="h-3.5 w-3.5" />
              Live Gemini API Key (Runtime Override):
            </label>
            <div className="flex gap-2">
              <Input
                type="password"
                placeholder="Paste AIza... or AQ.... key to override server .env"
                value={geminiApiKey}
                onChange={(e) => setGeminiApiKey(e.target.value)}
                className="h-9 text-xs font-mono bg-background"
              />
              <Button
                type="button"
                size="sm"
                onClick={handleSaveApiKey}
                className="h-9 px-4 text-xs font-semibold shrink-0"
              >
                {apiKeySaved ? "Key Active!" : "Apply Key"}
              </Button>
            </div>
            <p className="text-[11px] text-muted-foreground mt-1">
              Supports both Google AI Studio keys (<code className="font-mono">AIza...</code>) and Vertex AI Express keys (<code className="font-mono">AQ....</code>).
            </p>
          </div>
        </CardContent>
      </Card>

      {isFallback && (
        <div className="p-3.5 rounded-lg border border-amber-500/40 bg-amber-500/10 text-foreground flex items-center justify-between text-xs sm:text-sm">
          <div className="flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 text-amber-500 shrink-0" />
            <span>
              <strong>Offline Cached Profile:</strong> Displaying your last saved local settings.
            </span>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={loadProfileData}
            className="h-8 text-xs font-medium border-border hover:bg-muted ml-3 shrink-0"
          >
            <RefreshCw className="h-3 w-3 mr-1" /> Retry Sync
          </Button>
        </div>
      )}

      {loadError && (
        <div className="p-3.5 rounded-lg border border-destructive/40 bg-destructive/10 text-foreground flex items-center justify-between text-xs sm:text-sm">
          <div className="flex items-center gap-2">
            <AlertCircle className="h-4 w-4 text-destructive shrink-0" />
            <span>
              <strong>Could not reach profile server.</strong> Default settings loaded.
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
                Active Store: {activeStoreId}
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
                <label className="text-xs font-semibold text-foreground">State &amp; Cultural Region (Type Any State / Region):</label>
                <Input
                  type="text"
                  placeholder="e.g. Karnataka, Maharashtra, Telangana, Gujarat..."
                  value={stateRegion}
                  onChange={(e) => setStateRegion(e.target.value)}
                  className="h-10 text-sm bg-background border-border"
                />
                <div className="flex flex-wrap gap-1 pt-1">
                  {REGION_OPTIONS.slice(0, 4).map((opt) => (
                    <button
                      key={opt.value}
                      type="button"
                      onClick={() => setStateRegion(opt.value)}
                      className="text-[10px] px-2 py-0.5 rounded border border-border bg-muted/40 hover:bg-muted text-muted-foreground hover:text-foreground transition-colors"
                    >
                      {opt.value.split("&")[0].trim()}
                    </button>
                  ))}
                </div>
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
              <strong>Geographic Grounding:</strong> Regional Demographics feed directly into live Gemini Festival Discovery and localize vernacular messaging scripts across POS cashier cards and WhatsApp broadcasts.
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
                  Minimalist high-contrast monochrome design.
                </p>
              </div>

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
                  Neutral daylight surfaces with sharp typography.
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
                Cloud Architecture &amp; Live Engine Status
              </CardTitle>
              <Badge variant="outline" className="border-border bg-muted/60 text-xs font-semibold text-foreground">
                Live System Metrics
              </Badge>
            </div>
          </CardHeader>
          <CardContent className="p-5 space-y-3 text-xs sm:text-sm">
            <div className="flex items-center justify-between py-1.5 border-b border-border/50">
              <span className="text-muted-foreground font-medium">Live Gemini Search Engine:</span>
              <span className="font-semibold text-emerald-600 dark:text-emerald-400">
                {storageInfo?.gemini_live_active ? "Active (Real-Time Search Generation)" : "Standby"}
              </span>
            </div>

            <div className="flex items-center justify-between py-1.5 border-b border-border/50">
              <span className="text-muted-foreground font-medium">Storage Adapter Mode:</span>
              <span className="font-semibold text-foreground">
                {storageInfo?.mode === "CLOUD" && storageInfo?.firestore_connected
                  ? "Cloud Mode (Firestore Live)"
                  : "Hybrid Adapter Active"}
              </span>
            </div>

            <div className="flex items-center justify-between py-1.5 border-b border-border/50">
              <span className="text-muted-foreground font-medium">Firestore Namespace:</span>
              <span className="font-mono text-xs text-foreground bg-muted/60 px-2 py-0.5 rounded border border-border">
                stores/{storageInfo?.store_id || activeStoreId}/...
              </span>
            </div>

            <div className="flex items-center justify-between py-1.5 border-b border-border/50">
              <span className="text-muted-foreground font-medium">Demand Forecasting Engine:</span>
              <span className="font-semibold text-foreground">Holt-Winters Double Exponential Smoothing</span>
            </div>

            <div className="flex items-center justify-between py-1.5">
              <span className="text-muted-foreground font-medium">Smart Pairing Algorithm:</span>
              <span className="font-semibold text-foreground">Gemini Semantic Matching + Apriori Lift</span>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
