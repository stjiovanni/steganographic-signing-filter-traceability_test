# Final Consistency Audit

**Audit date:** 2026-08-26  
**Scope:** FPR v1.7, DPP v2, IPR v4, README, `CITATIONS.md`, promise-table evidence, result JSON/CSV summaries, dashboard claims, and `evidence/report_cleanup_log.md`.

## Audit basis and limitation

This was a read-only inspection. Existing files were not changed and no commit was made. Text inspection used `Read`, `Glob`, and `Grep`. The requested DOCX files are present, but `Read` reports them as binary and does not expose their document text; the binary DOCX contents were therefore not independently line-checked in this audit. The conclusions about FPR v1.7, DPP v2, and IPR v4 wording rely on the cleanup log, the maintained FPR source, repository references, and the named report artefacts. The DOCX files must receive a final human/Word comparison before submission.

The current report artefacts are:

| Artefact | Workspace state / audit relevance |
|---|---|
| `24163800_Opaleye_Toluwalope_FPR_v1.7.docx` | Present; described by the cleanup log as the cleaned derivative of locked v1.6. Adoption is still outstanding. |
| `24163800_OpaleyeToluwalope_DPP_v2.docx` | Present; binary text not independently inspected with the permitted read tools. |
| `24163800_Tolu_Opaleye_IPR_Report_V4.docx` | Present; binary text not independently inspected with the permitted read tools. |
| `output/FPR_v1.4.md` | Maintained textual FPR source according to the cleanup log, despite its v1.4 filename and report heading. |
| `evidence/report_cleanup_log.md` | Current cleanup and unresolved-caveat record. |

## Claims that match the evidence

The following claims are supported by the inspected source and evidence summaries, subject to the final DOCX comparison and the validation command being rerun at submission time.

### Dataset and experiment structure

- The dataset is the MS-COCO 2017 validation split, with lexicographically first image selection and seed 42 recorded in `output/results/final1200/reproducibility_record.md`.
- The principal final evidence scale is 1,200 images. The final manifest and reproducibility record both state `image_count: 1200`.
- The transform design has 12 transform families and 80 named transform/intensity conditions. This matches `transforms.py` references, the final threshold summary, and the final API fixture.
- Historical evidence remains a separate 100-image set: 64,000 hash rows, 8,100 rows per watermark method, and an 80-condition matrix. README and FPR v1.4 describe these as historical/baseline rather than final evidence.

### Final result counts and denominators

- Final hash output: 768,000 transformed rows, equal to `1,200 x 8 hash algorithms x 80 conditions`. The final file is compressed as `hash_robustness_results.csv.gz`.
- Final TrustMark, LSB, and DCT outputs: 97,200 rows each, equal to `1,200 baseline rows + 1,200 x 80 transformed rows`. The report correctly says that baseline rows are retained in the source files but excluded from transformed-condition means.
- Final ensemble matrix: 80 transformed-condition rows.
- Final payload/ECC selected configuration: 97,200 rows, corresponding to 1,200 images x 81 variants. The selection record states zero duplicate keys and zero null decodes.
- Development payload/ECC sweep: 97,200 rows, corresponding to 12 configurations x 100 images x 81 variants. The selected configuration is `bch_super_4chars`.

### Headline result values

- Final transformed-condition means in the maintained FPR source are TrustMark raw bit accuracy 0.8517, LSB 0.5878, DCT 0.7198, hash pooled bit-error fraction 0.0737, and hash worst-algorithm bit-error fraction 0.1645. These are condition-level descriptive aggregates, not image-level error rates.
- Final two-layer payload recovery is approximately 67.3% over 96,000 transformed observations, versus approximately 60.7% for TrustMark alone. Table 13 gives the more precise values 67.28% and 60.73%, a difference of 6.55 percentage points. The abstract's rounded 6.6 percentage-point wording is acceptable.
- Final JPEG quality-20 two-layer recovery is 0.9308, or 93.08%, while the overall two-layer result across all transformed conditions is 67.28%. These must not be presented as interchangeable.
- The original >90% across JPEG and PNG hypothesis is correctly recorded as not confirmed: the stated final JPEG comparison is 85.60% in the cleanup log/presentation evidence, and PNG was not implemented. This is a different, narrower JPEG comparison from the 67.28% all-condition transformed result and must retain its comparison definition.
- Final selected payload/ECC component-level corrected-exact recovery is 66.22% in the final1200 result summary. The final ensemble-aware summary reports 89.36% under its separate OR rule. These are different metrics and should remain labelled as such.
- The final uncertainty summary uses the image as the statistical unit, 2,000 bootstrap resamples with seed 20260812 for continuous metrics, and Wilson intervals for decode proportions. It explicitly describes the intervals as descriptive for the fixed sample.

