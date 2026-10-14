// ==============================================================================
// PromoMind AI — Reactive App Controller & State Engine (v2.5)
// Mobile/Cloud Architecture: Multi-Brand Curves, Regional Calendars & Conflict Control
// ==============================================================================

let currentScreen = "inventory";
let inventoryItems = [];
let activeOffers = [];
let regionalEvents = [];
let currentBrandComparison = null;
let brandChartViewMode = "ALL_BRANDS"; // "ALL_BRANDS" or "SINGLE_SKU"
let currentPlan = null;
let uploadedFileObject = null;

// Brand color palette matching CSS tokens
const BRAND_COLORS = [
  { stroke: "#1a73e8", name: "Brand 1 (Market Anchor)", fill: "rgba(26,115,232,0.15)" },
  { stroke: "#1e8e3e", name: "Brand 2 (High Margin)", fill: "rgba(30,142,62,0.15)" },
  { stroke: "#d93025", name: "Brand 3 (Alternative)", fill: "rgba(217,48,37,0.15)" },
  { stroke: "#9334e6", name: "Brand 4", fill: "rgba(147,52,230,0.15)" }
];

// ==============================================================================
// App Initialization
// ==============================================================================

document.addEventListener("DOMContentLoaded", () => {
  loadStoreProfile();
  setupDragAndDrop();
  
  // Initial data loading
  fetchInventory();
  fetchCalendarEvents();
  fetchActiveOffers();
  fetchKnowledgeMarkdown();
  fetchCloudStatus();
});

async function fetchCloudStatus() {
  try {
    const res = await fetch("/api/system/cloud-status");
    if (!res.ok) return;
    const data = await res.json();
    const badge = document.getElementById("cloudStatusBadge");
    if (badge) {
      if (data.is_connected) {
        badge.innerText = `🟢 Cloud Firestore Live (${data.project_id})`;
      } else {
        badge.innerText = `🟡 Dual-Mode Ready (Local JSON Sync)`;
      }
    }
  } catch (e) {
    console.error("Error fetching cloud status:", e);
  }
}

// ==============================================================================
// App Navigation & Screen Management
// ==============================================================================

function switchScreen(screenId) {
  currentScreen = screenId;

  // Toggle screen visibility
  document.querySelectorAll(".app-screen").forEach(el => el.classList.remove("active"));
  const targetScreen = document.getElementById(`screen-${screenId}`);
  if (targetScreen) {
    targetScreen.classList.add("active");
  }

  // Toggle nav buttons
  document.querySelectorAll(".nav-item").forEach(el => el.classList.remove("active"));
  const targetNav = document.getElementById(`nav-${screenId}`);
  if (targetNav) {
    targetNav.classList.add("active");
  }

  // Update topbar subtitle
  const subtitles = {
    inventory: "Stock & Multi-Brand Comparative Curves",
    promos: "Smart Bundles, Apriori Smart-Pairing & Omnichannel Copy",
    calendar: "Regional Festive Demand Spikes & Offer Conflict Prevention",
    upload: "Retail CSV Import & AI Knowledge Base Sync (.md)",
    profile: "Store Identity, Cultural Demographics & Google Theme"
  };
  const subEl = document.getElementById("topbarSubtitle");
  if (subEl && subtitles[screenId]) {
    subEl.innerText = subtitles[screenId];
  }

  // Toggle floating Copilot button: hide on promos screen (where copilot lives), show on other screens
  const floatingBtn = document.getElementById("copilotFloatingBtn");
  if (floatingBtn) {
    if (screenId === "promos") {
      floatingBtn.style.display = "none";
    } else {
      floatingBtn.style.display = "flex";
    }
  }

  // Contextual refresh
  if (screenId === "calendar") {
    fetchActiveOffers();
    fetchCalendarEvents();
  } else if (screenId === "upload") {
    fetchKnowledgeMarkdown();
  }

  window.scrollTo({ top: 0, behavior: "smooth" });
}

// ==============================================================================
// Store Profile, Region & Theme Engine
// ==============================================================================

async function loadStoreProfile() {
  const savedTheme = localStorage.getItem("promomind_theme") || "light";
  setThemeMode(savedTheme);

  // Attempt to load from server backend first
  try {
    const res = await fetch("/api/profile");
    if (res.ok) {
      const prof = await res.json();
      applyProfileToUI(prof);
      await fetchStorageStatus();
      return;
    }
  } catch (e) {
    console.log("Using cached localStorage profile");
  }

  // Fallback to localStorage
  const fallbackProf = {
    store_name: localStorage.getItem("promomind_store_name") || "Metro Supermarket & Retail Mart",
    owner_name: localStorage.getItem("promomind_owner_name") || "Ramesh Sharma",
    state_region: localStorage.getItem("promomind_region") || "Karnataka & South India",
    city: localStorage.getItem("promomind_city") || "Bengaluru",
    locality: localStorage.getItem("promomind_locality") || "Koramangala 4th Block",
    pincode: localStorage.getItem("promomind_pin") || "560034",
    phone: localStorage.getItem("promomind_phone") || "+91 98450 12345",
    gstin: localStorage.getItem("promomind_gstin") || "29AAAAA0000A1Z5",
    store_type: localStorage.getItem("promomind_store_type") || "Supermarket",
    audience_reach: parseInt(localStorage.getItem("promomind_audience") || "1420", 10),
    working_capital: parseFloat(localStorage.getItem("promomind_capital") || "500000"),
    min_gross_margin_target_pct: parseFloat(localStorage.getItem("promomind_margin") || "15.0")
  };
  applyProfileToUI(fallbackProf);
  await fetchStorageStatus();
}

function applyProfileToUI(prof) {
  const storeName = prof.store_name || "Metro Supermarket & Retail Mart";
  const city = prof.city || "Bengaluru";
  const region = prof.state_region || prof.region || "Karnataka & South India";
  const locality = prof.locality || "Koramangala 4th Block";
  const pin = prof.pincode || prof.pin_code || "560034";
  const phone = prof.phone || "+91 98450 12345";
  const gstin = prof.gstin || "29AAAAA0000A1Z5";
  const storeType = prof.store_type || "Supermarket";
  const audience = prof.audience_reach || prof.audience_size || 1420;
  const capital = prof.working_capital || prof.total_working_capital_inr || 500000;
  const margin = prof.min_gross_margin_target_pct || prof.default_min_margin_pct || 15.0;

  // Apply to Header and Profile Screen
  const topStore = document.getElementById("topStoreName");
  if (topStore) topStore.innerText = storeName;
  const topLoc = document.getElementById("topStoreLocation");
  if (topLoc) topLoc.innerText = `${city} • ${region.split("&")[0].trim()}`;
  const intelReg = document.getElementById("intelRegionName");
  if (intelReg) intelReg.innerText = region;

  // Set Profile fields
  const elStoreName = document.getElementById("profStoreName");
  if (elStoreName) elStoreName.value = storeName;
  const elOwner = document.getElementById("profOwnerName");
  if (elOwner) elOwner.value = prof.owner_name || "Ramesh Sharma";
  const elRegion = document.getElementById("profStateRegion");
  if (elRegion) elRegion.value = region;
  const elCity = document.getElementById("profCity");
  if (elCity) elCity.value = city;
  const elLocality = document.getElementById("profLocality");
  if (elLocality) elLocality.value = locality;
  const elPin = document.getElementById("profPin");
  if (elPin) elPin.value = pin;
  const elPhone = document.getElementById("profPhone");
  if (elPhone) elPhone.value = phone;
  const elGSTIN = document.getElementById("profGSTIN");
  if (elGSTIN) elGSTIN.value = gstin;
  const elStoreType = document.getElementById("profStoreType");
  if (elStoreType) elStoreType.value = storeType;
  const elAudience = document.getElementById("profAudienceSize");
  if (elAudience) elAudience.value = audience;
  const elCapital = document.getElementById("profWorkingCapital");
  if (elCapital) elCapital.value = capital;
  const elMargin = document.getElementById("profMinMargin");
  if (elMargin) elMargin.value = margin;

  // Sync calendar region select
  const calRegion = document.getElementById("calendarRegionSelect");
  if (calRegion) calRegion.value = region;

  // Sync Copilot Store Pill on Screen 2
  const copilotPill = document.getElementById("copilotStorePill");
  if (copilotPill) copilotPill.innerText = `📍 ${city} (${region.split("&")[0].trim()}) • Active Copilot`;
}

async function fetchStorageStatus() {
  try {
    const res = await fetch("/api/storage/status");
    if (!res.ok) return;
    const data = await res.json();
    const badgeEl = document.getElementById("storageStatusBadge");
    const collsEl = document.getElementById("storageCollectionsBadge");
    if (badgeEl) {
      if (data.mode === "CLOUD" && data.firestore_connected) {
        badgeEl.innerHTML = `🟢 <strong>Cloud Mode (Firestore Live)</strong>`;
        badgeEl.style.color = "#15803d";
      } else {
        badgeEl.innerHTML = `🟡 <strong>Local Fallback Mode (Zero Downtime)</strong>`;
        badgeEl.style.color = "#b45309";
      }
    }
    if (collsEl && data.collections) {
      collsEl.innerText = `stores/${data.store_id}/[inventory, promotions, calendar_events, store_profile, knowledge_catalog]`;
    }
  } catch (err) {
    console.warn("Could not query /api/storage/status:", err);
  }
}

async function fetchStoreProfile() {
  try {
    const res = await fetch("/api/store/profile");
    if (!res.ok) return;
    const profile = await res.json();
    applyProfileToUI(profile);
    if (profile.store_name) localStorage.setItem("promomind_store_name", profile.store_name);
    if (profile.owner_name) localStorage.setItem("promomind_owner_name", profile.owner_name);
    if (profile.phone) localStorage.setItem("promomind_phone", profile.phone);
    if (profile.gstin) localStorage.setItem("promomind_gstin", profile.gstin);
    if (profile.store_type) localStorage.setItem("promomind_store_type", profile.store_type);
    if (profile.audience_size !== undefined && profile.audience_size !== null) {
      localStorage.setItem("promomind_audience", String(profile.audience_size));
    }
    if (profile.region) localStorage.setItem("promomind_region", profile.region);
    if (profile.city) localStorage.setItem("promomind_city", profile.city);
    if (profile.locality) localStorage.setItem("promomind_locality", profile.locality);
    if (profile.pin_code) localStorage.setItem("promomind_pin", profile.pin_code);
    if (profile.total_working_capital_inr || profile.working_capital) {
      localStorage.setItem("promomind_capital", String(profile.total_working_capital_inr || profile.working_capital));
    }
    if (profile.default_min_margin_pct || profile.min_gross_margin_target_pct) {
      localStorage.setItem("promomind_margin", String(profile.default_min_margin_pct || profile.min_gross_margin_target_pct));
    }
  } catch (err) {
    console.warn("Could not fetch remote store profile:", err);
  }
}

