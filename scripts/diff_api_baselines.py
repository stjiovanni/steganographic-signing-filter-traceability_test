"""Diff live API responses against the pre-optimisation baselines in
evidence/perf_baseline/. Parsed-object equality (formatting ignored)."""

import json
import sys
import urllib.request

BASE = "http://127.0.0.1:8000"
BASELINE_DIR = "evidence/perf_baseline"
ENDPOINTS = {
    "_api_image_000000000139.json": "/api/image/000000000139",
    "_api_trustmark_by_transform_agg_mean.json": "/api/trustmark/by_transform?agg=mean",
    "_api_dataset.json": "/api/dataset",
    "_api_hash_by_algorithm_transform_brightn.json": "/api/hash/by_algorithm?transform=brightness&agg=mean",
    "_api_ensemble_matrix.json": "/api/ensemble/matrix",
}
sys.stdout.reconfigure(encoding="utf-8")

all_ok = True
for fname, ep in ENDPOINTS.items():
    with open(f"{BASELINE_DIR}/{fname}", encoding="utf-8") as f:
        baseline = json.load(f)
    with urllib.request.urlopen(BASE + ep, timeout=180) as resp:
        live = json.loads(resp.read().decode())
    ok = baseline == live
    all_ok &= ok
    print(("PASS  " if ok else "DIFF  ") + ep)
    if not ok:
        if isinstance(baseline, list) and isinstance(live, list):
            print(f"  baseline rows={len(baseline)} live rows={len(live)}")
        for k in set(list(baseline.keys() if isinstance(baseline, dict) else []) +
                     list(live.keys() if isinstance(live, dict) else [])):
            b = baseline.get(k) if isinstance(baseline, dict) else None
            l = live.get(k) if isinstance(live, dict) else None
            if b != l:
                print(f"  differing key: {k}")

print("\nRESULT:", "ALL RESPONSES MATCH BASELINES" if all_ok else "DIFFERENCES FOUND")