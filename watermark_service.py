"""Shared watermark service – singleton TrustMark, sign/verify dispatch.

Signing here means *watermark embedding* (soft binding). It is not
cryptographic signing: there are no keys, certificates, manifests or
trust chains. The 'hybrid' method embeds a TrustMark payload (primary)
plus a fallback watermark (BCH_SUPER-coded, DCT with repetition) and
reports the two-layer recovery outcome.
"""

import os
import tempfile
import threading
from PIL import Image

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "output", "uploads")
PROCESSED_DIR = os.path.join(os.path.dirname(__file__), "output", "processed")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)

# ── Experiment-script coupling ─────────────────────────────────────
# The LSB/DCT encode-decode implementations and the TrustMark packet/decode
# helpers live in the experiment scripts (lsb_robustness.py, dct_robustness.py,
# trustmark_robustness.py) because those scripts produced the reported results.
# The service reuses them through the lazy accessors below so both paths share
# one implementation. Extracting the codecs into a standalone module is
# deferred: the scripts double as CSV pipeline entry points with module-level
# payload constants and argparse mains, so moving the code would touch files
# owned by other workstreams. The accessors keep these imports off the service
# import path (and out of the rest of this file) until first use.

def _get_lsb_module():
    """lsb_robustness doubles as the service's LSB codec."""
    import lsb_robustness
    return lsb_robustness


def _get_dct_module():
    """dct_robustness doubles as the service's DCT codec."""
    import dct_robustness
    return dct_robustness


def _get_trustmark_decode():
    """decode_and_accuracy from the TrustMark robustness script."""
    from trustmark_robustness import decode_and_accuracy
    return decode_and_accuracy

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


# ── Confidence ─────────────────────────────────────────────────────
# Confidence is a transparent, deterministic scalar in [0, 1] derived
# ONLY from measured decode metrics (bit accuracy). It is deliberately
# NOT an identifier: no user id, filter id, or timestamp is encoded in
# the payload or reflected in the confidence value (privacy/ethics).
#   * single methods: confidence = bit_accuracy (already in [0, 1])
#   * hybrid:         confidence = max(trustmark.bit_accuracy,
#                                      fallback.bit_accuracy), unless
#                      neither channel recovers, in which case it is
#                      capped at CONFIDENCE_FAIL_CAP (0.5) so a failed
#                      recovery is never reported as high confidence.
CONFIDENCE_FAIL_CAP = 0.5
CONFIDENCE_DEFINITION = (
    "confidence = bit_accuracy for single methods; for hybrid, "
    "max(trustmark.bit_accuracy, fallback.bit_accuracy), capped at 0.5 "
    "when neither channel recovers. Deterministic function of measured "
    "decode metrics only - carries no identifier."
)


# ── Payload validation & capacity ──────────────────────────────────
# Each method embeds a fixed bit budget in 7-bit ASCII (codes 32-127).
#   * TrustMark BCH_4 packet = 100 bits; data bits = 100 - 28 ECC - 4
#     version = 68 bits -> 9 chars (63 bits; a 10th char would be
#     silently truncated by process_encode, corrupting the payload).
#   * LSB and DCT both pack PAYLOAD_BITS = 49 bits = exactly 7 chars.
#   * Hybrid: primary channel keeps the fixed "TM00001"; the *fallback*
#     channel carries the custom payload. The fallback uses BCH_SUPER
#     (100-bit packet, 40 data bits -> up to 5 chars), but it is capped
#     at 4 chars for headroom and to stay in line with the fixed FB01
#     default.

TRUSTMARK_MAX_CHARS = 9
LSB_MAX_CHARS = 7
DCT_MAX_CHARS = 7
HYBRID_FALLBACK_MAX_CHARS = 4

