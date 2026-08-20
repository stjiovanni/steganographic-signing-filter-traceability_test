"""Generate FPR remediation assets: data-derived figures, table data JSON, and
native Excel charts. All values are computed from the validated result files;
nothing is estimated or hard-coded."""

import csv
import gzip
import json
import os
from collections import defaultdict

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from openpyxl import load_workbook
from openpyxl.chart import BarChart, Reference

ROOT = os.path.dirname(os.path.abspath(__file__))
FINAL = os.path.join(ROOT, 'output', 'results', 'final1200')
PILOT = os.path.join(ROOT, 'output', 'results')
FIGURES = os.path.join(ROOT, 'output', 'figures')
TRANSFORM_ORDER = ['brightness', 'contrast', 'saturation', 'vibrancy', 'gaussian_blur',
                   'salt_pepper_noise', 'jpeg_compression', 'rotation', 'scaling',
                   'crop_center', 'crop_random', 'letterbox']
HASH_BITS = {'pdq': 256}


def read_csv(directory, name):
    path = os.path.join(directory, name)
    if not os.path.exists(path) and os.path.exists(path + '.gz'):
        path += '.gz'
    opener = gzip.open if path.endswith('.gz') else open
    with opener(path, 'rt', newline='', encoding='utf-8') as stream:
        return list(csv.DictReader(stream))


def wm_by_transform(rows):
    grouped = defaultdict(list)
    for row in rows:
        if row['transform_name'] != 'none':
            grouped[row['transform_name']].append(float(row['bit_accuracy']))
    return {name: sum(values) / len(values) for name, values in grouped.items()}


def wm_overall(rows):
    values = [float(row['bit_accuracy']) for row in rows if row['transform_name'] != 'none']
    return sum(values) / len(values)


def hash_by_transform(rows):
    pooled = defaultdict(list)
    per_algo = defaultdict(lambda: defaultdict(list))
    for row in rows:
        bits = HASH_BITS.get(row['hash_algorithm'], 64)
        frac = int(row['hamming_distance']) / bits
        pooled[row['transform_name']].append(frac)
        per_algo[row['transform_name']][row['hash_algorithm']].append(frac)
    mean_err = {name: sum(values) / len(values) for name, values in pooled.items()}
    worst = {name: max(sum(vals) / len(vals) for vals in algos.values())
             for name, algos in per_algo.items()}
    return mean_err, worst


