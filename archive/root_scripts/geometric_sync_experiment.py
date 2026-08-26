"""Opt-in geometric synchronisation pilot.

This is deliberately separate from the benchmark pipelines.  It reads source
images, applies a small declared set of transforms, and writes only its own
CSV.  It does not read, merge, or modify any existing result CSV.

No scientific result is implied until this module is executed on the selected
dataset.  Estimated alignment is optional: OpenCV is used only when present
and when its affine fit passes conservative sanity checks.
"""

import argparse
import csv
import json
import math
import os
import sys
import time
from glob import glob

from PIL import Image

import transforms


EXPERIMENT_NAME = "geometric_sync_pilot_v1"
IMAGE_COUNT = 8
HASH_NAMES = ("phash", "dhash", "ahash", "whash")
CONDITIONS = (
    ("rotation", 5),
    ("rotation", 20),
    ("scaling", 0.75),
    ("scaling", 1.5),
)
ALIGNMENT_MODES = ("none", "oracle", "estimated")
METRIC = "hamming_distance"


def _hashes(image):
    """Compute only image-derived perceptual metrics used by this pilot."""
    import imagehash

    rgb = image.convert("RGB")
    return {
        "phash": str(imagehash.phash(rgb)),
        "dhash": str(imagehash.dhash(rgb)),
        "ahash": str(imagehash.average_hash(rgb)),
        "whash": str(imagehash.whash(rgb, mode="haar")),
    }


def _hamming(left, right):
    if len(left) != len(right):
        raise ValueError("hash lengths differ")
    return sum(a != b for a, b in zip(left, right))


def _oracle_align(image, transform_name, intensity, reference_size):
    """Undo the known transform; crop loss is not included in this pilot."""
    if transform_name == "rotation":
        aligned = image.rotate(-int(intensity), expand=False, fillcolor=128)
    elif transform_name == "scaling":
        aligned = image.resize(reference_size, Image.Resampling.LANCZOS)
    else:
        raise ValueError(f"oracle alignment is not declared for {transform_name}")
    return aligned.convert("RGB")


def _estimated_align(image, reference):
    """Estimate a bounded affine warp, or raise a recorded failure."""
    try:
        import cv2
        import numpy as np
    except ImportError as exc:
        raise RuntimeError("OpenCV/numpy unavailable for estimated alignment") from exc

    width, height = reference.size
    candidate = image.convert("RGB").resize((width, height), Image.Resampling.BILINEAR)
    template_gray = np.asarray(reference.convert("L"), dtype=np.float32) / 255.0
    candidate_gray = np.asarray(candidate.convert("L"), dtype=np.float32) / 255.0
    warp = np.eye(2, 3, dtype=np.float32)
    criteria = (
        cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT,
        80,
        1e-5,
    )
    try:
        correlation, warp = cv2.findTransformECC(
            template_gray,
            candidate_gray,
            warp,
            cv2.MOTION_AFFINE,
            criteria,
            None,
            1,
        )
    except cv2.error as exc:
        raise RuntimeError(f"ECC alignment failed: {exc}") from exc

    if not math.isfinite(float(correlation)) or float(correlation) < 0.10:
        raise RuntimeError(f"ECC correlation below safety threshold: {correlation}")
    if not np.isfinite(warp).all() or np.max(np.abs(warp)) > 4.0:
        raise RuntimeError("estimated affine parameters failed safety bounds")

    aligned = cv2.warpAffine(
        np.asarray(candidate),
        warp,
        (width, height),
        flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=(128, 128, 128),
    )
    return Image.fromarray(aligned).convert("RGB")


def validate_configuration():
    """Small dependency-free validation suitable for CI and dry-run checks."""
    assert IMAGE_COUNT > 0
    assert HASH_NAMES == tuple(dict.fromkeys(HASH_NAMES))
    assert len(CONDITIONS) > 0
    assert set(ALIGNMENT_MODES) == {"none", "oracle", "estimated"}
    for name, intensity in CONDITIONS:
        assert name in {"rotation", "scaling"}
        assert intensity in transforms.TRANSFORM_STEPS[name]
    sample = Image.new("RGB", (32, 24), (90, 120, 150))
    assert _oracle_align(sample, "rotation", 5, sample.size).size == sample.size
    assert _oracle_align(sample, "scaling", 0.75, sample.size).size == sample.size
    sample.close()
    return True


def select_images(input_dir, image_count=IMAGE_COUNT):
    paths = sorted(glob(os.path.join(input_dir, "*.jpg")))
    if len(paths) < image_count:
        raise ValueError(f"Only {len(paths)} JPG images found; {image_count} required")
    return paths[:image_count]


