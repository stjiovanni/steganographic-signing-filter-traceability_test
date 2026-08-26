# Robustness Benchmark — Perceptual Hashing, Watermarking, and Ensemble Analysis

MSc dissertation project evaluating complementary verification signals: perceptual hashing (pHash, dHash, aHash, wHash, colorHash, PDQ), neural watermarking (TrustMark), and classical watermarking baselines (LSB, DCT) under graduated image transforms. The project does not treat any one signal as proof of authenticity.

## Study Companion (mobile tutorial)

A mobile-only web app that teaches the whole project chapter by chapter: `study-companion/`. Open `study-companion/index.html` in a mobile browser (or serve the folder) to read each chapter and answer its quiz. 10 chapters, 100 questions total, retakeable (best answers are kept; the score shows out of 100). It reuses the report figures and dashboard screenshots and follows the project's exact design tokens.

- `study-companion/index.html` — app shell
- `study-companion/styles.css` — design tokens (exact px spacing, typography, option state colours)
- `study-companion/data.js` — 10 chapters + 100 questions
- `study-companion/app.js` — chapter/quiz logic, scroll friction, dynamic blur
- `study-companion/assets/` — report figures and dashboard screenshots
- `study-companion/smoke_test.py` + `capture_shots.py` — verification scripts

## Pipeline Scripts

| Script | Purpose | Produces |
|--------|---------|----------|
| `transform_hash_robustness.py` | Applies 12 transforms × 80 intensity conditions to clean COCO images, computes 8 perceptual hashes per transform | `output/results/hash_robustness_results.csv` |
| `trustmark_robustness.py` | Embeds "TM00001" via TrustMark, applies same transforms, decodes post-transform | `output/results/trustmark_robustness_results.csv` |
| `lsb_robustness.py` | Embeds "LSB0001" in LSB plane, applies same transforms, recovers payload | `output/results/lsb_robustness_results.csv` |
| `dct_robustness.py` | Embeds payload in mid-frequency DCT coefficients (differential encoding), applies same transforms, recovers | `output/results/dct_robustness_results.csv` |
| `letterbox_hash_pipeline.py` | Earlier experiment: letterbox fill-color ablation (black vs grey fill) over 20 images | `output/hash_robustness_results_black_fill.csv`, `output/hash_robustness_results_grey_fill.csv` |
| `ensemble_analysis.py` | Reads all 4 result CSVs, produces threshold analysis + decision matrix | `output/threshold_analysis.md`, `output/results/ensemble_decision_matrix.csv` |
| `verify_results.py` | Reads hash CSV and prints mean Hamming distance per transform per hash type | — |
| `experiment_manifest.py` | Records selected image IDs, dimensions, and SHA-256 checksums | `output/results/image_manifest.json` |
| `validate_experiment.py` | Rejects incomplete or duplicated result coverage before analysis | — |
| `run_1200_experiment.py` | Runs the complete 1,200-image benchmark serially with a log and resume support | `output/logs/run_1200_experiment.log` |
| `generate_fpr_evidence.py` | Creates workbook sheets for results, Gantt evidence, risks, and objective mapping | `FPR_Evidence.xlsx` |
| `generate_figures.py` | Regenerates figures from the current CSVs and sample size | `output/figures/fpr_method_comparison.png` |
| `generate_improvement_comparison.py` | Compares the validated 100-image pilot with the validated 1,200-image final run and records implemented versus proposed improvements | `FPR_Improvement_Comparison.xlsx`, `output/figures/fpr_pilot_final_comparison.png` |

## Shared Modules

| Module | Purpose |
|--------|---------|
| `transforms.py` | Single source of truth for all 12 transform definitions, intensity steps, and stable seeds |

## Output CSVs — current results

| File | Rows | Script | Description |
|------|------|--------|-------------|
| `output/results/hash_robustness_results.csv` | 64,000 | `transform_hash_robustness.py` | 8 perceptual hashes × 100 images × 80 transform×intensity steps (normalized: one row per hash algorithm) |
| `output/results/trustmark_robustness_results.csv` | 8,100 | `trustmark_robustness.py` | TrustMark decode + bit accuracy × 100 images × 80 steps + 100 encode rows |
| `output/results/lsb_robustness_results.csv` | 8,100 | `lsb_robustness.py` | LSB baseline decode + bit accuracy × 100 images × 80 steps + 100 encode rows |
| `output/results/dct_robustness_results.csv` | 8,100 | `dct_robustness.py` | DCT baseline decode + bit accuracy × 100 images × 80 steps + 100 encode rows |
| `output/results/ensemble_decision_matrix.csv` | 80 | `ensemble_analysis.py` | Per (transform, intensity) best/fallback method and overlap notes |
| `output/threshold_analysis.md` | — | `ensemble_analysis.py` | Markdown table of intensity thresholds where each method drops below 50% and 10% |

