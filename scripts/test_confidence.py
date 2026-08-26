"""Exercise the privacy-safe confidence field on /api/verify.

Prefers a live server on 127.0.0.1:8000 (upload -> sign -> verify for all
four methods); if the server is not reachable it falls back to importing
watermark_service directly and sign/verify on a local source image. Either
way the returned dicts are the same shape, and confidence is produced for
every method.

Confidence definition (see watermark_service.CONFIDENCE_DEFINITION):
  * single methods -> bit_accuracy
  * hybrid -> max(trustmark.bit_accuracy, fallback.bit_accuracy), capped
    at 0.5 when neither channel recovers. Deterministic function of the
    measured decode metrics only; carries no identifier.
"""

import json
import os
import sys
import time
import urllib.request
import urllib.error

BASE = "http://127.0.0.1:8000"
LOCAL_IMG = os.path.join("coco_val2017", "val2017", "000000000139.jpg")
METHODS = ["trustmark", "lsb", "dct", "hybrid"]
sys.stdout.reconfigure(encoding="utf-8")


def api_reachable():
    try:
        with urllib.request.urlopen(BASE + "/api/dataset", timeout=3) as resp:
            resp.read()
        return True
    except Exception:
        return False


def api_request(method, path, body=None, form=None):
    url = BASE + path
    data = None
    headers = {}
    if form is not None:
        boundary = "x" * 32
        name = os.path.basename(form)
        with open(form, "rb") as f:
            raw = f.read()
        data = (
            f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{name}\"\r\n"
            f"Content-Type: image/jpeg\r\n\r\n"
        ).encode() + raw + f"\r\n--{boundary}--\r\n".encode()
        headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
    elif body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=180) as resp:
        return json.loads(resp.read().decode())


def run_via_api():
    up = api_request("POST", "/api/upload", form=LOCAL_IMG)
    image_id = up["image_id"]
    print(f"live API  | uploaded image_id={image_id}")
    for m in METHODS:
        sig = api_request("POST", "/api/sign", body={"image_id": image_id, "method": m})
        signed_id = sig["signed_id"]
        ver = api_request("POST", "/api/verify", body={"image_id": signed_id, "method": m})
        _report(m, ver)


def run_direct():
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import watermark_service
    with open(LOCAL_IMG, "rb") as f:
        import tempfile
        fd, tmp = tempfile.mkstemp(suffix=".jpg", dir=watermark_service.PROCESSED_DIR)
        os.close(fd)
        with open(tmp, "wb") as f2:
            f2.write(f.read())
    try:
        print(f"direct unit | source={LOCAL_IMG}")
        for m in METHODS:
            signed = watermark_service.sign_image(tmp, m)
            ver = watermark_service.verify_image(signed["signed_path"], m)
            _report(m, ver)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def _report(m, ver):
    if m == "hybrid":
        print(f"  hybrid : recovered={ver['recovered']} "
              f"tm_acc={ver['trustmark']['bit_accuracy']} "
              f"fb_acc={ver['fallback']['bit_accuracy']} "
              f"confidence={ver['confidence']}")
    else:
        print(f"  {m:9s}: detected={ver['detected']} "
              f"payload={ver['decoded_payload']!r} "
              f"bit_accuracy={ver['bit_accuracy']} "
              f"confidence={ver['confidence']}")
    assert "confidence" in ver, f"missing confidence for {m}"
    assert "confidence_definition" in ver, f"missing confidence_definition for {m}"
    assert 0.0 <= ver["confidence"] <= 1.0, f"confidence out of range for {m}"


def main():
    if api_reachable():
        run_via_api()
        mode = "live /api/verify"
    else:
        run_direct()
        mode = "watermark_service.verify_image (server not running)"
    print(f"PASSED  | confidence produced for {len(METHODS)} methods via {mode}")


if __name__ == "__main__":
    main()