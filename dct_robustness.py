"""DCT-domain watermarking baseline — embeds in mid-frequency coefficients using differential encoding.

Embedding rule per payload bit: pick the block at row-major position i, force
coefficient pair PAIR1/PAIR2 to differ by >= EMBED_STRENGTH in the direction
encoding the bit (skip blocks that already satisfy it). Each bit owns exactly
one block, so encode/decode are implemented as batched 8x8 DCTs over the
selected blocks (vectorised; numerically equivalent to the former per-block
loop).
"""

import os, sys, csv, math, random, argparse, time
from glob import glob
from PIL import Image
import numpy as np
from scipy.fftpack import dct, idct
import transforms

PIPELINE_VERSION = 'v2.1-reproducible'
DCT_PAYLOAD = 'DCT0001'
OUTPUT_DIR = transforms.OUTPUT_DIR

EMBED_STRENGTH = 40

# Mid-frequency differential pair inside an 8x8 block:
# zigzag 4 = (1, 1), zigzag 3 = (2, 0)
PAIR1 = (1, 1)
PAIR2 = (2, 0)

BLOCK_SIZE = 8


def text_to_bits(text):
    return ''.join(format(ord(t) & 127, '07b') for t in text)


PAYLOAD_BITS = text_to_bits(DCT_PAYLOAD)
N_BITS = len(PAYLOAD_BITS)


def mse_psnr(img1, img2):
    arr1 = np.asarray(img1).astype(np.int16)
    arr2 = np.asarray(img2).astype(np.int16)
    mse = np.mean(np.square(arr1 - arr2))
    if mse == 0:
        return 0.0, float('inf')
    psnr = 20 * math.log10(255.0) - 10 * math.log10(mse)
    return float(mse), float(psnr)


def dct_2d(block):
    """2D DCT on an 8x8 block."""
    return dct(dct(block.T, norm='ortho').T, norm='ortho')


def idct_2d(block):
    """2D inverse DCT on an 8x8 block."""
    return idct(idct(block.T, norm='ortho').T, norm='ortho')


def _dct2_batch(blocks):
    """Batched 2D DCT over (N, 8, 8); identical transform order to dct_2d."""
    t = np.swapaxes(blocks, -1, -2)
    t = dct(t, norm='ortho')
    t = np.swapaxes(t, -1, -2)
    return dct(t, norm='ortho')


def _idct2_batch(blocks):
    """Batched 2D inverse DCT over (N, 8, 8); identical transform order to idct_2d."""
    t = np.swapaxes(blocks, -1, -2)
    t = idct(t, norm='ortho')
    t = np.swapaxes(t, -1, -2)
    return idct(t, norm='ortho')


