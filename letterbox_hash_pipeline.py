"""
Letterboxing + Perceptual Hash Robustness Pipeline
----------------------------------------------------
Project: Steganographic Signing and Filter Traceability in Digital Media
Purpose: Load sample MS-COCO val2017 images, apply letterboxing,
         compute pHash/dHash/aHash before and after, and measure
         Hamming distance to evaluate perceptual hash robustness
         to letterboxing as a candidate fallback-layer transform.

SETUP (one-off, run locally — NOT inside this script):
    COCO hotlinks individual images inconsistently (some requests to
    images.cocodataset.org/val2017/<id>.jpg return 403 depending on
    network/region/headers). The dataset's own documented method is
    the bulk zip download. Run once:

        wget http://images.cocodataset.org/zips/val2017.zip
        unzip val2017.zip -d ./coco_val2017

    This gives you a local folder of ~5,000 images named like
    000000397133.jpg. Point --image-dir at that folder.

    `requests` is still used below — for the FastAPI integration step
    (calling your own /sign and /verify endpoints once built), which is
    the actual production-relevant use of that library in this project.
    Bulk dataset acquisition and live API calls are different concerns
    and shouldn't share the same fetch pattern.

Usage:
    python letterbox_hash_pipeline.py --image-dir ./coco_val2017 --n 20
"""

import argparse
import csv
from pathlib import Path

import imagehash
import numpy as np
import pdqhash
from PIL import Image

# --------------------------------------------------------------------------
# Config
# --------------------------------------------------------------------------
TARGET_SIZE = (480, 480)  # per dissertation spec
OUTPUT_DIR = Path("output")
LETTERBOXED_DIR = OUTPUT_DIR / "letterboxed"
RESULTS_CSV = OUTPUT_DIR / "hash_robustness_results_black_fill.csv"
RESULTS_CSV_GREY = OUTPUT_DIR / "hash_robustness_results_grey_fill.csv"


# --------------------------------------------------------------------------
# Step 1: Load local images
# --------------------------------------------------------------------------
def find_sample_images(image_dir: Path, n: int) -> list[Path]:
    """Return up to n image paths from a local COCO val2017 folder."""
    candidates = sorted(image_dir.glob("*.jpg"))
    if not candidates:
        raise FileNotFoundError(
            f"No .jpg files found in {image_dir}. "
            "Download and unzip val2017.zip first (see module docstring)."
        )
    return candidates[:n]


# --------------------------------------------------------------------------
# Step 2: Letterbox transform
# --------------------------------------------------------------------------
def letterbox(image: Image.Image, target_size: tuple[int, int],
              fill_color: tuple[int, int, int] = (0, 0, 0)) -> Image.Image:
    """
    Resize an image to fit within target_size while preserving aspect ratio,
    padding the remaining space with fill_color (letterboxing).
    This is the geometric transform under evaluation: it changes pixel
    layout and introduces uniform padding without cropping any content,
    distinct from the cropping/rotation/scaling transforms also in scope.
    """
    image = image.convert("RGB")
    original_w, original_h = image.size
    target_w, target_h = target_size

    scale = min(target_w / original_w, target_h / original_h)
    new_w, new_h = int(original_w * scale), int(original_h * scale)
    resized = image.resize((new_w, new_h), Image.LANCZOS)

    canvas = Image.new("RGB", target_size, fill_color)
    paste_x = (target_w - new_w) // 2
    paste_y = (target_h - new_h) // 2
    canvas.paste(resized, (paste_x, paste_y))
    return canvas


# --------------------------------------------------------------------------
# Step 3: Perceptual hashing
# --------------------------------------------------------------------------
HASH_FUNCS = {
    "phash": imagehash.phash,   # DCT-based; reported in literature as more robust to scaling
    "dhash": imagehash.dhash,   # gradient-based; sensitive to edge shifts
    "ahash": imagehash.average_hash,  # simplest, most sensitive to layout change
}


def pdq_hash(image: Image.Image) -> tuple[np.ndarray, int]:
    """Compute PDQ hash via Meta's pdqhash library.

    Returns (256-element binary vector, quality_score).
    Quality 0-100; >= 50 recommended as reliable per pdq-rs and Go
    pdq library docstrings, >= 80 per Facebook's own implementation
    verification standard (ThreatExchange README).
    """
    image_array = np.array(image.convert("RGB"))
    hash_vector, quality = pdqhash.compute(image_array)
    return hash_vector, quality


HASH_FUNCS_PDQ = {"pdq": pdq_hash}  # handled separately due to different API
ALL_HASH_NAMES = list(HASH_FUNCS) + list(HASH_FUNCS_PDQ)


def compute_hashes(image: Image.Image
                   ) -> tuple[dict[str, imagehash.ImageHash | np.ndarray],
                              dict[str, int]]:
    """Return (hash_dict, quality_dict).

    quality_dict only contains entries for hash types that return
    a quality score (currently pdq only).
    """
    hash_result: dict[str, imagehash.ImageHash | np.ndarray] = {}
    quality_result: dict[str, int] = {}
    for name, func in HASH_FUNCS.items():
        hash_result[name] = func(image)
    for name, func in HASH_FUNCS_PDQ.items():
        hv, q = func(image)
        hash_result[name] = hv
        quality_result[name] = q
    return hash_result, quality_result


