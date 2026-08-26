from docx import Document
d = Document('24163800_Opaleye_Toluwalope_FPR_v1.4.docx')
for t in d.tables:
    if t.rows[0].cells[0].text.strip() == 'IPR/DPP promise':
        print('promise table, rows:', len(t.rows))
        for i, r in enumerate(t.rows):
            print(f'{i}:', ' | '.join(c.text[:45] for c in r.cells))
        break
