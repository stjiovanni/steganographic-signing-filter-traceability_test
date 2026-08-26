from docx import Document
from docx.oxml.ns import qn
import sys
d = Document('24163800_Opaleye_Toluwalope_FPR_v1.4.docx')
full = []
for c in d.element.body.iterchildren():
    tag = c.tag.split('}')[1]
    if tag in ('p', 'tbl'):
        full.append(''.join(t.text or '' for t in c.iter(qn('w:t'))))
txt = '\n'.join(full).lower()
print('tables:', len(d.tables), '| shapes:', len(d.inline_shapes))
print('no placeholder ->', 'placeholder' not in txt)
print('SSIM delivered ->', 'delivered (10-image sample)' in txt)
print('React delivered ->', 'react (jsx) frontend' in txt and 'delivered' in txt)
print('custom payload ->', 'custom payload (name/copyright)' in txt)
print('watermark detection ->', 'watermark detection (two images)' in txt)
print('confidence output ->', 'confidence score output' in txt)
print('C2PA last-ish ->', 'c2pa/manifest/authenticity' in txt)
sys.stdout.flush()