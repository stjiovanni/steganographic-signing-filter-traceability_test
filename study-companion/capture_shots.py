"""Capture screenshots of the study companion: chapter, quiz selected, quiz after
correct answer (green state), and quiz after wrong answer (red state)."""

import os
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URL = Path(os.path.join(ROOT, 'study-companion', 'index.html')).as_uri()
OUT = os.path.join(ROOT, 'study-companion', 'shots')
sys.stdout.reconfigure(encoding='utf-8')
os.makedirs(OUT, exist_ok=True)


def main():
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page(viewport={'width': 390, 'height': 844},
                                device_scale_factor=2, is_mobile=True, has_touch=True)
        page.goto(URL, wait_until='load')
        page.wait_for_timeout(400)
        page.screenshot(path=os.path.join(OUT, 'chapter1.png'), full_page=True)

        # into quiz
        page.click('#next-btn')
        page.wait_for_timeout(150)
        # select the correct option and submit -> green
        correct = page.evaluate("STUDY[0].questions[0].a")
        page.click(f".option:nth-child({correct + 1})")
        page.wait_for_timeout(80)
        page.click('#submit-btn')
        page.wait_for_timeout(250)
        page.screenshot(path=os.path.join(OUT, 'quiz_correct.png'), full_page=True)

        # go to next question, pick a WRONG option -> red
        page.click('#next-btn')
        page.wait_for_timeout(150)
        correct = page.evaluate("STUDY[0].questions[1].a")
        wrong = (correct + 1) % 4
        page.click(f".option:nth-child({wrong + 1})")
        page.wait_for_timeout(80)
        page.click('#submit-btn')
        page.wait_for_timeout(250)
        page.screenshot(path=os.path.join(OUT, 'quiz_wrong.png'), full_page=True)

        browser.close()
    print('screenshots:', os.listdir(OUT))


if __name__ == '__main__':
    main()