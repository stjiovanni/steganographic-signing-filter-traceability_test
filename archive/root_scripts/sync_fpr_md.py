"""Synchronise the maintained FPR Markdown source to v1.1, mirroring the
approved DOCX remediation. Values in new tables come from
output/remediation_data.json (data-derived, not estimated)."""

import json
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
SOURCE = os.path.join(ROOT, 'output', 'FPR_v1.0.md')
TARGET = os.path.join(ROOT, 'output', 'FPR_v1.1.md')

with open(os.path.join(ROOT, 'output', 'remediation_data.json'), encoding='utf-8') as stream:
    DATA = json.load(stream)

with open(SOURCE, encoding='utf-8') as stream:
    text = stream.read()

# ---- Front matter ----
text = text.replace('## Final Project Report Draft v1.0', '## Final Project Report v1.1')
text = text.replace('**Institution:** [insert institution name]', '**Institution:** University of Hertfordshire')
text = text.replace('**School/department:** [insert school or department]',
                    '**School/department:** School of Physics, Engineering and Computer Science')
text = text.replace('**Submission date:** [insert confirmed submission date]', '**Submission date:** 20 August 2026')
text = text.replace('**Word count:** 8,110 (main text, excluding references and appendices)',
                    '**Word count:** approximately 9,700 (main text, excluding references and appendices; '
                    'regenerate after final editing)')

proofread_old = '''### Proofreading confirmation placeholder

I confirm that this report has been proofread for spelling, grammar, structure, terminology, figure and table numbering, cross-references, accessibility, and consistency between the report and its artefacts.

**Proofreader:** [name or approved proofreading arrangement]
**Date:** [insert date]
**Confirmation/signature:** [complete before submission]'''
proofread_new = '''### Proofreading confirmation

I confirm that this report has been proofread for spelling, grammar, structure, terminology, figure and table numbering, cross-references, accessibility, and consistency between the report and its artefacts.

**Proofreader:** Opaleye Toluwalope Abayomi
**Date:** 20/08/2026
**Confirmation/signature:** Opaleye Toluwalope Abayomi'''
text = text.replace(proofread_old, proofread_new)

decl_old_start = text.index('### Institutional ethics and non-plagiarism declaration placeholder')
decl_old_end = text.index('## Contents placeholder')
decl_new = '''### Institutional ethics and non-plagiarism declaration

This report is submitted in partial fulfilment of the requirement for the degree of Master of Science in Computer Science Masters Project, at the University of Hertfordshire.

I hereby declare that the work presented in this project and report is entirely my own, except where explicitly stated otherwise. All sources of information are acknowledged by means of references.

I did not use human participants in my MSc Project.

I hereby give permission for the report to be made available on the university website provided the source is acknowledged.

**Required institutional declaration/form:** the institution's prescribed declaration is completed and signed separately.
'''
text = text[:decl_old_start] + decl_new + text[decl_old_end:]

# ---- Contents, lists, glossary ----
contents_old_start = text.index('## Contents placeholder')
contents_old_end = text.index('## List of figures placeholder')
contents_new = '''## Contents

The page-numbered contents list is generated from the final document headings in the formatted submission. The order is: Abstract; 1 Introduction; 2 Literature Review; 3 Methodology; 4 Quality and Results; 5 Evaluation and Conclusion; References; Appendices A-I; and the user-action checklist. In the DOCX, the contents is a Word field that updates on open.
'''
text = text[:contents_old_start] + contents_new + text[contents_old_end:]

figures_old_start = text.index('## List of figures placeholder')
figures_old_end = text.index('## List of tables placeholder')
figures_new = '''## List of figures

- Figure 1: Transformation taxonomy and benchmark data flow (Section 3.3).
- Figure 2 (image to be supplied by the author): Dashboard overview view, final1200 dataset (Section 4.1).
- Figure 3 (image to be supplied by the author): Dashboard per-transform view, final1200 dataset (Section 4.1).
- Figure 4 (image to be supplied by the author): Dashboard ensemble decision-matrix view, final1200 dataset (Section 4.1).
- Figure 5: Final1200 per-transform watermark recovery and hash error (Section 4.6).
- Figure 6: Pilot (100-image) versus final (1,200-image) transformed-row means (Section 4.6).
- Figure 7: Payload/ECC ablation development-scale ranking with the selected configuration at 1,200 images (Section 4.7).
'''
text = text[:figures_old_start] + figures_new + text[figures_old_end:]

