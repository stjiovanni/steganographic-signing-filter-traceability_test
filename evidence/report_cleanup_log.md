# FPR Report Cleanup Log

Date: 2026-08-26

## Files Changed

- `output/FPR_v1.4.md`: maintained FPR source.
- `CITATIONS.md`: citation register reduced to directly used sources and implementation records.
- `24163800_Opaleye_Toluwalope_FPR_v1.7.docx`: cleaned formatted derivative of the locked v1.6 document.
- `evidence/report_cleanup_log.md`: this audit record.

The source and citation register were edited directly. The v1.6 DOCX could not be saved in place because it was locked by another process; v1.7 is the cleaned derivative and requires coordinator adoption or renaming after review.

## Removed Citations

- Stable Signature / Fernandez et al.
- Gaussian Shading / Yang et al.
- Zhao et al., generative-AI watermark removal.
- Yuan et al., text-to-image watermark removal.
- Jiang et al., AI-generated-content detection evasion.
- NIST SSDF / Souppaya, Scarfone and Dodson.
- American Statistical Association.
- WAVES / An et al.
- Jia, Li, Hayes, Moosavi-Dezfooli, Carlini and Wagner, and Papernot adversarial-attack sources.
- StegaStamp, ReDMark, RoSteALS, HiNet, DeepMIH and distortion-agnostic/invertible watermarking sources.
- Qin, Yan, Tang and Feng hashing sources, and Caldelli/Jin provenance-evaluation sources.
- Ansari, Kulkarni, Pardhu and Sharma classical-watermarking sources.

Their dependent literature-review and future-work prose was removed or reduced to implementation-specific caveats. No removed source remains as an in-text citation or bibliography entry in the cleaned FPR source.

## Retained Citations

- Bui et al. (2025), TrustMark: selected neural implementation and foundational method description.
- Zhu et al. (2018), HiDDeN: foundational learned watermarking context.
- McKeown and Buchanan (2023): perceptual-hash Hamming distributions and threshold caution.
- Lin et al. (2014): MS-COCO dataset record.
- Coalition for Content Provenance and Authenticity (2023): C2PA provenance boundary.
- ISO/IEC 21617-1:2025: JPEG Trust standards context.
- Windisch et al. (2024): separation of coding, raw bit accuracy and corrected recovery.
- BCS Code of Conduct (2026) and ACM Code of Ethics (2018): professional guidance.
- United Kingdom Data Protection Act 2018: future identifier/personal-data handling.

The fallback architecture is described as a local implementation detail. A Mareen citation was not retained because no complete, verifiable bibliography record exists in the workspace; no source was invented.

## Removed Sections And Structural Edits

- Removed the explicit `Appendix I: User-action checklist before submission` and its dependent action/placeholder language.
- Renamed the substantive validation and ethics appendices as requirements, preserving reproducibility, validation, legal and deployment controls.
- Removed the redundant pilot-versus-final Figure 6 reference while retaining the honest 100-image denominator in the evidence boundary and evidence matrix.
- Removed stale “image to be supplied by the author” figure placeholders and replaced them with existing figure-file references in the source.
- Added Figure 8, a captioned reference to the existing data-derived `output/figures/fpr_final1200_method_comparison.png` graph and its final1200 source/denominator.
- Updated the contents/list of figures references for Appendices A-H and Figure 8; corrected affected table references.

## Unresolved DPP/IPR Caveats

- The original hypothesis of payload recovery above 90% across JPEG and PNG is not confirmed. The final1200 JPEG two-layer result is 85.6% for the stated comparison, and PNG was not implemented.
- JPEG was tested; PNG and WebP re-encoding remain unimplemented.
- Custom LUT filters remain undelivered.
- Rotation, scaling and crop were tested, but stretch was not tested.
- GIF/animation handling is outside the still-image benchmark and was not delivered.
- SSIM exists only as a 10-image sample (`output/remediation_ssim.csv`), not as a full final1200 imperceptibility result.
- The 1,200-image result is the principal benchmark. Genuine 100-image pilot/development artefacts remain labelled with their denominator and are not pooled or relabelled as final1200 evidence.

## Verification

File inspection checks confirmed that the cleaned source contains no Stable Signature, Gaussian Shading, Zhao, Yuan, Jiang, NIST SSDF, American Statistical Association, or Appendix I checklist material. The retained bibliography names all have remaining in-text uses, and the retained in-text publication citations have matching bibliography entries. The Figure 8 image exists at `output/figures/fpr_final1200_method_comparison.png`.

Coordinator attention remains required to replace/adopt the locked v1.6 DOCX with v1.7 and to update Word-generated contents/list fields after opening the cleaned document.
