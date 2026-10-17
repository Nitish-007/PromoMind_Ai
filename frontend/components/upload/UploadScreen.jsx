"use client";

import { useState, useEffect, useRef } from "react";
import {
  uploadCsvFile,
  fetchInventory,
  fetchStorageStatus,
} from "@/lib/api";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  FileSpreadsheet,
  Download,
  CheckCircle2,
  AlertCircle,
  Loader2,
  FolderOpen,
  Database,
} from "lucide-react";

const SAMPLE_CSV_CONTENT = `product_id,name,category,brand,stock_quantity,cost_price,selling_price,weekly_sales_avg,expiry_days,customer_name,customer_phone
SKU_SAMPLE_01,Organic Pure Desi Ghee (1L),Dairy,Local Dairy,60,480.0,620.0,38,240,Deepak Nair,+91 98459 11223
SKU_SAMPLE_02,Roasted Salted Pistachios (250g),Dry Fruits,Royal Harvest,45,210.0,295.0,18,180,Priya Menon,+91 98459 22334
SKU_SAMPLE_03,Artisanal Terracotta Deepas (Pack of 12),Puja & Festive,Mitti Art,150,45.0,90.0,45,365,Suresh Babu,+91 98459 33445
SKU_SAMPLE_04,Premium Darjeeling First Flush Tea (500g),Beverages,Himalayan Leaf,80,310.0,420.0,36,300,Kavitha Shetty,+91 98459 44556`;

