# Archive

Moved 2026-08-21 during repository hygiene pass. Nothing was deleted: these are one-off
remediation scripts, report-versioning artefacts, and superseded document versions kept
for traceability. They are not part of the live pipeline and are not expected to run
from this location.

## root_scripts/ — one-off root scripts

One-off remediation, migration, and analysis utilities that were superseded by the
validated pipeline (see README.md "Pipeline Scripts"):

- `fix_ipr.py` — one-off IPR report fixes
- `sync_fpr_md.py` — one-off FPR markdown sync
- `sync_fpr_v13.py` — one-off v1.3 markdown sync
- `remediate_fpr_docx.py` — one-off FPR docx remediation
- `build_fpr_docx.py` — one-off FPR docx builder (superseded report tooling)
- `analyze_stats.py` — one-off statistics analysis for the early draft
- `geometric_sync_experiment.py` — earlier geometric-sync experiment
- `analyze_two_layer.py` — one-off two-layer fallback analysis
- `repair_fallback_baselines.py` — one-off fallback baseline repair
- `ensemble_aware_payload_analysis.py` — superseded by the recorded evidence in
  `output/results/final1200/` (note: `output/results/final1200/reproducibility_record.md`
  preserves the original invocation path as a historical log)
- `create_reproducibility_record.py` — one-off reproducibility record generator
- `migrate_to_db.py` — one-off PostgreSQL schema migration

Kept at root because they are still referenced by submission/pipeline docs:
- `letterbox_hash_pipeline.py` — listed in README.md Pipeline Scripts table
- `generate_remediation_assets.py` — cited in `output/FPR_v1.4.md` governance table (G8)

## reports/ — superseded report versions

Earlier versions of the Final Project Report and IPR report, retained for version
history. The current submissions remain at the repository root:
`24163800_Opaleye_Toluwalope_FPR_v1.4.docx`, `24163800_OpaleyeToluwalope_DPP_v2.docx`,
`24163800_Tolu_Opaleye_IPR_Report_V4.docx`, `MSc Final Project Declaration.docx`.

- `24163800_Opaleye_Toluwalope_FPR.docx`
- `24163800_Opaleye_Toluwalope_FPR_v0.5.docx`
- `24163800_Opaleye_Toluwalope_FPR_v1.0.docx`
- `24163800_Opaleye_Toluwalope_FPR_v1.1.docx`
- `24163800_Opaleye_Toluwalope_FPR_v1.2.docx`
- `24163800_Opaleye_Toluwalope_FPR_v1.3.docx`
- `IPR_Report_V1.docx`
- `IPR_Report_V2.docx`
- `24163800_Tolu_Opaleye_IPR_Report_V3.docx`

## report_scripts/ — one-off report/dashboard check scripts (from scripts/)

Audit, verification, and docx-editing helpers used while producing specific report
versions; they are tied to those versions rather than to the live pipeline:

- `audit_dpp_full.py`, `audit_dpp_ipr.py`
- `check_dashboard_text.py`, `check_fallback_baselines.py`, `check_fallback_csv.py`,
  `check_stale_views.py`, `check_v13.py`
- `find_stale_crossref.py`, `find_stale_views.py`, `fix_crossref.py`, `pg_mentions.py`
- `renumber_tables_v13.py`, `reorder_promise_table.py`,
  `show_promise_table.py`, `show_promise_v14.py`
- `update_docx_dashboard.py`, `update_docx_promise.py`, `update_fpr_v13.py`
- `verify_docx_v13.py`, `verify_docx_v14.py`, `verify_fpr_md.py`,
  `verify_fpr_v11.py`, `verify_fpr_v13.py`
- `test_repair_flow.py` (imports `repair_fallback_baselines`, now in
  `../root_scripts/`), `benchmark_fallback.py`

Kept in `scripts/`: `smoke_test.py`, `test_confidence.py`, `test_detect_watermark.py`,
`test_hybrid_sign_verify.py` (live pipeline tests) and `update_md_promise.py`.
