"""Threshold analysis (Task 7) and ensemble overlap analysis (Task 8)."""

import csv, os
from collections import defaultdict
import numpy as np

RESULTS_DIR = 'output/results'
OUTPUT_DIR = 'output'

HASH_NAMES = ['phash', 'dhash', 'ahash', 'whash', 'colorhash', 'dhash_vertical', 'phash_simple', 'pdq']


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


def run_analysis():
    hash_rows, tm_idx, lsb_idx, dct_idx = load_all()

    # Index hash rows by (transform, intensity) → list of (image_id, algo, dist)
    hash_by_tf = defaultdict(list)
    for r in hash_rows:
        key = (r['transform_name'], r['intensity_value'])
        d = parse_float(r['hamming_distance'])
        if d is not None:
            hash_by_tf[key].append(d)

    # Index watermark rows by (transform, intensity) → list of bit_accuracy
    wm_by_tf = {}
    for name, idx in [('trustmark', tm_idx), ('lsb', lsb_idx), ('dct', dct_idx)]:
        by_tf = defaultdict(list)
        for key, row in idx.items():
            tf_key = (row['transform_name'], row['intensity_value'])
            ba = parse_float(row['bit_accuracy'])
            if ba is not None:
                by_tf[tf_key].append(ba)
        wm_by_tf[name] = by_tf

    all_tf_intensities = sorted(hash_by_tf.keys())

    # ── Task 7: Threshold summary ──
    lines = []
    lines.append('# Per-Transform Threshold Analysis')
    lines.append('')
    lines.append('Thresholds for each method across all 100 images.')
    lines.append('Hash threshold: mean Hamming distance > 128 (50% bit error) / > 230 (90% bit error).')
    lines.append('Watermark threshold: mean bit_accuracy < 0.5 (< 50%) / < 0.1 (< 10%).')
    lines.append('')
    lines.append('| Transform | Metric | <50% threshold | <10% threshold |')
    lines.append('|---|---|---|---|')

    for tf_name in ['brightness', 'contrast', 'saturation', 'vibrancy', 'gaussian_blur',
                    'salt_pepper_noise', 'jpeg_compression', 'rotation', 'scaling',
                    'crop_center', 'crop_random', 'letterbox']:
        tf_intensities = sorted([iv for (tf, iv) in all_tf_intensities if tf == tf_name],
                                key=lambda x: (parse_float(x) is not None, parse_float(x) or x))

        for method_label, data_source in [
            ('Hash (mean)', hash_by_tf),
            ('TrustMark', wm_by_tf['trustmark']),
            ('LSB', wm_by_tf['lsb']),
            ('DCT', wm_by_tf['dct']),
        ]:
            below50 = None
            below10 = None
            is_hash = method_label.startswith('Hash')

            for iv in tf_intensities:
                key = (tf_name, iv)
                vals = data_source.get(key, [])
                if not vals:
                    continue
                mean_val = np.mean(vals)
                if is_hash:
                    # Hamming distance: higher = worse
                    if mean_val > 128 and below50 is None:
                        below50 = iv
                    if mean_val > 230 and below10 is None:
                        below10 = iv
                else:
                    # Bit accuracy: lower = worse
                    if mean_val < 0.5 and below50 is None:
                        below50 = iv
                    if mean_val < 0.1 and below10 is None:
                        below10 = iv

            lines.append(
                f'| {tf_name} | {method_label} | {below50 or "—"} | {below10 or "—"} |')

    # ── Task 8: Ensemble overlap ──
    lines.append('')
    lines.append('# Ensemble Overlap Analysis')
    lines.append('')
    lines.append('For each (transform, intensity) pair across all 100 images:')
    lines.append('- Hash success: mean Hamming < 128 across all 8 algorithms')
    lines.append('- Watermark success: mean bit_accuracy > 0.5')
    lines.append('')

    decision_rows = []
    for tf_name in ['brightness', 'contrast', 'saturation', 'vibrancy', 'gaussian_blur',
                    'salt_pepper_noise', 'jpeg_compression', 'rotation', 'scaling',
                    'crop_center', 'crop_random', 'letterbox']:
        tf_intensities = sorted([iv for (tf, iv) in all_tf_intensities if tf == tf_name],
                                key=lambda x: (parse_float(x) is not None, parse_float(x) or x))

        for iv in tf_intensities:
            key = (tf_name, iv)

            # Hash success
            hash_vals = hash_by_tf.get(key, [])
            hash_ok = np.mean(hash_vals) < 128 if hash_vals else False

            # Watermark success
            tm_vals = wm_by_tf['trustmark'].get(key, [])
            lsb_vals = wm_by_tf['lsb'].get(key, [])
            dct_vals = wm_by_tf['dct'].get(key, [])
            tm_ok = np.mean(tm_vals) > 0.5 if tm_vals else False
            lsb_ok = np.mean(lsb_vals) > 0.5 if lsb_vals else False
            dct_ok = np.mean(dct_vals) > 0.5 if dct_vals else False

            # Best method
            scores = {}
            if hash_ok: scores['hash'] = 0.8
            if tm_ok: scores['trustmark'] = 1.0
            if lsb_ok: scores['lsb'] = 0.5
            if dct_ok: scores['dct'] = 0.7
            best = max(scores, key=scores.get) if scores else 'none'

            # Fallback (second best)
            sorted_methods = sorted(scores, key=scores.get, reverse=True)
            fallback = sorted_methods[1] if len(sorted_methods) > 1 else best

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

            decision_rows.append({
                'transform_name': tf_name,
                'intensity_value': str(iv),
                'best_method': best,
                'fallback_method': fallback,
                'hash_ok': str(hash_ok),
                'trustmark_ok': str(tm_ok),
                'lsb_ok': str(lsb_ok),
                'dct_ok': str(dct_ok),
                'notes': '; '.join(notes),
            })

    # Write ensemble decision matrix CSV
    csv_path = os.path.join(OUTPUT_DIR, 'results', 'ensemble_decision_matrix.csv')
    with open(csv_path, 'w', newline='') as f:
        fieldnames = ['transform_name', 'intensity_value', 'best_method', 'fallback_method',
                      'hash_ok', 'trustmark_ok', 'lsb_ok', 'dct_ok', 'notes']
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(decision_rows)

    # Write summary markdown
    md_path = os.path.join(OUTPUT_DIR, 'threshold_analysis.md')
    with open(md_path, 'w') as f:
        f.write('\n'.join(lines))

    print(f'Threshold analysis → {md_path} ({len(lines)} lines)')
    print(f'Decision matrix    → {csv_path} ({len(decision_rows)} rows)')


if __name__ == '__main__':
    run_analysis()
