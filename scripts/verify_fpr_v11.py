from docx import Document
from docx.oxml.ns import qn
import sys

d = Document('24163800_Opaleye_Toluwalope_FPR_v1.1.docx')
seq = []
for c in d.element.body.iterchildren():
    tag = c.tag.split('}')[1]
    if tag in ('p', 'tbl'):
        seq.append((tag, ''.join(t.text or '' for t in c.iter(qn('w:t'))).strip()))
full = '\n'.join(t for _, t in seq).lower()

print('SEQ-CHECK')
for i, (tag, text) in enumerate(seq):
    low = text.lower()
    if any(k in low for k in ('3.7 reproducibility', 'table 5 records', '4.8 evidence',
                              'figure 7: payload', '4.10 uncertainty', '5. evaluation',
                              'table 6: evidence matrix', '4.6 final1200 evidence',
                              '4.7 payload/ecc')):
        print(f'{i}\t{tag}\t{text}')

print('CHECKS')
checks = [
    ('no draft wording', 'in this draft' not in full),
    ('no placeholder', 'placeholder' not in full),
    ('lin coco', 'microsoft coco: common objects in context' in full),
    ('xu pages', 'pp. 7875-7884' in full),
    ('hidden pages', 'pp. 682-697' in full),
    ('config note', 'not retroactively applied to the main benchmark' in full),
    ('csv_dir note', 'csv_dir environment variable' in full),
    ('caveat twice', full.count('descriptive variant-level pass rate under the declared or rule') == 2),
    ('auditable verifier', 'auditable image verifier' in full and 'calibrated image verifier' not in full),
    ('screening arrangement', 'two-layer screening arrangement' in full),
    ('word count', 'approximately 9,726' in full),
    ('screenshot slots', full.count('image to be supplied by the author')),
    ('glossary wrong payload', 'wrong payload' in full),
    ('toc field', 'toc' in full),
]
for name, value in checks:
    print(f'{name} -> {value}')
print('tables ->', len(d.tables), '| shapes ->', len(d.inline_shapes))
sys.stdout.flush()
