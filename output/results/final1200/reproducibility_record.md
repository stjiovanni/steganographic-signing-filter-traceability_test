# Reproducibility Record

Created (UTC): `2026-08-14T09:21:14.547550+00:00`

## Artefact Checksums

- Manifest: `output\results\final1200\image_manifest.json`
  SHA-256: `9827f57c6f57e385172d9b4a71aa16f68423cdd97ea9f906fd0b8ee0bbfe6be5`
- Final result: `output\results\final1200\ensemble_decision_matrix.csv`
  SHA-256: `5c0d7d62542803aa0de7bcee060bf11319cbfbab966fc7f0f4928314d90d0222`

## Runtime

- Python: `3.12.10`
- OS: `Windows-11-10.0.26200-SP0`
- CPU: `AMD64 Family 23 Model 24 Stepping 1, AuthenticAMD`
- GPU: `none detected`

## Model And Software

- Pipeline: `v2.1-reproducible`
- TrustMark model: package-managed default model
- Packages:
  - `imagehash`: `4.3.2`
  - `numpy`: `1.26.4`
  - `pdqhash`: `0.2.8`
  - `Pillow`: `12.3.0`
  - `scipy`: `1.13.1`
  - `torch`: `2.12.1`
  - `torchvision`: `0.27.1`
  - `trustmark`: `0.9.1`

## Transform Configuration

```json
{
  "image_count": 1200,
  "seed": 42,
  "selection": "lexicographically first 1200 JPG files",
  "transforms": {
    "brightness": [
      0.5,
      0.7,
      0.85,
      1.15,
      1.5,
      2.0
    ],
    "contrast": [
      0.5,
      0.7,
      0.85,
      1.15,
      1.5,
      2.0
    ],
    "saturation": [
      0.2,
      0.43,
      0.66,
      0.89,
      1.11,
      1.34,
      1.57,
      1.8
    ],
    "vibrancy": [
      0.2,
      0.43,
      0.66,
      0.89,
      1.11,
      1.34,
      1.57,
      1.8
    ],
    "gaussian_blur": [
      0.5,
      1.0,
      1.5,
      2.0,
      3.0,
      5.0
    ],
    "salt_pepper_noise": [
      0.01,
      0.02,
      0.04,
      0.06,
      0.1,
      0.15
    ],
    "jpeg_compression": [
      95,
      80,
      65,
      50,
      35,
      20,
      10,
      5
    ],
    "rotation": [
      1,
      2,
      5,
      10,
      20,
      45,
      70,
      90
    ],
    "scaling": [
      0.25,
      0.5,
      0.75,
      1.5,
      2.0,
      3.0
    ],
    "crop_center": [
      0.1,
      0.2,
      0.3,
      0.4,
      0.5,
      0.6,
      0.7,
      0.8
    ],
    "crop_random": [
      0.1,
      0.2,
      0.3,
      0.4,
      0.5,
      0.6,
      0.7,
      0.8
    ],
    "letterbox": [
      "black",
      "grey"
    ]
  },
  "random_transform_seed": "SHA-256(image_id_transform_name_intensity) first 8 bytes, masked to 31 bits"
}
```

## Validation

- Command: `C:\Users\hp\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\python.exe validate_experiment.py --image-count 1200 --results-dir C:\Users\hp\Documents\porfolio\msc_proj\output\results\final1200`
- Output/log location: `output/logs/run_1200_experiment.log (pipeline log); validation also writes stdout/stderr to the invoking terminal`

## Exact Rerun Commands

- `C:\Users\hp\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\python.exe experiment_manifest.py --input-dir C:\Users\hp\Documents\porfolio\msc_proj\coco_val2017\val2017 --image-count 1200 --seed 42 --output C:\Users\hp\Documents\porfolio\msc_proj\output\results\final1200\image_manifest.json`
- `C:\Users\hp\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\python.exe transform_hash_robustness.py --image-count 1200 --seed 42 --output-csv C:\Users\hp\Documents\porfolio\msc_proj\output\results\final1200\hash_robustness_results.csv.gz --resume`
- `C:\Users\hp\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\python.exe trustmark_robustness.py --image-count 1200 --seed 42 --output-csv C:\Users\hp\Documents\porfolio\msc_proj\output\results\final1200\trustmark_robustness_results.csv --resume`
- `C:\Users\hp\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\python.exe lsb_robustness.py --image-count 1200 --seed 42 --output-csv C:\Users\hp\Documents\porfolio\msc_proj\output\results\final1200\lsb_robustness_results.csv --resume`
- `C:\Users\hp\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\python.exe dct_robustness.py --image-count 1200 --seed 42 --output-csv C:\Users\hp\Documents\porfolio\msc_proj\output\results\final1200\dct_robustness_results.csv --resume`
- `C:\Users\hp\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\python.exe ensemble_analysis.py --results-dir C:\Users\hp\Documents\porfolio\msc_proj\output\results\final1200 --output-dir C:\Users\hp\Documents\porfolio\msc_proj\output\results\final1200`
- `C:\Users\hp\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\python.exe payload_ecc_ablation.py --execute --image-count 100 --output-csv C:\Users\hp\Documents\porfolio\msc_proj\output\results\payload_ecc_ablation_dev100.csv --resume`
- `C:\Users\hp\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\python.exe payload_ecc_ablation.py --execute --image-count 1200 --ecc-modes BCH_SUPER --payload-lengths 4 --output-csv C:\Users\hp\Documents\porfolio\msc_proj\output\results\payload_ecc_ablation_selected_final1200.csv --resume`
- `C:\Users\hp\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\python.exe ensemble_aware_payload_analysis.py --ablation C:\Users\hp\Documents\porfolio\msc_proj\output\results\payload_ecc_ablation_selected_final1200.csv --hash C:\Users\hp\Documents\porfolio\msc_proj\output\results\final1200\hash_robustness_results.csv.gz --out C:\Users\hp\Documents\porfolio\msc_proj\output\results\ensemble_aware_payload_final1200.md --scale-label final1200`
- `C:\Users\hp\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\python.exe validate_experiment.py --image-count 1200 --results-dir C:\Users\hp\Documents\porfolio\msc_proj\output\results\final1200`

## Secrets

No environment variables, .env files, credentials, tokens, or secret values are read or recorded.
