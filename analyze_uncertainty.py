"""Image-level uncertainty summaries for the validated final1200 benchmark.

This is deliberately separate from the existing analyses.  Each image is the
sampling unit: repeated hash-algorithm rows are first reduced to one value per
image and transform condition, and confidence intervals are then computed over
those image-level values.  The script never rewrites an input CSV.
"""

import argparse
import csv
import gzip
import json
import math
import os
import statistics
import sys
from collections import defaultdict

import numpy as np


DEFAULT_DIR = os.path.join("output", "results", "final1200")
METHOD_FILES = {
    "hash": "hash_robustness_results.csv",
    "trustmark": "trustmark_robustness_results.csv",
    "lsb": "lsb_robustness_results.csv",
    "dct": "dct_robustness_results.csv",
}
HASH_BITS = {"pdq": 256}
HASH_ALGORITHMS = {
    "phash", "dhash", "ahash", "whash", "colorhash", "dhash_vertical",
    "phash_simple", "pdq",
}


def resolve_input_path(path):
    """Resolve CSV or its .gz companion, preferring an explicitly supplied path."""
    if not os.path.exists(path) and os.path.exists(path + ".gz"):
        path += ".gz"
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    return path


def open_input(path):
    """Open CSV or its .gz companion, preferring an explicitly supplied path."""
    path = resolve_input_path(path)
    if path.endswith(".gz"):
        return gzip.open(path, "rt", newline="", encoding="utf-8")
    return open(path, "r", newline="", encoding="utf-8")


def load_rows(results_dir, filename):
    path = os.path.join(results_dir, filename)
    path = resolve_input_path(path)
    with open_input(path) as stream:
        rows = list(csv.DictReader(stream))
    if not rows:
        raise ValueError(f"No data rows in {path}")
    return rows, path


def parse_float(value, field, row_number):
    try:
        value = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"Invalid {field} at input row {row_number}: {value!r}")
    if not math.isfinite(value):
        raise ValueError(f"Non-finite {field} at input row {row_number}")
    return value


def validate_rows(name, rows, image_ids, expected_algorithms=None):
    required = {"image_id", "transform_name", "intensity_value"}
    if name == "hash":
        required |= {"hash_algorithm", "hamming_distance"}
    else:
        required |= {"bit_accuracy", "decode_present"}
    missing = required - set(rows[0])
    if missing:
        raise ValueError(f"{name} input is missing columns: {sorted(missing)}")

    keys = set()
    seen_images = set()
    condition_algorithms = defaultdict(set)
    for number, row in enumerate(rows, 2):
        image_id = row["image_id"]
        condition = (image_id, row["transform_name"], row["intensity_value"])
        key = condition + ((row["hash_algorithm"],) if name == "hash" else ())
        if key in keys:
            raise ValueError(f"Duplicate {name} key at input row {number}: {key}")
        keys.add(key)
        seen_images.add(image_id)
        if name == "hash":
            algorithm = row["hash_algorithm"]
            if algorithm not in HASH_ALGORITHMS:
                raise ValueError(f"Unexpected hash algorithm: {algorithm}")
            condition_algorithms[condition].add(algorithm)
            distance = parse_float(row["hamming_distance"], "hamming_distance", number)
            bits = 256 if algorithm == "pdq" else 64
            if not 0 <= distance <= bits:
                raise ValueError(f"Hamming distance outside [0, {bits}] at row {number}")
        else:
            accuracy = parse_float(row["bit_accuracy"], "bit_accuracy", number)
            if not 0 <= accuracy <= 1:
                raise ValueError(f"bit_accuracy outside [0, 1] at row {number}")
            if row["decode_present"].strip().lower() not in {"true", "false"}:
                raise ValueError(f"Invalid decode_present at input row {number}")

    if seen_images != image_ids:
        missing_images = len(image_ids - seen_images)
        extra_images = len(seen_images - image_ids)
        raise ValueError(f"{name} image coverage mismatch: missing={missing_images}, extra={extra_images}")
    if expected_algorithms is not None:
        incomplete = [key for key, algorithms in condition_algorithms.items()
                      if algorithms != expected_algorithms]
        if incomplete:
            raise ValueError(f"{name} has incomplete hash algorithm coverage for {len(incomplete)} conditions")


