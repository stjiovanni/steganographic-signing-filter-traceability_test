import os
import csv
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
RESULTS_DIR = os.path.join(os.path.dirname(__file__), "output", "results")


def get_connection():
    return psycopg2.connect(DATABASE_URL)


def create_tables(conn):
    cur = conn.cursor()
    cur.execute("""
        DROP TABLE IF EXISTS hash_results CASCADE;
        DROP TABLE IF EXISTS watermark_results CASCADE;
        DROP TABLE IF EXISTS ensemble_decision_matrix CASCADE;

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

        CREATE INDEX IF NOT EXISTS idx_hash_image ON hash_results(image_id);
        CREATE INDEX IF NOT EXISTS idx_hash_transform ON hash_results(transform_name);
        CREATE INDEX IF NOT EXISTS idx_hash_algorithm ON hash_results(hash_algorithm);
        CREATE INDEX IF NOT EXISTS idx_wm_image ON watermark_results(image_id);
        CREATE INDEX IF NOT EXISTS idx_wm_transform ON watermark_results(transform_name);
        CREATE INDEX IF NOT EXISTS idx_wm_pipeline ON watermark_results(pipeline);
    """)
    conn.commit()
    print("[OK] Tables and indexes created.")
    cur.close()


def parse_bool(val):
    if val is None:
        return False
    return val.strip().lower() == "true"


def sanitize(val):
    if val is None:
        return None
    return val.replace("\x00", "")


def load_hash_results(conn):
    filepath = os.path.join(RESULTS_DIR, "hash_robustness_results.csv")
    cur = conn.cursor()
    rows = []
    with open(filepath, "r", newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        for row in reader:
            if len(row) < 12:
                continue
            rows.append((
                sanitize(row[0]), sanitize(row[1]), sanitize(row[2]), sanitize(row[3]),
                sanitize(row[4]), sanitize(row[5]), sanitize(row[6]), sanitize(row[7]),
                float(row[8]) if row[8] else None,  # hamming_distance
                int(row[9]) if row[9] else None,      # width
                int(row[10]) if row[10] else None,    # height
                float(row[11]) if row[11] else None,  # aspect_ratio
            ))

    args_str = b",".join(
        cur.mogrify(
            "(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", row
        )
        for row in rows
    )
    cur.execute(
        b"INSERT INTO hash_results "
        b"(image_id, filename, transform_name, intensity_value, pipeline_version, "
        b"hash_algorithm, hash_value, hash_ref, hamming_distance, width, height, aspect_ratio) VALUES "
        + args_str
    )
    conn.commit()
    count = cur.rowcount
    print(f"[OK] hash_results: {count} rows inserted.")
    cur.close()
    return count


def load_watermark_results(conn, csv_filename, pipeline_name):
    filepath = os.path.join(RESULTS_DIR, csv_filename)
    cur = conn.cursor()
    rows = []
    with open(filepath, "r", newline="", encoding="utf-8", errors="replace") as f:
        reader = csv.reader(f)
        header = next(reader)
        for row in reader:
            if len(row) < 15:
                continue
            rows.append((
                pipeline_name,                         # pipeline
                sanitize(row[0]),                      # image_id
                sanitize(row[1]),                      # filename
                sanitize(row[2]),                      # transform_name
                sanitize(row[3]),                      # intensity_value
                sanitize(row[4]),                      # pipeline_version
                float(row[5]) if row[5] else None,    # encode_mse
                float(row[6]) if row[6] else None,    # encode_psnr
                sanitize(row[7]),                      # decode_secret
                parse_bool(row[8]),                    # decode_present
                sanitize(row[9]),                      # decode_schema
                float(row[10]) if row[10] else None,  # bit_accuracy
                int(row[11]) if row[11] else None,    # width
                int(row[12]) if row[12] else None,    # height
                float(row[13]) if row[13] else None,  # aspect_ratio
                parse_bool(row[14]),                   # auto_cropped
            ))

    args_str = b",".join(
        cur.mogrify(
            "(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", row
        )
        for row in rows
    )
    cur.execute(
        b"INSERT INTO watermark_results "
        b"(pipeline, image_id, filename, transform_name, intensity_value, pipeline_version, "
        b"encode_mse, encode_psnr, decode_secret, decode_present, decode_schema, "
        b"bit_accuracy, width, height, aspect_ratio, auto_cropped) VALUES "
        + args_str
    )
    conn.commit()
    count = cur.rowcount
    print(f"[OK] watermark_results ({pipeline_name}): {count} rows inserted.")
    cur.close()
    return count


def load_ensemble(conn):
    filepath = os.path.join(RESULTS_DIR, "ensemble_decision_matrix.csv")
    cur = conn.cursor()
    rows = []
    with open(filepath, "r", newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        for row in reader:
            if len(row) < 9:
                continue
            rows.append((
                sanitize(row[0]),  # transform_name
                sanitize(row[1]),  # intensity_value
                sanitize(row[2]),  # best_method
                sanitize(row[3]),  # fallback_method
                parse_bool(row[4]),  # hash_ok
                parse_bool(row[5]),  # trustmark_ok
                parse_bool(row[6]),  # lsb_ok
                parse_bool(row[7]),  # dct_ok
                sanitize(row[8]),  # notes
            ))

    args_str = b",".join(
        cur.mogrify(
            "(%s,%s,%s,%s,%s,%s,%s,%s,%s)", row
        )
        for row in rows
    )
    cur.execute(
        b"INSERT INTO ensemble_decision_matrix "
        b"(transform_name, intensity_value, best_method, fallback_method, "
        b"hash_ok, trustmark_ok, lsb_ok, dct_ok, notes) VALUES "
        + args_str
    )
    conn.commit()
    count = cur.rowcount
    print(f"[OK] ensemble_decision_matrix: {count} rows inserted.")
    cur.close()
    return count


def verify_counts(conn):
    cur = conn.cursor()
    tables = ["hash_results", "watermark_results", "ensemble_decision_matrix"]
    print("\n--- Verification ---")
    for t in tables:
        cur.execute(f"SELECT COUNT(*) FROM {t}")
        count = cur.fetchone()[0]
        print(f"  {t}: {count} rows")
    cur.close()


def main():
    print(f"Connecting to: {DATABASE_URL}")
    conn = get_connection()
    try:
        create_tables(conn)
        load_hash_results(conn)
        load_watermark_results(conn, "trustmark_robustness_results.csv", "trustmark")
        load_watermark_results(conn, "lsb_robustness_results.csv", "lsb")
        load_watermark_results(conn, "dct_robustness_results.csv", "dct")
        load_ensemble(conn)
        verify_counts(conn)
        print("\n[DONE] Migration complete.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