async function saveStoreProfile() {
  const storeName = (document.getElementById("profStoreName")?.value || "Metro Supermarket & Retail Mart").trim();
  const owner = (document.getElementById("profOwnerName")?.value || "Ramesh Sharma").trim();
  const phone = (document.getElementById("profPhone")?.value || "+91 98450 12345").trim();
  const gstin = (document.getElementById("profGSTIN")?.value || "29AAAAA0000A1Z5").trim();
  const storeType = document.getElementById("profStoreType")?.value || "Supermarket";
  const audience = parseInt(document.getElementById("profAudienceSize")?.value?.trim() || "1420", 10) || 1420;
  const region = document.getElementById("profStateRegion")?.value || "Karnataka & South India";
  const city = (document.getElementById("profCity")?.value || "Bengaluru").trim();
  const locality = (document.getElementById("profLocality")?.value || "Koramangala 4th Block").trim();
  const pin = (document.getElementById("profPin")?.value || "560034").trim();
  const capital = parseFloat(document.getElementById("profWorkingCapital")?.value || "500000") || 500000;
  const margin = parseFloat(document.getElementById("profMinMargin")?.value || "15.0") || 15.0;

  const prof = {
    store_name: storeName,
    owner_name: owner,
    phone: phone,
    gstin: gstin,
    store_type: storeType,
    audience_reach: audience,
    audience_size: audience,
    working_capital: capital,
    total_working_capital_inr: capital,
    min_gross_margin_target_pct: margin,
    default_min_margin_pct: margin,
    state_region: region,
    region: region,
    city: city,
    locality: locality,
    pincode: pin,
    pin_code: pin
  };

  localStorage.setItem("promomind_store_name", storeName);
  localStorage.setItem("promomind_owner_name", owner);
  localStorage.setItem("promomind_phone", phone);
  localStorage.setItem("promomind_gstin", gstin);
  localStorage.setItem("promomind_store_type", storeType);
  localStorage.setItem("promomind_audience", String(audience));
  localStorage.setItem("promomind_region", region);
  localStorage.setItem("promomind_city", city);
  localStorage.setItem("promomind_locality", locality);
  localStorage.setItem("promomind_pin", pin);
  localStorage.setItem("promomind_capital", String(capital));
  localStorage.setItem("promomind_margin", String(margin));

  // Sync with both endpoints
  try {
    await fetch("/api/profile", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(prof)
    });
  } catch (err) {
    console.error("Error saving profile to /api/profile:", err);
  }

  try {
    await fetch("/api/store/profile", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        store_name: storeName,
        owner_name: owner,
        phone: phone,
        gstin: gstin,
        store_type: storeType,
        audience_size: audience,
        region: region,
        city: city,
        locality: locality,
        pin_code: pin,
        total_working_capital_inr: capital,
        default_min_margin_pct: margin
      })
    });
  } catch (err) {
    console.warn("Could not push profile to /api/store/profile:", err);
  }

  applyProfileToUI(prof);
  if (typeof fetchKnowledgeMarkdown === "function") fetchKnowledgeMarkdown();
  if (typeof fetchStoreROI === "function") fetchStoreROI();
  if (typeof fetchStorageStatus === "function") fetchStorageStatus();
  showToast("Store profile & regional preferences saved & synced to AI Knowledge Base & Cloud Storage!");
}

function onProfileRegionChanged(region) {
  document.getElementById("calendarRegionSelect").value = region;
  document.getElementById("intelRegionName").innerText = region;
  updateRegionalTicker(region);
}

function onRegionChanged(region) {
  document.getElementById("profStateRegion").value = region;
  document.getElementById("intelRegionName").innerText = region;
  localStorage.setItem("promomind_region", region);
  updateRegionalTicker(region);
  fetchCalendarEvents();
}

function updateRegionalTicker(region) {
  const tickerEl = document.getElementById("tickerEventName");
  if (region.includes("Karnataka") || region.includes("South")) {
    tickerEl.innerText = "Diwali / Deepavali (South India)";
  } else if (region.includes("Maharashtra") || region.includes("West")) {
    tickerEl.innerText = "Diwali Lakshmi Pujan & Gudi Padwa";
  } else if (region.includes("Bengal") || region.includes("East")) {
    tickerEl.innerText = "Kali Puja & Durga Mahotsav";
  } else {
    tickerEl.innerText = "Diwali Maha Utsav (North India)";
  }
}

function setThemeMode(mode) {
  if (mode === "dark") {
    document.body.classList.add("dark-theme");
    document.body.classList.remove("light-theme");
    document.getElementById("themeToggleBtn").innerText = "☀️";
    const radioDark = document.getElementById("themeRadioDark");
    if (radioDark) radioDark.checked = true;
  } else {
    document.body.classList.remove("dark-theme");
    document.body.classList.add("light-theme");
    document.getElementById("themeToggleBtn").innerText = "🌙";
    const radioLight = document.getElementById("themeRadioLight");
    if (radioLight) radioLight.checked = true;
  }
  localStorage.setItem("promomind_theme", mode);

  // Redraw chart if open
  if (currentBrandComparison) {
    renderBrandSvgChart();
  }
}

function toggleTheme() {
  const isDark = document.body.classList.contains("dark-theme");
  setThemeMode(isDark ? "light" : "dark");
}

// ==============================================================================
// Screen 1: Inventory & Multi-Brand Sales Graph
// ==============================================================================

async function fetchInventory() {
  try {
    const res = await fetch("/api/inventory");
    if (!res.ok) throw new Error("Failed to fetch inventory");
    inventoryItems = await res.json();
    updateInventoryKPIs(inventoryItems);
    renderInventory(inventoryItems);
    populateAnchorDropdown(inventoryItems);
    populateSandboxSKUDropdown(inventoryItems);
    fetchStoreROI();
  } catch (err) {
    console.error("Error fetching inventory:", err);
    document.getElementById("inventoryTableBody").innerHTML = `
      <tr><td colspan="8" class="loading-td" style="color:var(--g-red);">⚠️ Failed to connect to inventory service. Retrying...</td></tr>
    `;
  }
}

async function fetchStoreROI() {
  try {
    const res = await fetch("/api/store/financial-roi");
    if (!res.ok) return;
    const data = await res.json();

    const invested = data.total_inventory_invested_inr ?? data.total_capital_invested ?? 0;
    const turnover = data.projected_sales_revenue_inr ?? data.projected_monthly_turnover ?? 0;
    const profit = data.projected_gross_profit_inr ?? data.projected_monthly_profit ?? 0;
    const roi = data.overall_roi_pct ?? data.effective_roi_pct ?? 0;
    const deadCap = data.dead_capital_at_risk_inr ?? data.dead_capital_at_risk ?? 0;
    const unlocked = data.unlocked_capital_from_promos_inr ?? data.unlocked_cash_via_promos ?? 0;
    const boost = data.net_promo_profit_boost_inr ?? data.promo_profit_boost ?? 0;

    const elInv = document.getElementById("roiInvestedVal");
    if (elInv) elInv.innerText = `₹${Math.round(invested).toLocaleString("en-IN")}`;
    const elInvSub = document.getElementById("roiInvestedSub");
    if (elInvSub) elInvSub.innerText = `In Store Inventory`;

    const elRev = document.getElementById("roiRevenueVal");
    if (elRev) elRev.innerText = `₹${Math.round(turnover).toLocaleString("en-IN")}`;
    const elProf = document.getElementById("roiProfitVal");
    if (elProf) elProf.innerText = `₹${Math.round(profit).toLocaleString("en-IN")}`;
    const elRoiBadge = document.getElementById("roiProfitPctBadge");
    if (elRoiBadge) elRoiBadge.innerText = `+${roi}% Net Return (ROI)`;

    const elDead = document.getElementById("roiDeadCapitalVal");
    if (elDead) elDead.innerText = `₹${Math.round(deadCap).toLocaleString("en-IN")}`;
    const elDeadSub = document.getElementById("roiDeadSkusSub");
    if (elDeadSub) elDeadSub.innerText = `In slow movers (>60d)`;

    const elCash = document.getElementById("roiUnlockedCashVal");
    if (elCash) elCash.innerText = `₹${Math.round(unlocked).toLocaleString("en-IN")}`;
    const elBoost = document.getElementById("roiPromoBoostSub");
    if (elBoost) elBoost.innerText = `+₹${Math.round(boost).toLocaleString("en-IN")} Net Promo Boost`;
  } catch (err) {
    console.error("Error fetching store financial ROI:", err);
  }
}

function toggleRoiSimulator() {
  const drawer = document.getElementById("roiSimulatorDrawer");
  const icon = document.getElementById("simToggleIcon");
  const text = document.getElementById("simToggleText");
  if (!drawer) return;
  const isHidden = drawer.classList.contains("hidden");

  if (isHidden) {
    drawer.classList.remove("hidden");
    if (icon) icon.innerText = "✖";
    if (text) text.innerText = "Close Simulator";
    runInteractiveRoiSimulation();
  } else {
    drawer.classList.add("hidden");
    if (icon) icon.innerText = "⚡";
    if (text) text.innerText = 'Open "What-If" ROI Simulator';
  }
}

async function runInteractiveRoiSimulation() {
  const discSlider = document.getElementById("simDiscountSlider");
  const volSlider = document.getElementById("simVolumeSlider");
  const discount = discSlider ? parseFloat(discSlider.value) : 16;
  const volume = volSlider ? parseFloat(volSlider.value) : 35;

  const discBadge = document.getElementById("simDiscountBadge");
  if (discBadge) discBadge.innerText = `${discount}% OFF`;
  const volBadge = document.getElementById("simVolumeBadge");
  if (volBadge) volBadge.innerText = `+${volume}% Units`;

  try {
    const res = await fetch("/api/store/simulate-roi", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        proposed_discount_depth_pct: discount,
        expected_volume_lift_pct: volume
      })
    });
    if (!res.ok) return;
    const sim = await res.json();

    const simRev = sim.simulated_revenue_inr ?? sim.simulated_turnover ?? 0;
    const simProf = sim.simulated_net_profit_inr ?? sim.simulated_net_profit ?? 0;
    const simRoi = sim.simulated_roi_pct ?? 0;
    const speedup = sim.capital_turnover_days_saved ?? sim.capital_turnover_speedup_days ?? 0;

    const elTurnover = document.getElementById("simTurnoverVal");
    if (elTurnover) elTurnover.innerText = `₹${Math.round(simRev).toLocaleString("en-IN")}`;
    const elProfit = document.getElementById("simProfitVal");
    if (elProfit) elProfit.innerText = `₹${Math.round(simProf).toLocaleString("en-IN")}`;
    const elRoi = document.getElementById("simRoiVal");
    if (elRoi) elRoi.innerText = `+${simRoi}%`;
    const elSpeed = document.getElementById("simSpeedupVal");
    if (elSpeed) elSpeed.innerText = `${speedup} Days Faster`;

    const verdictEl = document.getElementById("simVerdictBadge");
    if (verdictEl) {
      if (sim.is_profit_positive) {
        verdictEl.className = "badge-safe";
        verdictEl.innerText = "PROFIT POSITIVE";
      } else {
        verdictEl.className = "badge-warning";
        verdictEl.innerText = "MARGIN DILUTION RISK";
      }
    }
  } catch (err) {
    console.error("Error running ROI simulation:", err);
  }
}

function updateInventoryKPIs(items) {
  const totalSKUs = items.length;
  let totalValuation = 0;
  let fastMovers = 0;
  let stockoutAlerts = 0;

  items.forEach(item => {
    totalValuation += (item.stock_quantity * item.cost_price);
    if (item.velocity_status === "FAST_MOVING") fastMovers++;
    if (item.stock_quantity <= 20 || (item.sell_through_verdict && item.sell_through_verdict.includes("STRONG_INVEST"))) {
      stockoutAlerts++;
    }
  });

  document.getElementById("kpiTotalSKUs").innerText = totalSKUs;
  document.getElementById("kpiStockValuation").innerText = "₹" + Math.round(totalValuation).toLocaleString("en-IN");
  document.getElementById("kpiFastMovers").innerText = fastMovers;
  document.getElementById("kpiStockoutAlerts").innerText = stockoutAlerts;
}

function renderInventory(items) {
  const tbody = document.getElementById("inventoryTableBody");
  if (!items || items.length === 0) {
    tbody.innerHTML = `<tr><td colspan="8" class="loading-td">No products found matching filters.</td></tr>`;
    return;
  }

  tbody.innerHTML = items.map(item => {
    const marginPct = (((item.selling_price - item.cost_price) / item.selling_price) * 100).toFixed(1);
    
    // Stock status badge
    let stockClass = "tag-stock-good";
    let stockLabel = `${item.stock_quantity} in stock`;
    if (item.stock_quantity <= 15) {
      stockClass = "tag-stock-low";
      stockLabel = `⚠️ ${item.stock_quantity} Low Stock`;
    } else if (item.stock_quantity >= 120) {
      stockClass = "tag-stock-high";
      stockLabel = `📦 ${item.stock_quantity} High Stock`;
    }

    // Verdict badge styling
    let verdictClass = "verdict-caution";
    if (item.sell_through_verdict && item.sell_through_verdict.includes("STRONG_INVEST")) {
      verdictClass = "verdict-buy";
    } else if (item.sell_through_verdict && item.sell_through_verdict.includes("DO_NOT_REORDER")) {
      verdictClass = "verdict-hold";
    }

    return `
      <tr>
        <td>
          <div class="sku-name-cell">${item.name}</div>
          <div class="sku-sub">${item.id}</div>
        </td>
        <td>${item.category}</td>
        <td><span class="stock-tag ${stockClass}">${stockLabel}</span></td>
        <td>
          <div>₹${item.cost_price} / <strong>₹${item.selling_price}</strong></div>
        </td>
        <td><strong>${marginPct}%</strong></td>
        <td>
          <div>${item.weekly_sales_avg || 20} units/wk</div>
          <div class="sku-sub">${item.velocity_status}</div>
        </td>
        <td>
          <span class="verdict-tag ${verdictClass}">${item.verdict_badge || 'Monitored'}</span>
        </td>
        <td>
          <button class="btn btn-sm btn-secondary" onclick="openBrandComparisonModal('${item.id}')" title="Compare competing brands for this category on the exact same graph">
            <span>📊</span> Brand Curves
          </button>
        </td>
      </tr>
    `;
  }).join("");
}

