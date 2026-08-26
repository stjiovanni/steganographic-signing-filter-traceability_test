"""Capture FPR Figures 2-4: the live Sign/Verify dashboard against the
validated final1200 evidence set.

Fig 2 - Sign/Verify interface after upload (Original pane populated, dataset banner visible)
Fig 3 - Verification results, single method (TrustMark)
Fig 4 - Verification results, hybrid two-layer method (TrustMark + fallback)
"""

import os
import sys

from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG = os.path.join(ROOT, 'coco_val2017', 'val2017', '000000000139.jpg')
FIGDIR = os.path.join(ROOT, 'output', 'figures')
BASE = 'http://127.0.0.1:8000'
sys.stdout.reconfigure(encoding='utf-8')


def upload_and_sign(page, method):
    page.goto(BASE + '/', wait_until='networkidle')
    page.wait_for_selector('#dataset-banner:not([hidden])', timeout=120000)
    assert 'final1200' in page.inner_text('#dataset-banner'), 'banner must show final1200'
    page.set_input_files('#sv-file-input', IMG)
    page.click('#sv-upload-btn')
    page.wait_for_selector('#sv-preview-original img', timeout=120000)
    page.select_option('#sv-method-select', method)
    payload = '' if method == 'hybrid' else ''
    if method == 'hybrid':
        page.fill('#sv-payload-input', '')  # default FB01
    page.click('#sv-sign-btn')
    page.wait_for_selector('#sv-preview-signed img', timeout=180000)


def verify_and_shot(page, shot_path):
    page.click('#sv-verify-btn')
    page.wait_for_selector('#sv-results .sv-result-item', timeout=180000)
    page.wait_for_timeout(400)
    page.screenshot(path=shot_path, full_page=True)


def main():
    os.makedirs(FIGDIR, exist_ok=True)
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page(viewport={'width': 1440, 'height': 950},
                                device_scale_factor=1.5)

        # ---- Figure 2: interface after upload ----
        upload_and_sign(page, 'trustmark')
        page.screenshot(path=os.path.join(FIGDIR, 'dashboard_fig2_interface.png'),
                        full_page=True)
        print('captured dashboard_fig2_interface.png')

        # ---- Figure 3: single-method verification results ----
        verify_and_shot(page, os.path.join(FIGDIR, 'dashboard_fig3_verify_single.png'))
        results_text = page.inner_text('#sv-results-card').lower()
        assert 'method' in results_text and 'detected' in results_text, results_text[:200]
        print('captured dashboard_fig3_verify_single.png')

        # ---- Figure 4: hybrid two-layer verification results ----
        upload_and_sign(page, 'hybrid')
        verify_and_shot(page, os.path.join(FIGDIR, 'dashboard_fig4_verify_hybrid.png'))
        results_text = page.inner_text('#sv-results-card').lower()
        assert 'two-layer recovery' in results_text, results_text[:200]
        print('captured dashboard_fig4_verify_hybrid.png')

        browser.close()
    print('ALL SCREENSHOTS CAPTURED')


if __name__ == '__main__':
    main()