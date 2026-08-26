# Demo Runbook

## Prerequisites
- PostgreSQL container running: `docker start msc_postgres`
- Server started: `python scripts/serve_db.py` (or `python scripts/serve_final1200.py` for CSV mode)
- Study companion: served at `/companion/` or open `study-companion/index.html` directly

## Demo flow (5 minutes)

### 1. Dashboard overview (30 seconds)
- Open http://127.0.0.1:8000
- Point out the dataset banner: "final1200 (validated), 1200 images"
- Show the stats grid

### 2. Sign and verify (90 seconds)
- Scroll to Sign/Verify
- Upload a COCO image
- Select "Hybrid (TrustMark + Fallback)" method
- Tap Sign → wait for "Signed successfully"
- Tap Verify → show two-layer recovery: Yes, TrustMark 100%, fallback 98%
- Explain: "This is payload recovery, not authentication"

### 3. Custom payload (30 seconds)
- Type a short name in the Payload field
- Sign and verify — show the custom payload is recovered

### 4. Transform damage (60 seconds)
- Apply a filter (e.g. JPEG quality 20)
- Sign and verify — show recovery degrades
- Explain: "This is why we test — to find where signals survive"

### 5. Study companion (60 seconds)
- Navigate to http://127.0.0.1:8000/companion/
- Show a chapter with embedded figures
- Show a quiz question with correct/wrong feedback

### 6. Key numbers to remember
- Two-layer hybrid: 67.3% overall recovery
- TrustMark alone: 60.7%
- DCT: 15.3%, LSB: 4.9%
- JPEG quality 5 rescue: 2.7% → 69.7%
- Hypothesis: NOT confirmed at 90% target
- PostgreSQL: migrated, 768,000 + 291,600 + 97,200 + 80 rows verified

## Anticipated questions
- "Why not 90%?" → Honest: not confirmed; PNG not implemented
- "Is this secure?" → No — it's a benchmark, not a deployed service
- "Why not use SSIM?" → It was implemented late on a 10-image sample; PSNR is the primary imperceptibility metric
- "What about attacks?" → Future work; the benchmark screens benign transforms only