function filterInventory() {
  const query = (document.getElementById("inventorySearch").value || "").toLowerCase();
  const activePill = document.querySelector(".category-pills .pill-btn.active");
  const categoryFilter = activePill ? activePill.dataset.category || "ALL" : "ALL";

  const filtered = inventoryItems.filter(item => {
    const matchesSearch = item.name.toLowerCase().includes(query) ||
                          item.id.toLowerCase().includes(query) ||
                          item.category.toLowerCase().includes(query);
    const matchesCat = (categoryFilter === "ALL") || 
                       (item.category.toLowerCase().includes(categoryFilter.toLowerCase()));
    return matchesSearch && matchesCat;
  });

  renderInventory(filtered);
}

function setCategoryFilter(category, btn) {
  document.querySelectorAll(".category-pills .pill-btn").forEach(el => el.classList.remove("active"));
  btn.classList.add("active");
  btn.dataset.category = category;
  filterInventory();
}

// ==============================================================================
// Multi-Brand Comparative Sales Graph Modal
// (Amul vs Nandini vs Mother Dairy on the exact same chart)
// ==============================================================================

async function openBrandComparisonModal(productId) {
  const prod = inventoryItems.find(p => p.id === productId);
  if (!prod) return;

  try {
    const res = await fetch(`/api/inventory/${productId}/brand-comparison`);
    if (!res.ok) throw new Error("Failed to fetch brand comparison");
    const data = await res.json();
    currentBrandComparison = data;
    currentBrandComparison.selected_product = prod;

    // Populate modal titles
    document.getElementById("brandModalTitle").innerText = `Multi-Brand Sales Comparison: ${prod.category}`;
    document.getElementById("brandModalSubtitle").innerText = `Comparing ${data.brands.length} competing brands on the exact same past & projected sales axis`;
    document.getElementById("brandStrategyText").innerText = data.recommendation;

    // Render comparative metrics table
    renderBrandMetricsTable(data.brands);

    // Render SVG chart
    renderBrandSvgChart();

    // Show modal
    document.getElementById("brandModal").classList.remove("hidden");
  } catch (err) {
    console.error("Error loading brand comparison:", err);
    showToast("Error loading brand comparison data.");
  }
}

function closeBrandModal() {
  document.getElementById("brandModal").classList.add("hidden");
}

function closeBrandModalOnBackdrop(e) {
  if (e.target.id === "brandModal") closeBrandModal();
}

function setBrandChartView(viewMode) {
  brandChartViewMode = viewMode;
  document.getElementById("btnViewAllBrands").classList.toggle("active", viewMode === "ALL_BRANDS");
  document.getElementById("btnViewSingleSKU").classList.toggle("active", viewMode === "SINGLE_SKU");
  renderBrandSvgChart();
}

function renderBrandMetricsTable(brands) {
  const tbody = document.getElementById("brandComparisonTableBody");
  tbody.innerHTML = brands.map((b, idx) => {
    const color = BRAND_COLORS[idx % BRAND_COLORS.length].stroke;
    return `
      <tr>
        <td>
          <span style="display:inline-block;width:10px;height:10px;border-radius:50%;background-color:${color};margin-right:6px;"></span>
          <strong>${b.brand_name}</strong>
        </td>
        <td>₹${b.mrp}</td>
        <td>₹${b.cost_price}</td>
        <td><strong style="color:var(--g-green);">${b.margin_pct || b.margin_percent}%</strong></td>
        <td>${b.weekly_sales_avg || 25} units/wk</td>
        <td>${b.market_share_pct || 25}%</td>
        <td>
          <span class="stock-tag tag-stock-good">${b.turnover_rating || 'Active'}</span>
        </td>
      </tr>
    `;
  }).join("");
}

function renderBrandSvgChart() {
  if (!currentBrandComparison || !currentBrandComparison.brands) return;

  const svg = document.getElementById("brandSvgChart");
  const legendRow = document.getElementById("brandLegendRow");
  const xLabelsRow = document.getElementById("brandChartXLabels");

  const brands = (brandChartViewMode === "ALL_BRANDS")
    ? currentBrandComparison.brands
    : [currentBrandComparison.brands[0]];

  // SVG dimensions
  const width = 760;
  const height = 240;
  const paddingLeft = 45;
  const paddingRight = 30;
  const paddingTop = 25;
  const paddingBottom = 35;
  const chartW = width - paddingLeft - paddingRight;
  const chartH = height - paddingTop - paddingBottom;

  // Determine global max sales value across all plotted series
  let maxVal = 10;
  brands.forEach(b => {
    const allWeeks = [...(b.past_sales || b.past_sales_weeks || []), ...(b.forecast_sales || b.projected_sales_weeks || [])];
    allWeeks.forEach(v => { if (v > maxVal) maxVal = v; });
  });
  maxVal = Math.ceil(maxVal * 1.15); // Add headroom

  // Legend generation
  legendRow.innerHTML = brands.map((b, idx) => {
    const color = BRAND_COLORS[idx % BRAND_COLORS.length].stroke;
    return `
      <div class="legend-chip">
        <span class="legend-dot" style="background-color: ${color};"></span>
        <span>${b.brand_name}</span>
      </div>
    `;
  }).join("");

  // Total weeks on X axis (typically 6-8 past weeks + 4 forecast weeks = 10-12 data points)
  const samplePast = brands[0].past_sales || brands[0].past_sales_weeks || [20, 22, 24, 25, 26, 28];
  const sampleFore = brands[0].forecast_sales || brands[0].projected_sales_weeks || [32, 38, 44, 50];
  const totalPoints = samplePast.length + sampleFore.length;
  const stepX = chartW / (totalPoints - 1);

  // Build X-axis labels
  let labelsHtml = "";
  for (let i = 0; i < samplePast.length; i++) {
    labelsHtml += `<span>W${i + 1}</span>`;
  }
  for (let j = 0; j < sampleFore.length; j++) {
    labelsHtml += `<span style="color:var(--g-blue);font-weight:700;">F${j + 1} (Surge)</span>`;
  }
  xLabelsRow.innerHTML = labelsHtml;

  // Build SVG content
  let svgContent = `
    <defs>
      <linearGradient id="forecastHatch" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="rgba(26,115,232,0.08)"/>
        <stop offset="100%" stop-color="rgba(26,115,232,0.01)"/>
      </linearGradient>
    </defs>
  `;

  // Background Forecast Region Highlight
  const forecastStartX = paddingLeft + (samplePast.length - 1) * stepX;
  const forecastWidth = (sampleFore.length) * stepX;
  svgContent += `
    <rect x="${forecastStartX}" y="${paddingTop}" width="${forecastWidth}" height="${chartH}" fill="url(#forecastHatch)" rx="4"/>
    <line x1="${forecastStartX}" y1="${paddingTop}" x2="${forecastStartX}" y2="${height - paddingBottom}" stroke="#9aa0a6" stroke-dasharray="4,4" stroke-width="1.5"/>
    <text x="${forecastStartX + 10}" y="${paddingTop + 14}" fill="#1a73e8" font-size="11" font-weight="600">⚡ Festive Forecast Zone</text>
  `;

  // Grid lines
  for (let g = 0; g <= 4; g++) {
    const yVal = Math.round(maxVal * (g / 4));
    const yPos = height - paddingBottom - (g / 4) * chartH;
    svgContent += `
      <line x1="${paddingLeft}" y1="${yPos}" x2="${width - paddingRight}" y2="${yPos}" stroke="rgba(128,134,139,0.2)" stroke-width="1"/>
      <text x="${paddingLeft - 8}" y="${yPos + 4}" fill="#80868b" font-size="10" text-anchor="end">${yVal}</text>
    `;
  }

  // Draw lines for each brand
  brands.forEach((brand, idx) => {
    const color = BRAND_COLORS[idx % BRAND_COLORS.length].stroke;
    const past = brand.past_sales || brand.past_sales_weeks || [];
    const fore = brand.forecast_sales || brand.projected_sales_weeks || [];

    // Past sales points
    let pastPath = "";
    past.forEach((val, i) => {
      const x = paddingLeft + i * stepX;
      const y = height - paddingBottom - (val / maxVal) * chartH;
      pastPath += (i === 0 ? `M ${x} ${y}` : ` L ${x} ${y}`);
    });

    // Forecast sales points
    let forePath = "";
    const bridgeX = paddingLeft + (past.length - 1) * stepX;
    const bridgeY = height - paddingBottom - (past[past.length - 1] / maxVal) * chartH;
    forePath = `M ${bridgeX} ${bridgeY}`;
    fore.forEach((val, j) => {
      const x = paddingLeft + (past.length + j) * stepX;
      const y = height - paddingBottom - (val / maxVal) * chartH;
      forePath += ` L ${x} ${y}`;
    });

    // Append Path
    svgContent += `
      <!-- Past Line -->
      <path d="${pastPath}" fill="none" stroke="${color}" stroke-width="2.5" stroke-linecap="round"/>
      <!-- Forecast Line (Dashed) -->
      <path d="${forePath}" fill="none" stroke="${color}" stroke-width="2.5" stroke-dasharray="5,4" stroke-linecap="round"/>
    `;

    // Render Data Circles
    past.forEach((val, i) => {
      const x = paddingLeft + i * stepX;
      const y = height - paddingBottom - (val / maxVal) * chartH;
      svgContent += `
        <circle cx="${x}" cy="${y}" r="3.5" fill="${color}">
          <title>${brand.brand_name} (Week ${i + 1}): ${val} units</title>
        </circle>
      `;
    });

    fore.forEach((val, j) => {
      const x = paddingLeft + (past.length + j) * stepX;
      const y = height - paddingBottom - (val / maxVal) * chartH;
      svgContent += `
        <circle cx="${x}" cy="${y}" r="4.5" fill="#ffffff" stroke="${color}" stroke-width="2">
          <title>${brand.brand_name} (Forecast Week ${j + 1}): ${val} projected units</title>
        </circle>
      `;
    });
  });

  svg.innerHTML = svgContent;
}

function useProductInPromoFromModal() {
  if (!currentBrandComparison || !currentBrandComparison.selected_product) return;
  const prod = currentBrandComparison.selected_product;
  closeBrandModal();
  switchScreen("promos");

  // Select this product in anchor dropdown
  const anchorSelect = document.getElementById("promoAnchorSelect");
  if (anchorSelect) {
    anchorSelect.value = prod.id;
    onAnchorProductSelected(prod.id);
  }
}

// ==============================================================================
// Screen 2: Promo Generator Engine & Conflict Prevention
// ==============================================================================

function populateAnchorDropdown(items) {
  const select = document.getElementById("promoAnchorSelect");
  if (!select) return;

  select.innerHTML = `<option value="">-- Choose High-Velocity Anchor Product --</option>` +
    items.map(p => `
      <option value="${p.id}">${p.name} (Stock: ${p.stock_quantity} | MRP: ₹${p.selling_price})</option>
    `).join("");
}

function onAnchorProductSelected(anchorId) {
  const attachedSelect = document.getElementById("promoAttachedSelect");
  if (!anchorId) {
    attachedSelect.innerHTML = `<option value="">Select Anchor first...</option>`;
    return;
  }

  const anchor = inventoryItems.find(p => p.id === anchorId);
  const otherItems = inventoryItems.filter(p => p.id !== anchorId);

  // Compute smart pair suggestions with simulated Apriori affinity probability
  attachedSelect.innerHTML = `<option value="">-- Recommended Co-Purchase Partner --</option>` +
    otherItems.map(p => {
      let prob = "45%";
      let lift = "1.6x";
      if (anchor && anchor.category === "Beverages" && p.category === "Snacks") {
        prob = "68%"; lift = "2.2x";
      } else if (anchor && anchor.category === "Dairy" && p.category === "Dry Fruits") {
        prob = "54%"; lift = "1.8x";
      } else if (anchor && anchor.category === "Staples & Oils" && p.category === "Dairy") {
        prob = "49%"; lift = "1.5x";
      }
      return `<option value="${p.id}">${p.name} (Affinity P(B|A)=${prob}, Lift=${lift})</option>`;
    }).join("");

  checkConflictForSelectedProducts();
}

