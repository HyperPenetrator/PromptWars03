/**
 * EcoTrace — Frontend Application Logic
 *
 * Handles:
 * - API communication (fetch-based)
 * - Chart.js donut & line charts
 * - Log/Goal modal forms
 * - Insight panel rendering
 * - Tab navigation
 * - Toast notifications
 */

// ============================================================
// Constants & Configuration
// ============================================================

/** Sub-types per category with human-readable labels */
const SUB_TYPES = {
  transport: {
    car_petrol: "Car (Petrol)",
    car_electric: "Car (Electric)",
    bus: "Bus",
    train: "Train",
    flight_short: "Flight (Short-haul)",
    flight_long: "Flight (Long-haul)",
    cycling: "Cycling / Walking",
  },
  energy: {
    electricity_grid: "Electricity (Grid)",
    natural_gas: "Natural Gas",
    heating_oil: "Heating Oil",
  },
  diet: {
    beef_meal: "Beef Meal",
    pork_meal: "Pork Meal",
    chicken_meal: "Chicken Meal",
    fish_meal: "Fish Meal",
    vegetarian_meal: "Vegetarian Meal",
    vegan_meal: "Vegan Meal",
  },
  shopping: {
    clothing_item: "Clothing Item",
    electronics_item: "Electronics Item",
    streaming_hr: "Streaming (hours)",
  },
};

/** Units per category */
const UNITS = {
  transport: "km",
  energy: "kWh",
  diet: "meals",
  shopping: "items",
};

/** Category icons */
const CAT_ICONS = {
  transport: "🚗",
  energy: "⚡",
  diet: "🥗",
  shopping: "🛍️",
};

/** Category colors for charts */
const CAT_COLORS = {
  transport: "#3b82f6",
  energy: "#f59e0b",
  diet: "#10b981",
  shopping: "#a855f7",
};

// ============================================================
// DOM References
// ============================================================

const $ = (id) => document.getElementById(id);

const els = {
  // Stats
  statTotalValue: $("stat-total-value"),
  statEntriesValue: $("stat-entries-value"),
  statTopValue: $("stat-top-value"),
  statGoalsValue: $("stat-goals-value"),
  statTotalDelta: $("stat-total-delta"),

  // Charts
  chartDonut: $("chart-donut"),
  chartLine: $("chart-line"),

  // Tabs
  tabBtns: document.querySelectorAll(".tab-btn"),
  tabContents: document.querySelectorAll(".tab-content"),

  // Logs
  logsList: $("logs-list"),
  logsEmpty: $("logs-empty"),

  // Insights
  insightsContainer: $("insights-container"),
  insightsEmpty: $("insights-empty"),

  // Goals
  goalsList: $("goals-list"),
  goalsEmpty: $("goals-empty"),

  // Buttons
  btnOpenLog: $("btn-open-log"),
  btnGetInsights: $("btn-get-insights"),
  btnGetInsights2: $("btn-get-insights-2"),
  btnAddGoal: $("btn-add-goal"),

  // Log Modal
  logModal: $("log-modal"),
  logModalClose: $("log-modal-close"),
  logForm: $("log-form"),
  logCategory: $("log-category"),
  logSubtype: $("log-subtype"),
  logQuantity: $("log-quantity"),
  logNote: $("log-note"),
  logCancel: $("log-cancel"),
  logSubmit: $("log-submit"),
  logUnitHint: $("log-unit-hint"),

  // Goal Modal
  goalModal: $("goal-modal"),
  goalModalClose: $("goal-modal-close"),
  goalForm: $("goal-form"),
  goalCategory: $("goal-category"),
  goalTarget: $("goal-target"),
  goalDeadline: $("goal-deadline"),
  goalCancel: $("goal-cancel"),

  // Toast
  toastContainer: $("toast-container"),
};

// ============================================================
// State
// ============================================================

let donutChart = null;
let lineChart = null;

// ============================================================
// API Helpers
// ============================================================

/**
 * Make an API request with JSON body.
 * @param {string} path - API endpoint path
 * @param {object} options - fetch options
 * @returns {Promise<any>}
 */
