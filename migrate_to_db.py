"""Load the validated final1200 evidence into PostgreSQL.

Tables: hash_results, watermark_results (pipeline column), ensemble_decision_matrix,
fallback_results (two-layer fallback channel). Batched inserts (execute_values +
itertools.islice) keep memory bounded and load the 768k-row hash file quickly.
"""

import csv
import gzip
import itertools
import os
import sys

import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import execute_values

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output", "results", "final1200")
BATCH = 10_000


def _open(name):
    path = os.path.join(RESULTS_DIR, name)
    if os.path.exists(path + ".gz"):
        return gzip.open(path + ".gz", "rt", newline="", encoding="utf-8")
    return open(path, newline="", encoding="utf-8")


def parse_bool(val):
    if val is None:
        return False
    return str(val).strip().lower() == "true"


def sanitize(val):
    return None if val is None else str(val).replace("\x00", "")


def _num(val):
    try:
        return float(val) if val not in (None, "") else None
    except ValueError:
        return None


def _int(val):
    try:
        return int(float(val)) if val not in (None, "") else None
    except ValueError:
        return None


def create_tables(conn):
    cur = conn.cursor()
    cur.execute("""
        DROP TABLE IF EXISTS hash_results CASCADE;
        DROP TABLE IF EXISTS watermark_results CASCADE;
        DROP TABLE IF EXISTS ensemble_decision_matrix CASCADE;
        DROP TABLE IF EXISTS fallback_results CASCADE;

        CREATE TABLE hash_results (
            id SERIAL PRIMARY KEY,
            image_id VARCHAR(50),
            filename VARCHAR(255),
            transform_name VARCHAR(50),
            intensity_value VARCHAR(20),
            pipeline_version VARCHAR(20),
            hash_algorithm VARCHAR(50),
            hash_value TEXT,
            hash_ref TEXT,
            hamming_distance DOUBLE PRECISION,
            width INTEGER,
            height INTEGER,
            aspect_ratio DOUBLE PRECISION
        );

        CREATE TABLE watermark_results (
            id SERIAL PRIMARY KEY,
            pipeline VARCHAR(20) NOT NULL,
            image_id VARCHAR(50),
            filename VARCHAR(255),
            transform_name VARCHAR(50),
            intensity_value VARCHAR(20),
            pipeline_version VARCHAR(20),
            encode_mse DOUBLE PRECISION,
            encode_psnr DOUBLE PRECISION,
            decode_secret TEXT,
            decode_present BOOLEAN,
            decode_schema VARCHAR(20),
            bit_accuracy DOUBLE PRECISION,
            width INTEGER,
            height INTEGER,
            aspect_ratio DOUBLE PRECISION,
            auto_cropped BOOLEAN
        );

        CREATE TABLE fallback_results (
            id SERIAL PRIMARY KEY,
            image_id VARCHAR(50),
            filename VARCHAR(255),
            transform_name VARCHAR(50),
            intensity_value VARCHAR(20),
            pipeline_version VARCHAR(20),
            encode_mse DOUBLE PRECISION,
            encode_psnr DOUBLE PRECISION,
            fb_decode_secret TEXT,
            fb_decode_present BOOLEAN,
            fb_bit_accuracy DOUBLE PRECISION,
            tm_combined_baseline_present BOOLEAN,
            width INTEGER,
            height INTEGER,
            aspect_ratio DOUBLE PRECISION
        );

        CREATE TABLE ensemble_decision_matrix (
            id SERIAL PRIMARY KEY,
            transform_name VARCHAR(50),
            intensity_value VARCHAR(20),
            best_method VARCHAR(50),
            fallback_method VARCHAR(50),
            hash_ok BOOLEAN,
            trustmark_ok BOOLEAN,
            lsb_ok BOOLEAN,
            dct_ok BOOLEAN,
            notes TEXT
        );
    """)
    conn.commit()
    print("[OK] Tables created.", flush=True)


def _load(cur, sql_template, row_iter, label, conn):
    count = 0
    while True:
        chunk = list(itertools.islice(row_iter, BATCH))
        if not chunk:
            break
        execute_values(cur, sql_template, chunk, page_size=BATCH)
        count += len(chunk)
        print(f"  {label}: {count} rows...", flush=True)
    conn.commit()
    print(f"[OK] {label}: {count} rows inserted.", flush=True)


def load_hash_results(conn):
    cur = conn.cursor()

    def rows():
        with _open("hash_robustness_results.csv") as f:
            for r in csv.DictReader(f):
                yield (
                    sanitize(r["image_id"]), sanitize(r["filename"]),
                    sanitize(r["transform_name"]), sanitize(r["intensity_value"]),
                    sanitize(r["pipeline_version"]), sanitize(r["hash_algorithm"]),
                    sanitize(r["hash_value"]), sanitize(r["hash_ref"]),
                    _num(r["hamming_distance"]), _int(r["width"]), _int(r["height"]),
                    _num(r["aspect_ratio"]),
                )

    _load(cur, "INSERT INTO hash_results (image_id, filename, transform_name, "
               "intensity_value, pipeline_version, hash_algorithm, hash_value, "
               "hash_ref, hamming_distance, width, height, aspect_ratio) VALUES %s",
          rows(), "hash_results", conn)


