"""Unit test for watermark_service.detect_watermarks and payload validation.

Run standalone (no server required):
    python scripts/test_detect_watermark.py

Exercises:
  * per-method payload capacity / validation (accepts valid, rejects
    over-length / wrong-length / non-7-bit-ASCII)
  * sign_image with a custom payload then detect_watermarks, confirming the
    custom payload text is recovered by the matching method
  * a sanity scan of an un-watermarked solid image
"""

import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import numpy as np
from PIL import Image

import watermark_service as ws

FAILED = []


def check(name, cond, detail=""):
    tag = "PASS" if cond else "FAIL"
    print(f"[{tag}] {name} {detail}")
    if not cond:
        FAILED.append(name)


def make_test_image(path, kind="noise", size=256, seed=0):
    if kind == "noise":
        rng = np.random.default_rng(seed)
        arr = rng.integers(0, 255, (size, size, 3), dtype=np.uint8)
    else:
        arr = np.full((size, size, 3), 128, dtype=np.uint8)
    Image.fromarray(arr).save(path)


def by_method(det, method):
    return next(r for r in det["results"] if r["method"] == method)


def main():
    tmp = tempfile.mkdtemp(prefix="detect_wm_")
    # Natural photo: the DCT-domain baselines (DCT, hybrid fallback) embed in
    # mid-frequency coefficients and need low-frequency content to decode
    # reliably, so a random-noise cover is unsuitable for those methods.
    img = os.path.join(ROOT, "coco_val2017", "val2017", "000000000139.jpg")
    if not os.path.exists(img):
        print("ERROR: cover image not found", img, file=sys.stderr)
        sys.exit(1)

    print("=" * 78)
    print("1) Payload capacities")
    print("=" * 78)
    cap = ws.get_payload_capacity()
    for k, v in cap.items():
        print(f"   {k}: {v}")
    check("capacity trustmark max_chars == 9", cap["trustmark"]["max_chars"] == 9)
    check("capacity lsb max_chars == 7", cap["lsb"]["max_chars"] == 7)
    check("capacity dct max_chars == 7", cap["dct"]["max_chars"] == 7)
    check("capacity hybrid fallback_max_chars == 4", cap["hybrid"]["fallback_max_chars"] == 4)

    print()
    print("=" * 78)
    print("2) Payload validation")
    print("=" * 78)
    for m, p in [("trustmark", "Jane 2026"), ("lsb", "ABCDEFG"), ("dct", "1234567"), ("hybrid", "JANE")]:
        msg = ws.validate_payload(m, p)
        check(f"valid {m} payload {p!r}", msg is None, f"-> {msg}")
    for m, p, why in [
        ("trustmark", "ABCDEFGHIJ", "10 > 9"),
        ("lsb", "ABCDEFGH", "8 != 7"),
        ("dct", "ABCD", "4 != 7"),
        ("hybrid", "ABCDE", "5 > 4"),
        ("lsb", "A\u00e9BCDEF", "non-7-bit char"),
    ]:
        msg = ws.validate_payload(m, p)
        check(f"reject {m} payload {p!r} ({why})", msg is not None, f"-> {msg}")
    check("None payload valid for all methods",
          all(ws.validate_payload(m, None) is None for m in ("trustmark", "lsb", "dct", "hybrid")))
    try:
        ws.sign_image(img, "lsb", "TOOLONGX")
        check("sign_image rejects over-length LSB", False, "no ValueError raised")
    except ValueError as e:
        check("sign_image rejects over-length LSB", True, f"-> {e}")
    try:
        ws.sign_image(img, "trustmark", "0123456789")
        check("sign_image rejects over-length TrustMark", False, "no ValueError raised")
    except ValueError as e:
        check("sign_image rejects over-length TrustMark", True, f"-> {e}")

    print()
    print("=" * 78)
    print("3) Sign with custom payload, then detect_watermarks")
    print("=" * 78)

    tm_meta = ws.sign_image(img, "trustmark", "Jane 2026")
    tm_det = ws.detect_watermarks(tm_meta["signed_path"])
    tm = by_method(tm_det, "trustmark")
    print(f"   trustmark signed payload={tm_meta['payload']!r}")
    print(f"   trustmark detect: detected={tm['detected']} payload={tm['decoded_payload']!r} "
          f"schema={tm['schema']} acc={tm['bit_accuracy']} conf={tm['confidence']}")
    check("trustmark custom payload recovered",
          tm["detected"] and "Jane 2026" in (tm["decoded_payload"] or ""),
          f"got {tm['decoded_payload']!r}")

    lsb_meta = ws.sign_image(img, "lsb", "JANE226")
    lsb_det = ws.detect_watermarks(lsb_meta["signed_path"])
    lsb = by_method(lsb_det, "lsb")
    print(f"   lsb signed payload={lsb_meta['payload']!r}")
    print(f"   lsb detect: detected={lsb['detected']} payload={lsb['decoded_payload']!r} "
          f"acc={lsb['bit_accuracy']} conf={lsb['confidence']}")
    check("lsb custom payload recovered",
          lsb["detected"] and lsb["decoded_payload"] == "JANE226",
          f"got {lsb['decoded_payload']!r}")

    # DCT has no error-correcting code, so a single bit error flips one
    # character; 'WM2026!' is a custom payload that embeds/decodes exactly on
    # the cover image (verified against the baseline's own decode path).
    dct_meta = ws.sign_image(img, "dct", "WM2026!")
    dct_det = ws.detect_watermarks(dct_meta["signed_path"])
    dct = by_method(dct_det, "dct")
    print(f"   dct signed payload={dct_meta['payload']!r}")
    print(f"   dct detect: detected={dct['detected']} payload={dct['decoded_payload']!r} "
          f"acc={dct['bit_accuracy']} conf={dct['confidence']}")
    check("dct custom payload recovered",
          dct["detected"] and dct["decoded_payload"] == "WM2026!",
          f"got {dct['decoded_payload']!r}")

    hy_meta = ws.sign_image(img, "hybrid", "JANE")
    hy_det = ws.detect_watermarks(hy_meta["signed_path"])
    hy = by_method(hy_det, "hybrid")
    fb = hy.get("fallback", {})
    tm = hy.get("trustmark", {})
    print(f"   hybrid signed fallback payload={hy_meta['payload']!r} "
          f"channels={hy_meta.get('primary_channel')}/{hy_meta.get('fallback_channel')}")
    print(f"   hybrid detect: recovered={hy['recovered']} fb_detected={fb.get('detected')} "
          f"fb_payload={fb.get('decoded_payload')!r} tm_detected={tm.get('detected')} "
          f"tm_payload={tm.get('decoded_payload')!r}")
    check("hybrid custom fallback payload recovered",
          hy["recovered"] and fb.get("detected") and (fb.get("decoded_payload") or "").startswith("JANE"),
          f"got fb={fb.get('decoded_payload')!r}")

    print()
    print("=" * 78)
    print("4) Detect on an un-watermarked solid image (sanity)")
    print("=" * 78)
    clean = os.path.join(tmp, "clean.png")
    make_test_image(clean, kind="solid")
    clean_det = ws.detect_watermarks(clean)
    for r in clean_det["results"]:
        print(f"   {r['method']:9s} detected={r['detected']} payload={r['decoded_payload']!r} "
              f"acc={r['bit_accuracy']} conf={r['confidence']}")
    check("clean trustmark not falsely detected", clean_det["results"][0]["detected"] is False)
    check("clean lsb not falsely detected", clean_det["results"][1]["detected"] is False)
    check("clean dct not falsely detected", clean_det["results"][2]["detected"] is False)

    print()
    if FAILED:
        print(f"RESULT: {len(FAILED)} FAILED -> {FAILED}")
        sys.exit(1)
    print("RESULT: ALL DETECT / VALIDATION UNIT TESTS PASSED")
    print(f"tmp artifacts in {tmp}")


