"""Shared watermark service – singleton TrustMark, sign/verify dispatch."""

import os
import shutil
import tempfile
import threading
import numpy as np
from PIL import Image

from lsb_robustness import lsb_encode, lsb_decode, text_to_bits as lsb_text_to_bits, PAYLOAD_BITS as LSB_PAYLOAD_BITS
from dct_robustness import dct_encode, dct_decode, text_to_bits as dct_text_to_bits, PAYLOAD_BITS as DCT_PAYLOAD_BITS

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "output", "uploads")
PROCESSED_DIR = os.path.join(os.path.dirname(__file__), "output", "processed")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)

# ── TrustMark singleton ────────────────────────────────────────────
_tm = None
_tm_lock = threading.Lock()
_expected_packet = None


def _get_trustmark():
    global _tm, _expected_packet
    if _tm is None:
        with _tm_lock:
            if _tm is None:
                try:
                    from trustmark import TrustMark
                    from trustmark_robustness import encode_payload_to_packet, TM_PAYLOAD
                    _tm = TrustMark(verbose=False, model_type='Q', encoding_type=TrustMark.Encoding.BCH_4)
                    _expected_packet = encode_payload_to_packet(_tm, TM_PAYLOAD)
                except ImportError as e:
                    raise RuntimeError(
                        "TrustMark is not installed. "
                        "Install it with: pip install trustmark"
                    ) from e
    return _tm, _expected_packet


# ── Helpers ────────────────────────────────────────────────────────

def _save_temp(img: Image.Image, suffix: str = ".png") -> str:
    fd, path = tempfile.mkstemp(suffix=suffix, dir=PROCESSED_DIR)
    os.close(fd)
    img.save(path)
    return path


def _image_id_from_path(path: str) -> str:
    return os.path.splitext(os.path.basename(path))[0]


def _bits_to_text(bits: str) -> str:
    chars = []
    for i in range(0, len(bits), 7):
        chunk = bits[i:i + 7]
        if len(chunk) == 7:
            code = int(chunk, 2)
            chars.append(chr(code) if 32 <= code < 127 else f"\\x{code:02x}")
    return "".join(chars)


# ── Public API ─────────────────────────────────────────────────────

def sign_image(image_path: str, method: str, payload: str = None) -> dict:
    """Sign *image_path* with the given *method*. Returns metadata dict."""
    try:
        img = Image.open(image_path).convert("RGB")
    except OSError as e:
        print(f"[watermark_service] Cannot open image {image_path!r}: {e!r}")
        raise ValueError("Cannot open image") from e

    if method == "trustmark":
        try:
            tm, _ = _get_trustmark()
        except RuntimeError as e:
            raise ValueError(str(e)) from e
        try:
            signed = tm.encode(img, payload or "TM00001")
        except Exception as e:
            print(f"[watermark_service] TrustMark encode failed: {e!r}")
            raise ValueError("TrustMark encode failed") from e
        signed_path = _save_temp(signed, suffix=".png")
        return {
            "signed_path": signed_path,
            "method": "trustmark",
            "payload": payload or "TM00001",
            "width": signed.width,
            "height": signed.height,
        }

    elif method == "lsb":
        bits = lsb_text_to_bits(payload or "LSB0001")
        if len(bits) != len(LSB_PAYLOAD_BITS):
            raise ValueError(f"Payload must encode to {len(LSB_PAYLOAD_BITS)} bits (got {len(bits)})")
        try:
            signed = lsb_encode(img, bits)
        except Exception as e:
            print(f"[watermark_service] LSB encode failed: {e!r}")
            raise ValueError("LSB encode failed") from e
        signed_path = _save_temp(signed, suffix=".png")
        return {
            "signed_path": signed_path,
            "method": "lsb",
            "payload": payload or "LSB0001",
            "bit_count": len(bits),
        }

    elif method == "dct":
        bits = dct_text_to_bits(payload or "DCT0001")
        if len(bits) != len(DCT_PAYLOAD_BITS):
            raise ValueError(f"Payload must encode to {len(DCT_PAYLOAD_BITS)} bits (got {len(bits)})")
        try:
            signed = dct_encode(img, bits)
        except Exception as e:
            print(f"[watermark_service] DCT encode failed: {e!r}")
            raise ValueError("DCT encode failed") from e
        signed_path = _save_temp(signed, suffix=".png")
        return {
            "signed_path": signed_path,
            "method": "dct",
            "payload": payload or "DCT0001",
            "bit_count": len(bits),
        }

    else:
        raise ValueError(f"Unknown method: {method}")


def verify_image(image_path: str, method: str) -> dict:
    """Decode watermark from *image_path*. Returns verification results."""
    try:
        img = Image.open(image_path).convert("RGB")
    except OSError as e:
        print(f"[watermark_service] Cannot open image {image_path!r}: {e!r}")
        raise ValueError("Cannot open image") from e

    if method == "trustmark":
        try:
            tm, expected_packet = _get_trustmark()
        except RuntimeError as e:
            raise ValueError(str(e)) from e
        from trustmark_robustness import decode_and_accuracy
        try:
            decoded_text, present, schema, bit_acc = decode_and_accuracy(img, tm, expected_packet)
        except Exception as e:
            print(f"[watermark_service] TrustMark decode failed: {e!r}")
            raise ValueError("TrustMark decode failed") from e
        return {
            "method": "trustmark",
            "decoded_payload": decoded_text,
            "detected": present,
            "schema": schema,
            "bit_accuracy": round(bit_acc, 6),
        }

    elif method == "lsb":
        try:
            bits = lsb_decode(img, len(LSB_PAYLOAD_BITS))
        except Exception as e:
            print(f"[watermark_service] LSB decode failed: {e!r}")
            raise ValueError("LSB decode failed") from e
        from lsb_robustness import bit_accuracy as lsb_bit_acc
        ba = lsb_bit_acc(bits, LSB_PAYLOAD_BITS)
        extracted_text = _bits_to_text(bits)
        return {
            "method": "lsb",
            "decoded_payload": extracted_text,
            "detected": bits == LSB_PAYLOAD_BITS,
            "schema": None,
            "bit_accuracy": round(ba, 6),
        }

    elif method == "dct":
        try:
            bits = dct_decode(img, len(DCT_PAYLOAD_BITS))
        except Exception as e:
            print(f"[watermark_service] DCT decode failed: {e!r}")
            raise ValueError("DCT decode failed") from e
        from dct_robustness import bit_accuracy as dct_bit_acc
        ba = dct_bit_acc(bits, DCT_PAYLOAD_BITS)
        extracted_text = _bits_to_text(bits)
        return {
            "method": "dct",
            "decoded_payload": extracted_text,
            "detected": bits == DCT_PAYLOAD_BITS,
            "schema": None,
            "bit_accuracy": round(ba, 6),
        }

    else:
        raise ValueError(f"Unknown method: {method}")
