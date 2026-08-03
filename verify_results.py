import csv

with open('output/results/hash_robustness_results.csv', 'r') as f:
    rows = list(csv.DictReader(f))
print('=== HASH ROBUSTNESS RESULTS (all hash types) ===')
print('Total rows:', len(rows))
print('Unique images:', len(set(r['image_id'] for r in rows)))

HASH_NAMES = ['phash', 'dhash', 'ahash', 'whash', 'colorhash',
              'dhash_vertical', 'phash_simple', 'pdq']
TRANSFORM_NAMES = sorted(set(r['transform_name'] for r in rows))

width = max(len(a) for a in HASH_NAMES)
print(f'{"transform":{max(len(t) for t in TRANSFORM_NAMES)}s} | ' + ' | '.join(f'{a:{width}s}' for a in HASH_NAMES))
print('-' * (max(len(t) for t in TRANSFORM_NAMES) + 3 + (width + 3) * len(HASH_NAMES)))
for tf in TRANSFORM_NAMES:
    cells = []
    for a in HASH_NAMES:
        vals = [int(r['hamming_distance'])
                for r in rows if r['transform_name'] == tf and r['hash_algorithm'] == a]
        mean = sum(vals) / len(vals) if vals else float('nan')
        cells.append(f'{mean:{width}.2f}')
    print(f'{tf:{max(len(t) for t in TRANSFORM_NAMES)}s} | ' + ' | '.join(cells))
