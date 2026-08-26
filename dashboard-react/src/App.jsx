import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { api, previewUrl } from './api.js';

const METHODS = [
  { value: 'hybrid', label: 'Hybrid (TrustMark + Fallback)' },
  { value: 'trustmark', label: 'TrustMark' },
  { value: 'lsb', label: 'LSB' },
  { value: 'dct', label: 'DCT' },
];

// Format a number as a percentage (bit accuracy is a 0..1 fraction).
function pct(value) {
  if (value == null || Number.isNaN(Number(value))) return null;
  return (Number(value) * 100).toFixed(1) + '%';
}

// Resolve the confidence metric: prefer the backend's 'confidence' field
// when present, otherwise fall back to bit_accuracy.
function confidenceOf(item) {
  if (item && item.confidence != null) return item.confidence;
  if (item && item.bit_accuracy != null) return item.bit_accuracy;
  return null;
}

// --- Custom payload capacity & validation ---------------------------
// Limits come from GET /api/payload_capacity (7-bit ASCII chars).

function payloadLimitFor(method, cap) {
  if (!cap) return null;
  if (method === 'hybrid') {
    return cap.hybrid ? cap.hybrid.fallback_max_chars : null;
  }
  const m = cap[method];
  return m ? m.max_chars : null;
}

function payloadHintFor(method, cap) {
  if (!cap) return null;
  const n = payloadLimitFor(method, cap);
  if (n == null) return null;
  return method === 'lsb' || method === 'dct'
    ? `exactly ${n} ASCII chars`
    : `max ${n} ASCII chars`;
}

// Printable 7-bit ASCII (codes 32-127).
function isPrintableAscii(text) {
  return [...text].every((c) => {
    const code = c.codePointAt(0);
    return code >= 32 && code < 127;
  });
}

// Returns an error string, or null when the payload is valid/empty for method.
function payloadError(method, payload, cap) {
  if (!payload) return null;
  if (!isPrintableAscii(payload)) {
    return 'Payload must contain only printable 7-bit ASCII (codes 32-127)';
  }
  const n = payloadLimitFor(method, cap);
  if (n == null) return null;
  const exact = method === 'lsb' || method === 'dct';
  if (exact ? payload.length !== n : payload.length > n) {
    const name = method === 'hybrid' ? 'Hybrid fallback' : method === 'trustmark' ? 'TrustMark' : method.toUpperCase();
    return exact
      ? `${name} payload must be exactly ${n} chars (got ${payload.length})`
      : `${name} payload must be at most ${n} chars (got ${payload.length})`;
  }
  return null;
}

function ResultItem({ label, value, strong }) {
  return (
    <div className="sv-result-item">
      <div className="sv-result-label">{label}</div>
      <div className={`sv-result-value${strong ? ' strong' : ''}`}>{value}</div>
    </div>
  );
}

function PreviewSlot({ label, imageId }) {
  return (
    <div className="sv-preview-slot">
      <div className="sv-preview-label">{label}</div>
      <div className="sv-preview-img">
        {imageId ? (
          <img src={previewUrl(imageId)} alt={label} />
        ) : (
          <span className="sv-placeholder">—</span>
        )}
      </div>
    </div>
  );
}