tables_old_start = text.index('## List of tables placeholder')
tables_old_end = text.index('## Glossary placeholder')
tables_new = '''## List of tables

- Table 1: Objectives and success criteria (Section 1.3).
- Table 2: Evidence sets, artefacts and permitted use (Section 3.2).
- Table 3: Metric definitions and their evidentiary limits (Section 3.5).
- Table 4: Validation gates and failure responses (Section 3.6).
- Table 5: Validation gate enforcement audit (Section 3.6).
- Table 6: Evidence matrix: claims, sources, scale and permitted wording (Section 4.2).
- Table 7: Final1200 condition-level means by method and transform (Section 4.6).
- Table 8: Payload/ECC ablation development-scale ranking (Section 4.7).
- Table 9: Final1200 image-level uncertainty summary (Section 4.10).
- Table 10: Threat and risk matrix (Section 5.4).
- Table 11: Project work packages and outcomes (Section 5.5).
- Table 12: BCS Code of Conduct mapping (Section 5.6).
'''
text = text[:tables_old_start] + tables_new + text[tables_old_end:]

glossary_old_start = text.index('## Glossary placeholder')
glossary_old_end = text.index('## Abstract')
glossary_entries = [
    ('bit accuracy', 'The proportion of expected watermark bits recovered. Raw bit accuracy is measured before error correction and does not imply that a valid message was decoded.'),
    ('benign transformation', 'A routine, non-adversarial image operation such as resizing, recompression, filtering or padding, as opposed to a deliberate removal or evasion attack.'),
    ('C2PA', 'The Coalition for Content Provenance and Authenticity specification: an architecture of manifests, assertions, claims, signatures and content bindings for provenance. Not implemented in this project.'),
    ('decode presence', 'A binary outcome recording whether the decoder reported a valid payload. Distinct from raw bit accuracy because error correction can make the two diverge.'),
    ('DCT', 'Discrete cosine transform; the frequency-domain baseline used in this project embeds payload bits differentially in mid-frequency coefficients.'),
    ('false acceptance', 'Accepting an unrelated or incorrectly watermarked image as verified. Not measured in this project; identified as required future work.'),
    ('false rejection', 'Rejecting a genuinely related or correctly watermarked image. Not measured in this project; identified as required future work.'),
    ('Hamming distance', 'The number of differing bits between two hash representations; here, between a reference hash and the hash of a transformed image.'),
    ('hard binding', 'A cryptographic association between claims and exact asset bytes (C2PA terminology), able to detect byte-level change.'),
    ('integrity', 'Evidence that bytes or content are unchanged. Not established by watermark recovery or hash similarity alone.'),
    ('LSB', 'Least-significant-bit embedding; the fragile spatial-domain baseline used in this project.'),
    ('perceptual hash', 'A compact content-derived representation compared by distance (here Hamming distance) to judge perceptual relatedness. A similarity signal, not authentication.'),
    ('provenance', 'A signed, accountable record of claims about an asset. This project evaluates possible soft-binding signals only and does not create provenance records.'),
    ('PSNR', 'Peak signal-to-noise ratio; a pixel-domain encode-quality metric. It measures embedding distortion, not robustness, security or perceptual acceptability.'),
    ('soft binding', 'A content-derived association (fingerprint or watermark) that can help identify transformed or derived content (C2PA terminology).'),
    ('TrustMark', 'The learned image watermarking method (Bui et al., 2025) used as the neural candidate, version 0.9.1, model type Q.'),
    ('transform intensity', 'The parameter value of a named transformation condition (for example JPEG quality 20 or crop removal 0.5). Intensities are comparable only within their own transform family.'),
    ('watermark', 'Information embedded in an image and recovered after transformation; in this project a fixed test payload, never a real identifier.'),
    ('wrong payload', 'A decode event returning a different valid payload from the one embedded. Not measured in this project; identified as required future work.'),
]
glossary_new = '## Glossary\n\n' + '\n'.join(f'- **{term}.** {definition}' for term, definition in glossary_entries) + '\n'
text = text[:glossary_old_start] + glossary_new + text[glossary_old_end:]

# ---- Abstract and body wording ----
text = text.replace('improvements needed before deployment: image-level confidence intervals, image-as-unit analysis,',
                    'improvements needed before deployment: confirmatory calibration of the generated image-level intervals,')
text = text.replace('| Status in this draft |', '| Status |')
text = text.replace('the deployed two-layer system', 'the two-layer screening arrangement')
text = text.replace('a transformation-aware, calibrated image verifier',
                    'a transformation-aware, auditable image verifier')
text = text.replace('The dataset is the MS-COCO 2017 validation split.',
                    'The dataset is the MS-COCO 2017 validation split (Lin et al., 2014).')

config_note = ('Configuration note: the primary four-method benchmark uses TrustMark.Encoding.BCH_4 with the fixed '
               'payload TM00001. The payload/ECC ablation (Section 4.7) independently evaluates BCH_SUPER with a '
               'four-character payload; that selected configuration is not retroactively applied to the main '
               'benchmark results in Sections 4.3 and 4.6.')