## Output CSVs — archive (superseded or earlier experiments)

| File | Description |
|------|-------------|
| `output/archive/hash_robustness_results_pdq.csv` | Pre-fix PDQ run (superseded by `hash_robustness_results.csv` with corrected 256-bit PDQ serialization) |
| `output/archive/hash_organized/` | Organized hash images from the letterbox fill-color ablation (20 images × 4 hash types × 3 variants) |
| `output/hash_robustness_results_black_fill.csv` | Earlier letterbox-only experiment, black fill, 20 images |
| `output/hash_robustness_results_grey_fill.csv` | Earlier letterbox-only experiment, grey fill, 20 images |

## Pipeline status

| Stage | Status |
|-------|--------|
| Perceptual hash robustness (8 hash types, 12 transforms × 80 intensity conditions) | Done |
| TrustMark watermark robustness (12 transforms × 80 intensity conditions) | Done |
| LSB baseline | Done |
| DCT baseline | Done |
| Threshold analysis (per-transform intensity thresholds for <50% / <10% decode) | Done |
| Ensemble overlap analysis (decision matrix) | Done |
| Payload/ECC ablation (12-config dev sweep; selected config at 1,200; ensemble-aware rescoring) | Done |

## Dataset

MS-COCO 2017 validation split: 5000 images in `coco_val2017/val2017/`. The benchmark selection is the lexicographically first N JPG files, recorded in `output/results/image_manifest.json`. The default remains 100 for a quick pilot; the final run is configured for 1,200.

## Final evidence

The validated final evidence is under `output/results/final1200/` and contains 1,200-image hash, TrustMark, LSB and DCT outputs. Run `python validate_experiment.py --image-count 1200 --results-dir output/results/final1200` before regenerating report artefacts. The maintained FPR source is `output/FPR_v1.4.md`; the matching editable document is `24163800_Opaleye_Toluwalope_FPR_v1.7.docx` (earlier versions superseded; v1.7 is the cleaned derivative of locked v1.6). v1.7 contains the two-layer fallback experiment (Section 4.11), the method comparison workbook results (Section 4.12, `FPR_Method_Comparison.xlsx`), embedded dashboard screenshots (Figures 2-4), the hypothesis outcome, and the fully-reconciled IPR/DPP promise-vs-delivery table including the deployed PostgreSQL instance.

## PostgreSQL

A local PostgreSQL 16 runs in Docker (`msc_postgres`, port 5432, database `msc_proj`; credentials in `.env`, gitignored). `python migrate_to_db.py` loads the validated final1200 evidence into it (768,000 hash rows; 97,200 x TrustMark/LSB/DCT; 97,200 fallback; 80 ensemble) and verifies counts. The dashboard serves from the database when `DATABASE_URL` is set: `python scripts/serve_db.py`.

The payload/error-correction ablation is recorded under `output/results/`: the 12-config development sweep (`payload_ecc_ablation_dev100.csv`, selection in `payload_ecc_dev_selection.md`), the validated 1,200-image selected configuration (`payload_ecc_ablation_selected_final1200.csv`), and the ensemble-aware rescoring (`ensemble_aware_payload_dev100.md`, `ensemble_aware_payload_final1200.md`).

The dashboard reads `output/results` (the historical 100-image files) by default; set `CSV_DIR=output/results/final1200` to display the validated final evidence. This default is documented in the FPR (Section 4.1).

## Running

```powershell
# Hash robustness
$env:PYTHONUTF8="1"; python transform_hash_robustness.py --image-count 100

# TrustMark robustness
$env:PYTHONUTF8="1"; python trustmark_robustness.py --image-count 100

# LSB baseline
$env:PYTHONUTF8="1"; python lsb_robustness.py --image-count 100

# DCT baseline
$env:PYTHONUTF8="1"; python dct_robustness.py --image-count 100

# Analysis
$env:PYTHONUTF8="1"; python ensemble_analysis.py

# Verify
$env:PYTHONUTF8="1"; python verify_results.py

# Final-run preparation and validation
python experiment_manifest.py --input-dir coco_val2017/val2017 --image-count 1200
python run_1200_experiment.py
python generate_fpr_evidence.py
python generate_figures.py
```