async function checkConflictForSelectedProducts() {
  const anchorId = document.getElementById("promoAnchorSelect").value;
  const attachedId = document.getElementById("promoAttachedSelect").value;
  const banner = document.getElementById("promoConflictAlertBanner");

  if (!anchorId) {
    banner.classList.add("hidden");
    return;
  }

  try {
    const res = await fetch("/api/offers/check-conflict", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        anchor_id: anchorId,
        attached_id: attachedId || "NONE",
        proposed_discount_pct: 18.0
      })
    });
    if (!res.ok) return;
    const data = await res.json();

    if (data.has_conflict) {
      banner.classList.remove("hidden");
      document.getElementById("promoConflictTitle").innerText = "⚠️ Active Campaign Conflict Detected!";
      document.getElementById("promoConflictMessage").innerText = data.conflict_reason;
    } else {
      banner.classList.add("hidden");
    }
  } catch (err) {
    console.error("Error during conflict pre-check:", err);
  }
}

function selectGoalPreset(presetKey, btn) {
  document.querySelectorAll(".goal-presets-grid .goal-btn").forEach(el => el.classList.remove("active"));
  btn.classList.add("active");

  const promptInput = document.getElementById("promoPromptInput");
  const marginSlider = document.getElementById("promoMarginSlider");
  const marginBadge = document.getElementById("marginDisplayBadge");
  const eventSelect = document.getElementById("promoEventSelect");
  const offerTypeSelect = document.getElementById("promoOfferType");

  if (presetKey === "diwali_festive") {
    promptInput.value = "Create a premium Diwali festive combo pairing high-velocity Pure Cow Ghee with Dry Fruits or Sweets at an attractive discount for family celebrations.";
    marginSlider.value = 18;
    marginBadge.innerText = "18%";
    eventSelect.value = "Diwali Maha Utsav (Big Billion Days Edition)";
    offerTypeSelect.value = "COMBO_DISCOUNT";
    // Pre-select Ghee if available
    const ghee = inventoryItems.find(p => p.id.includes("GHEE"));
    if (ghee) {
      document.getElementById("promoAnchorSelect").value = ghee.id;
      onAnchorProductSelected(ghee.id);
    }
  } else if (presetKey === "clear_slow") {
    promptInput.value = "Bundle my slow-moving overstock biscuits with fast-selling morning tea to clear warehouse space before the expiry deadline.";
    marginSlider.value = 14;
    marginBadge.innerText = "14%";
    offerTypeSelect.value = "BOGO";
  } else if (presetKey === "high_margin") {
    promptInput.value = "Design an everyday high-margin essentials basket combining premium tea and cooking staples yielding over 22% net profit.";
    marginSlider.value = 22;
    marginBadge.innerText = "22%";
    offerTypeSelect.value = "COMBO_DISCOUNT";
  } else if (presetKey === "weekend_rush") {
    promptInput.value = "Fast 48-hour weekend grocery flash saver to boost retail counter basket size and turnover.";
    marginSlider.value = 16;
    marginBadge.innerText = "16%";
    eventSelect.value = "Super Weekend Retail Rush";
    offerTypeSelect.value = "COMBO_DISCOUNT";
  }
}

function resetPromoForm() {
  document.getElementById("promoAnchorSelect").value = "";
  document.getElementById("promoAttachedSelect").innerHTML = `<option value="">Select Anchor first...</option>`;
  document.getElementById("promoPromptInput").value = "";
  document.getElementById("promoConflictAlertBanner").classList.add("hidden");
  document.getElementById("planResultContainer").classList.add("hidden");
  document.getElementById("emptyPromoPlaceholder").classList.remove("hidden");
}

function selectPromoArchetype(archetype, btn) {
  document.querySelectorAll(".archetype-chips-grid .archetype-chip").forEach(el => el.classList.remove("active"));
  btn.classList.add("active");
  const input = document.getElementById("selectedArchetypeInput");
  if (input) input.value = archetype;
}

function copyCashierScript() {
  const el = document.getElementById("cashierScriptText");
  if (!el) return;
  navigator.clipboard.writeText(el.innerText).then(() => {
    showToast("Cashier verbal pitch copied to clipboard!");
  }).catch(() => {
    showToast("Copied script text!");
  });
}

// ==============================================================================
// Autonomous Weekly Offer Ideas (No Product Selection Needed)
// ==============================================================================

let cachedWeeklyIdeas = [];

async function toggleWeeklyOfferIdeas() {
  const panel = document.getElementById("weeklyIdeasPanel");
  if (!panel) return;
  if (!panel.classList.contains("hidden")) {
    panel.classList.add("hidden");
    return;
  }
  panel.classList.remove("hidden");
  await fetchWeeklyOfferIdeas();
}

function closeWeeklyOfferIdeas() {
  const panel = document.getElementById("weeklyIdeasPanel");
  if (panel) panel.classList.add("hidden");
}

async function fetchWeeklyOfferIdeas() {
  const grid = document.getElementById("weeklyIdeasGrid");
  if (!grid) return;
  grid.innerHTML = `<div style="grid-column:1/-1;text-align:center;padding:24px;color:var(--text-secondary);">⏳ Scanning store inventory velocity, shelf-life, and regional demand...</div>`;

  try {
    const region = (document.getElementById("profStateRegion") && document.getElementById("profStateRegion").value) || "Karnataka & South India";
    const res = await fetch(`/api/weekly-offer-ideas?region=${encodeURIComponent(region)}`);
    if (!res.ok) throw new Error("Failed to load weekly ideas");
    const data = await res.json();
    cachedWeeklyIdeas = data.ideas || [];
    renderWeeklyOfferIdeas(cachedWeeklyIdeas);
  } catch (err) {
    console.error("Error fetching weekly ideas:", err);
    grid.innerHTML = `<div style="grid-column:1/-1;color:red;padding:12px;">Error loading weekly offer ideas: ${err.message}</div>`;
  }
}

function renderWeeklyOfferIdeas(ideas) {
  const grid = document.getElementById("weeklyIdeasGrid");
  if (!grid) return;
  if (!ideas || ideas.length === 0) {
    grid.innerHTML = `<div style="grid-column:1/-1;padding:16px;text-align:center;">No offer ideas found. Add at least 2 products to your store inventory.</div>`;
    return;
  }

  grid.innerHTML = ideas.map((idea, idx) => `
    <div class="weekly-idea-card">
      <div>
        <div class="wic-top">
          <span class="wic-icon">${idea.icon || '🏷️'}</span>
          <span class="vcard-badge ${idea.badge_class || 'badge-variety-recommended'}">${idea.badge}</span>
        </div>
        <h4 class="wic-title">${idea.title}</h4>
        <div class="wic-tagline">${idea.tagline}</div>

        <div class="wic-pair-box">
          <div class="wic-pair-item">
            <span><strong>Anchor:</strong> ${idea.anchor_name}</span>
            <span>MRP ₹${Math.round(idea.anchor_mrp)}</span>
          </div>
          <div class="wic-pair-item">
            <span><strong>Attached:</strong> ${idea.attached_name}</span>
            <span>MRP ₹${Math.round(idea.attached_mrp)}</span>
          </div>
        </div>

        <div class="wic-price-row">
          <span class="wic-price">₹${Math.round(idea.combo_price)}</span>
          <span class="wic-mrp">₹${Math.round(idea.original_mrp)}</span>
          <span class="wic-savings">Save ₹${Math.round(idea.savings_amount)} (${idea.discount_pct}% OFF)</span>
        </div>

        <div class="wic-margin-row">
          <span>Net Profit Margin: <strong style="color:var(--g-green);">${idea.net_margin_pct}%</strong></span>
          <span>Volume Lift: <strong>+${idea.volume_lift_pct}%</strong></span>
        </div>

        <div class="wic-why">
          💡 <strong>Why it works:</strong> ${idea.why_recommended}
        </div>
      </div>

      <button type="button" class="btn btn-primary btn-block wic-btn" onclick="applyWeeklyOfferIdea(${idx})">
        <span>⚡</span> Apply & Generate Campaign
      </button>
    </div>
  `).join("");
}

async function applyWeeklyOfferIdea(idx) {
  const idea = cachedWeeklyIdeas[idx];
  if (!idea) return;

  // Set anchor in dropdown
  const anchorSelect = document.getElementById("promoAnchorSelect");
  if (anchorSelect) {
    anchorSelect.value = idea.anchor_id;
    onAnchorProductSelected(idea.anchor_id);
  }

  // Set attached in dropdown
  setTimeout(() => {
    const attachedSelect = document.getElementById("promoAttachedSelect");
    if (attachedSelect) attachedSelect.value = idea.attached_id;
  }, 60);

  // Set archetype chip
  const archBtn = document.querySelector(`.archetype-chip[data-archetype="${idea.archetype}"]`);
  if (archBtn) {
    selectPromoArchetype(idea.archetype, archBtn);
  }

  // Set event theme
  const eventSelect = document.getElementById("promoEventSelect");
  if (eventSelect && idea.event_theme) {
    eventSelect.value = idea.event_theme;
  }

  // Set prompt
  const promptInput = document.getElementById("promoPromptInput");
  if (promptInput) {
    promptInput.value = `Generate optimal promotion for ${idea.title}: Pairing ${idea.anchor_name} with ${idea.attached_name}.`;
  }

  // Close panel
  closeWeeklyOfferIdeas();
  showToast(`Applied "${idea.title}"! Generating full campaign...`);

  // Trigger campaign generation
  await generatePromotionPlan();
}

async function generatePromotionPlan() {
  const prompt = document.getElementById("promoPromptInput").value.trim() || "Create an optimal festive combo";
  const margin = parseFloat(document.getElementById("promoMarginSlider").value) || 18.0;
  const eventTheme = document.getElementById("promoEventSelect").value;
  const offerType = document.getElementById("promoOfferType").value;
  const anchorId = document.getElementById("promoAnchorSelect").value;
  const attachedId = document.getElementById("promoAttachedSelect").value;
  const archetype = (document.getElementById("selectedArchetypeInput") && document.getElementById("selectedArchetypeInput").value) || "ANCHOR_MARGIN_BOOSTER";
  const region = (document.getElementById("profStateRegion") && document.getElementById("profStateRegion").value) || "Karnataka & South India";

  const btn = document.getElementById("generatePlanBtn");
  btn.disabled = true;
  btn.innerHTML = `<span>⏳ Synthesizing Open-Source Models & Copy...</span>`;

  try {
    const res = await fetch("/api/generate-combo", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        prompt: prompt,
        min_margin_pct: margin,
        event_theme: eventTheme,
        offer_type: offerType,
        primary_product_id: anchorId || null,
        secondary_product_id: attachedId || null,
        region: region,
        archetype: archetype
      })
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Failed to generate combo plan");
    }

    const plan = await res.json();
    currentPlan = plan;
    renderGeneratedPlan(plan);
    showToast("Promotional plan & collateral successfully generated!");
  } catch (err) {
    console.error("Error generating combo:", err);
    showToast(`Error: ${err.message}`);
  } finally {
    btn.disabled = false;
    btn.innerHTML = `<span>✨ Generate AI Promotional Plan & Omnichannel Copy</span>`;
  }
}

let selectedVarietyIdx = 0;

function renderPromotionVarieties(varieties) {
  const container = document.getElementById("promoVarietiesGrid");
  const countBadge = document.getElementById("varietyCountBadge");
  if (!container) return;
  if (!varieties || varieties.length === 0) {
    container.innerHTML = "";
    if (countBadge) countBadge.innerText = "0 Modeled";
    return;
  }

  if (countBadge) countBadge.innerText = `${varieties.length} Offers Modeled`;

  container.innerHTML = varieties.map((v, idx) => {
    const isSelected = idx === selectedVarietyIdx;
    return `
      <div class="variety-choice-card ${isSelected ? 'selected' : ''}" onclick="selectPromotionVariety(${idx})">
        <div class="vcard-top">
          <span class="vcard-icon">${v.icon || '🏷️'}</span>
          <span class="vcard-badge ${v.badge_class || 'badge-variety-recommended'}">${v.badge || 'OFFER'}</span>
        </div>
        <h5 class="vcard-title">${v.title}</h5>
        <div class="vcard-price-row">
          <span class="vcard-price">₹${Math.round(v.combo_price)}</span>
          <span class="vcard-mrp">₹${Math.round(v.original_mrp)}</span>
          <span class="vcard-savings">Save ₹${Math.round(v.discount_amount)} (${v.discount_pct}% OFF)</span>
        </div>
        <div class="vcard-metrics-grid">
          <div class="vcard-m-item">
            <span class="label">Margin:</span>
            <span class="val" style="color: ${v.net_margin_pct >= 20 ? 'var(--g-green)' : (v.net_margin_pct >= 14 ? 'var(--g-blue)' : '#b45309')}">${v.net_margin_pct}%</span>
          </div>
          <div class="vcard-m-item">
            <span class="label">Vol. Lift:</span>
            <span class="val">+${v.projected_volume_lift_pct}%</span>
          </div>
          <div class="vcard-m-item">
            <span class="label">Turnover:</span>
            <span class="val">${v.capital_turnover_days} days</span>
          </div>
          <div class="vcard-m-item">
            <span class="label">Format:</span>
            <span class="val" style="font-size:10px;">${(v.variety_type || '').replace('VAR_', '')}</span>
          </div>
        </div>
        <div class="vcard-target">
          <span>🎯 ${v.customer_target}</span>
        </div>
        <button type="button" class="vcard-btn">
          ${isSelected ? '✓ Active Variety' : 'Apply Variety'}
        </button>
      </div>
    `;
  }).join("");
}

