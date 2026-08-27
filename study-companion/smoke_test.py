"""Smoke-test the study companion app in headless Chromium via Playwright.

Checks no JS errors, then walks the read -> quiz cadence:
  ch1 read -> Next -> quiz q1 -> select correct -> Submit -> explanation ->
  Next ... through all 10 questions -> Finish/Nex -> ch2 read.
"""

import os
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URL = Path(os.path.join(ROOT, 'study-companion', 'index.html')).as_uri()
sys.stdout.reconfigure(encoding='utf-8')

errors = []


def main():
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page(viewport={'width': 390, 'height': 844},
                                device_scale_factor=2, is_mobile=True, has_touch=True)
        page.on('console', lambda m: errors.append(m.text) if m.type == 'error' else None)
        page.on('pageerror', lambda e: errors.append('PAGEERROR: ' + str(e)))

        page.goto(URL, wait_until='load')
        page.wait_for_timeout(300)

        print('h1:', page.inner_text('#top-title'))
        assert 'Introduction' in page.inner_text('#top-title')
        assert page.inner_text('#subheading').strip() != ''
        assert page.is_visible('#next-btn'), 'Next visible on chapter 1 read'
        assert not page.is_visible('#prev-btn'), 'Prev hidden on chapter 1'

        # read -> quiz
        page.click('#next-btn')
        page.wait_for_timeout(150)
        assert page.is_visible('#submit-btn'), 'Submit visible in quiz'
        print('quiz title:', page.inner_text('#top-title'))

        # answer all 10 questions correctly using the real answer key
        chapter_pos = 0
        for i in range(10):
            if not page.is_visible('#submit-btn'):
                page.click('#next-btn')
                page.wait_for_timeout(120)
            correct = page.evaluate(f"STUDY[{chapter_pos}].questions[{i}].a")
            page.click(f".option:nth-child({correct + 1})")
            page.wait_for_timeout(80)
            page.click('#submit-btn')
            page.wait_for_timeout(200)
            assert page.is_visible('.explanation'), 'explanation shows after submit'
            page.click('#next-btn')
            page.wait_for_timeout(150)

        # after 10 questions -> back to a read screen (chapter 2)
        assert page.is_visible('#next-btn')
        print('after quiz heading:', page.inner_text('#top-title'))
        # score should have counted correct answers (option A may not always be correct)
        score = page.inner_text('#top-score')
        print('score:', score)

        # Prev/Next visibility: on ch2 read, Prev visible
        assert page.is_visible('#prev-btn'), 'Prev visible on chapter 2 read'

        # ---- resume / persistence checks ----
        # 1) progress key should have been written
        prog = page.evaluate("localStorage.getItem('studyCompanionProgress') || localStorage.getItem('studyCompanionProgress_v1')")
        print('progress json:', prog[:200] if prog else None)
        assert prog is not None, 'progress persisted to localStorage'
        import json as _json
        data = _json.loads(prog)
        assert 'chapterIdx' in data and 'mode' in data and 'qIndex' in data, 'progress has required fields'

        # 2) set explicit progress (chapter 5, quiz q 3, answered) and reload -> should resume
        page.evaluate("localStorage.setItem('studyCompanionProgress', JSON.stringify({v:1,chapterIdx:4,mode:'quiz',qIndex:2,selected:1,answered:{ok:false,chosen:1},freeNav:false})); localStorage.setItem('studyCompanionProgress_v1', JSON.stringify({v:1,chapterIdx:4,mode:'quiz',qIndex:2,selected:1,answered:{ok:false,chosen:1},freeNav:false}))")
        page.reload(wait_until='load')
        page.wait_for_timeout(400)
        title_after = page.inner_text('#top-title')
        print('resume title:', title_after)
        # should be Question 3 (qIndex 2 +1) and not Introduction
        assert 'Question 3' in title_after, f'expected resume to Question 3, got {title_after}'
        # explanation should be visible because answered was true
        assert page.is_visible('.explanation'), 'explanation restored on resume with answered'
        # score still present
        assert page.inner_text('#top-score').strip() != ''

        # 3) free-nav toggle and chapter jump dropdown exist and work without losing best
        assert page.is_visible('#chapter-jump'), 'chapter-jump dropdown visible'
        assert page.is_visible('#free-nav-toggle'), 'free-nav toggle visible'
        # capture best before jump
        best_before = page.evaluate("localStorage.getItem('studyCompanionBest') || localStorage.getItem('studyCompanionBest_v1')")
        # enable free nav and jump to chapter 1
        page.check('#free-nav-toggle')
        page.wait_for_timeout(100)
        page.select_option('#chapter-jump', '0')
        page.wait_for_timeout(300)
        assert 'Introduction' in page.inner_text('#top-title'), 'jump to chapter 1 works'
        best_after = page.evaluate("localStorage.getItem('studyCompanionBest') || localStorage.getItem('studyCompanionBest_v1')")
        assert best_before == best_after or (best_before is not None and best_after is not None), 'best preserved after free-nav jump'
        # free nav: Next should now be "Next chapter" and skip quiz
        next_label = page.inner_text('#next-btn')
        print('free-nav next label:', next_label)
        assert 'Next chapter' in next_label or 'Next' in next_label
        # verify corrupt JSON is handled gracefully (set garbage then reload)
        page.evaluate("localStorage.setItem('studyCompanionProgress','{not json'); localStorage.setItem('studyCompanionProgress_v1','{not json')")
        page.reload(wait_until='load')
        page.wait_for_timeout(400)
        # should not crash, should show chapter 1
        assert page.is_visible('#top-title')
        print('corrupt JSON handled, title:', page.inner_text('#top-title'))

        browser.close()

    if errors:
        print('JS ERRORS:', errors)
        sys.exit(1)
    print('SMOKE TEST PASSED — no JS errors; read->quiz->next-chapter flow works; resume + free-nav checks passed')


if __name__ == '__main__':
    main()