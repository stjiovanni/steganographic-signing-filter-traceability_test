from docx import Document
from docx.oxml.ns import qn

d = Document('24163800_Opaleye_Toluwalope_FPR_v1.3.docx')
full = []
for c in d.element.body.iterchildren():
    tag = c.tag.split('}')[1]
    if tag in ('p', 'tbl'):
        full.append(''.join(t.text or '' for t in c.iter(qn('w:t'))))
full_txt = '\n'.join(full).lower()
for term in ['per-transform', 'per-image', 'ensemble matrix view', 'overview view', 'overview, per-transform, ensemble']:
    if term in full_txt:
        print('STALE:', term)
    else:
        print('ok:', term)
