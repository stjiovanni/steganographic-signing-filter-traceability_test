"""Opt-in TrustMark payload/ECC ablation.

This experiment writes a new CSV only.  It deliberately reports decoder
packet accuracy separately from TrustMark's ECC-corrected text result.
Run without --execute for a fail-closed configuration check.
"""

import argparse
import csv
import gc
import hashlib
import math
import os
import py_compile
import sys
import time
from glob import glob

import numpy as np
from PIL import Image

import transforms


PIPELINE_VERSION = "payload-ecc-ablation-v1"
DEFAULT_PAYLOAD_LENGTHS = (1, 4, 5)
PAUSE_FILE = "output/logs/payload_ecc_ablation.pause"

def _paused():
    return os.path.exists(PAUSE_FILE)
ECC_NAMES = {
    "BCH_SUPER": 0,
    "BCH_5": 1,
    "BCH_4": 2,
    "BCH_3": 3,
}
FIELDNAMES = [
    "experiment", "config_id", "image_id", "filename", "ecc_mode",
    "ecc_encoding_type", "model_type", "secret_len", "payload",
    "payload_chars", "payload_data_bits", "transform_name",
    "intensity_value", "pipeline_version", "status", "error",
    "encode_mse", "encode_psnr", "raw_packet_bits", "raw_bit_accuracy",
    "corrected_payload", "corrected_decode_present", "corrected_schema",
    "corrected_exact", "width", "height", "aspect_ratio",
]


