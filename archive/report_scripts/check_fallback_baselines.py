import csv
rows = list(csv.DictReader(open('output/results/final1200/fallback_robustness_results.csv', encoding='utf-8')))
print('total rows:', len(rows))
print('baseline (none) rows:', sum(1 for r in rows if r['transform_name'] == 'none'))
with_baseline = {r['image_id'] for r in rows if r['transform_name'] == 'none'}
all_ids = {r['image_id'] for r in rows}
print('images missing baseline:', len(all_ids - with_baseline))
print('duplicate keys:', len([(r['image_id'], r['transform_name'], r['intensity_value']) for r in rows]) - len(set((r['image_id'], r['transform_name'], r['intensity_value']) for r in rows)))