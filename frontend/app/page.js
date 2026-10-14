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

export default function Home() {
  const [activeTab, setActiveTab] = useState("inventory");
  const [theme, setTheme] = useState("light");
  
  // Store Profile & Storage
  const [storeProfile, setStoreProfile] = useState({
    store_name: "Sharma Supermarket & Kirana",
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
    setActiveTab("promos");
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
          />
        )}

        {activeTab === "calendar" && (
          <div className="rounded-2xl border bg-card p-12 text-center shadow-xs">
            <h3 className="text-lg font-bold">Regional Festival Calendar</h3>
            <p className="text-xs text-muted-foreground mt-1">Ready for feature step #3.</p>
          </div>
        )}

        {activeTab === "upload" && (
          <div className="rounded-2xl border bg-card p-12 text-center shadow-xs">
            <h3 className="text-lg font-bold">CSV Intake & AI Markdown Sync</h3>
            <p className="text-xs text-muted-foreground mt-1">Ready for feature step #4.</p>
          </div>
        )}

        {activeTab === "profile" && (
          <div className="rounded-2xl border bg-card p-12 text-center shadow-xs">
            <h3 className="text-lg font-bold">Store Profile & Settings</h3>
            <p className="text-xs text-muted-foreground mt-1">Ready for feature step #5.</p>
          </div>
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
