# Steganographic Signing and Filter Traceability in Digital Media

## Final Project Report Draft v1.0

**Institution:** [insert institution name]
**School/department:** [insert school or department]
**Programme:** MSc Computer Science
**Module:** 7COM1040-0509-2025
**Student:** Opaleye Toluwalope Abayomi
**Student number:** 24163800
**Supervisor:** Daniel Barry
**Submission date:** [insert confirmed submission date]
**Word count:** 8,110 (main text, excluding references and appendices)

### Proofreading confirmation placeholder

I confirm that this report has been proofread for spelling, grammar, structure, terminology, figure and table numbering, cross-references, accessibility, and consistency between the report and its artefacts.

**Proofreader:** [name or approved proofreading arrangement]
**Date:** [insert date]
**Confirmation/signature:** [complete before submission]

### Institutional ethics and non-plagiarism declaration placeholder

The final submission must use the institution's prescribed declaration, not an improvised replacement. The intended project-specific wording for preparation is:

> I declare that this report and the associated implementation are my own work except where sources, collaborators, and external software are explicitly acknowledged. I have complied with the institution's academic-integrity and non-plagiarism requirements. The reported experiment uses a public image dataset, does not recruit human participants, and does not claim to establish the identity, truth, ownership, or provenance of an image. Any institutional ethics classification, approval, exemption, or supervisor confirmation required for this use is attached separately.

**Required institutional declaration/form:** [insert exact approved wording or attach the required form]
**Ethics reference/classification:** [insert, or state not required only after institutional confirmation]
**Student signature:** [complete]
**Date:** [complete]

## Contents placeholder

Generate a page-numbered contents list from the final document headings. The expected order is: Abstract; 1 Introduction; 2 Literature Review; 3 Methodology; 4 Quality and Results; 5 Evaluation and Conclusion; References; Appendices A-I; and the user-action checklist.

## List of figures placeholder

Insert final captions and page numbers after figures are regenerated from the evidence set. Candidate figures are: system boundary and data flow; transform taxonomy; method comparison; per-transform degradation curves; ensemble decision matrix; evidence-status diagram; and project Gantt.

## List of tables placeholder

Insert final captions and page numbers after final editing. Required tables are: objectives and success criteria; evidence matrix; transform matrix; metric definitions; validation gates; threat model; risk matrix; BCS mapping; results coverage; and future-work priorities.

## Glossary placeholder

Add an alphabetised glossary in the formatted submission. Required entries are: bit accuracy, benign transformation, C2PA, decode presence, DCT, false acceptance, false rejection, Hamming distance, hard binding, integrity, LSB, perceptual hash, provenance, PSNR, soft binding, TrustMark, transform intensity, watermark, and wrong payload.

## Abstract

Digital images routinely pass through resizing, compression, filtering, cropping, rotation, and padding. Such changes can remove metadata and disturb embedded signals. This project evaluates a layered verification prototype that compares perceptual hashing, a neural watermark, and classical watermarking baselines under a shared still-image transform matrix. It does not generate AI images, process video, or create a new watermark algorithm. Its purpose is not to prove authenticity. The main contribution is an auditable, transformation-aware verification framework in which signal recovery, image similarity, integrity, and provenance are reported as distinct constructs.

The repository contains two evidence scales that must not be silently combined. The historical/baseline experiment uses 100 deterministically selected MS-COCO 2017 validation images, 12 transform categories, 80 transform-intensity conditions, 64,000 hash rows, 8,100 rows for each watermark method, and an 80-row ensemble matrix. The final1200 validation result covers 1,200 images: the hash output contains 768,000 compressed transformed rows; TrustMark, LSB, and DCT each contain 97,200 rows, comprising 1,200 untransformed baseline rows plus 96,000 transformed rows (1,200 images times 80 conditions); and the ensemble matrix contains 80 transformed conditions. These sets are analysed separately, with baseline inclusion and aggregation stated for each claim.

The historical 100-image results show condition-specific complementarity. TrustMark generally retains high raw bit accuracy for several photometric, blur, compression, and scaling conditions, while geometric changes are more damaging. Perceptual hashes commonly retain similarity under modest value changes but differ substantially by algorithm and transform. LSB is fragile and DCT is a stronger but still limited classical comparator. The results are descriptive and are not population estimates. The final1200 files now provide a validated 1,200-image comparison across all four implemented pipelines, while historical numerical results remain clearly labelled as historical.

The report combines literature on HiDDeN, StegaStamp, ReDMark, distortion-agnostic watermarking, HiNet, robust invertible image steganography, DeepMIH, latent/diffusion watermarking, black-box attacks, WAVES, TrustMark, and removal attacks with C2PA, ISO, professional codes, and law. The diffusion and synthetic-media sources are contextual security literature only: no AI-generated images are created or evaluated here. The report identifies validation gates, threats, ethical and legal issues, and improvements needed before deployment: image-level confidence intervals, image-as-unit analysis, composed attacks, separation of benign transformations from removal attacks, false-positive and wrong-payload tests, calibration, and explicit distinctions between recovery, similarity, integrity, and provenance.

## 1. Introduction

### 1.1 Context and problem

The operational problem is simple to state but easy to misrepresent. An image that has been resized may still be recognisably the same image while its pixels, metadata, cryptographic digest, and embedded message have changed. A verification system must therefore answer several different questions. Is the transformed image perceptually related to a reference? Is a previously embedded payload recoverable? Is the asset byte-for-byte unchanged? Is there a signed, accountable provenance statement? These questions have different evidence requirements.

Perceptual hashing addresses a similarity question. It maps an image to a compact representation and compares representations, here using Hamming distance. A watermark addresses a signal-recovery question. It embeds information and attempts to decode it after transformation. A cryptographic hash or signature addresses integrity and accountability, subject to key management and validation. A provenance standard such as C2PA provides a structured way to bind claims, assertions, signatures, and content bindings. None of these mechanisms alone proves that an image is true, ethically produced, or created by a particular person.

The project investigates this boundary through an implementation rather than through a claim that one method is universally best. TrustMark is the selected neural method; LSB and DCT are deliberately simple baselines; eight perceptual hash variants provide a non-embedded comparison layer. All are exposed to the same independently applied transformations. The resulting framework makes it possible to inspect where a signal survives, where it degrades, and what a reported score can and cannot support.

### 1.2 Aim

The aim is to design and evaluate an auditable framework for measuring the transformation-aware behaviour of image similarity and watermark-recovery signals, while communicating the boundary between experimental evidence and provenance or authenticity claims.

### 1.3 Objectives and success criteria

| Objective | Evidence of completion | Status in this draft |
|---|---|---|
| Review current research, standards, law, and professional guidance | Literature and governance synthesis | Implemented in this report |
| Define a shared deterministic transformation pipeline | `transforms.py`, named conditions, stable seeds | Implemented |
| Compare TrustMark with LSB and DCT | Historical validated CSVs and final1200 CSVs | Implemented at both scales, with evidence separated |
| Compare eight perceptual hashes | Historical 100-image CSV and validated final1200 compressed hash result | Implemented at both scales, with evidence separated |
| Measure recovery and similarity separately | Raw bit accuracy, decode presence, PSNR/MSE, Hamming distance | Implemented |
| Produce threshold and ensemble views | 80-condition historical matrix and analysis script | Implemented for the historical set |
| Run a payload/error-correction ablation | 12-config dev-scale sweep (97,200 rows) plus ensemble-aware rescoring | Implemented at dev scale; selected config validated at 1,200 |
| Demonstrate a secure provenance system | Signed C2PA manifests, identity, key lifecycle, trust chain | Not implemented and not claimed |
| Establish universal robustness or authenticity | Independent replication and attack evaluation | Not achieved and explicitly out of scope |

### 1.4 Research question

To what extent do a neural watermark, perceptual hashes, and classical watermarking baselines retain interpretable verification signal when images undergo graduated photometric, compression, and geometric transformations, and how should that signal be reported without confusing recovery, similarity, integrity, or provenance?

### 1.5 Novelty and contribution

The work does not propose a new encoder, decoder, loss function, watermark payload, or proof of authenticity. Its contribution is an auditable framework and an evidence discipline. The shared transform source, deterministic selection, row-level traceability, validation script, corrected PDQ representation, corrected TrustMark raw-bit measurement, separate baselines, and ensemble view form a practical verification benchmark. The framework also records evidence maturity: a configured run is not a completed run, a partial file is not a final result, and a low Hamming distance is not provenance.

This is a modest but useful contribution for an MSc engineering project. It addresses a recurrent weakness in applied watermark reporting: aggregate scores are often presented without specifying whether they measure detection, identification, message recovery, image quality, or resistance to an adaptive remover. The strongest defensible contribution is therefore a transformation-aware, calibrated image verifier: not a new watermark algorithm, but a reproducible decision framework that reports signal recovery, similarity, integrity, and provenance as separate, calibrated outputs. Calibration and security testing remain proposed extensions, not completed capabilities.

### 1.6 Research-to-product integration

