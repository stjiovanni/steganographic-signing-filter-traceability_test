# Payload/ECC Ablation — Development-Scale Selection Record

Source (development data only): `output/results/payload_ecc_ablation_dev100.csv`
Validated: 97,200 rows; 12 configs x 100 images x 81 transform variants; 0 duplicate keys; 0 null decodes.

Selection metric: `corrected_exact` (ECC-corrected payload exactly matches embedded watermark) across all 81 variants,
with `corrected_decode_present` and clean-image decode as supporting evidence.

## Overall ranking

| config            | exact%  | present% | raw100% | clean% |
|-------------------|--------|----------|---------|--------|
| bch_super_4chars  |  66.36 |    66.96 |   53.30 |     99 |
| bch_super_5chars  |  66.02 |    66.83 |   52.38 |     99 |
| bch_super_1chars  |  64.80 |    65.63 |   48.65 |     98 |
| bch_5_4chars      |  63.09 |    63.94 |   49.74 |     99 |
| bch_5_5chars      |  62.73 |    63.40 |   49.22 |     99 |
| bch_4_5chars      |  61.72 |    62.56 |   48.01 |     98 |
| bch_4_4chars      |  61.53 |    62.46 |   49.06 |     99 |
| bch_3_5chars      |  60.22 |    61.80 |   49.04 |     98 |
| bch_3_4chars      |  59.12 |    60.79 |   46.63 |     98 |
| bch_4_1chars      |  58.06 |    59.02 |   37.19 |     99 |
| bch_5_1chars      |  58.09 |    58.81 |   34.07 |     98 |
| bch_3_1chars      |  50.28 |    52.53 |   25.85 |     96 |

## Decision

Selected configuration: **BCH_SUPER with 4-character payload (`bch_super_4chars`)**.

Rationale:
- Highest overall corrected-exact rate (66.36%) among all 12 configurations.
- Carries a practical 4-character metadata payload (32 data bits) rather than a single
  character, which is more representative of provenance use (e.g. an identifier).
- Clean-image decode is 99% and unchanged from the weaker ECC modes, so the extra
  redundancy is not bought at the cost of undegraded performance.
- Near-tied with `bch_super_5chars` (66.02%); the 4-char variant chosen as the more
  conservative robustness margin (66.36% vs 66.02%) at one character less payload.

Next step (completed): the selected configuration was run at the full 1,200-image benchmark scale
(`output/results/payload_ecc_ablation_selected_final1200.csv`), validated at 97,200 rows
(0 duplicate keys, 0 null decodes), and re-scored with the ensemble-aware rule
(`output/results/ensemble_aware_payload_final1200.md`). Component-level corrected-exact at
1,200 images is 66.22%; the deployed two-layer rule verifies 89.36%.

## Ensemble-aware view (deployed-system context)

A TrustMark-only ranking isolates the watermark layer. The project's actual verification
system is a two-layer ensemble: TrustMark is primary and the perceptual-hash ensemble is the
fallback (see `ensemble_analysis.py`). Re-scoring every variant as **verified** when either the
ECC-corrected payload decodes exactly OR the hash fallback passes (worst-algorithm bit-error
fraction < 0.5) collapses the config differences:

| config            | TM exact% | ensemble% | hash rescue pp |
|-------------------|-----------|-----------|----------------|
| bch_super_4chars  | 66.36     | 89.59     | +23.23         |
| bch_super_5chars  | 66.02     | 89.60     | +23.58         |
| bch_3_1chars      | 50.28     | 89.32     | +39.04         |
| ... (all 12 configs) | 50–66  | 89.3–89.6 | +23 to +39     |

Full per-config table: `output/results/ensemble_aware_payload_dev100.md`.

Interpretation for the report:
- **The hash fallback is the dominant contributor to end-to-end verification.** It recovers
  23–39 pp of variants that TrustMark alone fails, so all 12 configs land within ~0.3 pp of
  each other (89.3–89.6%) once the deployed system is scored.
- **ECC/payload tuning is a component-level choice, not a system-level lever.** `bch_super_4chars`
  remains the selected default, but its end-to-end advantage over the weakest config is ~0.3 pp,
  not the ~16 pp it showed in isolation.
- **The residual ~10% failure** (100 − 89.6) is where BOTH TrustMark and the hash fail together,
  i.e. extreme geometric/crop degradations that break every signal simultaneously.
- The selection therefore stands on component-level robustness, while the FPR narrative must
  state that system-level robustness is carried by the two-layer architecture, not by TrustMark
  tuning alone.