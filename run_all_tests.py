import socket
import subprocess
import sys

HOST = "127.0.0.1"
PORT = 8000

TESTS = [
    (
        "smoke_test",
        [sys.executable, "scripts/smoke_test.py"],
        True,
    ),
    (
        "test_confidence",
        [sys.executable, "scripts/test_confidence.py"],
        False,
    ),
    (
        "test_detect_watermark",
        [sys.executable, "scripts/test_detect_watermark.py"],
        False,
    ),
    (
        "verify_vectorised_dct",
        [sys.executable, "scripts/verify_vectorised_dct.py"],
        False,
    ),
    (
        "validate_experiment",
        [
            sys.executable,
            "validate_experiment.py",
            "--image-count",
            "1200",
            "--results-dir",
            "output/results/final1200",
        ],
        False,
    ),
]

MARKERS = {
    "PASS": "[PASS]",
    "FAIL": "[FAIL]",
    "SKIP": "[SKIP]",
}


def server_running():
    try:
        with socket.create_connection((HOST, PORT), timeout=2):
            return True
    except OSError:
        return False


def main():
    results = []

    for name, cmd, needs_server in TESTS:
        print("=" * 70)
        print(f"[RUN ] {name}")
        print(f"       {' '.join(cmd)}")

        if needs_server and not server_running():
            print(
                f"[SKIP] {name}: dashboard server not running on "
                f"{HOST}:{PORT}. Start it first with: python scripts/serve_db.py"
            )
            results.append((name, "SKIP"))
            continue

        completed = subprocess.run(cmd)
        status = "PASS" if completed.returncode == 0 else "FAIL"
        results.append((name, status))
        print(f"[{status}] {name} (exit code {completed.returncode})")

    print()
    print("=" * 70)
    print("SUMMARY")
    print("-" * 70)
    for name, status in results:
        print(f"  {MARKERS[status]} {name}")

    passed = sum(1 for _, status in results if status == "PASS")
    failed = sum(1 for _, status in results if status == "FAIL")
    skipped = sum(1 for _, status in results if status == "SKIP")
    print("-" * 70)
    print(f"  Total: {len(results)} | Passed: {passed} | Failed: {failed} | Skipped: {skipped}")

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