## Stale or contradictory claims

### Blocking contradictions

1. **PostgreSQL status is contradictory inside the maintained FPR source.** FPR v1.4 Table 2 / promise table says PostgreSQL persistence is delivered locally, executed against a live PostgreSQL 16 instance, with verified counts and dashboard database serving. However, FPR Section 4.1 states that the migration “has not been executed against a live database” and that the dashboard is CSV-backed. README says migration was executed and gives final counts; `DEMO.md` and `PROJECT_PRESENTATION_GUIDE.md` also say migrated and verified. One status must be selected and all report/dashboard/README/promise-table wording must match it. The current evidence strongly points to the delivered-local-database wording, but the live database run and count output must be attached or re-run before asserting it.

2. **FPR version and maintained-source naming are stale.** `output/FPR_v1.4.md` is described as maintained, while the cleaned submission derivative is `24163800_Opaleye_Toluwalope_FPR_v1.7.docx`. README still calls v1.6 the matching editable document; `SUBMISSION_MANIFEST.md` still names `24163800_Opaleye_Toluwalope_FPR_v1.4.docx` as the report. This creates a direct risk that the wrong report is submitted. The manifest and README must identify v1.7 as the final checked report, or explicitly identify the actual final filename after coordinator adoption.

3. **The FPR promise-table PostgreSQL row conflicts with the report's own quality-assurance paragraph.** This is not merely historical prose: both statements are in the maintained source. It must be resolved before final PDF export and DOCX adoption.

4. **The 480x480 DPP promise is not met as a full-set implementation claim.** `evidence/480px_check.md` records source short edges below 480 for 754/1,200 images (62.8%) and TrustMark internal encode/decode resolutions of 256/245. Any DPP v2 or IPR v4 wording that says the 480x480 minimum was delivered without this qualification is stale or contradictory. The honest wording is nominal target only, not an enforced full-set or model-operating resolution.

5. **README and `PROJECT_SUMMARY.md` describe different project states.** `PROJECT_SUMMARY.md` is an older 100-image summary and says the database was not executed, the dashboard was CSV-only, and only the 100-image set was complete. README and final evidence describe a 1,200-image final run and local PostgreSQL verification. `PROJECT_SUMMARY.md` must be excluded from final submission or clearly marked archival/stale; it must not be used as a current status document.

6. **README has stale/duplicated pipeline wording.** It lists `dct_robustness.py` twice with different descriptions and says “14 transforms” in the pipeline-status table while the maintained methodology and final evidence use 12 transform families. This is a documentation inconsistency even if the result data use 12 families.

7. **Historical default dashboard data can be mistaken for final evidence.** `csv_store.py` defaults to `output/results`, and the API fixture records the label `historical 100-image` but reports `image_count: 263`, not 100. This is a material dashboard-evidence problem: the historical directory currently contains more than the canonical 100-image result scope, or the summary endpoint is counting rows/images inconsistently. The final demo must set `CSV_DIR=output/results/final1200`, show the `final1200 (validated)` banner, and reconcile why the baseline API fixture reports 263 images.

8. **Dashboard implementation status is mixed across artefacts.** The React frontend exists and includes upload, sign, verify, custom payload, detection, and stress-test UI. The legacy `dashboard/` frontend also remains present. The FPR promise row should name the submitted frontend and its tested server path unambiguously, rather than using “dashboard” generically.

### Claims that are valid only with qualification

- “Stress test delivered” means a live endpoint/UI flow that signs, transforms, and verifies one uploaded image. It does not mean a population-level stress/load test or the full 1,200-image robustness experiment. No `**/*stress*` evidence file was found. Any report statement must use “interactive live stress-test workflow” rather than “stress testing completed” without a run record.
- “Confidence score output” is an API/UI field, not a calibrated probability. The FPR correctly says calibration and false-positive/wrong-payload evaluation remain future work; that qualification must survive in v1.7.
- “PostgreSQL delivered” means local Docker persistence and query integration, not hosted production deployment, access control, availability, security, or performance evidence.
- “SSIM delivered” is only a 10-image sample (`output/remediation_ssim.csv`), not a full final1200 imperceptibility result. The cleanup log correctly records this limitation.
- “Geometric robustness delivered” must retain “rotation, scaling and crop tested; stretch not tested.” The cleanup log explicitly records stretch as undelivered.
- “JPEG/PNG/WebP re-encoding delivered” is incorrect. Only JPEG was implemented; PNG and WebP remain unimplemented.

