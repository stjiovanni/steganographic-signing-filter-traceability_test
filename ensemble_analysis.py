"""Threshold analysis (Task 7) and ensemble overlap analysis (Task 8)."""

import csv, os
from collections import defaultdict
import numpy as np

RESULTS_DIR = 'output/results'
OUTPUT_DIR = 'output'

HASH_NAMES = ['phash', 'dhash', 'ahash', 'whash', 'colorhash', 'dhash_vertical', 'phash_simple', 'pdq']
# PDQ is a 256-bit hash; all other perceptual hashes in this project are 64-bit.
HASH_BITS = {name: (256 if name == 'pdq' else 64) for name in HASH_NAMES}

TRANSFORMS = ['brightness', 'contrast', 'saturation', 'vibrancy', 'gaussian_blur',
              'salt_pepper_noise', 'jpeg_compression', 'rotation', 'scaling',
              'crop_center', 'crop_random', 'letterbox']

# Failure thresholds. Hashes are scored on mean bit-error FRACTION (0 = perfect,
# 1 = every bit flipped); watermarks on mean bit_accuracy (1 = perfect).
HASH_FAIL50 = 0.5   # 50% of bits in error
HASH_FAIL90 = 0.9   # 90% of bits in error
WM_FAIL50 = 0.5     # bit_accuracy below 50%
WM_FAIL10 = 0.1     # bit_accuracy below 10%


def load_csv(fn):
    with open(os.path.join(RESULTS_DIR, fn)) as f:
        return list(csv.DictReader(f))


def load_all():
    hash_rows = load_csv('hash_robustness_results.csv')
    tm_rows = load_csv('trustmark_robustness_results.csv')
    lsb_rows = load_csv('lsb_robustness_results.csv')
    dct_rows = load_csv('dct_robustness_results.csv')

    def index_wm(rows):
        idx = {}
        for r in rows:
            key = (r['image_id'], r['transform_name'], r['intensity_value'])
            idx[key] = r
        return idx

    return hash_rows, index_wm(tm_rows), index_wm(lsb_rows), index_wm(dct_rows)


def parse_float(s):
    try:
        return float(s)
    except (ValueError, TypeError):
        return None


def hash_bit_error_fraction(row):
    """Normalize a Hamming distance to a bit-error fraction in [0, 1] by the
    hash's bit length (256 for PDQ, 64 for all others). This makes distances
    across different-sized hashes directly comparable before pooling."""
    algo = row.get('hash_algorithm')
    if algo not in HASH_BITS:
        return None
    d = parse_float(row.get('hamming_distance'))
    if d is None:
        return None
    return d / HASH_BITS[algo]


def summarize_crossings(pairs, lower_is_worse, fail50, fail90):
    """Given ordered (intensity, mean_metric) pairs, return the first intensity
    where each threshold is crossed AND the intensity with the most degraded
    mean metric among those that crossed. Non-monotonic degradation means the
    first crossing can understate the worst case, so both are reported.
    lower_is_worse=True → watermark bit_accuracy (crossed = below threshold);
    otherwise hash bit-error fraction (crossed = above threshold)."""
    first50 = first90 = None
    worst50 = worst90 = None
    worst50_val = worst90_val = None
    for iv, val in pairs:
        if val is None:
            continue
        crossed50 = val < fail50 if lower_is_worse else val > fail50
        crossed90 = val < fail90 if lower_is_worse else val > fail90
        if crossed50:
            if first50 is None:
                first50 = iv
            if worst50_val is None or (val < worst50_val if lower_is_worse else val > worst50_val):
                worst50_val = val
                worst50 = iv
        if crossed90:
            if first90 is None:
                first90 = iv
            if worst90_val is None or (val < worst90_val if lower_is_worse else val > worst90_val):
                worst90_val = val
                worst90 = iv
    return first50, worst50, first90, worst90


