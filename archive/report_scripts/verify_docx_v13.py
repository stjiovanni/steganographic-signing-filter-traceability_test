from docx import Document
from docx.oxml.ns import qn
import sys

d = Document('24163800_Opaleye_Toluwalope_FPR_v1.3.docx')
seq = []
for c in d.element.body.iterchildren():
    tag = c.tag.split('}')[1]
    if tag in ('p', 'tbl'):
        seq.append((tag, ''.join(t.text or '' for t in c.iter(qn('w:t'))).strip()))
full = '\n'.join(t for _, t in seq).lower()

print('tables:', len(d.tables), '| inline shapes:', len(d.inline_shapes))
print('no placeholder ->', 'placeholder' not in full)
print('toc field ->', 'toc' in full)
print('scope note ->', 'scope note:' in full)
print('hypothesis outcome ->', 'hypothesis outcome' in full and '85.6%' in full)
print('promise table ->', 'ipr/dpp promise versus delivery' in full)
print('section 4.11 ->', '4.11 two-layer payload recovery' in full)
print('T11 two-layer ->', 'table 11: final1200 two-layer payload-recovery rate' in full)
print('T12 jpeg ->', 'table 12: final1200 payload recovery by jpeg quality' in full)
print('lot 15 ->', 'table 15: bcs code of conduct mapping' in full)
print('no stale T14 reports ->', 'table 14 reports recovery by jpeg' not in full)
sys.stdout.flush()