def main():
    os.makedirs(FIGURES, exist_ok=True)
    data = {}

    # ---- final1200 core numbers ----
    final_tm = read_csv(FINAL, 'trustmark_robustness_results.csv')
    final_lsb = read_csv(FINAL, 'lsb_robustness_results.csv')
    final_dct = read_csv(FINAL, 'dct_robustness_results.csv')
    final_hash = read_csv(FINAL, 'hash_robustness_results.csv.gz')

    tm_tf = wm_by_transform(final_tm)
    lsb_tf = wm_by_transform(final_lsb)
    dct_tf = wm_by_transform(final_dct)
    hash_mean, hash_worst = hash_by_transform(final_hash)

    data['t7_final1200'] = [
        {
            'transform': name,
            'trustmark': round(tm_tf[name], 4),
            'lsb': round(lsb_tf[name], 4),
            'dct': round(dct_tf[name], 4),
            'hash_mean_error': round(hash_mean[name], 4),
            'hash_worst_error': round(hash_worst[name], 4),
        }
        for name in TRANSFORM_ORDER
    ]
    data['final1200_overall'] = {
        'trustmark': round(wm_overall(final_tm), 4),
        'lsb': round(wm_overall(final_lsb), 4),
        'dct': round(wm_overall(final_dct), 4),
        'hash_mean_error': round(sum(hash_mean.values()) / len(hash_mean), 4),
        'hash_worst_error': round(sum(hash_worst.values()) / len(hash_worst), 4),
    }

    # ---- Figure 1: final1200 per-transform comparison ----
    fig, (ax_top, ax_bottom) = plt.subplots(2, 1, figsize=(12, 9), sharex=True)
    x = range(len(TRANSFORM_ORDER))
    width = 0.27
    for offset, (label, mapping) in zip((-width, 0.0, width),
                                        (('TrustMark', tm_tf), ('LSB', lsb_tf), ('DCT', dct_tf))):
        ax_top.bar([p + offset for p in x], [mapping[name] for name in TRANSFORM_ORDER],
                   width, label=label)
    ax_top.axhline(0.5, color='black', linestyle='--', linewidth=0.8)
    ax_top.set_ylabel('Mean raw bit accuracy')
    ax_top.set_ylim(0, 1.05)
    ax_top.legend()
    ax_top.set_title('Final1200 (1,200 images): per-transform watermark recovery and hash error')
    ax_bottom.plot(x, [hash_mean[name] for name in TRANSFORM_ORDER], marker='o',
                   label='Hash pooled mean bit-error fraction')
    ax_bottom.plot(x, [hash_worst[name] for name in TRANSFORM_ORDER], marker='s',
                   label='Hash worst-algorithm bit-error fraction')
    ax_bottom.axhline(0.5, color='black', linestyle='--', linewidth=0.8)
    ax_bottom.set_ylabel('Bit-error fraction')
    ax_bottom.set_ylim(0, 1.05)
    ax_bottom.set_xticks(list(x))
    ax_bottom.set_xticklabels(TRANSFORM_ORDER, rotation=45, ha='right')
    ax_bottom.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(FIGURES, 'fpr_final1200_method_comparison.png'), dpi=180)
    plt.close(fig)

    # ---- Figure 2: payload/ECC development sweep ----
    dev = read_csv(PILOT, 'payload_ecc_ablation_dev100.csv')
    agg = defaultdict(lambda: {'n': 0, 'exact': 0, 'present': 0, 'clean_n': 0, 'clean_exact': 0})
    for row in dev:
        entry = agg[row['config_id']]
        entry['n'] += 1
        entry['exact'] += row['corrected_exact'] == 'True'
        entry['present'] += row['corrected_decode_present'] == 'True'
        if row['transform_name'] == 'none':
            entry['clean_n'] += 1
            entry['clean_exact'] += row['corrected_exact'] == 'True'
    configs = sorted(agg, key=lambda c: agg[c]['exact'] / agg[c]['n'], reverse=True)
    data['t8_ecc'] = [
        {
            'config': cfg,
            'n': agg[cfg]['n'],
            'corrected_exact_pct': round(agg[cfg]['exact'] / agg[cfg]['n'] * 100, 2),
            'decode_present_pct': round(agg[cfg]['present'] / agg[cfg]['n'] * 100, 2),
            'clean_exact_pct': round(agg[cfg]['clean_exact'] / agg[cfg]['clean_n'] * 100, 1),
        }
        for cfg in configs
    ]
    selected = read_csv(PILOT, 'payload_ecc_ablation_selected_final1200.csv')
    sel_exact = sum(1 for r in selected if r['corrected_exact'] == 'True') / len(selected) * 100
    data['t8_final1200_selected'] = {'config': 'bch_super_4chars', 'n': len(selected),
                                     'corrected_exact_pct': round(sel_exact, 2)}

    fig, axis = plt.subplots(figsize=(11, 5.5))
    values = [row['corrected_exact_pct'] for row in data['t8_ecc']]
    bars = axis.bar(range(len(configs)), values)
    for index, cfg in enumerate(configs):
        if cfg == 'bch_super_4chars':
            bars[index].set_color('#C00000')
    axis.axhline(sel_exact, color='#C00000', linestyle=':', linewidth=1.2,
                 label=f'Selected config at 1,200 images ({sel_exact:.2f}%)')
    axis.set_xticks(list(range(len(configs))))
    axis.set_xticklabels(configs, rotation=45, ha='right', fontsize=8)
    axis.set_ylabel('Corrected-exact decode (%)')
    axis.set_title('Payload/ECC ablation: development-scale ranking (100 images x 81 variants)')
    axis.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(FIGURES, 'fpr_payload_ecc_dev_sweep.png'), dpi=180)
    plt.close(fig)

    # ---- Figure 3: pilot vs final (watermarks; pilot files verified 8,100 rows / 100 images) ----
    pilot_means, final_means = [], []
    labels = ['TrustMark', 'LSB', 'DCT']
    for label, name in zip(labels, ('trustmark', 'lsb', 'dct')):
        pilot_rows = read_csv(PILOT, f'{name}_robustness_results.csv')
        pilot_images = {row['image_id'] for row in pilot_rows}
        assert len(pilot_images) == 100 and len(pilot_rows) == 8100, \
            f'Pilot {name} file is not the clean 100-image set'
        pilot_means.append(wm_overall(pilot_rows))
        final_means.append(wm_overall(read_csv(FINAL, f'{name}_robustness_results.csv')))
    data['f3_pilot'] = [round(v, 4) for v in pilot_means]
    data['f3_final'] = [round(v, 4) for v in final_means]
    fig, axis = plt.subplots(figsize=(8, 5))
    width = 0.36
    pos = range(len(labels))
    axis.bar([p - width / 2 for p in pos], pilot_means, width, label='Pilot (100 images)')
    axis.bar([p + width / 2 for p in pos], final_means, width, label='Final (1,200 images)')
    axis.set_xticks(list(pos))
    axis.set_xticklabels(labels)
    axis.set_ylim(0, 1.05)
    axis.set_ylabel('Mean raw bit accuracy, transformed rows')
    axis.set_title('Scale comparison: pilot versus final (descriptive, not causal)')
    axis.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(FIGURES, 'fpr_pilot_final_comparison.png'), dpi=180)
    plt.close(fig)

    # ---- Figure 4: transform taxonomy and data flow ----
    import transforms as transforms_module
    fig, axis = plt.subplots(figsize=(12, 7))
    axis.axis('off')
    axis.text(0.03, 0.97, 'Shared transform module (transforms.py): 12 categories, 80 named conditions',
              fontsize=11, fontweight='bold', va='top')
    categories = [(name, len(steps)) for name, steps in transforms_module.TRANSFORM_STEPS.items()]
    for index, (name, steps) in enumerate(categories):
        row, col = divmod(index, 4)
        axis.text(0.03 + col * 0.24, 0.86 - row * 0.11,
                  f'{name}\n{steps} condition{"s" if steps != 1 else ""}',
                  fontsize=8.5, va='top',
                  bbox=dict(boxstyle='round,pad=0.35', facecolor='#DCE6F1', edgecolor='#1F4E78'))
    pipelines = ['Perceptual hashes (8 algorithms)', 'TrustMark (BCH_4, TM00001)',
                 'LSB baseline (LSB0001)', 'DCT baseline (differential)']
    for index, name in enumerate(pipelines):
        axis.text(0.03 + index * 0.24, 0.42, name, fontsize=8.5, va='top',
                  bbox=dict(boxstyle='round,pad=0.35', facecolor='#E2EFDA', edgecolor='#375623'))
    axis.annotate('', xy=(0.5, 0.46), xytext=(0.5, 0.60),
                  arrowprops=dict(arrowstyle='->', lw=1.5))
    stages = ['Result CSVs\n(row-level lineage)', 'Coverage validation\n(validate_experiment.py)',
              'Analysis\n(thresholds, ensemble, uncertainty)', 'Report artefacts\n(tables, figures, workbook)']
    for index, name in enumerate(stages):
        axis.text(0.03 + index * 0.24, 0.22, name, fontsize=8.5, va='top',
                  bbox=dict(boxstyle='round,pad=0.35', facecolor='#FFF2CC', edgecolor='#7F6000'))
    for index in range(3):
        axis.annotate('', xy=(0.27 + index * 0.24, 0.16), xytext=(0.21 + index * 0.24, 0.16),
                      arrowprops=dict(arrowstyle='->', lw=1.2))
    axis.annotate('', xy=(0.5, 0.26), xytext=(0.5, 0.40),
                  arrowprops=dict(arrowstyle='->', lw=1.5))
    axis.set_xlim(0, 1)
    axis.set_ylim(0, 1)
    fig.tight_layout()
    fig.savefig(os.path.join(FIGURES, 'fpr_transform_taxonomy.png'), dpi=180)
    plt.close(fig)

    # ---- Table 9 data: uncertainty summary (transformed conditions only) ----
    uncertainty = read_csv(FINAL, 'uncertainty_summary.csv')
    grouped_u = defaultdict(list)
    for row in uncertainty:
        if row['transform_name'] == 'none':
            continue
        grouped_u[(row['method'], row['metric'])].append(row)
    t9 = []
    for (method, metric), rows in sorted(grouped_u.items()):
        means = [float(r['mean']) for r in rows]
        ci_lows = [float(r['ci_low']) for r in rows]
        ci_highs = [float(r['ci_high']) for r in rows]
        sds = [float(r['sd']) for r in rows]
        t9.append({
            'method': method,
            'metric': metric,
            'conditions': len(rows),
            'n_images': rows[0]['n_images'],
            'mean_of_condition_means': round(sum(means) / len(means), 4),
            'max_condition_sd': round(max(sds), 4),
            'ci_envelope': f"[{round(min(ci_lows), 4)}, {round(max(ci_highs), 4)}]",
            'ci_method': rows[0]['ci_method'],
        })
    data['t9_uncertainty'] = t9

    with open(os.path.join(ROOT, 'output', 'remediation_data.json'), 'w', encoding='utf-8') as stream:
        json.dump(data, stream, indent=2)

    # ---- Native Excel charts ----
    wb = load_workbook(os.path.join(ROOT, 'FPR_Evidence.xlsx'))
    ws = wb['PayloadECC']
    if not ws._charts:
        chart = BarChart()
        chart.title = 'Dev-scale corrected-exact % by configuration (100 images x 81 variants)'
        chart.y_axis.title = 'Corrected-exact %'
        chart.add_data(Reference(ws, min_col=4, min_row=1, max_row=13), titles_from_data=True)
        chart.set_categories(Reference(ws, min_col=2, min_row=2, max_row=13))
        ws.add_chart(chart, 'I2')
    wb.save(os.path.join(ROOT, 'FPR_Evidence.xlsx'))

    wb = load_workbook(os.path.join(ROOT, 'FPR_Improvement_Comparison.xlsx'))
    ws = wb['MethodComparison']
    # Repair the pilot hash cell: the default pilot hash CSV contains 263 images
    # (superseded extra rows); recompute over the clean pilot image set.
    clean_ids = None
    with open(os.path.join(PILOT, 'trustmark_robustness_results.csv'), newline='', encoding='utf-8') as f:
        clean_ids = {row['image_id'] for row in csv.DictReader(f)}
    pilot_hash = read_csv(PILOT, 'hash_robustness_results.csv')
    pilot_hash = [row for row in pilot_hash if row['image_id'] in clean_ids]
    pilot_hash_mean = sum(int(r['hamming_distance']) / HASH_BITS.get(r['hash_algorithm'], 64)
                          for r in pilot_hash) / len(pilot_hash)
    for row in ws.iter_rows(min_row=2, max_row=ws.max_row):
        if row[0].value == 'Hash':
            row[1].value = pilot_hash_mean
            row[3].value = row[2].value - pilot_hash_mean
            row[4].value = ('Mean normalised Hamming error, clean 100-image pilot subset '
                            '(image IDs shared with the validated pilot watermark files)')
    if not ws._charts:
        chart = BarChart()
        chart.title = 'Pilot (100) versus final (1,200) transformed-row means'
        chart.add_data(Reference(ws, min_col=2, max_col=3, min_row=1, max_row=4), titles_from_data=True)
        chart.set_categories(Reference(ws, min_col=1, min_row=2, max_row=4))
        ws.add_chart(chart, 'G2')
    ws = wb['PayloadECCAblation']
    if not ws._charts:
        chart = BarChart()
        chart.title = 'Dev-scale corrected-exact % by configuration'
        chart.add_data(Reference(ws, min_col=4, min_row=1, max_row=13), titles_from_data=True)
        chart.set_categories(Reference(ws, min_col=2, min_row=2, max_row=13))
        ws.add_chart(chart, 'H2')
    wb.save(os.path.join(ROOT, 'FPR_Improvement_Comparison.xlsx'))

    print('Figures written:', sorted(f for f in os.listdir(FIGURES) if f.startswith('fpr_')))
    print('JSON keys:', sorted(data))
    print('Final1200 overall:', data['final1200_overall'])
    print('ECC selected final1200:', data['t8_final1200_selected'])
    print('Pilot hash clean mean error:', round(pilot_hash_mean, 6), 'rows used:', len(pilot_hash))


if __name__ == '__main__':
    main()