def run_analysis():
    hash_rows, tm_idx, lsb_idx, dct_idx = load_all()

    # Index hash bit-error fractions by (transform, intensity).
    #   hash_by_tf: pooled fractions across all (image, algorithm) rows.
    #   hash_worst_by_tf: worst-algorithm mean fraction per (tf, iv), i.e. the
    #     weakest link. The pooled mean stays near 0 because 7 of 8 hashes are
    #     64-bit and robust, masking PDQ's failures, so the weakest link is the
    #     correct metric for pass/fail and ranking.
    hash_by_tf = defaultdict(list)
    hash_algo_by_tf = defaultdict(lambda: defaultdict(list))
    for r in hash_rows:
        frac = hash_bit_error_fraction(r)
        if frac is not None:
            key = (r['transform_name'], r['intensity_value'])
            hash_by_tf[key].append(frac)
            hash_algo_by_tf[key][r['hash_algorithm']].append(frac)
    hash_worst_by_tf = defaultdict(list)
    for key, algos in hash_algo_by_tf.items():
        hash_worst_by_tf[key].append(max(np.mean(v) for v in algos.values()))

    # Index watermark rows by (transform, intensity) → list of bit_accuracy
    wm_by_tf = {}
    for name, idx in [('trustmark', tm_idx), ('lsb', lsb_idx), ('dct', dct_idx)]:
        by_tf = defaultdict(list)
        for row in idx.values():
            tf_key = (row['transform_name'], row['intensity_value'])
            ba = parse_float(row['bit_accuracy'])
            if ba is not None:
                by_tf[tf_key].append(ba)
        wm_by_tf[name] = by_tf

    # Union of all (transform, intensity) pairs seen by any method
    tf_intensity_keys = set(hash_by_tf.keys())
    for by_tf in wm_by_tf.values():
        tf_intensity_keys |= set(by_tf.keys())

    # ── Task 7: Threshold summary ──
    lines = []
    lines.append('# Per-Transform Threshold Analysis')
    lines.append('')
    lines.append('Thresholds for each method across all 100 images.')
    lines.append('Hash threshold: mean bit-error fraction > 0.5 (50% bit error) / > 0.9 (90% bit error).')
    lines.append('  Bit-error fraction = Hamming distance / hash bit length (64 bits for all algorithms except PDQ = 256).')
    lines.append('  "Hash (mean)" = pooled mean over all 8 hash algorithms and all images (ensemble average).')
    lines.append('  "Hash (worst)" = worst-algorithm mean over images (weakest link). The pooled mean is dominated')
    lines.append('  by the 7 robust 64-bit hashes and can mask PDQ failures, so the worst algorithm is what drives')
    lines.append('  ensemble failure and is used for pass/fail decisions below.')
    lines.append('Watermark threshold: mean bit_accuracy < 0.5 (< 50%) / < 0.1 (< 10%).')
    lines.append('')
    lines.append('Degradation is not always monotonic, so each threshold reports BOTH the first intensity where it')
    lines.append('is crossed and the worst-case intensity (most degraded mean metric: max bit-error fraction for')
    lines.append('hashes, min bit_accuracy for watermarks) among the intensities that crossed.')
    lines.append('')
    lines.append('| Transform | Metric | <50% first | <50% worst | <10% first | <10% worst |')
    lines.append('|---|---|---|---|---|---|')

    for tf_name in TRANSFORMS:
        tf_intensities = sorted([iv for (tf, iv) in tf_intensity_keys if tf == tf_name],
                                key=lambda x: (parse_float(x) is not None, parse_float(x) or x))

        for method_label, data_source, lower_is_worse in [
            ('Hash (mean)', hash_by_tf, False),
            ('Hash (worst)', hash_worst_by_tf, False),
            ('TrustMark', wm_by_tf['trustmark'], True),
            ('LSB', wm_by_tf['lsb'], True),
            ('DCT', wm_by_tf['dct'], True),
        ]:
            pairs = []
            for iv in tf_intensities:
                vals = data_source.get((tf_name, iv), [])
                pairs.append((iv, np.mean(vals) if vals else None))
            fail50 = WM_FAIL50 if lower_is_worse else HASH_FAIL50
            fail90 = WM_FAIL10 if lower_is_worse else HASH_FAIL90
            first50, worst50, first90, worst90 = summarize_crossings(
                pairs, lower_is_worse, fail50, fail90)
            lines.append(
                f'| {tf_name} | {method_label} | {first50 or "—"} | {worst50 or "—"} | '
                f'{first90 or "—"} | {worst90 or "—"} |')

    # ── Task 8: Ensemble overlap ──
    lines.append('')
    lines.append('# Ensemble Overlap Analysis')
    lines.append('')
    lines.append('For each (transform, intensity) pair across all 100 images:')
    lines.append('- Hash success: worst-algorithm mean bit-error fraction < 0.5 (weakest link; Hamming')
    lines.append('  normalized by hash bit length). The pooled mean stays low because 7 of 8 hashes are')
    lines.append('  64-bit and robust, masking PDQ failures.')
    lines.append('- Watermark success: mean bit_accuracy > 0.5')
    lines.append('- best_method: largest robustness margin = distance from the failure line')
    lines.append('  (hash: 0.5 - worst-algorithm bit-error fraction; watermark: bit_accuracy - 0.5)')
    lines.append('')

    decision_rows = []
    for tf_name in TRANSFORMS:
        tf_intensities = sorted([iv for (tf, iv) in tf_intensity_keys if tf == tf_name],
                                key=lambda x: (parse_float(x) is not None, parse_float(x) or x))

        for iv in tf_intensities:
            key = (tf_name, iv)

            def mean_of(by_tf):
                vals = by_tf.get(key, [])
                return np.mean(vals) if vals else None

            hash_frac = mean_of(hash_by_tf)
            hash_worst = mean_of(hash_worst_by_tf)
            tm_ba = mean_of(wm_by_tf['trustmark'])
            lsb_ba = mean_of(wm_by_tf['lsb'])
            dct_ba = mean_of(wm_by_tf['dct'])

            hash_ok = hash_worst is not None and hash_worst < HASH_FAIL50
            tm_ok = tm_ba is not None and tm_ba > WM_FAIL50
            lsb_ok = lsb_ba is not None and lsb_ba > WM_FAIL50
            dct_ok = dct_ba is not None and dct_ba > WM_FAIL50

            # Robustness margin = distance from the failure line. Larger = better.
            # This is derived from measured data, not hardcoded method weights.
            # The hash ensemble is scored on its weakest link (worst algorithm).
            margins = {
                'hash': (HASH_FAIL50 - hash_worst) if hash_worst is not None else None,
                'trustmark': (tm_ba - WM_FAIL50) if tm_ba is not None else None,
                'lsb': (lsb_ba - WM_FAIL50) if lsb_ba is not None else None,
                'dct': (dct_ba - WM_FAIL50) if dct_ba is not None else None,
            }
            present = {m: v for m, v in margins.items() if v is not None}
            ranked = sorted(present, key=present.get, reverse=True)
            best = ranked[0] if ranked else 'none'
            fallback = ranked[1] if len(ranked) > 1 else ('none' if not ranked else best)

            # Notes
            notes = []
            if tm_ok and not hash_ok:
                notes.append('TrustMark exceeds hash tolerance')
            if not tm_ok and hash_ok:
                notes.append('Hashes exceed TrustMark tolerance')
            if lsb_ok and not tm_ok:
                notes.append('LSB outperforms TrustMark (*)')
            if dct_ok and not tm_ok:
                notes.append('DCT outperforms TrustMark (*)')

            def fmt(v):
                return f'{v:.4f}' if v is not None else ''

            decision_rows.append({
                'transform_name': tf_name,
                'intensity_value': str(iv),
                'best_method': best,
                'fallback_method': fallback,
                'hash_bit_error': fmt(hash_frac),
                'hash_worst_bit_error': fmt(hash_worst),
                'hash_ok': str(hash_ok),
                'trustmark_bit_accuracy': fmt(tm_ba),
                'trustmark_ok': str(tm_ok),
                'lsb_bit_accuracy': fmt(lsb_ba),
                'lsb_ok': str(lsb_ok),
                'dct_bit_accuracy': fmt(dct_ba),
                'dct_ok': str(dct_ok),
                'notes': '; '.join(notes),
            })

    # Write ensemble decision matrix CSV
    csv_path = os.path.join(OUTPUT_DIR, 'results', 'ensemble_decision_matrix.csv')
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['transform_name', 'intensity_value', 'best_method', 'fallback_method',
                      'hash_bit_error', 'hash_worst_bit_error', 'hash_ok',
                      'trustmark_bit_accuracy', 'trustmark_ok',
                      'lsb_bit_accuracy', 'lsb_ok', 'dct_bit_accuracy', 'dct_ok', 'notes']
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(decision_rows)

    # Write summary markdown
    md_path = os.path.join(OUTPUT_DIR, 'threshold_analysis.md')
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print(f'Threshold analysis -> {md_path} ({len(lines)} lines)')
    print(f'Decision matrix    -> {csv_path} ({len(decision_rows)} rows)')


if __name__ == '__main__':
    run_analysis()
