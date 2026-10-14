"use client";

import { useState, useEffect, useRef } from "react";
import {
  fetchKnowledgeMarkdown,
  uploadCsvFile,
  uploadRawCsv,
} from "@/lib/api";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  UploadCloud,
  FileSpreadsheet,
  FileText,
  Download,
  RefreshCw,
  ChevronDown,
  ChevronUp,
  CheckCircle2,
  AlertCircle,
  Loader2,
  FolderOpen,
} from "lucide-react";

const SAMPLE_CSV_CONTENT = `product_id,name,category,brand,stock_quantity,cost_price,selling_price,past_sales_weeks
SKU_SAMPLE_01,Organic Pure Desi Ghee (1L),Dairy,Local Dairy,60,480.0,620.0,18,20,24,28,32,38
SKU_SAMPLE_02,Roasted Salted Pistachios (250g),Dry Fruits,Royal Harvest,45,210.0,295.0,12,14,15,16,18,22
SKU_SAMPLE_03,Artisanal Terracotta Deepas (Pack of 12),Puja & Festive,Mitti Art,150,45.0,90.0,2,3,4,8,25,85
SKU_SAMPLE_04,Premium Darjeeling First Flush Tea (500g),Beverages,Himalayan Leaf,80,310.0,420.0,30,32,34,35,36,40`;