def percentile(values, probability):
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def bootstrap_mean_interval(values, rng, repetitions):
    """Percentile bootstrap 95% CI for a mean of image-level observations."""
    if len(values) == 1:
        return values[0], values[0]
    # Vectorization keeps the fixed-resample procedure practical for 1,200
    # images without changing the image-level sampling unit.
    sample_indices = rng.integers(0, len(values), size=(repetitions, len(values)))
    boot_means = np.asarray(values)[sample_indices].mean(axis=1)
    return percentile(boot_means.tolist(), 0.025), percentile(boot_means.tolist(), 0.975)


def wilson_interval(successes, trials, z=1.959963984540054):
    """Wilson 95% interval for a binomial proportion."""
    if not trials:
        return None, None
    p = successes / trials
    denominator = 1 + z * z / trials
    centre = (p + z * z / (2 * trials)) / denominator
    margin = z * math.sqrt((p * (1 - p) + z * z / (4 * trials)) / trials) / denominator
    return max(0.0, centre - margin), min(1.0, centre + margin)


def aggregate(rows, name):
    grouped = defaultdict(list)
    for row in rows:
        key = (row["transform_name"], row["intensity_value"], row["image_id"])
        if name == "hash":
            algorithm = row["hash_algorithm"]
            bits = 256 if algorithm == "pdq" else 64
            grouped[key].append(parse_float(row["hamming_distance"], "hamming_distance", 0) / bits)
        else:
            grouped[key].append((parse_float(row["bit_accuracy"], "bit_accuracy", 0),
                                 row["decode_present"].strip().lower() == "true"))

    output = []
    if name == "hash":
        for condition, values in grouped.items():
            if len(values) != len(HASH_ALGORITHMS):
                raise ValueError(f"Hash condition does not have 8 algorithms: {condition}")
            output.append((condition, "mean_bit_error_fraction", statistics.fmean(values)))
            output.append((condition, "worst_algorithm_bit_error_fraction", max(values)))
    else:
        for condition, values in grouped.items():
            if len(values) != 1:
                raise ValueError(f"{name} has repeated image-condition rows: {condition}")
            output.append((condition, "bit_accuracy", values[0][0]))
            output.append((condition, "decode_present", 1.0 if values[0][1] else 0.0))
    return output


def format_number(value):
    return "" if value is None else f"{value:.6f}"