tm_anchor = "TrustMark v0.9.1 is used as the neural candidate with a fixed test payload `TM00001` (Bui et al., 2025). The source image is encoded, transformed, and decoded."
assert tm_anchor in text
text = text.replace(tm_anchor, tm_anchor + '\n\n' + config_note)

gate_anchor = 'The existing validator is valuable because a command using `--image-count 100` cannot validate 1,200-image coverage. The final validation checks each pipeline and the combined comparison separately. A compressed CSV must be decompressed or read with an integrity check before its row count and unique keys are accepted.'
assert gate_anchor in text
gate_table = '''| Gate | Enforcing mechanism | Status |
|---|---|---|
| G1 Manifest count, IDs, checksums | `experiment_manifest.py` (creation); checksum re-verification manual | Partially enforced |
| G2 Expected coverage | `validate_experiment.py` | Enforced |
| G3 Duplicate keys | `validate_experiment.py` | Enforced |
| G4 PDQ serialisation | Corrected `transform_hash_robustness.py`; recompute | Enforced by correction; not runtime-checked |
| G5 Raw TrustMark bits before ECC | `trustmark_robustness.py` decode path | Enforced in code; not runtime-checked |
| G6 Missing values, ranges, dimensions | `analyze_uncertainty.py` | Partially enforced (separate script) |
| G7 Transform names match `transforms.py` | Expected counts derived from `transforms.py`; name drift not explicitly rejected | Partially enforced |
| G8 Tables and figures regenerate | `generate_figures.py`; `generate_remediation_assets.py` | Enforced by regeneration (manual invocation) |
| G9 Image-level unit and interval | `analyze_uncertainty.py` (final1200 descriptive intervals) | Enforced for descriptive summary |
| G10 Report, dashboard, CSV reconciliation | Manual review; this remediation pass | Manual |

**Table 5: Validation gate enforcement audit (mechanism and status, from direct code inspection).**

Table 5 records the enforcement mechanism for each gate: coverage and duplicate-key gates are enforced by `validate_experiment.py`; range and interval checks are enforced by `analyze_uncertainty.py`; the remainder are code corrections or manual controls.'''
text = text.replace(gate_anchor, gate_anchor + '\n\n' + gate_table)

text = text.replace('image-level bootstrap or binomial confidence intervals where appropriate;',
                    'confirmatory use of the image-level bootstrap and Wilson intervals now generated for the final1200 set (Section 4.10, Table 9);')
text = text.replace('but do not provide confidence intervals, false-positive tests, composed attacks, or calibration results',
                    'but provide only descriptive image-level intervals (Table 9); false-positive tests, composed attacks, and calibration results remain absent')

dash_anchor = 'It is a research visualisation and not a production signing service. The database migration exists but has not been executed against a live database; therefore database security, performance, and access control are not evaluated outcomes.'
assert dash_anchor in text
text = text.replace(dash_anchor, dash_anchor + ' The dashboard reads the historical `output/results` directory by default; setting the `CSV_DIR` environment variable to `output/results/final1200` points it at the validated final evidence set.')

caveat = ' This figure is a descriptive variant-level pass rate under the declared OR rule; it is not authentication accuracy, a calibrated probability, or a false-acceptance measure.'
for needle in ('at 1,200 images the selected configuration reaches 89.36%.',
               'the 1,200-image selected configuration lands at 89.36%.'):
    assert needle in text
    text = text.replace(needle, needle + caveat)

# ---- Table 7 (Section 4.6) ----
t7_anchor = 'A single pooled leaderboard across historical and final1200 rows would be misleading.'
assert t7_anchor in text
overall = DATA['final1200_overall']
t7_lead = (f'Table 7 reports the final1200 condition-level means by method and transform. Watermark means '
           f'exclude the untransformed baseline rows; hash error is normalised by bit length (256 bits for PDQ, '
           f'64 for the other algorithms). Across the 80 transformed conditions the overall means are: '
           f'TrustMark {overall["trustmark"]}, LSB {overall["lsb"]}, DCT {overall["dct"]} raw bit accuracy; '
           f'hash pooled bit-error fraction {overall["hash_mean_error"]} (worst-algorithm '
           f'{overall["hash_worst_error"]}). These are descriptive condition-level aggregates, not image-level error rates.')
t7_rows = '\n'.join(
    f'| {r["transform"]} | {r["trustmark"]} | {r["lsb"]} | {r["dct"]} | {r["hash_mean_error"]} | {r["hash_worst_error"]} |'
    for r in DATA['t7_final1200'])
