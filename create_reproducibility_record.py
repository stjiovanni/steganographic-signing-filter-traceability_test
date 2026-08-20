"""Create a self-contained reproducibility record for the final benchmark."""

import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import transforms


ROOT = Path(__file__).resolve().parent
DEFAULT_OUTPUT_DIR = ROOT / "output" / "results" / "final1200"
PACKAGE_NAMES = {
    "imagehash": "ImageHash",
    "numpy": "numpy",
    "pdqhash": "pdqhash",
    "Pillow": "Pillow",
    "scipy": "scipy",
    "torch": "torch",
    "torchvision": "torchvision",
    "trustmark": "trustmark",
}


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def package_versions():
    versions = {}
    for label, distribution in PACKAGE_NAMES.items():
        try:
            versions[label] = importlib.metadata.version(distribution)
        except importlib.metadata.PackageNotFoundError:
            versions[label] = None
    return versions


def gpu_details():
    try:
        import torch

        available = bool(torch.cuda.is_available())
        return {
            "available": available,
            "count": int(torch.cuda.device_count()) if available else 0,
            "devices": [torch.cuda.get_device_name(i) for i in range(torch.cuda.device_count())]
            if available else [],
            "cuda_version": torch.version.cuda,
        }
    except (ImportError, RuntimeError):
        return {"available": False, "count": 0, "devices": [], "cuda_version": None}


def command_text(argv):
    return " ".join(f'"{item}"' if " " in item else item for item in argv)


def build_commands(output_dir):
    python = sys.executable
    final = str(output_dir)
    return [
        [python, "experiment_manifest.py", "--input-dir", str(ROOT / "coco_val2017" / "val2017"),
         "--image-count", "1200", "--seed", "42", "--output", str(output_dir / "image_manifest.json")],
        [python, "transform_hash_robustness.py", "--image-count", "1200", "--seed", "42",
         "--output-csv", str(output_dir / "hash_robustness_results.csv.gz"), "--resume"],
        [python, "trustmark_robustness.py", "--image-count", "1200", "--seed", "42",
         "--output-csv", str(output_dir / "trustmark_robustness_results.csv"), "--resume"],
        [python, "lsb_robustness.py", "--image-count", "1200", "--seed", "42",
         "--output-csv", str(output_dir / "lsb_robustness_results.csv"), "--resume"],
        [python, "dct_robustness.py", "--image-count", "1200", "--seed", "42",
         "--output-csv", str(output_dir / "dct_robustness_results.csv"), "--resume"],
        [python, "ensemble_analysis.py", "--results-dir", final, "--output-dir", final],
        [python, "payload_ecc_ablation.py", "--execute", "--image-count", "100",
         "--output-csv", str(ROOT / "output" / "results" / "payload_ecc_ablation_dev100.csv"), "--resume"],
        [python, "payload_ecc_ablation.py", "--execute", "--image-count", "1200",
         "--ecc-modes", "BCH_SUPER", "--payload-lengths", "4",
         "--output-csv", str(ROOT / "output" / "results" / "payload_ecc_ablation_selected_final1200.csv"), "--resume"],
        [python, "ensemble_aware_payload_analysis.py", "--ablation",
         str(ROOT / "output" / "results" / "payload_ecc_ablation_selected_final1200.csv"),
         "--hash", str(output_dir / "hash_robustness_results.csv.gz"),
         "--out", str(ROOT / "output" / "results" / "ensemble_aware_payload_final1200.md"),
         "--scale-label", "final1200"],
        [python, "validate_experiment.py", "--image-count", "1200", "--results-dir", final],
    ]


