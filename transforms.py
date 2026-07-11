"""Shared transform definitions and intensity steps for all robustness pipelines.
Single source of truth — every script imports from here."""

from PIL import Image, ImageFilter, ImageEnhance
import numpy as np
import os

COCO_DIR = os.path.join(os.path.dirname(__file__), 'coco_val2017', 'val2017')
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), 'output')

# Intensity steps per transform
TRANSFORM_STEPS = {
    'brightness':       [0.5, 0.7, 0.85, 1.15, 1.5, 2.0],
    'contrast':         [0.5, 0.7, 0.85, 1.15, 1.5, 2.0],
    'saturation':       [0.2, 0.43, 0.66, 0.89, 1.11, 1.34, 1.57, 1.8],
    'vibrancy':         [0.2, 0.43, 0.66, 0.89, 1.11, 1.34, 1.57, 1.8],
    'gaussian_blur':    [0.5, 1.0, 1.5, 2.0, 3.0, 5.0],
    'salt_pepper_noise': [0.01, 0.02, 0.04, 0.06, 0.10, 0.15],
    'jpeg_compression': [95, 80, 65, 50, 35, 20, 10, 5],
    'rotation':         [1, 2, 5, 10, 20, 45, 70, 90],
    'scaling':          [0.25, 0.5, 0.75, 1.5, 2.0, 3.0],
    'crop_center':      [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8],
    'crop_random':      [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8],
    'letterbox':        ['black', 'grey'],
}

ALL_TRANSFORMS = list(TRANSFORM_STEPS.keys())

def make_seed(image_id, transform_name, intensity):
    """Deterministic seed for random transforms from image_id + transform + intensity."""
    h = hash(f'{image_id}_{transform_name}_{intensity}')
    return h & 0x7FFFFFFF


def apply_brightness(img, intensity, rng=None):
    return ImageEnhance.Brightness(img).enhance(intensity)


def apply_contrast(img, intensity, rng=None):
    return ImageEnhance.Contrast(img).enhance(intensity)


def apply_saturation(img, intensity, rng=None):
    return ImageEnhance.Color(img).enhance(intensity)


def apply_vibrancy(img, intensity, rng=None):
    """Non-linear saturation boost: favours less-saturated pixels more."""
    hsv = img.convert('HSV')
    h, s, v = hsv.split()
    s_np = np.array(s, dtype=np.float32) / 255.0
    boost = intensity - 1.0
    s_new = s_np + boost * (1.0 - s_np) ** 2
    s_new = np.clip(s_new, 0.0, 1.0)
    s_out = Image.fromarray((s_new * 255).astype(np.uint8))
    return Image.merge('HSV', (h, s_out, v)).convert('RGB')


def apply_gaussian_blur(img, intensity, rng=None):
    return img.filter(ImageFilter.GaussianBlur(radius=intensity))


def apply_salt_pepper_noise(img, intensity, rng=None):
    arr = np.asarray(img).astype(np.uint8)
    mask = rng.random(size=arr.shape[:2]) < intensity
    salt = rng.random(size=arr.shape[:2]) < 0.5
    arr[mask & salt] = 255
    arr[mask & ~salt] = 0
    return Image.fromarray(arr)


def apply_jpeg_compression(img, intensity, rng=None):
    path = os.path.join(OUTPUT_DIR, '_tmp_jpeg.jpg')
    img.save(path, 'JPEG', quality=int(intensity))
    result = Image.open(path).convert('RGB')
    if os.path.exists(path):
        os.remove(path)
    return result


def apply_rotation(img, intensity, rng=None):
    if int(intensity) == 90:
        return img.rotate(90, expand=True, fillcolor=128)
    return img.rotate(int(intensity), expand=False, fillcolor=128)


def apply_scaling(img, intensity, rng=None):
    w, h = img.size
    nw = max(1, int(w * intensity))
    nh = max(1, int(h * intensity))
    return img.resize((nw, nh), Image.LANCZOS)


def apply_crop_center(img, intensity, rng=None):
    """Crop to center region; intensity = fraction of dimension *removed*."""
    w, h = img.size
    keep = 1.0 - intensity
    cw = max(1, int(w * keep))
    ch = max(1, int(h * keep))
    return img.crop(((w - cw) // 2, (h - ch) // 2,
                     (w - cw) // 2 + cw, (h - ch) // 2 + ch))


def apply_crop_random(img, intensity, rng=None):
    """Random crop; intensity = fraction of dimension *removed*.
    Uses the provided rng for reproducibility (seeded per image_id)."""
    w, h = img.size
    keep = 1.0 - intensity
    cw = max(1, int(w * keep))
    ch = max(1, int(h * keep))
    max_x = w - cw
    max_y = h - ch
    x = int(rng.integers(0, max(max_x, 1))) if max_x > 0 else 0
    y = int(rng.integers(0, max(max_y, 1))) if max_y > 0 else 0
    return img.crop((x, y, x + cw, y + ch))


def apply_letterbox(img, intensity, rng=None):
    """Pad to square with fill color; intensity = 'black' or 'grey'."""
    w, h = img.size
    max_dim = max(w, h)
    fill = (0, 0, 0) if intensity == 'black' else (128, 128, 128)
    padded = Image.new('RGB', (max_dim, max_dim), fill)
    x_off = (max_dim - w) // 2
    y_off = (max_dim - h) // 2
    padded.paste(img, (x_off, y_off))
    return padded


TRANSFORM_FUNCTIONS = {
    'brightness':        apply_brightness,
    'contrast':          apply_contrast,
    'saturation':        apply_saturation,
    'vibrancy':          apply_vibrancy,
    'gaussian_blur':     apply_gaussian_blur,
    'salt_pepper_noise': apply_salt_pepper_noise,
    'jpeg_compression':  apply_jpeg_compression,
    'rotation':          apply_rotation,
    'scaling':           apply_scaling,
    'crop_center':       apply_crop_center,
    'crop_random':       apply_crop_random,
    'letterbox':         apply_letterbox,
}


def apply_transform(img, transform_name, intensity, image_id=None):
    """Apply a transform at a given intensity.
    Uses deterministic seeding for random transforms if image_id provided."""
    fn = TRANSFORM_FUNCTIONS.get(transform_name)
    if fn is None:
        raise ValueError(f'Unknown transform: {transform_name}')
    if image_id is not None:
        rng = np.random.default_rng(make_seed(image_id, transform_name, intensity))
    else:
        rng = np.random.default_rng(42)
    return fn(img, intensity, rng=rng)
