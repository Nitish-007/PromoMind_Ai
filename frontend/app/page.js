"use client";

import React, { useState, useEffect } from "react";
import { Header } from "@/components/layout/Header";
import { FestiveTickerBar } from "@/components/layout/FestiveTickerBar";
import { Navbar } from "@/components/layout/Navbar";
import { InventoryScreen } from "@/components/inventory/InventoryScreen";
import { CopilotScreen } from "@/components/copilot/CopilotScreen";
import { BrandComparisonModal } from "@/components/modals/BrandComparisonModal";
import { AddProductModal } from "@/components/modals/AddProductModal";
import { 
  fetchInventory, 
  fetchFinancialRoi, 
  simulateRoi, 
  fetchBrandComparison, 
  addProduct,
  fetchStoreProfile,
  fetchStorageStatus
} from "@/lib/api";

import { CalendarScreen } from "@/components/calendar/CalendarScreen";
import { UploadScreen } from "@/components/upload/UploadScreen";
import { ProfileScreen } from "@/components/profile/ProfileScreen";

export default function Home() {
  const [activeTab, setActiveTab] = useState("inventory");
  const [theme, setTheme] = useState("light");
  const [copilotPrompt, setCopilotPrompt] = useState("");
  
  // Store Profile & Storage
  const [storeProfile, setStoreProfile] = useState({
    store_name: "Metro Supermarket & Retail Mart",
    owner_name: "Ramesh Sharma",
    city: "Bengaluru",
    region: "Karnataka & South India",
    phone: "+91 98450 12345",
  });
  const [storageStatus, setStorageStatus] = useState(null);

  // Inventory & ROI Data
  const [products, setProducts] = useState([]);
  const [roiData, setRoiData] = useState(null);
  const [isLoadingInventory, setIsLoadingInventory] = useState(true);

  // Modals state
  const [isAddSkuOpen, setIsAddSkuOpen] = useState(false);
  const [brandModalProduct, setBrandModalProduct] = useState(null);
  const [brandComparisonData, setBrandComparisonData] = useState(null);

  // Initial load
  useEffect(() => {
    // Check saved theme
    const savedTheme = localStorage.getItem("promomind_theme") || "light";
    setTheme(savedTheme);
    if (savedTheme === "dark") {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }

    // Read cached store profile from localStorage after client hydration
    const cachedStoreName = localStorage.getItem("promomind_store_name");
    if (cachedStoreName) {
      setStoreProfile((prev) => ({
        ...prev,
        store_name: cachedStoreName,
        owner_name: localStorage.getItem("promomind_owner_name") || prev.owner_name,
        city: localStorage.getItem("promomind_city") || prev.city,
        region: localStorage.getItem("promomind_region") || prev.region,
        phone: localStorage.getItem("promomind_phone") || prev.phone,
      }));
    }

    loadInitialData();
  }, []);

  const toggleTheme = () => {
    const nextTheme = theme === "light" ? "dark" : "light";
    setTheme(nextTheme);
    localStorage.setItem("promomind_theme", nextTheme);
    if (nextTheme === "dark") {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
  };

  const loadInitialData = async () => {
    setIsLoadingInventory(true);
    try {
      // 1. Fetch store profile
      try {
        const prof = await fetchStoreProfile();
        if (prof) setStoreProfile((prev) => ({ ...prev, ...prof }));
      } catch (e) {
        console.warn("Could not load store profile:", e);
      }

      // 2. Fetch inventory
      try {
        const prods = await fetchInventory();
        if (Array.isArray(prods)) setProducts(prods);
      } catch (e) {
        console.warn("Could not load inventory:", e);
      }

      // 3. Fetch financial ROI
      try {
        const roi = await fetchFinancialRoi();
        if (roi) setRoiData(roi);
      } catch (e) {
        console.warn("Could not load ROI data:", e);
      }

      // 4. Storage status
      try {
        const status = await fetchStorageStatus();
        if (status) setStorageStatus(status);
      } catch (e) {
        console.warn("Could not load storage status:", e);
      }
    } finally {
      setIsLoadingInventory(false);
    }
  };

  const handleSimulateRoi = async (discountPct, volumeLiftPct) => {
    try {
      const res = await simulateRoi(discountPct, volumeLiftPct);
      return res;
    } catch (e) {
      console.warn("Error running simulation:", e);
      return null;
    }
  };

  const handleOpenBrandModal = async (product) => {
    setBrandModalProduct(product);
    try {
      const data = await fetchBrandComparison(product.id);
      setBrandComparisonData(data);
    } catch (e) {
      console.warn("Could not fetch brand comparison:", e);
      setBrandComparisonData(null);
    }
  };

  const handleAddSku = async (skuPayload) => {
    try {
      const updatedList = await addProduct(skuPayload);
      if (Array.isArray(updatedList)) {
        setProducts(updatedList);
      } else {
        await loadInitialData();
      }
    } catch (e) {
      console.error("Failed to add SKU:", e);
    }
  };

  const handleCreatePromoForProduct = (product) => {
    setCopilotPrompt(`Create a high-margin promotional offer featuring ${product.name} (${product.id})`);
    setActiveTab("promos");
  };

  const handleLaunchPromoForFestival = (festivalName, comboTitle) => {
    const prompt = comboTitle
      ? `Create a festival promotional bundle for ${festivalName} (${comboTitle})`
      : `Create an optimal festival promotional bundle for ${festivalName}`;
    setCopilotPrompt(prompt);
    setActiveTab("promos");
  };

  const handleProfileUpdated = (updatedProf) => {
    setStoreProfile((prev) => ({
      ...prev,
      ...updatedProf,
    }));
  };

  return (
    <div className="min-h-screen flex flex-col bg-background text-foreground transition-colors">
      {/* 1. App Top Bar */}
      <Header
        storeProfile={storeProfile}
        theme={theme}
        onToggleTheme={toggleTheme}
        onOpenProfile={() => setActiveTab("profile")}
      />

      {/* 2. Festive Alert Strip */}
      <FestiveTickerBar
        region={storeProfile.region}
        onOpenCalendar={() => setActiveTab("calendar")}
      />

      {/* 3. Navigation Tab Bar */}
      <Navbar activeTab={activeTab} onSelectTab={setActiveTab} />

      {/* 4. Main Screens Container */}
      <main className="flex-1 mx-auto w-full max-w-7xl px-4 sm:px-6 lg:px-8 py-6">
        {activeTab === "inventory" && (
          <InventoryScreen
            products={products}
            roiData={roiData}
            isLoading={isLoadingInventory}
            onRefresh={loadInitialData}
            onOpenAddSku={() => setIsAddSkuOpen(true)}
            onOpenImportCsv={() => setActiveTab("upload")}
            onOpenBrandModal={handleOpenBrandModal}
            onCreatePromoForProduct={handleCreatePromoForProduct}
            onSimulateRoi={handleSimulateRoi}
          />
        )}

        {/* Feature 2: AI Retail Copilot & Promo Generator */}
        {activeTab === "promos" && (
          <CopilotScreen
            storeProfile={storeProfile}
            onOfferActivated={() => setActiveTab("calendar")}
            initialPrompt={copilotPrompt}
            onClearInitialPrompt={() => setCopilotPrompt("")}
          />
        )}

        {/* Feature 3: Regional Festival Calendar & Conflict Tracker */}
        {activeTab === "calendar" && (
          <CalendarScreen
            onLaunchPromo={handleLaunchPromoForFestival}
          />
        )}

        {/* Feature 4: CSV Intake & AI Markdown Sync */}
        {activeTab === "upload" && (
          <UploadScreen
            onInventoryUpdated={loadInitialData}
          />
        )}

        {/* Feature 5: Store Profile & Settings */}
        {activeTab === "profile" && (
          <ProfileScreen
            onProfileUpdated={handleProfileUpdated}
          />
        )}
      </main>

      {/* Brand Comparison Modal */}
      <BrandComparisonModal
        isOpen={Boolean(brandModalProduct)}
        product={brandModalProduct}
        brandData={brandComparisonData}
        onClose={() => setBrandModalProduct(null)}
        onUseInPromo={handleCreatePromoForProduct}
      />

      {/* Add Product SKU Modal */}
      <AddProductModal
        isOpen={isAddSkuOpen}
        onClose={() => setIsAddSkuOpen(false)}
        onAddProduct={handleAddSku}
      />
    </div>
  );
}
