from docx import Document
from docx.oxml.ns import qn
import sys

d = Document('24163800_Opaleye_Toluwalope_FPR_v1.6.docx')
full = []
for c in d.element.body.iterchildren():
    tag = c.tag.split('}')[1]
    if tag in ('p', 'tbl'):
        full.append(''.join(t.text or '' for t in c.iter(qn('w:t'))))
txt = '\n'.join(full)
low = txt.lower()

print('tables:', len(d.tables), '| shapes:', len(d.inline_shapes))
print('no to-be-supplied ->', 'to be supplied' not in low)
print('fig2 caption ->', 'figure 2: dashboard sign/verify interface with the validated final1200' in low)
print('fig4 caption ->', 'figure 4: hybrid two-layer verification results' in low)
sys.stdout.flush()