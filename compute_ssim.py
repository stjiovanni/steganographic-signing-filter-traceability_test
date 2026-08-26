"""Compute SSIM + PSNR for the saved watermarked images.

Pairs each saved watermarked image (output/trustmark_watermarked,
output/lsb_watermarked, output/dct_watermarked) against its original in
coco_val2017/val2017 and writes output/remediation_ssim.csv.

This is a remediation metric only: it runs on whatever watermarked images
are already persisted, without re-running any watermark pipeline.
"""

import os, csv, math, argparse
from glob import glob
from PIL import Image
import numpy as np
import transforms
from ssim_metric import ssim

OUTPUT_DIR = transforms.OUTPUT_DIR
COCO_DIR = transforms.COCO_DIR
DEFAULT_OUTPUT_CSV = os.path.join(OUTPUT_DIR, 'remediation_ssim.csv')

# Map of watermarked-image subdirectories to scan.
WATERMARKED_DIRS = ['trustmark_watermarked', 'lsb_watermarked', 'dct_watermarked']


def mse_psnr(img1, img2):
    """Return (mse, psnr_dB) between two PIL images."""
    arr1 = np.asarray(img1).astype(np.int16)
    arr2 = np.asarray(img2).astype(np.int16)
    mse = np.mean(np.square(arr1 - arr2))
    if mse == 0:
        return 0.0, float('inf')
    psnr = 20 * math.log10(255.0) - 10 * math.log10(mse)
    return float(mse), float(psnr)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--watermark-dir', action='append', default=None,
                        help='Watermarked image dir to scan (repeatable). Default: all standard dirs.')
    parser.add_argument('--orig-dir', default=COCO_DIR)
    parser.add_argument('--output-csv', default=DEFAULT_OUTPUT_CSV)
    args = parser.parse_args()

    dirs = args.watermark_dir if args.watermark_dir else [
        os.path.join(OUTPUT_DIR, d) for d in WATERMARKED_DIRS
    ]

    rows = []
    missing_originals = 0
    total_found = 0

    for wm_dir in dirs:
        if not os.path.isdir(wm_dir):
            print(f'Skipping missing dir: {wm_dir}')
            continue
        files = sorted(glob(os.path.join(wm_dir, '*.jpg')))
        if not files:
            print(f'No watermarked images found in: {wm_dir}')
            continue
        for wm_path in files:
            total_found += 1
            fname = os.path.basename(wm_path)
            image_id = os.path.splitext(fname)[0]
            orig_path = os.path.join(args.orig_dir, fname)
            if not os.path.exists(orig_path):
                print(f'  WARNING: original not found for {fname} (skipping)')
                missing_originals += 1
                continue
            try:
                img_wm = Image.open(wm_path).convert('RGB')
                img_orig = Image.open(orig_path).convert('RGB')
            except Exception as e:
                print(f'  ERROR opening {wm_path}: {e}')
                continue

            mse, psnr = mse_psnr(img_orig, img_wm)
            ssim_val = ssim(np.asarray(img_orig), np.asarray(img_wm))
            psnr_str = f'{psnr:.4f}' if math.isfinite(psnr) else 'inf'
            rows.append({
                'watermark_dir': os.path.basename(wm_dir),
                'filename': fname,
                'image_id': image_id,
                'psnr_db': psnr_str,
                'ssim': f'{ssim_val:.4f}',
            })
            print(f'  {os.path.basename(wm_dir):<22} {fname}  '
                  f'PSNR={psnr_str:>8} dB  SSIM={ssim_val:.4f}')

    os.makedirs(os.path.dirname(args.output_csv), exist_ok=True)
    fieldnames = ['watermark_dir', 'filename', 'image_id', 'psnr_db', 'ssim']
    with open(args.output_csv, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f'\nTotal saved watermarked images found: {total_found}')
    print(f'Rows written: {len(rows)} (missing originals: {missing_originals})')
    print(f'CSV written to: {args.output_csv}')


if __name__ == '__main__':
    main()
