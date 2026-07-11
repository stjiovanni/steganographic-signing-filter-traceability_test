import csv

print('=== HASH ROBUSTNESS RESULTS (all hash types) ===')
with open('output/results/transform_robustness_results.csv', 'r') as f:
    rows = list(csv.DictReader(f))
print('Total rows:', len(rows))
print('Unique images:', len(set(r['image_id'] for r in rows)))

METRICS = [('ph_dist','pHash'),('dh_dist','dHash'),('ah_dist','aHash'),
           ('wh_dist','wHash'),('coh_dist','colorHash'),('dhv_dist','dHashV'),
           ('phs_dist','pHashS'),('pdq_dist','PDQ')]

transforms = sorted(set(r['transform_name'] for r in rows))
for tf in transforms:
    tf_rows = [r for r in rows if r['transform_name'] == tf]
    parts = []
    for metric, label in METRICS:
        vals = [float(r[metric]) for r in tf_rows]
        parts.append(f'{label}={sum(vals)/len(vals):.1f}')
    print(f'{tf:30s} | {"  ".join(parts)}')