async function api(path, options = {}) {
  const url = path.startsWith("http") ? path : path;
  const config = {
    headers: { "Content-Type": "application/json" },
    ...options,
  };
  if (config.body && typeof config.body === "object") {
    config.body = JSON.stringify(config.body);
  }
  const res = await fetch(url, config);
  if (res.status === 204) return null;
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

// ============================================================
// Toast Notifications
// ============================================================

/**
 * Show a toast notification.
 * @param {string} message
 * @param {"success"|"error"|"info"} type
 */
function showToast(message, type = "info") {
  const toast = document.createElement("div");
  toast.className = `toast ${type}`;

  const icons = { success: "✅", error: "❌", info: "ℹ️" };
  toast.innerHTML = `<span>${icons[type]}</span> ${message}`;

  els.toastContainer.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateX(40px)";
    toast.style.transition = "all 0.3s ease-in";
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

// ============================================================
// Tab Navigation
// ============================================================

function initTabs() {
  els.tabBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      // Update buttons
      els.tabBtns.forEach((b) => {
        b.classList.remove("active");
        b.setAttribute("aria-selected", "false");
      });
      btn.classList.add("active");
      btn.setAttribute("aria-selected", "true");

      // Update content panels
      const targetId = btn.getAttribute("aria-controls");
      els.tabContents.forEach((panel) => {
        panel.classList.remove("active");
      });
      document.getElementById(targetId).classList.add("active");
    });
  });
}

// ============================================================
// Charts
// ============================================================

/**
 * Initialize or update the donut chart with category breakdown data.
 * @param {object} byCategory - { transport: 12.5, energy: 8.3, ... }
 */
