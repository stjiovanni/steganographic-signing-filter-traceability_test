"""Create FPR v1.5: adds Section 4.12 method-comparison (Table 13) referencing
FPR_Method_Comparison.xlsx; renumbers risk/Gantt/BCS tables to 14/15/16 in
body captions and the List of Tables."""

import os
import shutil
import re

from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.text.paragraph import Paragraph

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, '24163800_Opaleye_Toluwalope_FPR_v1.4.docx')
TGT = os.path.join(ROOT, '24163800_Opaleye_Toluwalope_FPR_v1.5.docx')
if os.path.exists(TGT):
    os.remove(TGT)
shutil.copyfile(SRC, TGT)
d = Document(TGT)

# ---- 1. Insert Section 4.12 before Section 5 ----
sec5 = None
for p in d.paragraphs:
    if p.text.strip() == '5. Evaluation and Conclusion' and p.style.name.startswith('Heading'):
        sec5 = p
        break
assert sec5 is not None

h = OxmlElement('w:p')
sec5._p.addprevious(h)
heading = Paragraph(h, sec5._parent)
heading.style = d.styles['Heading 2']
heading.add_run('4.12 Method comparison workbook')

intro_p = OxmlElement('w:p')
h.addnext(intro_p)
para = Paragraph(intro_p, sec5._parent)
para.add_run(
    'A consolidated statistical comparison of the implemented channels is provided in '
    'FPR_Method_Comparison.xlsx (three sheets, two native charts, all values computed from the '
    'final1200 result files). The headline comparison of exact payload recovery over the 96,000 '
    'transformed observations is summarised in Table 13.')

# ---- Comparison table (Table 13) ----
from docx.shared import Pt

table = d.add_table(rows=5, cols=4)
table.style = 'Table Grid'
header = ['Channel', 'Payload recovery, transformed (%)', 'Clean-image recovery (%)',
          'Mean raw bit accuracy (%)']
data = [
    ['Hybrid two-layer (TrustMark OR fallback) - ours', '67.28', '99.75', 'not applicable (recovery metric)'],
    ['TrustMark alone', '60.73', '98.75', '85.17'],
    ['DCT baseline', '15.26', '34.33', '71.98'],
    ['LSB baseline (context)', '4.90', '100.00 (definitional)', '58.78'],
]
for j, v in enumerate(header):
    cell = table.cell(0, j)
    cell.text = v
    for run in cell.paragraphs[0].runs:
        run.bold = True
for i, row in enumerate(data, start=1):
    for j, v in enumerate(row):
        table.cell(i, j).text = v

caption = OxmlElement('w:p')
table._tbl.addprevious(caption)
cap = Paragraph(caption, table._parent)
run = cap.add_run('Table 13: Method comparison at final1200 scale (1,200 images x 80 conditions; '
                  'payload recovery = exact decode-present rate; mean raw bit accuracy reported '
                  'separately as it does not imply recovery).')
run.bold = True
run.font.size = Pt(10)

# Move table + caption to just before Section 5 heading, after intro paragraph
sec5._p.addprevious(table._tbl)

finding = OxmlElement('w:p')
table._tbl.addnext(finding)
fp = Paragraph(finding, sec5._parent)
fp.add_run(
    'Three findings follow. First, the hybrid two-layer channel improves exact payload recovery by '
    '6.55 percentage points over TrustMark alone overall (67.28% vs 60.73%), with the rescue '
    'concentrated on dimension-preserving conditions and low-quality JPEG. Second, the DCT '
    "baseline's higher raw bit accuracy (71.98%) than its recovery rate (15.26%) illustrates why "
    'bit accuracy and payload recovery must never be conflated: error correction, not coefficient '
    "agreement, determines whether a message survives. Third, LSB's definitional 100% clean-image "
    'self-decode is retained for transparency but carries no comparative meaning. The full '
    'per-transform breakdown, JPEG quality ladder, and native charts are in the workbook; recovery '
    'by transform is also tabulated in Table 11.')

# ---- 2. Renumber body captions 13->14, 14->15, 15->16 (reverse order) ----
renames = [
    ('Table 15: BCS Code of Conduct mapping.', 'Table 16: BCS Code of Conduct mapping.'),
    ('Table 14: Project work packages and outcomes.', 'Table 15: Project work packages and outcomes.'),
    ('Table 13: Threat and risk matrix.', 'Table 14: Threat and risk matrix.'),
]
changed = 0
for old, new in renames:
    for p in d.paragraphs:
        t = p.text.strip()
        if t == old:
            for r in list(p.runs):
                r._r.getparent().remove(r._r)
            p.add_run(new)
            changed += 1
            break

# ---- 3. Update List of Tables entries ----
lot_renames = [
    ('Table 15: BCS Code of Conduct mapping (Section 5.6).', 'Table 16: BCS Code of Conduct mapping (Section 5.6).'),
    ('Table 14: Project work packages and outcomes (Section 5.5).', 'Table 15: Project work packages and outcomes (Section 5.5).'),
    ('Table 13: Threat and risk matrix (Section 5.4).', 'Table 14: Threat and risk matrix (Section 5.4).'),
]
for old, new in lot_renames:
    for p in d.paragraphs:
        if p.text.strip() == old:
            for r in list(p.runs):
                r._r.getparent().remove(r._r)
            p.add_run(new)
            changed += 1
            break

# Insert new List of Tables entry after Table 12 entry
for p in d.paragraphs:
    if p.text.strip() == 'Table 12: Final1200 payload recovery by JPEG quality (Section 4.11).':
        new_p = OxmlElement('w:p')
        p._p.addnext(new_p)
        np_ = Paragraph(new_p, p._parent)
        np_.add_run('Table 13: Method comparison workbook summary (Section 4.12).')
        changed += 1
        break

d.save(TGT)
print(f'Wrote {TGT}; caption/list edits: {changed}')