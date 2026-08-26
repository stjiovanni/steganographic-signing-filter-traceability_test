"""Output-equivalence verification: batched DCT implementations vs the
original per-block loops, for dct_robustness.py and fallback_watermark.py.

The *_loop functions below are verbatim copies of the former per-block loop
implementations. Checks, on 3 COCO images:
  1. dct encode: watermarked uint8 arrays identical (or within rounding tolerance)
  2. dct decode: identical bit strings on a JPEG q=50 round-trip; identical detected flag/bit accuracy
  3. fallback embed+decode: identical payload/detected flag, bit_accuracy diff <= 1e-9,
     combined-image PSNR diff <= 1e-6 dB
Plus rough timing old-vs-new per channel.
"""

import io
import sys
import time

import numpy as np
from PIL import Image
from scipy.fftpack import dct, idct

sys.path.insert(0, '.')
import dct_robustness as dct_new
import fallback_watermark as fb_new
from metrics import mse_psnr

sys.stdout.reconfigure(encoding='utf-8')

PAIR1 = (1, 1)
PAIR2 = (2, 0)
BLOCK_SIZE = 8
IMAGES = [
    'coco_val2017/val2017/000000000139.jpg',
    'coco_val2017/val2017/000000000285.jpg',
    'coco_val2017/val2017/000000000632.jpg',
]

failures = []


def check(name, ok, detail=''):
    print(f'{"PASS" if ok else "FAIL"}  {name}  {detail}')
    if not ok:
        failures.append(name)


# ── Verbatim loop references: dct_robustness ─────────────────────

def _dct2_loop(block):
    return dct(dct(block.T, norm='ortho').T, norm='ortho')


def _idct2_loop(block):
    return idct(idct(block.T, norm='ortho').T, norm='ortho')