t7_block = (t7_lead + '\n\n'
            '| Transform | TrustMark bit accuracy | LSB bit accuracy | DCT bit accuracy | Hash mean bit-error | Hash worst-algorithm bit-error |\n'
            '|---|---|---|---|---|---|\n' + t7_rows + '\n\n'
            '**Table 7: Final1200 condition-level means by method and transform (1,200 images; watermark rows baseline-inclusive in the source files, excluded here; hash error normalised by bit length).**\n\n'
            'Figure 5 visualises the watermark and hash values in Table 7; Figure 6 shows the pilot-versus-final scale comparison.')
text = text.replace(t7_anchor, t7_anchor + '\n\n' + t7_block)

# ---- Table 8 (Section 4.7) ----
t8_anchor = 'The full config sweep and selection rationale are recorded in `output/results/payload_ecc_dev_selection.md`.'
assert t8_anchor in text
sel = DATA['t8_final1200_selected']
t8_rows = '\n'.join(
    f'| {r["config"]} | {r["n"]} | {r["corrected_exact_pct"]} | {r["decode_present_pct"]} | {r["clean_exact_pct"]} | dev100 |'
    for r in DATA['t8_ecc'])
t8_rows += f'\n| {sel["config"]} (selected) | {sel["n"]} | {sel["corrected_exact_pct"]} |  |  | final1200 |'
t8_block = ('| Configuration | Rows | Corrected-exact % | Decode-present % | Clean-image exact % | Scale |\n'
            '|---|---|---|---|---|---|\n' + t8_rows + '\n\n'
            '**Table 8: Payload/ECC ablation ranking (12 configurations x 100 images x 81 variants; corrected-exact = '
            'ECC-corrected payload exactly matches the embedded watermark), with the selected configuration validated at 1,200 images.**\n\n'
            'Figure 7 visualises the development-scale ranking in Table 8.')
text = text.replace(t8_anchor, t8_anchor + '\n\n' + t8_block)

# ---- New Section 4.10 ----
sec5_anchor = '## 5. Evaluation and Conclusion'
assert sec5_anchor in text
t9_rows = '\n'.join(
    f'| {r["method"]} | {r["metric"]} | {r["conditions"]} | {r["n_images"]} | {r["mean_of_condition_means"]} | '
    f'{r["max_condition_sd"]} | {r["ci_envelope"]} | {r["ci_method"]} |'
    for r in DATA['t9_uncertainty'])
sec410 = '''### 4.10 Uncertainty analysis (final1200)

Image-level uncertainty summaries are generated by `analyze_uncertainty.py` for the final1200 set: percentile bootstrap 95% confidence intervals (2,000 resamples, seed 20260812) for continuous metrics, and Wilson binomial intervals for decode proportions, with the image as the statistical unit. Hash rows are first reduced within each image and condition to mean and worst-algorithm bit-error fractions, so intervals span images rather than algorithm rows. Table 9 reports, per method and metric, the mean of the 80 per-condition means together with the envelope of the per-condition interval bounds (the widest lower and upper bounds observed). The intervals are descriptive: they quantify sampling uncertainty across this fixed image set and do not model transform implementation, codec, or pipeline uncertainty; images are treated as independent although content and selection can be correlated. Their confirmatory use for threshold and operating-point selection remains future work (Section 4.9).

| Method | Metric | Conditions | Images | Mean of condition means | Max condition SD | Interval envelope | Interval method |
|---|---|---|---|---|---|---|---|
''' + t9_rows + '''

**Table 9: Final1200 image-level uncertainty summary (percentile bootstrap 95% CI, 2,000 resamples, seed 20260812; Wilson intervals for decode proportions; the envelope spans the 80 transformed conditions; untransformed baseline rows excluded).**

'''
text = text.replace(sec5_anchor, sec410 + sec5_anchor)

# ---- References ----
text = text.replace('pp. 7865-7874', 'pp. 7875-7884')
text = text.replace('*European Conference on Computer Vision*, pp. 657-672.',
                    '*European Conference on Computer Vision*, pp. 682-697.')
lin_ref = ("Lin, T.-Y., Maire, M., Belongie, S., Hays, J., Perona, P., Ramanan, D., Dollár, P. and Zitnick, C.L. (2014) "
           "'Microsoft COCO: Common objects in context', *European Conference on Computer Vision*, pp. 740-755. Springer. "
           "doi:10.1007/978-3-319-10602-1_48.")
li_doi = 'doi:10.1109/TCSVT.2021.3138795.'
assert li_doi in text
idx = text.index(li_doi)
line_end = text.index('\n', idx)
text = text[:line_end + 1] + lin_ref + '\n' + text[line_end + 1:]

with open(TARGET, 'w', encoding='utf-8') as stream:
    stream.write(text)
print('Wrote', TARGET)