def run(results_dir, output_dir, seed, repetitions, validate=True):
    manifest_path = os.path.join(results_dir, "image_manifest.json")
    with open(manifest_path, "r", encoding="utf-8") as stream:
        manifest = json.load(stream)
    image_ids = {entry["image_id"] for entry in manifest["images"]}
    if len(image_ids) != manifest["image_count"]:
        raise ValueError("image_manifest.json contains duplicate image IDs")

    all_values = []
    loaded = {}
    for name, filename in METHOD_FILES.items():
        rows, path = load_rows(results_dir, filename)
        loaded[name] = (rows, path)
        if validate:
            validate_rows(name, rows, image_ids,
                          HASH_ALGORITHMS if name == "hash" else None)
        all_values.extend((name, metric, condition, value)
                          for condition, metric, value in aggregate(rows, name))

    # Group again by method, metric, and condition, leaving exactly one value
    # per image.  A fixed local RNG makes bootstrap results reproducible.
    by_condition = defaultdict(list)
    for name, metric, condition, value in all_values:
        by_condition[(name, metric, condition[0], condition[1])].append(value)

    rng = np.random.default_rng(seed)
    summary_rows = []
    for (name, metric, transform, intensity), values in sorted(by_condition.items()):
        mean = statistics.fmean(values)
        row = {
            "method": name,
            "metric": metric,
            "transform_name": transform,
            "intensity_value": intensity,
            "n_images": len(values),
            "mean": format_number(mean),
            "median": format_number(statistics.median(values)),
            "sd": format_number(statistics.stdev(values) if len(values) > 1 else 0.0),
            "ci_level": "0.95",
            "ci_method": "wilson_binomial" if metric == "decode_present" else "percentile_bootstrap_mean",
            "ci_low": "",
            "ci_high": "",
            "bootstrap_seed": seed if metric != "decode_present" else "",
            "bootstrap_repetitions": repetitions if metric != "decode_present" else "",
        }
        if metric == "decode_present":
            low, high = wilson_interval(round(sum(values)), len(values))
        else:
            low, high = bootstrap_mean_interval(values, rng, repetitions)
        row["ci_low"] = format_number(low)
        row["ci_high"] = format_number(high)
        summary_rows.append(row)

    os.makedirs(output_dir, exist_ok=True)
    csv_path = os.path.join(output_dir, "uncertainty_summary.csv")
    fields = list(summary_rows[0])
    with open(csv_path, "w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(summary_rows)

    md_path = os.path.join(output_dir, "uncertainty_summary.md")
    source_lines = [f"`{name}`: `{os.path.basename(path)}`" for name, (_, path) in loaded.items()]
    with open(md_path, "w", encoding="utf-8") as stream:
        stream.write("# Final1200 Uncertainty Summary\n\n")
        stream.write("All summaries use the image as the statistical unit. For hash results, the "
                     "eight algorithm rows are first reduced within each image and transform "
                     "condition to a mean and a worst-algorithm bit-error fraction; intervals "
                     "then span images, not algorithm rows. Continuous metrics use a fixed-seed "
                     f"percentile bootstrap ({repetitions:,} resamples); decode proportions use "
                     "the Wilson binomial 95% interval.\n\n")
        stream.write(f"- Images: {len(image_ids):,}\n- Bootstrap seed: `{seed}`\n")
        stream.write(f"- Rows written: {len(summary_rows):,}\n- Validation: {'enabled' if validate else 'disabled'}\n")
        stream.write("\n## Inputs\n\n")
        stream.write("\n".join(f"- {line}" for line in source_lines))
        stream.write("\n\n## Fields\n\n")
        stream.write("`mean`, `median`, and `sd` are descriptive statistics over image-level "
                     "values. `ci_low` and `ci_high` are 95% confidence limits. The CSV is the "
                     "machine-readable output; this file documents aggregation and provenance.\n")
        stream.write("\n## Limitations\n\n")
        stream.write("- Intervals describe sampling uncertainty across this fixed image sample; they "
                     "do not model transform implementation, codec, or pipeline uncertainty.\n")
        stream.write("- Images are treated as independent, although image content and dataset "
                     "selection can be correlated.\n")
        stream.write("- Bootstrap intervals are not used for decode rates because those outcomes are "
                     "binomial observations.\n")
    print(f"Wrote {csv_path}")
    print(f"Wrote {md_path}")


def self_test():
    rng = np.random.default_rng(42)
    low, high = bootstrap_mean_interval([0.0, 0.5, 1.0], rng, 200)
    assert 0 <= low <= high <= 1
    low, high = wilson_interval(0, 3)
    assert low <= 1e-12 and high > 0
    print("self-test passed")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-dir", default=DEFAULT_DIR)
    parser.add_argument("--output-dir", default=DEFAULT_DIR)
    parser.add_argument("--seed", type=int, default=20260812)
    parser.add_argument("--bootstrap-repetitions", type=int, default=2000)
    parser.add_argument("--no-validate", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    if args.bootstrap_repetitions < 100:
        parser.error("--bootstrap-repetitions must be at least 100")
    try:
        run(args.results_dir, args.output_dir, args.seed, args.bootstrap_repetitions,
            validate=not args.no_validate)
    except (FileNotFoundError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
