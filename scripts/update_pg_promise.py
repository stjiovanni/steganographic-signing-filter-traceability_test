"""Update the PostgreSQL row in the promise-vs-delivery table (DOCX v1.6 + md)
to reflect the now-deployed and verified local Docker PostgreSQL instance."""

from docx import Document
import sys

# ---- DOCX v1.6 ----
d = Document('24163800_Opaleye_Toluwalope_FPR_v1.6.docx')
for t in d.tables:
    if t.rows[0].cells[0].text.strip() == 'IPR/DPP promise':
        for row in t.rows[1:]:
            if 'PostgreSQL' in row.cells[0].text:
                row.cells[1].text = 'Delivered (local Docker PostgreSQL 16)'
                row.cells[2].text = ('migrate_to_db.py executed against a live instance; row counts '
                                     'verified (768,000 hash / 291,600 watermark / 97,200 fallback / 80 '
                                     'ensemble); dashboard serves from the database')
                print('DOCX promise row updated')
                break
        break
d.save('24163800_Opaleye_Toluwalope_FPR_v1.6.docx')

# ---- md ----
path = 'output/FPR_v1.4.md'
t = open(path, encoding='utf-8').read()
old = '| PostgreSQL persistence | Not deployed | CSV persistence; migration not run |'
new = ('| PostgreSQL persistence | Delivered (local Docker PostgreSQL 16) | '
       '`migrate_to_db.py` executed against a live instance; row counts verified '
       '(768,000 hash / 291,600 watermark / 97,200 fallback / 80 ensemble); dashboard serves from the database |')
if old in t:
    t = t.replace(old, new)
    print('md promise row updated')
else:
    print('md anchor not found:', old[:50])
open(path, 'w', encoding='utf-8').write(t)
sys.stdout.flush()