The expanded literature review changed the implementation and not only the bibliography. Benchmarking work led to explicit coverage and duplicate-key validation, because a large-looking result file is not evidence of a complete experiment. Work on distortion-aware watermarking led to the shared transform module and stable seeds, so each method receives the same named still-image conditions. Provenance standards led to separating similarity, watermark recovery, integrity, and provenance in the dashboard and report rather than calling the ensemble an authentication proof. Security literature led to a threat model, wrong-payload and false-positive controls as identified gaps, and a clear separation between benign transformations and future removal attacks. Software-quality and professional guidance led to the risk register, BCS mapping, evidence-status labels, storage-aware execution, and reproducibility manifest.

The review also identified improvements that are not yet implemented: image-level confidence intervals, composed attacks, calibrated operating points, negative-pair datasets, geometric registration, additional learned or wavelet baselines, and deliberate removal attacks. These are recorded as future work rather than presented as product capabilities. This distinction keeps the contribution centred on a custom, auditable verification framework instead of turning the project into an uncritical comparison of third-party libraries.

### 1.7 Feasibility and scope

The implementation is feasible because it uses a public research dataset, local Python pipelines, fixed test payloads, a shared transformation module, and CSV artefacts. The scope is deliberately bounded to still-image experiments and a small set of methods. It does not include AI-image generation, video, audio, human participants, real customer identifiers, a production identity service, C2PA manifest generation, an authenticated database deployment, or a claim that the selected MS-COCO images represent all digital media.

The final1200 artefacts require careful scope control. The manifest records 1,200 image records. The validated hash result contains 768,000 transformed rows; each validated watermark result contains 97,200 rows, including 1,200 untransformed baseline rows and 96,000 transformed rows; and the ensemble matrix contains 80 transformed conditions. This supports a combined 1,200-image comparison, but not a pooled combination with the historical 100-image results. Historical TrustMark, LSB, DCT, and hash figures therefore remain historical and are not silently joined to final1200 values.

### 1.8 Risks at project level

The largest technical risk was evidence mislabelling: treating a configured target as a completed experiment. Storage limitations and partial extended runs made this concrete. A second risk was construct error, particularly treating exact decoded payload presence as raw bit accuracy. A third was implementation drift across transform scripts. A fourth was overclaiming, for example calling soft verification signal proof of authenticity. These risks are addressed by validation gates and by retaining incomplete files as limitations rather than hiding them.

### 1.9 Report structure

Section 2 reviews the research landscape and governance context. Section 3 specifies the dataset, transforms, methods, metrics, implementation, threat model, and validation design. Section 4 reports evidence by scale and method, with quality controls and an explicit evidence matrix. Section 5 evaluates validity, professional practice, ethics, legal and social issues, project management, and future work before concluding. The appendices provide reproducibility, metric, risk, BCS, and submission records.

## 2. Literature Review

### 2.1 From steganography to learned watermarking

HiDDeN demonstrated an end-to-end learned encoder-decoder approach in which a message is hidden in an image and recovered after simulated distortions (Zhu et al., 2018). Its importance is methodological: robustness is not an inherent property of “deep learning”; it is produced by the distortions represented during training and evaluated by the decoder. StegaStamp extended learned embedding towards physical photographs and invisible hyperlinks, making geometric, capture, and re-imaging effects central to the design (Tancik et al., 2020). These studies motivate measuring a fixed transform family rather than reporting only clean-image decoding.

ReDMark used residual dense networks for image watermarking and diffusion-style residual embedding (Ahmadi et al., 2020). Distortion Agnostic Deep Watermarking explicitly sought to reduce dependence on a known distortion model through learned robustness (Luo et al., 2020). The lesson for this project is not that a learned method is distortion agnostic in every new environment, but that training and testing distributions must be documented. A local TrustMark measurement cannot inherit a paper's published robustness claims when the model, payload, image population, library versions, and transformations differ (Bui et al., 2025).

RoSteALS placed robust steganography in autoencoder latent space and examined the capacity and imperceptibility trade-off (Bui et al., 2023). HiNet used an invertible network for high-fidelity image hiding (Jing et al., 2021), while DeepMIH extended invertible networks to multiple-image hiding (Guan et al., 2023). Robust Invertible Image Steganography further targeted recoverability under transformations using an invertible design (Xu et al., 2022). These works show an important architectural direction: invertibility can support reconstruction and hiding, but it does not remove the need to test geometric misalignment, compression, adaptive removal, or wrong-payload behaviour. High fidelity and successful recovery are separate axes.

Classical transform-domain work provides useful baseline design choices. Ansari, Pant and Ahn (2016a) examine robust-reversible watermarking with optimisation, while Pardhu and Perli (2016) discuss frequency-domain embedding. Ansari, Pant and Ahn (2017) consider secured and optimised watermarking, and Sharma et al. (2017) examine a contourlet-domain design. Kulkarni, Mulani and Mane (2016) connect invisible watermarking with image authentication. These studies do not establish that a second baseline should be added without a fair implementation, but they identify achievable extensions: embedding-strength sweeps, keyed or adaptive embedding, reversible recovery, tamper localisation, and a multiscale comparison against the current DCT baseline.

Windisch et al. (2024) demonstrate why error correction should be treated as a separate experimental factor rather than hidden inside a recovery percentage. Their comparison of Hadamard coding with other coding approaches supports reporting raw bit error, corrected payload recovery, and false-positive behaviour separately. The current TrustMark configuration uses its own BCH-based packet and does not implement Hadamard coding; this source therefore motivates a future coding ablation rather than a current result.

### 2.2 Contextual AI-media literature and removal threats

Stable Signature embeds a signature in a latent diffusion generator rather than only modifying a finished image (Fernandez et al., 2023). Gaussian Shading uses diffusion latent structure to provide a watermarking construction with a stated performance-lossless objective (Yang et al., 2024). These sources are not implemented here and are not evidence about the current dataset. They are included only to clarify that generator-level signatures, post-hoc image watermarks, and signed provenance manifests bind different things. This project does not generate or test AI-generated images.

Jia et al. (2020) examined watermark perturbations for adversarial examples. Li et al. (2022) studied a concealed attack based on a generative model and perceptual loss. Jiang, Zhang and Gong (2023) showed that watermark-based detection of AI-generated content can be evaded. Hayes (2018) examined visible adversarial perturbations and digital watermarking. These sources are threat-model context, not implemented experiments. They justify separating ordinary still-image transformations from future deliberate-removal testing.

Zhao et al. (2024) reported that invisible image watermarks can be removable using generative AI. Yuan et al. (2025) studied watermark-removal attacks against text-to-image generative-model watermarking. These results are not evidence that the present implementation fails under every removal attack, but they establish why this report does not use “robust” as shorthand for “secure”. WAVES provides a benchmark protocol spanning detection and identification tasks, image quality, traditional distortions, diffusion-related attacks, and adversarial attacks (An et al., 2024). The present project is narrower: it is a still-image screening benchmark, not a replacement for WAVES and not an AI-image-generation study.

Black-box robust watermarking is especially relevant to deployment. In a black-box setting, an evaluator may query a detector without seeing model weights or gradients. Query-efficient search, transfer attacks, or content-adaptive editing can still expose weaknesses. The project's current threshold matrix is not a black-box security test because it uses known implementations and preselected transformations. A future black-box track should define an attacker query budget, success criterion, wrong-payload criterion, perceptual constraint, and whether the defender can rate-limit or rotate keys.

Older adversarial-robustness research makes this gap technically actionable. DeepFool and universal adversarial perturbations provide image-space procedures for measuring minimum or transferable perturbations (Moosavi-Dezfooli, Fawzi and Frossard, 2016; Moosavi-Dezfooli et al., 2017). Carlini and Wagner (2017) demonstrate optimisation-based robustness evaluation, while Papernot et al. (2016) and Papernot et al. (2017) motivate transfer and decision-only black-box testing. A feasible extension is not to claim a new attack algorithm, but to apply a declared perturbation budget to the existing image verifier and report attack success, PSNR, normalised hash change, watermark bit accuracy, query count, and false-positive/false-negative effects. This would move the project from fixed-transform screening towards an attack-aware evaluation without expanding beyond still images.

### 2.3 Similarity, hashing, and provenance

Perceptual hashing is useful for near-duplicate or transformed-image retrieval, but its output is a similarity signal (Qin et al., 2016; Yan et al., 2016a; Yan et al., 2016b; Tang et al., 2017; Feng et al., 2017). Tang et al. (2019) demonstrate a robust image-hashing design under distortion, while McKeown and Buchanan (2023) measured Hamming distributions of popular perceptual hashes and showed why thresholds depend on the algorithm and comparison population. The current project follows that caution by retaining algorithm identity, hash length, and transform condition. PDQ is represented as a 256-bit value; incorrectly serialising each dimension as multiple characters would change the construct and invalidate comparisons. Caldelli, Becarelli and Amerini (2017) and Jin et al. (2022) further show that provenance evaluation involves manipulation histories and benchmark tasks beyond a single similarity threshold; the current project does not reproduce those provenance tasks.

