"use client";

import React, { useState, useEffect } from "react";
import { X, Store, KeyRound, Plus, CheckCircle2, LogIn } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { CustomSelect } from "@/components/ui/custom-select";
import {
  loginStore,
  fetchStores,
  createOrSwitchStore,
  configureGeminiApiKey,
} from "@/lib/api";

const REGION_OPTIONS = [
  { value: "Karnataka & South India", label: "Karnataka & South India" },
  { value: "Maharashtra & West India", label: "Maharashtra & West India" },
  { value: "West Bengal & East India", label: "West Bengal & East India" },
  { value: "Delhi-NCR & North India", label: "Delhi-NCR & North India" },
  { value: "Tamil Nadu & South India", label: "Tamil Nadu & South India" },
  { value: "Gujarat & West India", label: "Gujarat & West India" },
  { value: "Kerala & South India", label: "Kerala & South India" },
];

export function LoginStoreModal({
  isOpen,
  onClose,
  currentProfile,
  onStoreAuthenticated,
}) {
  const [mode, setMode] = useState("login"); // "login" | "create"
  const [stores, setStores] = useState([]);
  const [selectedStoreId, setSelectedStoreId] = useState(
    currentProfile?.store_id || "sharma_supermarket_01"
  );
  const [storeNameInput, setStoreNameInput] = useState(
    currentProfile?.store_name || "Sharma Supermarket & Kirana"
  );
  const [ownerInput, setOwnerInput] = useState(
    currentProfile?.owner_name || "Ramesh Sharma"
  );
  const [cityInput, setCityInput] = useState(currentProfile?.city || "Bengaluru");
  const [regionInput, setRegionInput] = useState(
    currentProfile?.region || "Karnataka & South India"
  );
  const [audienceInput, setAudienceInput] = useState(
    currentProfile?.whatsapp_audience_size || currentProfile?.audience_size || 1420
  );
  const [apiKeyInput, setApiKeyInput] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");

  // Create New Store fields
  const [newStoreName, setNewStoreName] = useState("");
  const [newOwnerName, setNewOwnerName] = useState("");
  const [newCity, setNewCity] = useState("Bengaluru");
  const [newRegion, setNewRegion] = useState("Karnataka & South India");
  const [newPhone, setNewPhone] = useState("+91 98450 12345");
  const [newAudience, setNewAudience] = useState(1500);
  const [newCapital, setNewCapital] = useState(500000);

  useEffect(() => {
    if (isOpen) {
      loadStoresList();
      if (typeof window !== "undefined") {
        setApiKeyInput(localStorage.getItem("promomind_gemini_api_key") || "");
      }
    }
  }, [isOpen]);

  async function loadStoresList() {
    try {
      const res = await fetchStores();
      if (res && Array.isArray(res.stores)) {
        setStores(res.stores);
        const activeId = res.active_store_id || selectedStoreId;
        setSelectedStoreId(activeId);
        const matched = res.stores.find((s) => s.store_id === activeId);
        if (matched) {
          populateSelectedStore(matched);
        }
      }
    } catch (e) {
      console.warn("Could not load stores list:", e);
    }
  }

  function populateSelectedStore(st) {
    setSelectedStoreId(st.store_id);
    setStoreNameInput(st.store_name || "");
    setOwnerInput(st.owner_name || "");
    setCityInput(st.city || "Bengaluru");
    setRegionInput(st.region || "Karnataka & South India");
    setAudienceInput(st.whatsapp_audience_size || st.audience_size || 1420);
  }

  if (!isOpen) return null;

  async function handleLoginSubmit(e) {
    e.preventDefault();
    setSubmitting(true);
    setErrorMsg("");
    try {
      if (typeof window !== "undefined") {
        if (apiKeyInput.trim()) {
          localStorage.setItem("promomind_gemini_api_key", apiKeyInput.trim());
        }
        localStorage.setItem("promomind_store_id", selectedStoreId);
        localStorage.setItem("promomind_logged_in", "true");
      }

      const res = await loginStore({
        store_id: selectedStoreId,
        store_name: storeNameInput.trim() || undefined,
        owner_name: ownerInput.trim() || undefined,
        city: cityInput.trim() || undefined,
        region: regionInput.trim() || undefined,
        audience_size: Number(audienceInput) || 1420,
        gemini_api_key: apiKeyInput.trim() || undefined,
      });

      if (res && res.profile) {
        if (typeof window !== "undefined") {
          localStorage.setItem("promomind_store_name", res.profile.store_name || "");
          localStorage.setItem("promomind_owner_name", res.profile.owner_name || "");
          localStorage.setItem("promomind_city", res.profile.city || "");
          localStorage.setItem("promomind_region", res.profile.region || "");
          localStorage.setItem("promomind_phone", res.profile.phone || "");
          localStorage.setItem(
            "promomind_audience",
            String(res.profile.whatsapp_audience_size || res.profile.audience_size || 1420)
          );
        }
        if (onStoreAuthenticated) {
          onStoreAuthenticated(res.profile);
        }
      }
      onClose();
    } catch (err) {
      console.warn("Login notice:", err);
      setErrorMsg(err.message || "Failed to initialize store session");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleCreateStore(e) {
    e.preventDefault();
    if (!newStoreName.trim()) return;
    setSubmitting(true);
    setErrorMsg("");
    try {
      if (typeof window !== "undefined" && apiKeyInput.trim()) {
        localStorage.setItem("promomind_gemini_api_key", apiKeyInput.trim());
        await configureGeminiApiKey(apiKeyInput.trim());
      }

      const res = await createOrSwitchStore({
        store_name: newStoreName.trim(),
        owner_name: newOwnerName.trim() || "Store Manager",
        city: newCity.trim() || "Bengaluru",
        region: newRegion,
        phone: newPhone.trim(),
        audience_size: Number(newAudience) || 1500,
        whatsapp_audience_size: Number(newAudience) || 1500,
        total_working_capital_inr: Number(newCapital) || 500000,
      });

      if (res && res.profile) {
        if (typeof window !== "undefined") {
          localStorage.setItem("promomind_logged_in", "true");
          localStorage.setItem("promomind_store_id", res.active_store_id);
          localStorage.setItem("promomind_store_name", res.profile.store_name || "");
          localStorage.setItem("promomind_owner_name", res.profile.owner_name || "");
          localStorage.setItem("promomind_city", res.profile.city || "");
          localStorage.setItem("promomind_region", res.profile.region || "");
          localStorage.setItem(
            "promomind_audience",
            String(res.profile.whatsapp_audience_size || res.profile.audience_size || 1500)
          );
        }
        if (onStoreAuthenticated) {
          onStoreAuthenticated(res.profile);
        }
      }
      onClose();
    } catch (err) {
      console.warn("Create store notice:", err);
      setErrorMsg(err.message || "Failed to create store");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4 animate-in fade-in duration-150">
      <div className="relative w-full max-w-lg rounded-2xl border border-border bg-card shadow-2xl overflow-hidden max-h-[92vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-border px-5 py-4">
          <div className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-foreground text-background">
              <Store className="h-4 w-4" />
            </div>
            <div>
              <h3 className="font-bold text-base text-foreground">
                One-Time Store Login &amp; Regional Setup
              </h3>
              <p className="text-xs text-muted-foreground">
                Saves your store location &amp; automatically syncs regional festivals to Firestore
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-1.5 text-muted-foreground hover:bg-muted hover:text-foreground"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Mode Toggle Tabs */}
        <div className="grid grid-cols-2 gap-1 p-2 bg-muted/40 border-b border-border text-xs font-semibold">
          <button
            type="button"
            onClick={() => setMode("login")}
            className={`py-2 rounded-lg transition-colors flex items-center justify-center gap-1.5 ${
              mode === "login"
                ? "bg-card text-foreground shadow-xs border border-border"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            <LogIn className="h-3.5 w-3.5" />
            <span>Sign In &amp; Confirm Region</span>
          </button>
          <button
            type="button"
            onClick={() => setMode("create")}
            className={`py-2 rounded-lg transition-colors flex items-center justify-center gap-1.5 ${
              mode === "create"
                ? "bg-card text-foreground shadow-xs border border-border"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            <Plus className="h-3.5 w-3.5" />
            <span>Register New Store Branch</span>
          </button>
        </div>

        <div className="overflow-y-auto">
          {mode === "login" ? (
            <form onSubmit={handleLoginSubmit} className="p-5 space-y-4">
              <div className="space-y-2">
                <label className="text-xs font-semibold text-foreground">
                  1. Select Store Account (Firestore):
                </label>
                <div className="space-y-1.5 max-h-36 overflow-y-auto pr-1">
                  {stores.map((st) => {
                    const isSel = selectedStoreId === st.store_id;
                    return (
                      <div
                        key={st.store_id}
                        onClick={() => populateSelectedStore(st)}
                        className={`p-2.5 rounded-xl border cursor-pointer transition-colors flex items-center justify-between ${
                          isSel
                            ? "border-foreground bg-muted/60"
                            : "border-border bg-background hover:bg-muted/30"
                        }`}
                      >
                        <div>
                          <div className="text-xs font-bold text-foreground">
                            {st.store_name}
                          </div>
                          <div className="text-[11px] text-muted-foreground">
                            {st.owner_name} • {st.city} ({st.region?.split("&")[0]?.trim()})
                          </div>
                        </div>
                        {isSel && <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0" />}
                      </div>
                    );
                  })}
                </div>
              </div>

              <div className="space-y-3 pt-2 border-t border-border">
                <div className="text-xs font-semibold text-foreground">
                  2. Confirm Store Location &amp; Broadcast Reach (Auto-Syncs Regional Festivals):
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <label className="text-xs font-medium text-foreground">Store Name:</label>
                    <Input
                      type="text"
                      value={storeNameInput}
                      onChange={(e) => setStoreNameInput(e.target.value)}
                      className="text-xs h-9"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-xs font-medium text-foreground">Owner / Manager:</label>
                    <Input
                      type="text"
                      value={ownerInput}
                      onChange={(e) => setOwnerInput(e.target.value)}
                      className="text-xs h-9"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <div className="space-y-1">
                    <label className="text-xs font-medium text-foreground">State / Region:</label>
                    <Input
                      type="text"
                      placeholder="e.g. Karnataka, Telangana..."
                      value={regionInput}
                      onChange={(e) => setRegionInput(e.target.value)}
                      className="text-xs h-9"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-xs font-medium text-foreground">City:</label>
                    <Input
                      type="text"
                      placeholder="e.g. Bengaluru"
                      value={cityInput}
                      onChange={(e) => setCityInput(e.target.value)}
                      className="text-xs h-9"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-xs font-medium text-foreground">WhatsApp Reach:</label>
                    <Input
                      type="number"
                      value={audienceInput}
                      onChange={(e) => setAudienceInput(e.target.value)}
                      className="text-xs h-9"
                    />
                  </div>
                </div>
              </div>

              {/* Live Gemini API Key Input */}
              <div className="space-y-1.5 pt-2 border-t border-border">
                <label className="text-xs font-semibold text-foreground flex items-center gap-1.5">
                  <KeyRound className="h-3.5 w-3.5" />
                  Live Gemini API Key (Optional Override):
                </label>
                <Input
                  type="password"
                  placeholder="Paste AIza... or AQ.... key (leaves server .env key if blank)"
                  value={apiKeyInput}
                  onChange={(e) => setApiKeyInput(e.target.value)}
                  className="text-xs h-9 font-mono"
                />
              </div>

              {errorMsg && (
                <div className="p-2.5 rounded-xl bg-destructive/10 border border-destructive/20 text-destructive text-xs font-medium">
                  {errorMsg}
                </div>
              )}

              <div className="flex items-center justify-end gap-2 pt-2 border-t border-border">
                <Button type="button" variant="outline" size="sm" onClick={onClose} className="text-xs">
                  Cancel
                </Button>
                <Button type="submit" size="sm" disabled={submitting} className="text-xs font-semibold px-4">
                  {submitting ? "Syncing Store & Festivals..." : "Save Login & Sync Regional Festivals"}
                </Button>
              </div>
            </form>
          ) : (
            <form onSubmit={handleCreateStore} className="p-5 space-y-3.5">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-foreground">New Store Name:</label>
                  <Input
                    type="text"
                    placeholder="e.g. Indiranagar Super Mart"
                    value={newStoreName}
                    onChange={(e) => setNewStoreName(e.target.value)}
                    required
                    className="text-xs h-9"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-foreground">Owner / Manager Name:</label>
                  <Input
                    type="text"
                    placeholder="e.g. Nitish Naik"
                    value={newOwnerName}
                    onChange={(e) => setNewOwnerName(e.target.value)}
                    required
                    className="text-xs h-9"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-foreground">State / Cultural Region (Type Any):</label>
                  <Input
                    type="text"
                    placeholder="e.g. Karnataka, Telangana, Maharashtra, Punjab..."
                    value={newRegion}
                    onChange={(e) => setNewRegion(e.target.value)}
                    required
                    className="text-xs h-9"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-foreground">City:</label>
                  <Input
                    type="text"
                    placeholder="e.g. Bengaluru"
                    value={newCity}
                    onChange={(e) => setNewCity(e.target.value)}
                    required
                    className="text-xs h-9"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-foreground">WhatsApp Phone:</label>
                  <Input
                    type="text"
                    value={newPhone}
                    onChange={(e) => setNewPhone(e.target.value)}
                    className="text-xs h-9"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-foreground">Broadcast Reach:</label>
                  <Input
                    type="number"
                    value={newAudience}
                    onChange={(e) => setNewAudience(e.target.value)}
                    className="text-xs h-9"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-foreground">Working Capital (₹):</label>
                  <Input
                    type="number"
                    step="25000"
                    value={newCapital}
                    onChange={(e) => setNewCapital(e.target.value)}
                    className="text-xs h-9"
                  />
                </div>
              </div>

              {errorMsg && (
                <div className="p-2.5 rounded-xl bg-destructive/10 border border-destructive/20 text-destructive text-xs font-medium">
                  {errorMsg}
                </div>
              )}

              <div className="flex items-center justify-end gap-2 pt-3 border-t border-border">
                <Button type="button" variant="outline" size="sm" onClick={onClose} className="text-xs">
                  Cancel
                </Button>
                <Button type="submit" size="sm" disabled={submitting} className="text-xs font-semibold px-4">
                  {submitting ? "Creating Store & Syncing..." : "Create Store & Sync Festivals"}
                </Button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
