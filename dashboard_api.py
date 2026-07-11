import os
from collections import defaultdict

import psycopg2
import psycopg2.extras
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/msc_proj",
)

app = FastAPI(title="Watermark Robustness Dashboard")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _conn():
    return psycopg2.connect(DATABASE_URL)


# --- helpers ---


def _by_transform(table, pipeline=None, num_key="intensity_value", val_key="bit_accuracy", agg="mean"):
    """Generic aggregation: group by transform_name → intensity_value → aggregate(val_key)."""
    if pipeline is not None:
        sql = f"""
            SELECT transform_name, intensity_value, {val_key}
            FROM {table}
            WHERE transform_name != 'none' AND pipeline = %s
        """
        params = (pipeline,)
    else:
        sql = f"""
            SELECT transform_name, intensity_value, {val_key}
            FROM {table}
            WHERE transform_name != 'none'
        """
        params = ()

    with _conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()

    t_map = defaultdict(lambda: defaultdict(list))
    for r in rows:
        try:
            intensity = float(r["intensity_value"])
            value = float(r[val_key])
        except (ValueError, TypeError):
            continue
        t_map[r["transform_name"]][intensity].append(value)

    result = {}
    for t, by_int in t_map.items():
        ints = sorted(by_int.keys())
        if agg == "mean":
            result[t] = {str(i): sum(by_int[i]) / len(by_int[i]) for i in ints}
        elif agg == "median":
            import statistics
            result[t] = {str(i): statistics.median(by_int[i]) for i in ints}
    return result


def _transforms_from(table, pipeline=None):
    """Return (sorted_transform_names, {transform: sorted_intensities})."""
    if pipeline is not None:
        sql = f"SELECT transform_name, intensity_value FROM {table} WHERE pipeline = %s"
        params = (pipeline,)
    else:
        sql = f"SELECT transform_name, intensity_value FROM {table}"
        params = ()

    with _conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()

    t_map = defaultdict(set)
    for r in rows:
        t_map[r["transform_name"]].add(r["intensity_value"])
    transforms = sorted(k for k in t_map if k != "none")
    intensity_map = {
        t: sorted(s, key=lambda x: (x.replace("black", "z1").replace("grey", "z2")))
        for t, s in t_map.items()
        if t != "none"
    }
    return transforms, intensity_map


# --- endpoints ---


@app.get("/api/summary")
def get_summary():
    with _conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT DISTINCT image_id FROM hash_results WHERE transform_name != 'none'"
            )
            images = [r["image_id"] for r in cur.fetchall()]

            cur.execute(
                "SELECT DISTINCT transform_name FROM hash_results WHERE transform_name != 'none'"
            )
            transforms = [r["transform_name"] for r in cur.fetchall()]

            cur.execute("SELECT DISTINCT hash_algorithm FROM hash_results")
            hash_algs = [r["hash_algorithm"] for r in cur.fetchall()]

    return {
        "image_count": len(images),
        "transform_count": len(transforms),
        "hash_algorithms": sorted(hash_algs),
        "transforms": sorted(transforms),
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
    with _conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                SELECT transform_name, intensity_value, hamming_distance
                FROM hash_results
                """
            )
            rows = cur.fetchall()

    t_map = defaultdict(lambda: defaultdict(list))
    for r in rows:
        try:
            v = float(r["hamming_distance"])
            intensity = float(r["intensity_value"])
        except (ValueError, TypeError):
            continue
        t_map[r["transform_name"]][intensity].append(v)

    result = {}
    for t, by_int in t_map.items():
        ints = sorted(by_int.keys())
        if agg == "mean":
            result[t] = {str(i): sum(by_int[i]) / len(by_int[i]) for i in ints}
    return result


@app.get("/api/hash/by_algorithm")
def hash_by_algorithm(transform: str = None, agg: str = "mean"):
    with _conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT DISTINCT hash_algorithm FROM hash_results")
            algs = [r["hash_algorithm"] for r in cur.fetchall()]

    result = {}
    for alg in algs:
        with _conn() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                if transform:
                    cur.execute(
                        """
                        SELECT intensity_value, hamming_distance
                        FROM hash_results
                        WHERE hash_algorithm = %s AND transform_name = %s
                        """,
                        (alg, transform),
                    )
                else:
                    cur.execute(
                        """
                        SELECT intensity_value, hamming_distance
                        FROM hash_results
                        WHERE hash_algorithm = %s
                        """,
                        (alg,),
                    )
                rows = cur.fetchall()

        t_map = defaultdict(list)
        for r in rows:
            try:
                v = float(r["hamming_distance"])
                i = float(r["intensity_value"])
            except (ValueError, TypeError):
                continue
            t_map[i].append(v)

        ints = sorted(t_map.keys())
        if agg == "mean":
            result[alg] = {str(i): sum(t_map[i]) / len(t_map[i]) for i in ints}
    return result


@app.get("/api/ensemble")
def get_ensemble():
    with _conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM ensemble_decision_matrix")
            return cur.fetchall()


@app.get("/api/ensemble/matrix")
def ensemble_matrix():
    transforms, _ = _transforms_from("hash_results")

    with _conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT transform_name, intensity_value, best_method FROM ensemble_decision_matrix")
            rows = cur.fetchall()

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
    with _conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM hash_results WHERE image_id = %s", (image_id,))
            h = cur.fetchall()
            cur.execute(
                "SELECT * FROM watermark_results WHERE image_id = %s AND pipeline = 'trustmark'",
                (image_id,),
            )
            t = cur.fetchall()
            cur.execute(
                "SELECT * FROM watermark_results WHERE image_id = %s AND pipeline = 'lsb'",
                (image_id,),
            )
            l = cur.fetchall()
            cur.execute(
                "SELECT * FROM watermark_results WHERE image_id = %s AND pipeline = 'dct'",
                (image_id,),
            )
            d = cur.fetchall()
    return {"hash": h, "trustmark": t, "lsb": l, "dct": d}


# --- static dashboard ---
dashboard_dir = os.path.join(os.path.dirname(__file__), "dashboard")
if os.path.isdir(dashboard_dir):
    app.mount("/", StaticFiles(directory=dashboard_dir, html=True), name="dashboard")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
