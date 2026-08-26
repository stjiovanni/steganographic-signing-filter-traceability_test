import urllib.request
import json
import time
import sys
sys.stdout.reconfigure(encoding='utf-8')

BASE = "http://127.0.0.1:8000"
endpoints = [
    ("GET", "/api/dataset"),
    ("GET", "/api/summary"),
    ("GET", "/api/transforms"),
    ("GET", "/api/trustmark/by_transform?agg=mean"),
    ("GET", "/api/lsb/by_transform?agg=mean"),
    ("GET", "/api/dct/by_transform?agg=mean"),
    ("GET", "/api/hash/by_transform?agg=mean"),
    ("GET", "/api/hash/by_algorithm?transform=brightness&agg=mean"),
    ("GET", "/api/ensemble"),
    ("GET", "/api/ensemble/matrix"),
    ("GET", "/api/image/000000000139"),
    ("GET", "/"),
]

results = []
for method, path in endpoints:
    url = BASE + path
    label = f"{method} {path}"
    try:
        req = urllib.request.Request(url, method=method)
        t0 = time.time()
        resp = urllib.request.urlopen(req, timeout=30)
        elapsed = time.time() - t0
        body = resp.read()
        ct = resp.headers.get("Content-Type", "")
        size = len(body)
        try:
            j = json.loads(body)
            is_json = True
            if isinstance(j, dict):
                detail = f"{len(j)} keys"
            elif isinstance(j, list):
                detail = f"{len(j)} items"
            else:
                detail = type(j).__name__
        except Exception:
            is_json = False
            detail = f"CT={ct}"
        results.append(("✅ OK", label, f"{size} B", detail, f"{elapsed:.2f}s"))
    except Exception as e:
        code = getattr(e, "code", None)
        err_body = ""
        if hasattr(e, "read"):
            try:
                err_body = e.read().decode()[:200]
            except Exception:
                pass
        results.append(("❌ FAIL", label, f"HTTP {code}", err_body or str(e)[:200], ""))

print(f"{'Status':<10} {'Endpoint':<55} {'Size':<12} {'Detail':<30} {'Time'}")
print("-" * 120)
for row in results:
    print(f"{row[0]:<10} {row[1]:<55} {row[2]:<12} {row[3]:<30} {row[4]}")