C2PA defines a provenance architecture involving manifests, assertions, claims, signatures, and content bindings (Coalition for Content Provenance and Authenticity, 2023). ISO/IEC 21617-1:2025 provides a further standards context for trustworthy media annotation and provenance (International Organization for Standardization and International Electrotechnical Commission, 2025). These standards distinguish hard bindings from soft bindings. A cryptographic digest can bind exact bytes; a fingerprint or watermark can assist discovery of transformed or derived content. The framework in this report can be understood as evaluating possible soft-binding signals, but it does not create or validate a C2PA or JPEG Trust record. In particular, it has no signing keys, certificate trust, identity policy, revocation mechanism, or validator result. This boundary is essential: “watermark recovered” must not be written as “source authenticated”.

### 2.4 Standards, governance, and professional practice

NIST SSDF 1.1 supports secure development practices such as protecting software, responding to vulnerabilities, and producing well-secured releases (Souppaya, Scarfone and Dodson, 2022). ISO/IEC 23894 provides AI risk-management guidance, ISO/IEC 27001 frames information-security management, and ISO/IEC 25010:2023 separates software-quality characteristics such as functional suitability, reliability, security, maintainability, and portability (International Organization for Standardization and International Electrotechnical Commission, 2022; 2023a; 2023b). These sources support evaluating the prototype as a research tool rather than calling it production-ready because it has a dashboard.

The BCS Code of Conduct requires attention to public interest, competence, integrity, due care, privacy, security, and accurate representation (BCS, The Chartered Institute for IT, 2026). The ACM Code of Ethics similarly emphasises avoiding harm, respecting privacy, being honest about system limitations, and evaluating risks (Association for Computing Machinery, 2018). The American Statistical Association requires transparent communication of uncertainty, limitations, exploratory analysis, and reproducibility (American Statistical Association, 2022). The United Kingdom Data Protection Act 2018 is relevant if future payloads contain identifiers or if images are processed in a way that constitutes personal-data processing (United Kingdom, 2018).

### 2.5 Literature synthesis and gap

The literature establishes four requirements. First, robustness must be conditioned on transformations, quality constraints, payload and detector semantics. Second, evaluation must include removal, adversarial, and geometric scenarios rather than only benign photometric changes. Third, message recovery and detection must be separated from image quality and provenance. Fourth, governance and professional communication are part of technical validity.

The project's narrower gap is practical auditability across complementary signal types. Published algorithms generally optimise their own task; this project places one neural watermark, two classical baselines, and perceptual hashes under a common transform vocabulary and records the evidence limits of the comparison. It does not claim to fill the broader algorithmic research gap or to outperform the reviewed methods.

## 3. Methodology

### 3.1 Research design

The study is an engineering benchmark with repeated observations on the same images. Each image is evaluated under named transformation conditions. The experimental unit for primary future analysis should be the image, not the CSV row, because rows from the same image are dependent and each method sees the same source. Historical summary statistics were already generated as descriptive aggregates; they are retained with their provenance and not reinterpreted as independent population observations.

### 3.2 Dataset and evidence scales

The dataset is the MS-COCO 2017 validation split. The historical benchmark selected the first 100 JPG files in lexicographic order, deterministically. The final manifest records 1,200 selected images using the same style of selection. This is a reproducible engineering sample, not a random sample of all digital imagery and not an ethics-free guarantee simply because the source is public. Images may contain people and copyrighted material; the dataset terms and institutional classification remain relevant.

| Evidence set | Images | Main artefacts | Evidence status | Permitted use |
|---|---:|---|---|---|
| Historical/baseline | 100 | Hash CSV 64,000 rows; TrustMark, LSB, DCT 8,100 rows each; ensemble 80 rows | Validated historical result set | Historical numerical claims, clearly labelled |
| Final hash | 1,200 | Clean compressed hash result, 768,000 rows | Complete/clean final hash output | Hash-only final1200 reporting after coverage checks |
| Final LSB | 1,200 | `final1200/lsb_robustness_results.csv` | Complete final1200 output | LSB-only final1200 reporting after file reconciliation |
| Final DCT | 1,200 | `final1200/dct_robustness_results.csv` | Complete final1200 output | DCT-only final1200 reporting after file reconciliation |
| Final TrustMark | 1,200 | `final1200/trustmark_robustness_results.csv` | Complete/validated; 97,200 rows including baseline | Final1200 comparison, with transformed-condition aggregation stated |

The final1200 rows support a four-method comparison after each pipeline's coverage, uniqueness, missing-value, and version gates have passed. The comparison must distinguish the hash file's transformed-row count from the watermark files' baseline-inclusive row counts. Historical 100-image values remain a separate evidence scale.

### 3.3 Transformation matrix

`transforms.py` is the single source of truth. It defines 12 categories and 80 named conditions: brightness, contrast, saturation, vibrancy, Gaussian blur, salt-and-pepper noise, JPEG compression, rotation, scaling, centre crop, random crop, and letterbox padding. Settings range from mild to severe within each family. Brightness 0.5, blur radius 2, JPEG quality 20, and crop removal 0.5 are not a common linear severity scale. They are comparable only as named conditions within the experimental design.

Photometric and encoding transformations alter values while often preserving broad layout. Geometric transformations alter coordinate relationships or dimensions. Letterbox is kept separate because it adds padding rather than removing the same content as cropping. Operations are applied independently, not as cascades. Random operations derive stable seeds from image and condition identifiers, so they can be reconstructed. JPEG is actually written and reopened rather than represented only by a label. These controls improve internal consistency but do not establish robustness against all codecs or all crop policies.

### 3.4 Pipeline implementations

The hash pipeline computes a reference hash on the original image and a transformed hash for each condition. The eight variants are pHash, dHash, aHash, wHash, colorHash, vertical dHash, simplified pHash, and PDQ. The output stores algorithm, hash representation, bit length, image, condition, and Hamming distance.

TrustMark v0.9.1 is used as the neural candidate with a fixed test payload `TM00001` (Bui et al., 2025). The source image is encoded, transformed, and decoded. The output includes raw bit accuracy, decode presence, encode MSE, PSNR, decoded payload, and row metadata. The raw-bit metric is intended to inspect pre-error-correction recovery; exact decode presence is a separate binary outcome. The historical run corrected an earlier procedure that measured only exact payload recovery.

The LSB baseline writes `LSB0001` into the red-channel least-significant bit plane. The DCT baseline differentially embeds a fixed payload into mid-frequency coefficients. Both are intentionally simple and are not representative of every spatial or frequency-domain method. Their different payload structures and decoder semantics mean that a direct bit-accuracy ranking is comparative, not an information-theoretic statement.

### 3.5 Metric definitions

| Metric | Definition | What it supports | What it does not support |
|---|---|---|---|
| Hamming distance | Number of changed representation bits | Hash representation change | Authorship or exact integrity |
| Bit-error fraction | Hamming distance divided by method bit length | Normalised hash comparison | Universal similarity threshold |
| Raw bit accuracy | Expected packet bits recovered before correction | Signal recovery quality | Exact valid-message success or provenance |
| Decode presence | Decoder reports a valid payload | End-to-end decode event | Correct authorship or absence of wrong payload |
| PSNR | Pixel-domain encode quality measure | One imperceptibility dimension | Robustness or perceptual acceptability alone |
| MSE | Mean squared pixel error | Encode distortion | Security |
| Threshold pass | Current rule: watermark mean accuracy above 0.5 or hash worst-algorithm error below 0.5 | Screening matrix | Calibrated operational decision |

The threshold analysis uses mean watermark bit accuracy and a worst-algorithm hash rule over the 80 transformed conditions. That rule prevents seven 64-bit hashes from hiding a weak PDQ result. It is a declared analytical choice, not a security boundary. Decode rates must be reported separately from raw bit accuracy because error correction can make these diverge. The final matrix is condition-level aggregation over the 1,200-image final1200 rows; it is not an image-level error rate.

### 3.6 Validation gates

| Gate | Check | Failure response |
|---|---|---|
| G1 | Manifest count, unique IDs, filenames, and checksums | Stop; do not analyse |
| G2 | Expected image-condition-method coverage | Mark incomplete and stop final claims |
| G3 | No duplicate keys or unintended baseline duplication | Repair or exclude run |
| G4 | Correct PDQ bit serialisation and hash lengths | Recompute affected hash output |
| G5 | Raw TrustMark bits are measured before error correction | Recompute TrustMark metrics |
| G6 | Missing values, impossible ranges, payload lengths, and dimensions | Stop and inspect pipeline |
| G7 | Transform names and intensities match `transforms.py` | Reject drifted output |
| G8 | Numerical tables and figures regenerate from the declared files | Replace stale artefacts |
| G9 | Analysis records image-level unit, interval method, and baseline policy | Do not present pooled values as inferential |
| G10 | Report, dashboard, workbook, and CSV values reconcile | Hold submission until corrected |

