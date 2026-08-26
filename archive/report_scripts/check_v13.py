from docx import Document
from docx.oxml.ns import qn

d = Document('24163800_Opaleye_Toluwalope_FPR_v1.3.docx')
seq = []
for c in d.element.body.iterchildren():
    tag = c.tag.split('}')[1]
    if tag in ('p', 'tbl'):
        seq.append((tag, ''.join(t.text or '' for t in c.iter(qn('w:t'))).strip()[:70]))

# Print all captions and new headings
print('=== Tables count:', len(d.tables), '===')
for i, (tag, text) in enumerate(seq):
    low = text.lower()
    if low.startswith('table ') or low.startswith('figure ') or low.startswith('4.11') or 'scope note' in low or 'hypothesis outcome' in low or 'promise versus delivery' in low:
        print(f'{i}\t{tag}\t{text}')
