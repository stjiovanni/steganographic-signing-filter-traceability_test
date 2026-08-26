"""Update FPR v1.2 with the two-layer fallback experiment, hypothesis outcome,
promise-vs-delivery table, scope box and JPEG quality table.

All numbers come from output/remediation_two_layer.json and
output/remediation_data.json (data-derived). Writes v1.3.
"""

import json
import os
import shutil

from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.text.paragraph import Paragraph

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, '24163800_Opaleye_Toluwalope_FPR_v1.2.docx')
TGT = os.path.join(ROOT, '24163800_Opaleye_Toluwalope_FPR_v1.3.docx')
if os.path.exists(TGT):
    os.remove(TGT)
shutil.copyfile(SRC, TGT)

with open(os.path.join(ROOT, 'output', 'remediation_two_layer.json'), encoding='utf-8') as f:
    TL = json.load(f)
with open(os.path.join(ROOT, 'output', 'remediation_data.json'), encoding='utf-8') as f:
    RD = json.load(f)

doc = Document(TGT)


def find_para(contains, style_prefix=None):
    for p in doc.paragraphs:
        if contains in p.text and (style_prefix is None or p.style.name.startswith(style_prefix)):
            return p
    raise KeyError(f'Paragraph not found: {contains[:60]}')


def set_para_text(paragraph, text):
    for run in list(paragraph.runs):
        run._r.getparent().remove(run._r)
    paragraph.add_run(text)


def para_after(paragraph, text='', style=None):
    new_p = OxmlElement('w:p')
    paragraph._p.addnext(new_p)
    new_para = Paragraph(new_p, paragraph._parent)
    if style:
        new_para.style = style
    if text:
        new_para.add_run(text)
    return new_para


def add_caption_before(table, text):
    caption = OxmlElement('w:p')
    table._tbl.addprevious(caption)
    p = Paragraph(caption, table._parent)
    run = p.add_run(text)
    run.bold = True


def add_table_after(doc, ref_para, header, rows):
    table = doc.add_table(rows=len(rows) + 1, cols=len(header))
    table.style = 'Table Grid'
    for j, value in enumerate(header):
        cell = table.cell(0, j)
        cell.text = str(value)
        for run in cell.paragraphs[0].runs:
            run.bold = True
    for i, row in enumerate(rows, start=1):
        for j, value in enumerate(row):
            table.cell(i, j).text = str(value)
    ref_para._p.addnext(table._tbl)
    return table


def insert_para_after_table(table, text):
    p = OxmlElement('w:p')
    table._tbl.addnext(p)
    para = Paragraph(p, table._parent)
    para.add_run(text)
    return para

# ---- 1. Scope box on title page (after Project Title paragraph) ----
title_para = find_para('Project Title:')
scope = para_after(title_para)
scope.add_run('Scope note: ').bold = True
scope.add_run('this title reflects the proposed project scope. The implemented prototype is a '
              'transformation-aware watermarking and perceptual-hashing screening benchmark: it embeds and '
              'verifies watermark payloads (TrustMark, LSB, DCT and a two-layer hybrid) and compares perceptual '
              'hashes under a graded still-image transform matrix. It does not implement cryptographic signing, '
              'key management, C2PA provenance manifests, a trust chain, or an authenticity verdict.')

# ---- 2. Hypothesis outcome (Section 1.5 area, after Novelty) ----
hypo_anchor = find_para('The strongest defensible contribution is therefore')
hypo = para_after(hypo_anchor)
hypo.add_run('Hypothesis outcome. ').bold = True
hypo.add_run('The interim proposal (IPR, Section 1.1) hypothesised that a hybrid TrustMark-plus-perceptual-hash '
             'pipeline would achieve payload recovery above 90% across JPEG and PNG. The implemented two-layer '
             'benchmark at 1,200 images does not confirm that hypothesis: JPEG two-layer payload recovery '
             f'is {TL["hypothesis"]["jpeg_two_layer_recovery"] * 100:.1f}% (TrustMark alone '
             f'{TL["hypothesis"]["jpeg_trustmark_only_recovery"] * 100:.1f}%), below the 90% target; and PNG '
             'was never implemented in the transform matrix. The result is reported as a non-confirmation, not '
             'as an achieved target. The two-layer architecture measurably improves recovery on '
             'dimension-preserving conditions (Section 4.11) but does not reach the stated threshold, and '
             'geometric conditions remain near chance without registration.')

# ---- 3. New Section 4.11: Two-layer payload recovery ----
sec5 = find_para('5. Evaluation and Conclusion', style_prefix='Heading')
new_heading = OxmlElement('w:p')
sec5._p.addprevious(new_heading)
h = Paragraph(new_heading, sec5._parent)
h.style = doc.styles['Heading 2']
h.add_run('4.11 Two-layer payload recovery (fallback watermark channel)')

ov = TL['overall_transformed']
intro = para_after(h)
intro.add_run(
    'To test the proposed hybrid payload-recovery claim, a second independent payload channel was implemented '
    '(Mareen et al., 2021 style): a short BCH_SUPER-coded payload embedded in the DCT domain with repetition and '
    'interleaved block placement, decoded by majority vote before BCH correction. The perceptual hash is not a '
    'payload channel and is excluded from recovery. Two-layer recovery is defined per (image, transform, '
    f'intensity) as TrustMark decode-present OR fallback decode-present. Across the 80 transformed conditions '
    f'({ov["n"]} observations) the two-layer recovery rate is {ov["two_layer"] * 100:.1f}%, versus '
    f'{ov["tm"] * 100:.1f}% for TrustMark alone. On the untransformed baseline the two-layer rate is '
    f'{TL["clean_baseline"]["two_layer"] * 100:.2f}% (TrustMark {TL["clean_baseline"]["trustmark"] * 100:.2f}%), '
    'confirming that combined embedding does not materially degrade the primary channel.'
)

