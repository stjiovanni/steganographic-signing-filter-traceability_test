const API = "";
const COLORS = {
  trustmark: "#ff6b35",
  lsb: "#2ecc71",
  dct: "#3498db",
  hash: "#9b59b6",
};
const METHOD_KEYS = ["trustmark", "lsb", "dct"];

let overviewChart = null;
let transformChart = null;

// ── Helpers ──────────────────────────────────────────────────────
async function get(path) {
  const r = await fetch(`${API}${path}`);
  if (!r.ok) throw new Error(`${r.status} ${path}`);
  return r.json();
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
document.querySelectorAll(".tab").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach((t) => t.classList.remove("active"));
    document.querySelectorAll(".tab-panel").forEach((p) => p.classList.remove("active"));
    btn.classList.add("active");
    $(`#tab-${btn.dataset.tab}`).classList.add("active");

    if (btn.dataset.tab === "per-transform" && !$("#transform-select").options.length) {
      initPerTransform();
    }
    if (btn.dataset.tab === "ensemble" && !$("#ensemble-table").rows.length) {
      initEnsemble();
    }
    if (btn.dataset.tab === "per-image" && !$("#image-select").options.length) {
      initPerImage();
    }
  });
});

// ── Chart.js global defaults ─────────────────────────────────────
Chart.defaults.color = "#8888aa";
Chart.defaults.borderColor = "rgba(255,255,255,0.06)";
Chart.defaults.font.family = 'Jost, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, sans-serif';

// ── Overview ─────────────────────────────────────────────────────
async function initOverview() {
  const summary = await get("/api/summary");

  const grid = $("#stats-grid");
  grid.innerHTML = `
    <div class="stat-card"><div class="label">Images</div><div class="value accent">${summary.image_count}</div></div>
    <div class="stat-card"><div class="label">Transforms</div><div class="value green">${summary.transform_count}</div></div>
    <div class="stat-card"><div class="label">Hash Algorithms</div><div class="value purple">${summary.hash_algorithms.length}</div></div>
    <div class="stat-card"><div class="label">Transform Types</div><div class="value blue">${summary.transforms.length}</div></div>
  `;

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
    return 1 - raw / 256;
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
}

// ── Per-Transform ────────────────────────────────────────────────
async function initPerTransform() {
  const transforms = await get("/api/transforms");
  const sel = $("#transform-select");
  const names = Object.keys(transforms).sort();
  names.forEach((n) => {
    const o = document.createElement("option");
    o.value = n;
    o.textContent = n;
    sel.appendChild(o);
  });
  sel.addEventListener("change", () => loadTransformChart(sel.value));
  if (names.length) loadTransformChart(names[0]);
}

async function loadTransformChart(transform) {
  const [tm, ls, dc, hm] = await Promise.all([
    get(`/api/trustmark/by_transform?agg=mean`),
    get(`/api/lsb/by_transform?agg=mean`),
    get(`/api/dct/by_transform?agg=mean`),
    get(`/api/hash/by_algorithm?transform=${encodeURIComponent(transform)}&agg=mean`),
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

  // Hash: invert (1 - hamming/256)
  const hashAlgos = Object.keys(hm);
  const hashData = intensities.map((i) => {
    const vals = hashAlgos.map((a) => hm[a]?.[String(i)]).filter((v) => v != null);
    if (!vals.length) return null;
    const mean = vals.reduce((s, v) => s + v, 0) / vals.length;
    return 1 - mean / 256;
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
        annotation: undefined,
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
}

// ── Ensemble Matrix ──────────────────────────────────────────────
async function initEnsemble() {
  const data = await get("/api/ensemble/matrix");
  const table = $("#ensemble-table");

  const methodColorMap = {
    trustmark: COLORS.trustmark,
    hash: COLORS.hash,
    lsb: COLORS.lsb,
    dct: COLORS.dct,
  };

  let html = "<thead><tr><th>Transform</th>";
  const firstTransform = data.transforms[0];
  const intensities = data.intensities[firstTransform] || [];
  intensities.forEach((i) => {
    html += `<th>${i}</th>`;
  });
  html += "</tr></thead><tbody>";

  data.transforms.forEach((t) => {
    html += `<tr><th>${t}</th>`;
    const tIntensities = data.intensities[t] || [];
    tIntensities.forEach((i) => {
      const key = String(i);
      const entry = data.best[t]?.[key];
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

// ── Boot ─────────────────────────────────────────────────────────
initOverview();
