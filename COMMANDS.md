# Project Commands

## Setup
```powershell
# Download COCO val2017
curl -L -o coco_val2017/val2017.zip https://images.cocodataset.org/zips/val2017.zip
Expand-Archive coco_val2017/val2017.zip -DestinationPath coco_val2017/

# Install dependencies
pip install imagehash pillow requests numpy
pip install pdqhash
$env:PYTHONUTF8="1"; pip install trustmark
$env:PYTHONUTF8="1"; pip install "scipy<1.14" --no-deps
```

## Pipeline Scripts
```powershell
# Perceptual hash robustness (100 images, 12 transforms)
$env:PYTHONUTF8="1"; python transform_hash_robustness.py --image-count 100

# TrustMark watermark robustness (100 images, 12 transforms)
$env:PYTHONUTF8="1"; python trustmark_robustness.py --image-count 100
```

## Verify Results
```powershell
$env:PYTHONUTF8="1"; python verify_results.py
```

## System
```powershell
# Disable sleep (for long runs)
powercfg /change standby-timeout-ac 0
powercfg /change hibernate-timeout-ac 0

# Re-enable sleep
powercfg /change standby-timeout-ac 15
powercfg /change hibernate-timeout-ac 30
```
