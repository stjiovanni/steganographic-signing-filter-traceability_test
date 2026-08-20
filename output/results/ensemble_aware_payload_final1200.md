# Ensemble-Aware Payload/ECC Analysis (final1200 scale)

- Ablation source: `output/results/payload_ecc_ablation_selected_final1200.csv`
- Hash fallback source: `output/results/final1200/hash_robustness_results.csv.gz`

A (image, transform, intensity) variant is **verified** if the TrustMark ECC-corrected
payload decodes exactly **or** the hash fallback passes (worst-algorithm bit-error
fraction < 0.5), matching the threshold logic in `ensemble_analysis.py`.

`rescue = verified(ensemble) - verified(TrustMark alone)` is the fraction of variants
that fail TrustMark but are recovered by the perceptual-hash fallback.

| config | n | TM exact% | ensemble% | hash rescue pp |
|---|---|---|---|---|
| bch_super_4chars | 97200 | 66.22 | 89.36 | +23.14 |