The existing validator is valuable because a command using `--image-count 100` cannot validate 1,200-image coverage. The final validation checks each pipeline and the combined comparison separately. A compressed CSV must be decompressed or read with an integrity check before its row count and unique keys are accepted.

### 3.7 Reproducibility and data lineage

The data lineage begins with a source filename and image checksum, continues through an explicitly named transform, and ends in a row containing the method, metric, software context, and evidence-set identity. This lineage is more important than a dashboard screenshot because a screenshot cannot show whether a value came from the historical set, a partial run, or a regenerated final file. The manifest is therefore a research control, not merely an inventory. A future archive should preserve the manifest alongside a checksum of the compressed hash file and checksums for model and code artefacts.

The experiment uses CSV because it is transparent and portable. This is appropriate for a research prototype, but CSV lacks strong schema enforcement and transaction semantics. Fields such as `image_id`, transform intensity, bit length, and boolean decode flags should be typed and validated before analysis. A database migration may improve queryability, but migrating the data would not improve the scientific claim unless the same rows, keys, and calculations can be reconciled. A database deployment would also introduce authentication, authorisation, secrets management, backups, logging, and network exposure risks.

Reproducibility has three levels in this project. Computational reproducibility means that the same code and inputs produce the same rows. Analytical reproducibility means that the same rows and analysis script produce the same summaries. Independent reproducibility means that another researcher can obtain the relevant dataset, environment, model, and instructions and reproduce the result without undocumented knowledge. The current work makes progress on the first two levels, but the third remains conditional on dataset access, package versions, model files, operating-system behaviour, and adequate storage.

### 3.8 Analysis protocol and decision semantics

The historical analysis uses descriptive means and threshold summaries because those artefacts already exist in the repository. A threshold is a decision convention: watermark mean accuracy above 0.5 is treated as passing, while hash mean bit-error fraction below 0.5 is treated as passing under the worst-algorithm rule. A threshold crossing is not the same as a detector operating point. In particular, it is not a false-acceptance rate, a probability of authenticity, or a guarantee that one image will be classified correctly.

The analysis also distinguishes first crossing from worst observed condition. Transform degradation is not necessarily monotonic. A JPEG condition may behave differently from a neighbouring setting because codec quantisation, image dimensions, and decoder tolerance interact. A random crop uses a stable seed but still creates a content-dependent outcome. Reporting only the first threshold crossing would conceal recovery at a later condition or a non-monotonic result. The future analysis should retain the full curve and report a confidence interval around the image-level distribution at every condition.

The ensemble rule is intentionally conservative for the hash layer: the weakest algorithm can cause a hash-layer failure instead of being hidden by a pooled average. Other applications might choose the strongest available algorithm, a majority vote, or a calibrated fusion model. No rule is universally correct without a defined loss function. A missed match, an incorrect match, an incorrect payload, and an unauthorised provenance claim can have different consequences. The report therefore treats the current ensemble as an explanatory matrix, not a deployment policy.

The same distinction applies to image quality. PSNR is computed after embedding and is useful for detecting a gross quality trade-off. It does not model visual salience, semantic change, or detector visibility. A watermark can have a high PSNR and still be detectable by a steganalysis tool; a lower PSNR can be acceptable in one publishing pipeline and unacceptable in another. Future evaluation should include a stated perceptual metric or human-centred protocol only if the ethics and scope allow it, and should not substitute a quality metric for recovery or provenance.

### 3.9 Threat model

The protected asset is an image and, where applicable, a message embedded by the owner or evaluator. The verifier has access to the transformed image and the relevant reference, detector, or key. Benign actors apply routine platform transformations. A careless actor changes format or dimensions. An informed attacker knows the detector family and attempts to erase the signal, cause a false positive, produce a wrong payload, or create disagreement between methods. A black-box attacker can query the detector but cannot inspect weights; a white-box attacker has implementation knowledge.

The present experiment covers a subset of benign and careless transformations. It does not cover adaptive optimisation, model extraction, key compromise, malicious manifest signing, collusion, splicing, screenshot-and-recapture, or an attacker intentionally selecting a different valid payload. Consequently, the correct security statement is “screened under the named conditions”, not “resistant to attack”.

### 3.10 Ethical, legal, and social design

No human participants were recruited and no new participant data were collected. However, public images can contain recognisable persons, sensitive contexts, or third-party rights. The current fixed payloads do not contain real names, locations, or identifiers. Future payloads must have a purpose, lawful-use decision, minimisation, retention schedule, access control, deletion procedure, and misuse response. A watermark containing an identifier can become a tracking mechanism and can expose people to false association.

The system could be used defensively to track transformations, but it could also be used to support surveillance, copyright overreach, or unjustified content removal. False positives could cause a platform to reject legitimate work; false negatives could create misplaced confidence. User interfaces should explain whether the output indicates similarity, message recovery, integrity, or a signed provenance statement. They should not use a single “authentic” label when the underlying evidence is only a soft binding.

The dataset's official terms, external package licences, model licence, and redistribution restrictions must be checked before packaging images or outputs. The artefact checklist excludes `.env`, credentials, caches, and temporary files. The project does not provide legal advice. Any deployment classification would depend on the use case and governance context.

### 3.11 Implemented versus proposed improvements

Implemented controls include deterministic selection, stable random seeds, a central transform module, raw CSV preservation, row metadata, validation scripts, explicit baselines, separate raw-bit and decode metrics, corrected PDQ serialisation, the sample-size correction in this report, and a payload/error-correction ablation. The historical threshold and ensemble analyses are implemented.

Proposed improvements are not presented as completed results. They are: image-level bootstrap or binomial confidence intervals where appropriate; image-as-unit aggregation with paired comparisons; stratification by dimensions and aspect ratio; composed attack sequences; separate benign and malicious/removal tracks; negative pairs and wrong-payload tests; detector calibration and reliability plots; operating-point selection from false-acceptance and false-rejection costs; additional payloads beyond the tested 1-, 4-, and 5-character lengths and the selected BCH configuration; additional domains; and independent implementations or models. The final1200 comparison is currently condition-level aggregation; a future analysis should report per-image distributions and confidence intervals before any pooled mean.

## 4. Quality and Results

### 4.1 Quality-assurance evidence

Quality assurance combined code inspection, deterministic execution, row-count checks, duplicate-key checks, image-coverage checks, baseline retention, and regeneration scripts. The dashboard is CSV-backed and supports overview, per-transform, ensemble, and per-image inspection. It is a research visualisation and not a production signing service. The database migration exists but has not been executed against a live database; therefore database security, performance, and access control are not evaluated outcomes.

Two corrections materially improve validity. PDQ was serialised as one bit per dimension rather than as a multi-character representation. TrustMark was measured at the raw decoder output before error correction rather than only by exact decoded-message success. The validated final1200 TrustMark file uses these corrected measurements.

### 4.2 Evidence matrix

| Claim or output | Source | Scale | Status | Allowed wording |
|---|---|---:|---|---|
| Historical TrustMark robustness | baseline TrustMark CSV | 100 | Validated | “In the validated 100-image experiment…” |
| Historical LSB/DCT comparison | baseline CSVs | 100 | Validated | Historical comparison only |
| Historical hash comparison | baseline hash CSV | 100 | Validated | Historical comparison only |
| Historical ensemble | ensemble CSV | 100, 80 conditions | Validated | Thresholded screening matrix |
| Final hash robustness | compressed final1200 hash result | 1,200 | Complete/clean | Hash-only final1200 claim after reconciliation |
| Final LSB output | final1200 LSB CSV | 1,200 | Complete | LSB-only final1200 claim after validation |
| Final DCT output | final1200 DCT CSV | 1,200 | Complete | DCT-only final1200 claim after validation |
| Final TrustMark robustness | validated final1200 TrustMark CSV | 1,200; 97,200 rows | Complete/validated | Final1200 claim with baseline policy and aggregation stated |
| Authenticity/provenance | no signed manifest or trust chain | n/a | Not implemented | Must not be claimed |

### 4.3 Validated historical/baseline results

The historical result set contains 100 images and 80 transform-intensity conditions. The hash pipeline produced 64,000 rows: 100 images times eight algorithms times 80 conditions. Each watermark method produced 8,100 rows under the repository schema: 100 encode/baseline records plus 8,000 transformed records. The ensemble matrix contains 80 rows, one per condition. These counts are not interchangeable with final1200 counts.

The historical hash summaries report mean Hamming distances of approximately 4.62 bits for pHash, 4.67 for dHash, 3.59 for aHash, and 40.47 for PDQ under the current aggregation. These values indicate condition-specific representation stability, not identity or integrity. Geometric conditions, especially crop and rotation, produce larger changes. Letterbox is informative because padding can disturb a descriptor differently from content removal; the observed aHash and PDQ difference is a result for this sample and implementation, not a universal algorithmic ranking.

