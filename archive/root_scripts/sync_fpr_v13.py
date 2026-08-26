"""Sync the maintained FPR Markdown to v1.3 with the two-layer fallback
experiment, hypothesis outcome, scope note, promise-vs-delivery table, JPEG
quality table, and renumbered tables. Values from the two JSON data files.
"""

import json
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, 'output', 'FPR_v1.1.md')
TGT = os.path.join(ROOT, 'output', 'FPR_v1.3.md')

with open(os.path.join(ROOT, 'output', 'remediation_two_layer.json'), encoding='utf-8') as f:
    TL = json.load(f)
with open(os.path.join(ROOT, 'output', 'remediation_data.json'), encoding='utf-8') as f:
    RD = json.load(f)

with open(SRC, encoding='utf-8') as f:
    text = f.read()

# ---- Version heading ----
text = text.replace('## Final Project Report v1.1', '## Final Project Report v1.3')

# ---- Scope note after title ----
title_anchor = '# Steganographic Signing and Filter Traceability in Digital Media'
assert title_anchor in text
scope = ('\n\n> **Scope note:** this title reflects the proposed project scope. The implemented prototype is a '
         'transformation-aware watermarking and perceptual-hashing screening benchmark: it embeds and verifies '
         'watermark payloads (TrustMark, LSB, DCT and a two-layer hybrid) and compares perceptual hashes under '
         'a graded still-image transform matrix. It does not implement cryptographic signing, key management, '
         'C2PA provenance manifests, a trust chain, or an authenticity verdict.')
text = text.replace(title_anchor, title_anchor + scope)

# ---- Hypothesis outcome after Novelty anchor ----
hypo_anchor = 'The strongest defensible contribution is therefore'
assert hypo_anchor in text
hypo = (f'**Hypothesis outcome.** The interim proposal (IPR, Section 1.1) hypothesised that a hybrid '
        f'TrustMark-plus-perceptual-hash pipeline would achieve payload recovery above 90% across JPEG and PNG. '
        f'The implemented two-layer benchmark at 1,200 images does not confirm that hypothesis: JPEG two-layer '
        f'payload recovery is {TL["hypothesis"]["jpeg_two_layer_recovery"] * 100:.1f}% (TrustMark alone '
        f'{TL["hypothesis"]["jpeg_trustmark_only_recovery"] * 100:.1f}%), below the 90% target; and PNG was never '
        'implemented in the transform matrix. The result is reported as a non-confirmation, not as an achieved '
        'target. The two-layer architecture measurably improves recovery on dimension-preserving conditions '
        '(Section 4.11) but does not reach the stated threshold, and geometric conditions remain near chance '
        'without registration.')
text = text.replace(hypo_anchor, hypo_anchor + '\n\n' + hypo)

# ---- Promise-vs-delivery table (Table 2) after hypothesis outcome ----
delivery = '''| IPR/DPP promise | Status | Evidence |
|---|---|---|
| Payload recovery >90% across JPEG/PNG (hypothesis) | Not confirmed | JPEG two-layer 85.6%; PNG not implemented |
| TrustMark primary watermarking | Delivered | TrustMark final1200 benchmark |
| Perceptual hash fallback | Delivered (similarity screen) | Eight hashes benchmarked |
| Two-layer payload-recovery hybrid | Delivered | Fallback watermark channel, Section 4.11 |
| Filter pipeline (brightness, contrast, saturation) | Delivered | `transforms.py` |
| Custom LUT filters | Not delivered | Listed as future work |
| JPEG/PNG/WebP re-encoding | Partial (JPEG only) | PNG/WebP future work |
| Geometric robustness (crop, rotation, stretch) | Delivered (no stretch) | Rotation/scaling/crops tested |
| PSNR imperceptibility | Delivered | PSNR reported |
| SSIM imperceptibility | Not delivered | PSNR only; SSIM future work |
| Verification interface (web dashboard) | Delivered (Sign/Verify) | FastAPI dashboard |
| PostgreSQL persistence | Not deployed | CSV persistence; migration not run |
| C2PA/manifest/authenticity | Out of scope | Not claimed |

**Table 2: IPR/DPP promise versus delivery (status and evidence; see Section 4.11 for the two-layer result and Section 3.7 for the database).**

This table documents, rather than conceals, the gap between the stated proposal and the implemented deliverable. Items marked "Not confirmed", "Not delivered" or "Not deployed" are not reworded into successes; they are recorded with the evidence (or absence of evidence) that justifies the status.'''
text = text.replace(hypo_anchor + '\n\n' + hypo, hypo_anchor + '\n\n' + hypo + '\n\n' + delivery)

# ---- Renumber existing tables in the body (add 1 to tables 2-12, the old numbering) ----
# The old tables were numbered 1-12. New numbering: T1 objectives, T2 delivery(new), T3 evidence set,
# T4 metrics, T5 gates, T6 gate audit, T7 evidence matrix, T8 final1200 means, T9 ECC, T10 uncertainty,
# T11 risk, T12 gantt, T13 bcs.
renames = [
    ('Table 2: Evidence sets, artefacts and permitted use.', 'Table 3: Evidence sets, artefacts and permitted use.'),
    ('Table 3: Metric definitions and their evidentiary limits.', 'Table 4: Metric definitions and their evidentiary limits.'),
    ('Table 4: Validation gates and failure responses.', 'Table 5: Validation gates and failure responses.'),
    ('Table 5: Validation gate enforcement audit', 'Table 6: Validation gate enforcement audit'),
    ('Table 6: Evidence matrix: claims, sources, scale and permitted wording.', 'Table 7: Evidence matrix: claims, sources, scale and permitted wording.'),
    ('Table 7: Final1200 condition-level means by method and transform', 'Table 8: Final1200 condition-level means by method and transform'),
    ('Table 8: Payload/ECC ablation ranking', 'Table 9: Payload/ECC ablation ranking'),
    ('Table 9: Final1200 image-level uncertainty summary', 'Table 10: Final1200 image-level uncertainty summary'),
    ('Table 10: Threat and risk matrix.', 'Table 13: Threat and risk matrix.'),
    ('Table 11: Project work packages and outcomes.', 'Table 14: Project work packages and outcomes.'),
    ('Table 12: BCS Code of Conduct mapping.', 'Table 15: BCS Code of Conduct mapping.'),
]
for old, new in renames:
    text = text.replace(old, new)

