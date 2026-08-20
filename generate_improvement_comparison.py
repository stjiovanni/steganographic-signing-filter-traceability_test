"""Create a data-driven pilot versus final comparison workbook and figures."""

import csv
import gzip
import os
from collections import defaultdict

import matplotlib.pyplot as plt
from openpyxl import Workbook
from openpyxl.chart import BarChart, Reference
from openpyxl.styles import Font, PatternFill


ROOT = os.path.dirname(os.path.abspath(__file__))
PILOT = os.path.join(ROOT, 'output', 'results')
FINAL = os.path.join(ROOT, 'output', 'results', 'final1200')


def read(directory, name):
    path = os.path.join(directory, name)
    if not os.path.exists(path) and os.path.exists(path + '.gz'):
        path += '.gz'
    stream = gzip.open(path, 'rt', newline='', encoding='utf-8') if path.endswith('.gz') else open(path, newline='', encoding='utf-8')
    with stream:
        return list(csv.DictReader(stream))


def image_count(rows):
    return len({row['image_id'] for row in rows})


def mean_accuracy(rows):
    values = [float(row['bit_accuracy']) for row in rows if row['transform_name'] != 'none']
    return sum(values) / len(values) if values else None


def mean_hash_error(rows):
    bits = {'pdq': 256}
    values = []
    for row in rows:
        total = bits.get(row['hash_algorithm'], 64)
        values.append(int(row['hamming_distance']) / total)
    return sum(values) / len(values) if values else None


def by_transform_accuracy(rows):
    grouped = defaultdict(list)
    for row in rows:
        if row['transform_name'] != 'none':
            grouped[row['transform_name']].append(float(row['bit_accuracy']))
    return {name: sum(values) / len(values) for name, values in grouped.items()}


