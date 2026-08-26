import os, sys
sys.stdout.reconfigure(encoding='utf-8')
checks = [
    ('R2 requirements.txt', os.path.exists('requirements.txt')),
    ('R5 run_all_tests.py', os.path.exists('run_all_tests.py')),
    ('R7 DEMO.md', os.path.exists('DEMO.md')),
    ('R8 .env.example', os.path.exists('.env.example')),
    ('R9 LICENSE', os.path.exists('LICENSE')),
    ('R10 jpeg chart', os.path.exists(os.path.join('output', 'figures', 'jpeg_quality_recovery.png'))),
]
md = open('output/FPR_v1.4.md', encoding='utf-8').read()
checks.append(('R3 contribution in md', 'In a single sentence: this project delivers' in md))
checks.append(('R10 Figure 8 ref in md', 'Figure 8: Payload recovery by JPEG quality' in md))
checks.append(('R1 abstract two-layer', 'two-layer hybrid payload-recovery channel' in md))
checks.append(('R1b conclusion two-layer', '67.3% over TrustMark' in md or '67.3%' in md))
checks.append(('R4 salt-pepper explanation', 'impulsive noise corrupts individual DCT coefficients' in md))
for name, val in checks:
    print(f'{name}: {"OK" if val else "MISSING"}')
print(f'\nrequirements.txt content:')
if os.path.exists('requirements.txt'):
    print(open('requirements.txt').read()[:500])
