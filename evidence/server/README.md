# Server Artefact Evidence

This folder records the demonstrated behaviour of the FastAPI server artefact (the
dashboard / Sign-Verify web application described in the FPR, Section 4.1).

## How to reproduce

```powershell
# 1. Start the server (CSV mode; set CSV_DIR to the validated final evidence for the final dataset)
python dashboard_api.py
# 2. In a second terminal, run the smoke test
python scripts/smoke_test.py
# 3. Run the end-to-end hybrid sign/verify flow
python scripts/test_hybrid_sign_verify.py
```

## Files

- `smoke_test_output.txt` — output of `scripts/smoke_test.py`: all 12 read endpoints return
  HTTP 200 (overview, transforms, per-method by-transform/by-algorithm summaries, ensemble,
  per-image, and the static dashboard page).
- `hybrid_sign_verify_output.txt` — output of `scripts/test_hybrid_sign_verify.py`: the full
  upload -> sign -> verify flow. The `hybrid` method embeds a TrustMark payload (`TM00001`)
  and a fallback watermark payload (`FB01`) into the same image; verification recovers both
  channels and reports two-layer recovery.
- `detect_watermark_output.txt` — output of `scripts/test_detect_watermark.py --server`:
  end-to-end tests of custom payloads and two-image watermark detection. Confirms:
  - `/api/payload_capacity` reports per-method capacity (trustmark 9 chars, lsb/dct 7, hybrid fallback 4).
  - A user-supplied custom payload (e.g. `Jane 2026`) is embedded and recovered by TrustMark.
  - The hybrid fallback channel accepts a custom payload (e.g. `JANE`) recovered alongside the
    primary `TM00001`.
  - `/api/analyze` on an un-watermarked image reports no detection across all four methods.

## Custom payloads and watermark detection

- **Custom payload:** the user may supply a short payload (e.g. a name or small copyright string)
  in the Sign/Verify interface. It is validated per method against the channel's capacity and is
  embedded as the watermark. This is user-supplied at runtime; it is not a hard-coded identifier,
  so it respects the project's privacy/ethics position (no surveillance-style tracking IDs).
- **Watermark detection (two images):** the user can upload an image and the system decodes it
  with all four methods (TrustMark, LSB, DCT, hybrid), reporting which watermark is present, the
  decoded payload, bit accuracy and confidence. The `Detect` tab in the dashboard exercises
  `POST /api/analyze`.

## Honesty note

The endpoints `/api/sign` and `/api/verify` embed and verify watermark payloads (soft
binding). They are not cryptographic signing: there are no keys, certificates, manifests or
trust chains, and no authenticity verdict is produced. This is reflected in the API response
note and in the FPR (Section 4.1).