function ResultsPanel({ result }) {
  if (!result) return null;

  let items;
  if (result.method === 'hybrid') {
    const tm = result.trustmark || {};
    const fb = result.fallback || {};
    const tmConf = confidenceOf(tm);
    const fbConf = confidenceOf(fb);
    items = [
      { label: 'Method', value: 'Hybrid (TrustMark + Fallback)', strong: true },
      { label: 'Two-layer recovery', value: result.recovered ? 'Yes' : 'No' },
      { label: 'TrustMark detected', value: tm.detected ? 'Yes' : 'No' },
      { label: 'TrustMark payload', value: tm.decoded_payload || '—' },
      {
        label: 'TrustMark bit accuracy',
        value: tm.bit_accuracy != null ? pct(tm.bit_accuracy) : '—',
      },
      {
        label: 'TrustMark confidence',
        value: tmConf != null ? pct(tmConf) : '—',
      },
      { label: 'Fallback detected', value: fb.detected ? 'Yes' : 'No' },
      { label: 'Fallback payload', value: fb.decoded_payload || '—' },
      {
        label: 'Fallback bit accuracy',
        value: fb.bit_accuracy != null ? pct(fb.bit_accuracy) : '—',
      },
      {
        label: 'Fallback confidence',
        value: fbConf != null ? pct(fbConf) : '—',
      },
    ];
  } else {
    const conf = confidenceOf(result);
    items = [
      { label: 'Method', value: result.method, strong: true },
      { label: 'Detected', value: result.detected ? 'Yes' : 'No' },
      {
        label: 'Bit Accuracy',
        value: result.bit_accuracy != null ? pct(result.bit_accuracy) : '—',
      },
      { label: 'Payload', value: result.decoded_payload || '—' },
    ];
    if (conf != null) {
      items.push({ label: 'Confidence', value: pct(conf) });
    }
    if (result.schema) {
      items.push({ label: 'Schema', value: result.schema });
    }
  }

  return (
    <div className="card" id="sv-results-card">
      <h2>Verification Results</h2>
      <div className="sv-results-grid">
        {items.map((i) => (
          <ResultItem key={i.label} label={i.label} value={i.value} strong={i.strong} />
        ))}
      </div>
    </div>
  );
}

// --- Detect watermark results table --------------------------------

function detectRow(item) {
  if (item.method === 'hybrid') {
    const tm = item.trustmark || {};
    const fb = item.fallback || {};
    const parts = [];
    if (tm.detected) parts.push(`TM:${tm.decoded_payload}`);
    if (fb.detected) parts.push(`FB:${fb.decoded_payload}`);
    return {
      method: 'Hybrid',
      detected: item.recovered ? 'Yes' : 'No',
      payload: parts.join(' ') || '—',
      bitAccuracy: Math.max(tm.bit_accuracy || 0, fb.bit_accuracy || 0),
      confidence: item.confidence,
      schema: tm.schema || '—',
    };
  }
  return {
    method: item.method,
    detected: item.detected ? 'Yes' : 'No',
    payload: item.decoded_payload || '—',
    bitAccuracy: item.bit_accuracy,
    confidence: item.confidence,
    schema: item.schema || '—',
  };
}

function DetectResultsTable({ result }) {
  if (!result || !Array.isArray(result.results)) return null;
  const rows = result.results.map(detectRow);
  return (
    <div className="card" id="detect-results-card">
      <h2>Detection Results</h2>
      <table className="detect-table">
        <thead>
          <tr>
            <th>Method</th>
            <th>Detected</th>
            <th>Decoded Payload</th>
            <th>Bit Accuracy</th>
            <th>Confidence</th>
            <th>Schema</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.method}>
              <td>{r.method}</td>
              <td>{r.detected}</td>
              <td className="detect-payload">{r.payload}</td>
              <td>{r.bitAccuracy != null ? pct(r.bitAccuracy) : '—'}</td>
              <td>{r.confidence != null ? pct(r.confidence) : '—'}</td>
              <td>{r.schema}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {result.confidence != null && (
        <div className="detect-overall">Overall confidence: {pct(result.confidence)}</div>
      )}
      {result.note && <div className="detect-note">{result.note}</div>}
    </div>
  );
}