PAYLOAD_CAPACITY = {
    "trustmark": {"max_chars": TRUSTMARK_MAX_CHARS},
    "lsb": {"max_chars": LSB_MAX_CHARS},
    "dct": {"max_chars": DCT_MAX_CHARS},
    "hybrid": {"fallback_max_chars": HYBRID_FALLBACK_MAX_CHARS},
    "note": (
        "Capacities are in printable 7-bit ASCII characters (codes 32-127). "
        "LSB and DCT are fixed-length (exactly 7 chars). TrustMark accepts up "
        "to 9 chars; the hybrid fallback channel accepts up to 4 chars "
        "(the TrustMark primary channel stays at the fixed TM00001)."
    ),
}


def is_7bit_ascii(text: str) -> bool:
    return all(32 <= ord(c) < 127 for c in text)


def validate_payload(method: str, payload: str) -> str:
    """Validate *payload* for *method*. Returns None when valid, otherwise
    a human-readable error message. Raises ValueError for unknown methods.
    A None/empty payload is always valid (callers fall back to defaults)."""
    if payload is None or payload == "":
        return None
    if not is_7bit_ascii(payload):
        return (
            "Payload must contain only printable 7-bit ASCII characters "
            "(codes 32-127)"
        )
    if method == "trustmark":
        if len(payload) > TRUSTMARK_MAX_CHARS:
            return (
                f"TrustMark payload must be at most {TRUSTMARK_MAX_CHARS} "
                f"ASCII chars (got {len(payload)})"
            )
        return None
    if method == "lsb":
        if len(payload) != LSB_MAX_CHARS:
            return (
                f"LSB payload must be exactly {LSB_MAX_CHARS} ASCII chars "
                f"(got {len(payload)})"
            )
        return None
    if method == "dct":
        if len(payload) != DCT_MAX_CHARS:
            return (
                f"DCT payload must be exactly {DCT_MAX_CHARS} ASCII chars "
                f"(got {len(payload)})"
            )
        return None
    if method == "hybrid":
        if len(payload) > HYBRID_FALLBACK_MAX_CHARS:
            return (
                f"Hybrid fallback payload must be at most "
                f"{HYBRID_FALLBACK_MAX_CHARS} ASCII chars (got {len(payload)})"
            )
        return None
    raise ValueError(f"Unknown method: {method}")


def get_payload_capacity() -> dict:
    """Per-method payload capacities (7-bit ASCII chars) for the UI."""
    return dict(PAYLOAD_CAPACITY)


# ── Public API ─────────────────────────────────────────────────────