def _pad_to_blocks(y_np):
    h, w = y_np.shape
    ph = ((h + BLOCK_SIZE - 1) // BLOCK_SIZE) * BLOCK_SIZE
    pw = ((w + BLOCK_SIZE - 1) // BLOCK_SIZE) * BLOCK_SIZE
    padded = np.pad(y_np, ((0, ph - h), (0, pw - w)), mode='edge')
    return padded, ph, pw


def _block_index(n_bits, n_blocks_w):
    idx = np.arange(n_bits)
    return idx // n_blocks_w, idx % n_blocks_w


def _apply_differential(D, bits_array, strength):
    """Force PAIR1/PAIR2 apart by >= strength in the bit's direction, skipping
    blocks that already satisfy the condition (matches the original loop)."""
    c1 = D[:, PAIR1[0], PAIR1[1]]
    c2 = D[:, PAIR2[0], PAIR2[1]]
    avg = (c1 + c2) / 2.0
    half = strength / 2.0
    one = bits_array == 1
    need_one = one & ~((c2 - c1) > strength)
    need_zero = (~one) & ~((c1 - c2) > strength)
    D[need_one, PAIR1[0], PAIR1[1]] = avg[need_one] + half
    D[need_one, PAIR2[0], PAIR2[1]] = avg[need_one] - half
    D[need_zero, PAIR1[0], PAIR1[1]] = avg[need_zero] - half
    D[need_zero, PAIR2[0], PAIR2[1]] = avg[need_zero] + half


def dct_encode(img, payload_bits, strength=EMBED_STRENGTH):
    """Embed payload_bits in DCT mid-frequency coefficients of Y channel."""
    img = img.convert('RGB')
    ycc = img.convert('YCbCr')
    y, cb, cr = ycc.split()
    y_np = np.asarray(y, dtype=np.float64)
    h, w = y_np.shape

    y_padded, ph, pw = _pad_to_blocks(y_np)
    n_blocks_h = ph // BLOCK_SIZE
    n_blocks_w = pw // BLOCK_SIZE
    n_blocks_total = n_blocks_h * n_blocks_w

    if n_blocks_total < len(payload_bits):
        raise ValueError(f'Not enough blocks ({n_blocks_total}) for {len(payload_bits)} bits')

    bits_array = np.array([int(b) for b in payload_bits])

    y_blocks = y_padded.reshape(n_blocks_h, BLOCK_SIZE, n_blocks_w, BLOCK_SIZE)
    y_blocks = y_blocks.transpose(0, 2, 1, 3)

    bh, bw = _block_index(N_BITS, n_blocks_w)
    selected = y_blocks[bh, bw]
    D = _dct2_batch(selected)
    _apply_differential(D, bits_array, strength)
    y_blocks[bh, bw] = _idct2_batch(D)

    y_blocks = y_blocks.transpose(0, 2, 1, 3)
    y_recon = y_blocks.reshape(ph, pw)
    y_recon = np.clip(y_recon[:h, :w], 0, 255).astype(np.uint8)

    y_out = Image.fromarray(y_recon, mode='L')
    result = Image.merge('YCbCr', (y_out, cb, cr)).convert('RGB')
    return result


def dct_decode(img, n_bits):
    """Extract payload bits from DCT mid-frequency coefficients."""
    img = img.convert('RGB')
    ycc = img.convert('YCbCr')
    y, _, _ = ycc.split()
    y_np = np.asarray(y, dtype=np.float64)

    y_padded, ph, pw = _pad_to_blocks(y_np)
    n_blocks_h = ph // BLOCK_SIZE
    n_blocks_w = pw // BLOCK_SIZE

    y_blocks = y_padded.reshape(n_blocks_h, BLOCK_SIZE, n_blocks_w, BLOCK_SIZE)
    y_blocks = y_blocks.transpose(0, 2, 1, 3)

    available = n_blocks_h * n_blocks_w
    count = min(n_bits, available)
    bh, bw = _block_index(count, n_blocks_w)
    D = _dct2_batch(y_blocks[bh, bw])
    bits_arr = D[:, PAIR1[0], PAIR1[1]] > D[:, PAIR2[0], PAIR2[1]]

    bits = ''.join('1' if b else '0' for b in bits_arr)
    # Pad with zeros if not enough blocks
    bits += '0' * (n_bits - count)
    return bits


def bit_accuracy(extracted_bits, expected_bits):
    if len(extracted_bits) != len(expected_bits):
        return 0.0
    return sum(a == b for a, b in zip(extracted_bits, expected_bits)) / len(expected_bits)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input-dir', default=transforms.COCO_DIR)
    parser.add_argument('--output-csv', default=os.path.join(OUTPUT_DIR, 'results', 'dct_robustness_results.csv'))
    parser.add_argument('--image-count', type=int, default=100)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--resume', action='store_true')
    parser.add_argument('--strength', type=float, default=EMBED_STRENGTH)
    parser.add_argument('--save-image-count', type=int, default=10)
    args = parser.parse_args()

    random.seed(args.seed)
    strength = args.strength

    image_files = sorted(glob(os.path.join(args.input_dir, '*.jpg')))
    if len(image_files) == 0:
        print('ERROR: No images found in', args.input_dir, file=sys.stderr)
        sys.exit(1)
    image_files = image_files[:args.image_count]
    print(f'Found {len(image_files)} images, processing up to {args.image_count}')

    os.makedirs(os.path.join(OUTPUT_DIR, 'dct_watermarked'), exist_ok=True)
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

        try:
            img_wm = dct_encode(img_orig, PAYLOAD_BITS, strength=strength)
        except Exception as e:
            print(f'ERROR: DCT encode failed for {fname}: {e}', file=sys.stderr)
            continue

        if idx < args.save_image_count:
            wm_path = os.path.join(OUTPUT_DIR, 'dct_watermarked', fname)
            img_wm.save(wm_path)

        enc_mse, enc_psnr = mse_psnr(img_orig, img_wm)

        row_key = f'{image_id}_none_'
        if row_key not in done_ids:
            extracted = dct_decode(img_wm, len(PAYLOAD_BITS))
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

                extracted = dct_decode(img_tf, len(PAYLOAD_BITS))
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

        if (idx + 1) % 10 == 0:
            f_out.flush()
            elapsed = time.time() - t_start
            processed = idx + 1
            print(f'  Processed {processed}/{len(image_files)} images ({elapsed:.1f}s)', flush=True)

    f_out.close()
    elapsed = time.time() - t_start
    print(f'Done. {len(image_files)} images written to {args.output_csv}')
    print(f'Skipped {skipped} existing rows. Total time: {elapsed:.1f}s')

if __name__ == '__main__':
    main()