// Thin client for the FastAPI backend. The request/response shapes match
// dashboard_api.py exactly. /api is proxied to http://127.0.0.1:8000 in dev.

async function readError(r) {
  try {
    const body = await r.json();
    if (body && body.detail) {
      return typeof body.detail === 'string'
        ? body.detail
        : JSON.stringify(body.detail);
    }
    return r.statusText;
  } catch (_) {
    return r.statusText || `HTTP ${r.status}`;
  }
}

async function get(path) {
  const r = await fetch(path);
  if (!r.ok) throw new Error(await readError(r));
  return r.json();
}

async function postForm(path, fd) {
  const r = await fetch(path, { method: 'POST', body: fd });
  if (!r.ok) throw new Error(await readError(r));
  return r.json();
}

async function postJSON(path, body) {
  const r = await fetch(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!r.ok) throw new Error(await readError(r));
  return r.json();
}

export function previewUrl(imageId) {
  return `/api/preview/${imageId}`;
}

export const api = {
  // GET /api/dataset
  dataset: () => get('/api/dataset'),
  // GET /api/transforms/list -> { transforms, steps }
  transforms: () => get('/api/transforms/list'),
  // POST /api/upload (multipart, field "file")
  upload: (file) => {
    const fd = new FormData();
    fd.append('file', file);
    return postForm('/api/upload', fd);
  },
  // POST /api/filter { image_id, transform_name, intensity }
  filter: (imageId, transformName, intensity) =>
    postJSON('/api/filter', {
      image_id: imageId,
      transform_name: transformName,
      intensity,
    }),
  // POST /api/sign { image_id, method, payload? }
  sign: (imageId, method, payload) =>
    postJSON('/api/sign', { image_id: imageId, method, payload }),
  // POST /api/verify { image_id, method }
  verify: (imageId, method) =>
    postJSON('/api/verify', { image_id: imageId, method }),
  // POST /api/stress_test: sign -> transform signed output -> verify
  stressTest: (imageId, method, transformName, intensity, payload) =>
    postJSON('/api/stress_test', {
      image_id: imageId,
      method,
      transform_name: transformName,
      intensity,
      payload,
    }),
  // GET /api/payload_capacity -> per-method payload capacities
  payloadCapacity: () => get('/api/payload_capacity'),
  // POST /api/analyze { image_id } -> per-method watermark detection
  analyze: (imageId) => postJSON('/api/analyze', { image_id: imageId }),
};
