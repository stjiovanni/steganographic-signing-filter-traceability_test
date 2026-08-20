"""Run the complete benchmark serially and leave a reproducible log."""

import os
import subprocess
import sys
from datetime import datetime, timezone


ROOT = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(ROOT, 'output', 'logs')
os.makedirs(LOG_DIR, exist_ok=True)
LOG_PATH = os.path.join(LOG_DIR, 'run_1200_experiment.log')
FINAL_RESULTS = os.path.join(ROOT, 'output', 'results', 'final1200')


def main():
    os.makedirs(FINAL_RESULTS, exist_ok=True)
    commands = [
        [sys.executable, 'experiment_manifest.py', '--input-dir', os.path.join(ROOT, 'coco_val2017', 'val2017'), '--image-count', '1200', '--output', os.path.join(FINAL_RESULTS, 'image_manifest.json')],
        [sys.executable, 'transform_hash_robustness.py', '--image-count', '1200', '--seed', '42', '--output-csv', os.path.join(FINAL_RESULTS, 'hash_robustness_results.csv.gz'), '--resume'],
        [sys.executable, 'trustmark_robustness.py', '--image-count', '1200', '--seed', '42', '--output-csv', os.path.join(FINAL_RESULTS, 'trustmark_robustness_results.csv'), '--resume'],
        [sys.executable, 'lsb_robustness.py', '--image-count', '1200', '--seed', '42', '--output-csv', os.path.join(FINAL_RESULTS, 'lsb_robustness_results.csv'), '--resume'],
        [sys.executable, 'dct_robustness.py', '--image-count', '1200', '--seed', '42', '--output-csv', os.path.join(FINAL_RESULTS, 'dct_robustness_results.csv'), '--resume'],
        [sys.executable, 'ensemble_analysis.py', '--results-dir', FINAL_RESULTS, '--output-dir', FINAL_RESULTS],
        [sys.executable, 'validate_experiment.py', '--image-count', '1200', '--results-dir', FINAL_RESULTS],
    ]
    with open(LOG_PATH, 'a', encoding='utf-8') as log:
        log.write(f'\n[{datetime.now(timezone.utc).isoformat()}] 1,200-image run started\n')
        for command in commands:
            log.write(f'\n$ {" ".join(command)}\n')
            log.flush()
            result = subprocess.run(command, cwd=ROOT, env={**os.environ, 'PYTHONUTF8': '1'},
                                    stdout=log, stderr=subprocess.STDOUT, text=True)
            if result.returncode:
                log.write(f'Command failed with exit code {result.returncode}; run stopped.\n')
                raise SystemExit(result.returncode)
        log.write(f'\n[{datetime.now(timezone.utc).isoformat()}] 1,200-image run completed\n')


if __name__ == '__main__':
    main()