function selectPromotionVariety(idx) {
  if (!currentPlan || !currentPlan.varieties || !currentPlan.varieties[idx]) return;
  selectedVarietyIdx = idx;
  const v = currentPlan.varieties[idx];

  // Re-render variety cards with active state
  renderPromotionVarieties(currentPlan.varieties);

  // Update Active Variety Top Bar
  const avbIcon = document.getElementById("avbIcon");
  const avbTitle = document.getElementById("avbTitle");
  const avbTarget = document.getElementById("avbTarget");
  const avbTurnover = document.getElementById("avbTurnover");
  if (avbIcon) avbIcon.innerText = v.icon || '🏷️';
  if (avbTitle) avbTitle.innerText = `${v.title} — ₹${Math.round(v.combo_price)} (Save ₹${Math.round(v.discount_amount)})`;
  if (avbTarget) avbTarget.innerText = `🎯 Target: ${v.customer_target}`;
  if (avbTurnover) avbTurnover.innerText = `⚡ ${v.capital_turnover_days} Days Capital Recovery`;

  // Update Pricing Breakdown Pills
  const planOfferPrice = document.getElementById("planOfferPrice");
  const planSavings = document.getElementById("planSavings");
  const planMarginBadge = document.getElementById("planMarginBadge");
  if (planOfferPrice) planOfferPrice.innerText = `₹${Math.round(v.combo_price)}`;
  if (planSavings) planSavings.innerText = `₹${Math.round(v.discount_amount)} (${v.discount_pct}% OFF)`;
  if (planMarginBadge) planMarginBadge.innerText = `${v.net_margin_pct}% Net Margin`;

  // Update AI Rationale Text
  const rationaleEl = document.getElementById("planRationaleText");
  if (rationaleEl) {
    rationaleEl.innerHTML = `
      <strong>${v.title} (${v.badge}):</strong> Tailored for <em>${v.customer_target}</em>.
      At ₹${Math.round(v.combo_price)} (discounted by ₹${Math.round(v.discount_amount)} / ${v.discount_pct}%), it projects a <strong>+${v.projected_volume_lift_pct}% sales volume lift</strong> while strictly safeguarding a <strong>${v.net_margin_pct}% net merchant profit margin</strong>. Working capital is unlocked in <strong>${v.capital_turnover_days} days</strong>.
    `;
  }

  // Update WhatsApp Collateral
  const waMessageEl = document.getElementById("waMessageText");
  if (waMessageEl) waMessageEl.innerText = v.whatsapp_copy;
  const waLink = document.getElementById("openWhatsAppLink");
  if (waLink) waLink.href = `https://api.whatsapp.com/send?text=${encodeURIComponent(v.whatsapp_copy)}`;

  // Update In-Store Poster
  const posterTitle = document.getElementById("posterComboTitle");
  const posterDeal = document.getElementById("posterDealPrice");
  const posterSavingsEl = document.getElementById("posterSavings");
  if (posterTitle) posterTitle.innerText = (v.poster_headline || v.title).toUpperCase();
  if (posterDeal) posterDeal.innerText = `₹${Math.round(v.combo_price)}`;
  if (posterSavingsEl) posterSavingsEl.innerText = v.poster_savings || `YOU SAVE ₹${Math.round(v.discount_amount)} (${v.discount_pct}% OFF)`;

  // Update Cashier POS Upsell Pitch
  const cashierEl = document.getElementById("cashierScriptText");
  if (cashierEl) cashierEl.innerText = v.cashier_counter_pitch;
}

function renderGeneratedPlan(plan) {
  currentPlan = plan;
  document.getElementById("emptyPromoPlaceholder").classList.add("hidden");
  const resultCard = document.getElementById("planResultContainer");
  resultCard.classList.remove("hidden");

  // Plan header
  const comboTitle = plan.title || plan.combo_name || "Special Retail Bundle";
  document.getElementById("planThemeTag").innerText = plan.event_theme || "Festive Offer";
  document.getElementById("planTitle").innerText = comboTitle;
  document.getElementById("planMarginBadge").innerText = `${plan.net_margin_pct}% Net Margin`;

  // Baseline Pricing numbers
  const origPrice = plan.original_combined_mrp || plan.original_total_mrp || 0;
  const offerPrice = plan.recommended_combo_price || plan.bundle_selling_price || 0;
  const savings = plan.discount_amount || plan.savings_amount || 0;
  const combinedCost = (plan.anchor_product && plan.attached_product)
    ? (plan.anchor_product.cost_price + plan.attached_product.cost_price)
    : (plan.combined_cost || 0);

  document.getElementById("planOriginalPrice").innerText = `₹${Math.round(origPrice)}`;
  document.getElementById("planOfferPrice").innerText = `₹${Math.round(offerPrice)}`;
  document.getElementById("planSavings").innerText = `₹${Math.round(savings)} (${plan.discount_pct}% OFF)`;
  document.getElementById("planTotalCost").innerText = `₹${Math.round(combinedCost)}`;

  // AI Rationale
  document.getElementById("planRationaleText").innerText = plan.strategic_rationale || plan.ai_pitch || plan.ai_explanation || "";

  // WhatsApp text
  const waText = (plan.creative_assets && plan.creative_assets.whatsapp_message) || plan.whatsapp_copy || `🎉 Exclusive Festive Deal! Get ${comboTitle} for just ₹${offerPrice} (MRP ₹${origPrice}) at ${document.getElementById('topStoreName').innerText}! Limited stock.`;
  document.getElementById("waMessageText").innerText = waText;
  document.getElementById("waStoreNamePreview").innerText = document.getElementById("topStoreName").innerText;
  document.getElementById("openWhatsAppLink").href = `https://api.whatsapp.com/send?text=${encodeURIComponent(waText)}`;

  // Poster card
  document.getElementById("posterEventBadge").innerText = (plan.event_theme || "DIWALI SPECIAL").toUpperCase();
  document.getElementById("posterComboTitle").innerText = ((plan.creative_assets && plan.creative_assets.poster_headline) || comboTitle).toUpperCase();
  
  const itemNames = (plan.anchor_product && plan.attached_product)
    ? `${plan.anchor_product.name.split('(')[0].trim()} + ${plan.attached_product.name.split('(')[0].trim()}`
    : ((plan.items || []).map(i => i.name).join(" + ") || "Festive Products Duo");
  document.getElementById("posterBundleItems").innerText = itemNames;
  document.getElementById("posterMRP").innerText = `MRP ₹${Math.round(origPrice)}`;
  document.getElementById("posterDealPrice").innerText = `₹${Math.round(offerPrice)}`;
  document.getElementById("posterSavings").innerText = `YOU SAVE ₹${Math.round(savings)} (${plan.discount_pct}% OFF)`;
  document.getElementById("posterStoreLoc").innerText = `${document.getElementById('topStoreName').innerText}, ${document.getElementById('topStoreLocation').innerText}`;

  // Cashier POS counter script
  const cashierScriptEl = document.getElementById("cashierScriptText");
  if (cashierScriptEl) {
    const pitch = (plan.creative_assets && plan.creative_assets.cashier_counter_pitch) || plan.cashier_counter_pitch;
    if (pitch) {
      cashierScriptEl.innerText = pitch;
    } else {
      const anchorName = plan.anchor_product ? plan.anchor_product.name.split('(')[0].trim() : "this item";
      const attachedName = plan.attached_product ? plan.attached_product.name.split('(')[0].trim() : "this item";
      cashierScriptEl.innerText = `"Namaskara / Namaste! Sir, along with your ${anchorName}, if you take ${attachedName} today, you save flat ₹${Math.round(savings)}! Should I add it to your bag?"`;
    }
  }

  // Hybrid Neuro-Symbolic Architecture Data
  if (plan.hybrid_architecture) {
    const ha = plan.hybrid_architecture;
    const aiLayer = ha.ai_layer || {};
    const mathLayer = ha.math_layer || {};

    const elAiCtx = document.getElementById("hybridAiContext");
    const elAiVer = document.getElementById("hybridAiVernacular");
    const elAiPsy = document.getElementById("hybridAiPsychology");
    if (elAiCtx) elAiCtx.innerText = plan.event_theme || aiLayer.festive_driver || "Festival Shopping Rush";
    if (elAiVer) elAiVer.innerText = `${aiLayer.regional_grounding || 'Regional Store'} • Direct ₹ Bachat`;
    if (elAiPsy) elAiPsy.innerText = aiLayer.psychological_hook || "Basket Lift & Clearance Urgency";

    const elMathPED = document.getElementById("hybridMathPED");
    const elMathApriori = document.getElementById("hybridMathApriori");
    const elMathMargin = document.getElementById("hybridMathMargin");
    if (elMathPED) elMathPED.innerText = `${mathLayer.blended_elasticity || '-1.35'} (Category Elastic)`;
    if (elMathApriori) elMathApriori.innerText = `P(B|A) = ${mathLayer.apriori_confidence_pct || 62}% (Lift: ${mathLayer.apriori_lift || '1.8'}x)`;
    if (elMathMargin) elMathMargin.innerText = `✓ Safeguarded ${mathLayer.net_margin_pct || plan.net_margin_pct}% Net Margin Floor`;
  }

  // Multi-Variety Rendering: If varieties were generated, render them and select the recommended one
  if (plan.varieties && plan.varieties.length > 0) {
    const recIdx = plan.varieties.findIndex(v => v.is_recommended);
    selectedVarietyIdx = recIdx >= 0 ? recIdx : 0;
    renderPromotionVarieties(plan.varieties);
    selectPromotionVariety(selectedVarietyIdx);
  }
}

function switchCollateralTab(tabName, btn) {
  document.querySelectorAll(".collateral-tab-nav .c-tab-btn").forEach(el => el.classList.remove("active"));
  document.querySelectorAll(".collateral-tabs-container .c-tab-panel").forEach(el => el.classList.remove("active"));
  btn.classList.add("active");

  if (tabName === "whatsapp") {
    document.getElementById("cTabWhatsapp").classList.add("active");
  } else if (tabName === "poster") {
    document.getElementById("cTabPoster").classList.add("active");
  } else if (tabName === "cashier") {
    const pane = document.getElementById("cTabCashier");
    if (pane) pane.classList.add("active");
  }
}

function copyWhatsAppMessage() {
  const text = document.getElementById("waMessageText").innerText;
  navigator.clipboard.writeText(text).then(() => {
    showToast("WhatsApp broadcast copy copied to clipboard!");
  }).catch(() => {
    showToast("Failed to copy text.");
  });
}

async function activateCurrentOffer() {
  if (!currentPlan) return;

  const activeVar = (currentPlan.varieties && currentPlan.varieties[selectedVarietyIdx]) || null;
  const comboTitle = activeVar
    ? `${activeVar.title} (${currentPlan.title || currentPlan.combo_name})`
    : (currentPlan.title || currentPlan.combo_name || "Special Retail Bundle");
  const price = activeVar
    ? activeVar.combo_price
    : (currentPlan.recommended_combo_price || currentPlan.bundle_selling_price || 399);
  const discount_pct = activeVar
    ? activeVar.discount_pct
    : (currentPlan.discount_pct || 15);
  const anchor_id = currentPlan.anchor_product
    ? currentPlan.anchor_product.id
    : (currentPlan.items ? currentPlan.items[0].id : "PROD_TEA_01");
  const attached_id = currentPlan.attached_product
    ? currentPlan.attached_product.id
    : (currentPlan.items && currentPlan.items[1] ? currentPlan.items[1].id : "PROD_BISCUIT_01");

  try {
    const res = await fetch("/api/publish-offer", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        combo_id: currentPlan.combo_id || "COMBO_LIVE",
        title: comboTitle,
        anchor_id: anchor_id,
        attached_id: attached_id,
        discount_pct: discount_pct,
        price: price,
        event_theme: currentPlan.event_theme || "Active Campaign"
      })
    });
    if (!res.ok) throw new Error("Failed to activate offer");
    showToast(`Promotion active! Scheduled "${comboTitle}" in Calendar.`);
    if (typeof fetchScheduledOffers === "function") {
      await fetchScheduledOffers();
    }
    switchScreen("calendar");
  } catch (err) {
    console.error("Error activating offer:", err);
    showToast("Error activating offer.");
  }
}

