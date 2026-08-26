import sys, os
sys.path.insert(0, os.getcwd())
import importlib
import repair_fallback_baselines as m
import traceback

# Monkeypatch to a tiny subset: rebuild the CSV with only 3 missing images to test the flow
import csv
rows = list(csv.DictReader(open('output/results/final1200/fallback_robustness_results.csv', encoding='utf-8')))
fieldnames = rows[0].keys()
all_ids = {r['image_id'] for r in rows}
with_baseline = {r['image_id'] for r in rows if r['transform_name'] == 'none'}
missing = sorted(all_ids - with_baseline)[:3]

try:
    from trustmark import TrustMark
    from trustmark_robustness import decode_batch_and_accuracy, encode_payload_to_packet, TM_PAYLOAD
    import fallback_watermark as fb
    import transforms
    tm = TrustMark(verbose=False, model_type='Q', encoding_type=TrustMark.Encoding.BCH_4)
    layer = fb.make_codec()
    tm_packet = encode_payload_to_packet(tm, TM_PAYLOAD)
    for image_id in missing:
        path = os.path.join(transforms.COCO_DIR, image_id + '.jpg')
        img = __import__('PIL').Image.open(path).convert('RGB')
        img_tm = tm.encode(img, TM_PAYLOAD)
        img_combined = fb.embed(img_tm, layer, fb.FALLBACK_PAYLOAD)
        enc_mse, enc_psnr = m.mse_psnr(img, img_combined)
        fb_dec, fb_det, _, fb_acc = fb.decode(img_combined, layer, fb.FALLBACK_PAYLOAD)
        print(image_id, 'fb:', fb_det, round(fb_acc,3), 'psnr:', round(enc_psnr,2))
    jobs = []
    for image_id in missing:
        path = os.path.join(transforms.COCO_DIR, image_id + '.jpg')
        img = __import__('PIL').Image.open(path).convert('RGB')
        img_tm = tm.encode(img, TM_PAYLOAD)
        img_combined = fb.embed(img_tm, layer, fb.FALLBACK_PAYLOAD)
        jobs.append((img_combined, {'image_id': image_id}))
    results = decode_batch_and_accuracy([j[0] for j in jobs], tm, tm_packet)
    for j, r in zip(jobs, results):
        print('TM combined:', j[1]['image_id'], 'present=', bool(r[1]))
    print('3-image repair flow OK')
except Exception:
    traceback.print_exc()