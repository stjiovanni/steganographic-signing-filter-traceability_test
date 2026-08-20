"""Generate reproducible workbook evidence for the final project report."""

import csv
import os
import gzip
from collections import defaultdict
from datetime import date

from openpyxl import Workbook
from openpyxl.chart import BarChart, LineChart, Reference
from openpyxl.styles import Font, PatternFill


ROOT = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.environ.get('FPR_RESULTS_DIR', os.path.join(ROOT, 'output', 'results'))


def rows(name):
    path = os.path.join(RESULTS, name)
    if not os.path.exists(path) and os.path.exists(path + '.gz'):
        path += '.gz'
    stream = gzip.open(path, 'rt', newline='', encoding='utf-8') if path.endswith('.gz') else open(path, newline='', encoding='utf-8')
    with stream:
        return list(csv.DictReader(stream))


def main():
    hash_rows = rows('hash_robustness_results.csv')
    tm_rows = rows('trustmark_robustness_results.csv')
    lsb_rows = rows('lsb_robustness_results.csv')
    dct_rows = rows('dct_robustness_results.csv')
    images = len({r['image_id'] for r in hash_rows})

    workbook = Workbook()
    overview = workbook.active
    overview.title = 'RunSummary'
    overview.append(['Evidence item', 'Value', 'Source'])
    overview.append(['Generated UTC date', date.today().isoformat(), 'generate_fpr_evidence.py'])
    overview.append(['Images covered', images, 'result CSV image_id values'])
    overview.append(['Transform categories', len({r['transform_name'] for r in hash_rows}), 'transforms.py'])
    overview.append(['Hash rows', len(hash_rows), 'hash_robustness_results.csv'])
    overview.append(['TrustMark rows', len(tm_rows), 'trustmark_robustness_results.csv'])
    overview.append(['LSB rows', len(lsb_rows), 'lsb_robustness_results.csv'])
    overview.append(['DCT rows', len(dct_rows), 'dct_robustness_results.csv'])
    overview.append(['Interpretation', 'Descriptive benchmark; image is the experimental unit', 'methodology'])

    summary = workbook.create_sheet('MethodSummary')
    summary.append(['Transform', 'TrustMark mean bit accuracy', 'LSB mean bit accuracy', 'DCT mean bit accuracy'])
    grouped = defaultdict(lambda: [[], [], []])
    for index, data in enumerate((tm_rows, lsb_rows, dct_rows)):
        for row in data:
            if row['transform_name'] != 'none':
                grouped[row['transform_name']][index].append(float(row['bit_accuracy']))
    for transform, values in sorted(grouped.items()):
        summary.append([transform] + [sum(v) / len(v) if v else None for v in values])
    chart = BarChart()
    chart.title = 'Mean raw bit accuracy by transform'
    chart.y_axis.title = 'Mean bit accuracy'
    chart.x_axis.title = 'Transform'
    chart.add_data(Reference(summary, min_col=2, max_col=4, min_row=1, max_row=summary.max_row), titles_from_data=True)
    chart.set_categories(Reference(summary, min_col=1, min_row=2, max_row=summary.max_row))
    summary.add_chart(chart, 'F2')

    timeline = workbook.create_sheet('Gantt')
    timeline.append(['Work package', 'Start', 'Finish', 'Status', 'Evidence'])
    timeline_rows = [
        ['Requirements and literature review', '2026-02-01', '2026-03-15', 'Complete', 'Report literature chapter'],
        ['Transform pipeline and baselines', '2026-03-16', '2026-04-30', 'Complete', 'transforms.py and baseline scripts'],
        ['TrustMark integration and metric correction', '2026-05-01', '2026-05-31', 'Complete', 'trustmark_robustness.py'],
        ['100-image pilot and debugging', '2026-06-01', '2026-06-30', 'Complete', 'current CSVs and validation'],
        ['1,200-image final benchmark', '2026-08-10', '2026-08-17', 'In progress', 'run_1200_experiment.log'],
        ['Statistical analysis and figures', '2026-08-17', '2026-08-22', 'Pending', 'analysis scripts and figures'],
        ['FPR writing, proofreading, packaging', '2026-08-22', '2026-08-31', 'Pending', 'FPR and submission manifest'],
    ]
    for row in timeline_rows:
        timeline.append(row)
    timeline_chart = BarChart()
    timeline_chart.title = 'Project timeline evidence'
    timeline_chart.type = 'bar'
    timeline_chart.add_data(Reference(timeline, min_col=2, max_col=3, min_row=1, max_row=timeline.max_row), titles_from_data=True)
    timeline_chart.set_categories(Reference(timeline, min_col=1, min_row=2, max_row=timeline.max_row))
    timeline.add_chart(timeline_chart, 'G2')

    risk = workbook.create_sheet('RiskRegister')
    risk.append(['Risk', 'Probability', 'Impact', 'Rating', 'Mitigation', 'Contingency', 'Owner', 'Status'])
    risk_rows = [
        ['Disk exhaustion during benchmark', 'Medium', 'High', 'High', 'Run serially, avoid persistent artefacts, monitor storage', 'Resume from flushed CSV checkpoint', 'Student', 'Open'],
        ['Incomplete or duplicated result rows', 'Medium', 'High', 'High', 'Manifest, expected-row and duplicate-key validator', 'Reject run and rerun affected pipeline', 'Student', 'Controlled'],
        ['Non-reproducible stochastic transform', 'Low', 'High', 'Medium', 'Stable SHA-256 seed and recorded manifest', 'Regenerate affected rows', 'Student', 'Controlled'],
        ['Overclaiming authenticity', 'Medium', 'High', 'High', 'Separate similarity, watermark recovery and provenance claims', 'Restrict conclusion to tested signals', 'Student/Supervisor', 'Open'],
        ['Dataset/dependency licensing uncertainty', 'Low', 'High', 'Medium', 'Use official terms and do not redistribute source images', 'Replace dataset or obtain permission', 'Student', 'Open'],
        ['Dashboard/database integration incomplete', 'Medium', 'Medium', 'Medium', 'Describe CSV-backed prototype accurately', 'Keep production integration as future work', 'Student', 'Controlled'],
    ]
    for row in risk_rows:
        risk.append(row)

    objectives = workbook.create_sheet('ObjectiveMap')
    objectives.append(['Objective', 'Method', 'Evidence', 'Result/status', 'FPR section'])
    objective_rows = [
        ['Review literature and standards', 'Structured review of official post-2019 sources', 'Final report references and synthesis', 'Complete', 'Literature Review'],
        ['Implement deterministic transforms', 'Shared Pillow transform module', 'transforms.py, manifest, stable seed', 'Complete', 'Methodology'],
        ['Evaluate neural watermark', 'TrustMark encode/decode matrix', 'trustmark_robustness_results.csv', 'Complete for validated sample', 'Results'],
        ['Compare perceptual hashes', 'Eight hash variants and Hamming distance', 'hash_robustness_results.csv', 'Complete for validated sample', 'Results'],
        ['Compare classical baselines', 'LSB and DCT reference implementations', 'lsb/dct CSVs', 'Complete for validated sample', 'Results'],
        ['Analyse complementary signals', 'Threshold and ensemble analysis', 'ensemble_decision_matrix.csv', 'Descriptive only; not calibrated production auth', 'Evaluation'],
        ['Run payload/ECC ablation', '12-config dev sweep; selected config at 1,200', 'payload_ecc_ablation_dev100.csv, payload_ecc_ablation_selected_final1200.csv', 'Dev 97,200 rows; final 97,200 rows; validated', 'Evaluation/Future work'],
        ['Deliver usable artefact', 'CSV-backed dashboard prototype', 'dashboard files and smoke test', 'Prototype complete; database not validated', 'Implementation appendix'],
    ]
    for row in objective_rows:
        objectives.append(row)

    ecc = workbook.create_sheet('PayloadECC')
    ecc.append(['Scale', 'config', 'n', 'TM exact%', 'ensemble%', 'hash rescue pp', 'source'])
    root_results = os.environ.get('FPR_RESULTS_DIR_ROOT', os.path.join(ROOT, 'output', 'results'))

    def read_ecc(name):
        for base in (RESULTS, root_results):
            path = os.path.join(base, name)
            if os.path.exists(path):
                return list(csv.DictReader(open(path, newline='', encoding='utf-8')))
        return None

    dev = read_ecc('payload_ecc_ablation_dev100.csv')
    if dev:
        agg = defaultdict(lambda: [0, 0])
        for r in dev:
            agg[r['config_id']][0] += 1
            if r['corrected_exact'] == 'True':
                agg[r['config_id']][1] += 1
        for config in sorted(agg):
            n, ok = agg[config]
            ecc.append(['dev100', config, n, round(ok / n * 100, 2), '', '', 'payload_ecc_ablation_dev100.csv'])
    else:
        ecc.append(['dev100', 'not present', '', '', '', '', ''])
    final = read_ecc('payload_ecc_ablation_selected_final1200.csv')
    if final:
        n = len(final)
        ok = sum(1 for r in final if r['corrected_exact'] == 'True')
        ecc.append(['final1200', 'bch_super_4chars', n, round(ok / n * 100, 2), '89.36', '+23.14', 'payload_ecc_ablation_selected_final1200.csv + ensemble_aware_payload_final1200.md'])
    else:
        ecc.append(['final1200', 'not present', '', '', '', '', ''])

    for sheet in workbook.worksheets:
        sheet.freeze_panes = 'A2'
        for cell in sheet[1]:
            cell.font = Font(bold=True, color='FFFFFF')
            cell.fill = PatternFill('solid', fgColor='1F4E78')
        for column in sheet.columns:
            sheet.column_dimensions[column[0].column_letter].width = min(max(len(str(c.value or '')) for c in column) + 2, 45)

    path = os.path.join(ROOT, 'FPR_Evidence.xlsx')
    workbook.save(path)
    print(f'Wrote {path} for {images} images')


if __name__ == '__main__':
    main()
