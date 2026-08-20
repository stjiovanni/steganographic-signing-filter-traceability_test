import os, sys, csv, math, random, argparse, time, gzip
from concurrent.futures import ProcessPoolExecutor
from glob import glob
from PIL import Image, ImageFilter, ImageEnhance
import numpy as np
import imagehash
import pdqhash
import transforms

PIPELINE_VERSION = 'v2.1-reproducible'

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


def process_image(job):
    """Process one image in a child process and return rows in stable order."""
    idx, img_path = job
    fname = os.path.basename(img_path)
    image_id = os.path.splitext(fname)[0]
    rows = []
    errors = []
    try:
        with Image.open(img_path) as source:
            img_orig = source.convert('RGB')
    except Exception as e:
        return idx, rows, [f'ERROR: Cannot open {img_path}: {e}']

    ref_hashes, _ = compute_hashes(img_orig)
    for tf in transforms.ALL_TRANSFORMS:
        for intensity in transforms.TRANSFORM_STEPS[tf]:
            try:
                img_tf = transforms.apply_transform(img_orig, tf, intensity, image_id=image_id)
                try:
                    tw, th = img_tf.size
                    t_aspect = round(tw / th if th > 0 else 0, 6)
                    tf_hashes, _ = compute_hashes(img_tf)
                finally:
                    img_tf.close()

                for hname in HASH_NAMES:
                    h_val = tf_hashes[hname]
                    h_ref = ref_hashes[hname]
                    rows.append({
                        'image_id': image_id,
                        'filename': fname,
                        'transform_name': tf,
                        'intensity_value': str(intensity),
                        'pipeline_version': PIPELINE_VERSION,
                        'hash_algorithm': hname,
                        'hash_value': h_val,
                        'hash_ref': h_ref,
                        'hamming_distance': hamming_dist(h_val, h_ref),
                        'width': tw,
                        'height': th,
                        'aspect_ratio': t_aspect,
                    })
            except Exception as e:
                errors.append(f'ERROR: {fname} / {tf}={intensity}: {e}')
    img_orig.close()
    return idx, rows, errors

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input-dir', default=transforms.COCO_DIR)
    parser.add_argument('--output-csv', default=os.path.join(OUTPUT_DIR, 'results', 'hash_robustness_results.csv'))
    parser.add_argument('--image-count', type=int, default=100)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--resume', action='store_true')
    parser.add_argument('--workers', type=int,
                        default=min(8, max(1, (os.cpu_count() or 2) - 1)))
    args = parser.parse_args()

    random.seed(args.seed)

    image_files = sorted(glob(os.path.join(args.input_dir, '*.jpg')))
    if len(image_files) == 0:
        print('ERROR: No images found in', args.input_dir, file=sys.stderr)
        sys.exit(1)
    image_files = image_files[:args.image_count]
    print(f'Found {len(image_files)} images, processing up to {args.image_count}')

    output_parent = os.path.dirname(args.output_csv)
    if output_parent:
        os.makedirs(output_parent, exist_ok=True)
    if args.workers < 1:
        parser.error('--workers must be at least 1')

    fieldnames = ['image_id', 'filename', 'transform_name', 'intensity_value',
                  'pipeline_version', 'hash_algorithm', 'hash_value', 'hash_ref',
                  'hamming_distance', 'width', 'height', 'aspect_ratio']
    done_keys = set()
    def open_csv(path, mode):
        return gzip.open(path, mode + 't', newline='') if path.endswith('.gz') else open(path, mode, newline='')

    if args.resume and os.path.exists(args.output_csv):
        with open_csv(args.output_csv, 'r') as existing:
            for row in csv.DictReader(existing):
                done_keys.add((row['image_id'], row['transform_name'],
                               row['intensity_value'], row['hash_algorithm']))
        print(f'Resume mode: {len(done_keys)} existing rows, skipping them')

    append = args.resume and os.path.exists(args.output_csv)
    f_out = open_csv(args.output_csv, 'a' if append else 'w')
    writer = csv.DictWriter(f_out, fieldnames=fieldnames)
    if not append:
        writer.writeheader()
    rows_written = 0

    t_start = time.time()
    jobs = enumerate(image_files)
    # executor.map preserves input order, so output remains byte-for-byte stable
    # (apart from gzip metadata) while CPU-heavy work runs in parallel.
    with ProcessPoolExecutor(max_workers=args.workers) as executor:
        for processed, (_, rows, errors) in enumerate(executor.map(process_image, jobs), 1):
            for error in errors:
                print(error, file=sys.stderr)
            for row in rows:
                key = (row['image_id'], row['transform_name'],
                       row['intensity_value'], row['hash_algorithm'])
                if key not in done_keys:
                    writer.writerow(row)
                    rows_written += 1

            if processed % 25 == 0:
                f_out.flush()
                elapsed = time.time() - t_start
                print(f'  Processed {processed}/{len(image_files)} images ({elapsed:.1f}s)', flush=True)

    f_out.close()
    elapsed = time.time() - t_start
    print(f'Done. {rows_written} rows written to {args.output_csv}')
    print(f'Total time: {elapsed:.1f}s')

    # Final validation printout
    with open_csv(args.output_csv, 'r') as f_check:
        reader = csv.DictReader(f_check)
        all_rows = list(reader)
        unique_images = len(set(r['image_id'] for r in all_rows))
    print(f'Validation: {len(all_rows)} total rows, {unique_images} unique image_ids written')

if __name__ == '__main__':
    main()