Historical TrustMark mean raw bit accuracy is high for several value and encoding conditions: reported grouped means include 0.9687 for brightness, 0.9689 for contrast, 0.9696 for Gaussian blur, 0.9929 for saturation, 0.9663 for vibrancy, and 0.9946 for scaling. JPEG compression is reported at 0.9028 and salt-and-pepper noise at 0.8605. Geometric conditions are weaker: rotation 0.6453, centre crop 0.6578, random crop 0.6448, and letterbox 0.5775. Grouped non-geometric and geometric means are reported as 0.9489 and 0.7096 respectively. These figures are descriptive 100-image results and must not be transferred to the final1200 TrustMark claim.

Excluding the untransformed baseline, the historical LSB mean bit accuracy is reported as 0.5949 with a 6% overall decode rate, and DCT mean bit accuracy as 0.7134 with a 14% decode rate. DCT retains more signal for some photometric and compression conditions, while both baselines are vulnerable to spatial changes. The values are not a recommendation for production watermarking.

The historical ensemble matrix reports 56 conditions with all four methods passing, 21 with three passing, and three with two passing under the declared thresholds and worst-hash rule. LSB passes 75% of conditions and DCT 91.2% under that analysis. These are condition-level mean pass rates, not image-level authentication accuracy. They do not report false positives, false negatives, wrong payloads, confidence, or calibrated risk.

### 4.4 Results by transformation class

The results are easier to interpret when transformations are grouped by mechanism, while retaining the named conditions underneath. Value-level operations such as brightness, contrast, saturation, and vibrancy change pixel statistics but normally preserve coordinate correspondence. Blur and JPEG remove or redistribute high-frequency information. Noise changes selected pixel values. Rotation, cropping, scaling, and letterbox alter the spatial relationship between the encoded signal and the decoder's expected coordinates. This classification explains why a method may retain message bits after a colour change but lose them after a crop, without implying that every operation in a class has the same severity.

For perceptual hashes, low average distance under a value-level transformation means that the representation is relatively stable according to the selected algorithm. It does not mean that all images remain close, nor that the original byte sequence can be recovered. PDQ's longer representation also does not make it automatically more robust. Normalisation by bit length is necessary, but a normalised distance still depends on the representation's training or design assumptions and on the comparison population.

For watermarking, raw accuracy and decode presence can diverge in both directions. Error correction can convert a packet with bit errors into a valid decoded message, while an implementation may reject a packet whose raw accuracy remains above chance. A reported decode rate should therefore include its denominator and the baseline policy. An encode-only row is not a transformed observation and should not be silently included in robustness means. These details are particularly important when comparing historical 8,100-row method files with final1200 outputs whose coverage and completion status differ.

The most defensible conclusion from the historical class pattern is not that geometric attacks defeat all methods. Rather, coordinate-changing operations are a high-value area for further testing. Synchronisation, registration, multi-scale decoding, tiled embedding, or a geometric augmentation policy might improve robustness, but each could change imperceptibility, computational cost, false positives, and security exposure. Such improvements belong to future experiments and must not be attributed to the current implementation.

### 4.5 What the data cannot answer

The current data cannot estimate how often a real platform transformation will occur, because the transform matrix is engineered rather than sampled from platform logs. It cannot establish the prevalence of a particular attack, because no threat-intelligence population was collected. It cannot estimate a user-facing probability of authenticity, because there are no labelled claims, independent identities, signed manifests, or calibrated negative distributions. It cannot show whether a recovered payload is still semantically correct after an image has been edited, because the experiment measures packet recovery rather than content meaning.

It also cannot compare algorithms on equal security footing. TrustMark, LSB, and DCT have different embedding mechanisms and packet semantics. The hashes are not watermark detectors. A method may be strong against routine corruption and weak against a white-box remover. Conversely, a system may be useful for retrieval while being inappropriate for legal attribution. The contribution is consequently a measurement framework and an evidence map. The absence of an answer is recorded as a limitation rather than filled with an unsupported assumption.

### 4.6 Final1200 evidence

The validated final1200 result set contains 1,200 images. The hash output contains 768,000 compressed transformed rows. TrustMark, LSB, and DCT each contain 97,200 rows: 1,200 untransformed baseline rows plus 96,000 transformed rows. The ensemble matrix contains 80 transformed conditions. Thus a complete final1200 four-pipeline comparison exists. The method CSVs retain baseline rows, while the threshold and ensemble aggregation covers the 80 transformed conditions; these are not silently mixed.

Final1200 tables may report the four methods together, provided each table states its file, unique image count, row count, baseline inclusion, transformed conditions, aggregation, missing-value policy, and software version. Historical four-method evidence may appear beside final1200 panels only when captions make the scales and evidence statuses unmistakable. A single pooled leaderboard across historical and final1200 rows would be misleading.

### 4.7 Payload/ECC ablation result

A payload/error-correction ablation was run to isolate the TrustMark layer from the deployed two-layer system. At development scale (100 images), 12 configurations were compared: four BCH error-correction modes (`BCH_SUPER`, `BCH_5`, `BCH_4`, `BCH_3`) crossed with 1-, 4-, and 5-character payloads, over the full 81-variant transform battery (97,200 validated rows, 0 duplicate keys, 0 null decodes). The component-level metric is `corrected_exact`: the ECC-corrected payload decoded from a transformed image exactly matches the embedded watermark.

Component-level ranking selected `bch_super_4chars`: 66.4% corrected-exact across all variants, 99% clean-image decode, and the strongest ECC mode at a practical 4-character payload (32 data bits). The weaker ECC modes scored 50-63%. The selected configuration was then run and validated at the full 1,200-image scale (97,200 rows, 0 duplicate keys, 0 null decodes), reproducing 66.22% corrected-exact. The full config sweep and selection rationale are recorded in `output/results/payload_ecc_dev_selection.md`.

An ensemble-aware rescoring then scored every variant with the deployed rule: verified if TrustMark decodes exactly OR the perceptual-hash fallback passes (worst-algorithm bit-error fraction below 0.5). Across all 12 dev configurations this lands between 89.3% and 89.6% verified, a spread of about 0.3 percentage points; at 1,200 images the selected configuration reaches 89.36%. The hash fallback recovers 23.1-23.6 percentage points of variants that TrustMark alone fails. The results are recorded in `output/results/ensemble_aware_payload_dev100.md` and `output/results/ensemble_aware_payload_final1200.md`.

The implication is twofold. First, TrustMark tuning is a component-level choice: it changes the watermark layer's corrected-decode rate (50-66%) but is almost immaterial to the deployed system's verified rate once the hash fallback is active. Second, the residual failures are where TrustMark and the hash fail together, predominantly under extreme geometric and crop degradations. This is the clearest quantitative evidence that the two-layer architecture, not the watermark configuration, carries system-level robustness. The ablation does not cover uncoded or minimally coded bits, the Hadamard coding comparison of Windisch et al. (2024), or wrong-payload acceptance; no coding result beyond the tested BCH configurations is claimed.

### 4.8 Evidence interpretation

The historical results support a conditional pattern: neural watermark recovery is strongest for many value-level changes, hashes provide a complementary similarity signal, and simple baselines fail more readily under pixel or coordinate changes. The result does not establish that TrustMark is universally superior. A score can also be affected by the exact implementation, packet construction, error correction, image dimensions, transform order, fill colour, codec, and aggregation rule.

The ensemble is useful as an inspection device because it maps which method has the greatest margin from a chosen failure line. It is not a production policy. A condition where the mean passes can contain individual images that fail. A condition where a mean fails can contain recoverable images. The matrix should therefore be treated as a screening map until image-level calibration and error-cost analysis are complete.

### 4.9 Required statistical improvements

The primary unit should be an image-condition outcome. For each method and condition, report the distribution of image-level raw bit accuracy, decode presence, Hamming distance, and PSNR. Use paired comparisons because each method evaluates the same images. Confidence intervals should be computed at the image level, for example by bootstrap resampling images, rather than by treating every transform row as independent. Binary decode presence needs an interval appropriate to a proportion and a clear denominator.

The analysis should distinguish pooled rows, per-image means, per-condition means, and rates. It should report medians and quantiles alongside means, identify worst-case and percentile behaviour, and stratify by image dimensions, aspect ratio, and possibly semantic category. Multiple transform conditions create multiple comparisons; the analysis plan should identify whether the purpose is exploratory screening or confirmatory testing. These are proposed improvements, not hidden results.

Calibration is also needed. A watermark detector should be evaluated on positive pairs, transformed positives, unrelated negatives, and wrong-payload cases. A hash threshold should be selected using a reference population and application costs. Report false acceptance, false rejection, receiver-operating curves where meaningful, and a reliability diagram for any probability-like output. “Decode present” is not a calibrated probability.

## 5. Evaluation and Conclusion

### 5.1 Construct validity

The constructs are intentionally separated. Hamming distance measures representation change. Raw bit accuracy measures message agreement. Decode presence measures a decoder event. PSNR measures pixel-domain embedding distortion. None is equivalent to integrity or provenance. The separation improves construct validity, but the current experiment still uses proxies. A method can preserve a message while an attacker changes the visible meaning of an image; a hash can remain close after an undesired edit; a signed manifest can prove a claim was signed without proving the claim is true.

### 5.2 Internal validity