def _failure_row(image_id, filename, transform_name, intensity, mode, method,
                 runtime, error):
    return {
        "experiment": EXPERIMENT_NAME,
        "image_id": image_id,
        "filename": filename,
        "method": method,
        "transform": transform_name,
        "transform_parameters": json.dumps({"intensity": intensity}, sort_keys=True),
        "alignment_mode": mode,
        "metric": METRIC,
        "metric_value": "",
        "runtime_seconds": f"{runtime:.6f}",
        "failure": error,
    }


def evaluate_image(path):
    filename = os.path.basename(path)
    image_id = os.path.splitext(filename)[0]
    rows = []
    with Image.open(path) as source:
        reference = source.convert("RGB")
    try:
        reference_hashes = _hashes(reference)
        for transform_name, intensity in CONDITIONS:
            transformed = None
            try:
                transformed = transforms.apply_transform(
                    reference, transform_name, intensity, image_id=image_id
                )
            except Exception as exc:
                for mode in ALIGNMENT_MODES:
                    for method in HASH_NAMES:
                        rows.append(_failure_row(
                            image_id, filename, transform_name, intensity, mode,
                            method, 0.0, f"transform failed: {exc}"))
                continue

            for mode in ALIGNMENT_MODES:
                for method in HASH_NAMES:
                    started = time.perf_counter()
                    aligned = None
                    try:
                        if mode == "none":
                            aligned = transformed.convert("RGB")
                        elif mode == "oracle":
                            aligned = _oracle_align(
                                transformed, transform_name, intensity, reference.size
                            )
                        else:
                            aligned = _estimated_align(transformed, reference)
                        value = _hamming(_hashes(aligned)[method], reference_hashes[method])
                        rows.append({
                            "experiment": EXPERIMENT_NAME,
                            "image_id": image_id,
                            "filename": filename,
                            "method": method,
                            "transform": transform_name,
                            "transform_parameters": json.dumps(
                                {"intensity": intensity}, sort_keys=True
                            ),
                            "alignment_mode": mode,
                            "metric": METRIC,
                            "metric_value": str(value),
                            "runtime_seconds": f"{time.perf_counter() - started:.6f}",
                            "failure": "",
                        })
                    except Exception as exc:
                        rows.append(_failure_row(
                            image_id, filename, transform_name, intensity, mode,
                            method, time.perf_counter() - started, str(exc)))
                    finally:
                        if aligned is not None:
                            aligned.close()
            transformed.close()
    finally:
        reference.close()
    return rows


FIELDNAMES = [
    "experiment", "image_id", "filename", "method", "transform",
    "transform_parameters", "alignment_mode", "metric", "metric_value",
    "runtime_seconds", "failure",
]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", default=transforms.COCO_DIR)
    parser.add_argument(
        "--output-csv",
        default=os.path.join(transforms.OUTPUT_DIR, "results", "geometric_sync_experiment.csv"),
    )
    parser.add_argument("--image-count", type=int, default=IMAGE_COUNT)
    parser.add_argument("--dry-run", action="store_true", help="validate and print the plan only")
    parser.add_argument("--validate", action="store_true", help="run dependency-free unit validation")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args(argv)

    validate_configuration()
    if args.validate:
        print("geometric_sync_experiment validation: PASS")
        return 0
    if args.image_count < 1 or args.image_count > IMAGE_COUNT:
        parser.error(f"--image-count must be between 1 and {IMAGE_COUNT}")
    paths = select_images(args.input_dir, args.image_count)
    print(f"Plan: {EXPERIMENT_NAME}; images={len(paths)}; conditions={len(CONDITIONS)};")
    print(f"      modes={','.join(ALIGNMENT_MODES)}; methods={','.join(HASH_NAMES)}")
    print("      estimated alignment requires optional OpenCV and records failures safely")
    if args.dry_run:
        print("Dry run only: no images processed and no files written.")
        return 0
    if os.path.exists(args.output_csv) and not args.overwrite:
        raise SystemExit(f"Output exists; pass --overwrite to replace only {args.output_csv}")
    parent = os.path.dirname(args.output_csv)
    if parent:
        os.makedirs(parent, exist_ok=True)
    started = time.perf_counter()
    with open(args.output_csv, "w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDNAMES)
        writer.writeheader()
        for path in paths:
            for row in evaluate_image(path):
                writer.writerow(row)
    print(f"Wrote experiment-only results to {args.output_csv}")
    print(f"Elapsed CPU/wall time: {time.perf_counter() - started:.2f}s")
    print("No baseline result files were read or modified.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