# --------------------------------------------------------------------------
# Main pipeline
# --------------------------------------------------------------------------
def main(image_dir: Path, n: int, *,
         fill_color: tuple[int, int, int] = (0, 0, 0),
         results_csv: Path = RESULTS_CSV) -> list[dict]:
    LETTERBOXED_DIR.mkdir(parents=True, exist_ok=True)

    image_paths = find_sample_images(image_dir, n)
    rows: list[dict] = []

    color_label = "black" if fill_color == (0, 0, 0) else f"rgb{fill_color}"
    print(f"Processing {len(image_paths)} images from {image_dir} "
          f"(fill={color_label})...\n")

    for raw_path in image_paths:
        image_id = raw_path.stem
        print(f"[{image_id}]")

        original = Image.open(raw_path)
        w, h = original.size
        aspect_ratio = max(w, h) / min(w, h)

        letterboxed = letterbox(original, TARGET_SIZE, fill_color=fill_color)
        letterboxed.save(LETTERBOXED_DIR / f"{image_id}_letterboxed_{color_label}.jpg")

        original_hashes, original_quality = compute_hashes(original)
        letterboxed_hashes, letterboxed_quality = compute_hashes(letterboxed)

        row = {
            "image_id": image_id,
            "original_size": f"{w}x{h}",
            "aspect_ratio": f"{aspect_ratio:.4f}",
        }

        for hash_name in ALL_HASH_NAMES:
            oh = original_hashes[hash_name]
            lh = letterboxed_hashes[hash_name]
            if hash_name in HASH_FUNCS_PDQ:
                distance = int(np.count_nonzero(oh != lh))
                oq = original_quality[hash_name]
                lq = letterboxed_quality[hash_name]
                row["pdq_quality_original"] = oq
                row["pdq_quality_letterboxed"] = lq
                print(f"     pdq: bits_set_orig={int(np.count_nonzero(oh))} "
                      f"bits_set_let={int(np.count_nonzero(lh))} "
                      f"qual_orig={oq} qual_let={lq} "
                      f"hamming_distance={distance}")
            else:
                distance = oh - lh
                print(f"  {hash_name:>6}: original={oh} "
                      f"letterboxed={lh} "
                      f"hamming_distance={distance}")
            row[f"{hash_name}_hamming_distance"] = distance
        rows.append(row)
        print()

    # Write results CSV
    if rows:
        with open(results_csv, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
        print(f"Results written to {results_csv}")

        # Quick summary stats per hash type
        print("\n--- Summary: mean Hamming distance after letterboxing ---")
        for hash_name in ALL_HASH_NAMES:
            distances = [r[f"{hash_name}_hamming_distance"] for r in rows]
            mean_dist = sum(distances) / len(distances)
            print(f"  {hash_name}: mean={mean_dist:.2f}, max={max(distances)}, min={min(distances)}")

        # PDQ quality summary
        print("\n--- PDQ quality scores (0-100) ---")
        oqs = [r["pdq_quality_original"] for r in rows]
        lqs = [r["pdq_quality_letterboxed"] for r in rows]
        print(f"  original:   mean={sum(oqs)/len(oqs):.1f}, min={min(oqs)}, max={max(oqs)}")
        print(f"  letterboxed: mean={sum(lqs)/len(lqs):.1f}, min={min(lqs)}, max={max(lqs)}")
        drops = [o - l for o, l in zip(oqs, lqs)]
        if any(d < 0 for d in drops):
            print(f"  NOTE: {sum(1 for d in drops if d < 0)} image(s) had quality *increase* after letterboxing")
        if any(d > 0 for d in drops):
            print(f"  NOTE: {sum(1 for d in drops if d > 0)} image(s) had quality drop after letterboxing")
    else:
        print("No images were successfully processed.")

    return rows


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Letterbox + perceptual hash robustness pipeline")
    parser.add_argument("--image-dir", type=Path, required=True,
                         help="Path to local folder of COCO val2017 .jpg images")
    parser.add_argument("--n", type=int, default=10, help="Number of sample images to process")
    parser.add_argument("--fill", type=str, default="black",
                         choices=["black", "grey"],
                         help="Letterbox fill color: black (0,0,0) or grey (128,128,128)")
    parser.add_argument("--output-csv", type=Path, default=None,
                         help="Output CSV path (default: auto-named based on fill)")
    args = parser.parse_args()

    if args.fill == "black":
        fill = (0, 0, 0)
        csv_path = args.output_csv or OUTPUT_DIR / "hash_robustness_results_black_fill.csv"
    else:
        fill = (128, 128, 128)
        csv_path = args.output_csv or RESULTS_CSV_GREY

    main(args.image_dir, args.n, fill_color=fill, results_csv=csv_path)