The shared transform module, deterministic seeds, fixed payloads, row metadata, and validation reduce implementation drift. The PDQ and TrustMark corrections remove identified sources of measurement error. Remaining threats include different embedding mechanisms, different payload structures, codec and interpolation behaviour, potential baseline-row inconsistencies, and library-version differences. Independent reimplementation of selected transforms and cross-checking sample images would strengthen confidence.

### 5.3 External and statistical validity

The historical evidence is based on the first 100 filenames in one MS-COCO validation split, while final1200 uses 1,200 selected images from that same source domain. Results for medical images, diagrams, screenshots, and text-heavy images are unknown. Video, audio, and AI-generated media are outside the current project scope rather than untested project objectives. The final1200 files improve scale for all four implemented pipelines, but do not provide confidence intervals, false-positive tests, composed attacks, or calibration results. Those remain future work.

### 5.4 Threats and risk matrix

| Risk | Likelihood | Impact | Control | Residual concern |
|---|---|---|---|---|
| Partial run presented as complete | High | High | Evidence matrix, coverage gate, separate statuses | Future rerun still needs audit |
| Wrong metric or serialisation | Medium | High | PDQ and raw-bit checks; range tests | New versions may drift |
| False provenance confidence | Medium | High | Explicit construct distinctions; UI wording | Users may still overinterpret |
| Adaptive or generative removal | High | High | Threat model; future WAVES-style track | Not tested now |
| Wrong payload or false positive | Medium | High | Proposed negative/wrong-payload evaluation | Current data insufficient |
| Privacy or tracking misuse | Medium | High | Fixed non-personal payload; future DPIA-style review | Public images may contain people |
| Rights or licence breach | Medium | High | Terms and licence checklist | Final packaging decision pending |
| Dashboard exposure | Medium | Medium | Localhost scope; SSDF controls proposed | No auth, rate limiting, or audit log |
| Storage and reproducibility failure | Medium | Medium | Serial execution, manifest, checksums | Environment still needs capture |

### 5.5 Project management and Gantt reflection

| Work package | Planned sequence | Outcome/reflection |
|---|---|---|
| Requirements and ethics | Early | Established scope and public-dataset boundary |
| Literature and standards | Early and iterative | Expanded after threat and provenance risks became clear |
| Transform implementation | Early | Centralised in `transforms.py` |
| Hash pipeline | Early | Historical 100-image and clean final1200 output available |
| TrustMark integration | Middle | Historical and validated final1200 runs available |
| LSB and DCT baselines | Middle | Historical and complete final1200 outputs available |
| Validation and correction | Middle/later | Exposed PDQ and raw-bit issues; should have been earlier gates |
| Dashboard | Later | Functional CSV-backed research visualisation |
| Analysis and report | Final phase | Required sample-size correction and evidence separation |
| Packaging | Final gate | Declaration, proofreading, PDF, and `.txt` artefacts remain user actions |

The project followed an iterative rather than linear Gantt. The strongest decision was treating artefact existence as different from task completion. The principal weakness was late discovery of storage pressure and metric semantics. Earlier gates should have required a small known-payload test, storage estimate, manifest-to-result reconciliation, and metric-schema review before the larger run. The dashboard was sensibly kept CSV-backed to deliver an inspectable result within scope, but that decision leaves database security and deployment outside the validated contribution.

### 5.6 BCS mapping

| BCS responsibility | Project application |
|---|---|
| Public interest | Avoid claims that could cause unjustified censorship or trust |
| Competence | Recognise model, sample, and threat-model limits |
| Integrity | Correct PDQ and TrustMark measurement issues |
| Due care | Use validation gates and retain partial evidence |
| Privacy | Avoid real identifiers and document future payload controls |
| Security | State absence of authentication, key management, and attack testing |
| Accurate representation | Separate historical 100-image, validated final1200, and unimplemented evidence |

This mapping is not a claim of formal BCS certification. It is a professional reflection showing how the code and reporting choices respond to the code's principles.

### 5.7 Future work

The most achievable MSc-level extension is a controlled geometric-synchronisation study, rather than another unstructured library comparison. First, preserve the validated final1200 files, corrected raw-bit metric, model/version record, and matching manifest as a frozen reference. Then add one registration or synchronisation module and compare three explicitly labelled conditions: no alignment, oracle alignment using the known transform parameters, and estimated alignment recovered from the transformed image. Use the same still-image pairs, transform seeds, payload, and image-as-unit aggregation in all three arms. This isolates the value of synchronisation from the value of the verifier itself and makes failure cases inspectable. Report recovery, Hamming distance, PSNR, runtime, and alignment error, with paired confidence intervals and subgroup results. The expected contribution is an evidence-based account of when geometric synchronisation improves verification and what false-positive or quality cost it introduces, not a claim of universal geometric robustness.

Second, establish calibrated verification before selecting thresholds. Use genuine positive pairs, transformed positives, unrelated negatives, near-duplicate negatives, collages or splices, and wrong-payload trials. Fit thresholds only on a declared calibration split, reserve a test split, and report false acceptance, false rejection, wrong-payload acceptance, calibration or reliability plots where probability-like outputs are produced, and application-specific operating costs. A decode event is not a probability. This control set would convert the current recovery measurements into a defensible verifier evaluation.

Third, a payload and error-correction ablation has been run at development scale (100 images, 12 configurations: four BCH error-correction modes crossed with 1-, 4-, and 5-character payloads, 81 transform variants per image, 97,200 validated rows) and the selected configuration validated at the full 1,200-image benchmark scale. Hold the encoder, images, transforms, and decision rule fixed while varying payload length and coding treatment. The dev-scale sweep selected `bch_super_4chars`: the strongest ECC mode at a practical 4-character payload, with the best component-level corrected-decode rate (66.4% across all variants) and 99% clean-image decode. At 1,200 images the selected configuration reproduces the component-level result (66.22% corrected-exact across 97,200 validated rows, 0 duplicate keys, 0 null decodes). The ensemble-aware re-scoring shows why this is a component-level rather than system-level lever: when each variant is scored by the deployed two-layer rule (TrustMark exact decode OR the perceptual-hash fallback passing its worst-algorithm threshold), the dev-scale spread across all 12 configurations is 89.3-89.6% verified (about 0.3 percentage points), and the 1,200-image selected configuration lands at 89.36%. The perceptual-hash fallback recovers about 23 percentage points of variants that TrustMark alone fails (23.1-23.6 at both scales), so the two-layer architecture, not the watermark tuning, carries system-level robustness. Remaining ablation work includes uncoded or minimally coded bits, the Hadamard comparison of Windisch et al. (2024), and wrong-payload acceptance; no coding result beyond the BCH configurations is claimed here. This design tests whether apparent robustness comes from the embedded signal or from redundancy in the packet, and the answer at both scales is that redundancy within the packet is secondary to the hash fallback layer.

Fourth, make the protocol reproducible. Publish the manifest checksum, transform definitions and seeds, payload specification, software and model versions, calibration/test split, alignment settings, thresholds, resource limits, validation output, run log, and checksums for raw and derived results. Re-run all methods from the same still-image manifest and validate coverage, uniqueness, ranges, payload lengths, and baseline inclusion before analysis. Include composed benign operations, such as rotation followed by JPEG and crop followed by scaling, but label them separately from deliberate removal. The current results remain unchanged unless this protocol is run and passes its gates.

Fifth, treat adaptive and black-box attacks as a bounded later track, not completed work. The 2016-2017 adversarial literature provides feasible procedures: DeepFool and universal perturbations for image-space or transferable perturbations, optimisation-based evaluation from Carlini and Wagner, and transfer or decision-only black-box testing from Papernot et al. (Moosavi-Dezfooli, Fawzi and Frossard, 2016; Moosavi-Dezfooli et al., 2017; Carlini and Wagner, 2017; Papernot et al., 2016; Papernot et al., 2017). A future still-image study should predeclare the attacker knowledge, query budget, perturbation or perceptual budget, success criterion, wrong-payload criterion, and rate-limiting assumptions, then report attack success, PSNR, hash change, watermark bit accuracy, query count, and false-positive/false-negative effects. It should not be described as an achieved security result.

Finally, provenance integration and dashboard hardening remain separate deployment work. A high-assurance workflow would combine calibrated soft signals with cryptographic integrity and a signed provenance manifest, plus key management, revocation, audit logging, access control, and human oversight. C2PA integration should be evaluated as an engineering task, not inferred from watermark recovery. These additions would strengthen deployment readiness but would not turn the present still-image benchmark into proof of authenticity.

### 5.8 Conclusion

The project demonstrates a functioning and auditable framework for comparing perceptual hashes, TrustMark, LSB, and DCT under controlled still-image transformations. The validated historical evidence consists of 100 images, 8,100 rows per watermark method, 64,000 hash rows, and 80 ensemble conditions. The validated final1200 evidence consists of 1,200 images, 768,000 compressed hash rows, 97,200 rows for each watermark method, and an 80-condition ensemble matrix. Watermark counts include the 1,200 untransformed baseline rows; the ensemble aggregation uses transformed conditions only. These scales remain separate.

