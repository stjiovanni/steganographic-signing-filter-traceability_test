import sys
text = open('output/FPR_v1.1.md', encoding='utf-8').read()
checks = [
    ('front institution', 'University of Hertfordshire' in text),
    ('no placeholder', 'placeholder' not in text),
    ('glossary', 'wrong payload' in text and '**bit accuracy.**' in text),
    ('table5', 'Table 5: Validation gate enforcement audit' in text),
    ('table7', 'Table 7: Final1200 condition-level means' in text),
    ('table8', 'Table 8: Payload/ECC ablation ranking' in text),
    ('table9', 'Table 9: Final1200 image-level uncertainty summary' in text),
    ('sec410', '### 4.10 Uncertainty analysis' in text),
    ('lin ref', 'Microsoft COCO: Common objects in context' in text),
    ('xu pages', 'pp. 7875-7884' in text),
    ('hidden pages', 'pp. 682-697' in text),
    ('auditable verifier', 'auditable image verifier' in text),
    ('screening arrangement', 'two-layer screening arrangement' in text),
    ('config note', 'not retroactively applied to the main benchmark' in text),
    ('csv_dir note', 'CSV_DIR' in text),
    ('caveat x2', text.count('descriptive variant-level pass rate') >= 2),
    ('status col', '| Status |' in text and 'Status in this draft' not in text),
    ('fig list', 'Figure 5: Final1200 per-transform watermark recovery and hash error' in text),
    ('contents list', '## Contents' in text),
]
for k, v in checks:
    print(k, '->', v)
sys.stdout.flush()