def sign_image(image_path: str, method: str, payload: str = None) -> dict:
    """Sign *image_path* with the given *method*. Returns metadata dict."""
    try:
        img = Image.open(image_path).convert("RGB")
    except OSError as e:
        print(f"[watermark_service] Cannot open image {image_path!r}: {e!r}")
        raise ValueError("Cannot open image") from e

    if method == "trustmark":
        err = validate_payload("trustmark", payload)
        if err:
            raise ValueError(err)
        try:
            tm, _ = _get_trustmark()
        except RuntimeError as e:
            raise ValueError(str(e)) from e
        tm_payload = payload or "TM00001"
        try:
            signed = tm.encode(img, tm_payload)
        except Exception as e:
            print(f"[watermark_service] TrustMark encode failed: {e!r}")
            raise ValueError("TrustMark encode failed") from e
        signed_path = _save_temp(signed, suffix=".png")
        return {
            "signed_path": signed_path,
            "method": "trustmark",
            "payload": tm_payload,
            "width": signed.width,
            "height": signed.height,
        }

    elif method == "lsb":
        err = validate_payload("lsb", payload)
        if err:
            raise ValueError(err)
        lsb = _get_lsb_module()
        lsb_payload = payload or "LSB0001"
        bits = lsb.text_to_bits(lsb_payload)
        if len(bits) != len(lsb.PAYLOAD_BITS):
            raise ValueError(f"Payload must encode to {len(lsb.PAYLOAD_BITS)} bits (got {len(bits)})")
        try:
            signed = lsb.lsb_encode(img, bits)
        except Exception as e:
            print(f"[watermark_service] LSB encode failed: {e!r}")
            raise ValueError("LSB encode failed") from e
        signed_path = _save_temp(signed, suffix=".png")
        return {
            "signed_path": signed_path,
            "method": "lsb",
            "payload": lsb_payload,
            "bit_count": len(bits),
        }

    elif method == "dct":
        err = validate_payload("dct", payload)
        if err:
            raise ValueError(err)
        dct = _get_dct_module()
        dct_payload = payload or "DCT0001"
        bits = dct.text_to_bits(dct_payload)
        if len(bits) != len(dct.PAYLOAD_BITS):
            raise ValueError(f"Payload must encode to {len(dct.PAYLOAD_BITS)} bits (got {len(bits)})")
        try:
            signed = dct.dct_encode(img, bits)
        except Exception as e:
            print(f"[watermark_service] DCT encode failed: {e!r}")
            raise ValueError("DCT encode failed") from e
        signed_path = _save_temp(signed, suffix=".png")
        return {
            "signed_path": signed_path,
            "method": "dct",
            "payload": dct_payload,
            "bit_count": len(bits),
        }

    elif method == "hybrid":
        # Two-layer sign: TrustMark primary + fallback watermark. The custom
        # payload (if any) is embedded in the FALLBACK channel; the TrustMark
        # primary channel stays at the fixed "TM00001".
        err = validate_payload("hybrid", payload)
        if err:
            raise ValueError(err)
        try:
            tm, _ = _get_trustmark()
        except RuntimeError as e:
            raise ValueError(str(e)) from e
        import fallback_watermark as fb
        layer = fb.make_codec()
        fb_payload = payload or fb.FALLBACK_PAYLOAD
        try:
            signed_tm = tm.encode(img, "TM00001")
            signed = fb.embed(signed_tm, layer, fb_payload)
        except Exception as e:
            print(f"[watermark_service] Hybrid encode failed: {e!r}")
            raise ValueError("Hybrid encode failed") from e
        signed_path = _save_temp(signed, suffix=".png")
        return {
            "signed_path": signed_path,
            "method": "hybrid",
            "payload": fb_payload,
            "primary_channel": "trustmark (TM00001)",
            "fallback_channel": f"fallback ({fb_payload})",
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
        decode_and_accuracy = _get_trustmark_decode()
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
            "confidence": round(bit_acc, 6),
            "confidence_definition": CONFIDENCE_DEFINITION,
        }

    elif method == "lsb":
        lsb = _get_lsb_module()
        try:
            bits = lsb.lsb_decode(img, len(lsb.PAYLOAD_BITS))
        except Exception as e:
            print(f"[watermark_service] LSB decode failed: {e!r}")
            raise ValueError("LSB decode failed") from e
        ba = lsb.bit_accuracy(bits, lsb.PAYLOAD_BITS)
        extracted_text = _bits_to_text(bits)
        return {
            "method": "lsb",
            "decoded_payload": extracted_text,
            "detected": bits == lsb.PAYLOAD_BITS,
            "schema": None,
            "bit_accuracy": round(ba, 6),
            "confidence": round(ba, 6),
            "confidence_definition": CONFIDENCE_DEFINITION,
        }

    elif method == "dct":
        dct = _get_dct_module()
        try:
            bits = dct.dct_decode(img, len(dct.PAYLOAD_BITS))
        except Exception as e:
            print(f"[watermark_service] DCT decode failed: {e!r}")
            raise ValueError("DCT decode failed") from e
        ba = dct.bit_accuracy(bits, dct.PAYLOAD_BITS)
        extracted_text = _bits_to_text(bits)
        return {
            "method": "dct",
            "decoded_payload": extracted_text,
            "detected": bits == dct.PAYLOAD_BITS,
            "schema": None,
            "bit_accuracy": round(ba, 6),
            "confidence": round(ba, 6),
            "confidence_definition": CONFIDENCE_DEFINITION,
        }

    elif method == "hybrid":
        # Two-layer verify: decode TrustMark and the fallback watermark on the
        # same combined image; 'recovered' is true if either channel decodes.
        decode_and_accuracy = _get_trustmark_decode()
        import fallback_watermark as fb
        try:
            tm, expected_packet = _get_trustmark()
            layer = fb.make_codec()
        except RuntimeError as e:
            raise ValueError(str(e)) from e
        try:
            tm_text, tm_present, tm_schema, tm_acc = decode_and_accuracy(img, tm, expected_packet)
            fb_text, fb_present, fb_schema, fb_acc = fb.decode(img, layer, fb.FALLBACK_PAYLOAD)
        except Exception as e:
            print(f"[watermark_service] Hybrid decode failed: {e!r}")
            raise ValueError("Hybrid decode failed") from e
        # Confidence = best single-channel bit accuracy, capped below the
        # detection midpoint when neither layer recovers (see definition above).
        conf = max(tm_acc, fb_acc)
        if not (tm_present or fb_present):
            conf = min(conf, CONFIDENCE_FAIL_CAP)
        return {
            "method": "hybrid",
            "recovered": bool(tm_present or fb_present),
            "confidence": round(conf, 6),
            "confidence_definition": CONFIDENCE_DEFINITION,
            "trustmark": {
                "decoded_payload": tm_text,
                "detected": bool(tm_present),
                "schema": tm_schema,
                "bit_accuracy": round(tm_acc, 6),
            },
            "fallback": {
                "decoded_payload": fb_text,
                "detected": bool(fb_present),
                "schema": fb_schema,
                "bit_accuracy": round(fb_acc, 6),
            },
            "note": ("Two-layer payload recovery = TrustMark OR fallback decode. "
                     "This is payload recovery, not authentication or provenance."),
        }

    else:
        raise ValueError(f"Unknown method: {method}")


