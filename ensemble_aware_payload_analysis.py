"""Ensemble-aware payload/ECC analysis (dev scale).

Joins the payload/ECC ablation rows with the perceptual-hash fallback rows to
measure the deployed-system verification rate: a (image, transform, intensity)
variant counts as VERIFIED if the TrustMark watermark decodes exactly OR the
hash fallback passes (worst-algorithm bit-error fraction < 0.5), matching the
threshold logic in ensemble_analysis.py.
"""

import argparse
import csv
import gzip
import os

ABLATION = 'output/results/payload_ecc_ablation_dev100.csv'
HASH = 'output/results/final1200/hash_robustness_results.csv.gz'
OUT = 'output/results/ensemble_aware_payload_dev100.md'
SCALE_LABEL = 'development'
HASH_NAMES = ['phash', 'dhash', 'ahash', 'whash', 'colorhash', 'dhash_vertical', 'phash_simple', 'pdq']
HASH_BITS = {name: (256 if name == 'pdq' else 64) for name in HASH_NAMES}
HASH_FAIL50 = 0.5


def parse_float(s):
    try:
        return float(s)
    except (ValueError, TypeError):
        return None


def load_hash():
    path = HASH
    open_fn = gzip.open if path.endswith('.gz') else open
    rows = list(csv.DictReader(open_fn(path, 'rt', newline='', encoding='utf-8')))
    by_variant = {}
    for r in rows:
        algo = r.get('hash_algorithm')
        if algo not in HASH_BITS:
            continue
        d = parse_float(r.get('hamming_distance'))
        if d is None:
            continue
        key = (r['image_id'], r['transform_name'], r['intensity_value'])
        by_variant.setdefault(key, []).append(d / HASH_BITS[algo])
    return {k: max(vals) for k, vals in by_variant.items()}


def load_ablation():
    rows = list(csv.DictReader(open(ABLATION, newline='', encoding='utf-8')))
    configs = {}
    for r in rows:
        configs.setdefault(r['config_id'], []).append(r)
    return configs


def main():
    hash_worst = load_hash()
    configs = load_ablation()

    lines = []
    lines.append(f'# Ensemble-Aware Payload/ECC Analysis ({SCALE_LABEL} scale)')
    lines.append('')
    lines.append(f'- Ablation source: `{ABLATION}`')
    lines.append(f'- Hash fallback source: `{HASH}`')
    lines.append('')
    lines.append('A (image, transform, intensity) variant is **verified** if the TrustMark ECC-corrected')
    lines.append('payload decodes exactly **or** the hash fallback passes (worst-algorithm bit-error')
    lines.append('fraction < 0.5), matching the threshold logic in `ensemble_analysis.py`.')
    lines.append('')
    lines.append('`rescue = verified(ensemble) - verified(TrustMark alone)` is the fraction of variants')
    lines.append('that fail TrustMark but are recovered by the perceptual-hash fallback.')
    lines.append('')
    lines.append('| config | n | TM exact% | ensemble% | hash rescue pp |')
    lines.append('|---|---|---|---|---|')

    rows_out = []
    for config in sorted(configs):
        rows = configs[config]
        n = len(rows)
        tm_ok = 0
        ens_ok = 0
        for r in rows:
            tm = r['corrected_exact'] == 'True'
            h = hash_worst.get((r['image_id'], r['transform_name'], r['intensity_value']))
            hash_ok = h is not None and h < HASH_FAIL50
            if tm:
                tm_ok += 1
            if tm or hash_ok:
                ens_ok += 1
        tm_pct = tm_ok / n * 100
        ens_pct = ens_ok / n * 100
        rescue = ens_pct - tm_pct
        lines.append(f'| {config} | {n} | {tm_pct:.2f} | {ens_pct:.2f} | {rescue:+.2f} |')
        rows_out.append((config, n, tm_pct, ens_pct, rescue))

    with open(OUT, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
    print('\n'.join(lines))
    print(f'\nWrote -> {OUT}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--ablation', default=ABLATION)
    parser.add_argument('--hash', default=HASH)
    parser.add_argument('--out', default=OUT)
    parser.add_argument('--scale-label', default=SCALE_LABEL)
    args = parser.parse_args()
    ABLATION = args.ablation
    HASH = args.hash
    OUT = args.out
    SCALE_LABEL = args.scale_label
    main()