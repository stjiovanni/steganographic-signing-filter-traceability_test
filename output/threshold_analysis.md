# Per-Transform Threshold Analysis

Thresholds for each method across all 100 images.
Hash threshold: mean bit-error fraction > 0.5 (50% bit error) / > 0.9 (90% bit error).
  Bit-error fraction = Hamming distance / hash bit length (64 bits for all algorithms except PDQ = 256).
  "Hash (mean)" = pooled mean over all 8 hash algorithms and all images (ensemble average).
  "Hash (worst)" = worst-algorithm mean over images (weakest link). The pooled mean is dominated
  by the 7 robust 64-bit hashes and can mask PDQ failures, so the worst algorithm is what drives
  ensemble failure and is used for pass/fail decisions below.
Watermark threshold: mean bit_accuracy < 0.5 (< 50%) / < 0.1 (< 10%).

Degradation is not always monotonic, so each threshold reports BOTH the first intensity where it
is crossed and the worst-case intensity (most degraded mean metric: max bit-error fraction for
hashes, min bit_accuracy for watermarks) among the intensities that crossed.

| Transform | Metric | <50% first | <50% worst | <10% first | <10% worst |
|---|---|---|---|---|---|
| brightness | Hash (mean) | — | — | — | — |
| brightness | Hash (worst) | — | — | — | — |
| brightness | TrustMark | — | — | — | — |
| brightness | LSB | 0.7 | 0.85 | — | — |
| brightness | DCT | — | — | — | — |
| contrast | Hash (mean) | — | — | — | — |
| contrast | Hash (worst) | — | — | — | — |
| contrast | TrustMark | — | — | — | — |
| contrast | LSB | 0.85 | 0.85 | — | — |
| contrast | DCT | — | — | — | — |
| saturation | Hash (mean) | — | — | — | — |
| saturation | Hash (worst) | — | — | — | — |
| saturation | TrustMark | — | — | — | — |
| saturation | LSB | — | — | — | — |
| saturation | DCT | — | — | — | — |
| vibrancy | Hash (mean) | — | — | — | — |
| vibrancy | Hash (worst) | — | — | — | — |
| vibrancy | TrustMark | — | — | — | — |
| vibrancy | LSB | — | — | — | — |
| vibrancy | DCT | — | — | — | — |
| gaussian_blur | Hash (mean) | — | — | — | — |
| gaussian_blur | Hash (worst) | — | — | — | — |
| gaussian_blur | TrustMark | — | — | — | — |
| gaussian_blur | LSB | — | — | — | — |
| gaussian_blur | DCT | — | — | — | — |
| salt_pepper_noise | Hash (mean) | — | — | — | — |
| salt_pepper_noise | Hash (worst) | — | — | — | — |
| salt_pepper_noise | TrustMark | — | — | — | — |
| salt_pepper_noise | LSB | — | — | — | — |
| salt_pepper_noise | DCT | — | — | — | — |
| jpeg_compression | Hash (mean) | — | — | — | — |
| jpeg_compression | Hash (worst) | — | — | — | — |
| jpeg_compression | TrustMark | — | — | — | — |
| jpeg_compression | LSB | 20 | 80 | — | — |
| jpeg_compression | DCT | — | — | — | — |
| rotation | Hash (mean) | — | — | — | — |
| rotation | Hash (worst) | 70 | 70 | — | — |
| rotation | TrustMark | — | — | — | — |
| rotation | LSB | 90 | 90 | — | — |
| rotation | DCT | 1 | 1 | — | — |
| scaling | Hash (mean) | — | — | — | — |
| scaling | Hash (worst) | — | — | — | — |
| scaling | TrustMark | — | — | — | — |
| scaling | LSB | 0.25 | 0.25 | — | — |
| scaling | DCT | 0.25 | 3.0 | — | — |
| crop_center | Hash (mean) | — | — | — | — |
| crop_center | Hash (worst) | 0.8 | 0.8 | — | — |
| crop_center | TrustMark | — | — | — | — |
| crop_center | LSB | 0.1 | 0.7 | — | — |
| crop_center | DCT | 0.2 | 0.2 | — | — |
| crop_random | Hash (mean) | — | — | — | — |
| crop_random | Hash (worst) | 0.4 | 0.5 | — | — |
| crop_random | TrustMark | — | — | — | — |
| crop_random | LSB | 0.1 | 0.1 | — | — |
| crop_random | DCT | 0.3 | 0.8 | — | — |
| letterbox | Hash (mean) | — | — | — | — |
| letterbox | Hash (worst) | — | — | — | — |
| letterbox | TrustMark | — | — | — | — |
| letterbox | LSB | — | — | — | — |
| letterbox | DCT | — | — | — | — |

# Ensemble Overlap Analysis

For each (transform, intensity) pair across all 100 images:
- Hash success: worst-algorithm mean bit-error fraction < 0.5 (weakest link; Hamming
  normalized by hash bit length). The pooled mean stays low because 7 of 8 hashes are
  64-bit and robust, masking PDQ failures.
- Watermark success: mean bit_accuracy > 0.5
- best_method: largest robustness margin = distance from the failure line
  (hash: 0.5 - worst-algorithm bit-error fraction; watermark: bit_accuracy - 0.5)
