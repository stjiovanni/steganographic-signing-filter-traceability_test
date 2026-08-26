from docx import Document
from docx.oxml.ns import qn

d = Document('24163800_Opaleye_Toluwalope_FPR_v1.3.docx')
# Find any "Table N reports..." / "see Table N" cross-references that may be stale
for p in d.paragraphs:
    t = p.text
    if 'Table 14 reports' in t or ('Table ' in t and 'reports' in t):
        print('CROSSREF:', t[:120])
# Check the two-layer section's JPEG intro line
for p in d.paragraphs:
    if 'Table 14 reports recovery by JPEG' in p.text:
        print('FOUND stale:', p.text[:100])
