import csv
import gzip
import os
import threading
from typing import Any, Dict, List

CSV_DIR = os.getenv("CSV_DIR", os.path.join(os.path.dirname(__file__), "output", "results"))

CSV_FILES = {
    "trustmark": "trustmark_robustness_results.csv",
    "lsb": "lsb_robustness_results.csv",
    "dct": "dct_robustness_results.csv",
    "hash": "hash_robustness_results.csv",
    "ensemble": "ensemble_decision_matrix.csv",
}

NUMERIC_COLS = frozenset({
    "intensity_value", "encode_mse", "encode_psnr", "bit_accuracy",
    "hamming_distance", "width", "height", "aspect_ratio",
})
BOOL_COLS = frozenset({
    "decode_present", "auto_cropped", "hash_ok", "trustmark_ok", "lsb_ok", "dct_ok",
})

_lock = threading.Lock()
_rows_cache: Dict[str, List[Dict[str, Any]]] = {}
_index_cache: Dict[str, Dict[str, List[Dict[str, Any]]]] = {}


def _coerce_row(row: Dict[str, Any]) -> Dict[str, Any]:
    for col in NUMERIC_COLS:
        if col in row and row[col] not in (None, ""):
            try:
                row[col] = float(row[col])
            except ValueError:
                pass
    for col in BOOL_COLS:
        if col in row:
            row[col] = str(row[col]).strip().lower() in ("true", "1", "yes")
    return row


def _open_text(path: str):
    if os.path.exists(path):
        return open(path, "r", encoding="utf-8")
    gz_path = path + ".gz"
    if os.path.exists(gz_path):
        return gzip.open(gz_path, "rt", encoding="utf-8")
    return None


def load_rows(key: str) -> List[Dict[str, Any]]:
    rows = _rows_cache.get(key)
    if rows is not None:
        return rows
    with _lock:
        rows = _rows_cache.get(key)
        if rows is not None:
            return rows
        rows = []
        f = _open_text(os.path.join(CSV_DIR, CSV_FILES[key]))
        if f is not None:
            with f:
                for row in csv.DictReader(f):
                    rows.append(_coerce_row(row))
        _rows_cache[key] = rows
        return rows


def rows_for_image(key: str, image_id: str) -> List[Dict[str, Any]]:
    index = _index_cache.get(key)
    if index is None:
        with _lock:
            index = _index_cache.get(key)
            if index is None:
                index = {}
                for row in load_rows(key):
                    index.setdefault(row.get("image_id"), []).append(row)
                _index_cache[key] = index
    return index.get(image_id, [])
