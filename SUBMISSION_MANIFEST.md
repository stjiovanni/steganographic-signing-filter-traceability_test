# Final Submission Manifest

## Report

- `24163800_Opaleye_Toluwalope_FPR_v1.7.docx` (cleaned derivative of locked v1.6; `output/FPR_v1.4.md` is the maintained textual source)
- Export the final checked report to PDF after completing the institutional declaration, contents, figures, tables, glossary, and page-number checks.

## Artefact

- Submit the source code as plain text with the institution's required `.txt` naming convention.
- Include the Python pipelines, shared transforms, validation, analysis, dashboard, and experiment configuration.
- Do not include `.env`, database passwords, model caches, or generated temporary files.

## Supporting evidence

- `FPR_Evidence.xlsx`
- `FPR_Improvement_Comparison.xlsx`
- `FPR_Method_Comparison.xlsx`
- `output/results/image_manifest.json` (historical 100-image pilot)
- `output/results/*.csv` (historical 100-image: 64,000 hash rows, 8,100 per watermark, 80 ensemble)
- `output/results/final1200/` (validated final evidence: 768,000 hash rows compressed, 97,200 per watermark, 80 ensemble; 97,200 selected payload/ECC)
- `output/results/payload_ecc_dev_selection.md`
- `output/results/ensemble_aware_payload_dev100.md`
- `output/results/ensemble_aware_payload_final1200.md`
- `output/figures/*` (including `fpr_final1200_method_comparison.png`)
- `output/logs/run_1200_experiment.log`
- `study-companion/` (10 chapters, 100 questions; teaching companion, not evidence)
- `README.md`
- `CITATIONS.md`

## Final checks before submission

- Confirm all four result CSVs pass `python validate_experiment.py --image-count 1200`.
- Confirm the payload/ECC selected-config CSV (`payload_ecc_ablation_selected_final1200.csv`) holds 97,200 rows with 0 duplicate keys and 0 null decodes.
- Regenerate the workbook and figures after validation.
- Check that every report number and caption matches the final CSVs.
- Complete and sign the correct institutional ethics/non-plagiarism declaration.
- Replace all placeholders for name, registration number, module, supervisor, date, and proofreading confirmation.
- Remove `.env` and any secrets from the submission artefact.
- Rename the report and artefact using the required registration-number naming convention.
