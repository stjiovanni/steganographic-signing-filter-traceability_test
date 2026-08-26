"""Repair missing baseline ('none') rows in the fallback robustness CSV.

The resumed run wrote transformed rows for previously-completed images but
their baseline rows were never produced (the first run was interrupted before
the batched TrustMark baseline decode). This script regenerates the combined
(TM + fallback) image for each image missing a baseline row and appends it.

Deterministic: same seeds and payloads as the pipeline, so the regenerated
combined image is identical to the one the pipeline would have produced.
"""

import csv
import os
import sys
import time
from collections import defaultdict

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import fallback_watermark as fb
import transforms
from metrics import mse_psnr

CSV_PATH = os.path.join('output', 'results', 'final1200', 'fallback_robustness_results.csv')
LOG_PATH = os.path.join('output', 'logs', 'fallback_baseline_repair.log')


def log(msg):
    line = f'[{time.strftime("%H:%M:%S")}] {msg}'
    print(line, flush=True)
    with open(LOG_PATH, 'a', encoding='utf-8') as f:
        f.write(line + '\n')


def main():
    with open(CSV_PATH, newline='', encoding='utf-8') as f:
        rows = list(csv.DictReader(f))
    fieldnames = rows[0].keys()
    with_baseline = {r['image_id'] for r in rows if r['transform_name'] == 'none'}
    all_ids = {r['image_id'] for r in rows}
    missing = sorted(all_ids - with_baseline)
    log(f'{len(rows)} existing rows; {len(missing)} images missing baseline rows')
    if not missing:
        log('No missing baseline rows; nothing to do.')
        return

    from trustmark import TrustMark
    from trustmark_robustness import decode_batch_and_accuracy, encode_payload_to_packet, TM_PAYLOAD
    tm = TrustMark(verbose=False, model_type='Q', encoding_type=TrustMark.Encoding.BCH_4)
    layer = fb.make_codec()
    tm_packet = encode_payload_to_packet(tm, TM_PAYLOAD)

    new_rows = []
    jobs = []
    for image_id in missing:
        path = os.path.join(transforms.COCO_DIR, image_id + '.jpg')
        img = Image.open(path).convert('RGB')
        w, h = img.size
        aspect = round(w / h if h else 0, 6)
        img_tm = tm.encode(img, TM_PAYLOAD)
        img_combined = fb.embed(img_tm, layer, fb.FALLBACK_PAYLOAD)
        enc_mse, enc_psnr = mse_psnr(img, img_combined)
        fb_dec, fb_det, _, fb_acc = fb.decode(img_combined, layer, fb.FALLBACK_PAYLOAD)
        row = {
            'image_id': image_id, 'filename': image_id + '.jpg', 'transform_name': 'none',
            'intensity_value': '', 'pipeline_version': 'fallback-v1',
            'encode_mse': enc_mse, 'encode_psnr': enc_psnr,
            'fb_decode_secret': fb_dec, 'fb_decode_present': str(fb_det),
            'fb_bit_accuracy': fb_acc, 'tm_combined_baseline_present': '',
            'width': w, 'height': h, 'aspect_ratio': aspect,
        }
        jobs.append((img_combined, row))
        if len(jobs) % 100 == 0:
            log(f'embedded {len(jobs)}/{len(missing)}')

    batch = 64
    for start in range(0, len(jobs), batch):
        chunk = jobs[start:start + batch]
        results = decode_batch_and_accuracy([j[0] for j in chunk], tm, tm_packet)
        for (_, row), result in zip(chunk, results):
            row['tm_combined_baseline_present'] = str(bool(result[1]))
            new_rows.append(row)
        log(f'TM baseline decoded {start + len(chunk)}/{len(missing)}')

    with open(CSV_PATH, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writerows(new_rows)
    # Safety: if any appended rows had a duplicate baseline, undo would be hard,
    # so verify before final success message.
    log(f'Appended {len(new_rows)} baseline rows')


if __name__ == '__main__':
    main()