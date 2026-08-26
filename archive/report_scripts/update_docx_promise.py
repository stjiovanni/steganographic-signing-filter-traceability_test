"""Update the DOCX promise-vs-delivery table (Table 2) in FPR v1.3 with the
newly-delivered items (SSIM, React, custom payload, detection, confidence).
Writes v1.4."""

import os
import shutil
from docx import Document

SRC = '24163800_Opaleye_Toluwalope_FPR_v1.3.docx'
TGT = '24163800_Opaleye_Toluwalope_FPR_v1.4.docx'
if os.path.exists(TGT):
    os.remove(TGT)
shutil.copyfile(SRC, TGT)
d = Document(TGT)

# Locate the promise table by its caption text (Table 2: IPR/DPP promise versus delivery)
promise_table = None
for t in d.tables:
    # check caption above
    pass
# Find the table whose first data row header is 'IPR/DPP promise'
for t in d.tables:
    try:
        if t.rows[0].cells[0].text.strip() == 'IPR/DPP promise':
            promise_table = t
            break
    except Exception:
        continue

if promise_table is None:
    print('promise table not found by header; searching by caption')
    # fallback: search all paragraph captions
    from docx.oxml.ns import qn
    for c in d.element.body.iterchildren():
        if c.tag.endswith('}tbl'):
            # skip; handle below by searching all tables
            pass
    # Try all tables
    for t in d.tables:
        header = ' '.join(c.text for c in t.rows[0].cells)
        if 'IPR/DPP promise' in header:
            promise_table = t
            break

if promise_table is None:
    print('ERROR: promise table not located')
    raise SystemExit(1)

print('promise table found, rows:', len(promise_table.rows))

# Update existing cells
row_updates = {
    'SSIM imperceptibility': ['Delivered (10-image sample)', 'output/remediation_ssim.csv; SSIM 0.88-0.97'],
    'Verification interface (web dashboard)': ['Delivered (Sign/Verify, React)', 'FastAPI + React frontend (dashboard-react/)'],
}
for row in promise_table.rows[1:]:
    key = row.cells[0].text.strip()
    if key in row_updates:
        new_vals = row_updates[key]
        for i, val in enumerate(new_vals):
            if i + 1 < len(row.cells):
                row.cells[i + 1].text = val
        print('updated row:', key)

# Add new rows for delivered items
new_rows = [
    ['React (JSX) frontend', 'Delivered', 'dashboard-react/ (Vite + React)'],
    ['Custom payload (name/copyright)', 'Delivered (user-supplied)', 'Sign/Verify payload field; per-method capacity'],
    ['Watermark detection (two images)', 'Delivered', '/api/analyze; Detect tab'],
    ['Confidence score output', 'Delivered', '/api/verify returns confidence + definition'],
]
# Insert before the C2PA row (last row) to keep out-of-scope at the end
c2pa_idx = None
for i, row in enumerate(promise_table.rows):
    if 'C2PA' in row.cells[0].text:
        c2pa_idx = i
        break
# Add rows to the table (append then move is complex; python-docx appends at end)
for vals in new_rows:
    cells = promise_table.add_row().cells
    for i, v in enumerate(vals):
        cells[i].text = v
print('added', len(new_rows), 'rows (appended after C2PA; reorder optional)')

d.save(TGT)
print('Wrote', TGT)
