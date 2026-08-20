# Final1200 Uncertainty Summary

All summaries use the image as the statistical unit. For hash results, the eight algorithm rows are first reduced within each image and transform condition to a mean and a worst-algorithm bit-error fraction; intervals then span images, not algorithm rows. Continuous metrics use a fixed-seed percentile bootstrap (2,000 resamples); decode proportions use the Wilson binomial 95% interval.

- Images: 1,200
- Bootstrap seed: `20260812`
- Rows written: 646
- Validation: enabled

## Inputs

- `hash`: `hash_robustness_results.csv.gz`
- `trustmark`: `trustmark_robustness_results.csv`
- `lsb`: `lsb_robustness_results.csv`
- `dct`: `dct_robustness_results.csv`

## Fields

`mean`, `median`, and `sd` are descriptive statistics over image-level values. `ci_low` and `ci_high` are 95% confidence limits. The CSV is the machine-readable output; this file documents aggregation and provenance.

## Limitations

- Intervals describe sampling uncertainty across this fixed image sample; they do not model transform implementation, codec, or pipeline uncertainty.
- Images are treated as independent, although image content and dataset selection can be correlated.
- Bootstrap intervals are not used for decode rates because those outcomes are binomial observations.