# ---- New Section 4.11 ----
sec5_anchor = '## 5. Evaluation and Conclusion'
assert sec5_anchor in text
ov = TL['overall_transformed']
per_tf = TL['per_transform']
t11_rows = '\n'.join(
    f'| {tf} | {per_tf[tf]["two_layer"]:.4f} | {per_tf[tf]["tm"]:.4f} | {per_tf[tf]["fb"]:.4f} |'
    for tf in ['brightness', 'contrast', 'saturation', 'vibrancy', 'gaussian_blur',
               'salt_pepper_noise', 'jpeg_compression', 'rotation', 'scaling',
               'crop_center', 'crop_random', 'letterbox'])
jq = TL['jpeg_quality_table']
t12_rows = '\n'.join(
    f'| {r["quality"]} | {r["trustmark"]:.4f} | {r["fallback"]:.4f} | {r["two_layer"]:.4f} |' for r in jq)
sec411 = f'''### 4.11 Two-layer payload recovery (fallback watermark channel)

To test the proposed hybrid payload-recovery claim, a second independent payload channel was implemented (Mareen et al., 2021 style): a short BCH_SUPER-coded payload embedded in the DCT domain with repetition and interleaved block placement, decoded by majority vote before BCH correction. The perceptual hash is not a payload channel and is excluded from recovery. Two-layer recovery is defined per (image, transform, intensity) as TrustMark decode-present OR fallback decode-present. Across the 80 transformed conditions ({ov["n"]} observations) the two-layer recovery rate is {ov["two_layer"] * 100:.1f}%, versus {ov["tm"] * 100:.1f}% for TrustMark alone. On the untransformed baseline the two-layer rate is {TL["clean_baseline"]["two_layer"] * 100:.2f}% (TrustMark {TL["clean_baseline"]["trustmark"] * 100:.2f}%), confirming that combined embedding does not materially degrade the primary channel.

| Transform | Two-layer | TrustMark | Fallback |
|---|---|---|---|
{t11_rows}

**Table 11: Final1200 two-layer payload-recovery rate by transform (1,200 images; recovery = TrustMark decode-present OR fallback decode-present; condition-level).**

The fallback channel rescues dimension-preserving conditions: saturation (99.5% two-layer), brightness (92.1%), contrast (91.2%) and vibrancy (94.1%) all exceed the TrustMark-alone rates, and it substantially lifts low-quality JPEG (quality 5: 2.7% to 69.7%; quality 20: 42.3% to 93.1%). It cannot rescue dimension-changing conditions (rotation 25.6%, centre crop 27.3%, random crop 26.6%) because it has no geometric registration; letterbox (10.4%) and scaling (98.7% via TrustMark alone) show the same spatial-alignment boundary. This is the honest empirical limit of the two-layer design: it strengthens value-level and compression recovery but cannot recover a payload whose spatial layout has been destroyed.

Table 12 reports recovery by JPEG quality.

| JPEG quality | TrustMark | Fallback | Two-layer |
|---|---|---|---|
{t12_rows}

**Table 12: Final1200 payload recovery by JPEG quality (1,200 images per setting; decode-present rate).**

Recovery is at or above 90% for quality 65 and above; it drops below 90% at quality 50 and collapses at quality 10 and below, with an irregularity at quality 10 where the fallback ({jq[1]["fallback"] * 100:.1f}%) underperforms TrustMark ({jq[1]["trustmark"] * 100:.1f}%), reflecting codec-dependent interaction rather than monotonic degradation.

'''
text = text.replace(sec5_anchor, sec411 + sec5_anchor)

# ---- Update List of Tables for new numbering ----
lot_start = text.index('## List of tables')
lot_end = text.index('## Glossary')
new_lot = '''## List of tables

- Table 1: Objectives and success criteria (Section 1.3).
- Table 2: IPR/DPP promise versus delivery (Section 1.5).
- Table 3: Evidence sets, artefacts and permitted use (Section 3.2).
- Table 4: Metric definitions and their evidentiary limits (Section 3.5).
- Table 5: Validation gates and failure responses (Section 3.6).
- Table 6: Validation gate enforcement audit (Section 3.6).
- Table 7: Evidence matrix: claims, sources, scale and permitted wording (Section 4.2).
- Table 8: Final1200 condition-level means by method and transform (Section 4.6).
- Table 9: Payload/ECC ablation development-scale ranking (Section 4.7).
- Table 10: Final1200 image-level uncertainty summary (Section 4.10).
- Table 11: Final1200 two-layer payload-recovery rate by transform (Section 4.11).
- Table 12: Final1200 payload recovery by JPEG quality (Section 4.11).
- Table 13: Threat and risk matrix (Section 5.4).
- Table 14: Project work packages and outcomes (Section 5.5).
- Table 15: BCS Code of Conduct mapping (Section 5.6).
'''
text = text[:lot_start] + new_lot + text[lot_end:]

with open(TGT, 'w', encoding='utf-8') as f:
    f.write(text)
print('Wrote', TGT)