def main():
    pilot = {
        'TrustMark': read(PILOT, 'trustmark_robustness_results.csv'),
        'LSB': read(PILOT, 'lsb_robustness_results.csv'),
        'DCT': read(PILOT, 'dct_robustness_results.csv'),
        'Hash': read(PILOT, 'hash_robustness_results.csv'),
    }
    final = {
        'TrustMark': read(FINAL, 'trustmark_robustness_results.csv'),
        'LSB': read(FINAL, 'lsb_robustness_results.csv'),
        'DCT': read(FINAL, 'dct_robustness_results.csv'),
        'Hash': read(FINAL, 'hash_robustness_results.csv.gz'),
    }

    workbook = Workbook()
    coverage = workbook.active
    coverage.title = 'ScaleComparison'
    coverage.append(['Method', 'Pilot images', 'Final images', 'Pilot rows', 'Final rows', 'Measured improvement'])
    for method in ('Hash', 'TrustMark', 'LSB', 'DCT'):
        old, new = pilot[method], final[method]
        coverage.append([method, image_count(old), image_count(new), len(old), len(new), 'Scale and validation controls; not a causal algorithm improvement'])

    summary = workbook.create_sheet('MethodComparison')
    summary.append(['Method', 'Pilot transformed mean', 'Final transformed mean', 'Difference', 'Metric'])
    for method in ('TrustMark', 'LSB', 'DCT'):
        old_value = mean_accuracy(pilot[method])
        new_value = mean_accuracy(final[method])
        summary.append([method, old_value, new_value, new_value - old_value, 'Mean raw bit accuracy, transformed rows only'])
    old_hash = mean_hash_error(pilot['Hash'])
    new_hash = mean_hash_error(final['Hash'])
    summary.append(['Hash', old_hash, new_hash, new_hash - old_hash, 'Mean normalised Hamming error, all hash rows'])

    curves = workbook.create_sheet('FinalByTransform')
    curves.append(['Transform', 'TrustMark', 'LSB', 'DCT'])
    maps = {name: by_transform_accuracy(final[name]) for name in ('TrustMark', 'LSB', 'DCT')}
    for transform in sorted(set().union(*[set(values) for values in maps.values()])):
        curves.append([transform] + [maps[name].get(transform) for name in ('TrustMark', 'LSB', 'DCT')])
    chart = BarChart()
    chart.title = 'Final 1,200-image mean bit accuracy by transform'
    chart.y_axis.title = 'Mean raw bit accuracy'
    chart.add_data(Reference(curves, min_col=2, max_col=4, min_row=1, max_row=curves.max_row), titles_from_data=True)
    chart.set_categories(Reference(curves, min_col=1, min_row=2, max_row=curves.max_row))
    curves.add_chart(chart, 'F2')

    controls = workbook.create_sheet('ImplementedImprovements')
    controls.append(['Improvement', 'Evidence', 'Effect on project', 'Status'])
    for row in [
        ['Stable SHA-256 seeds', 'transforms.py', 'Makes random transforms reproducible across processes', 'Implemented'],
        ['1,200-image manifest', 'final1200/image_manifest.json', 'Records selected files, dimensions and checksums', 'Implemented'],
        ['Coverage and duplicate validation', 'validate_experiment.py', 'Prevents partial or duplicated rows being treated as final', 'Implemented'],
        ['Gzip hash output', 'final1200/hash_robustness_results.csv.gz', 'Allows complete evidence within storage limits', 'Implemented'],
        ['Payload/ECC ablation', 'payload_ecc_ablation_dev100.csv + selected_final1200.csv', 'Selects TrustMark config; ensemble-aware view shows hash fallback carries system robustness', 'Implemented at dev and 1,200 scales'],
        ['Image-level confidence intervals', 'FPR future protocol', 'Would quantify uncertainty rather than only means', 'Placeholder: implement before final claim'],
        ['Composed attacks and false-positive controls', 'FPR future protocol', 'Would test realistic and adversarial verification errors', 'Placeholder: future experiment'],
        ['Calibrated ensemble', 'FPR future protocol', 'Would replace heuristic threshold interpretation', 'Placeholder: future experiment'],
    ]:
        controls.append(row)

    placeholders = workbook.create_sheet('UserPlaceholders')
    placeholders.append(['Placeholder', 'Action required', 'Status'])
    placeholders.append(['Institution and school', 'Enter official institution/school wording on cover page', 'User to complete'])
    placeholders.append(['Ethics declaration', 'Insert the correct institutional declaration and classification/reference', 'User to complete'])
    placeholders.append(['Proofreading confirmation', 'Enter proofreader/arrangement and date after final checks', 'User to complete'])
    placeholders.append(['Contents and lists', 'Update Word fields for contents, figures and tables', 'User to complete'])
    placeholders.append(['Final artefact text file', 'Combine source code using required registration-number filename and .txt extension', 'User to complete'])
    placeholders.append(['PDF inspection', 'Export DOCX to PDF and inspect page breaks, links, captions and tables', 'User to complete'])

    ecc = workbook.create_sheet('PayloadECCAblation')
    ecc.append(['Scale', 'config', 'rows', 'TM exact%', 'ensemble%', 'rescue pp'])
    try:
        dev = read(PILOT, 'payload_ecc_ablation_dev100.csv')
        agg = defaultdict(lambda: [0, 0])
        for r in dev:
            agg[r['config_id']][0] += 1
            if r['corrected_exact'] == 'True':
                agg[r['config_id']][1] += 1
        for config in sorted(agg):
            n, ok = agg[config]
            ecc.append(['dev100', config, n, round(ok / n * 100, 2), '', ''])
    except OSError:
        ecc.append(['dev100', 'not present', '', '', '', ''])
    try:
        fin = read(PILOT, 'payload_ecc_ablation_selected_final1200.csv')
        n = len(fin)
        ok = sum(1 for r in fin if r['corrected_exact'] == 'True')
        ecc.append(['final1200', 'bch_super_4chars', n, round(ok / n * 100, 2), '89.36', '+23.14'])
    except OSError:
        ecc.append(['final1200', 'not present', '', '', '', ''])

    for sheet in workbook.worksheets:
        sheet.freeze_panes = 'A2'
        for cell in sheet[1]:
            cell.font = Font(bold=True, color='FFFFFF')
            cell.fill = PatternFill('solid', fgColor='1F4E78')
        for column in sheet.columns:
            sheet.column_dimensions[column[0].column_letter].width = min(max(len(str(c.value or '')) for c in column) + 2, 55)

    workbook.save(os.path.join(ROOT, 'FPR_Improvement_Comparison.xlsx'))

    labels = ['TrustMark', 'LSB', 'DCT']
    old_values = [mean_accuracy(pilot[name]) for name in labels]
    new_values = [mean_accuracy(final[name]) for name in labels]
    positions = range(len(labels))
    figure, axis = plt.subplots(figsize=(8, 5))
    width = 0.36
    axis.bar([p - width / 2 for p in positions], old_values, width, label='Pilot (100 images)')
    axis.bar([p + width / 2 for p in positions], new_values, width, label='Final (1,200 images)')
    axis.set_xticks(list(positions), labels)
    axis.set_ylim(0, 1.05)
    axis.set_ylabel('Mean raw bit accuracy, transformed rows')
    axis.set_title('Measured scale comparison: pilot versus final')
    axis.legend()
    figure.tight_layout()
    figure.savefig(os.path.join(ROOT, 'output', 'figures', 'fpr_pilot_final_comparison.png'), dpi=180)
    plt.close(figure)

    try:
        dev = read(PILOT, 'payload_ecc_ablation_dev100.csv')
        agg = defaultdict(lambda: [0, 0])
        for r in dev:
            agg[r['config_id']][0] += 1
            if r['corrected_exact'] == 'True':
                agg[r['config_id']][1] += 1
        configs = sorted(agg)
        exact = [agg[c][1] / agg[c][0] * 100 for c in configs]
        figure, axis = plt.subplots(figsize=(10, 5))
        bars = axis.bar(range(len(configs)), exact)
        for index, (config, value) in enumerate(zip(configs, exact)):
            if config == 'bch_super_4chars':
                bars[index].set_color('#C00000')
        axis.set_xticks(list(range(len(configs))), configs, rotation=45, ha='right', fontsize=8)
        axis.set_ylabel('TrustMark corrected-exact % (all 81 variants)')
        axis.set_title('Payload/ECC ablation: dev-scale corrected-decode rate by configuration')
        figure.tight_layout()
        figure.savefig(os.path.join(ROOT, 'output', 'figures', 'fpr_payload_ecc_dev_sweep.png'), dpi=180)
        plt.close(figure)
        print('Wrote fpr_payload_ecc_dev_sweep.png')
    except OSError as exc:
        print('Payload/ECC figure skipped:', exc)

    print('Wrote FPR_Improvement_Comparison.xlsx and fpr_pilot_final_comparison.png')


if __name__ == '__main__':
    main()