def git_revision():
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, check=True,
                              capture_output=True, text=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def make_record(output_dir, manifest, result_file):
    commands = build_commands(output_dir)
    return {
        "record_type": "reproducibility_record",
        "record_created_utc": datetime.now(timezone.utc).isoformat(),
        "project_root": str(ROOT),
        "git_revision": git_revision(),
        "runtime": {
            "python_version": sys.version,
            "python_executable": sys.executable,
            "packages": package_versions(),
        },
        "system": {
            "os": platform.platform(),
            "os_name": platform.system(),
            "os_release": platform.release(),
            "machine": platform.machine(),
            "cpu": platform.processor() or platform.uname().processor or "unknown",
            "cpu_count": os.cpu_count(),
            "gpu": gpu_details(),
        },
        "model_and_software_versions": {
            "pipeline_version": "v2.1-reproducible",
            "transform_implementation": "transforms.py",
            "perceptual_hashes": ["phash", "dhash", "ahash", "whash", "colorhash",
                                  "dhash_vertical", "phash_simple", "pdq"],
            "watermark_software": ["TrustMark", "LSB baseline", "DCT baseline", "payload/ECC ablation (TrustMark BCH modes)"],
            "trustmark_model": "TrustMark package-managed default model",
        },
        "transform_configuration": {
            "image_count": 1200,
            "seed": 42,
            "selection": "lexicographically first 1200 JPG files",
            "transforms": transforms.TRANSFORM_STEPS,
            "random_transform_seed": "SHA-256(image_id_transform_name_intensity) first 8 bytes, masked to 31 bits",
        },
        "artefacts": {
            "manifest": {"path": str(manifest.relative_to(ROOT)), "sha256": sha256_file(manifest)},
            "final_result_file": {"path": str(result_file.relative_to(ROOT)), "sha256": sha256_file(result_file)},
        },
        "validation": {
            "command": command_text(commands[-1]),
            "command_argv": commands[-1],
            "output_location": "output/logs/run_1200_experiment.log (pipeline log); validation also writes stdout/stderr to the invoking terminal",
        },
        "rerun_commands": [{"argv": command, "command": command_text(command)} for command in commands],
        "secrets_policy": "No environment variables, .env files, credentials, tokens, or secret values are read or recorded.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--final-result", type=Path)
    args = parser.parse_args()

    output_dir = args.output_dir if args.output_dir.is_absolute() else ROOT / args.output_dir
    manifest = args.manifest or output_dir / "image_manifest.json"
    result_file = args.final_result or output_dir / "ensemble_decision_matrix.csv"
    if not manifest.is_absolute():
        manifest = ROOT / manifest
    if not result_file.is_absolute():
        result_file = ROOT / result_file
    missing = [str(path) for path in (manifest, result_file) if not path.is_file()]
    if missing:
        raise SystemExit("Required artefact(s) not found: " + ", ".join(missing))

    output_dir.mkdir(parents=True, exist_ok=True)
    record = make_record(output_dir, manifest, result_file)
    json_path = output_dir / "reproducibility_record.json"
    markdown_path = output_dir / "reproducibility_record.md"
    json_path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")

    lines = ["# Reproducibility Record", "", f"Created (UTC): `{record['record_created_utc']}`", "",
             "## Artefact Checksums", "",
             f"- Manifest: `{record['artefacts']['manifest']['path']}`",
             f"  SHA-256: `{record['artefacts']['manifest']['sha256']}`",
             f"- Final result: `{record['artefacts']['final_result_file']['path']}`",
             f"  SHA-256: `{record['artefacts']['final_result_file']['sha256']}`", "",
             "## Runtime", "", f"- Python: `{record['runtime']['python_version'].split()[0]}`",
             f"- OS: `{record['system']['os']}`", f"- CPU: `{record['system']['cpu']}`",
             f"- GPU: `{record['system']['gpu']['devices'] or 'none detected'}`", "",
             "## Model And Software", "", "- Pipeline: `v2.1-reproducible`",
             "- TrustMark model: package-managed default model", "- Packages:"]
    lines.extend(f"  - `{name}`: `{version or 'not installed'}`" for name, version in record["runtime"]["packages"].items())
    lines.extend(["", "## Transform Configuration", "", "```json",
                  json.dumps(record["transform_configuration"], indent=2), "```", "",
                  "## Validation", "", f"- Command: `{record['validation']['command']}`",
                  f"- Output/log location: `{record['validation']['output_location']}`", "",
                  "## Exact Rerun Commands", ""])
    lines.extend(f"- `{item['command']}`" for item in record["rerun_commands"])
    lines.extend(["", "## Secrets", "", record["secrets_policy"], ""])
    markdown_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {json_path}")
    print(f"Wrote {markdown_path}")


if __name__ == "__main__":
    main()
