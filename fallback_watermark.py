"""Fallback watermark channel for the two-layer payload-recovery experiment.

Mareen et al. (2021) style: a short payload is BCH_SUPER-coded (TrustMark
DataLayer) into a fixed 100-bit packet, embedded in the DCT domain with
repetition and interleaved block placement, decoded by majority vote before
BCH correction. The perceptual hash stays a separate similarity screen and
never carries a payload.
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
    blocks_h = ph // BLOCK_SIZE
    blocks_w = pw // BLOCK_SIZE
    pos = _block_positions(ph, pw, n_bits, reps)
    for i, (bh, bw) in enumerate(pos):
        r, c = bh * BLOCK_SIZE, bw * BLOCK_SIZE
        block = _dct2(y_padded[r:r + BLOCK_SIZE, c:c + BLOCK_SIZE])
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
        y_padded[r:r + BLOCK_SIZE, c:c + BLOCK_SIZE] = _idct2(block)
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
    blocks_h = ph // BLOCK_SIZE
    blocks_w = pw // BLOCK_SIZE
    pos = _block_positions(ph, pw, n_bits, reps)
    votes = np.zeros((n_bits, reps), dtype=np.int8)
    for i, (bh, bw) in enumerate(pos):
        r, c = bh * BLOCK_SIZE, bw * BLOCK_SIZE
        block = _dct2(y_padded[r:r + BLOCK_SIZE, c:c + BLOCK_SIZE])
        votes[i % n_bits, i // n_bits] = 1 if block[PAIR1] > block[PAIR2] else 0
    bits = (np.sum(votes, axis=1) > (reps // 2)).astype(np.int8)
    bit_acc = float