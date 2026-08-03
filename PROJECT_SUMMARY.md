Project Summary - Watermark Robustness Benchmark

MSc dissertation project comparing the robustness of perceptual hashing, neural watermarking, and classical watermarking baselines under graduated image transforms. Built on MS-COCO 2017 validation images.

---

1. Objective

Evaluate whether perceptual hashes, neural watermarks, and classical watermarks degrade gracefully or catastrophically under common image transforms - and whether an ensemble of methods can cover each other's weaknesses. The project measures bit-level recovery accuracy across 12 transform types at multiple intensity levels, then analyses which method survives which attack at which severity.

---

2. Pipeline Components

Perceptual Hashing (8 algorithms)

Computed by transform_hash_robustness.py. Each algorithm produces a fixed-length binary hash; robustness is measured as Hamming distance between the reference (original) hash and the post-transform hash.

pHash (64-bit, imagehash), dHash (64-bit, imagehash), aHash (64-bit, imagehash), wHash (64-bit, imagehash), colorHash (imagehash), dhash_vertical (64-bit, imagehash), phash_simple (64-bit, imagehash), PDQ (256-bit, pdqhash)

TrustMark (neural watermark)

Embedded by trustmark_robustness.py using TrustMark v0.9.1 (Q model, CPU-only). A 7-character secret (TM00001) is embedded, then decoded post-transform. Metrics: bit_accuracy (character-level match fraction), decode_present, encode_mse/psnr.

LSB Baseline

Embedded by lsb_robustness.py. Payload LSB0001 is written into the least-significant bit plane of the red channel. Decoded post-transform by extracting the LSB plane and comparing. Serves as a fragile-watermark lower bound.

DCT Baseline

Embedded by dct_robustness.py. Payload is differentially encoded into mid-frequency DCT coefficients. Decoded by reversing the DCT and reading the embedded bits. Serves as a semi-robust frequency-domain baseline.

---

3. Transforms

12 transforms defined in transforms.py (single source of truth). Each has a list of intensity steps, giving 80 total (transform, intensity) pairs:

brightness (0.5, 0.7, 0.85, 1.15, 1.5, 2.0 - 6 steps)
contrast (0.5, 0.7, 0.85, 1.15, 1.5, 2.0 - 6 steps)
saturation (0.2 to 1.8, 8 steps)
vibrancy (0.2 to 1.8, 8 steps, non-linear HSV boost)
gaussian_blur (radius 0.5 to 5.0, 6 steps)
salt_pepper_noise (density 0.01 to 0.15, 6 steps)
jpeg_compression (quality 95 to 5, 8 steps)
rotation (1 to 90 degrees, 8 steps)
scaling (0.25x to 3.0x, 6 steps)
crop_center (10% to 80% removed, 8 steps)
crop_random (10% to 80% removed, 8 steps, seeded)
letterbox (black, grey - pad to square, 2 steps)

Intensity sweep design: Each transform sweeps from mild to severe distortion. Low values (e.g. blur radius 0.5) represent subtle real-world noise; high values (e.g. blur radius 5.0, JPEG quality 5) represent extreme degradation. The threshold analysis identifies the exact intensity where each method drops below 50% and 10% performance.

---

4. Data

Dataset: MS-COCO 2017 validation split (5,000 images available)
Images used: 100 (first 100 alphabetically, deterministic)
Transform types: 12
Intensity steps per type: 6 to 8 (80 total pairs)
Hash algorithms: 8
Watermark methods: 3 (TrustMark, LSB, DCT)

Output CSV row counts

hash_robustness_results.csv: 64,000 rows (100 images x 8 algorithms x 80 steps)
trustmark_robustness_results.csv: 8,100 rows (100 images x 80 steps + 100 encode-only rows)
lsb_robustness_results.csv: 8,100 rows (same structure as TrustMark)
dct_robustness_results.csv: 8,100 rows (same structure as TrustMark)
ensemble_decision_matrix.csv: 80 rows (one row per transform/intensity pair)
Total: 88,380 rows

---

5. Analysis

Threshold Analysis (ensemble_analysis.py)

For each of the 12 transforms, identifies the intensity level at which each method's mean performance drops below critical thresholds:

- Hash: mean Hamming distance > 128 (50% bit error) and > 230 (90% bit error)
- Watermarks: mean bit_accuracy < 0.5 (50%) and < 0.1 (10%)

Key finding from current results: hash and TrustMark never drop below 50% for any tested transform - they are highly robust. LSB fails under brightness 0.7, contrast 0.85, JPEG quality 20, rotation 90 degrees, and scaling 0.25x. DCT fails under rotation 1 degree, scaling 0.25x, and crop operations at low retention.

Ensemble Decision Matrix

For each (transform, intensity) pair, determines which method is best (weighted score: TrustMark 1.0, hash 0.8, DCT 0.7, LSB 0.5) and which is the fallback. Outputs a decision matrix CSV that a production system could use to choose the optimal watermarking strategy given the expected distortion profile.

---

6. Dashboard

Frontend (dashboard/)

Single-page app served by the FastAPI backend. Dark theme using OKLCH custom properties, Jost typeface, Chart.js for visualisations.

4 tabs:

- Overview: Stats grid (image count, transform count, hash algorithms) + grouped bar chart of mean bit accuracy per transform for TrustMark/LSB/DCT
- Per-Transform: Dropdown to select a transform; line chart plotting all 4 methods' performance vs intensity (hash inverted to 1 - hamming/256 for comparability, dual y-axis), with a 0.5 threshold line
- Ensemble Matrix: HTML table colour-coded by best method per cell (orange = TrustMark, purple = hash, green = LSB, blue = DCT)
- Per-Image: Dropdown to select an image; tables showing all hash results (algorithm x transform x intensity x hamming distance) and watermark results (method x transform x intensity x bit accuracy x present)

Backend (dashboard_api.py)

FastAPI app with CORS enabled, loads all 5 CSVs into memory at startup. Endpoints:

GET /api/summary - image count, transform count, algorithm list
GET /api/transforms - transform to intensity values map
GET /api/hash/by_transform - mean hamming distance per transform x intensity
GET /api/hash/by_algorithm - per-algorithm hamming distance (filterable by transform)
GET /api/trustmark/by_transform - mean bit accuracy per transform x intensity
GET /api/lsb/by_transform - same for LSB
GET /api/dct/by_transform - same for DCT
GET /api/ensemble - full decision matrix rows
GET /api/ensemble/matrix - transforms x intensities best-method grid
GET /api/image/{id} - all hash + watermark rows for a single image
Static mount / - serves dashboard/ files with html=True

Run with: python dashboard_api.py (uvicorn on 127.0.0.1:8000).

---

7. Database

Schema (migrate_to_db.py)

PostgreSQL via psycopg2. Three tables with indexes:

hash_results: 64,000 rows (all perceptual hash results)
watermark_results: 24,300 rows (TrustMark + LSB + DCT results unified)
ensemble_decision_matrix: 80 rows (best/fallback method per scenario)

Indexes on image_id, transform_name, hash_algorithm, and pipeline for fast dashboard queries. Connects via DATABASE_URL env var (loaded from .env).

---

8. Current State

Done and verified

- All 4 robustness pipelines (hash, TrustMark, LSB, DCT) completed on 100 images
- All 5 output CSVs produced with correct row counts
- Threshold analysis and ensemble decision matrix produced
- Dashboard frontend (4 tabs, Chart.js, OKLCH dark theme)
- Dashboard backend (FastAPI, all endpoints, static file serving)
- Database migration script (schema + bulk insert)
- transforms.py as single source of truth for all transforms

Running

- python dashboard_api.py serves the full dashboard at http://127.0.0.1:8000
- CSV-based backend is fully functional (no database required to view dashboard)

Pending / not yet done

- Git: Repository has zero commits; nothing is version-controlled
- Database: Migration script exists but has not been executed against a live PostgreSQL instance
- Dashboard/DB: Backend currently reads from CSV files, not PostgreSQL
- 1000-image extended run: A partial 1000-image TrustMark run was attempted but hit disk space limits; only the 100-image set is complete
- Qualitative examples: No sample watermarked/transformed images are saved to disk for the thesis figures
- Git cleanup: Legacy pilot CSVs (hash_robustness_results_black_fill.csv, _grey_fill.csv, _pdq.csv) and the val2017.zip duplicate (815 MB) remain in the project tree

---