The evidence supports a conditional engineering conclusion: the tested neural watermark and perceptual hashes provide complementary signals under many named conditions, while geometric changes and simple baselines expose important weaknesses. The final1200 set permits the four-pipeline comparison at its declared condition-level aggregation, while the historical results remain contextual pilot evidence. The main contribution is the auditable, transformation-aware verification framework and its evidence discipline, not a new watermark algorithm and not a proof of authenticity. Signal recovery, similarity, integrity, and provenance must remain distinct. Any stronger conclusion requires image-level uncertainty, composed and adaptive attacks, negative and wrong-payload evaluation, calibration, and a governance-aware provenance layer.

## References

References are restricted to official peer-reviewed publications, official standards, government sources, professional-body codes, or official legislation, dated 2016-2026. URLs are publisher, standards-body, government, or professional-body records. No preprint, blog, GitHub page, or Semantic Scholar record is used as a publication citation.

Ahmadi, M., Norouzi, A., Karimi, N., Samavi, S. and Emami, A. (2020) ‘ReDMark: Framework for residual diffusion watermarking based on deep networks’, *Expert Systems with Applications*, 146, 113157. doi:10.1016/j.eswa.2019.113157.
American Statistical Association (2022) *Ethical Guidelines for Statistical Practice*. Official professional-body publication: https://www.amstat.org/your-career/ethical-guidelines-for-statistical-practice.
An, B. et al. (2024) ‘WAVES: Benchmarking the robustness of image watermarks’, *Proceedings of the 41st International Conference on Machine Learning*, 235, pp. 1456-1492. PMLR. https://proceedings.mlr.press/v235/an24a.html.
Ansari, I.A., Pant, M. and Ahn, C.W. (2016a) ‘Artificial bee colony optimized robust-reversible image watermarking’, *Multimedia Tools and Applications*, 76(17), pp. 18001-18025. doi:10.1007/s11042-016-3680-z.
Ansari, I.A., Pant, M. and Ahn, C.W. (2017) ‘Secured and optimized robust image watermarking scheme’, *Arabian Journal for Science and Engineering*, 43(8), pp. 4085-4104. doi:10.1007/s13369-017-2777-7.
Association for Computing Machinery (2018) *ACM Code of Ethics and Professional Conduct*. Official professional-body code: https://www.acm.org/code-of-ethics.
BCS, The Chartered Institute for IT (2026) *BCS Code of Conduct*. Official professional-body publication: https://www.bcs.org/membership-and-registrations/become-a-member/bcs-code-of-conduct/.
Bui, T., Agarwal, S. and Collomosse, J. (2023) ‘RoSteALS: Robust steganography using autoencoder latent space’, *2023 IEEE/CVF Conference on Computer Vision and Pattern Recognition Workshops*, pp. 933-942. IEEE. doi:10.1109/CVPRW59228.2023.00100.
Bui, T., Agarwal, S. and Collomosse, J. (2025) ‘TrustMark: Robust watermarking and watermark removal for arbitrary resolution images’, *Proceedings of the IEEE/CVF International Conference on Computer Vision*, pp. 18629-18639. Official CVF publication: https://openaccess.thecvf.com/content/ICCV2025/html/Bui_TrustMark_Robust_Watermarking_and_Watermark_Removal_for_Arbitrary_Resolution_Images_ICCV_2025_paper.html.
Caldelli, R., Becarelli, R. and Amerini, I. (2017) ‘Image origin classification based on social network provenance’, *IEEE Transactions on Information Forensics and Security*, 12(6), pp. 1299-1308. IEEE. doi:10.1109/TIFS.2017.2656842.
Carlini, N. and Wagner, D. (2017) ‘Towards evaluating the robustness of neural networks’, *2017 IEEE Symposium on Security and Privacy*, pp. 39-57. IEEE. doi:10.1109/SP.2017.49.
Coalition for Content Provenance and Authenticity (2023) *C2PA Technical Specification, version 1.3*. Official specification: https://c2pa.org/specifications/specifications/1.3/specs/C2PA_Specification.html.
Feng, J., Karaman, S. and Chang, S.-F. (2017) ‘Deep image set hashing’, *2017 IEEE Winter Conference on Applications of Computer Vision*, pp. 1241-1250. IEEE. doi:10.1109/WACV.2017.143.
Fernandez, P., Couairon, G., Jégou, H., Douze, M. and Furon, T. (2023) ‘The Stable Signature: Rooting watermarks in latent diffusion models’, *2023 IEEE/CVF International Conference on Computer Vision*, pp. 22466-22477. Official CVF publication record: https://openaccess.thecvf.com/content/ICCV2023/html/Fernandez_The_Stable_Signature_Rooting_Watermarks_in_Latent_Diffusion_Models_ICCV_2023_paper.html.
Guan, Z., Jing, J., Deng, X., Xu, M., Jiang, L., Zhang, Z. and Li, Y. (2023) ‘DeepMIH: Deep invertible network for multiple image hiding’, *IEEE Transactions on Pattern Analysis and Machine Intelligence*, 45(1), pp. 372-390. doi:10.1109/TPAMI.2022.3141725.
Hayes, J. (2018) ‘On visible adversarial perturbations & digital watermarking’, *2018 IEEE/CVF Conference on Computer Vision and Pattern Recognition Workshops*, pp. 1678-1687. IEEE. doi:10.1109/CVPRW.2018.00210.
International Organization for Standardization and International Electrotechnical Commission (2022) *ISO/IEC 27001:2022 Information security, cybersecurity and privacy protection - Information security management systems - Requirements*. Official standard record: https://www.iso.org/standard/82875.html.
International Organization for Standardization and International Electrotechnical Commission (2023a) *ISO/IEC 23894:2023 Information technology - Artificial intelligence - Guidance on risk management*. Official standard record: https://www.iso.org/standard/77304.html.
International Organization for Standardization and International Electrotechnical Commission (2023b) *ISO/IEC 25010:2023 Systems and software engineering - Systems and software quality requirements and evaluation (SQuaRE) - Product quality model*. Official standard record: https://www.iso.org/standard/78176.html.
International Organization for Standardization and International Electrotechnical Commission (2025) *Information technology - JPEG Trust - Part 1: Core foundation*. ISO/IEC 21617-1:2025. Official standard record: https://www.iso.org/standard/86831.html.
Jia, X., Wei, X., Cao, X. and Han, X. (2020) ‘Adv-watermark: A novel watermark perturbation for adversarial examples’, *Proceedings of the 28th ACM International Conference on Multimedia*, pp. 1579-1587. ACM. doi:10.1145/3394171.3413976.
Jiang, Z., Zhang, J. and Gong, N.Z. (2023) ‘Evading watermark based detection of AI-generated content’, *Proceedings of the 2023 ACM SIGSAC Conference on Computer and Communications Security*, pp. 1168-1181. ACM. doi:10.1145/3576915.3623189.
Jin, X., Lee, Y., Fiscus, J.G., Guan, H., Yates, A., Delgado, A. and Zhou, D. (2022) ‘MFC-Prov: Media forensics challenge image provenance evaluation and data analysis on large-scale datasets’, *Neurocomputing*, 478, pp. 34-47. doi:10.1016/j.neucom.2021.10.042.
Jing, J., Deng, X., Xu, M., Wang, J. and Guan, Z. (2021) ‘HiNet: Deep image hiding by invertible network’, *2021 IEEE/CVF International Conference on Computer Vision*, pp. 4713-4722. IEEE. doi:10.1109/ICCV48922.2021.00469.
Kulkarni, P.R., Mulani, A.O. and Mane, P.B. (2016) ‘Robust invisible watermarking for image authentication’, *Emerging Trends in Electrical, Communications and Information Technologies*, pp. 193-200. doi:10.1007/978-981-10-1540-3_20.
Li, Q., Wang, X., Ma, B., Wang, X., Wang, C., Gao, S. and Shi, Y. (2022) ‘Concealed attack for robust watermarking based on generative model and perceptual loss’, *IEEE Transactions on Circuits and Systems for Video Technology*, 32(8), pp. 5695-5706. doi:10.1109/TCSVT.2021.3138795.
Luo, X., Zhan, R., Chang, H., Yang, F. and Milanfar, P. (2020) ‘Distortion agnostic deep watermarking’, *2020 IEEE/CVF Conference on Computer Vision and Pattern Recognition*, pp. 13545-13554. IEEE. doi:10.1109/CVPR42600.2020.01356.
McKeown, S. and Buchanan, W.J. (2023) ‘Hamming distributions of popular perceptual hashing techniques’, *Forensic Science International: Digital Investigation*, 44, 301509. doi:10.1016/j.fsidi.2023.301509.
Moosavi-Dezfooli, S.-M., Fawzi, A. and Frossard, P. (2016) ‘DeepFool: A simple and accurate method to fool deep neural networks’, *2016 IEEE Conference on Computer Vision and Pattern Recognition*, pp. 2574-2582. IEEE. doi:10.1109/CVPR.2016.282.
Moosavi-Dezfooli, S.-M. et al. (2017) ‘Universal adversarial perturbations’, *2017 IEEE Conference on Computer Vision and Pattern Recognition*, pp. 86-94. IEEE. doi:10.1109/CVPR.2017.17.
Papernot, N. et al. (2016) ‘The limitations of deep learning in adversarial settings’, *2016 IEEE European Symposium on Security and Privacy*, pp. 372-387. IEEE. doi:10.1109/EuroSP.2016.36.
Papernot, N. et al. (2017) ‘Practical black-box attacks against machine learning’, *Proceedings of the 2017 ACM on Asia Conference on Computer and Communications Security*, pp. 506-519. ACM. doi:10.1145/3052973.3053009.
Pardhu, T. and Perli, B.R. (2016) ‘Digital image watermarking in frequency domain’, *2016 International Conference on Communication and Signal Processing*, pp. 208-211. IEEE. doi:10.1109/ICCSP.2016.7754123.
Qin, C., Chen, X., Ye, D., Wang, J. and Sun, X. (2016) ‘A novel image hashing scheme with perceptual robustness using block truncation coding’, *Information Sciences*, 361-362, pp. 84-99. doi:10.1016/j.ins.2016.04.036.
Sharma, R., Gupta, A.K., Singh, D., Verma, V.S. and Bhardwaj, A. (2017) ‘A robust image watermarking in contourlet transform domain’, *AIP Conference Proceedings*, 1897, article 020014. doi:10.1063/1.5008693.
Souppaya, M., Scarfone, K. and Dodson, D. (2022) *Secure Software Development Framework (SSDF) version 1.1*, NIST SP 800-218. doi:10.6028/NIST.SP.800-218.
Tancik, M., Mildenhall, B., Wang, T., Schmidt, D., Sivic, J. and Ng, R. (2020) ‘StegaStamp: Invisible hyperlinks in physical photographs’, *2020 IEEE/CVF Conference on Computer Vision and Pattern Recognition*, pp. 2117-2126. IEEE. doi:10.1109/CVPR42600.2020.00219.
Tang, Z., Huang, Z., Zhang, X. and Lao, H. (2017) ‘Robust image hashing with multidimensional scaling’, *Signal Processing*, 137, pp. 240-250. Elsevier. doi:10.1016/j.sigpro.2017.02.008.
Tang, Z., Chen, L., Zhang, X. and Zhang, S. (2019) ‘Robust image hashing with tensor decomposition’, *IEEE Transactions on Knowledge and Data Engineering*, 31(3), pp. 549-560. doi:10.1109/TKDE.2018.2837745.
United Kingdom (2018) *Data Protection Act 2018*. Official legislation: https://www.legislation.gov.uk/ukpga/2018/12/contents/enacted.
Windisch, M., Wassermann, J., Leba, M. and Stoicuta, O. (2024) ‘Hadamard error-correcting codes and their application in digital watermarking’, *Sensors*, 24(10), article 3062. doi:10.3390/s24103062.
Xu, Y., Mou, C., Hu, Y., Xie, J. and Zhang, J. (2022) ‘Robust invertible image steganography’, *2022 IEEE/CVF Conference on Computer Vision and Pattern Recognition*, pp. 7865-7874. IEEE. doi:10.1109/CVPR52688.2022.00772.
Yan, C.-P., Pun, C.-M. and Yuan, X.-C. (2016a) ‘Multi-scale image hashing using adaptive local feature extraction for robust tampering detection’, *Signal Processing*, 121, pp. 1-16. Elsevier. doi:10.1016/j.sigpro.2015.10.027.
Yan, C.-P., Pun, C.-M. and Yuan, X.-C. (2016b) ‘Quaternion-based image hashing for adaptive tampering localization’, *IEEE Transactions on Information Forensics and Security*, 11(12), pp. 2664-2677. IEEE. doi:10.1109/TIFS.2016.2594136.
Yang, Z., Zeng, K., Chen, K., Fang, H., Zhang, W. and Yu, N. (2024) ‘Gaussian Shading: Provable performance-lossless image watermarking for diffusion models’, *2024 IEEE/CVF Conference on Computer Vision and Pattern Recognition*, pp. 12162-12171. IEEE. doi:10.1109/CVPR52733.2024.01156.
Yuan, Z., Li, L., Wang, Z., Jiang, J. and Zhang, X. (2025) ‘Watermark removal attack against text-to-image generative model watermarking’, *IEEE Signal Processing Letters*, 32, pp. 1470-1474. doi:10.1109/LSP.2025.3554514.
Zhao, X. et al. (2024) ‘Invisible image watermarks are provably removable using generative AI’, *Advances in Neural Information Processing Systems*, 37. Official proceedings record: https://doi.org/10.52202/079017-0276.
Zhu, J., Kaplan, R., Johnson, J. and Fei-Fei, L. (2018) ‘HiDDeN: Hiding data with deep networks’, *European Conference on Computer Vision*, pp. 657-672. Springer. doi:10.1007/978-3-030-01267-0_40.

