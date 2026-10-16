const API_BASE =
  process.env.NEXT_PUBLIC_API_URL !== undefined && process.env.NEXT_PUBLIC_API_URL !== ""
    ? process.env.NEXT_PUBLIC_API_URL
    : (typeof window !== "undefined" && (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1")
        ? "http://127.0.0.1:8080"
        : "");

function getAuthHeaders(extraHeaders = {}) {
  const headers = { ...extraHeaders };
  if (typeof window !== "undefined") {
    const apiKey = localStorage.getItem("promomind_gemini_api_key");
    const storeId = localStorage.getItem("promomind_store_id");
    const userRaw = localStorage.getItem("promomind_user");
    if (apiKey && apiKey.trim()) {
      headers["X-Gemini-Api-Key"] = apiKey.trim();
    }
    if (storeId && storeId.trim()) {
      headers["X-Store-Id"] = storeId.trim();
    }
    if (userRaw) {
      try {
        const u = JSON.parse(userRaw);
        if (u && u.user_id) {
          headers["X-User-Id"] = u.user_id;
        }
      } catch (_) {}
    }
  }
  return headers;
}

async function apiRequest(path, options = {}) {
  const url = `${API_BASE}${path}`;
  const isFormData = options.body instanceof FormData;
  const baseHeaders = isFormData ? {} : { "Content-Type": "application/json" };
  const headers = getAuthHeaders({ ...baseHeaders, ...(options.headers || {}) });

  const res = await fetch(url, {
    ...options,
    headers,
    cache: "no-store",
  });

  if (!res.ok) {
    let errDetail = "";
    try {
      const rawText = await res.text();
      try {
        const errJson = JSON.parse(rawText);
        if (typeof errJson.detail === "string") {
          errDetail = errJson.detail;
        } else if (Array.isArray(errJson.detail)) {
          errDetail = errJson.detail.map((d) => d.msg || JSON.stringify(d)).join("; ");
        } else if (typeof errJson.message === "string") {
          errDetail = errJson.message;
        } else if (typeof errJson.error === "string") {
          errDetail = errJson.error;
        } else {
          errDetail = JSON.stringify(errJson);
        }
      } catch {
        if (rawText && !rawText.includes("<!DOCTYPE") && !rawText.includes("<html")) {
          errDetail = rawText.trim();
        }
      }
    } catch (_) {}

    const method = options.method || "GET";
    const statusInfo = errDetail
      ? `HTTP ${res.status}: ${errDetail}`
      : `HTTP ${res.status} (Backend unreachable or internal error on ${method} ${path}. Ensure FastAPI backend is running on http://127.0.0.1:8080)`;

    throw new Error(statusInfo);
  }
  return res.json();
}

// ============================================================================
// User Authentication & Multi-Store Management Under User
// ============================================================================

export async function signUpUser({ email, password, full_name, phone }) {
  return apiRequest("/api/auth/signup", {
    method: "POST",
    body: JSON.stringify({ email, password, full_name, phone }),
  });
}

export async function signInUser({ email, password }) {
  return apiRequest("/api/auth/signin", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export async function fetchCurrentUser(userId = null, email = null) {
  let query = "";
  if (userId) query = `?user_id=${encodeURIComponent(userId)}`;
  else if (email) query = `?email=${encodeURIComponent(email)}`;
  return apiRequest(`/api/auth/me${query}`);
}

export async function switchUserStore(storeId, userId = null) {
  return apiRequest("/api/auth/switch-store", {
    method: "POST",
    body: JSON.stringify({ store_id: storeId, user_id: userId }),
  });
}

// ============================================================================
// Store Management & API Key Config
// ============================================================================

export async function loginStore(payload) {
  return apiRequest("/api/auth/login", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function fetchStores(userId = null) {
  const query = userId ? `?user_id=${encodeURIComponent(userId)}` : "";
  return apiRequest(`/api/stores${query}`);
}

export async function createOrSwitchStore(payload) {
  return apiRequest("/api/stores", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function configureGeminiApiKey(geminiApiKey, geminiModel = "gemini-2.5-flash") {
  return apiRequest("/api/config/api-key", {
    method: "POST",
    body: JSON.stringify({
      gemini_api_key: geminiApiKey,
      gemini_model: geminiModel,
    }),
  });
}

// ============================================================================
// Store Profile & Storage Status
// ============================================================================

export async function fetchStoreProfile() {
  return apiRequest("/api/store/profile");
}

export async function saveStoreProfile(payload) {
  return apiRequest("/api/store/profile", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function fetchStorageStatus() {
  return apiRequest("/api/storage/status");
}

// ============================================================================
// Inventory, Multi-Brand Curves & Financial ROI
// ============================================================================

export async function fetchInventory() {
  return apiRequest("/api/inventory");
}

export async function addProduct(skuPayload) {
  return apiRequest("/api/products", {
    method: "POST",
    body: JSON.stringify(skuPayload),
  });
}

export async function fetchBrandComparison(productId) {
  return apiRequest(`/api/inventory/${encodeURIComponent(productId)}/brand-comparison`);
}

export async function fetchFinancialRoi() {
  const data = await apiRequest("/api/store/financial-roi");
  return {
    ...data,
    capital_invested_inr: data.total_inventory_invested_inr,
    projected_30d_turnover_inr: data.projected_sales_revenue_inr,
    projected_net_profit_inr: data.projected_gross_profit_inr,
    net_return_pct: data.overall_roi_pct,
    dead_capital_at_risk_inr: data.dead_capital_at_risk_inr,
    unlocked_cash_via_promos_inr: data.unlocked_capital_from_promos_inr,
  };
}

export async function simulateRoi(discountPct, volumeLiftPct) {
  const data = await apiRequest("/api/store/simulate-roi", {
    method: "POST",
    body: JSON.stringify({
      proposed_discount_depth_pct: discountPct,
      expected_volume_lift_pct: volumeLiftPct,
    }),
  });
  return {
    ...data,
    simulated_turnover_inr: data.simulated_revenue_inr,
    simulated_net_profit_inr: data.simulated_profit_inr,
  };
}

// ============================================================================
// Regional Festival Calendar & Store Offers Lifecycle Manager
// ============================================================================

export async function fetchCalendarEvents(region = "", isRefresh = false, country = "India", city = "") {
  if (!isRefresh) {
    const params = new URLSearchParams();
    if (region) params.set("region", region);
    if (country) params.set("country", country);
    if (city) params.set("city", city);
    params.set("refresh", "false");
    return apiRequest(`/api/calendar/events?${params.toString()}`);
  }
  return apiRequest("/api/calendar/discover", {
    method: "POST",
    body: JSON.stringify({
      region: region || undefined,
      country: country || "India",
      city: city || undefined,
      force_refresh: true,
    }),
  });
}

export async function fetchActiveOffers() {
  return apiRequest("/api/offers/active");
}

export async function updateOfferStatus(offerId, payload) {
  return apiRequest(`/api/offers/${encodeURIComponent(offerId)}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export async function deleteOffer(offerId) {
  return apiRequest(`/api/offers/${encodeURIComponent(offerId)}`, {
    method: "DELETE",
  });
}

export async function checkOfferConflict(anchorId, attachedId = "NONE", startDate = "2026-10-20", endDate = "2026-10-30") {
  return apiRequest("/api/offers/check-conflict", {
    method: "POST",
    body: JSON.stringify({
      anchor_id: anchorId,
      attached_id: attachedId,
      start_date: startDate,
      end_date: endDate,
    }),
  });
}

// ============================================================================
// AI Retail Copilot, Weekly Ideas & Combo Generation
// ============================================================================

export async function sendChatMessage(message, region = null, minMarginPct = null) {
  return apiRequest("/api/chat", {
    method: "POST",
    body: JSON.stringify({
      message,
      region,
      min_margin_pct: minMarginPct,
    }),
  });
}

export async function generateComboOffer(payload) {
  return apiRequest("/api/generate-combo", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function publishOffer(payload) {
  return apiRequest("/api/publish-offer", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

// ============================================================================
// Smart Deduplicating Firestore CSV Upload
// ============================================================================

export async function uploadCsvFile(formData) {
  return apiRequest("/api/upload-csv", {
    method: "POST",
    body: formData,
  });
}

export async function uploadRawCsv(rawText) {
  const formData = new FormData();
  formData.append("raw_csv", rawText);
  return apiRequest("/api/upload-csv", {
    method: "POST",
    body: formData,
  });
}

export async function fetchKnowledgeMarkdown() {
  return apiRequest("/api/knowledge-md");
}