def detect_watermarks(image_path: str) -> dict:
    """Decode *image_path* with all four methods and report per-method results.

    Reuses the existing decode paths (verify_image), so each element of the
    ``results`` list has the same shape as a verify_image result (method,
    decoded_payload, detected/recovered, bit_accuracy, confidence,
    confidence_definition, schema). Returns ``{results, confidence, note}``
    where confidence is the best per-method confidence.

    LSB and DCT have no error-correcting code, so verify_image's ``detected``
    only matches the known default payload. In this blind scan a fully
    printable 7-char decode is therefore also counted as a recovered payload
    (a custom payload like "JANE226" shows up as recovered text even though it
    is not the default LSB0001/DCT0001).
    """
    results = []
    for method in ("trustmark", "lsb", "dct", "hybrid"):
        try:
            res = verify_image(image_path, method)
        except ValueError as e:
            res = {
                "method": method,
                "decoded_payload": None,
                "detected": False,
                "schema": None,
                "bit_accuracy": 0.0,
                "confidence": 0.0,
                "confidence_definition": CONFIDENCE_DEFINITION,
                "error": str(e),
            }
        else:
            # _bits_to_text escapes any non-printable 7-bit chunk as "\xNN";
            # their absence means every decoded character was printable ASCII,
            # i.e. a meaningful payload was recovered.
            if method == "hybrid":
                # verify_image reports hybrid via 'recovered' (nested channels);
                # expose the same boolean as 'detected' and a top-level
                # decoded_payload (fallback text when its channel recovered,
                # else the TrustMark text) for a uniform per-method shape.
                res["detected"] = bool(res.get("recovered"))
                fb = res.get("fallback") or {}
                tm = res.get("trustmark") or {}
                res["decoded_payload"] = (
                    fb.get("decoded_payload") if fb.get("detected")
                    else tm.get("decoded_payload")
                )
                res["bit_accuracy"] = max(
                    tm.get("bit_accuracy") or 0.0, fb.get("bit_accuracy") or 0.0
                )
            elif method in ("lsb", "dct"):
                text = res.get("decoded_payload") or ""
                if text and "\\x" not in text:
                    res["detected"] = True
        results.append(res)
    conf = max((r.get("confidence") or 0.0) for r in results)
    return {
        "results": results,
        "confidence": round(conf, 6),
        "note": ("Per-method payload-recovery scan of the suspect image. "
                 "'detected' means the embedded text was recovered; for the "
                 "no-ECC baselines (LSB/DCT) a fully printable 7-char decode "
                 "counts as recovered. This is payload recovery, not "
                 "authentication or provenance."),
    }