per_tf = TL['per_transform']
rows = [[tf,
         per_tf[tf]['two_layer'], per_tf[tf]['tm'], per_tf[tf]['fb']] for tf in
        ['brightness', 'contrast', 'saturation', 'vibrancy', 'gaussian_blur',
         'salt_pepper_noise', 'jpeg_compression', 'rotation', 'scaling',
         'crop_center', 'crop_random', 'letterbox']]
t11 = add_table_after(doc, intro,
                      ['Transform', 'Two-layer', 'TrustMark', 'Fallback'],
                      [[r[0], f'{r[1]:.4f}', f'{r[2]:.4f}', f'{r[3]:.4f}'] for r in rows])
add_caption_before(t11, 'Table 13: Final1200 two-layer payload-recovery rate by transform (1,200 images; '
                        'recovery = TrustMark decode-present OR fallback decode-present; decode rates are '
                        'condition-level).')
anchor = insert_para_after_table(t11, '')
anchor.add_run('The fallback channel rescues dimension-preserving conditions: saturation (99.5% two-layer), '
               'brightness (92.1%), contrast (91.2%) and vibrancy (94.1%) all exceed the TrustMark-alone rates, '
               'and it substantially lifts low-quality JPEG (quality 5: 2.7% to 69.7%; quality 20: 42.3% to '
               '93.1%). It cannot rescue dimension-changing conditions (rotation 25.6%, centre crop 27.3%, '
               'random crop 26.6%) because it has no geometric registration; letterbox (10.4%) and scaling '
               '(98.7% via TrustMark alone) show the same spatial-alignment boundary. This is the honest '
               'empirical limit of the two-layer design: it strengthens value-level and compression recovery '
               'but cannot recover a payload whose spatial layout has been destroyed.')

# JPEG quality table
jq = TL['jpeg_quality_table']
anchor2 = para_after(anchor)
anchor2.add_run('Table 14 reports recovery by JPEG quality.')
t12 = add_table_after(doc, anchor2,
                      ['JPEG quality', 'TrustMark', 'Fallback', 'Two-layer'],
                      [[r['quality'], f"{r['trustmark']:.4f}", f"{r['fallback']:.4f}", f"{r['two_layer']:.4f}"]
                       for r in jq])
add_caption_before(t12, 'Table 14: Final1200 payload recovery by JPEG quality (1,200 images per setting; '
                        'decode-present rate).')
anchor3 = insert_para_after_table(t12, '')
anchor3.add_run('Recovery is at or above 90% for quality 65 and above; it drops below 90% at quality 50 and '
                'collapses at quality 10 and below, with an irregularity at quality 10 where the fallback '
                f'({jq[1]["fallback"] * 100:.1f}%) underperforms TrustMark ({jq[1]["trustmark"] * 100:.1f}%), '
                'reflecting codec-dependent interaction rather than monotonic degradation.')

# ---- 4. Promise-vs-delivery table (Section 1, after Hypothesis outcome) ----
delivery = [
    ['IPR/DPP promise', 'Status', 'Evidence'],
    ['Payload recovery >90% across JPEG/PNG (hypothesis)', 'Not confirmed', 'JPEG two-layer 85.6%; PNG not implemented'],
    ['TrustMark primary watermarking', 'Delivered', 'TM final1200 benchmark'],
    ['Perceptual hash fallback', 'Delivered (similarity screen)', '8 hashes benchmarked'],
    ['Two-layer payload-recovery hybrid', 'Delivered (new, Path B)', 'Fallback watermark channel, Section 4.11'],
    ['Filter pipeline (brightness, contrast, saturation)', 'Delivered', 'transforms.py'],
    ['Custom LUT filters', 'Not delivered', 'Listed as future work'],
    ['JPEG/PNG/WebP re-encoding', 'Partial (JPEG only)', 'PNG/WebP future work'],
    ['Geometric robustness (crop, rotation, stretch)', 'Delivered (no stretch)', 'Rotation/scaling/crops tested'],
    ['PSNR imperceptibility', 'Delivered', 'PSNR reported'],
    ['SSIM imperceptibility', 'Not delivered', 'PSNR only; SSIM future work'],
    ['Verification interface (web dashboard)', 'Delivered (Sign/Verify)', 'FastAPI dashboard'],
    ['PostgreSQL persistence', 'Not deployed', 'CSV persistence; migration not run'],
    ['C2PA/manifest/authenticity', 'Explicitly out of scope', 'Not claimed'],
]
dtable = add_table_after(doc, hypo, delivery[0], delivery[1:])
add_caption_before(dtable, 'Table 2: IPR/DPP promise versus delivery (status and evidence; see Section 4.11 for '
                           'the two-layer result and Section 3.7 for the database).')
insert_para_after_table(dtable, 'This table documents, rather than conceals, the gap between the stated proposal '
                                'and the implemented deliverable. Items marked "Not confirmed", "Not delivered" '
                                'or "Not deployed" are not reworded into successes; they are recorded with the '
                                'evidence (or absence of evidence) that justifies the status.')
# ---- 5. Refine dashboard endpoint description (Section 4.1) ----
dash = find_para('The dashboard is a CSV-backed single-page web application')
if 'hybrid' not in dash.text:
    dash.add_run(' The hybrid method (TrustMark + fallback) is selectable in the Sign/Verify interface and '
                 'reports two-layer recovery; the endpoints /api/sign and /api/verify embed and verify watermark '
                 'payloads only and are not cryptographic signing, with no key management or manifests.')

doc.save(TGT)
print('Wrote', TGT)