export function UploadScreen({ storeProfile, onInventoryUpdated }) {
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);
  const [dragActive, setDragActive] = useState(false);

  const [syncedProducts, setSyncedProducts] = useState([]);
  const [loadingInventory, setLoadingInventory] = useState(true);
  const [storageStatus, setStorageStatus] = useState(null);

  const fileInputRef = useRef(null);

  useEffect(() => {
    loadFirestoreInventory();
  }, [storeProfile?.store_id]);

  async function loadFirestoreInventory() {
    setLoadingInventory(true);
    try {
      const [prods, status] = await Promise.all([
        fetchInventory(),
        fetchStorageStatus().catch(() => null),
      ]);
      if (Array.isArray(prods)) setSyncedProducts(prods);
      if (status) setStorageStatus(status);
    } catch (e) {
      console.error("Failed to load Firestore inventory:", e);
    } finally {
      setLoadingInventory(false);
    }
  }

  function handleFileDrop(e) {
    e.preventDefault();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      const lower = file.name.toLowerCase();
      if (lower.endsWith(".csv") || lower.endsWith(".xlsx") || lower.endsWith(".xls")) {
        setSelectedFile(file);
      } else {
        alert("Please upload a .csv or .xlsx file");
      }
    }
  }

  function handleFileSelect(e) {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
    }
  }

  async function handleProcessUploadedCSV() {
    if (!selectedFile) return;
    setUploading(true);
    setUploadResult(null);

    try {
      const formData = new FormData();
      formData.append("file", selectedFile);
      const res = await uploadCsvFile(formData);
      setUploadResult({
        success: true,
        title: "Smart Schema Structuring & Firestore Sync Complete",
        message: res.message,
        stats: {
          imported_count: res.imported_count || 0,
          new_skus_added: res.new_skus_added ?? res.imported_count ?? 0,
          existing_skus_updated: res.existing_skus_updated || 0,
          duplicates_prevented: res.duplicates_prevented || 0,
          broadcast_contacts_synced: res.broadcast_contacts_synced || 0,
          active_broadcast_reach: res.active_broadcast_reach || storeProfile?.whatsapp_audience_size || 1420,
          columns_mapped: res.columns_mapped || [],
        },
      });
      setSelectedFile(null);
      if (Array.isArray(res.products)) {
        setSyncedProducts(res.products);
      } else {
        await loadFirestoreInventory();
      }
      if (onInventoryUpdated) onInventoryUpdated(res.store_profile);
    } catch (e) {
      console.error("CSV upload error:", e);
      setUploadResult({
        success: false,
        title: "Firestore CSV Sync Failed",
        message: "Failed to process CSV file. Ensure valid product rows are present.",
      });
    } finally {
      setUploading(false);
    }
  }

  function handleDownloadSample() {
    const blob = new Blob([SAMPLE_CSV_CONTENT], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "promomind_smart_inventory_and_broadcast.csv";
    a.click();
    URL.revokeObjectURL(url);
  }

  const collectionPath = `stores/${storeProfile?.store_id || "store_default"}/inventory`;

  return (
    <div className="space-y-6">
      {/* Screen Header */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between border-b border-border pb-4">
        <div>
          <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
            <Database className="h-6 w-6 text-foreground" />
            Smart CSV Structurizer &amp; Firestore Sync
          </h2>
          <p className="text-sm text-muted-foreground mt-1">
            Upload any POS or distributor CSV. PromoMind AI automatically structures arbitrary columns into our canonical schema, prevents duplicates on re-upload, updates WhatsApp broadcast reach, and syncs to Firestore (<code className="font-mono text-xs bg-muted px-1.5 py-0.5 rounded border border-border">{collectionPath}</code>).
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant="outline" className="px-3 py-1.5 text-xs font-semibold border-border bg-muted/60 text-foreground">
            Broadcast Reach: {(storeProfile?.whatsapp_audience_size || storeProfile?.audience_size || 1420).toLocaleString("en-IN")} Customers
          </Badge>
          <Button
            variant="outline"
            onClick={handleDownloadSample}
            className="border-border bg-card text-foreground hover:bg-muted text-xs sm:text-sm h-10 font-medium"
          >
            <Download className="h-4 w-4 mr-2" />
            Download Sample CSV
          </Button>
        </div>
      </div>

      {/* Single-Stage Smart Firestore CSV Upload Card */}
      <Card className="border border-border bg-card shadow-xs">
        <CardHeader className="pb-3 border-b border-border">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div>
              <CardTitle className="text-base font-bold text-foreground">
                Upload Inventory &amp; Broadcast CSV to Firestore
              </CardTitle>
              <CardDescription className="text-xs text-muted-foreground mt-0.5">
                Auto-normalizes column names (e.g., Item/Product, Rate/Cost, Price/MRP, Qty/Stock, Customer WhatsApp) &amp; upserts without duplicating SKUs.
              </CardDescription>
            </div>
            <Badge variant="outline" className="border-border bg-muted/60 text-xs font-semibold text-foreground w-fit">
              Zero-Duplicate Upsert Engine
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="p-6 space-y-4">
          <div
            onDragOver={(e) => {
              e.preventDefault();
              setDragActive(true);
            }}
            onDragLeave={() => setDragActive(false)}
            onDrop={handleFileDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors ${
              dragActive
                ? "border-foreground bg-muted/50"
                : "border-border hover:border-foreground/40 bg-muted/20"
            }`}
          >
            <input
              type="file"
              ref={fileInputRef}
              accept=".csv, .xlsx, .xls"
              className="hidden"
              onChange={handleFileSelect}
            />
            <FolderOpen className="h-10 w-10 mx-auto text-muted-foreground mb-3" />
            <h4 className="text-base font-semibold text-foreground">
              Drag &amp; Drop any Retail POS, Distributor CSV or Excel (.xlsx) here
            </h4>
            <p className="text-xs text-muted-foreground mt-1">
              Re-uploading an updated sheet updates stock &amp; prices in place without creating duplicate items
            </p>
            <div className="mt-3 text-[11px] text-muted-foreground font-mono bg-muted/60 border border-border px-2.5 py-1 rounded-md inline-block">
              Auto-maps: Product/Item Name, Category, Stock/Qty, Cost/Buy Rate, MRP/Price, Sales Velocity &amp; Customer WhatsApp
            </div>
          </div>

          {selectedFile && (
            <div className="p-4 rounded-lg border border-border bg-muted/30 flex items-center justify-between gap-3">
              <div className="flex items-center gap-2.5 overflow-hidden">
                <FileSpreadsheet className="h-5 w-5 text-foreground shrink-0" />
                <div>
                  <div className="text-sm font-semibold text-foreground truncate">
                    {selectedFile.name}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    Ready to structure, deduplicate, and sync to {collectionPath}
                  </div>
                </div>
              </div>
              <Button
                onClick={handleProcessUploadedCSV}
                disabled={uploading}
                className="font-semibold text-xs h-10 px-5 bg-primary text-primary-foreground hover:bg-primary/90 shrink-0"
              >
                {uploading ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin mr-2" />
                    Structuring &amp; Syncing...
                  </>
                ) : (
                  "Structure & Sync to Firestore"
                )}
              </Button>
            </div>
          )}

          {/* Detailed Structuring & De-Duplication Telemetry Report */}
          {uploadResult && (
            <div
              className={`p-4 rounded-xl border text-xs sm:text-sm space-y-3 ${
                uploadResult.success
                  ? "border-emerald-500/40 bg-emerald-500/10 text-foreground"
                  : "border-destructive/40 bg-destructive/10 text-destructive"
              }`}
            >
              <div className="font-bold flex items-center gap-1.5">
                {uploadResult.success ? (
                  <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                ) : (
                  <AlertCircle className="h-4 w-4 text-destructive" />
                )}
                {uploadResult.title}
              </div>
              <p className="text-muted-foreground">{uploadResult.message}</p>

              {uploadResult.stats && (
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 pt-1">
                  <div className="p-2.5 rounded-lg border border-border bg-card">
                    <div className="text-[11px] text-muted-foreground">New SKUs Added</div>
                    <div className="text-base font-bold text-foreground mt-0.5">
                      +{uploadResult.stats.new_skus_added}
                    </div>
                  </div>
                  <div className="p-2.5 rounded-lg border border-border bg-card">
                    <div className="text-[11px] text-muted-foreground">Updated In-Place</div>
                    <div className="text-base font-bold text-emerald-600 dark:text-emerald-400 mt-0.5">
                      {uploadResult.stats.existing_skus_updated} SKUs
                    </div>
                  </div>
                  <div className="p-2.5 rounded-lg border border-border bg-card">
                    <div className="text-[11px] text-muted-foreground">Duplicates Prevented</div>
                    <div className="text-base font-bold text-foreground mt-0.5">
                      {uploadResult.stats.duplicates_prevented} Merged
                    </div>
                  </div>
                  <div className="p-2.5 rounded-lg border border-border bg-card">
                    <div className="text-[11px] text-muted-foreground">Broadcast Reach</div>
                    <div className="text-base font-bold text-foreground mt-0.5">
                      {uploadResult.stats.active_broadcast_reach.toLocaleString("en-IN")}
                    </div>
                  </div>
                </div>
              )}
              {uploadResult.success && (
                <div className="pt-2 flex justify-end">
                  <Button
                    onClick={() => window.dispatchEvent(new CustomEvent('switch-tab', { detail: 'inventory' }))}
                    className="font-semibold text-xs h-9 px-4 gap-2 bg-foreground text-background hover:bg-foreground/90 cursor-pointer"
                  >
                    <span>View Structured Inventory in Stock &amp; Brands &rarr;</span>
                  </Button>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Live Synced Firestore Inventory Preview */}
      <Card className="border border-border bg-card shadow-xs">
        <CardHeader className="pb-3 border-b border-border">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-base font-bold text-foreground">
                Structured Firestore Inventory Collection ({syncedProducts.length} Unique SKUs)
              </CardTitle>
              <CardDescription className="text-xs text-muted-foreground font-mono mt-0.5">
                {collectionPath}
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-muted/40 text-muted-foreground uppercase tracking-wider font-semibold border-b border-border">
                <tr>
                  <th className="px-4 py-3">SKU ID</th>
                  <th className="px-4 py-3">Product Name</th>
                  <th className="px-4 py-3">Category</th>
                  <th className="px-4 py-3">Stock</th>
                  <th className="px-4 py-3">Cost / MRP</th>
                  <th className="px-4 py-3">Velocity</th>
                  <th className="px-4 py-3">4-Week Forecast</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/60">
                {loadingInventory ? (
                  [...Array(4)].map((_, i) => (
                    <tr key={i}>
                      <td className="px-4 py-3"><Skeleton className="h-4 w-20" /></td>
                      <td className="px-4 py-3"><Skeleton className="h-4 w-44" /></td>
                      <td className="px-4 py-3"><Skeleton className="h-4 w-24" /></td>
                      <td className="px-4 py-3"><Skeleton className="h-4 w-16" /></td>
                      <td className="px-4 py-3"><Skeleton className="h-4 w-24" /></td>
                      <td className="px-4 py-3"><Skeleton className="h-4 w-20" /></td>
                      <td className="px-4 py-3"><Skeleton className="h-4 w-28" /></td>
                    </tr>
                  ))
                ) : syncedProducts.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="px-4 py-12 text-center text-muted-foreground">
                      <div className="flex flex-col items-center justify-center space-y-2">
                        <FolderOpen className="h-8 w-8 text-muted-foreground/60" />
                        <p className="text-sm font-medium text-foreground">
                          No SKUs structured in this Firestore collection yet.
                        </p>
                        <p className="text-xs text-muted-foreground max-w-md">
                          Upload your Excel (.xlsx) or CSV spreadsheet above to structure and sync your products directly into <code className="bg-muted px-1.5 py-0.5 rounded text-[11px] font-mono">{collectionPath}</code>.
                        </p>
                      </div>
                    </td>
                  </tr>
                ) : (
                  syncedProducts.map((p) => (
                    <tr key={p.id} className="hover:bg-muted/20">
                      <td className="px-4 py-3 font-mono text-muted-foreground">{p.id}</td>
                      <td className="px-4 py-3 font-semibold text-foreground">{p.name}</td>
                      <td className="px-4 py-3">
                        <Badge variant="outline" className="text-xs font-normal">{p.category}</Badge>
                      </td>
                      <td className="px-4 py-3 font-medium">{p.stock_quantity} units</td>
                      <td className="px-4 py-3">₹{p.cost_price} / <strong>₹{p.selling_price}</strong></td>
                      <td className="px-4 py-3">{p.velocity_status} ({p.weekly_sales_avg}/wk)</td>
                      <td className="px-4 py-3 font-mono text-muted-foreground">
                        [{(p.forecast_sales_weeks || []).join(", ")}]
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