def _payload(length):
    alphabet = "ABCDE12345"
    return (alphabet * ((length + len(alphabet) - 1) // len(alphabet)))[:length]


def _parse_int_list(value, label):
    try:
        result = tuple(int(item.strip()) for item in value.split(",") if item.strip())
    except ValueError as exc:
        raise ValueError(f"{label} must be comma-separated integers") from exc
    if not result:
        raise ValueError(f"{label} must not be empty")
    return result


def _packet(datalaer, payload):
    text_bytes = datalaer.encode_text_ascii(payload)
    text_bits = "".join(format(byte, "08b") for byte in text_bytes)
    packet = datalaer.process_encode(text_bits)
    return np.asarray(packet, dtype=np.int32), len(text_bits)


def validate_configuration(payload_lengths, ecc_modes, secret_len, model_type):
    """Validate against TrustMark's native packet implementation, not guesses."""
    try:
        from trustmark import TrustMark
        from trustmark.datalayer import DataLayer
    except ImportError as exc:
        raise RuntimeError(
            "TrustMark is not installed; install it with: pip install trustmark"
        ) from exc

    if secret_len != 100:
        raise RuntimeError(
            "This package's shipped checkpoints expose 100 decoder bits; "
            "a different secret_len is rejected rather than inferred."
        )
    if model_type not in {"C", "Q", "B", "P"}:
        raise RuntimeError("model_type must be one of C, Q, B, P")

    available = {
        name: getattr(TrustMark.Encoding, name, None) for name in ECC_NAMES
    }
    missing = [name for name, value in available.items() if value is None]
    if missing:
        raise RuntimeError(
            "Installed TrustMark lacks native ECC enum(s): " + ", ".join(missing)
        )

    checks = []
    for mode_name in ecc_modes:
        if mode_name not in available:
            raise RuntimeError(f"Unsupported native ECC mode: {mode_name}")
        mode_value = available[mode_name]
        layer = DataLayer(secret_len, verbose=False, encoding_mode=mode_value)
        for length in payload_lengths:
            if length < 1:
                raise RuntimeError("payload lengths must be positive")
            payload = _payload(length)
            packet, data_bits = _packet(layer, payload)
            if len(packet) != secret_len:
                raise RuntimeError(
                    f"{mode_name}/{length}: native packet has {len(packet)} bits, "
                    f"expected {secret_len}"
                )
            if data_bits > secret_len - layer.bch_encoder.get_ecc_bits() - layer.versionbits:
                raise RuntimeError(
                    f"{mode_name}/{length}: payload exceeds native data capacity; "
                    "choose a shorter payload"
                )
            decoded, detected, version = layer.decode_bitstream(
                packet[np.newaxis, :], "text"
            )[0]
            if not detected or decoded != payload:
                raise RuntimeError(
                    f"{mode_name}/{length}: native clean packet did not round-trip "
                    f"({decoded!r}, detected={detected}, version={version})"
                )
            checks.append({
                "config_id": f"{mode_name.lower()}_{length}chars",
                "ecc_mode": mode_name,
                "ecc_encoding_type": int(mode_value),
                "payload": payload,
                "payload_chars": length,
                "payload_data_bits": data_bits,
                "packet_bits": len(packet),
                "ecc_bits": int(layer.bch_encoder.get_ecc_bits()),
            })
    return checks


def _metrics(original, watermarked):
    first = np.asarray(original).astype(np.int16)
    second = np.asarray(watermarked).astype(np.int16)
    mse = float(np.mean(np.square(first - second)))
    psnr = float("inf") if mse == 0 else float(20 * math.log10(255.0) - 10 * math.log10(mse))
    return mse, psnr


def _candidates(watermarked, image_id):
    yield "none", "", watermarked
    for name in transforms.ALL_TRANSFORMS:
        for intensity in transforms.TRANSFORM_STEPS[name]:
            candidate = transforms.apply_transform(watermarked, name, intensity, image_id=image_id)
            yield name, str(intensity), candidate


def _decode(image, tm, expected):
    import torch
    from torchvision import transforms as tv_transforms

    resized = image.convert("RGB").resize(
        (tm.model_resolution_dec, tm.model_resolution_dec), Image.BILINEAR
    )
    tensor = tv_transforms.ToTensor()(resized).unsqueeze(0).to(tm.decoder.device) * 2.0 - 1.0
    with torch.no_grad():
        raw = (tm.decoder.decoder(tensor) > 0).cpu().numpy().astype(np.int32)
    received = raw[0]
    raw_accuracy = float(np.mean(expected == received))
    corrected, present, version = tm.ecc.decode_bitstream(raw, "text")[0]
    del tensor, raw, received
    return raw_accuracy, corrected, bool(present), version


def run(args, checks):
    from trustmark import TrustMark

    paths = sorted(glob(os.path.join(args.input_dir, "*.jpg")))[:args.image_count]
    if len(paths) < args.image_count:
        raise RuntimeError(f"Only {len(paths)} JPG images found; {args.image_count} required")
    os.makedirs(os.path.dirname(args.output_csv) or ".", exist_ok=True)
    existing = set()
    if args.resume and os.path.exists(args.output_csv):
        with open(args.output_csv, newline="", encoding="utf-8") as stream:
            existing = {row["row_key"] for row in csv.DictReader(stream) if row.get("row_key")}

    file_exists = args.resume and os.path.exists(args.output_csv)
    with open(args.output_csv, "a" if file_exists else "w", newline="", encoding="utf-8") as stream:
        fields = FIELDNAMES + ["row_key"]
        writer = csv.DictWriter(stream, fieldnames=fields)
        if not file_exists:
            writer.writeheader()
        started = time.time()
        for check in checks:
            mode = getattr(TrustMark.Encoding, check["ecc_mode"])
            tm = TrustMark(verbose=False, model_type=args.model_type,
                           secret_len=args.secret_len, encoding_type=mode,
                           loadRemover=False)
            expected, _ = _packet(tm.ecc, check["payload"])
            for image_index, path in enumerate(paths):
                if _paused():
                    print(f"PAUSE triggered before image {image_index}/{len(paths)} "
                          f"({check['config_id']}); rows are safe to resume.", flush=True)
                    return
                image_id = os.path.splitext(os.path.basename(path))[0]
                with Image.open(path) as opened:
                    original = opened.convert("RGB")
                watermarked = tm.encode(original, check["payload"])
                mse, psnr = _metrics(original, watermarked)
                for transform_name, intensity, candidate in _candidates(watermarked, image_id):
                    row_key = hashlib.sha256(
                        f"{check['config_id']}|{image_id}|{transform_name}|{intensity}".encode()
                    ).hexdigest()
                    if row_key in existing:
                        continue
                    width, height = candidate.size
                    row = {"experiment": "payload_ecc_ablation", "config_id": check["config_id"],
                           "image_id": image_id, "filename": os.path.basename(path),
                           "ecc_mode": check["ecc_mode"],
                           "ecc_encoding_type": check["ecc_encoding_type"],
                           "model_type": args.model_type, "secret_len": args.secret_len,
                           "payload": check["payload"], "payload_chars": check["payload_chars"],
                           "payload_data_bits": check["payload_data_bits"],
                           "transform_name": transform_name, "intensity_value": intensity,
                           "pipeline_version": PIPELINE_VERSION, "status": "ok", "error": "",
                           "encode_mse": mse, "encode_psnr": psnr, "raw_packet_bits": len(expected),
                           "raw_bit_accuracy": None, "corrected_payload": None,
                           "corrected_decode_present": None, "corrected_schema": None,
                           "corrected_exact": None, "width": width, "height": height,
                           "aspect_ratio": round(width / height, 6) if height else None,
                           "row_key": row_key}
                    try:
                        raw_acc, corrected, present, version = _decode(candidate, tm, expected)
                        row.update(raw_bit_accuracy=raw_acc, corrected_payload=corrected,
                                   corrected_decode_present=present, corrected_schema=version,
                                   corrected_exact=bool(present and corrected == check["payload"]))
                    except Exception as exc:
                        row.update(status="error", error=f"{type(exc).__name__}: {exc}")
                    writer.writerow(row)
                    del candidate
                del watermarked, original
                if image_index and image_index % 25 == 0:
                    gc.collect()
                stream.flush()
        print(f"Wrote ablation rows to {args.output_csv} in {time.time() - started:.1f}s")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="validate only; default when --execute is absent")
    parser.add_argument("--execute", action="store_true", help="run the opt-in experiment")
    parser.add_argument("--compile-check", action="store_true", help="compile this script and exit")
    parser.add_argument("--input-dir", default=transforms.COCO_DIR)
    parser.add_argument("--output-csv", default="output/results/payload_ecc_ablation_results.csv")
    parser.add_argument("--image-count", type=int, default=10)
    parser.add_argument("--payload-lengths", default=",".join(map(str, DEFAULT_PAYLOAD_LENGTHS)))
    parser.add_argument("--ecc-modes", default=",".join(ECC_NAMES))
    parser.add_argument("--model-type", default="Q")
    parser.add_argument("--secret-len", type=int, default=100)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    if args.compile_check:
        py_compile.compile(__file__, doraise=True)
        print("compile-check: OK")
        return 0
    if args.image_count < 1:
        parser.error("--image-count must be positive")
    try:
        lengths = _parse_int_list(args.payload_lengths, "--payload-lengths")
        modes = tuple(item.strip() for item in args.ecc_modes.split(",") if item.strip())
        checks = validate_configuration(lengths, modes, args.secret_len, args.model_type)
    except (RuntimeError, ValueError) as exc:
        print(f"DRY-RUN FAILED: {exc}", file=sys.stderr)
        return 2
    print(f"DRY-RUN OK: {len(checks)} native configurations; no existing result files changed")
    for check in checks:
        print("  {config_id}: {ecc_bits} ECC bits, {payload_data_bits} payload bits".format(**check))
    if args.execute and not args.dry_run:
        try:
            run(args, checks)
        except Exception as exc:
            print(f"EXECUTION FAILED: {type(exc).__name__}: {exc}", file=sys.stderr)
            return 1
    elif args.execute and args.dry_run:
        parser.error("use either --dry-run or --execute, not both")
    else:
        print("Not executed. Pass --execute to opt in.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
