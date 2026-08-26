"""Apply the approved remediation plan to the FPR DOCX (v2, text-anchored).

Locates every target paragraph by its content rather than by index, so
insertions cannot shift later edits. Reads the user-updated v1.0 DOCX and
writes v1.1, preserving the user's cover-page and declaration edits.
All inserted numbers come from output/remediation_data.json.
"""

import json
import os

from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt
from docx.text.paragraph import Paragraph

ROOT = os.path.dirname(os.path.abspath(__file__))
SOURCE = os.path.join(ROOT, '24163800_Opaleye_Toluwalope_FPR_v1.0.docx')
TARGET = os.path.join(ROOT, '24163800_Opaleye_Toluwalope_FPR_v1.1.docx')
FIGURES = os.path.join(ROOT, 'output', 'figures')

with open(os.path.join(ROOT, 'output', 'remediation_data.json'), encoding='utf-8') as stream:
    DATA = json.load(stream)

TABLE_CAPTIONS = {
    0: 'Table 1: Objectives and success criteria.',
    1: 'Table 2: Evidence sets, artefacts and permitted use.',
    2: 'Table 3: Metric definitions and their evidentiary limits.',
    3: 'Table 4: Validation gates and failure responses.',
    4: 'Table 6: Evidence matrix: claims, sources, scale and permitted wording.',
    5: 'Table 10: Threat and risk matrix.',
    6: 'Table 11: Project work packages and outcomes.',
    7: 'Table 12: BCS Code of Conduct mapping.',
}

FIGURE_LIST = [
    'Figure 1: Transformation taxonomy and benchmark data flow (Section 3.3).',
    'Figure 2 (image to be supplied by the author): Dashboard overview view, final1200 dataset (Section 4.1).',
    'Figure 3 (image to be supplied by the author): Dashboard per-transform view, final1200 dataset (Section 4.1).',
    'Figure 4 (image to be supplied by the author): Dashboard ensemble decision-matrix view, final1200 dataset (Section 4.1).',
    'Figure 5: Final1200 per-transform watermark recovery and hash error (Section 4.6).',
    'Figure 6: Pilot (100-image) versus final (1,200-image) transformed-row means (Section 4.6).',
    'Figure 7: Payload/ECC ablation development-scale ranking with the selected configuration at 1,200 images (Section 4.7).',
]

TABLE_LIST = [
    'Table 1: Objectives and success criteria (Section 1.3).',
    'Table 2: Evidence sets, artefacts and permitted use (Section 3.2).',
    'Table 3: Metric definitions and their evidentiary limits (Section 3.5).',
    'Table 4: Validation gates and failure responses (Section 3.6).',
    'Table 5: Validation gate enforcement audit (Section 3.6).',
    'Table 6: Evidence matrix: claims, sources, scale and permitted wording (Section 4.2).',
    'Table 7: Final1200 condition-level means by method and transform (Section 4.6).',
    'Table 8: Payload/ECC ablation development-scale ranking (Section 4.7).',
    'Table 9: Final1200 image-level uncertainty summary (Section 4.10).',
    'Table 10: Threat and risk matrix (Section 5.4).',
    'Table 11: Project work packages and outcomes (Section 5.5).',
    'Table 12: BCS Code of Conduct mapping (Section 5.6).',
]