export default function App() {
  const [dataset, setDataset] = useState(null);
  const [transforms, setTransforms] = useState([]);
  const [steps, setSteps] = useState({});
  const [transformsError, setTransformsError] = useState(null);

  const [file, setFile] = useState(null);
  const [imageId, setImageId] = useState(null);
  const [filteredId, setFilteredId] = useState(null);
  const [signedId, setSignedId] = useState(null);
  const [signedMethod, setSignedMethod] = useState(null);

  const [transform, setTransform] = useState('');
  const [intensity, setIntensity] = useState('');
  const [method, setMethod] = useState('hybrid');
  const [payload, setPayload] = useState('');
  const [payloadCap, setPayloadCap] = useState(null);

  const [busy, setBusy] = useState(null);
  const [status, setStatus] = useState({ msg: '', type: '' });
  const [verifyResult, setVerifyResult] = useState(null);
  const [stressResult, setStressResult] = useState(null);

  const [mode, setMode] = useState('sign');

  const [detectFile, setDetectFile] = useState(null);
  const [detectImageId, setDetectImageId] = useState(null);
  const [detectResult, setDetectResult] = useState(null);
  const [detectBusy, setDetectBusy] = useState(false);
  const [detectStatus, setDetectStatus] = useState({ msg: '', type: '' });

  const fileInputRef = useRef(null);
  const detectFileInputRef = useRef(null);

  const stepsForTransform = useMemo(
    () => (transform ? steps[transform] || [] : []),
    [transform, steps]
  );

  const loadTransforms = useCallback(async () => {
    try {
      const data = await api.transforms();
      setSteps(data.steps || {});
      const list = data.transforms || [];
      setTransforms(list);
      setTransformsError(null);
      if (list.length) {
        setTransform(list[0]);
      }
    } catch (e) {
      setTransformsError(`Failed to load transforms: ${e.message}`);
    }
  }, []);

  useEffect(() => {
    api.dataset().then(setDataset).catch(() => {});
    loadTransforms();
    api.payloadCapacity().then(setPayloadCap).catch(() => {});
  }, [loadTransforms]);

  // When the transform changes, reset the intensity to the first step.
  useEffect(() => {
    const list = steps[transform] || [];
    if (list.length) {
      setIntensity(String(list[0]));
    } else {
      setIntensity('');
    }
  }, [transform, steps]);

  const updateStatus = (msg, type = '') => setStatus({ msg, type });

  const handleFileChange = (e) => {
    const f = e.target.files && e.target.files[0];
    setFile(f || null);
  };

  const handleUpload = async () => {
    if (!file) return updateStatus('Select a file first', 'error');
    setBusy('upload');
    updateStatus('Uploading…');
    try {
      const data = await api.upload(file);
      setImageId(data.image_id);
      setFilteredId(null);
      setSignedId(null);
      setSignedMethod(null);
      setVerifyResult(null);
      setStressResult(null);
      updateStatus('Uploaded', 'ok');
    } catch (e) {
      updateStatus('Upload failed: ' + e.message, 'error');
    } finally {
      setBusy(null);
    }
  };

  const handleFilter = async () => {
    if (!imageId) return updateStatus('Upload an image first', 'error');
    const list = stepsForTransform;
    if (!list.length) {
      return updateStatus('No intensity steps available for this transform', 'error');
    }
    if (!intensity || !list.includes(intensity)) {
      return updateStatus(`Invalid intensity. Expected one of: ${list.join(', ')}`, 'error');
    }
    setBusy('filter');
    setFilteredId(null);
    updateStatus('Applying filter…');
    try {
      const data = await api.filter(
        imageId,
        transform,
        Number.isNaN(Number(intensity)) ? intensity : Number(intensity)
      );
      setFilteredId(`${data.image_id}_${data.transform}_${data.intensity}`);
      updateStatus('Filter applied', 'ok');
    } catch (e) {
      updateStatus('Filter failed: ' + e.message, 'error');
    } finally {
      setBusy(null);
    }
  };

  const handleSign = async () => {
    const id = filteredId || imageId;
    if (!id) return updateStatus('Upload an image first', 'error');
    if (payload) {
      const err = payloadError(method, payload, payloadCap);
      if (err) return updateStatus(err, 'error');
    }
    setBusy('sign');
    updateStatus('Signing… (hybrid/TrustMark may take a moment)');
    try {
      const data = await api.sign(id, method, payload || undefined);
      setSignedId(data.signed_id);
      setSignedMethod(method);
      setVerifyResult(null);
      updateStatus('Signed successfully', 'ok');
    } catch (e) {
      updateStatus('Sign failed: ' + e.message, 'error');
    } finally {
      setBusy(null);
    }
  };

  const handleVerify = async () => {
    if (!signedId) return updateStatus('Sign an image first', 'error');
    if (!signedMethod) return updateStatus('Sign an image first', 'error');
    setBusy('verify');
    updateStatus('Verifying…');
    try {
      const data = await api.verify(signedId, signedMethod);
      setVerifyResult(data);
      updateStatus('Verification complete', 'ok');
    } catch (e) {
      updateStatus('Verify failed: ' + e.message, 'error');
    } finally {
      setBusy(null);
    }
  };

  const handleStressTest = async () => {
    if (!imageId) return updateStatus('Upload an image first', 'error');
    if (!stepsForTransform.includes(intensity)) {
      return updateStatus(`Invalid intensity. Expected one of: ${stepsForTransform.join(', ')}`, 'error');
    }
    if (payload) {
      const err = payloadError(method, payload, payloadCap);
      if (err) return updateStatus(err, 'error');
    }
    setBusy('stress');
    updateStatus('Running stress test: signing, transforming, then verifying…');
    try {
      const data = await api.stressTest(
        imageId,
        method,
        transform,
        Number.isNaN(Number(intensity)) ? intensity : Number(intensity),
        payload || undefined,
      );
      setStressResult(data);
      updateStatus('Stress test complete', 'ok');
    } catch (e) {
      updateStatus('Stress test failed: ' + e.message, 'error');
    } finally {
      setBusy(null);
    }
  };

  const handleDetectFileChange = (e) => {
    const f = e.target.files && e.target.files[0];
    setDetectFile(f || null);
  };

  const handleDetectUpload = async () => {
    if (!detectFile) return setDetectStatus({ msg: 'Select a file first', type: 'error' });
    setDetectBusy(true);
    setDetectResult(null);
    setDetectStatus({ msg: 'Uploading…', type: '' });
    try {
      const data = await api.upload(detectFile);
      setDetectImageId(data.image_id);
      setDetectStatus({ msg: 'Uploaded. Click Detect to scan.', type: 'ok' });
    } catch (e) {
      setDetectStatus({ msg: 'Upload failed: ' + e.message, type: 'error' });
    } finally {
      setDetectBusy(false);
    }
  };

  const handleDetect = async () => {
    if (!detectImageId) {
      return setDetectStatus({ msg: 'Upload an image first', type: 'error' });
    }
    setDetectBusy(true);
    setDetectResult(null);
    setDetectStatus({ msg: 'Detecting watermark… (TrustMark decode may take a moment)', type: '' });
    try {
      const data = await api.analyze(detectImageId);
      setDetectResult(data);
      setDetectStatus({ msg: 'Detection complete', type: 'ok' });
    } catch (e) {
      setDetectStatus({ msg: 'Detect failed: ' + e.message, type: 'error' });
    } finally {
      setDetectBusy(false);
    }
  };

  const canFilter = Boolean(imageId) && !busy;
  const canSign = Boolean(filteredId || imageId) && !busy;
  const canVerify = Boolean(signedId) && !busy;

  return (
    <div className="app">
      <header>
        <h1>Watermark Sign / Verify</h1>
        {dataset && (
          <div className="dataset-banner">
            Evidence: {dataset.evidence_label} | {dataset.image_count} images,{' '}
            {dataset.transform_count} transforms, {dataset.condition_count} conditions |
            source: {dataset.source}
          </div>
        )}
        <nav className="sv-tabs" aria-label="Modes">
          <button
            type="button"
            className={`sv-tab${mode === 'sign' ? ' active' : ''}`}
            onClick={() => setMode('sign')}
          >
            Sign / Verify
          </button>
          <button
            type="button"
            className={`sv-tab${mode === 'detect' ? ' active' : ''}`}
            onClick={() => setMode('detect')}
          >
            Detect Watermark
          </button>
        </nav>
      </header>

      <main>
        {mode === 'sign' ? (
          <div className="sv-grid">
          <div className="sv-left">
           <div className="card">
              <h2>Upload &amp; Filter</h2>

              <div className="sv-upload-row">
                <label className="sv-file-btn" htmlFor="sv-file-input">
                  Choose Image
                </label>
                <input
                  ref={fileInputRef}
                  type="file"
                  id="sv-file-input"
                  accept="image/*"
                  hidden
                  onChange={handleFileChange}
                />
                <span className="sv-file-name">{file ? file.name : 'No file chosen'}</span>
              </div>
              <button
                className="sv-btn accent"
                onClick={handleUpload}
                disabled={!file || busy === 'upload'}
              >
                {busy === 'upload' ? 'Uploading…' : 'Upload'}
              </button>

              <div className="sv-sep" />

              <label className="sv-label" htmlFor="sv-filter-select">
                Filter
              </label>
              <select
                id="sv-filter-select"
                className="sv-select"
                value={transform}
                onChange={(e) => setTransform(e.target.value)}
                disabled={!transforms.length}
              >
                {transforms.map((t) => (
                  <option key={t} value={t}>
                    {t}
                  </option>
                ))}
              </select>
              {transformsError && <div className="sv-error">{transformsError}</div>}

              <label className="sv-label" htmlFor="sv-intensity-input">
                Intensity
              </label>
              <div className="sv-intensity-row">
                <input
                  type="range"
                  id="sv-intensity-slider"
                  className="sv-slider"
                  aria-label="Intensity slider"
                  min={0}
                  max={Math.max(stepsForTransform.length - 1, 0)}
                  value={stepsForTransform.indexOf(intensity) >= 0 ? stepsForTransform.indexOf(intensity) : 0}
                  onChange={(e) => {
                    const idx = Number(e.target.value);
                    const v = stepsForTransform[idx];
                    if (v !== undefined) setIntensity(String(v));
                  }}
                  disabled={!stepsForTransform.length}
                />
                <input
                  type="text"
                  id="sv-intensity-input"
                  className="sv-intensity-text"
                  value={intensity}
                  onChange={(e) => setIntensity(e.target.value)}
                  aria-label="Intensity value"
                />
              </div>
              <button
                className="sv-btn"
                onClick={handleFilter}
                disabled={!canFilter}
              >
                {busy === 'filter' ? 'Applying…' : 'Apply Filter'}
              </button>

              <div className="sv-sep" />

              <label className="sv-label" htmlFor="sv-method-select">
                Method
              </label>
              <select
                id="sv-method-select"
                className="sv-select"
                value={method}
                onChange={(e) => setMethod(e.target.value)}
                disabled={Boolean(signedMethod)}
              >
                {METHODS.map((m) => (
                  <option key={m.value} value={m.value}>
                    {m.label}
                  </option>
                ))}
              </select>

              <label className="sv-label" htmlFor="sv-payload-input">
                Custom payload (optional)
              </label>
              <input
                type="text"
                id="sv-payload-input"
                className="sv-text-input"
                placeholder="auto"
                value={payload}
                onChange={(e) => setPayload(e.target.value)}
                disabled={Boolean(signedMethod)}
              />
              {payloadHintFor(method, payloadCap) && (
                <div className="sv-payload-hint">
                  {method === 'hybrid' ? 'fallback channel — ' : ''}
                  {payloadHintFor(method, payloadCap)}
                </div>
              )}
              {payload && payloadError(method, payload, payloadCap) && (
                <div className="sv-error">{payloadError(method, payload, payloadCap)}</div>
              )}

              <div className="sv-btn-row">
                <button className="sv-btn accent" onClick={handleSign} disabled={!canSign}>
                  {busy === 'sign' ? 'Signing…' : 'Sign'}
                </button>
                <button className="sv-btn green" onClick={handleVerify} disabled={!canVerify}>
                  {busy === 'verify' ? 'Verifying…' : 'Verify'}
                </button>
              </div>
              <div className="sv-sep" />
              <h2>Live Stress Test</h2>
              <p className="stress-intro">Tests watermark survival after signing. This uses the uploaded original, signs first, transforms the signed output, and verifies that transformed image.</p>
              <button className="sv-btn accent" onClick={handleStressTest} disabled={!imageId || busy}>
                {busy === 'stress' ? 'Running…' : 'Run Stress Test'}
              </button>
              {stressResult && (
                <div className="stress-result">
                  <div className="stress-chain">Signed → Transformed → Verified</div>
                  <div className="stress-result-grid">
                    <ResultItem label="Method" value={stressResult.method} />
                    <ResultItem label="Transform" value={stressResult.transform} />
                    <ResultItem label="Intensity" value={stressResult.intensity} />
                    <ResultItem label="Detected / recovered" value={stressResult.verify.recovered ?? stressResult.verify.detected ? 'Yes' : 'No'} />
                    <ResultItem label="Payload" value={stressResult.verify.decoded_payload || stressResult.verify.fallback?.decoded_payload || '—'} />
                    <ResultItem label="Bit accuracy" value={pct(stressResult.verify.bit_accuracy ?? Math.max(stressResult.verify.trustmark?.bit_accuracy || 0, stressResult.verify.fallback?.bit_accuracy || 0)) || '—'} />
                    <ResultItem label="Confidence" value={pct(stressResult.verify.confidence) || '—'} />
                  </div>
                </div>
              )}
            </div>
          </div>

          <div className="sv-right">
            <div className="card">
              <h2>Preview</h2>
              <div className="sv-preview-grid">
                <PreviewSlot label="Original" imageId={imageId} />
                <PreviewSlot label="Filtered" imageId={filteredId} />
                <PreviewSlot label="Signed" imageId={signedId} />
              </div>
            </div>

            <ResultsPanel result={verifyResult} />
          </div>
        </div>
        ) : (
          <div className="sv-grid">
            <div className="sv-left">
              <div className="card">
                <h2>Detect Watermark</h2>
                <div className="sv-upload-row">
                  <label className="sv-file-btn" htmlFor="detect-file-input">
                    Choose Image
                  </label>
                  <input
                    ref={detectFileInputRef}
                    type="file"
                    id="detect-file-input"
                    accept="image/*"
                    hidden
                    onChange={handleDetectFileChange}
                  />
                  <span className="sv-file-name">
                    {detectFile ? detectFile.name : 'No file chosen'}
                  </span>
                </div>
                <button
                  className="sv-btn accent"
                  onClick={handleDetectUpload}
                  disabled={!detectFile || detectBusy}
                >
                  {detectBusy ? 'Uploading…' : 'Upload'}
                </button>

                <div className="sv-sep" />

                <div className="sv-preview-grid">
                  <PreviewSlot label="Suspect" imageId={detectImageId} />
                </div>

                <div className="sv-btn-row">
                  <button
                    className="sv-btn green"
                    onClick={handleDetect}
                    disabled={!detectImageId || detectBusy}
                  >
                    {detectBusy ? 'Detecting…' : 'Detect Watermark'}
                  </button>
                </div>
                <p className="detect-hint">
                  Uploads the suspect image, then scans it with all four methods
                  (TrustMark, LSB, DCT, hybrid) and reports what each recovers.
                </p>
              </div>
            </div>

            <div className="sv-right">
              <DetectResultsTable result={detectResult} />
            </div>
          </div>
        )}

        <div className={`sv-status${status.type ? ` ${status.type}` : ''}`} role="status" aria-live="polite">
          {status.msg}
        </div>
        {mode === 'detect' && (
          <div className={`sv-status${detectStatus.type ? ` ${detectStatus.type}` : ''}`} role="status" aria-live="polite">
            {detectStatus.msg}
          </div>
        )}
      </main>
    </div>
  );
}
