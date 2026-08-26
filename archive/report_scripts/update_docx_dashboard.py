from docx import Document
import shutil
import os

SRC = '24163800_Opaleye_Toluwalope_FPR_v1.1.docx'
TGT = '24163800_Opaleye_Toluwalope_FPR_v1.2.docx'
if os.path.exists(TGT):
    os.remove(TGT)
shutil.copyfile(SRC, TGT)
d = Document(TGT)

reps = [
    ('The dashboard is CSV-backed and supports overview, per-transform, ensemble, and per-image inspection.',
     'The dashboard is a CSV-backed single-page web application that implements the promised upload, filter, '
     'sign and verify workflow. It shows a dataset banner identifying the active evidence set (historical '
     'output/results by default; set CSV_DIR to output/results/final1200 for the validated final evidence) '
     'and reports verification results per method, including two-layer recovery for the hybrid '
     '(TrustMark + fallback) method.'),
    ('Figure 2 (image to be supplied by the author): Dashboard overview view, final1200 dataset (Section 4.1).',
     'Figure 2 (image to be supplied by the author): Dashboard Sign/Verify interface, upload and preview panes (Section 4.1).'),
    ('Figure 3 (image to be supplied by the author): Dashboard per-transform view, final1200 dataset (Section 4.1).',
     'Figure 3 (image to be supplied by the author): Dashboard verification results, single method (Section 4.1).'),
    ('Figure 4 (image to be supplied by the author): Dashboard ensemble decision-matrix view, final1200 dataset (Section 4.1).',
     'Figure 4 (image to be supplied by the author): Dashboard verification results, hybrid two-layer method (Section 4.1).'),
    ('Figure 2 (image to be supplied by the author): Dashboard overview view with the final1200 dataset active (CSV_DIR=output/results/final1200).',
     'Figure 2 (image to be supplied by the author): Dashboard Sign/Verify interface with the final1200 dataset active (CSV_DIR=output/results/final1200).'),
    ('Figure 3 (image to be supplied by the author): Dashboard per-transform view with the final1200 dataset active (CSV_DIR=output/results/final1200).',
     'Figure 3 (image to be supplied by the author): Dashboard verification results, single method, final1200 dataset active (CSV_DIR=output/results/final1200).'),
    ('Figure 4 (image to be supplied by the author): Dashboard ensemble decision-matrix view with the final1200 dataset active (CSV_DIR=output/results/final1200).',
     'Figure 4 (image to be supplied by the author): Dashboard verification results, hybrid two-layer method, final1200 dataset active (CSV_DIR=output/results/final1200).'),
]
changed = 0
for old, new in reps:
    for p in d.paragraphs:
        if old in p.text:
            text = p.text.replace(old, new)
            for r in list(p.runs):
                r.text = ''
            p.runs[0].text = text
            changed += 1
            break
d.save(TGT)
print('paragraph edits applied:', changed)