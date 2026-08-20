"""Validate result coverage before statistical analysis or report updates."""

import argparse
import csv
import os
import gzip
from collections import Counter
import transforms


def read_rows(path):
    if not os.path.exists(path) and os.path.exists(path + '.gz'):
        path += '.gz'
    stream = gzip.open(path, 'rt', newline='', encoding='utf-8') if path.endswith('.gz') else open(path, newline='', encoding='utf-8')
    with stream:
        return list(csv.DictReader(stream))


def validate(path, image_count, expected_per_image, key_columns):
    rows = read_rows(path)
    ids = {row['image_id'] for row in rows}
    keys = [tuple(row[column] for column in key_columns) for row in rows]
    duplicates = len(keys) - len(set(keys))
    expected_rows = image_count * expected_per_image
    print(f'{os.path.basename(path)}: rows={len(rows)}, images={len(ids)}, expected_rows={expected_rows}, duplicates={duplicates}')
    if len(ids) != image_count or len(rows) != expected_rows or duplicates:
        raise SystemExit(f'Coverage validation failed for {path}')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--image-count', type=int, required=True)
    parser.add_argument('--results-dir', default='output/results')
    args = parser.parse_args()
    transform_count = sum(len(values) for values in transforms.TRANSFORM_STEPS.values())
    validate(os.path.join(args.results_dir, 'hash_robustness_results.csv'), args.image_count,
             transform_count * 8, ['image_id', 'transform_name', 'intensity_value', 'hash_algorithm'])
    for name in ('trustmark', 'lsb', 'dct'):
        validate(os.path.join(args.results_dir, f'{name}_robustness_results.csv'), args.image_count,
                 transform_count + 1, ['image_id', 'transform_name', 'intensity_value'])
    print('All result files passed coverage and duplicate-key validation.')


if __name__ == '__main__':
    main()
