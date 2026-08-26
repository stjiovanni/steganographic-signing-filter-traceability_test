"""Exercise the running dashboard API with real watermark implementations."""

import json
import mimetypes
import os
import urllib.request
import urllib.error
import uuid


BASE = os.environ.get("STRESS_TEST_BASE", "http://127.0.0.1:8000")
IMAGE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output", "uploads", "1250efd7fc5c.jpg")


def request(path, body=None, image_path=None):
    headers = {}
    if image_path:
        boundary = uuid.uuid4().hex
        with open(image_path, "rb") as image:
            raw = image.read()
        name = os.path.basename(image_path)
        data = (
            f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{name}\"\r\n"
            f"Content-Type: {mimetypes.guess_type(name)[0] or 'application/octet-stream'}\r\n\r\n"
        ).encode() + raw + f"\r\n--{boundary}--\r\n".encode()
        headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
    else:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(BASE + path, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=300) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as error:
        detail = error.read().decode(errors="replace")
        raise RuntimeError(f"HTTP {error.code} for {path}: {detail}") from error


def run(method, image_id):
    result = request(
        "/api/stress_test",
        {
            "image_id": image_id,
            "method": method,
            "transform_name": "jpeg_compression",
            "intensity": 80,
        },
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    assert result["signed_id"]
    assert result["transformed_id"]
    assert result["method"] == method
    assert result["transform"] == "jpeg_compression"
    assert result["intensity"] in {"80", "80.0"}
    assert result["verification"] == result["verify"]
    return result


if __name__ == "__main__":
    uploaded = request("/api/upload", image_path=IMAGE)
    print("UPLOAD")
    print(json.dumps(uploaded, indent=2, sort_keys=True))
    print("TRUSTMARK_JPEG")
    run("trustmark", uploaded["image_id"])
    print("HYBRID_JPEG")
    run("hybrid", uploaded["image_id"])
    print("LIVE STRESS TESTS PASSED")