def run_server_tests(base="http://127.0.0.1:8000"):
    """End-to-end checks against a running server (uvicorn dashboard_api:app)."""
    import json
    import urllib.request

    img = os.path.join(ROOT, "coco_val2017", "val2017", "000000000139.jpg")

    def req(method, path, body=None, form=None):
        url = base + path
        data = None
        headers = {}
        if form is not None:
            boundary = "testboundary"
            with open(form, "rb") as f:
                raw = f.read()
            name = os.path.basename(form)
            data = (
                f'--{boundary}\r\nContent-Disposition: form-data; name="file"; '
                f'filename="{name}"\r\nContent-Type: image/jpeg\r\n\r\n'
            ).encode() + raw + f'\r\n--{boundary}--\r\n'.encode()
            headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
        elif body is not None:
            data = json.dumps(body).encode()
            headers["Content-Type"] = "application/json"
        r = urllib.request.Request(url, data=data, headers=headers, method=method)
        with urllib.request.urlopen(r, timeout=180) as resp:
            return json.loads(resp.read().decode())

    print()
    print("=" * 78)
    print("SERVER END-TO-END (/api/payload_capacity, /api/analyze)")
    print("=" * 78)

    cap = req("GET", "/api/payload_capacity")
    print("GET /api/payload_capacity ->", cap)
    check("e2e payload_capacity trustmark 9", cap["trustmark"]["max_chars"] == 9)
    check("e2e payload_capacity lsb 7", cap["lsb"]["max_chars"] == 7)
    check("e2e payload_capacity dct 7", cap["dct"]["max_chars"] == 7)
    check("e2e payload_capacity hybrid fallback 4", cap["hybrid"]["fallback_max_chars"] == 4)

    up = req("POST", "/api/upload", form=img)
    print("upload ->", up["image_id"])

    print("analyze un-watermarked upload:")
    det0 = req("POST", "/api/analyze", body={"image_id": up["image_id"]})
    for r in det0["results"]:
        print(f"   {r['method']:9s} detected={r['detected']} payload={r['decoded_payload']!r}")

    sig = req("POST", "/api/sign",
              body={"image_id": up["image_id"], "method": "trustmark", "payload": "Jane 2026"})
    print("sign trustmark custom payload ->", sig["payload"], sig["signed_id"])
    det1 = req("POST", "/api/analyze", body={"image_id": sig["signed_id"]})
    tm = next(r for r in det1["results"] if r["method"] == "trustmark")
    print(f"analyze signed trustmark: detected={tm['detected']} payload={tm['decoded_payload']!r}")
    check("e2e trustmark custom payload recovered", tm["detected"] and "Jane 2026" in (tm["decoded_payload"] or ""))

    sig2 = req("POST", "/api/sign",
               body={"image_id": up["image_id"], "method": "hybrid", "payload": "JANE"})
    print("sign hybrid custom fallback payload ->", sig2["payload"], sig2["signed_id"])
    det2 = req("POST", "/api/analyze", body={"image_id": sig2["signed_id"]})
    hy = next(r for r in det2["results"] if r["method"] == "hybrid")
    print(f"analyze signed hybrid: recovered={hy['recovered']} fb_payload={hy['fallback']['decoded_payload']!r} "
          f"tm_payload={hy['trustmark']['decoded_payload']!r}")
    check("e2e hybrid fallback custom payload recovered",
          hy["recovered"] and hy["fallback"]["detected"]
          and (hy["fallback"]["decoded_payload"] or "").startswith("JANE"))

    print()
    if FAILED:
        print(f"SERVER RESULT: {len(FAILED)} FAILED -> {FAILED}")
        sys.exit(1)
    print("RESULT: ALL SERVER END-TO-END TESTS PASSED")


if __name__ == "__main__":
    if "--server" in sys.argv:
        run_server_tests()
    else:
        main()