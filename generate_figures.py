"""Regenerate report figures from result CSVs without hardcoded sample sizes."""

import csv
import os
from collections import defaultdict

import matplotlib.pyplot as plt


ROOT = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.environ.get('FPR_RESULTS_DIR', os.path.join(ROOT, 'output', 'results'))
FIGURES = os.path.join(ROOT, 'output', 'figures')


def read(name):
    with open(os.path.join(RESULTS, name), newline='', encoding='utf-8') as stream:
        return list(csv.DictReader(stream))


def main():
    os.makedirs(FIGURES, exist_ok=True)
    tm, lsb, dct = (read(f'{name}_robustness_results.csv') for name in ('trustmark', 'lsb', 'dct'))
    image_count = len({row['image_id'] for row in tm})
    grouped = defaultdict(lambda: [[], [], []])
    for method_index, rows in enumerate((tm, lsb, dct)):
        for row in rows:
            if row['transform_name'] != 'none':
                grouped[row['transform_name']][method_index].append(float(row['bit_accuracy']))
    names = sorted(grouped)
    means = [[sum(grouped[name][i]) / len(grouped[name][i]) for name in names] for i in range(3)]
    fig, axis = plt.subplots(figsize=(13, 6))
    for label, values in zip(('TrustMark', 'LSB', 'DCT'), means):
        axis.plot(names, values, marker='o', label=label)
    axis.axhline(0.5, color='black', linestyle='--', linewidth=0.8, label='50% reference')
    axis.set_title(f'Watermark baseline comparison ({image_count} images)')
    axis.set_ylabel('Mean raw bit accuracy')
    axis.set_ylim(0, 1.05)
    axis.tick_params(axis='x', rotation=45)
    axis.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(FIGURES, 'fpr_method_comparison.png'), dpi=180)
    plt.close(fig)
    print(f'Wrote FPR figures for {image_count} images')


if __name__ == '__main__':
    main()
