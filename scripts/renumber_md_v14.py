import sys

path = 'output/FPR_v1.4.md'
t = open(path, encoding='utf-8').read()

# 1. Renumber List of Tables entries (13->14, 14->15, 15->16); order avoids collisions
lot = [
    ('- Table 15: BCS Code of Conduct mapping (Section 5.6).', '- Table 16: BCS Code of Conduct mapping (Section 5.6).'),
    ('- Table 14: Project work packages and outcomes (Section 5.5).', '- Table 15: Project work packages and outcomes (Section 5.5).'),
    ('- Table 13: Threat and risk matrix (Section 5.4).', '- Table 14: Threat and risk matrix (Section 5.4).'),
]
for old, new in lot:
    assert old in t, old
    t = t.replace(old, new)

# 2. Insert new Table 13 entry after Table 12 in the List of tables
anchor = '- Table 12: Final1200 payload recovery by JPEG quality (Section 4.11).'
assert anchor in t
t = t.replace(anchor, anchor + '\n- Table 13: Method comparison workbook summary (Section 4.12).')

# 3. Insert body captions for the three inherited tables (they previously had none)
inserts = [
    ('### 5.4 Threats and risk matrix\n',
     '### 5.4 Threats and risk matrix\n\n**Table 14: Threat and risk matrix.**\n'),
    ('### 5.5 Project management and Gantt reflection\n',
     '### 5.5 Project management and Gantt reflection\n\n**Table 15: Project work packages and outcomes.**\n'),
    ('### 5.6 BCS mapping\n',
     '### 5.6 BCS mapping\n\n**Table 16: BCS Code of Conduct mapping.**\n'),
]
for anchor_txt, replacement in inserts:
    assert anchor_txt in t, anchor_txt
    t = t.replace(anchor_txt, replacement)

# 4. Appendix A: mention the comparison workbook
appA = 'The report must identify the exact file version used for every final table.'
if appA in t:
    t = t.replace(appA, 'The method-comparison workbook `FPR_Method_Comparison.xlsx` and the report must identify '
                        'the exact file version used for every final table.')

with open(path, 'w', encoding='utf-8') as f:
    f.write(t)
print('md renumbering complete')
sys.stdout.flush()