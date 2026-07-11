import os, sys, csv, math, random, argparse, time
from glob import glob
from PIL import Image, ImageFilter, ImageEnhance
import numpy as np
import torch
from torchvision import transforms as tv_transforms
from trustmark import TrustMark
import transforms

PIPELINE_VERSION = 'v2.0'
TM_PAYLOAD = 'TM00001'
OUTPUT_DIR = transforms.OUTPUT_DIR

def mse_psnr(img1, img2):
    arr1 = np.asarray(img1).astype(np.int16)
    arr2 = np.asarray(img2).astype(np.int16)
    mse = np.mean(np.square(arr1 - arr2))
    if mse == 0:
        return 0.0, float('inf')
    psnr = 20 * math.log10(255.0) - 10 * math.log10(mse)
    return float(mse), float(psnr)


def encode_payload_to_packet(tm, payload):
    ecc = tm.ecc
    text_bytes = ecc.encode_text_ascii(payload)
    text_bits = ''.join(format(b, '08b') for b in text_bytes)
    packet = ecc.process_encode(text_bits)
    return np.array(packet, dtype=np.int32)


@torch.no_grad()
def decode_and_accuracy(image, tm, expected_packet):
    """Run decoder once, return (decoded_text, decode_present, decode_schema, bit_accuracy)."""
    img_rgb = image.convert('RGB')
    img_resized = img_rgb.resize((tm.model_resolution_dec, tm.model_resolution_dec), Image.BILINEAR)
    stego = tv_transforms.ToTensor()(img_resized).unsqueeze(0).to(tm.decoder.device) * 2.0 - 1.0
    raw_bits = (tm.decoder.decoder(stego) > 0).cpu().numpy()
    received = raw_bits[0].astype(np.int32)
    bit_acc = float(np.mean(expected_packet == received))
    # Now apply ECC to same raw bits
    secret_pred, detected, version = tm.ecc.decode_bitstream(raw_bits, 'text')[0]
    return secret_pred, detected, version, bit_acc


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input-dir', default=transforms.COCO_DIR)
    parser.add_argument('--output-csv', default=os.path.join(OUTPUT_DIR, 'results', 'trustmark_robustness_results.csv'))
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

    os.makedirs(os.path.join(OUTPUT_DIR, 'trustmark_watermarked'), exist_ok=True)
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

    print('Loading TrustMark model_type=Q...', flush=True)
    tm = TrustMark(verbose=False, model_type='Q', encoding_type=TrustMark.Encoding.BCH_4)
    expected_packet = encode_payload_to_packet(tm, TM_PAYLOAD)
    print(f'TrustMark model loaded. Payload encoded to {len(expected_packet)}-bit packet.', flush=True)

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
            img_wm = tm.encode(img_orig, TM_PAYLOAD)
        except Exception as e:
            print(f'ERROR: TrustMark encode failed for {fname}: {e}', file=sys.stderr)
            continue

        wm_path = os.path.join(OUTPUT_DIR, 'trustmark_watermarked', fname)
        img_wm.save(wm_path)

        enc_mse, enc_psnr = mse_psnr(img_orig, img_wm)

        # Encode row ('none' transform)
        row_key = f'{image_id}_none_'
        if row_key not in done_ids:
            try:
                secret, present, schema, ba = decode_and_accuracy(img_wm, tm, expected_packet)
            except Exception:
                secret, present, schema, ba = None, False, None, 0.0

            enc_row = {
                'image_id': image_id, 'filename': fname, 'transform_name': 'none',
                'intensity_value': '', 'pipeline_version': PIPELINE_VERSION,
                'encode_mse': enc_mse, 'encode_psnr': enc_psnr,
                'decode_secret': secret, 'decode_present': present, 'decode_schema': schema,
                'bit_accuracy': ba,
                'width': w, 'height': h, 'aspect_ratio': aspect,
                'auto_cropped': auto_cropped,
            }
            writer.writerow(enc_row)
        else:
            skipped += 1

        # Transform rows
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

                try:
                    t_secret, t_present, t_schema, t_ba = decode_and_accuracy(img_tf, tm, expected_packet)
                except Exception as e:
                    print(f'ERROR: decode after {tf}={intensity} on {fname}: {e}', file=sys.stderr)
                    t_secret, t_present, t_schema, t_ba = None, False, None, 0.0

                row = {
                    'image_id': image_id, 'filename': fname,
                    'transform_name': tf, 'intensity_value': str(intensity),
                    'pipeline_version': PIPELINE_VERSION,
                    'encode_mse': enc_mse, 'encode_psnr': enc_psnr,
                    'decode_secret': t_secret, 'decode_present': t_present,
                    'decode_schema': t_schema, 'bit_accuracy': t_ba,
                    'width': tw, 'height': th, 'aspect_ratio': t_aspect,
                    'auto_cropped': auto_cropped,
                }
                writer.writerow(row)

        if (idx + 1) % 10 == 0:
            elapsed = time.time() - t_start
            processed = idx + 1
            print(f'  Processed {processed}/{len(image_files)} images ({elapsed:.1f}s)', flush=True)

    f_out.close()
    elapsed = time.time() - t_start
    total_rows = len(image_files) * (1 + sum(len(v) for v in transforms.TRANSFORM_STEPS.values()))
    print(f'Done. {len(image_files)} images → ~{total_rows} rows written to {args.output_csv}')
    print(f'Skipped {skipped} existing rows. Total time: {elapsed:.1f}s')

if __name__ == '__main__':
    main()
