/* Project Study Companion — app logic.
   - Chapter-by-chapter scrolling with images
   - Per-chapter quiz (one question at a time; submit -> explain -> next)
   - Best score per question aggregates to the overall /100 (retakeable)
   - Prev/Next only appears when there is ahead/behind
   - Scroll friction (rubber-band resistance) + dynamic backdrop blur
   - Persistence: best scores + navigation progress (chapterIdx, mode, qIndex)
   - Free navigation: chapter jump dropdown + Free nav toggle */

(function () {
  "use strict";

  const $ = (s) => document.querySelector(s);
  const content = $("#content");
  const scrollRoot = $("#scroll-root");
  const titleEl = $("#top-title");
  const subheadEl = $("#subheading");
  const scoreEl = $("#top-score");
  const prevBtn = $("#prev-btn");
  const nextBtn = $("#next-btn");
  const submitBtn = $("#submit-btn");
  const bottombar = $("#bottombar");
  const chapterJump = $("#chapter-jump");
  const freeNavToggle = $("#free-nav-toggle");
  const resumeBadge = $("#resume-badge");

  // ---------- Persistence of best scores (versioned, handles corrupt JSON) ----------
  const BEST_KEY = "studyCompanionBest";
  const BEST_KEY_V1 = "studyCompanionBest_v1";
  const PROGRESS_KEY = "studyCompanionProgress";
  const PROGRESS_KEY_V1 = "studyCompanionProgress_v1";
  const PROGRESS_VERSION = 1;

  let best = {};
  function loadBest() {
    // try versioned key first, then legacy
    const keys = [BEST_KEY_V1, BEST_KEY];
    for (const k of keys) {
      try {
        const raw = localStorage.getItem(k);
        if (!raw) continue;
        const parsed = JSON.parse(raw);
        if (parsed && typeof parsed === "object" && !Array.isArray(parsed)) {
          best = parsed;
          // migrate to versioned key if came from legacy
          if (k === BEST_KEY) {
            try { localStorage.setItem(BEST_KEY_V1, JSON.stringify(best)); } catch (e) {}
          }
          return;
        }
      } catch (e) { /* corrupt -> try next */ }
    }
    best = {};
  }
  loadBest();
  function saveBest() {
    try {
      const payload = JSON.stringify(best);
      localStorage.setItem(BEST_KEY, payload);
      localStorage.setItem(BEST_KEY_V1, payload);
    } catch (e) {}
  }

  let chapterIdx = 0;       // current chapter index
  let mode = "read";        // "read" | "quiz" | "done"
  let qIndex = 0;           // current question index within chapter
  let selected = null;      // selected option index
  let answered = null;      // { ok, chosen } after submit
  let freeNavEnabled = false;
  let restoredFromProgress = false;

  const TOTAL_QUESTIONS = STUDY.reduce((n, ch) => n + ch.questions.length, 0);

  // ---------- Progress persistence ----------
  function saveProgress() {
    try {
      const payload = {
        v: PROGRESS_VERSION,
        chapterIdx,
        mode,
        qIndex,
        selected,
        answered,
        freeNav: freeNavEnabled
      };
      const s = JSON.stringify(payload);
      localStorage.setItem(PROGRESS_KEY, s);
      localStorage.setItem(PROGRESS_KEY_V1, s);
    } catch (e) {}
  }

  function loadProgress() {
    const keys = [PROGRESS_KEY_V1, PROGRESS_KEY];
    for (const k of keys) {
      try {
        const raw = localStorage.getItem(k);
        if (!raw) continue;
        const data = JSON.parse(raw);
        if (!data || typeof data !== "object") continue;
        // version check: allow missing v (legacy) or matching version
        // clamp chapterIdx
        let cIdx = Number(data.chapterIdx);
        if (!Number.isFinite(cIdx)) continue;
        cIdx = Math.max(0, Math.min(STUDY.length - 1, Math.floor(cIdx)));
        let m = data.mode;
        if (m !== "read" && m !== "quiz" && m !== "done") m = "read";
        let qi = Number(data.qIndex);
        if (!Number.isFinite(qi)) qi = 0;
        const ch = STUDY[cIdx];
        if (ch && ch.questions && ch.questions.length) {
          qi = Math.max(0, Math.min(ch.questions.length - 1, Math.floor(qi)));
        } else {
          qi = 0;
        }
        let sel = data.selected;
        if (sel !== null && sel !== undefined) {
          sel = Number(sel);
          if (!Number.isFinite(sel) || sel < 0 || sel >= 6) sel = null;
        } else sel = null;
        let ans = data.answered;
        // answered can be null or {ok, chosen}
        if (ans !== null && ans !== undefined) {
          if (typeof ans === "object" && typeof ans.ok === "boolean" && Number.isFinite(Number(ans.chosen))) {
            ans = { ok: !!ans.ok, chosen: Number(ans.chosen) };
          } else if (ans === true || ans === false) {
            // legacy bool -> keep minimal
            ans = null;
          } else {
            ans = null;
          }
        } else ans = null;
        const fn = !!data.freeNav;
        // migrate to versioned key
        if (k === PROGRESS_KEY) {
          try { localStorage.setItem(PROGRESS_KEY_V1, JSON.stringify({ v: PROGRESS_VERSION, chapterIdx: cIdx, mode: m, qIndex: qi, selected: sel, answered: ans, freeNav: fn })); } catch (e) {}
        }
        return { chapterIdx: cIdx, mode: m, qIndex: qi, selected: sel, answered: ans, freeNav: fn };
      } catch (e) { continue; }
    }
    return null;
  }

  // ---------- Chapter jump dropdown ----------
  function populateChapterJump() {
    if (!chapterJump) return;
    chapterJump.innerHTML = "";
    STUDY.forEach((ch, idx) => {
      const opt = document.createElement("option");
      opt.value = String(idx);
      opt.textContent = (idx + 1) + ". " + ch.title;
      chapterJump.appendChild(opt);
    });
    chapterJump.value = String(chapterIdx);
  }

  function syncChapterJump() {
    if (chapterJump) chapterJump.value = String(chapterIdx);
  }

  if (chapterJump) {
    chapterJump.addEventListener("change", () => {
      const idx = Number(chapterJump.value);
      if (!Number.isFinite(idx) || idx < 0 || idx >= STUDY.length) return;
      chapterIdx = idx;
      mode = "read";
      selected = null; answered = null;
      qIndex = 0;
      renderChapter();
      // progress saved inside renderChapter
      if (resumeBadge) {
        resumeBadge.hidden = true;
        resumeBadge.textContent = "";
      }
    });
  }

  if (freeNavToggle) {
    freeNavToggle.addEventListener("change", () => {
      freeNavEnabled = !!freeNavToggle.checked;
      saveProgress();
      updateButtons();
      // update next label immediately
      if (mode === "read") {
        // keep user on same chapter but refresh button labels
        updateButtons();
      }
    });
  }

  // ---------- Aggregated score (best per question) ----------
  function totalCorrect() {
    let n = 0;
    STUDY.forEach((ch, cid) => {
      const b = best[String(ch.id)] || {};
      for (let i = 0; i < ch.questions.length; i++) if (b[i]) n++;
    });
    return n;
  }
  function updateScore() {
    const t = totalCorrect();
    scoreEl.textContent = t + "/" + TOTAL_QUESTIONS;
    scoreEl.hidden = false;
  }
  function chapterCorrect(cid) {
    const ch = STUDY[cid];
    const b = best[String(ch.id)] || {};
    let n = 0;
    for (let i = 0; i < ch.questions.length; i++) if (b[i]) n++;
    return n;
  }

  // ---------- Rendering ----------
  function renderChapter() {
    mode = "read";
    selected = null; answered = null;
    const ch = STUDY[chapterIdx];
    titleEl.textContent = ch.title;
    subheadEl.textContent = ch.heading;
    content.innerHTML = "";
    ch.sections.forEach((sec) => {
      if (sec.type === "body") {
        const p = document.createElement("p");
        p.className = "body";
        p.textContent = sec.text;
        content.appendChild(p);
      } else if (sec.type === "image") {
        const fig = document.createElement("figure");
        const img = document.createElement("img");
        img.src = sec.src;
        img.alt = sec.caption || "figure";
        fig.appendChild(img);
        const cap = document.createElement("figcaption");
        cap.textContent = sec.caption || "";
        fig.appendChild(cap);
        content.appendChild(fig);
      }
    });
    const intro = document.createElement("p");
    intro.className = "body";
    intro.style.marginTop = "12px";
    const done = chapterCorrect(chapterIdx);
    intro.textContent = `Read this chapter, then tap Next to answer its quiz. So far: ${done}/${ch.questions.length} correct.`;
    content.appendChild(intro);
    // when freeNav is ON and user is on a later chapter, offer a quick "Start quiz" helper
    if (freeNavEnabled) {
      const quizBtn = document.createElement("button");
      quizBtn.className = "nav-btn primary";
      quizBtn.type = "button";
      quizBtn.textContent = "Take quiz";
      quizBtn.style.marginTop = "8px";
      quizBtn.addEventListener("click", () => {
        mode = "quiz";
        qIndex = 0;
        selected = null; answered = null;
        renderQuiz();
      });
      content.appendChild(quizBtn);
    }
    updateButtons();
    syncChapterJump();
    saveProgress();
    scrollRoot.scrollTop = 0;
  }

  function renderQuiz() {
    mode = "quiz";
    // do NOT reset selected/answered if we are restoring a answered state outside; caller controls
    // For normal entry, selected/answered already cleared by caller
    // Ensure mode is quiz (fix legacy bug where it wrote to `screen`)
    const ch = STUDY[chapterIdx];
    titleEl.textContent = "Question " + (qIndex + 1);
    subheadEl.textContent = ch.heading;
    const chCorrect = chapterCorrect(chapterIdx);
    const score = totalCorrect();
    content.innerHTML = "";

    const meta = document.createElement("p");
    meta.className = "q-meta";
    meta.innerHTML = chCorrect + " OUT OF " + ch.questions.length + ". <span class='correct'>" +
      score + "/" + TOTAL_QUESTIONS + "</span>";
    content.appendChild(meta);

    const q = ch.questions[qIndex];
    const qt = document.createElement("h2");
    qt.className = "q-title";
    qt.textContent = q.q;
    content.appendChild(qt);

    const optsWrap = document.createElement("div");
    optsWrap.className = "options";
    const letters = ["A", "B", "C", "D", "E", "F"];
    q.opts.forEach((opt, i) => {
      const btn = document.createElement("button");
      btn.className = "option";
      btn.type = "button";
      const tag = document.createElement("span");
      tag.className = "tag";
      tag.textContent = letters[i] + ".";
      const txt = document.createElement("span");
      txt.className = "opt-text";
      txt.textContent = opt;
      btn.appendChild(tag);
      btn.appendChild(txt);
      // restore selected visual if reloading
      if (selected !== null && selected === i && !answered) {
        btn.classList.add("selected");
      }
      btn.addEventListener("click", () => onSelect(i, btn));
      optsWrap.appendChild(btn);
    });
    content.appendChild(optsWrap);

    const expBox = document.createElement("div");
    expBox.className = "explanation";
    expBox.hidden = true;
    const expP = document.createElement("p");
    expP.className = "body";
    expP.textContent = "";
    expBox.appendChild(expP);
    content.appendChild(expBox);
    content._expBox = expBox;
    content._expP = expP;

    // if restoring an answered state, re-apply correct/wrong UI and explanation without overwriting best
    if (answered) {
      const opts = optsWrap.querySelectorAll(".option");
      opts.forEach((o, i) => {
        o.classList.add("locked");
        if (i === q.a) o.classList.add("correct");
        else if (i === answered.chosen) o.classList.add("wrong");
        if (i === answered.chosen) o.classList.add("selected");
      });
      const box = expBox;
      const p = expP;
      const letter = ["A", "B", "C", "D", "E", "F"][q.a];
      p.textContent = "The correct answer was option " + letter.toLowerCase() + ", " + q.opts[q.a] +
        ". " + q.exp;
      box.hidden = false;
    }

    updateButtons();
    syncChapterJump();
    saveProgress();
    scrollRoot.scrollTop = 0;
  }

  function onSelect(i, btn) {
    if (answered) return;
    selected = i;
    document.querySelectorAll(".option").forEach((o) => o.classList.remove("selected"));
    btn.classList.add("selected");
    // persist selection so reload restores chosen option (even before submit)
    saveProgress();
  }

  function submit() {
    if (answered) return;
    if (selected === null) return;
    const q = STUDY[chapterIdx].questions[qIndex];
    const ok = selected === q.a;
    answered = { ok, chosen: selected };

    const opts = document.querySelectorAll(".option");
    const ch = STUDY[chapterIdx];
    const b = best[String(ch.id)] || {};
    // only record best once per question, never downgrade a correct to incorrect
    if (b[qIndex] !== true) {
      // if already true keep true; if undefined/false and ok true, set true; else if ok false keep false/undefined? preserve true only
      if (ok) { b[qIndex] = true; }
      else if (b[qIndex] === undefined) { b[qIndex] = false; }
      best[String(ch.id)] = b; saveBest(); updateScore();
    } else {
      // already true, no change
    }

    opts.forEach((o, i) => {
      o.classList.add("locked");
      if (i === q.a) o.classList.add("correct");
      else if (i === selected) o.classList.add("wrong");
    });

    const box = content._expBox;
    const p = content._expP;
    const letter = ["A", "B", "C", "D", "E", "F"][q.a];
    p.textContent = "The correct answer was option " + letter.toLowerCase() + ", " + q.opts[q.a] +
      ". " + q.exp;
    box.hidden = false;

    // After answering, Next advances; submit hides, next becomes primary
    submitBtn.hidden = true;
    nextBtn.hidden = false;
    nextBtn.disabled = false;
    nextBtn.textContent = qIndex === STUDY[chapterIdx].questions.length - 1 ? "Finish" : "Next";
    saveProgress();
  }

  // ---------- Navigation & button visibility ----------
  function updateButtons() {
    if (mode === "read") {
      prevBtn.hidden = !(chapterIdx > 0);
      // Free nav: prev always visible where applicable (same as read logic) – keep simple
      nextBtn.hidden = false;
      nextBtn.disabled = false;
      if (freeNavEnabled) {
        nextBtn.textContent = chapterIdx === STUDY.length - 1 ? "Finish" : "Next chapter";
      } else {
        nextBtn.textContent = "Next";
      }
      submitBtn.hidden = true;
    } else if (mode === "quiz") {
      if (freeNavEnabled) {
        // allow moving freely: show Prev (back to chapter) and Next even before answering
        prevBtn.hidden = false;
        prevBtn.textContent = "Back";
      } else {
        prevBtn.hidden = true;
      }
      if (answered === null) {
        submitBtn.hidden = false;
        submitBtn.textContent = "Submit";
        if (freeNavEnabled) {
          // free nav: Next is visible but acts as Skip
          nextBtn.hidden = false;
          nextBtn.disabled = false;
          nextBtn.textContent = "Skip";
        } else {
          nextBtn.hidden = true;
          nextBtn.disabled = true;
        }
      } else {
        submitBtn.hidden = true;
        nextBtn.hidden = false;
        nextBtn.disabled = false;
        nextBtn.textContent = qIndex === STUDY[chapterIdx].questions.length - 1 ? "Finish" : "Next";
        if (freeNavEnabled) prevBtn.hidden = false;
      }
    } else {
      // done
      prevBtn.hidden = true;
      submitBtn.hidden = true;
      nextBtn.hidden = true;
      nextBtn.disabled = true;
    }
  }

  function renderDone() {
    mode = "done";
    selected = null; answered = null;
    titleEl.textContent = "All done";
    subheadEl.textContent = "Complete";
    const t = totalCorrect();
    content.innerHTML = "";
    const box = document.createElement("div");
    box.className = "result-box";
    const big = document.createElement("div");
    big.className = "big";
    big.innerHTML = t + "/" + TOTAL_QUESTIONS + " <span class='green'>" + t + "</span>";
    box.appendChild(big);
    const sub = document.createElement("div");
    sub.className = "sub";
    sub.textContent = "Retake any chapter to improve your score — best answers are kept.";
    box.appendChild(sub);
    const btn = document.createElement("button");
    btn.className = "nav-btn full";
    btn.type = "button";
    btn.textContent = "Start again";
    btn.addEventListener("click", () => { chapterIdx = 0; mode = "read"; qIndex = 0; selected = null; answered = null; renderChapter(); if (resumeBadge) { resumeBadge.hidden = true; resumeBadge.textContent = ""; } });
    box.appendChild(btn);
    content.appendChild(box);
    updateButtons();
    syncChapterJump();
    saveProgress();
    scrollRoot.scrollTop = 0;
  }

  prevBtn.addEventListener("click", () => {
    if (mode === "read" && chapterIdx > 0) {
      chapterIdx--;
      // keep read mode, reset quiz indices
      qIndex = 0; selected = null; answered = null;
      renderChapter();
      if (resumeBadge) { resumeBadge.hidden = true; resumeBadge.textContent = ""; }
    } else if (mode === "quiz" && freeNavEnabled) {
      // free nav: back to read of same chapter, preserve qIndex for return
      mode = "read";
      selected = null; answered = null;
      renderChapter();
    }
  });

  nextBtn.addEventListener("click", () => {
    if (mode === "read") {
      if (freeNavEnabled) {
        // free nav: skip quiz, go to next chapter directly
        if (chapterIdx < STUDY.length - 1) {
          chapterIdx++;
          qIndex = 0; selected = null; answered = null;
          renderChapter();
        } else {
          renderDone();
        }
        if (resumeBadge) { resumeBadge.hidden = true; resumeBadge.textContent = ""; }
      } else {
        mode = "quiz";
        qIndex = 0;
        selected = null; answered = null;
        renderQuiz();
      }
    } else if (mode === "quiz") {
      // if not answered and freeNav disabled, ignore
      if (!answered && !freeNavEnabled) return;
      // if freeNav and not answered, treat as skip (no best update)
      if (!answered && freeNavEnabled) {
        // skip without grading: clear selection/answered and advance
        selected = null; answered = null;
      }
      const ch = STUDY[chapterIdx];
      if (qIndex < ch.questions.length - 1) {
        qIndex++;
        selected = null; answered = null;
        renderQuiz();
      } else if (chapterIdx < STUDY.length - 1) {
        chapterIdx++;
        qIndex = 0; selected = null; answered = null;
        renderChapter();
      } else {
        renderDone();
      }
      if (resumeBadge) { resumeBadge.hidden = true; resumeBadge.textContent = ""; }
    }
  });

  submitBtn.addEventListener("click", submit);

  // ---------- Scroll friction (rubber-band resistance at edges) ----------
  let isMacLikely = true; // ignored; we detect resistance and apply transform
  let nudge = 0;
  let nudgeTarget = 0;
  let raf = null;
  function applyNudge() {
    nudge += (nudgeTarget - nudge) * 0.18;
    if (Math.abs(nudge) < 0.1 && Math.abs(nudgeTarget) < 0.1) { nudge = 0; }
    content.style.transform = "translateY(" + nudge.toFixed(2) + "px)";
    // spring back toward target continuously
    if (Math.abs(nudgeTarget) > 0.01 || Math.abs(nudge) > 0.01) {
      raf = requestAnimationFrame(applyNudge);
    } else { raf = null; }
  }
  function bounce(start) { nudgeTarget = start; if (!raf) raf = requestAnimationFrame(applyNudge); }
  function release() { nudgeTarget = 0; }

  scrollRoot.addEventListener("touchstart", () => { release(); }, { passive: true });
  scrollRoot.addEventListener("touchmove", (e) => {
    const el = scrollRoot;
    const atTop = el.scrollTop <= 0;
    const atBottom = el.scrollTop + el.clientHeight >= el.scrollHeight - 1;
    const delta = e.touches[0].clientY;
    // resistance when overscrolling past an edge
    if ((atTop && delta > 0) || (atBottom && delta < 0)) {
      const sign = atTop ? 1 : -1;
      nudgeTarget = sign * Math.min(28, Math.abs(nudgeTarget) + 2);
      if (!raf) raf = requestAnimationFrame(applyNudge);
    }
  }, { passive: true });
  scrollRoot.addEventListener("touchend", () => { release(); }, { passive: true });

  // ---------- Dynamic backdrop blur (low while scrolling fast) ----------
  let blurTimer = null;
  let lastY = 0;
  function onScroll() {
    const y = scrollRoot.scrollTop;
    const speed = Math.abs(y - lastY);
    lastY = y;
    // lower blur while moving (perf + smoothness), restore after 120ms idle
    const moving = speed > 16 ? 6 : 8;   // px while moving
    const idle = 18;                     // px when settled
    clearTimeout(blurTimer);
    if (speed > 16) {
      bottombar.style.setProperty("--accent-blur-base", moving + "px");
    }
    blurTimer = setTimeout(() => {
      bottombar.style.setProperty("--accent-blur-base", idle + "px");
    }, 120);
  }
  scrollRoot.addEventListener("scroll", onScroll, { passive: true });

  // ---------- Init with progress restore ----------
  updateScore();
  populateChapterJump();

  const saved = loadProgress();
  if (saved) {
    chapterIdx = saved.chapterIdx;
    mode = saved.mode;
    qIndex = saved.qIndex;
    selected = saved.selected;
    answered = saved.answered;
    freeNavEnabled = !!saved.freeNav;
    if (freeNavToggle) freeNavToggle.checked = freeNavEnabled;
    syncChapterJump();
    restoredFromProgress = !(chapterIdx === 0 && mode === "read" && qIndex === 0 && !answered);
    if (restoredFromProgress && resumeBadge) {
      resumeBadge.hidden = false;
      const ch = STUDY[chapterIdx];
      if (mode === "quiz") {
        resumeBadge.textContent = "Resumed: Ch " + (chapterIdx + 1) + " · Q" + (qIndex + 1) + (answered ? " · answered" : "");
      } else if (mode === "done") {
        resumeBadge.textContent = "Resumed: Complete";
      } else {
        resumeBadge.textContent = "Resumed: Ch " + (chapterIdx + 1) + " · " + ch.title;
      }
      // auto-hide after 4s but keep accessible
      setTimeout(() => { if (resumeBadge) resumeBadge.hidden = true; }, 4000);
    }
    // clamp validation already done; render appropriate mode
    if (mode === "quiz") {
      // ensure qIndex valid for chapter
      const ch = STUDY[chapterIdx];
      if (qIndex >= ch.questions.length) qIndex = ch.questions.length - 1;
      renderQuiz();
      // if we restored answered, renderQuiz already showed it; need to ensure buttons reflect correctly
      // saveProgress again to normalize v
      saveProgress();
    } else if (mode === "done") {
      renderDone();
    } else {
      mode = "read";
      renderChapter();
    }
  } else {
    if (freeNavToggle) freeNavToggle.checked = false;
    renderChapter();
  }
})();