function updateDonutChart(byCategory) {
  const labels = Object.keys(byCategory).map(
    (c) => `${CAT_ICONS[c] || ""} ${c.charAt(0).toUpperCase() + c.slice(1)}`
  );
  const data = Object.values(byCategory);
  const colors = Object.keys(byCategory).map((c) => CAT_COLORS[c] || "#6b7280");

  const config = {
    type: "doughnut",
    data: {
      labels,
      datasets: [
        {
          data,
          backgroundColor: colors,
          borderColor: "rgba(10, 15, 26, 0.8)",
          borderWidth: 3,
          hoverBorderColor: "#ffffff",
          hoverBorderWidth: 2,
          hoverOffset: 8,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: "65%",
      plugins: {
        legend: {
          position: "bottom",
          labels: {
            color: "#94a3b8",
            padding: 16,
            font: { family: "Inter", size: 12, weight: 500 },
            usePointStyle: true,
            pointStyleWidth: 8,
          },
        },
        tooltip: {
          backgroundColor: "rgba(17, 24, 39, 0.95)",
          titleColor: "#f1f5f9",
          bodyColor: "#94a3b8",
          borderColor: "rgba(255,255,255,0.1)",
          borderWidth: 1,
          padding: 12,
          cornerRadius: 8,
          callbacks: {
            label: (ctx) => ` ${ctx.parsed.toFixed(2)} kg CO₂e`,
          },
        },
      },
    },
  };

  if (donutChart) {
    donutChart.data = config.data;
    donutChart.update("active");
  } else {
    donutChart = new Chart(els.chartDonut, config);
  }
}

/**
 * Initialize or update the line chart with daily emissions.
 * @param {object[]} logs - array of log entries
 */
function updateLineChart(logs) {
  // Group by date
  const dailyTotals = {};
  const now = new Date();

  // Initialize last 7 days
  for (let i = 6; i >= 0; i--) {
    const d = new Date(now);
    d.setDate(d.getDate() - i);
    const key = d.toISOString().split("T")[0];
    dailyTotals[key] = 0;
  }

  // Sum CO₂e per day
  logs.forEach((log) => {
    const day = new Date(log.logged_at).toISOString().split("T")[0];
    if (dailyTotals.hasOwnProperty(day)) {
      dailyTotals[day] += log.co2e_kg;
    }
  });

  const labels = Object.keys(dailyTotals).map((d) => {
    const date = new Date(d + "T00:00:00");
    return date.toLocaleDateString("en-US", { weekday: "short", month: "short", day: "numeric" });
  });
  const data = Object.values(dailyTotals).map((v) => parseFloat(v.toFixed(2)));

  const config = {
    type: "line",
    data: {
      labels,
      datasets: [
        {
          label: "CO₂e (kg)",
          data,
          borderColor: "#10b981",
          backgroundColor: "rgba(16, 185, 129, 0.1)",
          borderWidth: 2.5,
          pointBackgroundColor: "#10b981",
          pointBorderColor: "#0a0f1a",
          pointBorderWidth: 2,
          pointRadius: 5,
          pointHoverRadius: 7,
          tension: 0.4,
          fill: true,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: {
          grid: { color: "rgba(255,255,255,0.04)" },
          ticks: { color: "#64748b", font: { family: "Inter", size: 11 } },
        },
        y: {
          beginAtZero: true,
          grid: { color: "rgba(255,255,255,0.04)" },
          ticks: {
            color: "#64748b",
            font: { family: "Inter", size: 11 },
            callback: (v) => v + " kg",
          },
        },
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: "rgba(17, 24, 39, 0.95)",
          titleColor: "#f1f5f9",
          bodyColor: "#94a3b8",
          borderColor: "rgba(255,255,255,0.1)",
          borderWidth: 1,
          padding: 12,
          cornerRadius: 8,
          callbacks: {
            label: (ctx) => ` ${ctx.parsed.y.toFixed(2)} kg CO₂e`,
          },
        },
      },
    },
  };

  if (lineChart) {
    lineChart.data = config.data;
    lineChart.update("active");
  } else {
    lineChart = new Chart(els.chartLine, config);
  }
}

// ============================================================
// Data Loading
// ============================================================

/** Load logs and update the dashboard. */
async function loadDashboard() {
  try {
    const [logs, summary, goals] = await Promise.all([
      api("/logs?days=7"),
      api("/logs/summary?days=7"),
      api("/goals"),
    ]);

    // Update stat cards
    els.statTotalValue.textContent = summary.total_co2e_kg.toFixed(1);
    els.statEntriesValue.textContent = summary.entry_count;
    els.statGoalsValue.textContent = goals.length;

    // Find top emission category
    const cats = summary.by_category;
    if (Object.keys(cats).length > 0) {
      const topCat = Object.entries(cats).sort((a, b) => b[1] - a[1])[0];
      els.statTopValue.textContent =
        topCat[0].charAt(0).toUpperCase() + topCat[0].slice(1);
    } else {
      els.statTopValue.textContent = "—";
    }

    // Update charts
    if (Object.keys(cats).length > 0) {
      updateDonutChart(cats);
    } else {
      updateDonutChart({ transport: 0, energy: 0, diet: 0, shopping: 0 });
    }
    updateLineChart(logs);

    // Update logs list
    renderLogs(logs);

    // Update goals list
    renderGoals(goals);
  } catch (err) {
    console.error("Failed to load dashboard:", err);
    showToast("Failed to load data. Is the server running?", "error");
  }
}

// ============================================================
// Render Functions
// ============================================================

/** Render the log entries list. */
function renderLogs(logs) {
  if (logs.length === 0) {
    els.logsList.innerHTML = `
      <div class="empty-state">
        <div class="icon" aria-hidden="true">📝</div>
        <div class="message">No activities logged yet. Start by clicking "Log Activity" above!</div>
      </div>
    `;
    return;
  }

  els.logsList.innerHTML = logs
    .map((log) => {
      const icon = CAT_ICONS[log.category] || "📦";
      const label =
        SUB_TYPES[log.category]?.[log.sub_type] || log.sub_type.replace(/_/g, " ");
      const time = new Date(log.logged_at).toLocaleString("en-US", {
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
      const note = log.note ? ` · ${log.note}` : "";

      return `
        <div class="log-item" data-log-id="${log.id}">
          <div class="log-cat-icon ${log.category}" aria-hidden="true">${icon}</div>
          <div class="log-details">
            <div class="log-type">${label}</div>
            <div class="log-meta">${log.quantity} ${log.unit} · ${time}${note}</div>
          </div>
          <div class="log-co2" style="color: ${CAT_COLORS[log.category]}">${log.co2e_kg.toFixed(1)} kg</div>
          <div class="log-actions">
            <button class="btn btn-icon btn-danger" onclick="deleteLog(${log.id})" aria-label="Delete log entry" title="Delete">🗑️</button>
          </div>
        </div>
      `;
    })
    .join("");
}

/** Render the goals list. */
function renderGoals(goals) {
  if (goals.length === 0) {
    els.goalsList.innerHTML = `
      <div class="empty-state">
        <div class="icon" aria-hidden="true">🎯</div>
        <div class="message">No goals set yet. Create a CO₂e reduction target to stay motivated!</div>
      </div>
    `;
    return;
  }

  els.goalsList.innerHTML = goals
    .map((goal) => {
      let fillClass = "";
      if (goal.progress_pct > 80) fillClass = "danger";
      else if (goal.progress_pct > 50) fillClass = "warning";

      const deadlineStr = new Date(goal.deadline).toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
      });

      return `
        <div class="goal-item">
          <div class="goal-header">
            <div class="goal-category">
              <span class="cat-dot ${goal.category}"></span>
              ${goal.category}
            </div>
            <div class="goal-deadline">📅 ${deadlineStr}</div>
          </div>
          <div class="goal-progress-bar">
            <div class="goal-progress-fill ${fillClass}" style="width: ${goal.progress_pct}%"></div>
          </div>
          <div class="goal-stats">
            <span class="current">${goal.current_co2e_kg.toFixed(1)} / ${goal.target_co2e_kg.toFixed(1)} kg CO₂e</span>
            <span>${goal.progress_pct.toFixed(0)}% used</span>
          </div>
        </div>
      `;
    })
    .join("");
}

/** Render AI insight response. */
function renderInsight(data) {
  const insight = data.insight;

  if (!insight) {
    els.insightsContainer.innerHTML = `
      <div class="empty-state">
        <div class="icon" aria-hidden="true">😕</div>
        <div class="message">Could not generate insights. Try logging more activities first.</div>
      </div>
    `;
    return;
  }

  const suggestionsHtml = (insight.suggestions || [])
    .map((s) => {
      const diffClass = s.difficulty || "easy";
      return `
        <li class="insight-suggestion">
          <span class="suggestion-icon" aria-hidden="true">💡</span>
          <div class="suggestion-text">
            <div class="suggestion-action">${s.action}</div>
            <div class="suggestion-saving">↓ ${s.potential_saving_kg?.toFixed(1) || "?"} kg CO₂e potential saving</div>
          </div>
          <span class="difficulty-badge ${diffClass}">${diffClass}</span>
        </li>
      `;
    })
    .join("");

  els.insightsContainer.innerHTML = `
    <div class="insight-panel">
      <div class="insight-summary">${insight.summary || "Here are your insights."}</div>

      ${
        insight.top_emission
          ? `<div style="margin-bottom: 16px; padding: 12px 16px; background: rgba(245, 158, 11, 0.08); border: 1px solid rgba(245, 158, 11, 0.15); border-radius: 8px;">
              <span style="color: #f59e0b; font-weight: 700;">⚠️ Top Emission:</span>
              <span style="color: #fbbf24;">${insight.top_emission.category} — ${insight.top_emission.co2e_kg?.toFixed(1)} kg CO₂e (${insight.top_emission.percentage}%)</span>
            </div>`
          : ""
      }

      <ul class="insight-suggestions">${suggestionsHtml}</ul>

      ${
        insight.encouragement
          ? `<div class="insight-encouragement">
              <span aria-hidden="true">🌟</span>
              ${insight.encouragement}
            </div>`
          : ""
      }
    </div>
  `;
}

// ============================================================
// Actions
// ============================================================

/** Delete a log entry. */
async function deleteLog(id) {
  try {
    await api(`/logs/${id}`, { method: "DELETE" });
    showToast("Log entry deleted", "success");
    loadDashboard();
  } catch (err) {
    showToast(`Failed to delete: ${err.message}`, "error");
  }
}

/** Request AI insights. */
async function getInsights() {
  // Switch to insights tab
  document.getElementById("tab-btn-insights").click();

  // Show loading state
  els.insightsContainer.innerHTML = `
    <div class="loading-overlay">
      <div class="spinner"></div>
      Analyzing your carbon footprint with AI...
    </div>
  `;

  try {
    const data = await api("/insights", { method: "POST" });
    renderInsight(data);
    showToast("Insights generated successfully!", "success");
  } catch (err) {
    els.insightsContainer.innerHTML = `
      <div class="empty-state">
        <div class="icon" aria-hidden="true">❌</div>
        <div class="message">Failed to generate insights: ${err.message}</div>
        <button class="btn btn-primary" onclick="getInsights()" aria-label="Retry insights">Try Again</button>
      </div>
    `;
    showToast("Insight generation failed", "error");
  }
}

// ============================================================
// Log Modal
// ============================================================

function openLogModal(presetCategory = "") {
  els.logModal.classList.add("active");
  els.logForm.reset();
  els.logSubtype.disabled = true;
  els.logQuantity.disabled = true;
  els.logSubmit.disabled = true;
  els.logSubtype.innerHTML = '<option value="">Select category first...</option>';
  els.logUnitHint.textContent = "Select a category to see the unit";

  if (presetCategory) {
    els.logCategory.value = presetCategory;
    updateSubTypeOptions(presetCategory);
  }

  // Focus the category select
  setTimeout(() => els.logCategory.focus(), 100);
}

function closeLogModal() {
  els.logModal.classList.remove("active");
}

function updateSubTypeOptions(category) {
  const subtypes = SUB_TYPES[category];
  if (!subtypes) {
    els.logSubtype.disabled = true;
    els.logQuantity.disabled = true;
    els.logSubmit.disabled = true;
    return;
  }

  els.logSubtype.disabled = false;
  els.logQuantity.disabled = false;
  els.logSubtype.innerHTML =
    '<option value="">Select activity...</option>' +
    Object.entries(subtypes)
      .map(([val, label]) => `<option value="${val}">${label}</option>`)
      .join("");

  els.logUnitHint.textContent = `Unit: ${UNITS[category]}`;
}

function validateLogForm() {
  const valid =
    els.logCategory.value &&
    els.logSubtype.value &&
    els.logQuantity.value &&
    parseFloat(els.logQuantity.value) > 0;

  els.logSubmit.disabled = !valid;
}

async function submitLog(e) {
  e.preventDefault();

  const body = {
    category: els.logCategory.value,
    sub_type: els.logSubtype.value,
    quantity: parseFloat(els.logQuantity.value),
    note: els.logNote.value || null,
  };

  try {
    els.logSubmit.disabled = true;
    els.logSubmit.textContent = "Saving...";
    await api("/logs", { method: "POST", body });
    showToast("Activity logged successfully! 🌱", "success");
    closeLogModal();
    loadDashboard();
  } catch (err) {
    showToast(`Failed to log: ${err.message}`, "error");
  } finally {
    els.logSubmit.disabled = false;
    els.logSubmit.textContent = "Save Activity";
  }
}

// ============================================================
// Goal Modal
// ============================================================

function openGoalModal() {
  els.goalModal.classList.add("active");
  els.goalForm.reset();

  // Set default deadline to 30 days from now
  const deadline = new Date();
  deadline.setDate(deadline.getDate() + 30);
  els.goalDeadline.value = deadline.toISOString().split("T")[0];

  setTimeout(() => els.goalCategory.focus(), 100);
}

function closeGoalModal() {
  els.goalModal.classList.remove("active");
}

async function submitGoal(e) {
  e.preventDefault();

  const body = {
    category: els.goalCategory.value,
    target_co2e_kg: parseFloat(els.goalTarget.value),
    deadline: els.goalDeadline.value,
  };

  if (!body.category || !body.target_co2e_kg || !body.deadline) {
    showToast("Please fill in all fields", "error");
    return;
  }

  try {
    await api("/goals", { method: "POST", body });
    showToast("Goal created! 🎯", "success");
    closeGoalModal();
    loadDashboard();
  } catch (err) {
    showToast(`Failed to create goal: ${err.message}`, "error");
  }
}

// ============================================================
// Event Listeners
// ============================================================

function initEventListeners() {
  // Log modal
  els.btnOpenLog.addEventListener("click", () => openLogModal());
  els.logModalClose.addEventListener("click", closeLogModal);
  els.logCancel.addEventListener("click", closeLogModal);
  els.logModal.addEventListener("click", (e) => {
    if (e.target === els.logModal) closeLogModal();
  });

  // Log form
  els.logCategory.addEventListener("change", (e) => {
    updateSubTypeOptions(e.target.value);
    validateLogForm();
  });
  els.logSubtype.addEventListener("change", validateLogForm);
  els.logQuantity.addEventListener("input", validateLogForm);
  els.logForm.addEventListener("submit", submitLog);

  // Quick log buttons
  document.querySelectorAll(".quick-log-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      openLogModal(btn.dataset.category);
    });
  });

  // Insights
  els.btnGetInsights.addEventListener("click", getInsights);
  els.btnGetInsights2.addEventListener("click", getInsights);

  // Goal modal
  els.btnAddGoal.addEventListener("click", openGoalModal);
  els.goalModalClose.addEventListener("click", closeGoalModal);
  els.goalCancel.addEventListener("click", closeGoalModal);
  els.goalModal.addEventListener("click", (e) => {
    if (e.target === els.goalModal) closeGoalModal();
  });
  els.goalForm.addEventListener("submit", submitGoal);

  // Keyboard: Escape closes modals
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      closeLogModal();
      closeGoalModal();
    }
  });
}

// ============================================================
// Init
// ============================================================

document.addEventListener("DOMContentLoaded", () => {
  initTabs();
  initEventListeners();
  loadDashboard();
});
