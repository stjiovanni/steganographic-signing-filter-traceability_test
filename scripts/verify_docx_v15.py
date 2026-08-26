from docx import Document
from docx.oxml.ns import qn
import sys

d = Document('24163800_Opaleye_Toluwalope_FPR_v1.5.docx')
full = []
for c in d.element.body.iterchildren():
    tag = c.tag.split('}')[1]
    if tag in ('p', 'tbl'):
        full.append(''.join(t.text or '' for t in c.iter(qn('w:t'))))
txt = '\n'.join(full)
low = txt.lower()

print('tables:', len(d.tables), '| shapes:', len(d.inline_shapes))
checks = [
    ('sec 4.12 heading', '4.12 method comparison workbook' in low),
    ('workbook named', 'fpr_method_comparison.xlsx' in low),
    ('T13 comparison', 'table 13: method comparison at final1200 scale' in low),
    ('hybrid 67.28', '67.28' in txt),
    ('DCT 15.26', '15.26' in txt),
    ('T14 risk', 'table 14: threat and risk matrix.' in low),
    ('T15 gantt', 'table 15: project work packages and outcomes.' in low),
    ('T16 bcs', 'table 16: bcs code of conduct mapping.' in low),
    ('LoT T13 entry', 'table 13: method comparison workbook summary (section 4.12)' in low),
    ('no stale T13 risk', 'table 13: threat and risk matrix' not in low),
    ('findings para', '6.55 percentage points' in txt),
]
for k, v in checks:
    print(k, '->', v)
sys.stdout.flush()