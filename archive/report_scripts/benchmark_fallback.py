"""Benchmark the fallback watermark: speed, imperceptibility, and combined
embedding with TrustMark (does TrustMark still decode after layering?)."""

import os
import sys
import time
from glob import glob

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import fallback_watermark as fb
from trustmark import TrustMark
from trustmark_robustness import encode_payload_to_packet, TM_PAYLOAD
from dct_robustness import mse_psnr

sys.stdout.reconfigure(encoding='utf-8')

files = sorted(glob('coco_val2017/val2017/*.jpg'))[:6]
tm = TrustMark(verbose=False, model_type='Q', encoding_type=TrustMark.Encoding.BCH_4)
layer = fb.make_codec()
expected_packet = encode_payload_to_packet(tm, TM_PAYLOAD)

t_embed = []
t_decode = []
psnrs = []
tm_alone = 0
tm_combined = 0

for f in files:
    img = Image.open(f).convert('RGB')

    t0 = time.perf_counter()
    tm_img = tm.encode(img, TM_PAYLOAD)
    combined = fb.embed(tm_img, layer, fb.FALLBACK_PAYLOAD)
    t_embed.append(time.perf_counter() - t0)

    psnrs.append(mse_psnr(img, combined)[1])

    # TM decode on TM-only vs combined
    def tm_present(im):
        from trustmark_robustness import decode_and_accuracy
        return decode_and_accuracy(im, tm, expected_packet)[1]

    tm_alone += tm_present(tm_img)
    tm_combined += tm_present(combined)

    # fallback decode on combined (untransformed)
    t0 = time.perf_counter()
    decoded, detected, version, acc = fb.decode(combined, layer, fb.FALLBACK_PAYLOAD)
    t_decode.append(time.perf_counter() - t0)

print(f'images={len(files)}')
print(f'embed (TM+fallback) mean: {np.mean(t_embed):.3f}s')
print(f'fallback decode mean:     {np.mean(t_decode):.3f}s')
print(f'combined PSNR mean:       {np.mean(psnrs):.1f} dB')
print(f'TM decode-present alone:     {tm_alone}/{len(files)}')
print(f'TM decode-present combined:  {tm_combined}/{len(files)}')
print(f'fallback clean decode:       {sum(1 for f in files) * 0 + (tm_combined > 0)} check below')
for f in files:
    img = Image.open(f).convert('RGB')
    tm_img = tm.encode(img, TM_PAYLOAD)
    combined = fb.embed(tm_img, layer, fb.FALLBACK_PAYLOAD)
    d, det, v, acc = fb.decode(combined, layer, fb.FALLBACK_PAYLOAD)
    print('  fallback:', d, 'detected=', det, 'bit_acc=', round(acc, 4))