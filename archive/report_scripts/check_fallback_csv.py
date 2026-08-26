import csv
from collections import Counter
rows = list(csv.DictReader(open('output/results/final1200/fallback_robustness_results.csv', encoding='utf-8')))
print('total rows:', len(rows))
print('unique images:', len({r['image_id'] for r in rows}))
keys = [(r['image_id'], r['transform_name'], r['intensity_value']) for r in rows]
print('dup keys:', len(keys) - len(set(keys)))
print('baseline (none) rows:', sum(1 for r in rows if r['transform_name'] == 'none'))
c = Counter(r['transform_name'] for r in rows)
print('transformed rows by transform:', sum(c.values()) - c.get('none', 0))
ids_with_none = {r['image_id'] for r in rows if r['transform_name'] == 'none'}
all_ids = {r['image_id'] for r in rows}
print('images missing baseline row:', len(all_ids - ids_with_none))
print('TM combined baseline present:', sum(1 for r in rows if r['transform_name']=='none' and r['tm_combined_baseline_present']=='True'))