GLOSSARY = [
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


def para_after(paragraph, text='', style=None):
    new_p = OxmlElement('w:p')
    paragraph._p.addnext(new_p)
    new_para = Paragraph(new_p, paragraph._parent)
    if style:
        new_para.style = style
    if text:
        new_para.add_run(text)
    return new_para


def clear_para(paragraph):
    for run in list(paragraph.runs):
        run._r.getparent().remove(run._r)


def set_para_text(paragraph, text):
    clear_para(paragraph)
    if text:
        paragraph.add_run(text)


def replace_in_para(paragraph, old, new):
    if old in paragraph.text:
        set_para_text(paragraph, paragraph.text.replace(old, new))
        return True
    return False


def add_caption_before(table, text):
    caption = OxmlElement('w:p')
    table._tbl.addprevious(caption)
    p = Paragraph(caption, table._parent)
    run = p.add_run(text)
    run.bold = True
    run.font.size = Pt(10)


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


def add_figure_after(doc, ref_para, filename, caption, width_inches=6.3):
    shape_paragraph = doc.add_paragraph()
    shape_paragraph.add_run().add_picture(os.path.join(FIGURES, filename), width=Inches(width_inches))
    ref_para._p.addnext(shape_paragraph._p)
    caption_para = para_after(shape_paragraph)
    number, _, rest = caption.partition(':')
    caption_para.add_run(number + ':').bold = True
    caption_para.add_run(rest)
    for run in caption_para.runs:
        run.font.size = Pt(10)
        run.italic = True
    return caption_para


def find_para(doc, contains, style_prefix=None):
    for p in doc.paragraphs:
        if contains in p.text and (style_prefix is None or p.style.name.startswith(style_prefix)):
            return p
    raise KeyError(f'Paragraph not found: {contains[:60]}')


def add_toc_field(doc, ref_para):
    p = para_after(ref_para)
    run = p.add_run()
    begin = OxmlElement('w:fldChar')
    begin.set(qn('w:fldCharType'), 'begin')
    begin.set(qn('w:dirty'), 'true')
    instruction = OxmlElement('w:instrText')
    instruction.set(qn('xml:space'), 'preserve')
    instruction.text = ' TOC \\o "1-2" \\h \\z \\u '
    separate = OxmlElement('w:fldChar')
    separate.set(qn('w:fldCharType'), 'separate')
    end = OxmlElement('w:fldChar')
    end.set(qn('w:fldCharType'), 'end')
    run._r.extend([begin, instruction, separate, end])
    note = para_after(p, 'If the contents list appears empty, open in Microsoft Word and choose "Update Field" (fields are set to update on open).')
    for run in note.runs:
        run.italic = True
        run.font.size = Pt(9)


def main():
    doc = Document(SOURCE)

    # ---- 1. Front-matter headings and placeholder bodies ----
    set_para_text(find_para(doc, 'Proofreading confirmation placeholder'), 'Proofreading confirmation')

    contents_heading = find_para(doc, 'Contents placeholder')
    set_para_text(contents_heading, 'Contents')
    contents_body = find_para(doc, 'Generate a page-numbered contents list from the final document headings')
    set_para_text(contents_body, '')
    add_toc_field(doc, contents_body)

    figures_heading = find_para(doc, 'List of figures placeholder')
    set_para_text(figures_heading, 'List of figures')
    figures_body = find_para(doc, 'Insert final captions and page numbers after figures are regenerated')
    set_para_text(figures_body, FIGURE_LIST[0])
    anchor = figures_body
    for entry in FIGURE_LIST[1:]:
        anchor = para_after(anchor, entry)

    tables_heading = find_para(doc, 'List of tables placeholder')
    set_para_text(tables_heading, 'List of tables')
    tables_body = find_para(doc, 'Insert final captions and page numbers after final editing')
    set_para_text(tables_body, TABLE_LIST[0])
    anchor = tables_body
    for entry in TABLE_LIST[1:]:
        anchor = para_after(anchor, entry)

    glossary_heading = find_para(doc, 'Glossary placeholder')
    set_para_text(glossary_heading, 'Glossary')
    glossary_body = find_para(doc, 'Add an alphabetised glossary in the formatted submission')
    set_para_text(glossary_body, '')
    anchor = glossary_body
    for term, definition in GLOSSARY:
        anchor = para_after(anchor)
        anchor.add_run(term + '. ').bold = True
        anchor.add_run(definition)

    # ---- 2. Captions on existing tables (document order) ----
    for index, caption in TABLE_CAPTIONS.items():
        add_caption_before(doc.tables[index], caption)

    # Fix draft-era table header
    objectives = doc.tables[0]
    if objectives.cell(0, 2).text.strip() == 'Status in this draft':
        objectives.cell(0, 2).text = 'Status'

    # ---- 3. Textual corrections ----
    replace_in_para(find_para(doc, 'a transformation-aware, calibrated image verifier'),
                    'a transformation-aware, calibrated image verifier',
                    'a transformation-aware, auditable image verifier')
    replace_in_para(find_para(doc, 'isolate the TrustMark layer from the deployed two-layer system'),
                    'the deployed two-layer system', 'the two-layer screening arrangement')
    replace_in_para(find_para(doc, 'The dataset is the MS-COCO 2017 validation split.'),
                    'The dataset is the MS-COCO 2017 validation split.',
                    'The dataset is the MS-COCO 2017 validation split (Lin et al., 2014).')
    replace_in_para(find_para(doc, 'image-level bootstrap or binomial confidence intervals where appropriate;'),
                    'image-level bootstrap or binomial confidence intervals where appropriate;',
                    'confirmatory use of the image-level bootstrap and Wilson intervals now generated for the final1200 set (Section 4.10, Table 9);')
    replace_in_para(find_para(doc, 'but do not provide confidence intervals, false-positive tests'),
                    'but do not provide confidence intervals, false-positive tests, composed attacks, or calibration results',
                    'but provide only descriptive image-level intervals (Table 9); false-positive tests, composed attacks, and calibration results remain absent')
    replace_in_para(find_para(doc, 'improvements needed before deployment: image-level confidence intervals'),
                    'improvements needed before deployment: image-level confidence intervals, image-as-unit analysis,',
                    'improvements needed before deployment: confirmatory calibration of the generated image-level intervals,')

    caveat = (' This figure is a descriptive variant-level pass rate under the declared OR rule; '
              'it is not authentication accuracy, a calibrated probability, or a false-acceptance measure.')
    for needle in ('at 1,200 images the selected configuration reaches 89.36%',
                   'the 1,200-image selected configuration lands at 89.36%'):
        p = find_para(doc, needle)
        if caveat.strip() not in p.text:
            p.add_run(caveat)

    dashboard_para = find_para(doc, 'The dashboard is CSV-backed and supports overview')
    dashboard_para.add_run(' The dashboard reads the historical output/results directory by default; '
                           'setting the CSV_DIR environment variable to output/results/final1200 '
                           'points it at the validated final evidence set.')

    # Configuration note in Section 3.4
    tm_para = find_para(doc, 'TrustMark v0.9.1 is used as the neural candidate')
    note = para_after(tm_para)
    note.add_run('Configuration note: ').bold = True
    note.add_run('the primary four-method benchmark uses TrustMark.Encoding.BCH_4 with the fixed '
                 'payload TM00001. The payload/ECC ablation (Section 4.7) independently evaluates '
                 'BCH_SUPER with a four-character payload; that selected configuration is not '
                 'retroactively applied to the main benchmark results in Sections 4.3 and 4.6.')

    # ---- 4. Table 5: validation gate enforcement audit (Section 3.6) ----
    gates_intro = find_para(doc, 'The existing validator is valuable because')
    t5 = add_table_after(doc, gates_intro,
                         ['Gate', 'Enforcing mechanism', 'Status'],
                         [
                             ['G1 Manifest count, IDs, checksums', 'experiment_manifest.py (creation); checksum re-verification manual', 'Partially enforced'],
                             ['G2 Expected coverage', 'validate_experiment.py', 'Enforced'],
                             ['G3 Duplicate keys', 'validate_experiment.py', 'Enforced'],
                             ['G4 PDQ serialisation', 'Corrected transform_hash_robustness.py; recompute', 'Enforced by correction; not runtime-checked'],
                             ['G5 Raw TrustMark bits before ECC', 'trustmark_robustness.py decode path', 'Enforced in code; not runtime-checked'],
                             ['G6 Missing values, ranges, dimensions', 'analyze_uncertainty.py', 'Partially enforced (separate script)'],
                             ['G7 Transform names match transforms.py', 'Expected counts derived from transforms.py; name drift not explicitly rejected', 'Partially enforced'],
                             ['G8 Tables and figures regenerate', 'generate_figures.py; generate_remediation_assets.py', 'Enforced by regeneration (manual invocation)'],
                             ['G9 Image-level unit and interval', 'analyze_uncertainty.py (final1200 descriptive intervals)', 'Enforced for descriptive summary'],
                             ['G10 Report, dashboard, CSV reconciliation', 'Manual review; this remediation pass', 'Manual'],
                         ])
    add_caption_before(t5, 'Table 5: Validation gate enforcement audit (mechanism and status, from direct code inspection).')
    insert_para_after_table(t5, 'Table 5 records the enforcement mechanism for each gate: coverage and duplicate-key '
                                'gates are enforced by validate_experiment.py; range and interval checks are enforced by '
                                'analyze_uncertainty.py; the remainder are code corrections or manual controls.')

    # ---- 5. Section 4.6: Table 7 and Figures 5-6 ----
    end_46 = find_para(doc, 'A single pooled leaderboard across historical and final1200 rows would be misleading.')
    lead = para_after(end_46)
    lead.add_run('Table 7 reports the final1200 condition-level means by method and transform. '
                 'Watermark means exclude the untransformed baseline rows; hash error is normalised by '
                 'bit length (256 bits for PDQ, 64 for the other algorithms). Across the 80 transformed '
                 f"conditions the overall means are: TrustMark {DATA['final1200_overall']['trustmark']}, "
                 f"LSB {DATA['final1200_overall']['lsb']}, DCT {DATA['final1200_overall']['dct']} raw bit accuracy; "
                 f"hash pooled bit-error fraction {DATA['final1200_overall']['hash_mean_error']} "
                 f"(worst-algorithm {DATA['final1200_overall']['hash_worst_error']}). "
                 'These are descriptive condition-level aggregates, not image-level error rates.')
    t7 = add_table_after(doc, lead,
                         ['Transform', 'TrustMark bit accuracy', 'LSB bit accuracy', 'DCT bit accuracy',
                          'Hash mean bit-error', 'Hash worst-algorithm bit-error'],
                         [[row['transform'], row['trustmark'], row['lsb'], row['dct'],
                           row['hash_mean_error'], row['hash_worst_error']] for row in DATA['t7_final1200']])
    add_caption_before(t7, 'Table 7: Final1200 condition-level means by method and transform '
                           '(1,200 images; watermark rows baseline-inclusive in the source files, excluded here; '
                           'hash error normalised by bit length).')
    anchor = insert_para_after_table(t7, '')
    anchor = add_figure_after(doc, anchor, 'fpr_final1200_method_comparison.png',
                              'Figure 5: Final1200 per-transform watermark recovery and hash error '
                              '(1,200 images; watermark means exclude untransformed baseline rows; '
                              'hash error normalised by hash bit length).')
    anchor = add_figure_after(doc, anchor, 'fpr_pilot_final_comparison.png',
                              'Figure 6: Pilot (100-image) versus final (1,200-image) transformed-row mean raw bit '
                              'accuracy. The two evidence scales are reported separately; differences reflect scale '
                              'and validation controls, not causal algorithm improvement.')

    # ---- 6. Section 4.7: Table 8 and Figure 7 ----
    end_47 = find_para(doc, 'no coding result beyond the tested BCH configurations is claimed.')
    t8_rows = [[row['config'], row['n'], row['corrected_exact_pct'], row['decode_present_pct'],
                row['clean_exact_pct'], 'dev100'] for row in DATA['t8_ecc']]
    sel = DATA['t8_final1200_selected']
    t8_rows.append([sel['config'] + ' (selected)', sel['n'], sel['corrected_exact_pct'], '', '', 'final1200'])
    t8 = add_table_after(doc, end_47,
                         ['Configuration', 'Rows', 'Corrected-exact %', 'Decode-present %',
                          'Clean-image exact %', 'Scale'],
                         t8_rows)
    add_caption_before(t8, 'Table 8: Payload/ECC ablation ranking (12 configurations x 100 images x 81 variants; '
                           'corrected-exact = ECC-corrected payload exactly matches the embedded watermark), '
                           'with the selected configuration validated at 1,200 images.')
    anchor = insert_para_after_table(t8, '')
    add_figure_after(doc, anchor, 'fpr_payload_ecc_dev_sweep.png',
                     'Figure 7: Payload/ECC ablation development-scale ranking (100 images x 81 variants); '
                     'the selected bch_super_4chars configuration is highlighted and its validated 1,200-image '
                     'corrected-exact rate (66.22%) is shown as a dotted reference line.')

    # ---- 7. New Section 4.10: uncertainty ----
    evaluation_heading = find_para(doc, '5. Evaluation and Conclusion', style_prefix='Heading')
    new_heading = OxmlElement('w:p')
    evaluation_heading._p.addprevious(new_heading)
    h = Paragraph(new_heading, evaluation_heading._parent)
    h.style = doc.styles['Heading 2']
    h.add_run('4.10 Uncertainty analysis (final1200)')
    intro = para_after(h)
    intro.add_run('Image-level uncertainty summaries are generated by analyze_uncertainty.py for the final1200 set: '
                  'percentile bootstrap 95% confidence intervals (2,000 resamples, seed 20260812) for continuous '
                  'metrics, and Wilson binomial intervals for decode proportions, with the image as the statistical '
                  'unit. Hash rows are first reduced within each image and condition to mean and worst-algorithm '
                  'bit-error fractions, so intervals span images rather than algorithm rows. Table 9 reports, per '
                  'method and metric, the mean of the 80 per-condition means together with the envelope of the '
                  'per-condition interval bounds (the widest lower and upper bounds observed). The intervals are '
                  'descriptive: they quantify sampling uncertainty across this fixed image set and do not model '
                  'transform implementation, codec, or pipeline uncertainty; images are treated as independent '
                  'although content and selection can be correlated. Their confirmatory use for threshold and '
                  'operating-point selection remains future work (Section 4.9).')
    t9 = add_table_after(doc, intro,
                         ['Method', 'Metric', 'Conditions', 'Images', 'Mean of condition means',
                          'Max condition SD', 'Interval envelope', 'Interval method'],
                         [[row['method'], row['metric'], row['conditions'], row['n_images'],
                           row['mean_of_condition_means'], row['max_condition_sd'],
                           row['ci_envelope'], row['ci_method']] for row in DATA['t9_uncertainty']])
    add_caption_before(t9, 'Table 9: Final1200 image-level uncertainty summary (percentile bootstrap 95% CI, '
                           '2,000 resamples, seed 20260812; Wilson intervals for decode proportions; the envelope '
                           'spans the 80 transformed conditions; untransformed baseline rows excluded).')

    # ---- 8. Figure 1: taxonomy (Section 3.3) ----
    end_33 = find_para(doc, 'These controls improve internal consistency but do not establish robustness against all codecs')
    add_figure_after(doc, end_33, 'fpr_transform_taxonomy.png',
                     'Figure 1: Transformation taxonomy and benchmark data flow. The shared transforms module '
                     'defines 12 categories (80 named conditions); four pipelines consume the same selected images; '
                     'outputs pass coverage validation before analysis.')

    # ---- 9. Screenshot slots (Section 4.1; images to be supplied by the author) ----
    anchor = dashboard_para
    for number, view in ((2, 'overview'), (3, 'per-transform'), (4, 'ensemble decision-matrix')):
        slot = para_after(anchor)
        slot.add_run(f'Figure {number} (image to be supplied by the author): ').bold = True
        slot.add_run(f'Dashboard {view} view with the final1200 dataset active '
                     '(CSV_DIR=output/results/final1200).')
        for run in slot.runs:
            run.italic = True
            run.font.size = Pt(10)
        anchor = slot

    # ---- 10. References corrections and MS-COCO entry ----
    replace_in_para(find_para(doc, 'Robust invertible image steganography'),
                    'pp. 7865-7874', 'pp. 7875-7884')
    replace_in_para(find_para(doc, 'HiDDeN: Hiding data with deep networks'),
                    'pp. 657-672', 'pp. 682-697')
    li_para = find_para(doc, 'Concealed attack for robust watermarking based on generative model')
    lin = para_after(li_para, "Lin, T.-Y., Maire, M., Belongie, S., Hays, J., Perona, P., Ramanan, D., "
                              "Dollár, P. and Zitnick, C.L. (2014) 'Microsoft COCO: Common objects in context', "
                              "European Conference on Computer Vision, pp. 740-755. Springer. "
                              "doi:10.1007/978-3-319-10602-1_48.")

    # ---- 11. Word count (body text, Abstract to end of Conclusion) ----
    in_body = False
    words = 0
    for p in doc.paragraphs:
        text = p.text.strip()
        if p.style.name == 'Heading 1' and text == 'Abstract':
            in_body = True
            continue
        if p.style.name == 'Heading 1' and text == 'References':
            in_body = False
        if in_body:
            words += len(text.split())
    for t in doc.tables:
        for row in t.rows:
            for cell in row.cells:
                words += len(cell.text.split())
    for p in doc.paragraphs:
        if 'Word count:' in p.text:
            set_para_text(p, f'Word count: approximately {words:,} (main text, excluding references and appendices; '
                             'regenerate this figure after final editing)')
            break

    # ---- 12. Update fields on open ----
    settings = doc.settings.element
    update = OxmlElement('w:updateFields')
    update.set(qn('w:val'), 'true')
    settings.append(update)

    doc.save(TARGET)
    print(f'Wrote {TARGET}; body word count {words:,}')


if __name__ == '__main__':
    main()