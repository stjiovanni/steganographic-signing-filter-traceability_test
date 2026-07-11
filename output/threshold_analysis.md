# Per-Transform Threshold Analysis

Thresholds for each method across all 100 images.
Hash threshold: mean Hamming distance > 128 (50% bit error) / > 230 (90% bit error).
Watermark threshold: mean bit_accuracy < 0.5 (< 50%) / < 0.1 (< 10%).

| Transform | Metric | <50% threshold | <10% threshold |
|---|---|---|---|
| brightness | Hash (mean) | — | — |
| brightness | TrustMark | — | — |
| brightness | LSB | 0.7 | — |
| brightness | DCT | — | — |
| contrast | Hash (mean) | — | — |
| contrast | TrustMark | — | — |
| contrast | LSB | 0.85 | — |
| contrast | DCT | — | — |
| saturation | Hash (mean) | — | — |
| saturation | TrustMark | — | — |
| saturation | LSB | — | — |
| saturation | DCT | — | — |
| vibrancy | Hash (mean) | — | — |
| vibrancy | TrustMark | — | — |
| vibrancy | LSB | — | — |
| vibrancy | DCT | — | — |
| gaussian_blur | Hash (mean) | — | — |
| gaussian_blur | TrustMark | — | — |
| gaussian_blur | LSB | — | — |
| gaussian_blur | DCT | — | — |
| salt_pepper_noise | Hash (mean) | — | — |
| salt_pepper_noise | TrustMark | — | — |
| salt_pepper_noise | LSB | — | — |
| salt_pepper_noise | DCT | — | — |
| jpeg_compression | Hash (mean) | — | — |
| jpeg_compression | TrustMark | — | — |
| jpeg_compression | LSB | 20 | — |
| jpeg_compression | DCT | — | — |
| rotation | Hash (mean) | — | — |
| rotation | TrustMark | — | — |
| rotation | LSB | 90 | — |
| rotation | DCT | 1 | — |
| scaling | Hash (mean) | — | — |
| scaling | TrustMark | — | — |
| scaling | LSB | 0.25 | — |
| scaling | DCT | 0.25 | — |
| crop_center | Hash (mean) | — | — |
| crop_center | TrustMark | — | — |
| crop_center | LSB | 0.1 | — |
| crop_center | DCT | 0.2 | — |
| crop_random | Hash (mean) | — | — |
| crop_random | TrustMark | — | — |
| crop_random | LSB | 0.1 | — |
| crop_random | DCT | 0.3 | — |
| letterbox | Hash (mean) | — | — |
| letterbox | TrustMark | — | — |
| letterbox | LSB | — | — |
| letterbox | DCT | — | — |

# Ensemble Overlap Analysis

For each (transform, intensity) pair across all 100 images:
- Hash success: mean Hamming < 128 across all 8 algorithms
- Watermark success: mean bit_accuracy > 0.5
