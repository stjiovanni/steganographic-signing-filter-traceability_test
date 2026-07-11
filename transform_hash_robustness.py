import os, sys, csv, math, random, argparse, time
from glob import glob
from PIL import Image, ImageFilter, ImageEnhance
import numpy as np
import imagehash
import pdqhash
import transforms

PIPELINE_VERSION = 'v2.0'

OUTPUT_DIR = transforms.OUTPUT_DIR

def compute_hashes(img):
    img_rgb = img.convert('RGB')
    ph = imagehash.phash(img_rgb)
    dh = imagehash.dhash(img_rgb)
    ah = imagehash.average_hash(img_rgb)
    wh = imagehash.whash(img_rgb, mode='haar')
    coh = imagehash.colorhash(img_rgb)
    dhv = imagehash.dhash_vertical(img_rgb)
    phs = imagehash.phash_simple(img_rgb)
    arr = np.asarray(img_rgb)
    pdq_vec, pdq_q = pdqhash.compute(arr)
    pdq_bin = ''.join(str(int(x)) for x in pdq_vec)
    return {
        'phash': str(ph),
        'dhash': str(dh),
        'ahash': str(ah),
        'whash': str(wh),
        'colorhash': str(coh),
        'dhash_vertical': str(dhv),
        'phash_simple': str(phs),
        'pdq': pdq_bin,
    }, {
        'pdq': int(pdq_q),
    }

HASH_NAMES = ['phash', 'dhash', 'ahash', 'whash', 'colorhash', 'dhash_vertical', 'phash_simple', 'pdq']

def hamming_dist(a, b):
    if len(a) != len(b):
        return -1
    return sum(c1 != c2 for c1, c2 in zip(a, b))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input-dir', default=transforms.COCO_DIR)
    parser.add_argument('--output-csv', default=os.path.join(OUTPUT_DIR, 'results', 'hash_robustness_results.csv'))
    parser.add_argument('--image-count', type=int, default=100)
    parser.add_argument('--seed', type=int, default=42)
    args = parser.parse_args()

    random.seed(args.seed)

    image_files = sorted(glob(os.path.join(args.input_dir, '*.jpg')))
    if len(image_files) == 0:
        print('ERROR: No images found in', args.input_dir, file=sys.stderr)
        sys.exit(1)
    image_files = image_files[:args.image_count]
    print(f'Found {len(image_files)} images, processing up to {args.image_count}')

    os.makedirs(os.path.dirname(args.output_csv), exist_ok=True)

    fieldnames = ['image_id', 'filename', 'transform_name', 'intensity_value',
                  'pipeline_version', 'hash_algorithm', 'hash_value', 'hash_ref',
                  'hamming_distance', 'width', 'height', 'aspect_ratio']
    f_out = open(args.output_csv, 'w', newline='')
    writer = csv.DictWriter(f_out, fieldnames=fieldnames)
    writer.writeheader()

    t_start = time.time()
    for idx, img_path in enumerate(image_files):
        fname = os.path.basename(img_path)
        image_id = os.path.splitext(fname)[0]
        try:
            img_orig = Image.open(img_path).convert('RGB')
        except Exception as e:
            print(f'ERROR: Cannot open {img_path}: {e}', file=sys.stderr)
            continue

        # Compute reference hashes once per image
        ref_hashes, ref_quality = compute_hashes(img_orig)

        for tf in transforms.ALL_TRANSFORMS:
            steps = transforms.TRANSFORM_STEPS[tf]
            for intensity in steps:
                try:
                    img_tf = transforms.apply_transform(img_orig, tf, intensity, image_id=image_id)
                    tw, th = img_tf.size
                    t_aspect = round(tw / th if th > 0 else 0, 6)

                    tf_hashes, _ = compute_hashes(img_tf)

                    for hname in HASH_NAMES:
                        h_val = tf_hashes[hname]
                        h_ref = ref_hashes[hname]
                        dist = hamming_dist(h_val, h_ref)

                        row = {
                            'image_id': image_id,
                            'filename': fname,
                            'transform_name': tf,
                            'intensity_value': str(intensity),
                            'pipeline_version': PIPELINE_VERSION,
                            'hash_algorithm': hname,
                            'hash_value': h_val,
                            'hash_ref': h_ref,
                            'hamming_distance': dist,
                            'width': tw,
                            'height': th,
                            'aspect_ratio': t_aspect,
                        }
                        writer.writerow(row)
                except Exception as e:
                    print(f'ERROR: {fname} / {tf}={intensity}: {e}', file=sys.stderr)
                    continue

        if (idx + 1) % 25 == 0:
            elapsed = time.time() - t_start
            print(f'  Processed {idx+1}/{len(image_files)} images ({elapsed:.1f}s)', flush=True)

    f_out.close()
    elapsed = time.time() - t_start
    print(f'Done. {len(image_files)} images written to {args.output_csv}')
    print(f'Total time: {elapsed:.1f}s')

if __name__ == '__main__':
    main()
