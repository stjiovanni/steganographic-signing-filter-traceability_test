"""Compute the two-layer payload-recovery analysis from the fallback results
and the existing TrustMark results, both at final1200 scale.

Two-layer recovery per (image, transform, intensity):
    recovered = TrustMark decode_present OR fallback decode_present
The perceptual hash is a separate similarity screen and does not count as
payload recovery. Reports per-transform rates, the JPEG quality table, the
overall rate, and the IPR hypothesis outcome.
"""

import csv
import json
import os
from collections import defaultdict

FINAL = os.path.join('output', 'results', 'final1200')
OUT = os.path.join('output', 'remediation_two_layer.json')


def read_csv(directory, name):
    with open(os.path.join(directory, name), newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def main():
    tm = read_csv(FINAL, 'trustmark_robustness_results.csv')
    fb = read_csv(FINAL, 'fallback_robustness_results.csv')

    # index TM decode_present by (image, transform, intensity)
    tm_present = {}
    for r in tm:
        tm_present[(r['image_id'], r['transform_name'], r['intensity_value'])] = r['decode_present'] == 'True'

    fb_present = {}
    fb_by_cond = defaultdict(list)
    for r in fb:
        key = (r['image_id'], r['transform_name'], r['intensity_value'])
        fb_present[key] = r['fb_decode_present'] == 'True'
        fb_by_cond[(r['transform_name'], r['intensity_value'])].append(r)

    # Per (transform, intensity): rates
    stats = defaultdict(lambda: {'n': 0, 'tm': 0, 'fb': 0, 'two_layer': 0})
    for key, fbp in fb_present.items():
        t = stats[key[1:]]
        t['n'] += 1
        t['tm'] += tm_present.get(key, False)
        t['fb'] += fbp
        t['two_layer'] += (tm_present.get(key, False) or fbp)

    per_transform = {}
    jpeg_table = []
    two_layer_total = {'n': 0, 'tm': 0, 'fb': 0, 'two_layer': 0}
    transformed = 0
    for (tf, iv), s in stats.items():
        if tf == 'none':
            continue
        transformed += s['n']
        per_transform.setdefault(tf, {'n': 0, 'tm': 0, 'fb': 0, 'two_layer': 0})
        for k in ('n', 'tm', 'fb', 'two_layer'):
            per_transform[tf][k] += s[k]
        two_layer_total[k]  # noop
    for k in ('n', 'tm', 'fb', 'two_layer'):
        two_layer_total[k] = sum(s[k] for (tf, iv), s in stats.items() if tf != 'none')

    # JPEG quality table (decoding rate by intensity)
    for iv in sorted([iv for (tf, iv) in stats if tf == 'jpeg_compression'], key=lambda x: float(x)):
        s = stats[('jpeg_compression', iv)]
        jpeg_table.append({
            'quality': iv,
            'n': s['n'],
            'trustmark': round(s['tm'] / s['n'], 4),
            'fallback': round(s['fb'] / s['n'], 4),
            'two_layer': round(s['two_layer'] / s['n'], 4),
        })

    # clean baseline
    baseline = stats[('none', '')]
    clean = {
        'n': baseline['n'],
        'trustmark': round(baseline['tm'] / baseline['n'], 4),
        'fallback': round(baseline['fb'] / baseline['n'], 4),
        'two_layer': round(baseline['two_layer'] / baseline['n'], 4),
    }

    overall = {k: round(v / two_layer_total['n'], 4) for k, v in two_layer_total.items()}
    overall['n'] = two_layer_total['n']

    # Hypothesis outcome: >90% payload recovery across JPEG
    jpeg_two = sum(s['two_layer'] for (tf, iv), s in stats.items() if tf == 'jpeg_compression')
    jpeg_n = sum(s['n'] for (tf, iv), s in stats.items() if tf == 'jpeg_compression')
    jpeg_tm = sum(s['tm'] for (tf, iv), s in stats.items() if tf == 'jpeg_compression')
    hypothesis = {
        'ipr_claim': 'Hybrid achieves payload recovery >90% across JPEG',
        'jpeg_two_layer_recovery': round(jpeg_two / jpeg_n, 4),
        'jpeg_trustmark_only_recovery': round(jpeg_tm / jpeg_n, 4),
        'jpeg_n': jpeg_n,
        'confirmed': (jpeg_two / jpeg_n) >= 0.90,
    }

    result = {
        'clean_baseline': clean,
        'overall_transformed': overall,
        'per_transform': {tf: {k: round(v / s['n'], 4) if k != 'n' else v for k, v in s.items()}
                          for tf, s in per_transform.items()},
        'jpeg_quality_table': jpeg_table,
        'hypothesis': hypothesis,
        'baseline_missing': None,
    }

    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)
    print('Wrote', OUT)
    print('overall transformed two-layer recovery:', overall['two_layer'])
    print('hypothesis:', hypothesis)
    print('jpeg table:')
    for row in jpeg_table:
        print('  q=', row['quality'], 'TM=', row['trustmark'], 'FB=', row['fallback'], '2L=', row['two_layer'])


if __name__ == '__main__':
    main()