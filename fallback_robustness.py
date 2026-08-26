"""Two-layer payload-recovery pipeline (fallback watermark channel).

For each image: TrustMark encode (primary), then fallback watermark embed
(BCH_SUPER-coded payload in DCT with repetition). Decodes the fallback
channel for every condition. Also decodes TrustMark on the combined image
for the untransformed baseline to measure any combined-embedding degradation.

Two-layer recovery is computed offline: TrustMark decode-present per condition
(from trustmark_robustness_results.csv) OR fallback decode-present per condition
(from this file). The perceptual hash stays a separate similarity screen.
"""

import argparse
import csv
import os
import random
import sys
import time
from collections import defaultdict
from glob import glob

from PIL import Image

import fallback_watermark as fb
import transforms
from metrics import mse_psnr

PIPELINE_VERSION = 'fallback-v1'
FALLBACK_PAYLOAD = fb.FALLBACK_PAYLOAD
LOG_PATH = os.path.join(transforms.OUTPUT_DIR, 'logs', 'fallback_1200.log')


def log(msg):
    line = f'[{time.strftime("%H:%M:%S")}] {msg}'
    print(line, flush=True)
    try:
        with open(LOG_PATH, 'a', encoding='utf-8') as f:
            f.write(line + '\n')
    except OSError:
        pass


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input-dir', default=transforms.COCO_DIR)
    parser.add_argument('--output-csv', default=os.path.join(transforms.OUTPUT_DIR, 'results', 'final1200', 'fallback_robustness_results.csv'))
    parser.add_argument('--image-count', type=int, default=1200)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--save-image-count', type=int, default=0)
    parser.add_argument('--resume', action='store_true')
    args = parser.parse_args()

    random.seed(args.seed)
    image_files = sorted(glob(os.path.join(args.input_dir, '*.jpg')))[:args.image_count]
    print(f'Found {len(image_files)} images', flush=True)

    done_images = set()
    if args.resume and os.path.exists(args.output_csv):
        with open(args.output_csv, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            counts = defaultdict(int)
            for row in reader:
                if row['transform_name'] != 'none':
                    counts[row['image_id']] += 1
        expected_per_image = 1 + sum(len(v) for v in transforms.TRANSFORM_STEPS.values()) - 1
        done_images = {img for img, n in counts.items() if n == sum(len(v) for v in transforms.TRANSFORM_STEPS.values())}
        print(f'Resume: {len(done_images)} images already complete', flush=True)

    from trustmark import TrustMark
    from trustmark_robustness import decode_batch_and_accuracy, encode_payload_to_packet, TM_PAYLOAD
    tm = TrustMark(verbose=False, model_type='Q', encoding_type=TrustMark.Encoding.BCH_4)
    layer = fb.make_codec()
    tm_packet = encode_payload_to_packet(tm, TM_PAYLOAD)
    print('TrustMark + fallback codec loaded', flush=True)

    fieldnames = ['image_id', 'filename', 'transform_name', 'intensity_value',
                  'pipeline_version', 'encode_mse', 'encode_psnr',
                  'fb_decode_secret', 'fb_decode_present', 'fb_bit_accuracy',
                  'tm_combined_baseline_present', 'width', 'height', 'aspect_ratio']
    mode = 'a' if args.resume and os.path.exists(args.output_csv) else 'w'
    out = open(args.output_csv, mode, newline='')
    writer = csv.DictWriter(out, fieldnames=fieldnames)
    if mode == 'w':
        writer.writeheader()

    baseline_jobs = []   # combined images for TM baseline decode (batched)
    baseline_rows = []
    t_start = time.time()

    for idx, img_path in enumerate(image_files):
        fname = os.path.basename(img_path)
        image_id = os.path.splitext(fname)[0]
        if image_id in done_images:
            continue
        try:
            img_orig = Image.open(img_path).convert('RGB')
        except Exception as e:
            print(f'ERROR open {fname}: {e}', file=sys.stderr)
            continue
        w, h = img_orig.size
        aspect = round(w / h if h else 0, 6)

        try:
            img_tm = tm.encode(img_orig, TM_PAYLOAD)
            img_combined = fb.embed(img_tm, layer, FALLBACK_PAYLOAD)
        except Exception as e:
            print(f'ERROR embed {fname}: {e}', file=sys.stderr)
            continue

        enc_mse, enc_psnr = mse_psnr(img_orig, img_combined)

        # baseline row (untransformed combined image) - decode fallback now, TM batched later
        fb_dec, fb_det, _, fb_acc = fb.decode(img_combined, layer, FALLBACK_PAYLOAD)
        row = {
            'image_id': image_id, 'filename': fname, 'transform_name': 'none',
            'intensity_value': '', 'pipeline_version': PIPELINE_VERSION,
            'encode_mse': enc_mse, 'encode_psnr': enc_psnr,
            'fb_decode_secret': fb_dec, 'fb_decode_present': str(fb_det),
            'fb_bit_accuracy': fb_acc,
            'tm_combined_baseline_present': '', 'width': w, 'height': h, 'aspect_ratio': aspect,
        }
        baseline_rows.append(row)
        baseline_jobs.append((img_combined, row))

        for tf in transforms.ALL_TRANSFORMS:
            for intensity in transforms.TRANSFORM_STEPS[tf]:
                try:
                    img_tf = transforms.apply_transform(img_combined, tf, intensity, image_id=image_id)
                except Exception as e:
                    print(f'ERROR transform {tf}={intensity} on {fname}: {e}', file=sys.stderr)
                    continue
                tw, th = img_tf.size
                t_aspect = round(tw / th if th else 0, 6)
                fb_dec, fb_det, _, fb_acc = fb.decode(img_tf, layer, FALLBACK_PAYLOAD)
                writer.writerow({
                    'image_id': image_id, 'filename': fname,
                    'transform_name': tf, 'intensity_value': str(intensity),
                    'pipeline_version': PIPELINE_VERSION,
                    'encode_mse': enc_mse, 'encode_psnr': enc_psnr,
                    'fb_decode_secret': fb_dec, 'fb_decode_present': str(fb_det),
                    'fb_bit_accuracy': fb_acc,
                    'tm_combined_baseline_present': '',
                    'width': tw, 'height': th, 'aspect_ratio': t_aspect,
                })

        if (idx + 1) % 50 == 0:
            out.flush()
            print(f'  Processed {idx + 1}/{len(image_files)} ({time.time() - t_start:.0f}s)', flush=True)

    # Batched TM decode on combined baseline images (degradation check)
    print('Decoding TrustMark on combined baselines (batched)...', flush=True)
    batch = 64
    for start in range(0, len(baseline_jobs), batch):
        jobs = baseline_jobs[start:start + batch]
        results = decode_batch_and_accuracy([job[0] for job in jobs], tm, tm_packet)
        for (_, row), result in zip(jobs, results):
            row['tm_combined_baseline_present'] = str(bool(result[1]))
            writer.writerow(row)
    out.close()

    elapsed = time.time() - t_start
    expected = (len(image_files) - len(done_images)) * (1 + sum(len(v) for v in transforms.TRANSFORM_STEPS.values()))
    print(f'Done. {len(image_files) - len(done_images)} new images -> {expected} rows in {elapsed:.0f}s', flush=True)


if __name__ == '__main__':
    main()