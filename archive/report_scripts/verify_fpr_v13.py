import sys
text = open('output/FPR_v1.3.md', encoding='utf-8').read()
checks = [
    ('version 1.3', 'Final Project Report v1.3' in text),
    ('scope note', 'Scope note:' in text),
    ('hypothesis outcome', 'Hypothesis outcome' in text and '85.6%' in text),
    ('promise table T2', 'Table 2: IPR/DPP promise versus delivery' in text),
    ('section 4.11', '### 4.11 Two-layer payload recovery' in text),
    ('T11 two-layer', 'Table 11: Final1200 two-layer payload-recovery rate' in text),
    ('T12 jpeg', 'Table 12: Final1200 payload recovery by JPEG quality' in text),
    ('jpeg q5 69.7', '2.7% to 69.7%' in text),
    ('jpeg q20 93.1', '42.3% to 93.1%' in text),
    ('lot has 15', 'Table 15: BCS Code of Conduct mapping' in text),
    ('lot T2 delivery', '- Table 2: IPR/DPP promise versus delivery' in text),
    ('no stale Table 14 reports', 'Table 14 reports recovery by JPEG' not in text),
    ('evidence set now T3', 'Table 3: Evidence sets' in text),
    ('overall 67.3', '67.3%' in text),
]
for k, v in checks:
    print(k, '->', v)
sys.stdout.flush()