## Citations retained, removed, and unused

### Retained and currently evidenced

`CITATIONS.md` retains the TrustMark paper and software record, perceptual-hash software records, MS-COCO, ACM, BCS, C2PA, JPEG Trust, McKeown and Buchanan, the UK Data Protection Act, Windisch, and HiDDeN. The maintained FPR bibliography contains matching publication entries for the directly used sources: Bui et al.; Zhu et al.; McKeown and Buchanan; Lin et al.; C2PA; ISO/IEC 21617-1:2025; Windisch et al.; BCS; ACM; and the UK Data Protection Act. The cleanup log says each retained bibliography name has an in-text use. This matches the inspected source.

### Removed

The cleanup log records removal of Stable Signature/Fernandez, Gaussian Shading/Yang, generative-AI removal sources (Zhao and Yuan), AI-detection evasion (Jiang), NIST SSDF, American Statistical Association, WAVES, the listed adversarial-attack sources, StegaStamp/ReDMark/RoSteALS/HiNet/DeepMIH and related watermarking sources, additional hashing/provenance sources, and additional classical-watermarking sources. It also says dependent literature-review/future-work prose was removed or reduced and that no removed source remains in the cleaned FPR source. This is consistent with the retained `CITATIONS.md` statement.

### Remaining unused or potentially unused citation records

- The **TrustMark software record** and **perceptual-hash software records** are intentionally implementation records, not publication citations. They are not unused if the final report keeps the corresponding implementation/version statements, but they should not appear as ordinary bibliography entries unless the DOCX explicitly labels them accordingly.
- The `references/official_sources/` directory contains records for twelve additional references described as used or proposed in older FPR material. They are not in the current `CITATIONS.md` retained list. They are therefore unused by the cleaned final source and should remain outside the final bibliography/submission package unless a final DOCX comparison proves otherwise.
- Windisch et al. is retained for the distinction between coding, raw bit accuracy, and corrected recovery; it must not be described as evidence of an implemented Hadamard comparison. The FPR currently makes that distinction correctly.
- The final DOCX bibliography still requires a direct visual/text comparison against `CITATIONS.md`; this cannot be verified from binary DOCX inspection with the permitted tools.

## 100-image versus 1,200-image wording that must remain

The final submission must preserve both denominators, because they describe different evidence sets:

| Use | Required wording |
|---|---|
| Historical/pilot claims | “validated 100-image historical/pilot experiment” or equivalent; do not call it final1200. Counts are 64,000 hash rows, 8,100 rows per watermark method, and 80 ensemble conditions. |
| Final principal benchmark | “validated final1200 evidence” or “1,200-image final benchmark”; state 1,200 images and the relevant row/condition denominator. |
| Final watermark CSVs | 97,200 rows including 1,200 untransformed baseline rows and 96,000 transformed rows. State when baseline rows are excluded from transformed means. |
| Final hash CSV | 768,000 compressed transformed rows, with no baseline-inclusive comparison to the watermark row count. |
| Final transformed recovery | 96,000 observations (`1,200 x 80`) for the four-method transformed-condition comparison. |
| Development ablation | 97,200 rows at 100-image development scale (`12 x 100 x 81`), separate from the selected 97,200-row final1200 configuration. |
| Dashboard default | Historical `output/results` is the default and must be labelled historical; `CSV_DIR=output/results/final1200` is required for final evidence. |

Never replace “100-image pilot” with “1,200-image result,” and never use a final1200 headline without identifying whether its denominator is 1,200 images, 96,000 transformed observations, 97,200 baseline-inclusive rows, or 80 aggregated conditions.

## PostgreSQL, React, and stress-test status

### PostgreSQL

**Status: locally delivered according to README, promise table, DEMO, and presentation guide; internally contradicted by FPR Section 4.1 and not independently verified here.** The claimed verified counts are 768,000 hash rows, 291,600 combined TrustMark/LSB/DCT watermark rows, 97,200 fallback rows, and 80 ensemble rows. The arithmetic is consistent: `97,200 x 3 = 291,600`. Required evidence is a reproducible migration/probe output or a fresh run, plus one final decision on whether the report claims only local persistence or also claims dashboard database serving.