def load_watermark_results(conn, name, pipeline):
    cur = conn.cursor()

    def rows():
        with _open(f"{name}_robustness_results.csv") as f:
            for r in csv.DictReader(f):
                yield (
                    pipeline, sanitize(r["image_id"]), sanitize(r["filename"]),
                    sanitize(r["transform_name"]), sanitize(r["intensity_value"]),
                    sanitize(r["pipeline_version"]), _num(r["encode_mse"]), _num(r["encode_psnr"]),
                    sanitize(r["decode_secret"]), parse_bool(r["decode_present"]),
                    sanitize(r["decode_schema"]), _num(r["bit_accuracy"]),
                    _int(r["width"]), _int(r["height"]), _num(r["aspect_ratio"]),
                    parse_bool(r.get("auto_cropped")),
                )

    _load(cur, "INSERT INTO watermark_results (pipeline, image_id, filename, "
               "transform_name, intensity_value, pipeline_version, encode_mse, "
               "encode_psnr, decode_secret, decode_present, decode_schema, "
               "bit_accuracy, width, height, aspect_ratio, auto_cropped) VALUES %s",
          rows(), f"watermark_results ({pipeline})", conn)


def load_fallback_results(conn):
    cur = conn.cursor()

    def rows():
        with _open("fallback_robustness_results.csv") as f:
            for r in csv.DictReader(f):
                yield (
                    sanitize(r["image_id"]), sanitize(r["filename"]),
                    sanitize(r["transform_name"]), sanitize(r["intensity_value"]),
                    sanitize(r["pipeline_version"]), _num(r["encode_mse"]), _num(r["encode_psnr"]),
                    sanitize(r["fb_decode_secret"]), parse_bool(r["fb_decode_present"]),
                    _num(r["fb_bit_accuracy"]),
                    parse_bool(r["tm_combined_baseline_present"]) if r.get("tm_combined_baseline_present") else None,
                    _int(r["width"]), _int(r["height"]), _num(r["aspect_ratio"]),
                )

    _load(cur, "INSERT INTO fallback_results (image_id, filename, transform_name, "
               "intensity_value, pipeline_version, encode_mse, encode_psnr, "
               "fb_decode_secret, fb_decode_present, fb_bit_accuracy, "
               "tm_combined_baseline_present, width, height, aspect_ratio) VALUES %s",
          rows(), "fallback_results", conn)


def load_ensemble(conn):
    cur = conn.cursor()

    def rows():
        with _open("ensemble_decision_matrix.csv") as f:
            for r in csv.DictReader(f):
                yield (
                    sanitize(r["transform_name"]), sanitize(r["intensity_value"]),
                    sanitize(r["best_method"]), sanitize(r["fallback_method"]),
                    parse_bool(r["hash_ok"]), parse_bool(r["trustmark_ok"]),
                    parse_bool(r["lsb_ok"]), parse_bool(r["dct_ok"]),
                    sanitize(r["notes"]),
                )

    _load(cur, "INSERT INTO ensemble_decision_matrix (transform_name, intensity_value, "
               "best_method, fallback_method, hash_ok, trustmark_ok, lsb_ok, dct_ok, "
               "notes) VALUES %s", rows(), "ensemble_decision_matrix", conn)


def verify_counts(conn):
    cur = conn.cursor()
    expected = {
        "hash_results": 768_000,
        "watermark_results": 291_600,
        "fallback_results": 97_200,
        "ensemble_decision_matrix": 80,
    }
    print("\n--- Verification ---", flush=True)
    ok = True
    for t, exp in expected.items():
        cur.execute(f"SELECT COUNT(*) FROM {t}")
        got = cur.fetchone()[0]
        status = "[OK]" if got == exp else "[MISMATCH]"
        if got != exp:
            ok = False
        print(f"  {t}: {got} rows (expected {exp}) {status}", flush=True)
    cur.close()
    return ok


def main():
    print("Connecting to PostgreSQL...", flush=True)
    conn = psycopg2.connect(DATABASE_URL)
    try:
        create_tables(conn)
        load_hash_results(conn)
        load_watermark_results(conn, "trustmark", "trustmark")
        load_watermark_results(conn, "lsb", "lsb")
        load_watermark_results(conn, "dct", "dct")
        load_fallback_results(conn)
        load_ensemble(conn)
        if verify_counts(conn):
            print("\n[DONE] Migration complete; all row counts verified.", flush=True)
        else:
            print("\n[WARN] Migration finished with count mismatches.", flush=True)
            sys.exit(2)
    finally:
        conn.close()


if __name__ == "__main__":
    main()