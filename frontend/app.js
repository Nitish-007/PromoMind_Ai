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
});

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

function loadStoreProfile() {
  const savedTheme = localStorage.getItem("promomind_theme") || "light";
  setThemeMode(savedTheme);

  const savedStoreName = localStorage.getItem("promomind_store_name") || "Sharma Supermarket & Kirana";
  const savedOwner = localStorage.getItem("promomind_owner_name") || "Ramesh Sharma";
  const savedRegion = localStorage.getItem("promomind_region") || "Karnataka & South India";
  const savedCity = localStorage.getItem("promomind_city") || "Bengaluru";
  const savedPin = localStorage.getItem("promomind_pin") || "560034";
  const savedPhone = localStorage.getItem("promomind_phone") || "+91 98450 12345";
  const savedAudience = localStorage.getItem("promomind_audience") || "1420";

  // Apply to Header and Profile Screen
  document.getElementById("topStoreName").innerText = savedStoreName;
  document.getElementById("topStoreLocation").innerText = `${savedCity} • ${savedRegion.split("&")[0].trim()}`;
  document.getElementById("intelRegionName").innerText = savedRegion;

  // Set Profile fields
  const elStoreName = document.getElementById("profStoreName");
  if (elStoreName) elStoreName.value = savedStoreName;
  const elOwner = document.getElementById("profOwnerName");
  if (elOwner) elOwner.value = savedOwner;
  const elRegion = document.getElementById("profStateRegion");
  if (elRegion) elRegion.value = savedRegion;
  const elCity = document.getElementById("profCity");
  if (elCity) elCity.value = savedCity;
  const elPin = document.getElementById("profPin");
  if (elPin) elPin.value = savedPin;
  const elPhone = document.getElementById("profPhone");
  if (elPhone) elPhone.value = savedPhone;
  const elAudience = document.getElementById("profAudienceSize");
  if (elAudience) elAudience.value = savedAudience;

  // Sync calendar region select
  const calRegion = document.getElementById("calendarRegionSelect");
  if (calRegion) calRegion.value = savedRegion;
}