## Appendices

### Appendix A: Repository evidence index

Relevant evidence files are `CITATIONS.md`, `README.md`, `PROJECT_SUMMARY.md`, `transforms.py`, `transform_hash_robustness.py`, `trustmark_robustness.py`, `lsb_robustness.py`, `dct_robustness.py`, `ensemble_analysis.py`, `validate_experiment.py`, `run_1200_experiment.py`, `dashboard_api.py`, `output/results/*.csv`, and `output/results/final1200/*`. The report must identify the exact file version used for every final table.

### Appendix B: Artefact and reproducibility record

Record the operating system, Python version, package versions, CPU/GPU information, TrustMark package and model details, transform-module version, input-manifest checksum, compressed-file checksum, run log, validator output, and final working-tree state. Preserve raw outputs separately from derived summaries. Do not submit `.env`, passwords, model caches, or temporary files.

### Appendix C: Transform and payload specification

The final formatted report should reproduce the exact values from `transforms.py`. Payloads are `TM00001` for TrustMark and `LSB0001` for LSB; the DCT payload is defined by its implementation. Record image selection, seed derivation, padding colour, interpolation, JPEG handling, and whether the baseline row is included in every summary.

### Appendix D: Expanded validation checklist

1. Confirm manifest and unique image IDs.
2. Confirm final hash has 1,200 images and 768,000 compressed rows.
3. Confirm final LSB and DCT files are complete at 1,200 images.
4. Confirm the validated final1200 TrustMark file has 1,200 images and 97,200 baseline-inclusive rows.
5. Check duplicates, missing values, ranges, payload lengths, dimensions, conditions, and baseline rows.
6. Confirm corrected PDQ and raw TrustMark calculations.
7. Regenerate tables, figures, workbook, and dashboard summaries.
8. Reconcile all report numbers and captions against source files.

### Appendix E: Proposed final statistical table

For each method and condition, report image count, mean, median, standard deviation or robust dispersion, selected quantiles, image-level confidence interval, decode rate where applicable, false-positive rate on negatives, wrong-payload rate, and the declared aggregation rule. A table without those denominators should not be called a final performance table.

### Appendix F: Ethics, legal, and deployment checklist

Attach the institutional ethics classification or approval, use the prescribed non-plagiarism declaration, record dataset terms, record dependency and model licences, document any future identifier payload, define retention and deletion, prohibit unsupported authenticity wording, and keep the dashboard local unless security controls are implemented and reviewed.

### Appendix G: Future experiment protocol

Use the validated final1200 TrustMark file rather than appending partial rows, and retain its version and manifest checks. Run or re-run all pipelines only from the same declared image manifest and transform version. Validate each output before analysis. For geometric synchronisation, record no-alignment, oracle-alignment, and estimated-alignment arms. Add negative pairs, wrong payloads, composed operations, benign/removal labels, image-level intervals, calibration, payload and coding ablations, and bounded attack budgets as future work. Store the calibration/test split, run log, thresholds, settings, and checksums with the result pack.

### Appendix H: Figure and table publication gates

Every figure and table must identify its producer script and source file; state image count and evidence status; state baseline inclusion and aggregation; state threshold and hash normalisation; and be regenerated after any data change. Historical and final1200 panels must carry visibly different captions.

### Appendix I: User-action checklist before submission

- Complete the exact institutional ethics and non-plagiarism declaration details.
- Insert confirmed institution, school, module, supervisor, submission date, word count, and signature fields.
- Complete the proofreading confirmation and check all cross-references.
- Regenerate contents, list of figures, list of tables, glossary, figures, and tables.
- Run final validation and reconcile every numerical claim with its declared evidence set.
- Export the checked report to PDF and inspect page breaks, fonts, captions, and hyperlinks.
- Package the source artefact as the institution-required `.txt` files.
- Exclude `.env`, credentials, model caches, temporary files, and unapproved image redistribution.
- Keep any partial or superseded TrustMark files labelled as historical/limitation artefacts; report the validated final1200 CSV as final evidence.
- Confirm the final filename and artefact names follow the registration-number convention.