// ==============================================================================
// Screen 3: Regional Festival Calendar & Conflict Management
// ==============================================================================

async function fetchCalendarEvents(forcedRegion, forcedCountry, isRefresh = false) {
  try {
    const customInput = document.getElementById("calendarCustomRegionInput");
    
    const region = forcedRegion || (customInput && customInput.value.trim()) || localStorage.getItem("promomind_region") || "Karnataka";
    const country = forcedCountry || "India";
    
    if (customInput && !customInput.value.trim()) {
      customInput.value = region.split("&")[0].trim();
    }

    const badge = document.getElementById("calActiveRegionBadge");
    if (badge) badge.innerText = `📍 Active State: ${region.split("&")[0].trim()}`;

    const url = `/api/calendar/events?region=${encodeURIComponent(region)}&country=${encodeURIComponent(country)}&refresh=${isRefresh}`;
    const res = await fetch(url);
    if (!res.ok) throw new Error("Failed to load calendar events");
    regionalEvents = await res.json();
    renderFestivalCards(regionalEvents);
    updateRegionalIntelCard(regionalEvents, region, country);
  } catch (err) {
    console.error("Error fetching calendar:", err);
  }
}

async function discoverCustomRegionFestivals() {
  const customInput = document.getElementById("calendarCustomRegionInput");
  const btn = document.getElementById("discoverFestivalsBtn");
  const listEl = document.getElementById("festivalCardsList");

  const region = (customInput && customInput.value.trim()) || "Karnataka";
  const country = "India";

  if (btn) {
    btn.disabled = true;
    btn.innerHTML = `<span>⏳ Consulting Gemini AI & Google Search...</span>`;
  }
  if (listEl) {
    listEl.innerHTML = `
      <div style="padding:30px 20px;text-align:center;">
        <div class="loader-spinner" style="margin:0 auto 12px;"></div>
        <p style="font-weight:600;color:var(--text-primary);margin-bottom:4px;">Gemini AI is discovering regional festivals & traditions for ${escapeHtml(region)}...</p>
        <span style="font-size:12px;color:var(--text-secondary);">Identifying cultural demand spikes and scanning live store inventory for matching SKUs</span>
      </div>
    `;
  }

  try {
    await fetchCalendarEvents(region, country, true);
    showToast(`✨ Gemini AI discovered top 3 upcoming festivals & demand surges for ${region}!`);
  } catch (e) {
    showToast(`Error discovering festivals: ${e.message}`);
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = `<span>🔍 AI Festival Discovery</span>`;
    }
  }
}

function onSelectRegionPill(regionName, btn) {
  const customInput = document.getElementById("calendarCustomRegionInput");
  if (customInput) customInput.value = regionName;

  document.querySelectorAll(".cdb-pill").forEach(p => p.classList.remove("active"));
  if (btn) btn.classList.add("active");

  discoverCustomRegionFestivals();
}

function updateRegionalIntelCard(events, region, country) {
  const intelName = document.getElementById("intelRegionName");
  if (intelName) intelName.innerText = region.split("&")[0].trim();

  const factsGrid = document.getElementById("intelFactsGrid");
  if (!factsGrid || !events || events.length === 0) return;

  const topTwo = events.slice(0, 2);
  let html = topTwo.map(ev => `
    <div class="intel-fact-item">
      <span class="fact-icon">${ev.icon || '🪔'}</span>
      <div>
        <strong>${escapeHtml(ev.name)}:</strong>
        <p>Demand for <strong>${escapeHtml(ev.key_items.slice(0, 4).join(", "))}</strong> spikes by <strong>+${Math.round(ev.demand_lift_pct)}%</strong>. ${escapeHtml(ev.description || '')}</p>
      </div>
    </div>
  `).join("");

  html += `
    <div class="intel-fact-item">
      <span class="fact-icon">🛡️</span>
      <div>
        <strong>Offer Conflict Prevention:</strong>
        <p>Running simultaneous discounts on the same SKU causes retailer margin dilution. PromoMind AI flags overlapping dates before promotions go live.</p>
      </div>
    </div>
  `;

  factsGrid.innerHTML = html;
}

function renderFestivalCards(events) {
  const listEl = document.getElementById("festivalCardsList");
  if (!events || events.length === 0) {
    listEl.innerHTML = `<p class="section-desc">No events found for this region. Click AI Festival Discovery above to search.</p>`;
    return;
  }

  const countBadge = document.getElementById("festivalCountBadge");
  if (countBadge) countBadge.innerText = `${events.length} Upcoming Festivals`;

  listEl.innerHTML = events.map(evt => {
    const matched = evt.matched_inventory_items || [];
    const matchedHtml = matched.length > 0 ? `
      <div class="matched-inventory-box">
        <div class="mib-header">
          <span>📦 Live Store SKUs Matching Demand (${matched.length}):</span>
          <span style="color:var(--g-green);font-size:11px;">✓ High Margin & Ready</span>
        </div>
        <div class="mib-chips-grid">
          ${matched.map(m => `
            <div class="mib-chip">
              <span class="mib-chip-title">${escapeHtml(m.name)}</span>
              <span class="mib-chip-stats">Stock: <strong>${m.stock_quantity}</strong> • ₹${Math.round(m.selling_price)} (${m.margin_pct}% margin)</span>
            </div>
          `).join("")}
        </div>
      </div>
    ` : '';

    return `
      <div class="festival-card">
        <div class="fest-top-row">
          <div class="fest-title-block">
            <span class="fest-icon">${evt.icon || '🪔'}</span>
            <div>
              <div class="fest-name">${escapeHtml(evt.name)}</div>
              <div class="fest-dates">${escapeHtml(evt.date_window)} • <strong>${escapeHtml(evt.region)}</strong></div>
            </div>
          </div>
          <span class="surge-badge">🔥 +${Math.round(evt.demand_lift_pct)}% Surge</span>
        </div>

        <p class="fest-desc">${escapeHtml(evt.description)}</p>

        ${evt.tradition_notes ? `<div class="fest-tradition-box">✨ <strong>Cultural Retail Tradition:</strong> ${escapeHtml(evt.tradition_notes)}</div>` : ''}

        ${matchedHtml}

        <!-- Multi-Horizon Planning Deadlines (Advance Procurement, Launch, Clearance) -->
        <div class="fest-horizons-grid">
          ${evt.advance_procurement_window ? `
            <div class="horizon-pill">
              <strong class="hz-procure">📦 T-14d Procurement:</strong>
              <span>${escapeHtml(evt.advance_procurement_window)}</span>
            </div>` : ''}
          ${evt.promo_launch_window ? `
            <div class="horizon-pill">
              <strong class="hz-launch">🚀 T-7d Promo Launch:</strong>
              <span>${escapeHtml(evt.promo_launch_window)}</span>
            </div>` : ''}
          ${evt.clearance_window ? `
            <div class="horizon-pill">
              <strong class="hz-clear">🧹 T+2d Clearance:</strong>
              <span>${escapeHtml(evt.clearance_window)}</span>
            </div>` : ''}
        </div>

        <div class="key-skus-row">
          ${(evt.key_items || []).map(item => `<span class="sku-pill">🏷️ ${escapeHtml(item)}</span>`).join("")}
        </div>

        <div class="fest-launch-row">
          <button class="btn btn-primary fest-promo-launch-btn" onclick="launchPromoForFestival('${escapeHtml(evt.name)}', '${escapeHtml(evt.suggested_combo_title || '')}', '${escapeHtml(evt.recommended_promo_type || '')}')">
            <span>⚡</span> Generate AI Promo Offer for ${escapeHtml(evt.name.split('(')[0].trim())}
          </button>
        </div>
      </div>
    `;
  }).join("");
}

function launchPromoForFestival(festivalName, comboTitle, recommendedType) {
  switchScreen("promos");
  showToast(`⚡ Loading AI Copilot promotion for ${festivalName}...`);
  
  const prompt = comboTitle 
    ? `Create a festival promotional bundle for ${festivalName} (${comboTitle})`
    : `Create an optimal festival promotional bundle for ${festivalName}`;
    
  setTimeout(() => {
    sendMainChatMessage(prompt);
  }, 250);
}

async function fetchActiveOffers() {
  try {
    const res = await fetch("/api/offers/active");
    if (!res.ok) throw new Error("Failed to load active offers");
    activeOffers = await res.json();
    renderScheduledOffers(activeOffers);
  } catch (err) {
    console.error("Error fetching active offers:", err);
  }
}

function renderScheduledOffers(offers) {
  const listEl = document.getElementById("scheduledOffersList");
  document.getElementById("activeOffersCountBadge").innerText = `${offers.length} Active`;

  if (!offers || offers.length === 0) {
    listEl.innerHTML = `<p class="section-desc">No active scheduled promotions currently running.</p>`;
    return;
  }

  listEl.innerHTML = offers.map(off => `
    <div class="offer-card">
      <div class="offer-info-block">
        <div class="offer-title">${off.title}</div>
        <div class="offer-dates">📅 Active: ${off.start_date} to ${off.end_date} • <strong>${off.discount_pct}% OFF (₹${off.combo_price})</strong></div>
        <div class="offer-skus">SKUs: ${off.anchor_id} + ${off.attached_id}</div>
      </div>
      <div>
        <span class="offer-badge-active">${off.status}</span>
      </div>
    </div>
  `).join("");
}

function populateSandboxSKUDropdown(items) {
  const select = document.getElementById("conflictTestSKU");
  if (!select) return;
  select.innerHTML = `<option value="">-- Select SKU to Test --</option>` +
    items.map(p => `<option value="${p.id}">${p.name} (${p.id})</option>`).join("");
}

async function runSandboxConflictCheck() {
  const sku = document.getElementById("conflictTestSKU").value;
  const disc = parseFloat(document.getElementById("conflictTestDiscount").value) || 20;
  const resBox = document.getElementById("sandboxResultBox");

  if (!sku) {
    showToast("Please choose a SKU to test.");
    return;
  }

  resBox.classList.remove("hidden");
  resBox.className = "sandbox-result";
  resBox.innerHTML = `<span>⏳ Simulating offer collision engine...</span>`;

  try {
    const res = await fetch("/api/offers/check-conflict", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        anchor_id: sku,
        attached_id: "NONE",
        proposed_discount_pct: disc
      })
    });
    const data = await res.json();

    if (data.has_conflict) {
      resBox.className = "sandbox-result result-conflict";
      resBox.innerHTML = `
        <strong>⚠️ OFFER CONFLICT DETECTED!</strong>
        <p>${data.conflict_reason}</p>
        <p style="margin-top:6px;"><strong>Recommended Strategy:</strong> ${data.recommended_action}</p>
      `;
    } else {
      resBox.className = "sandbox-result result-safe";
      resBox.innerHTML = `
        <strong>✅ NO OVERLAPPING CONFLICTS!</strong>
        <p>${data.recommended_action}</p>
        <p style="margin-top:4px;">SKU <code>${sku}</code> is clear to schedule at ${disc}% discount without cannibalizing existing offers.</p>
      `;
    }
  } catch (err) {
    resBox.className = "sandbox-result";
    resBox.innerText = "Error testing conflict.";
  }
}

// ==============================================================================
// Screen 4: CSV Data Import & AI Knowledge Base Sync
// ==============================================================================

function setupDragAndDrop() {
  const dropZone = document.getElementById("dropZone");
  if (!dropZone) return;

  ['dragenter', 'dragover'].forEach(eventName => {
    dropZone.addEventListener(eventName, (e) => {
      e.preventDefault();
      dropZone.classList.add("dragover");
    }, false);
  });

  ['dragleave', 'drop'].forEach(eventName => {
    dropZone.addEventListener(eventName, (e) => {
      e.preventDefault();
      dropZone.classList.remove("dragover");
    }, false);
  });

  dropZone.addEventListener('drop', (e) => {
    const dt = e.dataTransfer;
    const files = dt.files;
    if (files.length) handleFileSelected(files);
  }, false);
}