function saveStoreProfile() {
  const storeName = document.getElementById("profStoreName").value.trim() || "Sharma Supermarket";
  const owner = document.getElementById("profOwnerName").value.trim();
  const region = document.getElementById("profStateRegion").value;
  const city = document.getElementById("profCity").value.trim();
  const pin = document.getElementById("profPin").value.trim();
  const phone = document.getElementById("profPhone").value.trim();
  const audience = document.getElementById("profAudienceSize").value.trim();

  localStorage.setItem("promomind_store_name", storeName);
  localStorage.setItem("promomind_owner_name", owner);
  localStorage.setItem("promomind_region", region);
  localStorage.setItem("promomind_city", city);
  localStorage.setItem("promomind_pin", pin);
  localStorage.setItem("promomind_phone", phone);
  localStorage.setItem("promomind_audience", audience);

  // Update header and calendar
  document.getElementById("topStoreName").innerText = storeName;
  document.getElementById("topStoreLocation").innerText = `${city} • ${region.split("&")[0].trim()}`;
  document.getElementById("intelRegionName").innerText = region;
  document.getElementById("calendarRegionSelect").value = region;

  showToast("Store profile & regional preferences saved successfully!");
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
  } catch (err) {
    console.error("Error fetching inventory:", err);
    document.getElementById("inventoryTableBody").innerHTML = `
      <tr><td colspan="8" class="loading-td" style="color:var(--g-red);">⚠️ Failed to connect to inventory service. Retrying...</td></tr>
    `;
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
    eventSelect.value = "Super Weekend Kirana Rush";
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

async function generatePromotionPlan() {
  const prompt = document.getElementById("promoPromptInput").value.trim() || "Create an optimal festive combo";
  const margin = parseFloat(document.getElementById("promoMarginSlider").value) || 18.0;
  const eventTheme = document.getElementById("promoEventSelect").value;
  const offerType = document.getElementById("promoOfferType").value;
  const anchorId = document.getElementById("promoAnchorSelect").value;
  const attachedId = document.getElementById("promoAttachedSelect").value;

  const btn = document.getElementById("generatePlanBtn");
  btn.disabled = true;
  btn.innerHTML = `<span>⏳ Synthesizing Demand Models & Collateral...</span>`;

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
        secondary_product_id: attachedId || null
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

function renderGeneratedPlan(plan) {
  document.getElementById("emptyPromoPlaceholder").classList.add("hidden");
  const resultCard = document.getElementById("planResultContainer");
  resultCard.classList.remove("hidden");

  // Plan header
  document.getElementById("planThemeTag").innerText = plan.event_theme || "Festive Offer";
  document.getElementById("planTitle").innerText = plan.combo_name || "Special Kirana Bundle";
  document.getElementById("planMarginBadge").innerText = `${plan.net_margin_pct}% Net Margin`;

  // Pricing numbers
  document.getElementById("planOriginalPrice").innerText = `₹${plan.original_total_mrp}`;
  document.getElementById("planOfferPrice").innerText = `₹${plan.bundle_selling_price}`;
  document.getElementById("planSavings").innerText = `₹${plan.savings_amount} (${plan.discount_pct}% OFF)`;
  document.getElementById("planTotalCost").innerText = `₹${plan.combined_cost}`;

  // AI Rationale
  document.getElementById("planRationaleText").innerText = plan.ai_pitch || plan.ai_explanation;

  // WhatsApp text
  const waText = plan.whatsapp_copy || `🎉 Exclusive Festive Deal! Get ${plan.combo_name} for just ₹${plan.bundle_selling_price} (MRP ₹${plan.original_total_mrp}) at ${document.getElementById('topStoreName').innerText}! Limited stock.`;
  document.getElementById("waMessageText").innerText = waText;
  document.getElementById("waStoreNamePreview").innerText = document.getElementById("topStoreName").innerText;

  // WhatsApp direct link
  const encodedText = encodeURIComponent(waText);
  document.getElementById("openWhatsAppLink").href = `https://api.whatsapp.com/send?text=${encodedText}`;

  // Poster card
  document.getElementById("posterEventBadge").innerText = (plan.event_theme || "DIWALI SPECIAL").toUpperCase();
  document.getElementById("posterComboTitle").innerText = plan.combo_name.toUpperCase();
  const itemNames = (plan.items || []).map(i => i.name).join(" + ") || "Festive Products Duo";
  document.getElementById("posterBundleItems").innerText = itemNames;
  document.getElementById("posterMRP").innerText = `MRP ₹${plan.original_total_mrp}`;
  document.getElementById("posterDealPrice").innerText = `₹${plan.bundle_selling_price}`;
  document.getElementById("posterSavings").innerText = `YOU SAVE ₹${plan.savings_amount} (${plan.discount_pct}% OFF)`;
  document.getElementById("posterStoreLoc").innerText = `${document.getElementById('topStoreName').innerText}, ${document.getElementById('topStoreLocation').innerText}`;
}

function switchCollateralTab(tabName, btn) {
  document.querySelectorAll(".collateral-tab-nav .c-tab-btn").forEach(el => el.classList.remove("active"));
  document.querySelectorAll(".collateral-tabs-container .c-tab-panel").forEach(el => el.classList.remove("active"));
  btn.classList.add("active");

  if (tabName === "whatsapp") {
    document.getElementById("cTabWhatsapp").classList.add("active");
  } else {
    document.getElementById("cTabPoster").classList.add("active");
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

  try {
    const res = await fetch("/api/publish-offer", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        combo_id: currentPlan.combo_id || "COMBO_LIVE",
        title: currentPlan.combo_name,
        anchor_id: currentPlan.items ? currentPlan.items[0].id : "PROD_TEA_01",
        attached_id: currentPlan.items && currentPlan.items[1] ? currentPlan.items[1].id : "PROD_BISCUIT_01",
        discount_pct: currentPlan.discount_pct,
        price: currentPlan.bundle_selling_price,
        event_theme: currentPlan.event_theme
      })
    });
    if (!res.ok) throw new Error("Failed to activate offer");
    showToast("Offer scheduled and dispatched across POS terminals & WhatsApp!");
    switchScreen("calendar");
  } catch (err) {
    console.error("Error activating offer:", err);
    showToast("Error activating offer.");
  }
}

// ==============================================================================
// Screen 3: Regional Festival Calendar & Conflict Management
// ==============================================================================

async function fetchCalendarEvents() {
  try {
    const res = await fetch("/api/calendar/events");
    if (!res.ok) throw new Error("Failed to load calendar events");
    regionalEvents = await res.json();
    renderFestivalCards(regionalEvents);
  } catch (err) {
    console.error("Error fetching calendar:", err);
  }
}

function renderFestivalCards(events) {
  const listEl = document.getElementById("festivalCardsList");
  if (!events || events.length === 0) {
    listEl.innerHTML = `<p class="section-desc">No events found for this region.</p>`;
    return;
  }

  document.getElementById("festivalCountBadge").innerText = `${events.length} Events`;

  listEl.innerHTML = events.map(evt => `
    <div class="festival-card">
      <div class="fest-top-row">
        <div class="fest-title-block">
          <span class="fest-icon">${evt.icon || '🪔'}</span>
          <div>
            <div class="fest-name">${evt.name}</div>
            <div class="fest-dates">${evt.date_window} • <strong>${evt.region}</strong></div>
          </div>
        </div>
        <span class="surge-badge">+${evt.demand_lift_pct}% Surge</span>
      </div>

      <p class="fest-desc">${evt.description}</p>

      <div class="key-skus-row">
        ${(evt.key_items || []).map(item => `<span class="sku-pill">🏷️ ${item}</span>`).join("")}
      </div>

      <div class="fest-action-btn">
        <button class="btn btn-sm btn-secondary" onclick="preparePromoForFestival('${evt.name}')">
          <span>⚡</span> Create Festival Bundle
        </button>
      </div>
    </div>
  `).join("");
}

function preparePromoForFestival(festivalName) {
  switchScreen("promos");
  document.getElementById("promoEventSelect").value = "Diwali Maha Utsav (Big Billion Days Edition)";
  document.getElementById("promoPromptInput").value = `Create an irresistible promotional offer tailored for ${festivalName} focusing on regional festival essentials.`;
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
