import logging
import os
import re
import uuid
import tempfile
import statistics
from collections import defaultdict
from typing import Optional, Union, List, Dict, Any

import psycopg2
import psycopg2.extras
from psycopg2 import sql as psql
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from PIL import Image

import transforms
import watermark_service
from csv_store import CSV_DIR, load_rows, rows_for_image

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")

app = FastAPI(title="Watermark Robustness Dashboard")
app.add_middleware(
    CORSMiddleware,
    # Local research tool: the dashboard binds to 127.0.0.1 and CORS is
    # restricted to localhost origins. It is not a deployed service.
    allow_origins=["http://127.0.0.1:8000", "http://localhost:8000"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# --- limits / validation ---

_MAX_UPLOAD_BYTES = 20 * 1024 * 1024
_MAX_IMAGE_PIXELS = 50_000_000
_ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
# Blocks path separators, drive letters, and traversal while allowing
# float intensities (e.g. "1.15") and letterbox values ("black"/"grey").
_SAFE_FILENAME_RE = re.compile(r"^[A-Za-z0-9_.\-]+$")

_HASH_COLS = (
    "image_id, filename, transform_name, intensity_value, pipeline_version, "
    "hash_algorithm, hash_value, hash_ref, hamming_distance, width, height, aspect_ratio"
)
_WATERMARK_COLS = (
    "image_id, filename, transform_name, intensity_value, pipeline_version, "
    "encode_mse, encode_psnr, decode_secret, decode_present, decode_schema, "
    "bit_accuracy, width, height, aspect_ratio, auto_cropped"
)
_ENSEMBLE_COLS = (
    "transform_name, intensity_value, best_method, fallback_method, "
    "hash_ok, trustmark_ok, lsb_ok, dct_ok, notes"
)


def _validate_safe(value: str, field: str) -> str:
    if not value or not _SAFE_FILENAME_RE.match(value):
        raise HTTPException(400, f"Invalid {field}: must match [A-Za-z0-9_.-]+")
    return value


def _conn():
    return psycopg2.connect(DATABASE_URL, connect_timeout=3)


def _query_db(sql, params: tuple = ()) -> List[Dict[str, Any]]:
    try:
        with _conn() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(sql, params)
                return cur.fetchall()
    except psycopg2.OperationalError as exc:
        logger.warning("Database unavailable (%s); falling back to CSV", exc)
        return []


def _by_transform(table: str, pipeline: Optional[str] = None, num_key: str = "intensity_value", val_key: str = "bit_accuracy", agg: str = "mean") -> Dict[str, Dict[str, float]]:
    base = psql.SQL("SELECT transform_name, {num}, {val} FROM {table}").format(
        num=psql.Identifier(num_key), val=psql.Identifier(val_key), table=psql.Identifier(table)
    )
    if pipeline is not None:
        sql = base + psql.SQL(" WHERE transform_name != 'none' AND pipeline = %s")
        params = (pipeline,)
    else:
        sql = base + psql.SQL(" WHERE transform_name != 'none'")
        params = ()

    rows = _query_db(sql, params)
    if not rows:
        if table == "watermark_results" and pipeline == "trustmark":
            rows = load_rows("trustmark")
        elif table == "watermark_results" and pipeline == "lsb":
            rows = load_rows("lsb")
        elif table == "watermark_results" and pipeline == "dct":
            rows = load_rows("dct")
        elif table == "hash_results":
            rows = load_rows("hash")

    t_map = defaultdict(lambda: defaultdict(list))
    for r in rows:
        try:
            intensity = float(r["intensity_value"])
            value = float(r[val_key])
        except (ValueError, TypeError, KeyError):
            continue
        t_map[r["transform_name"]][intensity].append(value)

    result = {}
    for t, by_int in t_map.items():
        ints = sorted(by_int.keys())
        if agg == "mean":
            result[t] = {str(i): sum(by_int[i]) / len(by_int[i]) for i in ints}
        elif agg == "median":
            result[t] = {str(i): statistics.median(by_int[i]) for i in ints}
    return result


def _intensity_sort_key(x):
    if isinstance(x, (int, float)):
        return (0, float(x), "")
    try:
        return (0, float(x), "")
    except (ValueError, TypeError):
        return (1, 0, str(x).replace("black", "z1").replace("grey", "z2"))


def _transforms_from(table: str, pipeline: Optional[str] = None):
    base = psql.SQL("SELECT transform_name, intensity_value FROM {table}").format(
        table=psql.Identifier(table)
    )
    if pipeline is not None:
        sql = base + psql.SQL(" WHERE pipeline = %s")
        params = (pipeline,)
    else:
        sql = base
        params = ()

    rows = _query_db(sql, params)
    if not rows:
        if table == "hash_results":
            rows = load_rows("hash")
        elif table == "watermark_results" and pipeline == "lsb":
            rows = load_rows("lsb")

    t_map = defaultdict(set)
    for r in rows:
        t_map[r["transform_name"]].add(r["intensity_value"])
    transforms = sorted(k for k in t_map if k != "none")
    intensity_map = {
        t: sorted(s, key=_intensity_sort_key)
        for t, s in t_map.items()
        if t != "none"
    }
    return transforms, intensity_map


# --- endpoints ---


@app.get("/api/summary")
def get_summary():
    images = _query_db("SELECT DISTINCT image_id FROM hash_results WHERE transform_name != 'none'")
    if not images:
        images = [r for r in load_rows("hash") if r.get("transform_name") != "none"]
    transforms = _query_db("SELECT DISTINCT transform_name FROM hash_results WHERE transform_name != 'none'")
    if not transforms:
        transforms = [r for r in load_rows("hash") if r.get("transform_name") != "none"]
    hash_algs = _query_db("SELECT DISTINCT hash_algorithm FROM hash_results")
    if not hash_algs:
        hash_algs = load_rows("hash")

    return {
        "image_count": len(set(r["image_id"] for r in images)),
        "transform_count": len(set(r["transform_name"] for r in transforms)),
        "hash_algorithms": sorted(set(r["hash_algorithm"] for r in hash_algs)),
        "transforms": sorted(set(r["transform_name"] for r in transforms)),
    }


@app.get("/api/transforms")
def get_transforms():
    _, tmap_h = _transforms_from("hash_results")
    _, tmap_l = _transforms_from("watermark_results", pipeline="lsb")
    return tmap_h if tmap_h else tmap_l


@app.get("/api/trustmark/by_transform")
def tm_by_transform(agg: str = "mean"):
    return _by_transform("watermark_results", pipeline="trustmark", agg=agg)


@app.get("/api/lsb/by_transform")
def lsb_by_transform(agg: str = "mean"):
    return _by_transform("watermark_results", pipeline="lsb", agg=agg)


@app.get("/api/dct/by_transform")
def dct_by_transform(agg: str = "mean"):
    return _by_transform("watermark_results", pipeline="dct", agg=agg)


@app.get("/api/hash/by_transform")
def hash_by_transform(agg: str = "mean"):
    rows = _query_db("SELECT transform_name, intensity_value, hamming_distance FROM hash_results")
    if not rows:
        rows = load_rows("hash")

    t_map = defaultdict(lambda: defaultdict(list))
    for r in rows:
        try:
            v = float(r["hamming_distance"])
            intensity = float(r["intensity_value"])
        except (ValueError, TypeError, KeyError):
            continue
        t_map[r["transform_name"]][intensity].append(v)

    result = {}
    for t, by_int in t_map.items():
        ints = sorted(by_int.keys())
        if agg == "mean":
            result[t] = {str(i): sum(by_int[i]) / len(by_int[i]) for i in ints}
        elif agg == "median":
            result[t] = {str(i): statistics.median(by_int[i]) for i in ints}
    return result


@app.get("/api/hash/by_algorithm")
def hash_by_algorithm(transform: str = None, agg: str = "mean"):
    rows = _query_db(
        "SELECT hash_algorithm, intensity_value, hamming_distance FROM hash_results"
        + (" WHERE transform_name = %s" if transform else ""),
        (transform,) if transform else (),
    )
    if not rows:
        rows = load_rows("hash")
        if transform:
            rows = [r for r in rows if r.get("transform_name") == transform]

    buckets = defaultdict(lambda: defaultdict(list))
    for r in rows:
        try:
            v = float(r["hamming_distance"])
            i = float(r["intensity_value"])
        except (ValueError, TypeError, KeyError):
            continue
        buckets[r["hash_algorithm"]][i].append(v)

    result = {}
    for alg, t_map in buckets.items():
        ints = sorted(t_map.keys())
        if agg == "mean":
            result[alg] = {str(i): sum(t_map[i]) / len(t_map[i]) for i in ints}
        elif agg == "median":
            result[alg] = {str(i): statistics.median(t_map[i]) for i in ints}
    return result


@app.get("/api/dataset")
def get_dataset():
    rows = load_rows("hash")
    images = {r["image_id"] for r in rows if r.get("transform_name") != "none"}
    transforms_set = {r["transform_name"] for r in rows if r.get("transform_name") != "none"}
    conditions = {f'{r["transform_name"]}:{r["intensity_value"]}' for r in rows
                  if r.get("transform_name") != "none"}
    try:
        db_probe = _conn()
        db_probe.close()
        source = "postgresql"
    except Exception:
        source = "csv"
    evidence_label = "final1200 (validated)" if "final1200" in os.path.normpath(CSV_DIR).replace("\\", "/") else "historical 100-image"
    return {
        "source": source,
        "csv_dir": os.path.normpath(CSV_DIR),
        "evidence_label": evidence_label,
        "image_count": len(images),
        "transform_count": len(transforms_set),
        "condition_count": len(conditions),
    }


@app.get("/api/ensemble")
def get_ensemble():
    rows = _query_db(f"SELECT {_ENSEMBLE_COLS} FROM ensemble_decision_matrix")
    if not rows:
        rows = load_rows("ensemble")
    return rows


@app.get("/api/ensemble/matrix")
def ensemble_matrix():
    transforms, _ = _transforms_from("hash_results")

    rows = _query_db("SELECT transform_name, intensity_value, best_method FROM ensemble_decision_matrix")
    if not rows:
        rows = load_rows("ensemble")

    ints_by_t = {t: [] for t in transforms}
    best = {}
    for r in rows:
        t = r["transform_name"]
        i = r["intensity_value"]
        ints_by_t.setdefault(t, []).append(i)
        best.setdefault(t, {})[i] = r["best_method"]
    return {"transforms": transforms, "intensities": ints_by_t, "best": best}


@app.get("/api/image/{image_id}")
def get_image(image_id: str):
    h = _query_db(f"SELECT {_HASH_COLS} FROM hash_results WHERE image_id = %s", (image_id,))
    t = _query_db(f"SELECT {_WATERMARK_COLS} FROM watermark_results WHERE image_id = %s AND pipeline = 'trustmark'", (image_id,))
    l = _query_db(f"SELECT {_WATERMARK_COLS} FROM watermark_results WHERE image_id = %s AND pipeline = 'lsb'", (image_id,))
    d = _query_db(f"SELECT {_WATERMARK_COLS} FROM watermark_results WHERE image_id = %s AND pipeline = 'dct'", (image_id,))

    if not h:
        h = rows_for_image("hash", image_id)
    if not t:
        t = rows_for_image("trustmark", image_id)
    if not l:
        l = rows_for_image("lsb", image_id)
    if not d:
        d = rows_for_image("dct", image_id)

    return {"hash": h, "trustmark": t, "lsb": l, "dct": d}


# --- sign / verify pipeline endpoints ---


class FilterRequest(BaseModel):
    image_id: str
    transform_name: str
    intensity: Union[float, str]


class SignRequest(BaseModel):
    image_id: str
    method: str
    payload: Optional[str] = None


class VerifyRequest(BaseModel):
    image_id: str
    method: str


class StressTestRequest(BaseModel):
    image_id: str
    method: str
    transform_name: str
    intensity: Union[float, str]
    payload: Optional[str] = None


def _stress_intensity_is_valid(transform_name: str, intensity: Union[float, str]) -> bool:
    for allowed in transforms.TRANSFORM_STEPS[transform_name]:
        if str(allowed) == str(intensity):
            return True
        try:
            if float(allowed) == float(intensity):
                return True
        except (TypeError, ValueError):
            pass
    return False


_STRESS_METHODS = {"trustmark", "lsb", "dct", "hybrid"}


def _validate_stress_request(req: StressTestRequest) -> None:
    """Validate the complete stress-test condition before touching an image."""
    _validate_safe(req.image_id, "image_id")
    _validate_safe(req.method, "method")
    _validate_safe(req.transform_name, "transform_name")
    _validate_safe(str(req.intensity), "intensity")
    if req.method not in _STRESS_METHODS:
        raise HTTPException(400, f"Unknown method: {req.method}")
    if req.transform_name not in transforms.TRANSFORM_STEPS:
        raise HTTPException(400, f"Unknown transform: {req.transform_name}")
    if not _stress_intensity_is_valid(req.transform_name, req.intensity):
        allowed = ", ".join(str(v) for v in transforms.TRANSFORM_STEPS[req.transform_name])
        raise HTTPException(400, f"Invalid intensity for {req.transform_name}; expected one of: {allowed}")


@app.get("/api/transforms/list")
def list_transforms():
    return {
        "transforms": transforms.ALL_TRANSFORMS,
        "steps": {k: [str(s) for s in v] for k, v in transforms.TRANSFORM_STEPS.items()},
    }


@app.post("/api/upload")
async def upload_image(file: UploadFile = File(...)):
    filename = file.filename or ""
    ext = os.path.splitext(filename)[1].lower()
    if ext not in _ALLOWED_EXTENSIONS:
        raise HTTPException(400, "Unsupported file type; allowed: png, jpg, jpeg, webp")
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(400, "File must be an image")

    fd, tmp_path = tempfile.mkstemp(suffix=ext, dir=watermark_service.PROCESSED_DIR)
    size = 0
    try:
        with os.fdopen(fd, "wb") as f:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                size += len(chunk)
                if size > _MAX_UPLOAD_BYTES:
                    raise HTTPException(400, "File too large (max 20MB)")
                f.write(chunk)
        try:
            img = Image.open(tmp_path)
            img.load()
            img = img.convert("RGB")
        except Exception:
            raise HTTPException(400, "Uploaded file is not a valid image")
        if img.width * img.height > _MAX_IMAGE_PIXELS:
            raise HTTPException(400, "Image is too large (max 50 megapixels)")
        image_id = uuid.uuid4().hex[:12]
        dest = os.path.join(watermark_service.UPLOAD_DIR, f"{image_id}{ext}")
        img.save(dest)
        return {
            "image_id": image_id,
            "path": f"/api/preview/{image_id}",
            "filename": filename,
        }
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


@app.post("/api/filter")
def apply_filter(req: FilterRequest):
    _validate_safe(req.image_id, "image_id")
    _validate_safe(req.transform_name, "transform_name")
    _validate_safe(str(req.intensity), "intensity")
    src = _resolve_image(req.image_id)
    try:
        img = Image.open(src).convert("RGB")
    except Exception:
        raise HTTPException(400, "Cannot read source image")
    try:
        result = transforms.apply_transform(img, req.transform_name, req.intensity, image_id=req.image_id)
    except ValueError as e:
        raise HTTPException(400, str(e))
    out_name = f"{req.image_id}_{req.transform_name}_{req.intensity}.png"
    out_path = os.path.join(watermark_service.PROCESSED_DIR, out_name)
    result.save(out_path)
    return {
        "image_id": req.image_id,
        "filtered_path": f"/api/preview/{req.image_id}_{req.transform_name}_{req.intensity}",
        "transform": req.transform_name,
        "intensity": str(req.intensity),
    }


@app.post("/api/sign")
def sign(req: SignRequest):
    src = _resolve_image(req.image_id)
    try:
        meta = watermark_service.sign_image(src, req.method, req.payload)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        print(f"[sign] error: image_id={req.image_id!r} method={req.method!r} exc={e!r}")
        raise HTTPException(500, "Signing failed")
    signed_id = os.path.splitext(os.path.basename(meta["signed_path"]))[0]
    meta.pop("signed_path", None)
    return {"signed_id": signed_id, "preview": f"/api/preview/{signed_id}", **meta}


@app.post("/api/verify")
def verify(req: VerifyRequest):
    src = _resolve_image(req.image_id)
    try:
        result = watermark_service.verify_image(src, req.method)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        print(f"[verify] error: image_id={req.image_id!r} method={req.method!r} exc={e!r}")
        raise HTTPException(500, "Verification failed")
    return result


@app.post("/api/stress_test")
def stress_test(req: StressTestRequest):
    """Sign first, transform the signed image, then verify that transformed image."""
    _validate_stress_request(req)

    src = _resolve_image(req.image_id)
    try:
        # Keep this order explicit: the transform must never be applied to the
        # uploaded source or to an unverified intermediate.
        signed_meta = watermark_service.sign_image(src, req.method, req.payload)
        signed_path = signed_meta["signed_path"]
        signed_id = os.path.splitext(os.path.basename(signed_path))[0]
        with Image.open(signed_path) as signed_image:
            transformed = transforms.apply_transform(
                signed_image.convert("RGB"), req.transform_name, req.intensity, image_id=signed_id
            )
        fd, transformed_path = tempfile.mkstemp(
            prefix=f"{signed_id}_stress_", suffix=".png", dir=watermark_service.PROCESSED_DIR
        )
        os.close(fd)
        transformed.save(transformed_path, format="PNG")
        transformed_id = os.path.splitext(os.path.basename(transformed_path))[0]
        verify_result = watermark_service.verify_image(transformed_path, req.method)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception:
        logger.exception("Stress test failed: image_id=%r", req.image_id)
        raise HTTPException(500, "Stress test failed")

    return {
        "signed_id": signed_id,
        "signed_preview": f"/api/preview/{signed_id}",
        "transformed_id": transformed_id,
        "transformed_preview": f"/api/preview/{transformed_id}",
        "method": req.method,
        "transform": req.transform_name,
        "intensity": str(req.intensity),
        "verification": verify_result,
        "verify": verify_result,
    }


@app.get("/api/payload_capacity")
def payload_capacity():
    """Per-method payload capacities (7-bit ASCII chars) for the UI."""
    return watermark_service.get_payload_capacity()


class AnalyzeRequest(BaseModel):
    image_id: str


@app.post("/api/analyze")
def analyze(req: AnalyzeRequest):
    src = _resolve_image(req.image_id)
    try:
        result = watermark_service.detect_watermarks(src)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        print(f"[analyze] error: image_id={req.image_id!r} exc={e!r}")
        raise HTTPException(500, "Analysis failed")
    return result


@app.get("/api/preview/{image_id}")
def preview_image(image_id: str):
    path = _resolve_image(image_id)
    ext = os.path.splitext(path)[1].lower()
    media_type = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
    }.get(ext, "image/png")
    return FileResponse(path, media_type=media_type)


def _resolve_image(image_id: str) -> str:
    _validate_safe(image_id, "image_id")
    for d in (watermark_service.UPLOAD_DIR, watermark_service.PROCESSED_DIR):
        real_d = os.path.realpath(d)
        prefix = real_d + os.sep
        for f in os.listdir(d):
            if f.startswith(image_id + ".") or f.startswith(image_id + "_"):
                path = os.path.realpath(os.path.join(d, f))
                if path.startswith(prefix):
                    return path
    raise HTTPException(404, f"Image {image_id} not found")


# --- static mounts (order matters: /companion before the "/" catch-all) ---
companion_dir = os.path.join(os.path.dirname(__file__), "study-companion")
if os.path.isdir(companion_dir):
    app.mount("/companion", StaticFiles(directory=companion_dir, html=True), name="companion")

dashboard_dir = os.path.join(os.path.dirname(__file__), "dashboard")
if os.path.isdir(dashboard_dir):
    app.mount("/", StaticFiles(directory=dashboard_dir, html=True), name="dashboard")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
