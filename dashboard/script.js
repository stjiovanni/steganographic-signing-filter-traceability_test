const API = "";
const COLORS = {
  trustmark: "#ff6b35",
  lsb: "#2ecc71",
  dct: "#3498db",
  hash: "#9b59b6",
};
const METHOD_KEYS = ["trustmark", "lsb", "dct"];
const HASH_BITS = 256;

let overviewChart = null;
let transformChart = null;
let transformAbort = null;

let overviewFailed = false;
let perTransformFailed = false;
let ensembleFailed = false;
let svTransformsFailed = false;

// ── Helpers ──────────────────────────────────────────────────────
async function get(path, opts) {
  const r = await fetch(`${API}${path}`, opts);
  if (!r.ok) throw new Error(await readError(r));
  return r.json();
}

async function postForm(path, fd) {
  const r = await fetch(`${API}${path}`, { method: "POST", body: fd });
  if (!r.ok) throw new Error(await readError(r));
  return r.json();
}

async function postJSON(path, body) {
  const r = await fetch(`${API}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!r.ok) throw new Error(await readError(r));
  return r.json();
}

async function readError(r) {
  try {
    const body = await r.json();
    if (body && body.detail) {
      return typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
    }
    return r.statusText;
  } catch (_) {
    return r.statusText || `HTTP ${r.status}`;
  }
}

function showError(el, msg) {
  if (!el) return;
  el.textContent = msg;
  el.hidden = false;
}

function clearError(el) {
  if (!el) return;
  el.textContent = "";
  el.hidden = true;
}

function $(sel) {
  return document.querySelector(sel);
}

function meanValues(obj) {
  const vals = Object.values(obj);
  if (!vals.length) return 0;
  return vals.reduce((s, v) => s + v, 0) / vals.length;
}

// ── Tab Switching ────────────────────────────────────────────────
function activateTab(btn) {
  document.querySelectorAll(".tab").forEach((t) => {
    const active = t === btn;
    t.classList.toggle("active", active);
    t.setAttribute("aria-selected", String(active));
    t.tabIndex = active ? 0 : -1;
  });
  document.querySelectorAll(".tab-panel").forEach((p) => p.classList.remove("active"));
  const panel = $(`#tab-${btn.dataset.tab}`);
  panel.classList.add("active");

  if (btn.dataset.tab === "overview" && overviewFailed) {
    overviewFailed = false;
    initOverview();
  }
  if (btn.dataset.tab === "per-transform" && (!$("#transform-select").options.length || perTransformFailed)) {
    perTransformFailed = false;
    initPerTransform();
  }
  if (btn.dataset.tab === "ensemble" && (!$("#ensemble-table").rows.length || ensembleFailed)) {
    ensembleFailed = false;
    initEnsemble();
  }
  if (btn.dataset.tab === "per-image" && !$("#image-select").options.length) {
    initPerImage();
  }
  if (btn.dataset.tab === "sign-verify" && (!$("#sv-filter-select").options.length || svTransformsFailed)) {
    svTransformsFailed = false;
    svInitTransforms();
  }
}

document.querySelectorAll(".tab").forEach((btn) => {
  btn.addEventListener("click", () => activateTab(btn));
});

$("#tabs").addEventListener("keydown", (e) => {
  const tabs = Array.from(document.querySelectorAll(".tab"));
  const idx = tabs.indexOf(document.activeElement);
  if (idx === -1) return;
  let next = null;
  if (e.key === "ArrowRight") next = tabs[(idx + 1) % tabs.length];
  else if (e.key === "ArrowLeft") next = tabs[(idx - 1 + tabs.length) % tabs.length];
  else if (e.key === "Home") next = tabs[0];
  else if (e.key === "End") next = tabs[tabs.length - 1];
  else return;
  e.preventDefault();
  next.focus();
  activateTab(next);
});

// ── Chart.js global defaults ─────────────────────────────────────
if (typeof Chart !== "undefined") {
  Chart.defaults.color = "#8888aa";
  Chart.defaults.borderColor = "rgba(255,255,255,0.06)";
  Chart.defaults.font.family = 'Jost, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, sans-serif';
}

// ── Overview ─────────────────────────────────────────────────────
async function initOverview() {
  if (overviewChart) {
    overviewChart.destroy();
    overviewChart = null;
  }
  clearError($("#overview-chart-error"));

  let summary;
  try {
    summary = await get("/api/summary");
  } catch (e) {
    overviewFailed = true;
    $("#stats-grid").innerHTML = `<div class="no-data">Failed to load overview: ${e.message}</div>`;
    return;
  }

  const grid = $("#stats-grid");
  grid.innerHTML = `
    <div class="stat-card"><div class="label">Images</div><div class="value accent">${summary.image_count}</div></div>
    <div class="stat-card"><div class="label">Transforms</div><div class="value green">${summary.transform_count}</div></div>
    <div class="stat-card"><div class="label">Hash Algorithms</div><div class="value purple">${summary.hash_algorithms.length}</div></div>
    <div class="stat-card"><div class="label">Transform Types</div><div class="value blue">${summary.transforms.length}</div></div>
  `;

  try {
    const [tm, ls, dc, hm] = await Promise.all([
      get("/api/trustmark/by_transform?agg=mean"),
      get("/api/lsb/by_transform?agg=mean"),
      get("/api/dct/by_transform?agg=mean"),
      get("/api/hash/by_transform?agg=mean"),
    ]);

    const transforms = summary.transforms;
    const tmMeans = transforms.map((t) => meanValues(tm[t] || {}));
    const lsMeans = transforms.map((t) => meanValues(ls[t] || {}));
    const dcMeans = transforms.map((t) => meanValues(dc[t] || {}));
    const hmMeans = transforms.map((t) => {
      const raw = meanValues(hm[t] || {});
      return 1 - raw / HASH_BITS;
    });

    const ctx = $("#overview-chart").getContext("2d");
    overviewChart = new Chart(ctx, {
      type: "bar",
      data: {
        labels: transforms,
        datasets: [
          { label: "TrustMark", data: tmMeans, backgroundColor: COLORS.trustmark + "cc" },
          { label: "LSB", data: lsMeans, backgroundColor: COLORS.lsb + "cc" },
          { label: "DCT", data: dcMeans, backgroundColor: COLORS.dct + "cc" },
          { label: "Hash", data: hmMeans, backgroundColor: COLORS.hash + "cc" },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: true,
        plugins: { legend: { labels: { usePointStyle: true, pointStyle: "circle" } } },
        scales: {
          y: { beginAtZero: true, max: 1, title: { display: true, text: "Mean Robustness (0-1)" } },
          x: { ticks: { maxRotation: 45, minRotation: 30 } },
        },
      },
    });
    overviewFailed = false;
  } catch (e) {
    overviewFailed = true;
    showError($("#overview-chart-error"), `Failed to load chart data: ${e.message}`);
  }
}

// ── Per-Transform ────────────────────────────────────────────────
async function initPerTransform() {
  let transforms;
  try {
    transforms = await get("/api/transforms");
  } catch (e) {
    perTransformFailed = true;
    showError($("#transform-error"), `Failed to load transforms: ${e.message}`);
    return;
  }
  clearError($("#transform-error"));

  const sel = $("#transform-select");
  sel.innerHTML = "";
  const names = Object.keys(transforms).sort();
  names.forEach((n) => {
    const o = document.createElement("option");
    o.value = n;
    o.textContent = n;
    sel.appendChild(o);
  });
  if (!sel.dataset.bound) {
    sel.dataset.bound = "1";
    sel.addEventListener("change", () => {
      clearError($("#transform-error"));
      loadTransformChart(sel.value).catch((e) => {
        if (e.name === "AbortError") return;
        showError($("#transform-error"), `Failed to load chart: ${e.message}`);
      });
    });
  }
  if (names.length) {
    loadTransformChart(names[0]).catch((e) => {
      if (e.name === "AbortError") return;
      showError($("#transform-error"), `Failed to load chart: ${e.message}`);
    });
  }
  perTransformFailed = false;
}

async function loadTransformChart(transform) {
  if (transformAbort) transformAbort.abort();
  const controller = new AbortController();
  transformAbort = controller;
  const signal = controller.signal;
  try {
    const [tm, ls, dc, hm] = await Promise.all([
      get(`/api/trustmark/by_transform?agg=mean`, { signal }),
      get(`/api/lsb/by_transform?agg=mean`, { signal }),
      get(`/api/dct/by_transform?agg=mean`, { signal }),
      get(`/api/hash/by_algorithm?transform=${encodeURIComponent(transform)}&agg=mean`, { signal }),
    ]);

    const tmIntensities = tm[transform] || {};
    const lsIntensities = ls[transform] || {};
    const dcIntensities = dc[transform] || {};

    // Collect all intensities across watermark methods
    const intensitySet = new Set();
    [tmIntensities, lsIntensities, dcIntensities].forEach((o) =>
      Object.keys(o).forEach((k) => intensitySet.add(k))
    );
    // Add hash intensities
    Object.values(hm).forEach((o) => Object.keys(o).forEach((k) => intensitySet.add(k)));

    const intensities = Array.from(intensitySet)
      .map(Number)
      .sort((a, b) => a - b);

    const tmData = intensities.map((i) => tmIntensities[String(i)] ?? null);
    const lsData = intensities.map((i) => lsIntensities[String(i)] ?? null);
    const dcData = intensities.map((i) => dcIntensities[String(i)] ?? null);

    // Hash: invert (1 - hamming/HASH_BITS)
    const hashAlgos = Object.keys(hm);
    const hashData = intensities.map((i) => {
      const vals = hashAlgos.map((a) => hm[a]?.[String(i)]).filter((v) => v != null);
      if (!vals.length) return null;
      const mean = vals.reduce((s, v) => s + v, 0) / vals.length;
      return 1 - mean / HASH_BITS;
    });

    const labels = intensities.map(String);

    if (transformChart) transformChart.destroy();

    const ctx = $("#transform-chart").getContext("2d");
    transformChart = new Chart(ctx, {
      type: "line",
      data: {
        labels,
        datasets: [
          { label: "TrustMark", data: tmData, borderColor: COLORS.trustmark, backgroundColor: COLORS.trustmark + "22", tension: 0.25, yAxisID: "y", pointRadius: 2 },
          { label: "LSB", data: lsData, borderColor: COLORS.lsb, backgroundColor: COLORS.lsb + "22", tension: 0.25, yAxisID: "y", pointRadius: 2 },
          { label: "DCT", data: dcData, borderColor: COLORS.dct, backgroundColor: COLORS.dct + "22", tension: 0.25, yAxisID: "y", pointRadius: 2 },
          { label: "Hash (inv)", data: hashData, borderColor: COLORS.hash, backgroundColor: COLORS.hash + "22", tension: 0.25, yAxisID: "y2", pointRadius: 2, borderDash: [6, 3] },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: true,
        interaction: { mode: "index", intersect: false },
        plugins: {
          legend: { labels: { usePointStyle: true, pointStyle: "circle" } },
        },
        scales: {
          y: {
            type: "linear",
            position: "left",
            min: 0,
            max: 1,
            title: { display: true, text: "Bit Accuracy" },
          },
          y2: {
            type: "linear",
            position: "right",
            min: 0,
            max: 1,
            title: { display: true, text: "Hash (inv)" },
            grid: { drawOnChartArea: false },
          },
          x: { title: { display: true, text: "Intensity" } },
        },
      },
      plugins: [
        {
          id: "thresholdLine",
          afterDraw(chart) {
            const yScale = chart.scales.y;
            const y = yScale.getPixelForValue(0.5);
            const ctx = chart.ctx;
            ctx.save();
            ctx.setLineDash([8, 4]);
            ctx.strokeStyle = "rgba(255,255,255,0.3)";
            ctx.lineWidth = 1;
            ctx.beginPath();
            ctx.moveTo(chart.chartArea.left, y);
            ctx.lineTo(chart.chartArea.right, y);
            ctx.stroke();
            ctx.restore();
          },
        },
      ],
    });
  } finally {
    if (transformAbort === controller) transformAbort = null;
  }
}

// ── Ensemble Matrix ──────────────────────────────────────────────
async function initEnsemble() {
  let data;
  try {
    data = await get("/api/ensemble/matrix");
  } catch (e) {
    ensembleFailed = true;
    showError($("#ensemble-error"), `Failed to load ensemble matrix: ${e.message}`);
    return;
  }

  const table = $("#ensemble-table");
  const methodColorMap = {
    trustmark: COLORS.trustmark,
    hash: COLORS.hash,
    lsb: COLORS.lsb,
    dct: COLORS.dct,
  };

  const transforms = data.transforms || [];
  if (!transforms.length) {
    showError($("#ensemble-error"), "No ensemble data available.");
    return;
  }
  clearError($("#ensemble-error"));

  const intensities = data.intensities?.[transforms[0]] || [];
  let html = "<thead><tr><th>Transform</th>";
  intensities.forEach((i) => {
    html += `<th>${i}</th>`;
  });
  html += "</tr></thead><tbody>";

  transforms.forEach((t) => {
    html += `<tr><th>${t}</th>`;
    const tIntensities = data.intensities?.[t] || [];
    tIntensities.forEach((i) => {
      const key = String(i);
      const entry = data.best?.[t]?.[key];
      if (entry) {
        const color = methodColorMap[entry] || "#555";
        html += `<td class="matrix-cell" style="background:${color}22;color:${color}">${entry}</td>`;
      } else {
        html += `<td></td>`;
      }
    });
    html += "</tr>";
  });
  html += "</tbody>";
  table.innerHTML = html;
  ensembleFailed = false;
}

// ── Per-Image ────────────────────────────────────────────────────
let perImageAbort = null;

function initPerImage() {
  const sel = $("#image-select");
  const ids = [
    139, 367, 595, 823, 1051, 1279, 1507, 1735, 1963, 2191,
    2419, 2647, 2875, 3103, 3331, 3559, 3787, 4015, 4243, 4471,
    4699, 4927, 5155, 5383, 5611, 5839, 6067, 6295, 6523, 6751,
    6979, 7207, 7435, 7663, 7891, 8119, 8347, 8575, 8803, 9031,
    9259, 9487, 9891,
  ];
  ids.forEach((id) => {
    const o = document.createElement("option");
    o.value = String(id).padStart(13, "0");
    o.textContent = `IMG-${String(id).padStart(13, "0")}`;
    sel.appendChild(o);
  });
  sel.addEventListener("change", () => loadPerImage(sel.value));
  if (ids.length) loadPerImage(String(ids[0]).padStart(13, "0"));
}

async function loadPerImage(id) {
  if (perImageAbort) perImageAbort.abort();
  perImageAbort = new AbortController();

  const container = $("#per-image-content");
  while (container.firstChild) container.removeChild(container.firstChild);
  container.innerHTML = '<div class="no-data">Loading...</div>';

  try {
    const data = await get(`/api/image/${id}`);
    while (container.firstChild) container.removeChild(container.firstChild);
    let html = "";

    // Hash results (flat array)
    const hashRows = Array.isArray(data.hash) ? data.hash : [];
    if (hashRows.length) {
      html += '<div class="card"><h2>Hash Results</h2><table><thead><tr><th>Algorithm</th><th>Transform</th><th>Intensity</th><th>Hamming Distance</th></tr></thead><tbody>';
      hashRows.forEach((r) => {
        html += `<tr><td>${r.hash_algorithm ?? ""}</td><td>${r.transform_name ?? ""}</td><td class="numeric">${r.intensity_value ?? ""}</td><td class="numeric">${r.hamming_distance ?? ""}</td></tr>`;
      });
      html += "</tbody></table></div>";
    }

    // Watermark results (flat arrays per method)
    const wmMethods = ["trustmark", "lsb", "dct"];
    const wmRows = [];
    wmMethods.forEach((m) => {
      const arr = Array.isArray(data[m]) ? data[m] : [];
      arr.forEach((r) => wmRows.push({ method: m, ...r }));
    });

    if (wmRows.length) {
      html += '<div class="card"><h2>Watermark Results</h2><table><thead><tr><th>Method</th><th>Transform</th><th>Intensity</th><th>Bit Accuracy</th><th>Present</th></tr></thead><tbody>';
      wmRows.forEach((r) => {
        const present = r.decode_present === true || r.decode_present === "True" || r.decode_present === "true";
        html += `<tr><td style="color:${COLORS[r.method]};font-weight:600">${r.method}</td><td>${r.transform_name ?? ""}</td><td class="numeric">${r.intensity_value ?? ""}</td><td class="numeric">${r.bit_accuracy ?? ""}</td><td>${present ? "Yes" : "No"}</td></tr>`;
      });
      html += "</tbody></table></div>";
    }

    if (!html) html = '<div class="no-data">No data available for this image.</div>';
    container.innerHTML = html;
  } catch (e) {
    if (e.name === "AbortError") return;
    container.innerHTML = `<div class="no-data">Failed to load image ${id}: ${e.message}</div>`;
  }
}

// ── Sign / Verify ───────────────────────────────────────────────
let svState = {
  imageId: null,
  filteredId: null,
  signedId: null,
  signedMethod: null,
  transformSteps: {},
};

function svPlaceholder(slot) {
  slot.innerHTML = '<span class="sv-placeholder">—</span>';
}

function svShowImage(slot, imageId, alt) {
  slot.innerHTML = `<img src="/api/preview/${imageId}" alt="${alt}">`;
}

function svStatus(msg, type) {
  const el = $("#sv-status");
  el.textContent = msg;
  el.className = "sv-status" + (type ? ` ${type}` : "");
}

function svShowResults(data) {
  const card = $("#sv-results-card");
  const grid = $("#sv-results");
  card.style.display = "";
  const items = [
    { label: "Method", value: data.method },
    { label: "Detected", value: data.detected ? "Yes" : "No" },
    { label: "Bit Accuracy", value: (data.bit_accuracy * 100).toFixed(1) + "%" },
    { label: "Payload", value: data.decoded_payload || "—" },
  ];
  if (data.schema) {
    items.push({ label: "Schema", value: data.schema });
  }
  grid.innerHTML = items
    .map(
      (i) =>
        `<div class="sv-result-item"><div class="sv-result-label">${i.label}</div><div class="sv-result-value">${i.value}</div></div>`
    )
    .join("");
}

function svResetPreviews() {
  svPlaceholder($("#sv-preview-original"));
  svPlaceholder($("#sv-preview-filtered"));
  svPlaceholder($("#sv-preview-signed"));
  $("#sv-results-card").style.display = "none";
}

async function svInitTransforms() {
  try {
    const data = await get("/api/transforms/list");
    svState.transformSteps = data.steps;
    const sel = $("#sv-filter-select");
    sel.innerHTML = "";
    data.transforms.forEach((t) => {
      const o = document.createElement("option");
      o.value = t;
      o.textContent = t;
      sel.appendChild(o);
    });
    if (data.transforms.length) svUpdateIntensitySlider();
    clearError($("#sv-transforms-error"));
    svTransformsFailed = false;
  } catch (e) {
    svTransformsFailed = true;
    showError($("#sv-transforms-error"), `Failed to load transforms: ${e.message}`);
  }
}

function svUpdateIntensitySlider() {
  const sel = $("#sv-filter-select");
  const steps = svState.transformSteps[sel.value] || [];
  const slider = $("#sv-intensity-slider");
  const text = $("#sv-intensity-input");
  if (steps.length === 0) {
    slider.min = 0;
    slider.max = 100;
    slider.value = 50;
    text.value = "";
    return;
  }
  slider.min = 0;
  slider.max = steps.length - 1;
  slider.value = 0;
  text.value = String(steps[0]);
  text.dataset.steps = JSON.stringify(steps);
}

// File picker
$("#sv-file-input").addEventListener("change", (e) => {
  const f = e.target.files[0];
  $("#sv-file-name").textContent = f ? f.name : "No file chosen";
});

// Upload
$("#sv-upload-btn").addEventListener("click", async () => {
  const file = $("#sv-file-input").files[0];
  if (!file) return svStatus("Select a file first", "error");
  const btn = $("#sv-upload-btn");
  const fd = new FormData();
  fd.append("file", file);
  btn.disabled = true;
  svStatus("Uploading…");
  try {
    const data = await postForm("/api/upload", fd);
    svState.imageId = data.image_id;
    svState.filteredId = null;
    svState.signedId = null;
    svState.signedMethod = null;
    $("#sv-method-select").disabled = false;
    svResetPreviews();
    svShowImage($("#sv-preview-original"), data.image_id, "Original");
    $("#sv-filter-btn").disabled = false;
    $("#sv-sign-btn").disabled = false;
    $("#sv-verify-btn").disabled = true;
    svStatus("Uploaded", "ok");
  } catch (e) {
    svStatus("Upload failed: " + e.message, "error");
  } finally {
    btn.disabled = false;
  }
});

// Filter select → update slider
$("#sv-filter-select").addEventListener("change", svUpdateIntensitySlider);

// Slider ↔ text sync
$("#sv-intensity-slider").addEventListener("input", () => {
  const steps = JSON.parse($("#sv-intensity-input").dataset.steps || "[]");
  const idx = parseInt($("#sv-intensity-slider").value, 10);
  if (steps.length > idx) $("#sv-intensity-input").value = String(steps[idx]);
});

// Apply Filter
$("#sv-filter-btn").addEventListener("click", async () => {
  const id = svState.imageId;
  if (!id) return svStatus("Upload an image first", "error");
  const transform = $("#sv-filter-select").value;
  const intensity = $("#sv-intensity-input").value;
  const steps = svState.transformSteps[transform] || [];
  if (!steps.length) return svStatus("No intensity steps available for this transform", "error");
  if (!steps.includes(intensity)) {
    return svStatus(`Invalid intensity. Expected one of: ${steps.join(", ")}`, "error");
  }
  const btn = $("#sv-filter-btn");
  btn.disabled = true;
  svState.filteredId = null;
  svStatus("Applying filter…");
  try {
    const data = await postJSON("/api/filter", {
      image_id: id,
      transform_name: transform,
      intensity: isNaN(Number(intensity)) ? intensity : Number(intensity),
    });
    svState.filteredId = data.image_id + "_" + data.transform + "_" + data.intensity;
    svShowImage($("#sv-preview-filtered"), svState.filteredId, "Filtered");
    $("#sv-sign-btn").disabled = false;
    svStatus("Filter applied", "ok");
  } catch (e) {
    svStatus("Filter failed: " + e.message, "error");
  } finally {
    btn.disabled = false;
  }
});

// Sign
$("#sv-sign-btn").addEventListener("click", async () => {
  const id = svState.filteredId || svState.imageId;
  if (!id) return svStatus("Upload an image first", "error");
  const method = $("#sv-method-select").value;
  const payload = $("#sv-payload-input").value || undefined;
  const btn = $("#sv-sign-btn");
  btn.disabled = true;
  svStatus("Signing… (TrustMark may take a moment)");
  try {
    const data = await postJSON("/api/sign", { image_id: id, method, payload });
    svState.signedId = data.signed_id;
    svState.signedMethod = method;
    $("#sv-method-select").disabled = true;
    svShowImage($("#sv-preview-signed"), data.signed_id, "Signed");
    $("#sv-verify-btn").disabled = false;
    svStatus("Signed successfully", "ok");
  } catch (e) {
    svStatus("Sign failed: " + e.message, "error");
  } finally {
    btn.disabled = false;
  }
});

// Verify
$("#sv-verify-btn").addEventListener("click", async () => {
  const id = svState.signedId;
  if (!id) return svStatus("Sign an image first", "error");
  const method = svState.signedMethod;
  if (!method) return svStatus("Sign an image first", "error");
  const btn = $("#sv-verify-btn");
  btn.disabled = true;
  svStatus("Verifying…");
  try {
    const data = await postJSON("/api/verify", { image_id: id, method });
    svShowResults(data);
    svStatus("Verification complete", "ok");
  } catch (e) {
    svStatus("Verify failed: " + e.message, "error");
  } finally {
    btn.disabled = false;
  }
});

// ── Boot ─────────────────────────────────────────────────────────
initOverview();

window.addEventListener("pagehide", () => {
  if (overviewChart) {
    overviewChart.destroy();
    overviewChart = null;
  }
  if (transformChart) {
    transformChart.destroy();
    transformChart = null;
  }
  if (perImageAbort) perImageAbort.abort();
  if (transformAbort) transformAbort.abort();
});