function handleFileSelected(files) {
  if (!files || files.length === 0) return;
  uploadedFileObject = files[0];
  document.getElementById("selectedFileName").innerText = uploadedFileObject.name;
  document.getElementById("selectedFileStatus").classList.remove("hidden");
}

async function submitUploadedCSV() {
  if (!uploadedFileObject) {
    showToast("No CSV file selected.");
    return;
  }

  const formData = new FormData();
  formData.append("file", uploadedFileObject);

  showToast("Processing CSV and running Holt-Winters demand engine...");

  try {
    const res = await fetch("/api/upload-csv", {
      method: "POST",
      body: formData
    });
    if (!res.ok) throw new Error("CSV processing failed");
    const data = await res.json();

    document.getElementById("importLogBox").classList.remove("hidden");
    document.getElementById("importLogTitle").innerText = "Import Succeeded";
    document.getElementById("importLogMsg").innerText = data.message;

    // Refresh inventory and markdown
    fetchInventory();
    fetchKnowledgeMarkdown();
    showToast(`Successfully imported ${data.imported_count} SKUs!`);
  } catch (err) {
    console.error("Error uploading CSV:", err);
    showToast("Failed to process CSV file.");
  }
}

function toggleRawCSVAccordion() {
  const body = document.getElementById("accBody");
  const arrow = document.getElementById("accArrow");
  const isHidden = body.classList.contains("hidden");
  body.classList.toggle("hidden", !isHidden);
  arrow.innerText = isHidden ? "▴" : "▾";
}

async function submitRawCSV() {
  const text = document.getElementById("rawCsvText").value.trim();
  if (!text) {
    showToast("Please enter CSV text.");
    return;
  }

  const formData = new FormData();
  formData.append("raw_csv", text);

  try {
    const res = await fetch("/api/upload-csv", {
      method: "POST",
      body: formData
    });
    if (!res.ok) throw new Error("Failed to parse raw CSV");
    const data = await res.json();

    document.getElementById("importLogBox").classList.remove("hidden");
    document.getElementById("importLogTitle").innerText = "Raw CSV Synced";
    document.getElementById("importLogMsg").innerText = data.message;

    fetchInventory();
    fetchKnowledgeMarkdown();
    showToast(`Parsed ${data.imported_count} SKUs into persistent inventory!`);
  } catch (err) {
    showToast("Error parsing raw CSV data.");
  }
}

async function fetchKnowledgeMarkdown() {
  try {
    const res = await fetch("/api/knowledge-md");
    if (!res.ok) throw new Error("Failed to load knowledge markdown");
    const data = await res.json();
    document.getElementById("knowledgeMdContent").innerText = data.markdown;
  } catch (err) {
    console.error("Error loading knowledge markdown:", err);
  }
}

function syncKnowledgeMarkdown() {
  fetchKnowledgeMarkdown();
  showToast("Synchronized AI Knowledge Base (.md)!");
}

