"""Fallback watermark channel for the two-layer payload-recovery experiment.

Mareen et al. (2021) style: a short payload is BCH_SUPER-coded (TrustMark
DataLayer) into a fixed 100-bit packet, embedded in the DCT domain with
repetition and interleaved block placement, decoded by majority vote before
BCH correction. The perceptual hash stays a separate similarity screen and
never carries a payload.

Embed/decode are batched: all carrier blocks are DCT-transformed in a single
vectorised call (each slot touches exactly one disjoint 8x8 block, so batching
is equivalent to the former per-slot loop).
"""

import numpy as np
from PIL import Image
from scipy.fftpack import dct, idct

FALLBACK_PAYLOAD = 'FB01'
REPETITIONS = 5
STRENGTH = 40
BLOCK_SIZE = 8
PAIR1 = (1, 1)   # zigzag 4
PAIR2 = (2, 0)   # zigzag 3


def make_codec():
    from trustmark import TrustMark
    from trustmark.datalayer import DataLayer
    return DataLayer(100, verbose=False, encoding_mode=TrustMark.Encoding.BCH_SUPER)


def encode_packet(layer, payload):
    text_bytes = layer.encode_text_ascii(payload)
    bits = ''.join(format(b, '08b') for b in text_bytes)
    packet = layer.process_encode(bits)
    return np.asarray(packet, dtype=np.int32)


def _dct2(block):
    return dct(dct(block.T, norm='ortho').T, norm='ortho')


def _idct2(block):
    return idct(idct(block.T, norm='ortho').T, norm='ortho')


def _dct2_batch(blocks):
    """Batched 2D DCT over (N, 8, 8); identical transform order to _dct2."""
    t = np.swapaxes(blocks, -1, -2)
    t = dct(t, norm='ortho')
    t = np.swapaxes(t, -1, -2)
    return dct(t, norm='ortho')


def _idct2_batch(blocks):
    """Batched 2D inverse DCT over (N, 8, 8); identical transform order to _idct2."""
    t = np.swapaxes(blocks, -1, -2)
    t = idct(t, norm='ortho')
    t = np.swapaxes(t, -1, -2)
    return idct(t, norm='ortho')


def _block_positions(h, w, n_bits, reps):
    """Evenly spread each bit's repeats across the whole image so partial
    crops destroy at most a fraction of the repeats. Returns None if the
    image is too small to hold the slot count (embed layout defined on the
    full-size image; dimension-changing transforms therefore decode as a
    clean failure rather than with a mismatched layout)."""
    total_blocks = (h // BLOCK_SIZE) * (w // BLOCK_SIZE)
    per_bit = total_blocks // (n_bits * reps)
    if per_bit < 1:
        return None
    positions = []
    for bit in range(n_bits):
        for rep in range(reps):
            flat = (bit * reps + rep) * per_bit
            positions.append((flat // (w // BLOCK_SIZE), (flat % (w // BLOCK_SIZE))))
    return positions


def _slot_windows(y_padded, pos):
    """Gather the 8x8 blocks at the slot positions as one (M, 8, 8) array.
    Returns the selection plus the (M, 8) row/column index grids used to
    scatter modified blocks back."""
    arr = np.asarray(pos)
    rows = arr[:, 0] * BLOCK_SIZE
    cols = arr[:, 1] * BLOCK_SIZE
    rr = rows[:, None] + np.arange(BLOCK_SIZE)[None, :]
    cc = cols[:, None] + np.arange(BLOCK_SIZE)[None, :]
    sel = y_padded[rr[:, :, None], cc[:, None, :]]
    return sel, rr, cc


def _apply_differential(D, targets, strength):
    c1 = D[:, PAIR1[0], PAIR1[1]]
    c2 = D[:, PAIR2[0], PAIR2[1]]
    avg = (c1 + c2) / 2.0
    half = strength / 2.0
    one = targets == 1
    need_one = one & ~((c2 - c1) > strength)
    need_zero = (~one) & ~((c1 - c2) > strength)
    D[need_one, PAIR1[0], PAIR1[1]] = avg[need_one] + half
    D[need_one, PAIR2[0], PAIR2[1]] = avg[need_one] - half
    D[need_zero, PAIR1[0], PAIR1[1]] = avg[need_zero] - half
    D[need_zero, PAIR2[0], PAIR2[1]] = avg[need_zero] + half


def embed(image, layer, payload=FALLBACK_PAYLOAD, strength=STRENGTH, reps=REPETITIONS):
    packet = encode_packet(layer, payload)
    n_bits = len(packet)
    img = image.convert('RGB')
    ycc = img.convert('YCbCr')
    y, cb, cr = ycc.split()
    y_np = np.asarray(y, dtype=np.float64)
    h, w = y_np.shape
    ph = ((h + BLOCK_SIZE - 1) // BLOCK_SIZE) * BLOCK_SIZE
    pw = ((w + BLOCK_SIZE - 1) // BLOCK_SIZE) * BLOCK_SIZE
    y_padded = np.pad(y_np, ((0, ph - h), (0, pw - w)), mode='edge')
    pos = _block_positions(ph, pw, n_bits, reps)
    if pos is None:
        raise ValueError('image too small for fallback slot layout')

    sel, rr, cc = _slot_windows(y_padded, pos)
    D = _dct2_batch(sel)
    targets = packet[np.arange(len(pos)) % n_bits]
    _apply_differential(D, targets, strength)
    y_padded[rr[:, :, None], cc[:, None, :]] = _idct2_batch(D)

    y_out = np.clip(y_padded[:h, :w], 0, 255).astype(np.uint8)
    result = Image.merge('YCbCr', (Image.fromarray(y_out, mode='L'), cb, cr)).convert('RGB')
    return result


def decode(image, layer, payload=FALLBACK_PAYLOAD, reps=REPETITIONS):
    packet = encode_packet(layer, payload)
    n_bits = len(packet)
    img = image.convert('RGB')
    y, _, _ = img.convert('YCbCr').split()
    y_np = np.asarray(y, dtype=np.float64)
    h, w = y_np.shape
    ph = ((h + BLOCK_SIZE - 1) // BLOCK_SIZE) * BLOCK_SIZE
    pw = ((w + BLOCK_SIZE - 1) // BLOCK_SIZE) * BLOCK_SIZE
    y_padded = np.pad(y_np, ((0, ph - h), (0, pw - w)), mode='edge')
    pos = _block_positions(ph, pw, n_bits, reps)
    if pos is None:
        return None, False, None, 0.0

    sel, _, _ = _slot_windows(y_padded, pos)
    D = _dct2_batch(sel)
    hi = D[:, PAIR1[0], PAIR1[1]] > D[:, PAIR2[0], PAIR2[1]]
    # Slot i carries packet bit (i % n_bits) and is copy number (i // n_bits);
    # slots are enumerated in that order, so the votes matrix is the flatten
    # transposed: votes[bit, copy] = hi[copy * n_bits + bit].
    votes = hi.reshape(reps, n_bits).T.astype(np.int8)
    bits = (np.sum(votes, axis=1) > (reps // 2)).astype(np.int8)
    bit_acc = float(np.mean(bits == packet))
    decoded, detected, version = layer.decode_bitstream(bits[np.newaxis, :], 'text')[0]
    return decoded, bool(detected), version, bit_acc