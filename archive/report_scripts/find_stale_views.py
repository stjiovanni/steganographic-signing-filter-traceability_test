from docx import Document
from docx.oxml.ns import qn

d = Document('24163800_Opaleye_Toluwalope_FPR_v1.3.docx')
for c in d.element.body.iterchildren():
    tag = c.tag.split('}')[1]
    if tag != 'p':
        continue
    txt = ''.join(t.text or '' for t in c.iter(qn('w:t')))
    if 'per-transform' in txt.lower() or 'per-image' in txt.lower():
        print('P:', txt[:220])
        print('---')
# also tables
for ti, t in enumerate(d.tables):
    for r in t.rows:
        for cell in r.cells:
            if 'per-transform' in cell.text.lower() or 'per-image' in cell.text.lower():
                print(f'TABLE {ti}:', cell.text[:150])
