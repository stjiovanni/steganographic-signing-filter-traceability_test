# Ensemble-Aware Payload/ECC Analysis (development scale)

- Ablation source: `output/results/payload_ecc_ablation_dev100.csv`
- Hash fallback source: `output/results/final1200/hash_robustness_results.csv.gz` (1,200-image validated set)

A (image, transform, intensity) variant is **verified** if the TrustMark ECC-corrected
payload decodes exactly **or** the hash fallback passes (worst-algorithm bit-error
fraction < 0.5), matching the threshold logic in `ensemble_analysis.py`.

`rescue = verified(ensemble) - verified(TrustMark alone)` is the fraction of variants
that fail TrustMark but are recovered by the perceptual-hash fallback.

| config | n | TM exact% | ensemble% | hash rescue pp |
|---|---|---|---|---|
| bch_3_1chars | 8100 | 50.28 | 89.32 | +39.04 |
| bch_3_4chars | 8100 | 59.12 | 89.57 | +30.44 |
| bch_3_5chars | 8100 | 60.22 | 89.58 | +29.36 |
| bch_4_1chars | 8100 | 58.06 | 89.52 | +31.46 |
| bch_4_4chars | 8100 | 61.53 | 89.58 | +28.05 |
| bch_4_5chars | 8100 | 61.72 | 89.57 | +27.85 |
| bch_5_1chars | 8100 | 58.09 | 89.54 | +31.46 |
| bch_5_4chars | 8100 | 63.09 | 89.60 | +26.52 |
| bch_5_5chars | 8100 | 62.73 | 89.59 | +26.86 |
| bch_super_1chars | 8100 | 64.80 | 89.58 | +24.78 |
| bch_super_4chars | 8100 | 66.36 | 89.59 | +23.23 |
| bch_super_5chars | 8100 | 66.02 | 89.60 | +23.58 |