function downloadSampleCSV() {
  const sampleCSV = `product_id,name,category,brand,stock_quantity,cost_price,selling_price,past_sales_weeks
SKU_SAMPLE_01,Organic Pure Desi Ghee (1L),Dairy,Local Dairy,60,480.0,620.0,18,20,24,28,32,38
SKU_SAMPLE_02,Roasted Salted Pistachios (250g),Dry Fruits,Royal Harvest,45,210.0,295.0,12,14,15,16,18,22
SKU_SAMPLE_03,Artisanal Terracotta Deepas (Pack of 12),Puja & Festive,Mitti Art,150,45.0,90.0,2,3,4,8,25,85
SKU_SAMPLE_04,Premium Darjeeling First Flush Tea (500g),Beverages,Himalayan Leaf,80,310.0,420.0,30,32,34,35,36,40`;

  const blob = new Blob([sampleCSV], { type: "text/csv" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "promomind_sample_inventory.csv";
  a.click();
  URL.revokeObjectURL(url);
}

function downloadMarkdownFile() {
  const content = document.getElementById("knowledgeMdContent").innerText;
  const blob = new Blob([content], { type: "text/markdown" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "store_knowledge.md";
  a.click();
  URL.revokeObjectURL(url);
}

// ==============================================================================
// Add SKU Modal
// ==============================================================================

function openAddProductModal() {
  document.getElementById("addProductModal").classList.remove("hidden");
}

function closeAddProductModal() {
  document.getElementById("addProductModal").classList.add("hidden");
}

function closeAddProductModalOnBackdrop(e) {
  if (e.target.id === "addProductModal") closeAddProductModal();
}

async function submitNewProduct(e) {
  e.preventDefault();
  const name = document.getElementById("newProdName").value.trim();
  const category = document.getElementById("newProdCategory").value;
  const stock = parseInt(document.getElementById("newProdStock").value) || 50;
  const cost = parseFloat(document.getElementById("newProdCost").value) || 100;
  const mrp = parseFloat(document.getElementById("newProdMRP").value) || 140;
  const weekly = parseInt(document.getElementById("newProdWeeklySales").value) || 20;

  try {
    const res = await fetch("/api/products", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: name,
        category: category,
        cost_price: cost,
        selling_price: mrp,
        stock_quantity: stock,
        weekly_sales_avg: weekly
      })
    });

    if (!res.ok) throw new Error("Failed to add SKU");
    closeAddProductModal();
    document.getElementById("addProductForm").reset();
    showToast(`Added ${name}! Holt-Winters demand models generated.`);
    fetchInventory();
  } catch (err) {
    showToast(`Error adding product: ${err.message}`);
  }
}

// ==============================================================================
// Utility: Toast Notification
// ==============================================================================

function showToast(msg) {
  const container = document.getElementById("toastContainer");
  const toast = document.createElement("div");
  toast.className = "toast";
  toast.innerHTML = `<span>ℹ️</span> <span>${msg}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateX(20px)";
    setTimeout(() => toast.remove(), 250);
  }, 3500);
}

// ==============================================================================
// AI Retail Sales Copilot (Conversational Advisor & Autonomous Sales Engine)
// ==============================================================================

let copilotMarginTarget = 18.0;
let lastCopilotPlan = null;
let lastCopilotIdeas = [];

function openRetailCopilot(initialQuery) {
  switchScreen('promos');
  const input = document.getElementById("mainCopilotInput");
  if (input) {
    if (initialQuery) {
      input.value = initialQuery;
      sendMainChatMessage();
    } else {
      setTimeout(() => {
        input.focus();
        input.scrollIntoView({ behavior: "smooth", block: "center" });
      }, 150);
    }
  }
}

// Seamless alias so any button triggers the direct unified copilot
function toggleCopilotDrawer(initialQuery) {
  openRetailCopilot(initialQuery);
}

function closeCopilotDrawer() {
  const drawer = document.getElementById("copilotDrawer");
  const backdrop = document.getElementById("copilotBackdrop");
  if (drawer) drawer.classList.add("hidden");
  if (backdrop) backdrop.classList.add("hidden");
}

function onChatMarginChanged(val) {
  copilotMarginTarget = parseFloat(val) || 18.0;
  showToast(`Copilot margin protection set to ${copilotMarginTarget}%`);
}

function sendQuickChatMessage(promptText) {
  openRetailCopilot(promptText);
}

async function sendCopilotChatMessage() {
  const input = document.getElementById("copilotInputText");
  const thread = document.getElementById("copilotThread");
  if (!input || !thread) return;

  const userText = input.value.trim();
  if (!userText) return;

  // Clear input
  input.value = "";

  // Append user message
  const userMsgEl = document.createElement("div");
  userMsgEl.className = "chat-msg user";
  userMsgEl.innerHTML = `
    <div class="chat-bubble">${escapeHtml(userText)}</div>
    <span class="chat-time">${formatChatTime()}</span>
  `;
  thread.appendChild(userMsgEl);

  // Append temporary thinking bot message
  const botThinkingId = "bot-thinking-" + Date.now();
  const botThinkingEl = document.createElement("div");
  botThinkingEl.className = "chat-msg bot";
  botThinkingEl.id = botThinkingId;
  botThinkingEl.innerHTML = `
    <div class="chat-bubble" style="display:flex;align-items:center;gap:8px;">
      <div class="loader-spinner" style="width:14px;height:14px;margin:0;"></div>
      <span>Consulting retail knowledge base & executing margin optimization...</span>
    </div>
  `;
  thread.appendChild(botThinkingEl);
  thread.scrollTop = thread.scrollHeight;

  // Get current store region & margin
  const region = (document.getElementById("profStateRegion") && document.getElementById("profStateRegion").value) || "Karnataka & South India";
  const marginSelect = document.getElementById("chatMarginSelect");
  if (marginSelect) copilotMarginTarget = parseFloat(marginSelect.value) || 18.0;

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: userText,
        min_margin_pct: copilotMarginTarget,
        region: region
      })
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Error from Copilot server");
    }

    const data = await res.json();
    
    // Build bot response markup
    let bubbleContent = formatBotReply(data.reply);

    // If an offer plan was generated
    if (data.plan) {
      lastCopilotPlan = data.plan;
      const p = data.plan;
      const anchorName = p.anchor_product ? p.anchor_product.name.split('(')[0].trim() : "Anchor Item";
      const attachedName = p.attached_product ? p.attached_product.name.split('(')[0].trim() : "Attached Item";
      const comboPrice = Math.round(p.recommended_combo_price || p.combo_price || 0);
      const originalMrp = Math.round(p.original_combined_mrp || p.original_total_mrp || ((p.anchor_product?.selling_price || 0) + (p.attached_product?.selling_price || 0)) || comboPrice);
      const savings = Math.round(p.discount_amount || Math.max(0, originalMrp - comboPrice));
      const margin = p.net_margin_pct || 18.0;
      const lift = p.roi_prediction ? p.roi_prediction.units_lift_pct : (p.projected_volume_lift_pct || 25);

      bubbleContent += `
        <div class="chat-offer-card">
          <div class="coc-badge-row">
            <span class="coc-badge">⚡ READY BUNDLE</span>
            <span class="coc-margin-tag">✓ ${margin}% Net Margin</span>
          </div>
          <h4 class="coc-title">${p.title || 'Dynamic Combo Bundle'}</h4>
          <div class="coc-pair">📦 <strong>${anchorName}</strong> + <strong>${attachedName}</strong></div>
          <div class="coc-pricing">
            <span class="coc-price">₹${comboPrice}</span>
            <span class="coc-mrp">₹${originalMrp}</span>
            <span class="coc-savings">Save ₹${savings} (${p.discount_pct || 10}% OFF)</span>
          </div>
          <div style="font-size:11px;color:var(--text-secondary);margin-bottom:10px;">
            Lift: <strong>+${lift}%</strong> • Working Capital recovered in <strong>${p.capital_turnover_days || 4} days</strong>
          </div>
          <button type="button" class="coc-action-btn" onclick="applyPlanFromCopilot()">
            <span>⚡</span> Load into Screen 2 & Launch Campaign
          </button>
        </div>
      `;
    }

    // If weekly ideas are returned
    if (data.ideas && data.ideas.length > 0) {
      lastCopilotIdeas = data.ideas;
      bubbleContent += `
        <div style="margin-top:12px;display:flex;flex-direction:column;gap:10px;">
          ${data.ideas.map((idea, i) => `
            <div class="chat-offer-card" style="margin-top:0;">
              <div class="coc-badge-row">
                <span class="coc-badge">${idea.badge || 'RECOMMENDED'}</span>
                <span class="coc-margin-tag">✓ ${idea.net_margin_pct}% Margin</span>
              </div>
              <h5 class="coc-title" style="font-size:13px;margin-bottom:4px;">${idea.title}</h5>
              <div class="coc-pair">📦 <strong>${idea.anchor_name}</strong> + <strong>${idea.attached_name}</strong></div>
              <div class="coc-pricing">
                <span class="coc-price" style="font-size:16px;">₹${Math.round(idea.combo_price)}</span>
                <span class="coc-mrp" style="font-size:12px;text-decoration:line-through;">₹${Math.round(idea.original_mrp)}</span>
                <span class="coc-savings">Save ₹${Math.round(idea.savings_amount)} (${idea.discount_pct}% OFF)</span>
              </div>
              <div style="font-size:11px;color:var(--text-secondary);margin-bottom:8px;">
                💡 ${idea.why_recommended}
              </div>
              <button type="button" class="coc-action-btn" onclick="applyWeeklyIdeaFromCopilot(${i})">
                <span>⚡</span> Load this Offer into Screen 2
              </button>
            </div>
          `).join("")}
        </div>
      `;
    }

    // Replace thinking bubble with real response
    const thinkingEl = document.getElementById(botThinkingId);
    if (thinkingEl) {
      thinkingEl.innerHTML = `
        <div class="chat-bubble">${bubbleContent}</div>
        <span class="chat-time">${formatChatTime()}</span>
      `;
    }
  } catch (err) {
    console.error("Copilot error:", err);
    const thinkingEl = document.getElementById(botThinkingId);
    if (thinkingEl) {
      thinkingEl.innerHTML = `
        <div class="chat-bubble" style="color:var(--g-red);">
          ⚠️ Error communicating with Copilot: ${err.message}. Please verify the server is running.
        </div>
        <span class="chat-time">${formatChatTime()}</span>
      `;
    }
  }

  thread.scrollTop = thread.scrollHeight;
}

function applyPlanFromCopilot() {
  if (!lastCopilotPlan) return;
  closeCopilotDrawer();
  switchScreen("promos");
  currentPlan = lastCopilotPlan;
  renderGeneratedPlan(lastCopilotPlan);
  showToast("Loaded AI & Mathematical bundle into Campaign Engine!");

  const target = document.getElementById("promoResultsArea");
  if (target) {
    target.classList.remove("hidden");
    target.scrollIntoView({ behavior: "smooth" });
  }
}

async function applyWeeklyIdeaFromCopilot(idx) {
  if (!lastCopilotIdeas || !lastCopilotIdeas[idx]) return;
  const idea = lastCopilotIdeas[idx];
  closeCopilotDrawer();
  switchScreen("promos");
  
  // Set anchor in dropdown
  const anchorSelect = document.getElementById("promoAnchorSelect");
  if (anchorSelect) {
    anchorSelect.value = idea.anchor_id;
    onAnchorProductSelected(idea.anchor_id);
  }
  
  setTimeout(async () => {
    const attachedSelect = document.getElementById("promoAttachedSelect");
    if (attachedSelect) {
      attachedSelect.value = idea.attached_id;
      onAttachedProductSelected(idea.attached_id);
    }
    const promptInput = document.getElementById("promoCustomPrompt");
    if (promptInput) promptInput.value = `${idea.title}: ${idea.why_recommended}`;
    
    // Auto trigger generation
    await generatePromotionalPlan();
  }, 100);
}

function escapeHtml(str) {
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

function formatBotReply(text) {
  if (!text) return "";
  let formatted = escapeHtml(text);
  formatted = formatted.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
  formatted = formatted.replace(/\*(.*?)\*/g, "<em>$1</em>");
  formatted = formatted.replace(/\n\n/g, "<br><br>");
  formatted = formatted.replace(/\n/g, "<br>");
  return formatted;
}

function formatChatTime() {
  const d = new Date();
  let hours = d.getHours();
  const minutes = d.getMinutes().toString().padStart(2, "0");
  const ampm = hours >= 12 ? "PM" : "AM";
  hours = hours % 12;
  hours = hours ? hours : 12;
  return `${hours}:${minutes} ${ampm}`;
}

// ==============================================================================
// Screen 2: Dedicated AI Retail Copilot & Sales Advisor Chatbot
// ==============================================================================

window.lastActivePlan = null;
window.lastActiveIdeas = [];

async function sendMainChatMessage(prefilledText) {
  const input = document.getElementById("mainCopilotInput");
  const thread = document.getElementById("mainCopilotThread");
  if (!thread) return;

  if (prefilledText) {
    if (input) input.value = prefilledText;
  }

  const userText = input ? input.value.trim() : "";
  if (!userText) return;

  // Clear input
  if (input) input.value = "";

  // Append user message bubble
  const userMsgEl = document.createElement("div");
  userMsgEl.className = "chat-msg user";
  userMsgEl.innerHTML = `
    <div class="chat-bubble">${escapeHtml(userText)}</div>
    <span class="chat-time">${formatChatTime()}</span>
  `;
  thread.appendChild(userMsgEl);

  // Append temporary thinking bot message
  const botThinkingId = "main-bot-thinking-" + Date.now();
  const botThinkingEl = document.createElement("div");
  botThinkingEl.className = "chat-msg bot";
  botThinkingEl.id = botThinkingId;
  botThinkingEl.innerHTML = `
    <div class="chat-bubble" style="display:flex;align-items:center;gap:8px;">
      <div class="loader-spinner" style="width:14px;height:14px;margin:0;"></div>
      <span>Analyzing store sales & computing optimal margins...</span>
    </div>
  `;
  thread.appendChild(botThinkingEl);
  thread.scrollTop = thread.scrollHeight;

  // Get current store region
  const region = (document.getElementById("profStateRegion") && document.getElementById("profStateRegion").value) || "Karnataka & South India";

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: userText,
        region: region
      })
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Error from Copilot server");
    }

    const data = await res.json();

    // Format bot reply
    let bubbleContent = formatBotReply(data.reply);

    // If an offer plan was generated (e.g. failing product rescue or weekly deal)
    if (data.plan) {
      window.lastActivePlan = data.plan;
      const p = data.plan;
      const anchorName = p.anchor_product ? p.anchor_product.name.split('(')[0].trim() : "Anchor Item";
      const attachedName = p.attached_product ? p.attached_product.name.split('(')[0].trim() : "Attached Item";
      const comboPrice = Math.round(p.recommended_combo_price || p.combo_price || 0);
      const originalMrp = Math.round(p.original_combined_mrp || p.original_total_mrp || ((p.anchor_product?.selling_price || 0) + (p.attached_product?.selling_price || 0)) || comboPrice);
      const savings = Math.round(p.discount_amount || Math.max(0, originalMrp - comboPrice));
      const margin = p.net_margin_pct || 18.0;
      const lift = p.roi_prediction ? p.roi_prediction.units_lift_pct : (p.projected_volume_lift_pct || 25);

      bubbleContent += `
        <div class="chat-offer-card">
          <div class="coc-badge-row">
            <span class="coc-badge">⚡ READY BUNDLE</span>
            <span class="coc-margin-tag">✓ ${margin}% Net Margin</span>
          </div>
          <h4 class="coc-title">${escapeHtml(p.title || 'Dynamic Combo Bundle')}</h4>
          <div class="coc-pair">📦 <strong>${escapeHtml(anchorName)}</strong> + <strong>${escapeHtml(attachedName)}</strong></div>
          <div class="coc-pricing">
            <span class="coc-price">₹${comboPrice}</span>
            <span class="coc-mrp">₹${originalMrp}</span>
            <span class="coc-savings">Save ₹${savings} (${p.discount_pct || 10}% OFF)</span>
          </div>
          <div style="font-size:11px;color:var(--text-secondary);margin-bottom:10px;">
            Lift: <strong>+${lift}%</strong> • Working Capital recovered in <strong>${p.capital_turnover_days || 4} days</strong>
          </div>
          <button type="button" class="coc-action-btn" onclick="loadPlanIntoStudioDirect()">
            <span>⚡</span> View WhatsApp Broadcast, Poster & Cashier Script
          </button>
        </div>
      `;

      // Auto load into right-hand Collateral Studio
      renderGeneratedPlan(p);
    }

    // If weekly ideas are returned
    if (data.ideas && data.ideas.length > 0) {
      window.lastActiveIdeas = data.ideas;
      bubbleContent += `
        <div style="margin-top:12px;display:flex;flex-direction:column;gap:10px;">
          ${data.ideas.map((idea, i) => `
            <div class="chat-offer-card" style="margin-top:0;">
              <div class="coc-badge-row">
                <span class="coc-badge">${escapeHtml(idea.badge || 'RECOMMENDED')}</span>
                <span class="coc-margin-tag">✓ ${idea.net_margin_pct}% Margin</span>
              </div>
              <h5 class="coc-title" style="font-size:13px;margin-bottom:4px;">${escapeHtml(idea.title)}</h5>
              <div class="coc-pair">📦 <strong>${escapeHtml(idea.anchor_name)}</strong> + <strong>${escapeHtml(idea.attached_name)}</strong></div>
              <div class="coc-pricing">
                <span class="coc-price" style="font-size:16px;">₹${Math.round(idea.combo_price)}</span>
                <span class="coc-mrp" style="font-size:12px;text-decoration:line-through;">₹${Math.round(idea.original_mrp)}</span>
                <span class="coc-savings">Save ₹${Math.round(idea.savings_amount)} (${idea.discount_pct}% OFF)</span>
              </div>
              <div style="font-size:11px;color:var(--text-secondary);margin-bottom:8px;">
                💡 ${escapeHtml(idea.why_recommended)}
              </div>
              <button type="button" class="coc-action-btn" onclick="selectWeeklyIdeaForStudio(${i})">
                <span>⚡</span> Load this Offer into Collateral Studio
              </button>
            </div>
          `).join("")}
        </div>
      `;
    }

    // Replace thinking bubble with real response
    const thinkingEl = document.getElementById(botThinkingId);
    if (thinkingEl) {
      thinkingEl.innerHTML = `
        <div class="chat-bubble">${bubbleContent}</div>
        <span class="chat-time">${formatChatTime()}</span>
      `;
    }
  } catch (err) {
    console.error("Main Copilot error:", err);
    const thinkingEl = document.getElementById(botThinkingId);
    if (thinkingEl) {
      thinkingEl.innerHTML = `
        <div class="chat-bubble" style="color:var(--g-red);">
          ⚠️ Error communicating with Copilot: ${escapeHtml(err.message)}. Please verify the server is running.
        </div>
        <span class="chat-time">${formatChatTime()}</span>
      `;
    }
  }

  thread.scrollTop = thread.scrollHeight;
}

function loadPlanIntoStudioDirect() {
  if (!window.lastActivePlan) return;
  renderGeneratedPlan(window.lastActivePlan);
  showToast("Offer loaded into Campaign Collateral Studio!");
  const studioCard = document.getElementById("promoOutputCard");
  if (studioCard) studioCard.scrollIntoView({ behavior: "smooth" });
}

async function selectWeeklyIdeaForStudio(idx) {
  if (!window.lastActiveIdeas || !window.lastActiveIdeas[idx]) return;
  const idea = window.lastActiveIdeas[idx];
  showToast(`Generating collateral for: ${idea.title}...`);

  try {
    const res = await fetch("/api/generate-combo", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        prompt: idea.title + ": " + idea.why_recommended,
        min_margin_pct: idea.net_margin_pct || 16.0,
        event_theme: idea.event_theme || "Weekly Retail Deal",
        primary_product_id: idea.anchor_id,
        secondary_product_id: idea.attached_id,
        region: (document.getElementById("profStateRegion") && document.getElementById("profStateRegion").value) || "Karnataka & South India",
        archetype: idea.archetype || "ANCHOR_MARGIN_BOOSTER"
      })
    });

    if (res.ok) {
      const plan = await res.json();
      window.lastActivePlan = plan;
      renderGeneratedPlan(plan);
      showToast(`Ready! WhatsApp, poster & script loaded for ${idea.title}`);
      const studioCard = document.getElementById("promoOutputCard");
      if (studioCard) studioCard.scrollIntoView({ behavior: "smooth" });
    } else {
      throw new Error("Failed to generate complete collateral");
    }
  } catch (err) {
    console.error("Error generating weekly idea plan:", err);
    showToast(`Error loading offer: ${err.message}`);
  }
}

function clearMainChatHistory() {
  const thread = document.getElementById("mainCopilotThread");
  if (!thread) return;
  thread.innerHTML = `
    <div class="chat-msg bot">
      <div class="chat-bubble">
        Namaskara / Namaste! 👋 I am your AI Retail Sales Copilot.<br><br>
        <strong>No complicated forms or marketing jargon here!</strong> Think of me as your personal retail growth advisor. Just ask me naturally:
        <div class="chat-examples" style="margin-top:8px;">
          <em>• "Which product is failing or stuck on my shelves?"</em><br>
          <em>• "Suggest 3 best offers for this week"</em><br>
          <em>• "How can I increase this weekend's sales?"</em><br>
          <em>• "Create a Diwali sweet & dry fruit gift pack"</em>
        </div>
      </div>
      <span class="chat-time">Just now</span>
    </div>
  `;
  showToast("Chat history reset");
}