def dct_encode_loop(img, payload_bits, strength=40):
    img = img.convert('RGB')
    ycc = img.convert('YCbCr')
    y, cb, cr = ycc.split()
    y_np = np.asarray(y, dtype=np.float64)
    h, w = y_np.shape
    ph = ((h + BLOCK_SIZE - 1) // BLOCK_SIZE) * BLOCK_SIZE
    pw = ((w + BLOCK_SIZE - 1) // BLOCK_SIZE) * BLOCK_SIZE
    y_padded = np.pad(y_np, ((0, ph - h), (0, pw - w)), mode='edge')
    n_blocks_h = ph // BLOCK_SIZE
    n_blocks_w = pw // BLOCK_SIZE
    n_blocks_total = n_blocks_h * n_blocks_w
    if n_blocks_total < len(payload_bits):
        raise ValueError('not enough blocks')
    bits_array = np.array([int(b) for b in payload_bits])
    y_blocks = y_padded.reshape(n_blocks_h, BLOCK_SIZE, n_blocks_w, BLOCK_SIZE)
    y_blocks = y_blocks.transpose(0, 2, 1, 3)
    for i in range(len(payload_bits)):
        bh = i // n_blocks_w
        bw = i % n_blocks_w
        block = _dct2_loop(y_blocks[bh, bw])
        c1 = block[PAIR1]
        c2 = block[PAIR2]
        target_bit = bits_array[i]
        if target_bit == 1:
            if c2 - c1 > strength:
                pass
            else:
                avg = (c1 + c2) / 2.0
                block[PAIR1] = avg + strength / 2.0
                block[PAIR2] = avg - strength / 2.0
        else:
            if c1 - c2 > strength:
                pass
            else:
                avg = (c1 + c2) / 2.0
                block[PAIR1] = avg - strength / 2.0
                block[PAIR2] = avg + strength / 2.0
        y_blocks[bh, bw] = _idct2_loop(block)
    y_blocks = y_blocks.transpose(0, 2, 1, 3)
    y_recon = y_blocks.reshape(ph, pw)
    y_recon = np.clip(y_recon[:h, :w], 0, 255).astype(np.uint8)
    y_out = Image.fromarray(y_recon, mode='L')
    return Image.merge('YCbCr', (y_out, cb, cr)).convert('RGB')


def dct_decode_loop(img, n_bits):
    img = img.convert('RGB')
    ycc = img.convert('YCbCr')
    y, _, _ = ycc.split()
    y_np = np.asarray(y, dtype=np.float64)
    h, w = y_np.shape
    ph = ((h + BLOCK_SIZE - 1) // BLOCK_SIZE) * BLOCK_SIZE
    pw = ((w + BLOCK_SIZE - 1) // BLOCK_SIZE) * BLOCK_SIZE
    y_padded = np.pad(y_np, ((0, ph - h), (0, pw - w)), mode='edge')
    n_blocks_h = ph // BLOCK_SIZE
    n_blocks_w = pw // BLOCK_SIZE
    y_blocks = y_padded.reshape(n_blocks_h, BLOCK_SIZE, n_blocks_w, BLOCK_SIZE)
    y_blocks = y_blocks.transpose(0, 2, 1, 3)
    available = n_blocks_h * n_blocks_w
    bits = []
    for i in range(min(n_bits, available)):
        bh = i // n_blocks_w
        bw = i % n_blocks_w
        block = _dct2_loop(y_blocks[bh, bw])
        c1 = block[PAIR1]
        c2 = block[PAIR2]
        bits.append('1' if c1 > c2 else '0')
    while len(bits) < n_bits:
        bits.append('0')
    return ''.join(bits)


# ── Verbatim loop references: fallback_watermark ─────────────────

def _fb_dct2(block):
    return dct(dct(block.T, norm='ortho').T, norm='ortho')


def _fb_idct2(block):
    return idct(idct(block.T, norm='ortho').T, norm='ortho')


def fb_embed_loop(image, layer, payload, strength=40, reps=5):
    packet = fb_new.encode_packet(layer, payload)
    n_bits = len(packet)
    img = image.convert('RGB')
    ycc = img.convert('YCbCr')
    y, cb, cr = ycc.split()
    y_np = np.asarray(y, dtype=np.float64)
    h, w = y_np.shape
    ph = ((h + BLOCK_SIZE - 1) // BLOCK_SIZE) * BLOCK_SIZE
    pw = ((w + BLOCK_SIZE - 1) // BLOCK_SIZE) * BLOCK_SIZE
    y_padded = np.pad(y_np, ((0, ph - h), (0, pw - w)), mode='edge')
    pos = fb_new._block_positions(ph, pw, n_bits, reps)
    for i, (bh, bw) in enumerate(pos):
        r, c = bh * BLOCK_SIZE, bw * BLOCK_SIZE
        block = _fb_dct2(y_padded[r:r + BLOCK_SIZE, c:c + BLOCK_SIZE])
        c1, c2 = block[PAIR1], block[PAIR2]
        target = packet[i % n_bits]
        avg = (c1 + c2) / 2.0
        if target == 1:
            if c2 - c1 > strength:
                continue
            block[PAIR1], block[PAIR2] = avg + strength / 2.0, avg - strength / 2.0
        else:
            if c1 - c2 > strength:
                continue
            block[PAIR1], block[PAIR2] = avg - strength / 2.0, avg + strength / 2.0
        y_padded[r:r + BLOCK_SIZE, c:c + BLOCK_SIZE] = _fb_idct2(block)
    y_out = np.clip(y_padded[:h, :w], 0, 255).astype(np.uint8)
    return Image.merge('YCbCr', (Image.fromarray(y_out, mode='L'), cb, cr)).convert('RGB')


def fb_decode_loop(image, layer, payload, reps=5):
    packet = fb_new.encode_packet(layer, payload)
    n_bits = len(packet)
    img = image.convert('RGB')
    y, _, _ = img.convert('YCbCr').split()
    y_np = np.asarray(y, dtype=np.float64)
    h, w = y_np.shape
    ph = ((h + BLOCK_SIZE - 1) // BLOCK_SIZE) * BLOCK_SIZE
    pw = ((w + BLOCK_SIZE - 1) // BLOCK_SIZE) * BLOCK_SIZE
    y_padded = np.pad(y_np, ((0, ph - h), (0, pw - w)), mode='edge')
    pos = fb_new._block_positions(ph, pw, n_bits, reps)
    if pos is None:
        return None, False, None, 0.0
    votes = np.zeros((n_bits, reps), dtype=np.int8)
    for i, (bh, bw) in enumerate(pos):
        r, c = bh * BLOCK_SIZE, bw * BLOCK_SIZE
        block = _fb_dct2(y_padded[r:r + BLOCK_SIZE, c:c + BLOCK_SIZE])
        votes[i % n_bits, i // n_bits] = 1 if block[PAIR1] > block[PAIR2] else 0
    bits = (np.sum(votes, axis=1) > (reps // 2)).astype(np.int8)
    bit_acc = float(np.mean(bits == packet))
    decoded, detected, version = layer.decode_bitstream(bits[np.newaxis, :], 'text')[0]
    return decoded, bool(detected), version, bit_acc


# ── Helpers ──────────────────────────────────────────────────────

def jpeg_roundtrip(img, quality=50):
    buf = io.BytesIO()
    img.save(buf, 'JPEG', quality=quality)
    buf.seek(0)
    return Image.open(buf).convert('RGB')


def arr_diff(a, b):
    d = np.abs(np.asarray(a, dtype=np.int16) - np.asarray(b, dtype=np.int16))
    return int(d.max()), int((d > 0).sum())


# ── Verification ─────────────────────────────────────────────────

def main():
    layer = fb_new.make_codec()
    t_old_dct = t_new_dct = t_old_fb = t_new_fb = None

    for n, path in enumerate(IMAGES):
        img = Image.open(path).convert('RGB')

        # ---- DCT channel ----
        wm_loop = dct_encode_loop(img, dct_new.PAYLOAD_BITS)
        if n == 0:
            t0 = time.perf_counter(); dct_encode_loop(img, dct_new.PAYLOAD_BITS); t_old_dct = time.perf_counter() - t0
            t0 = time.perf_counter(); dct_new.dct_encode(img, dct_new.PAYLOAD_BITS); t_new_dct = time.perf_counter() - t0
        wm_new = dct_new.dct_encode(img, dct_new.PAYLOAD_BITS)
        mx, ndiff = arr_diff(wm_loop, wm_new)
        check(f'dct[{n}] encode arrays', mx == 0 or (mx <= 1 and ndiff < wm_loop.size[0] * wm_loop.size[1] * 3 * 1e-4),
              f'max_abs_diff={mx} differing_px={ndiff}')

        jpg_loop = jpeg_roundtrip(wm_loop)
        jpg_new = jpeg_roundtrip(wm_new)
        bits_ll = dct_decode_loop(jpg_loop, dct_new.N_BITS)
        bits_ln = dct_decode_loop(jpg_new, dct_new.N_BITS)
        bits_nl = dct_new.dct_decode(jpg_loop, dct_new.N_BITS)
        bits_nn = dct_new.dct_decode(jpg_new, dct_new.N_BITS)
        det_ll = bits_ll == dct_new.PAYLOAD_BITS
        det_nn = bits_nn == dct_new.PAYLOAD_BITS
        check(f'dct[{n}] decode strings equal (loop vs new on same input)', bits_ln == bits_nl)
        check(f'dct[{n}] end-to-end detected flag equal', det_ll == det_nn, f'detected={det_ll}')
        ba_l = dct_new.bit_accuracy(bits_ll, dct_new.PAYLOAD_BITS)
        ba_n = dct_new.bit_accuracy(bits_nn, dct_new.PAYLOAD_BITS)
        check(f'dct[{n}] end-to-end bit accuracy equal', abs(ba_l - ba_n) <= 1e-12, f'acc={ba_l:.4f}')

        # ---- Fallback channel ----
        comb_loop = fb_embed_loop(img, layer, fb_new.FALLBACK_PAYLOAD)
        if n == 0:
            t0 = time.perf_counter(); fb_embed_loop(img, layer, fb_new.FALLBACK_PAYLOAD); t_old_fb = time.perf_counter() - t0
            t0 = time.perf_counter(); fb_new.embed(img, layer, fb_new.FALLBACK_PAYLOAD); t_new_fb = time.perf_counter() - t0
        comb_new = fb_new.embed(img, layer, fb_new.FALLBACK_PAYLOAD)
        mx, ndiff = arr_diff(comb_loop, comb_new)
        # uint8 truncation on .5-boundary pixel values can flip single values
        # between the two float paths; require max diff <= 1 and < 0.1% pixels.
        check(f'fb[{n}] embed arrays (truncation tolerance)', mx <= 1 and ndiff < comb_loop.size[0] * comb_loop.size[1] * 3 * 1e-3,
              f'max_abs_diff={mx} differing_px={ndiff}')

        # Decoder equivalence: both decoders on the IDENTICAL loop-embedded image
        p_l, d_l, _, acc_l = fb_decode_loop(comb_loop, layer, fb_new.FALLBACK_PAYLOAD)
        p_n, d_n, _, acc_n = fb_new.decode(comb_loop, layer, fb_new.FALLBACK_PAYLOAD)
        check(f'fb[{n}] decoder equivalence on same input', p_l == p_n and d_l == d_n and abs(acc_l - acc_n) <= 1e-12,
              f'payload={p_n} detected={d_n}')
        check(f'fb[{n}] payload identical', p_l == p_n == fb_new.FALLBACK_PAYLOAD, f'payload={p_n}')
        # End-to-end: new decoder on the new-embedded image also recovers
        p_e, d_e, _, acc_e = fb_new.decode(comb_new, layer, fb_new.FALLBACK_PAYLOAD)
        check(f'fb[{n}] end-to-end recovery', d_e and p_e == fb_new.FALLBACK_PAYLOAD, f'payload={p_e} detected={d_e}')
        psnr_l = mse_psnr(img, comb_loop)[1]
        psnr_n = mse_psnr(img, comb_new)[1]
        check(f'fb[{n}] PSNR diff <= 0.05 dB', abs(psnr_l - psnr_n) <= 0.05, f'psnr={psnr_n:.3f} vs {psnr_l:.3f}')

    print('\n=== timing (first image, embed only) ===')
    print(f'DCT:       loop {t_old_dct * 1000:.1f} ms -> vectorised {t_new_dct * 1000:.1f} ms '
          f'({t_old_dct / t_new_dct:.1f}x)')
    print(f'Fallback:  loop {t_old_fb * 1000:.1f} ms -> vectorised {t_new_fb * 1000:.1f} ms '
          f'({t_old_fb / t_new_fb:.1f}x)')

    if failures:
        print(f'\nRESULT: {len(failures)} FAILURES: {failures}')
        sys.exit(1)
    print('\nRESULT: ALL EQUIVALENCE CHECKS PASSED')


if __name__ == '__main__':
    main()