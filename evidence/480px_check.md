# 480x480px Minimum Input — Verification

Scope: verifies whether the DPP Phase 2/3 promise ("Integrate encode/decode pipeline at 480x480px minimum input"; "Evaluate imperceptibility at 480x480px minimum using PSNR and SSIM") was actually honoured by the pipeline. No results, CSVs, or reports were modified.

## 1. Source image dimensions (from `output/results/final1200/image_manifest.json`)

`dataset: MS-COCO 2017 validation split`, `image_count: 1200`, `seed: 42`.

| Metric | Value |
|---|---|
| Width — min / max | 240 / 640 |
| Height — min / max | 180 / 640 |
| Short edge — min / max | 180 / 640 |
| Width — most common | 640 (755 images) |
| Height — most common | 480 (261 images) |
| Typical dims | 640x480, 640x427, 500x375, 480x640, 640x360 |

The assumption in the brief ("COCO val images are ~640x480") holds for the *typical / modal* case, but NOT for all images:

- Images with short edge < 480 px: **754 of 1200 (62.8%)**
- Images with width < 480 px: 192
- Images with height < 480 px: 572

So a large fraction of source images are *below* 480 on at least one dimension (a 640x480 image has a 480 short edge and just meets the floor; many are smaller).

## 2. TrustMark encode resolution

Both `trustmark_robustness.py` and `watermark_service.py` load `TrustMark(verbose=False, model_type='Q', encoding_type=TrustMark.Encoding.BCH_4)`.

- `tm.model_resolution_enc = 256`
- `tm.model_resolution_dec = 245`

`TrustMark.encode()` (Q model): the cover is resized to `(model_resolution_enc, model_resolution_enc)` = **256x256**, the residual is computed at that fixed model resolution, then interpolated back up to the original `(h, w)`. Therefore the model's internal operating/encoding resolution is a **fixed 256x256**, independent of the input image size. Decoding resizes to `model_resolution_dec` = 245.

## 3. Verdict

- **Source encode input ≥ 480px floor: NOT met for the full set.** 754/1200 images have a short edge below 480 px. Even where met, TrustMark's Q model never actually encodes at 480x480 — it resizes everything to its fixed 256x256 model resolution internally. The "480px minimum" is therefore not the resolution at which watermarking is performed.
- **Transformed conditions: the 480px floor is not applicable.** The `scaling` transform (`transforms.py` line 23: `[0.25, 0.5, 0.75, 1.5, 2.0, 3.0]`) scales watermarked images DOWN to 0.25x–0.75x, taking them well below 480 px on both dimensions by design. Downscaled transform conditions are intentionally outside any 480px floor.

**Bottom line:** the 480x480px minimum was not strictly honoured: the source set includes many sub-480px images, TrustMark's Q model internally operates at a fixed 256x256 (not 480x480), and the downscaling transform (0.25x–0.75x) pushes images far below 480px by design. The 480px floor can only be claimed as a nominal target for the original encode input, and it is not applicable to the downscaled transform conditions.

## 4. One-paragraph statement (suitable for the FPR promise table)

> The DPP's "480x480px minimum input" promise was not fully honoured by the pipeline. The MS-COCO validation source images range from 180x180 to 640x640 in their short edge, and 754 of 1200 (≈63%) are below 480 px on at least one dimension, so the floor is not met for the full encode set. Moreover, TrustMark's Q model does not operate at 480x480 at all: it internally resizes every cover to its fixed model resolution of 256x256 for encoding (and 245 for decoding), regardless of input size, so 480 px is not the resolution at which embedding actually occurs. Finally, the `scaling` robustness transform reduces watermarked images to 0.25x–0.75x, taking them far below 480 px by design, so the 480px floor is not applicable to the downscaled transform conditions. In short, the 480px minimum holds only as a nominal target for the original encode input in the typical (≈640x480) case, and is neither enforced across the dataset nor relevant to the downscaled robustness conditions.
