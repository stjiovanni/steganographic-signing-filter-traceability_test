# Robustness Benchmark — Perceptual Hashing, Watermarking, and Ensemble Analysis

MSc dissertation project comparing robustness of perceptual hashing (pHash, dHash, aHash, wHash, colorHash, PDQ), neural watermarking (TrustMark), and classical watermarking baselines (LSB, DCT) under graduated image transforms.

## Pipeline Scripts

| Script | Purpose | Produces |
|--------|---------|----------|
| `transform_hash_robustness.py` | Applies 14 transforms × intensity steps to clean COCO images, computes 8 perceptual hashes per transform | `output/results/hash_robustness_results.csv` |
| `trustmark_robustness.py` | Embeds "TM00001" via TrustMark, applies same transforms, decodes post-transform | `output/results/trustmark_robustness_results.csv` |
| `lsb_robustness.py` | Embeds "LSB0001" in LSB plane, applies same transforms, recovers payload | `output/results/lsb_robustness_results.csv` |
| `dct_robustness.py` | Embeds payload in mid-frequency DCT coefficients, applies same transforms, recovers | `output/results/dct_robustness_results.csv` |
| `letterbox_hash_pipeline.py` | Earlier experiment: letterbox fill-color ablation (black vs grey fill) over 20 images | `output/hash_robustness_results_black_fill.csv`, `output/hash_robustness_results_grey_fill.csv` |
| `dct_robustness.py` | Embeds payload in mid-frequency DCT coefficients (differential encoding), applies transforms, recovers | `output/results/dct_robustness_results.csv` |
| `ensemble_analysis.py` | Reads all 4 result CSVs, produces threshold analysis + decision matrix | `output/threshold_analysis.md`, `output/results/ensemble_decision_matrix.csv` |
| `verify_results.py` | Reads hash CSV and prints mean Hamming distance per transform per hash type | — |
| `letterbox_hash_pipeline.py` | Earlier experiment: letterbox fill-color ablation (black vs grey fill) over 20 images | `output/hash_robustness_results_black_fill.csv`, `output/hash_robustness_results_grey_fill.csv` |

## Shared Modules

| Module | Purpose |
|--------|---------|
| `transforms.py` | Single source of truth for all 14 transform definitions and their intensity steps |

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
| Perceptual hash robustness (8 hash types, 14 transforms × intensity steps) | Done |
| TrustMark watermark robustness (14 transforms × intensity steps) | Done |
| LSB baseline | Done |
| DCT baseline | Done |
| Threshold analysis (per-transform intensity thresholds for <50% / <10% decode) | Done |
| Ensemble overlap analysis (decision matrix) | Done |

## Dataset

MS-COCO 2017 validation split: 5000 images in `coco_val2017/val2017/`. All pipelines operate on the first N images (default 100).

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
```