export function UploadScreen({ onInventoryUpdated }) {
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);

  const [rawCsvOpen, setRawCsvOpen] = useState(false);
  const [rawCsvText, setRawCsvText] = useState("");
  const [parsingRaw, setParsingRaw] = useState(false);

  const [markdownContent, setMarkdownContent] = useState("");
  const [loadingMarkdown, setLoadingMarkdown] = useState(true);
  const [syncingMarkdown, setSyncingMarkdown] = useState(false);
  const [dragActive, setDragActive] = useState(false);

  const fileInputRef = useRef(null);

  useEffect(() => {
    loadMarkdown();
  }, []);

  async function loadMarkdown() {
    setLoadingMarkdown(true);
    try {
      const data = await fetchKnowledgeMarkdown();
      setMarkdownContent(data.markdown || "");
    } catch (e) {
      console.error("Failed to load knowledge markdown:", e);
      setMarkdownContent("Could not load knowledge markdown.");
    } finally {
      setLoadingMarkdown(false);
    }
  }

  async function handleSyncMarkdown() {
    setSyncingMarkdown(true);
    try {
      await loadMarkdown();
    } finally {
      setSyncingMarkdown(false);
    }
  }

  function handleFileDrop(e) {
    e.preventDefault();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      if (file.name.endsWith(".csv")) {
        setSelectedFile(file);
      } else {
        alert("Please upload a .csv file");
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
        title: "Import Succeeded",
        message: res.message || `Successfully processed ${selectedFile.name}`,
      });
      setSelectedFile(null);
      await loadMarkdown();
      if (onInventoryUpdated) onInventoryUpdated();
    } catch (e) {
      console.error("CSV upload error:", e);
      setUploadResult({
        success: false,
        title: "Upload Failed",
        message: "Failed to process CSV file. Ensure required columns are present.",
      });
    } finally {
      setUploading(false);
    }
  }

  async function handleParseRawCSV() {
    if (!rawCsvText.trim()) return;
    setParsingRaw(true);
    setUploadResult(null);

    try {
      const res = await uploadRawCsv(rawCsvText.trim());
      setUploadResult({
        success: true,
        title: "Raw CSV Synced",
        message: res.message || "Parsed raw text into inventory and updated forecasts.",
      });
      setRawCsvText("");
      await loadMarkdown();
      if (onInventoryUpdated) onInventoryUpdated();
    } catch (e) {
      console.error("Raw CSV error:", e);
      setUploadResult({
        success: false,
        title: "Parse Error",
        message: "Error parsing raw CSV data. Check column formatting.",
      });
    } finally {
      setParsingRaw(false);
    }
  }

  function handleDownloadSample() {
    const blob = new Blob([SAMPLE_CSV_CONTENT], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "promomind_sample_inventory.csv";
    a.click();
    URL.revokeObjectURL(url);
  }

  function handleDownloadMarkdown() {
    const blob = new Blob([markdownContent], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "store_knowledge.md";
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="space-y-6">
      {/* Screen Header */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between border-b border-border pb-4">
        <div>
          <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
            <FileSpreadsheet className="h-6 w-6 text-foreground" />
            Retail Data Intake &amp; AI Knowledge Sync
          </h2>
          <p className="text-sm text-muted-foreground mt-1">
            Upload distributor CSV or inventory files. PromoMind AI parses SKUs, executes Holt&apos;s demand forecasting, and compiles the AI Knowledge Base (<code className="font-mono text-xs bg-muted px-1.5 py-0.5 rounded border border-border">store_knowledge.md</code>).
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Button
            variant="outline"
            onClick={handleDownloadSample}
            className="border-border bg-card text-foreground hover:bg-muted text-xs sm:text-sm h-10 font-medium"
          >
            <Download className="h-4 w-4 mr-2" />
            Download Sample CSV Template
          </Button>
          <Button
            onClick={handleSyncMarkdown}
            disabled={syncingMarkdown}
            className="bg-primary text-primary-foreground hover:bg-primary/90 text-xs sm:text-sm h-10 font-semibold"
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${syncingMarkdown ? "animate-spin" : ""}`} />
            Sync Knowledge Base Now
          </Button>
        </div>
      </div>

      {/* Two Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: CSV Upload Card */}
        <div className="lg:col-span-6 space-y-4">
          <Card className="border border-border bg-card shadow-xs">
            <CardHeader className="pb-3 border-b border-border">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base font-bold text-foreground">
                  1. Upload Inventory CSV Data
                </CardTitle>
                <Badge variant="outline" className="border-border bg-muted/60 text-xs font-semibold text-foreground">
                  Data Intake
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="p-5 space-y-4">
              {/* Drag and Drop Dropzone */}
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
                  accept=".csv"
                  className="hidden"
                  onChange={handleFileSelect}
                />
                <FolderOpen className="h-10 w-10 mx-auto text-muted-foreground mb-3" />
                <h4 className="text-base font-semibold text-foreground">
                  Drag &amp; Drop your Retail CSV here
                </h4>
                <p className="text-xs text-muted-foreground mt-1">
                  or click to browse from your computer
                </p>
                <div className="mt-3 text-[11px] text-muted-foreground font-mono bg-muted/60 border border-border px-2.5 py-1 rounded-md inline-block">
                  Supports .csv (Product ID, Name, Category, Brand, Stock, Cost, MRP, Sales)
                </div>
              </div>

              {/* Selected File Status */}
              {selectedFile && (
                <div className="p-3.5 rounded-lg border border-border bg-muted/30 flex items-center justify-between gap-3">
                  <div className="flex items-center gap-2 overflow-hidden">
                    <FileSpreadsheet className="h-5 w-5 text-foreground shrink-0" />
                    <span className="text-sm font-semibold text-foreground truncate">
                      {selectedFile.name}
                    </span>
                  </div>
                  <Button
                    onClick={handleProcessUploadedCSV}
                    disabled={uploading}
                    className="font-semibold text-xs h-9 bg-primary text-primary-foreground hover:bg-primary/90 shrink-0"
                  >
                    {uploading ? (
                      <>
                        <Loader2 className="h-3.5 w-3.5 animate-spin mr-1.5" />
                        Forecasting...
                      </>
                    ) : (
                      <>⚡ Process &amp; Forecast</>
                    )}
                  </Button>
                </div>
              )}

              {/* Or Paste Raw CSV Text */}
              <div className="border border-border rounded-lg overflow-hidden">
                <button
                  type="button"
                  onClick={() => setRawCsvOpen(!rawCsvOpen)}
                  className="w-full px-4 py-3 bg-muted/30 hover:bg-muted/50 flex items-center justify-between text-xs sm:text-sm font-semibold text-foreground transition-colors"
                >
                  <span className="flex items-center gap-2">
                    <FileText className="h-4 w-4" />
                    Or Paste Raw CSV Text
                  </span>
                  {rawCsvOpen ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                </button>

                {rawCsvOpen && (
                  <div className="p-4 space-y-3 bg-card border-t border-border">
                    <textarea
                      rows={6}
                      value={rawCsvText}
                      onChange={(e) => setRawCsvText(e.target.value)}
                      placeholder="product_id,name,category,brand,stock_quantity,cost_price,selling_price,past_sales_weeks&#10;SKU_GHEE_99,Organic A2 Desi Cow Ghee,Dairy,Local Farm,50,480.0,620.0,15,18,22,25,28,34"
                      className="w-full p-3 text-xs font-mono bg-background border border-border rounded-md text-foreground focus:outline-none focus:ring-1 focus:ring-ring"
                    />
                    <Button
                      onClick={handleParseRawCSV}
                      disabled={!rawCsvText.trim() || parsingRaw}
                      variant="outline"
                      className="w-full font-semibold text-xs h-9 border-border bg-secondary text-secondary-foreground hover:bg-secondary/80"
                    >
                      {parsingRaw ? (
                        <>
                          <Loader2 className="h-3.5 w-3.5 animate-spin mr-1.5" />
                          Parsing...
                        </>
                      ) : (
                        <>⚡ Parse Raw Text &amp; Update Knowledge</>
                      )}
                    </Button>
                  </div>
                )}
              </div>

              {/* Import Log Result */}
              {uploadResult && (
                <div
                  className={`p-4 rounded-lg border text-xs sm:text-sm space-y-1 ${
                    uploadResult.success
                      ? "border-border bg-muted/40 text-foreground"
                      : "border-destructive/40 bg-destructive/10 text-destructive"
                  }`}
                >
                  <div className="font-bold flex items-center gap-1.5">
                    {uploadResult.success ? (
                      <CheckCircle2 className="h-4 w-4 text-foreground" />
                    ) : (
                      <AlertCircle className="h-4 w-4 text-destructive" />
                    )}
                    {uploadResult.title}
                  </div>
                  <p className="text-muted-foreground">{uploadResult.message}</p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Right Column: AI Knowledge Base Markdown Viewer */}
        <div className="lg:col-span-6 space-y-4">
          <Card className="border border-border bg-card shadow-xs">
            <CardHeader className="pb-3 border-b border-border">
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-base font-bold text-foreground">
                    2. AI Grounding Knowledge Base
                  </CardTitle>
                  <CardDescription className="text-xs text-muted-foreground font-mono mt-0.5">
                    data/store_knowledge.md
                  </CardDescription>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleDownloadMarkdown}
                  className="border-border text-xs h-8"
                >
                  <Download className="h-3.5 w-3.5 mr-1.5" />
                  Download .md
                </Button>
              </div>
            </CardHeader>
            <CardContent className="p-5 space-y-3">
              <p className="text-xs sm:text-sm text-muted-foreground leading-relaxed">
                This structured Markdown document is auto-generated by the system. Multi-agent models (Gemini Strategy, Inventory &amp; Pricing) query this file to ground recommendations in real stock levels and historical demand.
              </p>

              <div className="rounded-lg border border-border bg-muted/30 p-4 max-h-[480px] overflow-y-auto">
                {loadingMarkdown ? (
                  <div className="space-y-2.5 py-4 animate-pulse">
                    <Skeleton className="h-4 w-3/4 rounded" />
                    <Skeleton className="h-4 w-1/2 rounded" />
                    <Skeleton className="h-4 w-5/6 rounded" />
                    <Skeleton className="h-4 w-2/3 rounded" />
                    <Skeleton className="h-4 w-4/5 rounded" />
                    <Skeleton className="h-4 w-3/5 rounded" />
                  </div>
                ) : (
                  <pre className="font-mono text-xs leading-relaxed text-foreground whitespace-pre-wrap select-text">
                    {markdownContent || "No knowledge base markdown content available."}
                  </pre>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

