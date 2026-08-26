"""Shared metrics helpers used across the watermarking pipelines."""

import numpy as np


def mse_psnr(img1, img2):
    """Mean squared error and peak signal-to-noise ratio (dB) between two PIL images.

    Returns (mse, psnr); psnr is float('inf') when the images are identical.
    """
    arr1 = np.asarray(img1).astype(np.int16)
    arr2 = np.asarray(img2).astype(np.int16)
    mse = np.mean(np.square(arr1 - arr2))
    if mse == 0:
        return 0.0, float('inf')
    psnr = 20 * np.log10(255.0) - 10 * np.log10(mse)
    return float(mse), float(psnr)


def bit_accuracy(extracted_bits, expected_bits):
    """Fraction of matching bits between two equal-length bit strings."""
    if len(extracted_bits) != len(expected_bits):
        return 0.0
    return sum(a == b for a, b in zip(extracted_bits, expected_bits)) / len(expected_bits)


def text_to_bits(text):
    """7-bit ASCII encoding used by the LSB/DCT baselines."""
    return ''.join(format(ord(t) & 127, '07b') for t in text)
