"""LSB embedding baseline — structurally parallel to trustmark_robustness.py."""

import os, sys, csv, math, random, argparse, time
from glob import glob
from PIL import Image
import numpy as np
import transforms

PIPELINE_VERSION = 'v2.0'
LSB_PAYLOAD = 'LSB0001'
OUTPUT_DIR = transforms.OUTPUT_DIR


def text_to_bits(text):
    """7-bit ASCII to bitstring (same scheme as TrustMark encode_text_ascii)."""
    return ''.join(format(ord(t) & 127, '07b') for t in text)


PAYLOAD_BITS = text_to_bits(LSB_PAYLOAD)  # 49 bits


def mse_psnr(img1, img2):
    arr1 = np.asarray(img1).astype(np.int16)
    arr2 = np.asarray(img2).astype(np.int16)
    mse = np.mean(np.square(arr1 - arr2))
    if mse == 0:
        return 0.0, float('inf')
    psnr = 20 * math.log10(255.0) - 10 * math.log10(mse)
    return float(mse), float(psnr)


def lsb_encode(img, payload_bits):
    """Embed payload_bits into LSBs of first N pixels (row-major, R→G→B)."""
    arr = np.asarray(img).copy()
    h, w, c = arr.shape
    n_bits = len(payload_bits)
    flat = arr.reshape(-1)
    if len(flat) < n_bits:
        raise ValueError(f'Image too small: {len(flat)} channels, need {n_bits}')
    for i, bit in enumerate(payload_bits):
        flat[i] = (flat[i] & 0xFE) | int(bit)
    return Image.fromarray(flat.reshape(h, w, c))


def lsb_decode(img, n_bits):
    """Extract LSBs from first N pixels."""
    arr = np.asarray(img)
    flat = arr.reshape(-1)
    bits = ''.join(str(flat[i] & 1) for i in range(n_bits))
    return bits


def bit_accuracy(extracted_bits, expected_bits):
    if len(extracted_bits) != len(expected_bits):
        return 0.0
    return sum(a == b for a, b in zip(extracted_bits, expected_bits)) / len(expected_bits)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input-dir', default=transforms.COCO_DIR)
    parser.add_argument('--output-csv', default=os.path.join(OUTPUT_DIR, 'results', 'lsb_robustness_results.csv'))
    parser.add_argument('--image-count', type=int, default=100)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--resume', action='store_true')
    args = parser.parse_args()

    random.seed(args.seed)

    image_files = sorted(glob(os.path.join(args.input_dir, '*.jpg')))
    if len(image_files) == 0:
        print('ERROR: No images found in', args.input_dir, file=sys.stderr)
        sys.exit(1)
    image_files = image_files[:args.image_count]
    print(f'Found {len(image_files)} images, processing up to {args.image_count}')

    os.makedirs(os.path.join(OUTPUT_DIR, 'lsb_watermarked'), exist_ok=True)
    os.makedirs(os.path.dirname(args.output_csv), exist_ok=True)

    done_ids = set()
    if args.resume and os.path.exists(args.output_csv):
        with open(args.output_csv, 'r', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                done_ids.add(f"{row['image_id']}_{row['transform_name']}_{row['intensity_value']}")
        print(f'Resume mode: {len(done_ids)} existing rows, skipping them')

    fieldnames = ['image_id', 'filename', 'transform_name', 'intensity_value',
                  'pipeline_version', 'encode_mse', 'encode_psnr',
                  'decode_secret', 'decode_present', 'decode_schema', 'bit_accuracy',
                  'width', 'height', 'aspect_ratio', 'auto_cropped']
    f_out = open(args.output_csv, 'a', newline='') if args.resume and os.path.exists(args.output_csv) else open(args.output_csv, 'w', newline='')
    writer = csv.DictWriter(f_out, fieldnames=fieldnames)
    if not (args.resume and os.path.exists(args.output_csv)):
        writer.writeheader()

    t_start = time.time()
    skipped = 0
    for idx, img_path in enumerate(image_files):
        fname = os.path.basename(img_path)
        image_id = os.path.splitext(fname)[0]

        try:
            img_orig = Image.open(img_path).convert('RGB')
        except Exception as e:
            print(f'ERROR: Cannot open {img_path}: {e}', file=sys.stderr)
            continue

        w, h = img_orig.size
        aspect = round(w / h if h > 0 else 0, 6)
        aspect_ratio_val = w / h if h > 0 else float('inf')
        auto_cropped = aspect_ratio_val > 2.0 or aspect_ratio_val < 0.5

        # Encode
        try:
            img_wm = lsb_encode(img_orig, PAYLOAD_BITS)
        except Exception as e:
            print(f'ERROR: LSB encode failed for {fname}: {e}', file=sys.stderr)
            continue

        wm_path = os.path.join(OUTPUT_DIR, 'lsb_watermarked', fname)
        img_wm.save(wm_path)

        enc_mse, enc_psnr = mse_psnr(img_orig, img_wm)

        row_key = f'{image_id}_none_'
        if row_key not in done_ids:
            extracted = lsb_decode(img_wm, len(PAYLOAD_BITS))
            present = extracted == PAYLOAD_BITS
            ba = bit_accuracy(extracted, PAYLOAD_BITS)

            enc_row = {
                'image_id': image_id, 'filename': fname, 'transform_name': 'none',
                'intensity_value': '', 'pipeline_version': PIPELINE_VERSION,
                'encode_mse': enc_mse, 'encode_psnr': enc_psnr,
                'decode_secret': extracted, 'decode_present': present,
                'decode_schema': None, 'bit_accuracy': ba,
                'width': w, 'height': h, 'aspect_ratio': aspect,
                'auto_cropped': auto_cropped,
            }
            writer.writerow(enc_row)
        else:
            skipped += 1

        for tf in transforms.ALL_TRANSFORMS:
            steps = transforms.TRANSFORM_STEPS[tf]
            for intensity in steps:
                row_key = f'{image_id}_{tf}_{intensity}'
                if row_key in done_ids:
                    skipped += 1
                    continue

                try:
                    img_tf = transforms.apply_transform(img_wm, tf, intensity, image_id=image_id)
                except Exception as e:
                    print(f'ERROR: transform {tf}={intensity} on {fname}: {e}', file=sys.stderr)
                    continue

                tw, th = img_tf.size
                t_aspect = round(tw / th if th > 0 else 0, 6)

                extracted = lsb_decode(img_tf, len(PAYLOAD_BITS))
                present = extracted == PAYLOAD_BITS
                ba = bit_accuracy(extracted, PAYLOAD_BITS)

                row = {
                    'image_id': image_id, 'filename': fname,
                    'transform_name': tf, 'intensity_value': str(intensity),
                    'pipeline_version': PIPELINE_VERSION,
                    'encode_mse': enc_mse, 'encode_psnr': enc_psnr,
                    'decode_secret': extracted, 'decode_present': present,
                    'decode_schema': None, 'bit_accuracy': ba,
                    'width': tw, 'height': th, 'aspect_ratio': t_aspect,
                    'auto_cropped': auto_cropped,
                }
                writer.writerow(row)

        if (idx + 1) % 25 == 0:
            elapsed = time.time() - t_start
            processed = idx + 1
            print(f'  Processed {processed}/{len(image_files)} images ({elapsed:.1f}s)', flush=True)

    f_out.close()
    elapsed = time.time() - t_start
    print(f'Done. {len(image_files)} images written to {args.output_csv}')
    print(f'Skipped {skipped} existing rows. Total time: {elapsed:.1f}s')

if __name__ == '__main__':
    main()