### React

**Status: delivered in source.** `dashboard-react/package.json`, `src/main.jsx`, `src/App.jsx`, and `src/api.js` establish a React/Vite frontend. The React app includes custom payload handling, detection, and a live stress-test action. This supports a “React frontend delivered” claim, but the final DOCX must be checked to ensure screenshots and prose refer to `dashboard-react/`, not only the older `dashboard/` app.

### Stress test

**Status: interactive workflow implemented; independent stress-test evidence not found.** The API exposes `POST /api/stress_test`; the React UI labels the sequence “Signed -> Transformed -> Verified”; and `evidence/server/README.md` documents upload/sign/verify evidence. However, no stress-specific log/output file was found by globbing, and the binary server output files could not be read with `Read`. Do not claim a completed stress/load-test campaign. Before submission, capture one readable, reproducible stress-test output if the report claims demonstrated stress testing.

## Exact blocking actions before final submission

1. **Adopt the correct report file:** open `24163800_Opaleye_Toluwalope_FPR_v1.7.docx`, update Word contents/list-of-figures fields, verify figures/tables/captions, complete declarations and proofreading fields, and confirm it contains the cleaned source rather than locked v1.6 or v1.4 content.
2. **Update the submission manifest and README report pointers:** replace stale v1.4/v1.6 final-report references with the adopted v1.7 filename and explicitly identify `output/FPR_v1.4.md` as a source only if that is still true.
3. **Resolve PostgreSQL wording globally:** choose “local database migrated and verified” or “migration not executed,” produce the corresponding evidence, then make FPR Section 4.1, Table 2, README, DEMO, presentation guide, and promise tables identical. Do not retain both statuses.
4. **Reconcile the dashboard dataset label/count:** run the dashboard against `CSV_DIR=output/results/final1200`, confirm the API reports 1,200 images and 80 conditions, and explain/fix the baseline fixture showing `historical 100-image` with `image_count: 263` before using dashboard screenshots or claims.
5. **Run and preserve final validation:** execute `validate_experiment.py --image-count 1200 --results-dir output/results/final1200`; record the successful output; verify all four final pipeline files, compressed hash integrity, coverage, uniqueness, missing values, baseline policy, and the selected payload/ECC file's 97,200 rows/zero duplicate keys/zero null decodes.
6. **Reconcile every report number and chart:** compare FPR v1.7, DPP v2, IPR v4, workbook, JSON/CSV summaries, dashboard claims, and captions. In particular check 67.28/60.73/6.55, 85.60 JPEG comparison, 89.36 ensemble-aware rate, 0.8517/0.5878/0.7198, 768,000, 97,200, 96,000, 291,600, 754/1,200, and all baseline-inclusive versus transformed-only statements.
7. **Preserve the honest limitations:** retain not-confirmed >90% JPEG/PNG hypothesis, PNG/WebP absence, no stretch, partial SSIM sample, no cryptographic provenance/authenticity, no calibrated confidence, no wrong-payload/negative-pair proof, and no adaptive/removal attack claim.
8. **Clarify stress-test evidence:** either add a readable reproducibility record for the interactive stress-test demonstration or remove “stress-tested/completed” wording and describe only the implemented endpoint/UI workflow.
9. **Audit citations in the actual DOCX:** confirm every retained bibliography item has an in-text use, every in-text citation has a matching bibliography entry, removed citations do not remain, software records are not misrepresented as publications, and unused official-source files are excluded or explicitly classified as archive.
10. **Package only final artefacts:** exclude `.env`, secrets, caches, temporary files, stale report versions, stale summary documents, partial CSVs, and unverified screenshots. Rename the final report and source artefacts according to the institutional registration-number convention after the coordinator adopts v1.7.

## Final verdict

The final1200 evidence boundary, major result arithmetic, citation cleanup intent, and limitation language are substantially consistent in the inspected textual source. Submission is **blocked** until the v1.7 DOCX is formally adopted and checked, the PostgreSQL contradiction is removed, the dashboard's historical `263` image count is reconciled, final validation is rerun and recorded, and all DPP/IPR promise-table wording is reconciled against the actual DOCX contents. The 100-image pilot and 1,200-image final denominators must remain separate throughout.
