/* Project Study Companion — VIVA PREPARATION content.
   5 chapters, 40 self-test questions, retakeable.
   Repurposed from a revision quiz into consultant-grade defence prep for the
   MSc project "Steganographic Signing and Filter Traceability in Digital Media".
   Every number is drawn from FPR v3.1 and the Viva Briefing. */

const STUDY = [
  /* ================= Chapter 1 ================= */
  {
    id: 1, title: "The Narrative", heading: "What did we do, why, and how? (FPR 1, 3, 4)",
    sections: [
      { type: "body", text: "WHAT. I built an auditable benchmarking framework that measures how well verification signals survive the everyday transformations an image goes through online, then added my own two-layer recovery channel on top and wrapped it in a dashboard. On 1,200 deterministically selected MS-COCO 2017 validation images I applied twelve transform families across eighty named conditions and ran four pipelines: TrustMark (a neural watermark), two deliberately simple classical baselines (LSB and DCT), and eight perceptual hash variants including the 256-bit PDQ. That is 768,000 hash rows and 97,200 rows per watermark method." },
      { type: "image", src: "assets/fpr_transform_taxonomy.png", caption: "The benchmark maps a fixed set of named image operations onto a fixed sample, then measures how each verification signal survives." },
      { type: "body", text: "WHY. Because provenance claims are easy to overstate. When a platform recompresses or crops an image the metadata is stripped, the pixels change and the cryptographic digest breaks, yet the image is still recognisably the same image. Four different questions keep getting blurred together: is this image similar to a reference, can I recover a hidden message, is it byte-for-byte intact, and who signed it. I separated similarity, recovery, integrity and accountability, and measured honestly where each signal lives and where it dies. Misreading a similarity score as an authenticity guarantee causes real harm, so the whole framework is built around evidence discipline." },
      { type: "body", text: "RESEARCH QUESTION. To what extent do a neural watermark, perceptual hashes and classical watermarking baselines retain interpretable verification signal when images undergo graduated photometric, compression and geometric transformations, and how should that signal be reported without confusing recovery, similarity, integrity or provenance?" },
      { type: "body", text: "HOW. Everything runs through one shared module, transforms.py, the single source of truth for the twelve families and eighty conditions. Random operations derive their seeds deterministically from image ID, transform name and intensity via SHA-256, so any machine reconstructs the same transformed image. JPEG is genuinely written to disk and reopened, so we test the real codec. Ten validation gates guard coverage and duplicate keys, and a run that fails validation is never reported. For uncertainty the image is the statistical unit, with percentile bootstrap (2,000 resamples, seed 20260812) and Wilson intervals." },
      { type: "body", text: "THE HONEST EDGE. My interim proposal hypothesised over 90 percent recovery across JPEG and PNG. The measured two-layer JPEG figure is 85.6 percent and PNG was never implemented. That is reported as a non-confirmation, with the same prominence as the headline win, because the project's thesis is that inflated provenance claims are a professional failure." },
    ],
    questions: [
      { q: "In one sentence, what did you build?",
        opts: [
          "A new state-of-the-art neural watermark algorithm that beats TrustMark",
          "An auditable benchmarking framework measuring whether similarity and recovery signals survive 80 named image transforms, with a two-layer recovery channel and a dashboard",
          "A provenance certificate system for signing images",
          "A larger image dataset"
        ], a: 1,
        exp: "Say: an auditable benchmarking framework that measures whether similarity and watermark-recovery signals survive eighty named transforms, with my own two-layer recovery channel on top and a dashboard to demonstrate it. Everything is validated against a frozen 1,200-image manifest before any number is reported. (FPR 1.2, 4.12)" },
      { q: "What is the actual intellectual contribution?",
        opts: [
          "A faster hash function",
          "The evidence discipline (one transform module, deterministic seeding, ten validation gates, an evidence matrix), the two-layer channel lifting exact recovery from 60.73% to 67.28%, and honest boundary-work separating four constructs",
          "Outperforming WAVES on every transform",
          "Proving watermarks are unremovable"
        ], a: 1,
        exp: "Say: three things. First the evidence discipline: one transform module, deterministic seeding, ten validation gates and an evidence matrix binding each claim to a file, scale and permitted wording. Second the two-layer channel: TrustMark OR a BCH-coded DCT fallback, lifting exact recovery 60.73 to 67.28 percent over 96,000 observations. Third honest boundary-work, including a falsified hypothesis reported as such. (FPR 1.5)" },
      { q: "Why does the report separate four constructs: similarity, recovery, integrity and provenance?",
        opts: [
          "To make the report longer",
          "Because each requires different evidence and a different mechanism; conflating them produces over-claiming",
          "Because provenance is out of scope",
          "Because hashes cannot be compared"
        ], a: 1,
        exp: "Say: similarity needs a hash comparison, recovery needs a decoder, integrity needs a byte-exact binding, and provenance needs signatures and a trust chain. Blur them and you can accidentally present a similar-looking image as authentic. (FPR 1.1, 3.5, 5.1)" },
      { q: "What does a recovered watermark actually tell you, and what does it not?",
        opts: [
          "It proves the image is authentic",
          "It proves who created the image",
          "It tells you an embedded packet survived the tested transform; it does NOT establish similarity, integrity or provenance",
          "It is identical to a hash match"
        ], a: 2,
        exp: "Say: recovery is an observation that the payload persisted under named conditions. It is not similarity (the hash), not integrity (a cryptographic digest) and not provenance (a signed, accountable manifest). (FPR 1.1, 3.5)" },
      { q: "How is your work different from WAVES, the SoK paper, or Du et al.?",
        opts: [
          "It uses more images, so it is more authoritative",
          "It is not another attack benchmark; it is a complementary-signal framework where hashes, a neural watermark and classical baselines share one transform vocabulary with validation gates and construct separation",
          "It benchmarks more watermark algorithms",
          "It proves those papers wrong"
        ], a: 1,
        exp: "Say: WAVES and the SoK evaluate attack suites against methods, and Du surveys hash families. Mine is a complementary-signal framework under ONE shared transform vocabulary, with the validation gates and construct separation those papers argue for but often omit. I explicitly do not claim better algorithms. (FPR 2.4)" },
      { q: "Why did you falsify your hypothesis so openly? Would a win not score better?",
        opts: [
          "The hypothesis was quietly edited to match the results",
          "The promised >90% JPEG/PNG recovery measured 85.6% for JPEG and PNG was never implemented; reporting the non-confirmation IS the demonstration of the report's thesis about evidence discipline",
          "The hypothesis was confirmed at 99%",
          "The hypothesis did not matter"
        ], a: 1,
        exp: "Say: the hypothesis said above 90 percent across JPEG and PNG. Measured JPEG two-layer is 85.6 percent and PNG was never implemented, so it is a non-confirmation. Reporting that is the win here, because the whole argument is that inflated provenance claims are a professional failure. Claiming a hidden edit would contradict the framework's own thesis. (FPR 1.5, Table 2)" },
      { q: "What is the strongest single claim the project defends?",
        opts: [
          "Watermarking proves authenticity",
          "An auditable, transformation-aware framework whose claims are bounded by explicit evidence, plus a measured, targeted rescue channel",
          "A new watermark algorithm",
          "A provenance certificate service"
        ], a: 1,
        exp: "Say: the framework itself, because deterministic selection, row-level traceability, validation gates, corrected metrics and separate baselines are what survive scrutiny. The two-layer rescue is real but bounded, and I never claim more than the validated 1,200-image benchmark can support. (FPR 5.1-5.3)" },
      { q: "Where is the line between your work and real provenance?",
        opts: [
          "My dashboard is C2PA-compliant",
          "I evaluate soft-binding signals only; real provenance needs signing keys, certificate trust, identity policy and revocation, and I implemented a development Ed25519 manifest as a stated pattern only",
          "Provenance is just a watermark",
          "Provenance was fully implemented"
        ], a: 1,
        exp: "Say: the report is explicit that I evaluate soft-binding signals only. Real provenance needs key lifecycle, certificate trust, identity policy and revocation. I implemented a development Ed25519 manifest as a pattern, stated as development-level, and the evidence matrix even lists the permitted wording: signature valid under project development key. (FPR 2.2, Table 7)" },
    ],
  },

  /* ================= Chapter 2 ================= */
  {
    id: 2, title: "Code I'm Proud Of", heading: "Six functions I can demo and defend (Artefact)",
    sections: [
      { type: "body", text: "ITEM 1, deterministic seeding. transforms.py make_seed, lines 35-40, with the dispatcher at 165-180. It builds a seed for stochastic transforms from SHA-256 of image ID plus transform name plus intensity, and deliberately avoids Python's built-in hash(), which is randomised between processes. Say: this one function is why 96,000 benchmark rows are reproducible on any machine." },
      { type: "body", text: "ITEM 2, raw bit accuracy before ECC. trustmark_robustness.py decode_and_accuracy, lines 24-35, with the batched variant at 38-62. It taps TrustMark's decoder BEFORE error correction, records bit accuracy against the expected packet, then passes the same raw bits into the ECC decode. Say: this shows I audit metrics, not just run libraries; TrustMark mean raw accuracy is 85.17 percent while exact decode is 60.73 percent." },
      { type: "body", text: "ITEM 3, the fallback channel, my own contribution. fallback_watermark.py _block_positions lines 63-78, embed 108-131, decode 134-158, with the vectorised batch DCT at 47-61. Each payload bit is BCH_SUPER-coded into a 100-bit packet and repeated five times in interleaved 8x8 DCT blocks spread evenly over the image; decoding is majority vote then BCH. Dimension-changing transforms return a clean failure rather than decoding against a mismatched layout. Say: this decision avoids a false rescue." },
      { type: "body", text: "ITEM 4, hard validation gates. validate_experiment.py validate lines 19-27, main 31-42. It recomputes expected coverage, counts unique image IDs, detects duplicate composite keys and raises SystemExit on any mismatch. Say: a 100-image command cannot validate a 1,200-image file, so a partial run can never masquerade as a final result." },
      { type: "body", text: "ITEM 5, reproducible statistics. analyze_uncertainty.py bootstrap lines 133-141, Wilson 144-152, local RNG at 212, PDQ bit length 29 and 99-102, CLI guard 298-299, self-test 277-284. The image is the statistical unit, a local rng seeded 20260812 cannot be perturbed by other code, and the CLI refuses fewer than 100 resamples. Say: statistics you can rerun and defend." },
      { type: "body", text: "ITEM 6, provenance manifest. scripts/provenance_manifest.py sha256_file 40-46, canonical JSON 49-51, create_manifest 58-92, sign_manifest from 146, verify_manifest from 166. It binds a manifest to the image by SHA-256, signs canonical (sorted, compact) JSON with Ed25519, and verifies hash binding plus signature. Say: this connects soft signals to hard cryptographic binding, the same separation the report argues for conceptually." },
    ],
    questions: [
      { q: "Why not just use numpy default_rng with a fixed global seed?",
        opts: [
          "A global seed is faster",
          "A global seed breaks when parallel jobs or resumed runs reorder RNG consumption; hashing the image+condition pair makes each cell reproducible in isolation",
          "Global seeds are deprecated",
          "The dataset forbids it"
        ], a: 1,
        exp: "Say: a global seed breaks when parallel jobs or resumed runs reorder consumption. Hashing the image, transform and intensity pair makes each cell reproducible on its own, which is gate-level reproducibility by design. (transforms.py 35-40)" },
      { q: "A TrustMark row shows bit_accuracy 0.93 and decode_present false. What does that mean?",
        opts: [
          "The row is corrupt",
          "93% of raw bits matched, but error correction could not produce a valid message; the two metrics legitimately diverge",
          "The payload decoded perfectly",
          "The transform was skipped"
        ], a: 1,
        exp: "Say: raw accuracy and decode presence are different constructs. Raw bit accuracy measures signal agreement before ECC; decode presence is the end-to-end event after ECC. Conflating them is a construct error. (trustmark_robustness.py 24-35; FPR Table 4)" },
      { q: "DCT has 71.98% raw bit accuracy but only 15.26% recovery. What does that prove?",
        opts: [
          "DCT is the best method",
          "High bit agreement does not mean a message survived; bit accuracy and recovery measure different things",
          "Error correction is unnecessary",
          "The test was unfair"
        ], a: 1,
        exp: "Say: it proves the constructs diverge. High raw-bit agreement without crossing the ECC threshold yields almost no recovered messages, which is exactly why the report keeps them in separate columns. (FPR Table 8, Table 13)" },
      { q: "Why does the fallback fail cleanly on rotation and crop instead of trying harder?",
        opts: [
          "It is faster to fail",
          "The block layout is defined on full-size dimensions; a dimension-changing transform means returning a clean failure rather than decoding against a mismatched layout and manufacturing a false rescue",
          "Rotation is always benign",
          "The code has a bug"
        ], a: 1,
        exp: "Say: clean failure is deliberate failure engineering. The embedding layout presumes dimensions survived, so rotation, crop and letterbox fail honestly rather than producing a false decode. That is why the rescue is concentrated in dimension-preserving conditions. (fallback_watermark.py 63-78, 134-158)" },
      { q: "Could a corrupted or partially complete CSV get through your validation gate?",
        opts: [
          "Yes, the gate only checks file size",
          "No: rows, unique image count, expected rows and duplicate keys must all reconcile, and compressed output is integrity-checked before counting",
          "Yes, duplicates are ignored",
          "Only if the CSV is gzipped"
        ], a: 1,
        exp: "Say: not past this gate. It recomputes expected coverage as image count times conditions, counts unique IDs, and detects duplicate composite keys, then exits the run loudly. A partial run cannot masquerade as a final result. (validate_experiment.py 19-42)" },
      { q: "Why use Wilson intervals rather than Wald?",
        opts: [
          "Wilson is faster to compute",
          "Wilson intervals stay inside [0,1] and behave better near boundaries than the normal-approximation Wald",
          "Wald is proprietary",
          "They are identical"
        ], a: 1,
        exp: "Say: Wilson stays in the unit interval and behaves better near boundaries than the normal-approximation Wald. The reference is Kahouadji (2025), and the bootstrap cites Efron and Hastie (2016). (FPR 4.10)" },
      { q: "Is your provenance manifest C2PA?",
        opts: [
          "Yes, it is fully C2PA compliant",
          "No: it is a development Ed25519 key and manifest pattern only; real provenance needs key lifecycle, a trust chain and identity policy",
          "It is a watermark, so C2PA does not apply",
          "It replaces C2PA"
        ], a: 1,
        exp: "Say: no, and the report says so explicitly. C2PA requires key lifecycle, certificate trust and identity policy. Mine is a development Ed25519 manifest pattern, claimed at development level only. (scripts/provenance_manifest.py; FPR 2.2, Table 7)" },
      { q: "Why measure raw TrustMark bits before error correction rather than trusting exact-decode success?",
        opts: [
          "Because ECC is broken",
          "Because exact-decode success hides partial signal; measuring upstream of ECC is gate G5 and reveals how much signal actually survived",
          "Because it is faster",
          "Because decode presence is unreliable"
        ], a: 1,
        exp: "Say: exact decode success hides partial signal. Tapping the decoder before ECC is gate G5 and it changed the numbers: TrustMark mean raw bit accuracy 85.17 percent versus 60.73 percent exact decode. (trustmark_robustness.py 24-35; FPR Table 5)" },
    ],
  },

  /* ================= Chapter 3 ================= */
  {
    id: 3, title: "Figure Rationales", heading: "Why every number looks the way it does (FPR 4)",
    sections: [
      { type: "body", text: "RATIONALE 1, the full 0-100% axis. Recovery is a proportion, so the honest frame is the full scale. A truncated axis (say 55 to 75 percent) would make the +6.6-point gain look enormous and hide that geometric attacks still beat us. Figure 8 and Figure 5 show the whole scale deliberately. Say: axis truncation is a rhetoric choice, and I declined it." },
      { type: "body", text: "RATIONALE 2, percentages versus decimals. They are different constructs. Recovery (decode presence) is an end-to-end binary event reported as percentages of the 96,000 transformed observations (Tables 11-13). Raw bit accuracy is the fraction of expected packet bits recovered BEFORE error correction, reported as 0.xx (Table 8). Mixing formats would invite exactly the construct confusion the report exists to prevent." },
      { type: "body", text: "RATIONALE 3, the seed 20260812. The bootstrap is a random resampling procedure, so without a pinned seed the intervals wiggle on every rerun. 20260812 is arbitrary but public, essentially the analysis-freeze date (12 August 2026), recorded in output metadata so any rerun reproduces identical intervals. It is a mnemonic, not a claim about the data." },
      { type: "body", text: "RATIONALE 4, PDQ at 256 bits. PDQ's longer representation is normalised by bit length before comparison with the seven 64-bit hashes. The report also flags a real serialisation bug: PDQ had been stored as a multi-character representation per dimension instead of one bit, silently inflating every Hamming distance. Gate G4 forced a recompute and re-validation. Normalisation is necessary, but the report never claims PDQ is more robust because it is longer." },
      { type: "body", text: "RATIONALE 5, the non-confirmation kept prominent. The interim proposal predicted over 90 percent recovery across JPEG and PNG; measured two-layer JPEG is 85.6 percent, PNG was never implemented. Sections 1.5, 4.11 and Table 2 state this as a non-confirmation with the same prominence as the headline win. It is the answer to how you handle a falsified hypothesis: name it, quantify it, bound the claim." },
      { type: "body", text: "RATIONALE 6, image-level intervals. Eighty rows come from each image and are dependent. Treating 96,000 pooled rows as independent would overstate precision dramatically. So hash rows are first reduced per image-condition, and intervals span images. Decode proportions get Wilson intervals; continuous metrics get the percentile bootstrap. (FPR 4.10, Table 10)" },
    ],
    questions: [
      { q: "Why not truncate the axis to make the +6.6pp gain look bigger?",
        opts: [
          "Truncation would be better for impact",
          "A truncated axis would exaggerate the gain and hide that geometric attacks still beat us; the full 0-100% scale shows the gain is real but modest",
          "The charting library forbids it",
          "Truncation is impossible in the tool used"
        ], a: 1,
        exp: "Say: axis truncation is a rhetoric choice and I declined it. Recovery is a proportion, so the honest frame is the full 0-100 scale. The full scale shows the gain is real but modest, and that rotation, crops and letterbox remain near chance. (FPR Figure 5, Figure 8)" },
      { q: "Why do some tables use percentages and others decimals?",
        opts: [
          "It is a formatting inconsistency",
          "Recovery is a binary end-to-end event reported as percentages; raw bit accuracy is a pre-ECC fraction reported as 0.xx; they are different constructs and must not share a format",
          "Decimals are more accurate",
          "Percentages are only used for hashes"
        ], a: 1,
        exp: "Say: they are different constructs. Recovery is decode presence over the 96,000 transformed observations. Raw bit accuracy is the pre-ECC fraction. Mixing them would invite the construct confusion the report is built to prevent. (FPR Table 4, Table 13)" },
      { q: "Why is the bootstrap seed 20260812 and what does it mean?",
        opts: [
          "It encodes a statistical result",
          "It is an arbitrary public constant, the analysis-freeze date, pinned so intervals reproduce identically; it has no semantic meaning about the data",
          "It is the number of resamples",
          "It is the dataset version"
        ], a: 1,
        exp: "Say: the bootstrap is random, so without a pinned seed the intervals wiggle on every rerun. 20260812 is arbitrary but public, effectively the analysis-freeze date, recorded in metadata so anyone reproduces identical intervals. It is a mnemonic, not a claim about the data. (FPR 4.10; analyze_uncertainty.py 212)" },
      { q: "Why does PDQ being 256-bit matter?",
        opts: [
          "Longer hashes are always more robust",
          "Distances are normalised by bit length before comparing PDQ with the 64-bit hashes, and a serialisation bug where PDQ was stored per-dimension was fixed under gate G4",
          "PDQ is the only hash used",
          "256-bit means it cannot be attacked"
        ], a: 1,
        exp: "Say: PDQ is 256-bit while the other seven are 64-bit, so distances must be normalised by bit length. There was also a real bug: PDQ had been stored as multi-character per dimension, which silently inflated distances. Gate G4 forced a recompute, but I never claim PDQ is more robust because it is longer. (analyze_uncertainty.py 29, 99-102; FPR 2.2)" },
      { q: "Why give the falsified hypothesis as much space as the win?",
        opts: [
          "Because it failed and failure is more interesting",
          "Because hiding it would destroy the project's thesis of evidence discipline; a non-confirmation reported plainly is worth more than a quietly edited target",
          "Because the hypothesis was never important",
          "Because the marker required it"
        ], a: 1,
        exp: "Say: the whole argument is that inflated provenance claims are a professional failure. Hiding the 85.6 percent non-confirmation would contradict that thesis. Naming it, quantifying it and bounding the claim is the demonstration. (FPR 1.5, 4.11, Table 2)" },
      { q: "Why is the image the statistical unit rather than the row?",
        opts: [
          "Because there are fewer images",
          "Because 80 rows come from each image and are dependent; pooling 96,000 rows as independent would overstate precision, so rows are reduced per image-condition first",
          "Because rows are duplicates",
          "Because the bootstrap requires it"
        ], a: 1,
        exp: "Say: eighty rows per image are dependent. Treating 96,000 pooled rows as independent would overstate confidence dramatically, so I reduce per image-condition and span images with intervals: Wilson for decode proportions, percentile bootstrap for continuous metrics. (FPR 4.10, Table 10)" },
      { q: "What does Table 13 deliberately keep in separate columns?",
        opts: [
          "Pilot and final results",
          "Recovery percentages and raw bit accuracy, with the recovery column marked not applicable for the hybrid, so bit accuracy is never read as recovery",
          "Hashes and watermarks",
          "Per-image and per-transform results"
        ], a: 1,
        exp: "Say: Table 13 puts 67.28, 60.73, 15.26 and 4.90 percent recovery on one side and raw bit accuracy on the other, with a caption stating accuracy does not imply recovery. It is the designed answer to 'bit accuracy is not recovery'. (FPR 4.12, Table 13)" },
      { q: "What is the correct way to read the JPEG quality ladder?",
        opts: [
          "As one JPEG average",
          "Per quality setting, because degradation is non-monotonic and the q10 irregularity would be invisible in a single average",
          "As proof the fallback is immune to JPEG",
          "As a security boundary"
        ], a: 1,
        exp: "Say: per setting, because the behaviour is not monotonic. Quality 5 goes 2.7 to 69.7 percent, quality 20 goes 42.3 to 93.1 percent, but quality 10 dips to 32.2 percent, and that irregularity would be hidden by a single average. (FPR 4.11, Table 12)" },
    ],
  },

  /* ================= Chapter 4 ================= */
  {
    id: 4, title: "Probable Viva Questions", heading: "Fifteen questions and spoken answers (FPR 1-5)",
    sections: [
      { type: "body", text: "This chapter turns the fifteen probable viva questions into self-tests. For each, one option is the spoken model answer and the others are mistakes a nervous candidate might make. Read the explanation as the answer you would actually say aloud." },
      { type: "body", text: "Pattern for every answer: name the construct, give the number, point to the evidence. 'Recovery is X because Y, validated at 1,200 images, Table N.' Never let a number float without its denominator and source." },
    ],
    questions: [
      { q: "What would you do differently if you started again?",
        opts: [
          "Nothing, it went perfectly",
          "Register geometry from day one with a synchronisation arm, and plan calibration earlier so thresholds are operating points; both are listed as future work, not pretended as done",
          "Use more images",
          "Use a different dataset"
        ], a: 1,
        exp: "Say: two things. First, register geometry from day one, adding a synchronisation arm of no-alignment, oracle and estimated, rather than discovering at the end that rotation and crop defeat the fallback. Second, plan calibration earlier: negative pairs, wrong-payload trials and a declared split, so thresholds become operating points. (FPR 4.9, 5.7)" },
      { q: "Is 67.3% recovery actually useful?",
        opts: [
          "Yes, it is deployment-ready proof of authenticity",
          "Yes as a screening signal under benign transforms, no as an authenticity verdict; it must be calibrated against false acceptance before deployment and geometry remains near chance",
          "No, 67% is useless",
          "Only for TrustMark"
        ], a: 1,
        exp: "Say: as a screening signal under benign transforms, yes. As a deployed authenticity verdict, no, and the report never claims that. The gain is concentrated where recompression and value-level edits dominate real pipelines, but it needs calibration against false acceptance first. (FPR 4.11-4.12, 4.5)" },
      { q: "Explain the quality-10 JPEG irregularity.",
        opts: [
          "It is a measurement error",
          "Recovery is not monotonic: at quality 10 the fallback underperforms its own quality-5 result, a codec-quantisation interaction that was reported openly rather than smoothed away",
          "Quality 10 is the best case",
          "The fallback is immune to JPEG"
        ], a: 1,
        exp: "Say: recovery does not degrade monotonically. At quality 10 the fallback underperforms its own quality-5 figure, because different quantisation scale factors interact. The honest move was to report the anomaly and decline first-crossing-only smoothing. (FPR 4.11)" },
      { q: "How would a determined attacker beat your system?",
        opts: [
          "They could not, because the watermark is cryptographic",
          "The threat model covers informed, black-box and white-box attackers; adaptive removal is explicitly out of scope, and the correct security statement is screened under named benign and careless conditions",
          "By changing the image format",
          "By reading the slide deck"
        ], a: 1,
        exp: "Say: the threat model covers informed, black-box and white-box attackers, but the benchmark only covers benign and careless operations. An adaptive regeneration attacker is explicitly out of scope, so the correct statement is screened under named benign and careless conditions, reported exactly that way. (FPR 3.9)" },
      { q: "Why TrustMark and not RoSteALS, Stable Signature or StegaStamp?",
        opts: [
          "TrustMark is the only published method",
          "It is a published strong neural candidate with feasible version pinning (0.9.1, model Q); the report reviews alternatives and does not claim to beat them, and the same pipeline would host any of them unchanged",
          "TrustMark is the fastest",
          "The others are unimplemented"
        ], a: 1,
        exp: "Say: TrustMark is a published strong neural candidate and version pinning was feasible. The report reviews the alternatives but does not claim to beat them. The contribution is the framework; the neural method is the chosen candidate, and the pipeline would host RoSteALS or Stable Signature unchanged. (FPR 2.1)" },
      { q: "Walk me through the validation gates.",
        opts: [
          "There is one gate on file size",
          "Ten gates, G1-G10, covering manifest checksums, coverage, duplicate keys, PDQ serialisation, raw TrustMark bits before ECC, ranges and dimensions, transform drift, figure regeneration, interval method and report reconciliation; two are fully code-enforced and Table 6 marks each honestly including partial enforcement",
          "The gates are all manual",
          "Validation is done by the dataset provider"
        ], a: 1,
        exp: "Say: ten gates, G1 to G10. Two are fully enforced in code, validate_experiment.py and analyze_uncertainty.py; the rest are corrected code or manual review, and Table 6 marks each honestly, including partially enforced where that is the truth. (FPR 3.6, Tables 5-6)" },
      { q: "What about ethics and legal exposure?",
        opts: [
          "None, the dataset is public",
          "No human participants, but public images may contain people and payloads must never carry real identifiers (fixed test payloads only); misuse, copyright and false-association risks are in the risk matrix with residual concerns flagged, and the dashboard stays local",
          "Ethics approval was rejected",
          "Only the watermarking is a concern"
        ], a: 1,
        exp: "Say: no participants, but public images may contain people and payloads must never carry real identifiers, so only fixed test payloads are used. Surveillance misuse, copyright overreach and false associations are in the threat and risk matrix with residual concerns flagged. The dashboard stays local. (FPR 3.10, 5.4, Appendix F)" },
      { q: "A recovered watermark proves the image is genuine, right?",
        opts: [
          "Yes, always",
          "Yes if bit accuracy is 100%",
          "No: recovery is signal persistence, not an authenticity verdict; provenance needs signed manifests, keys and a trust chain that are out of scope",
          "Only for the hybrid"
        ], a: 2,
        exp: "Say: no. Recovery establishes that the payload survived the transform; authenticity would require provenance infrastructure, signed manifests, key management and a trust chain, which are explicitly out of scope. Presenting an uncalibrated decode as a probability of authenticity would be the exact over-claim the project argues against. (FPR 1.1, 3.5, 5.1)" },
      { q: "Walk me through the +6.6 percentage-point gain.",
        opts: [
          "The hybrid is better everywhere by a uniform margin",
          "Denominator first: 96,000 transformed observations. TrustMark alone decodes exactly on 60.73%; OR-ing in the fallback lifts that to 67.28%; the rescue is targeted at value-level and low-quality JPEG, while geometric conditions and salt-and-pepper barely move",
          "The gain comes from tuning the BCH mode",
          "The gain is on clean images only"
        ], a: 1,
        exp: "Say: denominator first, 96,000 transformed observations, validated. TrustMark alone decodes exactly on 60.73 percent; the fallback OR rule lifts that to 67.28 percent. The rescue is not uniform: brightness 83.7 to 92.1, saturation 97.4 to 99.5, JPEG quality 5 from 2.7 to 69.7, quality 20 from 42.3 to 93.1, while geometric conditions and salt-and-pepper barely move. (FPR 4.11-4.12, Table 12)" },
      { q: "What is the primary limitation you accept?",
        opts: [
          "The dataset is too small",
          "No false-acceptance, negative-pair or calibration evaluation exists, and geometric registration is absent; both are named as required future work, not glossed over",
          "The code is too slow",
          "There are too many figures"
        ], a: 1,
        exp: "Say: no false-acceptance, negative-pair or calibration evaluation exists, and there is no geometric registration, so rotation, crop and letterbox remain near chance. Both are named as required future work. Calibration, negatives, wrong-payload and adaptive attacks are recorded, not hidden. (FPR 5.7, Appendix G)" },
    ],
  },

  /* ================= Chapter 5 ================= */
  {
    id: 5, title: "The Spoken Script", heading: "Ten minutes, timed, memorizable (FPR v3.1)",
    sections: [
      { type: "body", text: "[30 sec] OPENING. My project asked a narrow, answerable question: when a photograph goes through everyday platform transformations such as resizing, JPEG recompression, filters, cropping, rotation and padding, how much verification signal survives, and how should we report that without blurring similarity, recovery, integrity and provenance?" },
      { type: "body", text: "[1 min] WHAT. I built an auditable benchmarking framework. On 1,200 deterministically selected MS-COCO validation images I applied twelve transform families across eighty named conditions and ran four pipelines: TrustMark, two simple classical baselines (LSB and DCT) and eight perceptual hash variants including the 256-bit PDQ. That is 768,000 hash rows and 97,200 rows per watermark method. On top I built a hybrid two-layer recovery channel, where a BCH-coded DCT fallback can rescue the payload when TrustMark fails. The whole thing is wrapped in a dashboard." },
      { type: "body", text: "[1.5 min] WHY. Provenance claims are easy to overstate, and the consequence is real: misread a similarity score as an authenticity guarantee and you get unjustified takedowns or misplaced trust. The literature blurs four questions: is this image similar to a reference, can I recover a hidden message, is it byte-for-byte intact, and who signed it. I separated similarity, recovery, integrity and accountability, and measured honestly where each signal lives and where it dies. The report maps that to the BCS Code of Conduct, especially accurate representation." },
      { type: "body", text: "[2.5 min] HOW. Everything runs through one shared module, transforms.py, the single source of truth for the twelve families and eighty conditions. Random operations derive their seeds deterministically from image ID, transform name and intensity via SHA-256, so any machine reconstructs the same transformed image. JPEG is genuinely written to disk and reopened, so we test the real codec. Ten validation gates guard coverage, duplicate keys and ranges, and a failing run is never reported. For uncertainty the image is the statistical unit: percentile bootstrap with 2,000 resamples at the fixed seed 20260812, and Wilson intervals for decode proportions. I also corrected two measurement errors mid-project: PDQ was serialised per dimension instead of one bit, silently inflating distances, and TrustMark raw bits are now measured before error correction. Both changed numbers and were revalidated." },
      { type: "body", text: "[3 min] RESULTS. The headline: the hybrid channel lifts exact payload recovery from 60.7 percent to 67.3 percent over the 96,000 transformed observations, a 6.6-point gain. Table 12 is the money table: at JPEG quality 5 TrustMark alone recovers just 2.7 percent, the two-layer system gets 69.7; at quality 20 it is 42.3 up to 93.1. Quality 10 dips to 32.2 percent, reported openly as a codec irregularity. Every recovery figure is drawn on a full 0-to-100 scale, a deliberate honesty choice. Geometric attacks still beat us: rotation, crops and letterbox are near chance, letterbox at 10.4 percent. And honesty includes the hypothesis: my interim proposal promised over 90 percent across JPEG and PNG; measured JPEG is 85.6 percent and PNG was never implemented, reported as a non-confirmation." },
      { type: "body", text: "[1.5 min] CONCLUSION. The conclusion is deliberately narrow: a functioning, auditable framework where every claim is bounded by what the validated 1,200-image benchmark supports, plus a measured, targeted rescue channel. The strongest claim I defend is the framework itself, because deterministic selection, row-level traceability, validation gates, corrected metrics and separate baselines are what survive scrutiny. The open frontier is geometric synchronisation, recorded as future work with a protocol. Deployment-ready provenance needs cryptographic signing, calibration and governance, and the dashboard's development Ed25519 manifest is a stated pattern, not a trust chain. Thank you, I am ready for questions." },
      { type: "body", text: "[backup close] If interrupted: one body, one discipline. Validated 1,200 images, eighty conditions, a +6.6-point two-layer gain, and a hypothesis falsified and reported. Everything else is detail, and I can take you to the file or table for any of it." },
    ],
    questions: [
      { q: "If you had one sentence to summarise the whole project, what is it?",
        opts: [
          "I built a watermark that proves images are real",
          "I built an auditable framework that measures how verification signals survive real image transformations and reports the result honestly, with a two-layer recovery channel on top",
          "I compared some hashes",
          "I made a dashboard"
        ], a: 1,
        exp: "Say: an auditable, transformation-aware verification framework with a measured two-layer rescue, where every claim is bounded by a validated 1,200-image benchmark. (FPR 1.2, 4.12)" },
      { q: "What is your backup close if the chair interrupts you?",
        opts: [
          "Apologise and stop",
          "One body, one discipline: validated 1,200 images, 80 conditions, a +6.6pp two-layer gain, and a hypothesis falsified and reported; everything else is detail I can point to",
          "Repeat the abstract from the start",
          "Ask for more time"
        ], a: 1,
        exp: "Say: one body, one discipline, validated 1,200 images, eighty conditions, a 6.6-point two-layer gain, and a hypothesis falsified and reported. Everything else is detail, and I can take you to the file or table for any of it." },
      { q: "How do you open the results section so it lands?",
        opts: [
          "With the methodology again",
          "With the headline denominator first: 96,000 transformed observations, then 60.7% TrustMark versus 67.3% two-layer",
          "With an apology for the limits",
          "With the hash results"
        ], a: 1,
        exp: "Say: denominator first, 96,000 transformed observations, then the headline, 60.7 percent TrustMark versus 67.3 percent two-layer, and immediately locate where the rescue happens using Table 12." },
      { q: "How do you open the methodology section?",
        opts: [
          "With the list of files",
          "With the single source of truth, transforms.py, because it is the precondition for every fair comparison",
          "With the dataset size",
          "With the hardware used"
        ], a: 1,
        exp: "Say: everything runs through one shared module, transforms.py, the single source of truth for the twelve families and eighty conditions, and deterministic seeding is why 96,000 rows are reproducible on any machine." },
      { q: "How do you land the conclusion?",
        opts: [
          "By claiming the system is production-ready",
          "By narrowing the claim: the framework is what survives scrutiny, geometry is the open frontier, and deployment provenance needs signing and governance that are out of scope",
          "By listing every limitation",
          "By thanking the marker for their time"
        ], a: 1,
        exp: "Say: the conclusion is deliberately narrow. The framework is the strongest defensible claim; geometric synchronisation is the recorded open frontier; and deployment-ready provenance needs cryptographic signing, calibration and governance that are explicitly out of scope. (FPR 5.1-5.8)" },
      { q: "What one number should you never quote without its denominator?",
        opts: [
          "The image count",
          "The recovery percentage: always pair 67.3% with the 96,000 transformed observations and the 60.7% baseline",
          "The seed",
          "The file size"
        ], a: 1,
        exp: "Say: never quote recovery without its denominator. 67.3 percent means nothing without the 96,000 transformed observations and the 60.7 percent TrustMark-alone baseline that it improves on. (FPR 4.11-4.12)" },
    ],
  },
];
