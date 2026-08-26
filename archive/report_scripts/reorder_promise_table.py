"""Reorder the promise table in FPR v1.4 so the 4 newly-added delivered rows
(React, custom payload, detection, confidence) come before the C2PA 'out of
scope' row, which should be last."""

from docx import Document
import os, shutil

SRC = '24163800_Opaleye_Toluwalope_FPR_v1.4.docx'
TGT = '24163800_Opaleye_Toluwalope_FPR_v1.4.docx'
d = Document(SRC)

# Locate promise table
promise_table = None
for t in d.tables:
    if t.rows[0].cells[0].text.strip() == 'IPR/DPP promise':
        promise_table = t
        break
if promise_table is None:
    raise SystemExit('promise table not found')

# Read all rows (excluding header) as list of cell-text tuples
rows = []
for r in promise_table.rows[1:]:
    rows.append([c.text for c in r.cells])

# Desired order: keep rows 1..12 as-is (the delivered/partial/not items),
# then the 4 new delivered rows, then C2PA last.
c2pa_row = None
new_rows = []
ordered = []
for row in rows:
    key = row[0]
    if key.startswith('C2PA'):
        c2pa_row = row
    elif key in ('React (JSX) frontend', 'Custom payload (name/copyright)',
                 'Watermark detection (two images)', 'Confidence score output'):
        new_rows.append(row)
    else:
        ordered.append(row)
ordered += new_rows
if c2pa_row is not None:
    ordered.append(c2pa_row)

# Remove existing data rows and re-insert in order
# python-docx: delete all rows except header, then add
import copy
header = promise_table.rows[0]
# Remove all rows except header
for r in list(promise_table.rows[1:]):
    r._tr.getparent().remove(r._tr)

for vals in ordered:
    cells = promise_table.add_row().cells
    for i, v in enumerate(vals):
        cells[i].text = v

d.save(TGT)
print('reordered; final rows:')
for i, r in enumerate(promise_table.rows):
    print(f'{i}:', ' | '.join(c.text[:40] for c in r.cells))