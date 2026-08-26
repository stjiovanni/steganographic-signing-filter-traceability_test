const API = "";
const COLORS = {
  trustmark: "#ff6b35",
  lsb: "#2ecc71",
  dct: "#3498db",
  hash: "#9b59b6",
  hybrid: "#e91e63",
};

let svTransformsFailed = false;
let stressSteps = {};

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

// ── Dataset banner ───────────────────────────────────────────────
async function initDatasetBanner() {
  try {
    const info = await get("/api/dataset");
    const el = $("#dataset-banner");
    el.textContent = `Evidence: ${info.evidence_label} | ${info.image_count} images, ` +
      `${info.transform_count} transforms, ${info.condition_count} conditions | source: ${info.source}`;
    el.hidden = false;
  } catch (_) {
    // Banner is informational; failure is non-fatal.
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
  let items = [];
  if (data.method === "hybrid") {
    const tm = data.trustmark || {};
    const fb = data.fallback || {};
    items = [
      { label: "Method", value: "Hybrid (TrustMark + Fallback)" },
      { label: "Two-layer recovery", value: data.recovered ? "Yes" : "No" },
      { label: "TrustMark detected", value: tm.detected ? "Yes" : "No" },
      { label: "TrustMark payload", value: tm.decoded_payload || "—" },
      { label: "TrustMark bit accuracy", value: tm.bit_accuracy != null ? (tm.bit_accuracy * 100).toFixed(1) + "%" : "—" },
      { label: "Fallback detected", value: fb.detected ? "Yes" : "No" },
      { label: "Fallback payload", value: fb.decoded_payload || "—" },
      { label: "Fallback bit accuracy", value: fb.bit_accuracy != null ? (fb.bit_accuracy * 100).toFixed(1) + "%" : "—" },
    ];
  } else {
    items = [
      { label: "Method", value: data.method },
      { label: "Detected", value: data.detected ? "Yes" : "No" },
      { label: "Bit Accuracy", value: (data.bit_accuracy * 100).toFixed(1) + "%" },
      { label: "Payload", value: data.decoded_payload || "—" },
    ];
    if (data.schema) {
      items.push({ label: "Schema", value: data.schema });
    }
  }
  grid.innerHTML = items
    .map(
      (i) =>
        `<div class="sv-result-item"><div class="sv-result-label">${i.label}</div><div class="sv-result-value">${i.value}</div></div>`
    )
    .join("");
}

function stressItems(result) {
  if (result.method === "hybrid") {
    const tm = result.trustmark || {}, fb = result.fallback || {};
    return [
      ["Detected / recovered", result.recovered ? "Yes" : "No"],
      ["TrustMark payload", tm.decoded_payload || "—"],
      ["TrustMark bit accuracy", tm.bit_accuracy != null ? (tm.bit_accuracy * 100).toFixed(1) + "%" : "—"],
      ["Fallback payload", fb.decoded_payload || "—"],
      ["Fallback bit accuracy", fb.bit_accuracy != null ? (fb.bit_accuracy * 100).toFixed(1) + "%" : "—"],
      ["Confidence", result.confidence != null ? (result.confidence * 100).toFixed(1) + "%" : "—"],
    ];
  }
  return [
    ["Detected", result.detected ? "Yes" : "No"],
    ["Payload", result.decoded_payload || "—"],
    ["Bit accuracy", result.bit_accuracy != null ? (result.bit_accuracy * 100).toFixed(1) + "%" : "—"],
    ["Confidence", result.confidence != null ? (result.confidence * 100).toFixed(1) + "%" : "—"],
  ];
}

function showStressResult(data) {
  const verify = data.verification || data.verify || {};
  const items = [["Method", data.method], ["Transform", data.transform], ["Intensity", data.intensity], ...stressItems(verify)];
  $("#stress-result").innerHTML = `<div class="stress-chain">Signed → Transformed → Verified</div><div class="stress-result-grid">${items.map(([label, value]) => `<div class="sv-result-item"><div class="sv-result-label">${label}</div><div class="sv-result-value">${value}</div></div>`).join("")}</div>`;
  $("#stress-result").hidden = false;
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
    stressSteps = data.steps;
    const sel = $("#sv-filter-select");
    sel.innerHTML = "";
    data.transforms.forEach((t) => {
      const o = document.createElement("option");
      o.value = t;
      o.textContent = t;
      sel.appendChild(o);
    });
    if (data.transforms.length) svUpdateIntensitySlider();
    const stressSelect = $("#stress-transform");
    stressSelect.innerHTML = "";
    data.transforms.forEach((t) => stressSelect.add(new Option(t, t)));
    updateStressIntensity();
    clearError($("#sv-transforms-error"));
    svTransformsFailed = false;
  } catch (e) {
    svTransformsFailed = true;
    showError($("#sv-transforms-error"), `Failed to load transforms: ${e.message}`);
  }
}

function updateStressIntensity() {
  const transform = $("#stress-transform").value;
  const select = $("#stress-intensity");
  select.innerHTML = "";
  (stressSteps[transform] || []).forEach((value) => select.add(new Option(String(value), String(value))));
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
    $("#stress-run-btn").disabled = false;
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
  svStatus("Signing… (hybrid/TrustMark may take a moment)");
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

$("#stress-transform").addEventListener("change", updateStressIntensity);
$("#stress-run-btn").addEventListener("click", async () => {
  if (!svState.imageId) return svStatus("Upload an image first", "error");
  const btn = $("#stress-run-btn");
  btn.disabled = true;
  svStatus("Running stress test: signing, transforming, then verifying…");
  try {
    const intensity = $("#stress-intensity").value;
    const data = await postJSON("/api/stress_test", {
      image_id: svState.imageId,
      method: $("#stress-method").value,
      transform_name: $("#stress-transform").value,
      intensity: isNaN(Number(intensity)) ? intensity : Number(intensity),
      payload: $("#stress-payload").value || undefined,
    });
    showStressResult(data);
    svShowImage($("#stress-preview-signed"), data.signed_id, "Signed stress-test image");
    svShowImage($("#stress-preview-transformed"), data.transformed_id, "Transformed stress-test image");
    svStatus("Stress test complete", "ok");
  } catch (e) {
    svStatus("Stress test failed: " + e.message, "error");
  } finally {
    btn.disabled = !svState.imageId;
  }
});

// ── Boot ─────────────────────────────────────────────────────────
initDatasetBanner();
svInitTransforms();
