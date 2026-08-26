from docx import Document

# Full DPP objectives block
d = Document('24163800_OpaleyeToluwalope_DPP_v2.docx')
print('==== DPP objectives + phase list ====')
for i in range(8, 40):
    t = d.paragraphs[i].text.strip()
    if t:
        print(i, '|', t[:300])
