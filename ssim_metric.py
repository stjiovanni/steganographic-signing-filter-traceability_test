"""SSIM (Structural Similarity Index) metric implementation.

Implements the window-based SSIM from Wang et al. 2004
("Image Quality Assessment: From Error Visibility to Structural Similarity"),
using a Gaussian window and the standard constants C1 = (K1 * L)^2 and
C2 = (K2 * L)^2 with L = 255 for 8-bit images.

Uses scipy.signal.convolve2d (scipy is available in this project).
"""

import numpy as np
from scipy.signal import convolve2d

# Constants from Wang et al. 2004
K1 = 0.01
K2 = 0.03
L = 255.0          # dynamic range for 8-bit images
WINDOW = 11        # 11x11 Gaussian window
SIGMA = 1.5        # sigma for the Gaussian window


def _gaussian_window(size=WINDOW, sigma=SIGMA):
    """Return a normalized 2D Gaussian window of the given size."""
    coords = np.arange(size, dtype=np.float64) - size // 2
    gauss_1d = np.exp(-(coords ** 2) / (2.0 * sigma ** 2))
    window = np.outer(gauss_1d, gauss_1d)
    return window / window.sum()


def ssim(img1, img2, window_size=WINDOW, sigma=SIGMA, K1=K1, K2=K2, L=L):
    """Compute the SSIM index (0-1) between two images.

    Args:
        img1, img2: numpy arrays of the same shape (H, W) or (H, W, C),
            with values in [0, 255]. Colour images are compared
            luminance-only (single channel) as in the classic SSIM.
        window_size: size of the Gaussian window (default 11).
        sigma: sigma of the Gaussian window (default 1.5).
        K1, K2: stabilisation constants.
        L: dynamic range of the pixel values.

    Returns:
        float: the mean SSIM index in [0, 1] (1 = identical).
    """
    img1 = np.asarray(img1, dtype=np.float64)
    img2 = np.asarray(img2, dtype=np.float64)

    if img1.shape != img2.shape:
        raise ValueError(f'Image shapes do not match: {img1.shape} vs {img2.shape}')

    # Compare luminance only (single channel) for colour images.
    if img1.ndim == 3:
        img1 = img1.mean(axis=2)
        img2 = img2.mean(axis=2)

    window = _gaussian_window(window_size, sigma)

    # Local statistics.
    mu1 = convolve2d(img1, window, mode='valid')
    mu2 = convolve2d(img2, window, mode='valid')
    mu1_sq = mu1 * mu1
    mu2_sq = mu2 * mu2
    mu1_mu2 = mu1 * mu2

    sigma1_sq = convolve2d(img1 * img1, window, mode='valid') - mu1_sq
    sigma2_sq = convolve2d(img2 * img2, window, mode='valid') - mu2_sq
    sigma12 = convolve2d(img1 * img2, window, mode='valid') - mu1_mu2

    C1 = (K1 * L) ** 2
    C2 = (K2 * L) ** 2

    ssim_map = ((2 * mu1_mu2 + C1) * (2 * sigma12 + C2)) / \
               ((mu1_sq + mu2_sq + C1) * (sigma1_sq + sigma2_sq + C2))
    return float(ssim_map.mean())
