# Final Project Report Draft

## Steganographic Signing and Filter Traceability in Digital Media

**Module:** 7COM1040-0509-2025, MSc Computer Science  
**Student:** Opaleye Toluwalope Abayomi  
**Student number:** 24163800  
**Supervisor:** Daniel Barry  
**Submission date:** [insert confirmed submission date]

### Proofreading declaration placeholder

I declare that this report has been proofread for spelling, grammar, structure, figure and table numbering, cross-references, and consistency of terminology.  
**Proofreader/name/date:** [complete before submission]

### Ethics and non-plagiarism declaration placeholder

I declare that the work and writing in this report are my own, that sources and external software are acknowledged, and that the submitted work complies with the institution's ethics, academic-integrity, and non-plagiarism requirements. The project uses a public research image dataset and does not report human-participant data.  
**Signed/name/date:** [complete using the required institutional declaration]

## Contents placeholder

The final formatted submission should generate a page-numbered contents list from the headings in this file. The intended order is: Abstract; Introduction; Literature Review; Methodology; Quality and Results; Evaluation and Conclusion; References; and Appendices A-G.

## Glossary placeholder

The final formatted submission should insert an alphabetised glossary here. Required entries include: bit accuracy, C2PA, decode presence, DCT, Hamming distance, LSB, perceptual hash, PSNR, soft binding, TrustMark, transform intensity, and watermark.

## Abstract

This project evaluates whether perceptual hashing and image watermarking retain useful verification signal after common image transformations. The implemented benchmark compares eight perceptual-hash variants with TrustMark, least-significant-bit (LSB) steganography, and a differential discrete cosine transform (DCT) baseline. The completed evidence set contains 100 deterministically selected MS-COCO validation images, 12 transform categories, 80 transform-intensity conditions, 64,000 hash rows, and 24,300 watermark rows. Hash robustness is measured by Hamming distance from the original-image hash. Watermark robustness is measured by raw bit accuracy and exact decode presence.

The completed 100-image results indicate that TrustMark and the stronger hash configurations retain useful signal under many photometric and compression transformations, while geometric transformations are more damaging, particularly to the watermark and classical baselines. TrustMark's reported mean raw bit accuracy is 0.9489 for the grouped non-geometric conditions and 0.7096 for the grouped geometric conditions. Excluding the untransformed baseline, the reported mean bit accuracies are 0.5949 for LSB and 0.7134 for DCT. These are descriptive results from the completed 100-image experiment, not population estimates.

The report explicitly corrects the project scale. The completed robustness result files cover 100 images, not 1,200. A 1,200-image manifest and execution runner exist, but a complete four-pipeline 1,200-image result set has not been validated in the current repository. No performance claim is made for 1,200 images. The contribution is therefore an auditable, reproducible prototype benchmark and dashboard demonstrating complementary verification signals, together with a candid account of measurement corrections, limitations, and the evidence required before the larger experiment can replace the current results.

## 1. Introduction

### 1.1 Background

Digital images are routinely resized, recompressed, filtered, cropped, rotated, or re-encoded. These operations can remove metadata and disturb embedded signals. A verification system therefore needs to distinguish between at least three different questions: whether a transformed image remains similar to a reference image, whether an embedded payload remains recoverable, and whether a result constitutes trustworthy provenance evidence rather than a claim that an image is true or authentic.

The C2PA Technical Specification describes provenance manifests, assertions, claims, signatures, and content bindings. It distinguishes hard bindings, such as cryptographic hashes, from soft bindings, such as fingerprints and watermarks [R1]. This project does not implement the C2PA manifest or trust infrastructure. It instead evaluates two classes of soft verification signal, a neural watermark and perceptual hashes, alongside classical baselines. The distinction is important throughout this report: a low hash distance or a recovered watermark is evidence of similarity or signal recovery under the tested conditions, not proof of authorship or provenance.

### 1.2 Problem statement

Watermarking and hashing methods can behave differently under the same transformation. A watermark may retain a payload while a hash changes, or a hash may remain stable after a payload has become undecodable. A practical research question is therefore not simply which method is best, but which signal survives which transformation and how the measurements should be interpreted.

### 1.3 Research question

To what extent do a neural watermark, perceptual hashes, and classical watermarking baselines retain recoverable verification signal when images undergo graduated photometric, compression, and geometric transformations?

### 1.4 Objectives

1. Review current standards, official guidance, and formally published work relevant to media provenance, watermarking, hashing, risk, and professional practice.
2. Implement a shared and deterministic image-transform pipeline.
3. Embed and decode a fixed TrustMark payload and compare it with LSB and DCT baselines.
4. Compute reference-to-transformed hash Hamming distances for eight hash variants.
5. Report raw bit accuracy, decode presence, encode quality, and hash distance using measures tied to the implementation.
6. Produce per-transform threshold and ensemble analyses and expose them through a dashboard.
7. Validate the results, document implementation corrections, assess ethical and professional issues, and define what evidence is needed before scaling the experiment.

### 1.5 Research process and decisions

The work proceeded iteratively. Initial implementation focused on the transform pipeline and hash comparison. TrustMark, LSB, and DCT were then integrated into the same transform harness. Inspection of intermediate outputs exposed two methodological problems: PDQ values had initially been serialised incorrectly, and the initial TrustMark measure represented exact decoded-payload success rather than raw pre-error-correction bit accuracy. These issues were corrected before the current result interpretation.

The project also made a scope decision after an attempted larger run encountered disk-space limitations. The complete comparable result set remained the 100-image run. A later manifest and runner were configured for 1,200 images, but configuration and partial inventory are not treated as completed experimental evidence. This decision prioritises traceability over presenting the intended scale as achieved.

### 1.6 Contribution and report structure

The contribution is a reproducible comparison of four implemented verification pipelines over a shared set of independently applied transformations, including letterbox padding, with threshold and ensemble views. The work also contributes an explicit audit trail for metric correction and sample-size correction. Section 2 reviews the relevant context. Section 3 describes implementation and validation. Section 4 reports quality controls and results. Section 5 evaluates the contribution and limitations. Appendices index the repository evidence and remaining requirements.

### 1.7 Research context and system boundary

The project sits between image processing, information security, and media provenance. Those areas overlap, but they are not interchangeable. Image processing asks whether an operation changes pixels in a controlled way. Watermarking asks whether information can be embedded and recovered. Perceptual hashing asks whether two images can be treated as related under a chosen similarity rule. Provenance standards ask how assertions about an asset can be bound to the asset and presented for trust decisions. A method can perform well in one of these roles and poorly in another.

This distinction determines the boundary of the system evaluated here. The benchmark does not attempt to establish the identity of a person, determine whether an image is factually true, or provide a certificate of origin. It evaluates signal persistence under a defined set of transformations. The dashboard then exposes the observations so that a researcher can inspect trade-offs. A future production service would need additional components: authenticated key management, a defined identity model, secure storage, access control, abuse handling, privacy controls, and a formally specified provenance representation. None of those components can be inferred from a successful watermark decode.

The project also distinguishes benign transformation from adversarial attack. Brightness adjustment, compression, or resizing may be routine operations in a content-delivery pipeline. Cropping, rotation, or padding may be deliberate or incidental. An attacker may select operations adaptively, combine them, or optimise them against a known detector. The current design tests a controlled set of isolated transformations and therefore addresses robustness screening rather than adversarial security. This is a deliberate boundary: it makes the current experiment interpretable, but it prevents broad claims about attack resistance.

### 1.8 Success criteria and decision logic

The original practical aim was to determine whether a hybrid arrangement could offer useful fallback behaviour when one verification signal degrades. The project translates that aim into observable criteria rather than a single universal success percentage. Hash stability is represented by normalised Hamming distance. Watermark persistence is represented by both raw bit accuracy and exact decode presence. The ensemble analysis applies a stated threshold and identifies a primary and fallback method for each transform-intensity condition.

This decision logic is useful for engineering comparison, but it has limitations. A threshold of 0.5 is a decision convention in the current analysis, not a security proof or a user-validated acceptance criterion. It treats all tested images and all transform levels through aggregate means, so it does not directly describe worst-case individual-image behaviour. It also does not assign a cost to false acceptance, false rejection, or the consequences of exposing a false provenance signal. Those issues would need a threat model and an application-specific operating point before deployment.

## 2. Literature Review

### 2.1 Provenance, authenticity, and soft bindings

C2PA Technical Specification 1.3 defines an architecture in which assertions and claims are associated with assets and protected by signatures and content bindings [R1]. A hard binding can detect changes to specified asset bytes, whereas a soft binding can help identify related or derived content. The project design is conceptually aligned with the soft-binding role of fingerprints and watermarks, but the prototype does not claim C2PA compatibility because it does not create manifests, certificates, signed claims, or a validation trust chain.

C2PA also places privacy, responsibility, security, accessibility, interoperability, and harms/misuse within its design goals [R1]. That guidance is relevant to a system that embeds identifiers. A payload can support traceability, but it can also become a tracking mechanism if it contains a user identifier or is retained without a clear purpose. The current experiment therefore uses fixed test payloads rather than real user identity data.

### 2.2 Neural watermarking

Bui, Agarwal and Collomosse present TrustMark as a learned image watermarking method designed for arbitrary-resolution images. Their formally published ICCV paper describes a spatio-spectral loss, a learned encoder/decoder, and robustness evaluation against perturbations while maintaining image quality above 43 dB on the paper's own benchmarks [R2]. This work motivated selection of TrustMark as the primary neural candidate, but published benchmark numbers were not substituted for local measurements. The current study uses the installed implementation, fixed payload, local image sample, and local transform definitions.

An important methodological implication is the distinction between raw bit accuracy and exact decoded payload. Error correction can allow a payload to decode exactly even when some raw bits are incorrect. Conversely, raw bit accuracy can remain above chance when exact decoding fails. The current TrustMark result file records both `bit_accuracy` and `decode_present`, which makes this distinction visible.

The security literature also shows why robustness should be tested against more than routine image transformations. Hayes [R16] and Jia et al. [R17] study adversarial perturbations designed to alter or evade watermark-related behaviour. Li et al. [R18] examine a concealed attack using a generative model and perceptual loss. These works support including attack-oriented transformations and reporting the threat model separately from ordinary corruption robustness. Jiang, Zhang and Gong [R19] further show that watermark-based detection of generated images can be evaded with small, visually inconspicuous post-processing changes.

Diffusion-specific work expands the evaluation space beyond post-hoc image embedding. Stable Signature fine-tunes a latent diffusion generator so generated images carry a detectable signature [R20], while Gaussian Shading embeds a watermark through the diffusion latent process and evaluates resistance to processing and erasure attempts [R21]. Yuan et al. provide a directly relevant recent removal attack against text-to-image generative-model watermarking [R22]. These sources are contextual security evidence, not substitutes for the local TrustMark, LSB and DCT measurements.

### 2.3 Perceptual hashing

Perceptual hashing represents image characteristics in a compact form intended to remain similar for selected near-duplicate transformations. The project operationalises robustness as Hamming distance between the reference hash of an original image and the hash of its transformed version. The eight tested variants are pHash, dHash, aHash, wHash, colorHash, vertical dHash, a simplified pHash variant, and PDQ. PDQ is represented as a 256-bit value in the current implementation; the other hash lengths follow their implementation records.

Hash similarity is not cryptographic authentication. A low Hamming distance can support a near-duplicate comparison, but it does not prove who created an image. A high distance can result from a benign transformation and does not itself establish malicious alteration. This is why the report treats hash results as a complementary verification signal rather than as a replacement for signed provenance.

### 2.4 Classical watermarking baselines

The LSB baseline writes a fixed payload into the least-significant bit plane of the red channel. It is intentionally simple and is expected to be fragile under operations that alter pixel values. The DCT baseline differentially encodes a fixed payload into mid-frequency coefficients. It is included as a frequency-domain comparator that may retain more signal under some photometric and compression operations but can still be affected by spatial reorganisation.

The baselines serve two purposes. They provide a lower-complexity comparison against TrustMark, and they show that a high-level claim about watermark robustness must be tied to a specific implementation, payload, transform, and metric. The results do not establish universal properties of all LSB or DCT methods.

### 2.5 Risk, quality, and professional responsibility

The NIST AI Risk Management Framework recommends considering trustworthiness throughout the design, development, use, and evaluation of AI systems [R3]. ISO/IEC 23894:2023 provides guidance for managing AI-related risk [R4], while ISO/IEC 27001:2022 provides a broader information-security management context [R5]. These sources support the report's decision to document intended use, measurement limitations, implementation corrections, and the risk of overclaiming.

The BCS Code of Conduct requires regard for public interest, privacy, security, wellbeing, competence, integrity, due care, and accurate representation of performance [R6]. The report applies those principles by separating completed results from configured targets, retaining failure cases, avoiding claims that a watermark proves truth, and identifying privacy and dual-use issues before any deployment claim.

### 2.6 Gap and contribution

The project does not claim to establish a literature-wide gap. Its narrower contribution is an auditable comparison over a shared transform matrix that includes letterbox padding and a threshold/ensemble analysis. Letterbox behaviour is a useful test case because padding changes layout without simply removing image content, but the current 100-image result is not sufficient to claim a general algorithmic ranking or a novel universal property. Replication on larger and more diverse datasets is required.

### 2.7 Synthesis of the reviewed context

The reviewed sources lead to three design principles. First, a verification signal must be described according to what it actually binds. A hash can provide a content-derived similarity value; a watermark can carry embedded information; a signed provenance manifest can bind structured claims to an asset. These mechanisms may be combined, but they should not be presented as equivalent. This is why the project reports hash and watermark outcomes separately before applying an ensemble rule.

Second, robustness is conditional. The TrustMark publication motivates a neural watermark because learned encoders can be trained against a range of perturbations [R2]. It does not imply that the installed model will survive every operation in a new evaluation. Similarly, C2PA's distinction between hard and soft bindings indicates that a soft fingerprint can be useful when an asset has been separated from its metadata, but it is not a substitute for a cryptographic binding [R1]. The benchmark consequently tests the local implementation and avoids importing external performance claims.

Third, governance is part of technical quality. NIST AI RMF and ISO/IEC 23894 frame risk as something to identify, measure, manage, and communicate rather than something solved by selecting a model [R3, R4]. ISO/IEC 27001 adds an information-security management perspective, particularly relevant to future payload storage and dashboard deployment [R5]. The BCS Code of Conduct makes the same issue concrete at professional level: competence includes recognising limits, and integrity includes not misrepresenting system performance [R6]. The report's sample-size correction and metric disclosure are therefore not editorial details; they are part of the system's reliability case.

### 2.8 Implications for the experimental design

The literature and standards support a layered evaluation rather than a single leaderboard. A method should be assessed for signal fidelity, robustness, interpretability, and operational risk. The current benchmark addresses the first two directly and addresses interpretability through the dashboard and threshold matrix. It addresses operational risk only at a preliminary level through the ethics, privacy, and software-engineering discussion. It does not evaluate identity credentials, key compromise, manifest recovery, or user-facing trust communication.

This synthesis also explains why the study uses simple baselines. If a neural method is compared only with another neural method, it is difficult to determine whether its advantage comes from the model, the embedding domain, or the metric. LSB provides a fragile spatial-domain reference. DCT provides a classical frequency-domain reference. Hashes provide a non-embedded comparison layer. The resulting comparison is not exhaustive, but it makes the source of some observed differences easier to discuss.

## 3. Methodology

### 3.1 Dataset and sample selection

The completed result CSVs use the first 100 JPG images in lexicographic filename order from the MS-COCO 2017 validation set. The repository describes 5,000 images as available in that split. Selection is deterministic, and the transformation code derives deterministic seeds from image ID, transform name, and intensity for random operations. The experiment does not recruit participants or collect new personal data.

The repository also contains `output/results/image_manifest.json` with 1,200 image records and a `run_1200_experiment.py` runner configured to request 1,200 images. These artefacts show that a larger inventory and execution path were prepared. They do not show that all four pipelines completed, passed coverage validation, and generated the reported results for 1,200 images. All numerical results in this report are therefore explicitly labelled as 100-image results.

### 3.2 Transform design

The single-source-of-truth module `transforms.py` defines 12 categories and 80 transform-intensity pairs:

| Category | Settings in the current implementation |
|---|---|
| Brightness | 0.5, 0.7, 0.85, 1.15, 1.5, 2.0 |
| Contrast | 0.5, 0.7, 0.85, 1.15, 1.5, 2.0 |
| Saturation and vibrancy | 8 settings each from 0.2 to 1.8 |
| Gaussian blur | radius 0.5 to 5.0, 6 settings |
| Salt-and-pepper noise | density 0.01 to 0.15, 6 settings |
| JPEG compression | quality 95 to 5, 8 settings |
| Rotation | 1 to 90 degrees, 8 settings |
| Scaling | 0.25x to 3.0x, 6 settings |
| Centre crop and random crop | removal fraction 0.1 to 0.8, 8 settings each |
| Letterbox | black and grey padding |

Brightness, contrast, colour, blur, noise, and JPEG settings model photometric or encoding changes. Rotation, scaling, cropping, and letterbox model spatial or geometric changes. Categories are applied independently, not as cascaded attacks. The choice makes per-transform interpretation clearer but limits the study's relevance to compound or adaptive attacks.

### 3.3 Pipeline implementation

The hash pipeline computes each hash on the original and transformed image and stores the hash values and Hamming distance. TrustMark embeds the fixed payload `TM00001`, applies the transform, and records encode mean squared error, PSNR, decoded payload, decode presence, and raw bit accuracy. The LSB pipeline uses the fixed `LSB0001` payload in the red-channel least-significant bit plane. The DCT pipeline differentially embeds a payload in mid-frequency coefficients and reverses that process for decoding.

The dashboard is a FastAPI-served, CSV-backed prototype. It provides overview, per-transform, ensemble-matrix, and per-image views. The repository also contains a sign/verify interface scaffold. The PostgreSQL migration script exists but has not been executed against a live PostgreSQL instance. The dashboard is consequently evaluated as a research visualisation, not a production signing service.

### 3.4 Metrics and decision rules

- **Hash Hamming distance:** the number of differing bits between transformed and reference hash values.
- **Hash bit-error fraction:** Hamming distance divided by the relevant hash length.
- **Raw bit accuracy:** the proportion of expected TrustMark packet bits recovered before error correction.
- **Decode presence:** whether the implementation reports a valid decoded payload.
- **PSNR:** an encode-quality metric, not a robustness score.
- **Threshold success:** watermark mean bit accuracy above 0.5, or hash mean bit-error fraction below 0.5, according to the analysis definition.

For the ensemble analysis, the hash decision uses the worst-algorithm mean rather than only a pooled hash mean. This prevents several robust 64-bit hashes from masking a weaker algorithm such as PDQ. The matrix contains one row per transform-intensity condition and records best method, fallback method, method scores, and pass/fail flags.

### 3.5 Validation and correction process

The validation script checks image coverage, expected rows, and duplicate keys when run with the correct expected image count. The current CSV row counts are 64,000 for hashes, 8,100 each for TrustMark, LSB, and DCT, and 80 for the ensemble matrix. The combined total reported by the project summary is 88,380 rows.

Two corrections materially affect interpretation. First, the PDQ serialisation was corrected to represent each dimension as one bit rather than an incorrect multi-character representation. Second, the TrustMark measure was corrected to access decoder output before error correction, rather than reporting only exact payload recovery. These corrections are reflected in the current code/results interpretation and must be retained in any larger rerun.

### 3.6 Rationale for the sample and selection rule

The completed sample is a convenience sample from a public benchmark dataset rather than a random sample of all digital images. Filename ordering provides a simple reproducible selection rule and avoids an undocumented manual choice of visually appealing images. It also makes reruns comparable if the same source files are available. The limitation is that the first 100 filenames may not represent the visual, semantic, or technical diversity of the whole dataset. The report therefore treats the sample as an engineering test set, not as a representative estimate of real-world image performance.

The larger 1,200-image configuration was intended to reduce sampling uncertainty and make subgroup behaviour more informative. It was not used to justify the current results because the repository does not contain complete, validated outputs for every method at that scale. This is an important distinction between study design and study execution: an intended sample can describe what the experiment was supposed to test, but only a validated result set can support a numerical conclusion.

### 3.7 Semantics of the transform matrix

The transform values have method-specific meanings and should not be interpreted as a common linear severity scale. A brightness value of 0.5 is not directly comparable with JPEG quality 50, a blur radius of 2.0, or a crop-removal fraction of 0.5. Each parameter is meaningful within its own transform family. The analysis therefore compares methods at the same named condition and uses per-transform threshold tables rather than constructing one global severity ranking.

Brightness and contrast use Pillow enhancement operations. Values below 1 reduce the corresponding property and values above 1 increase it. Saturation uses colour enhancement, while vibrancy applies a non-linear HSV saturation adjustment that favours less-saturated pixels. These two colour operations are related but not interchangeable, so they remain separate categories.

Gaussian blur applies a radius parameter. Salt-and-pepper noise uses a density parameter and randomly assigns salt or pepper values at selected pixel positions. The random generator is seeded from image and condition identifiers, so the same condition can be reconstructed. JPEG compression writes a temporary JPEG at the requested quality and reopens it before downstream measurement. This makes the transform include an actual re-encoding step rather than a symbolic quality label.

Rotation uses an expanded canvas for the 90-degree case and a non-expanded operation for other tested angles, with a neutral fill colour. Scaling uses LANCZOS resizing and changes image dimensions. Centre cropping removes the specified fraction from both dimensions around the centre. Random cropping removes the same fraction but selects the retained region with a deterministic random generator. Letterbox creates a square canvas, preserves the original image dimensions within that canvas, and uses either black or grey padding. These implementation details matter because they determine which pixels are changed and how much spatial alignment is disturbed.

The transform design deliberately includes both content-preserving operations and spatial operations. This enables a comparison between signal degradation caused primarily by value changes and degradation caused by changes in coordinate layout. It does not establish a formal taxonomy of attacks, and the selected parameters do not cover every codec, interpolation method, or crop policy.

### 3.8 Pipeline execution and data flow

Each pipeline begins with the same selected source image and condition. The hash pipeline computes a reference representation once for the original image and then computes a transformed representation for each condition. The Hamming distance is stored with image ID, filename, condition, pipeline version, algorithm, dimensions, and aspect ratio. This structure allows an individual image, algorithm, transform, and intensity to be traced back to a row.

The watermark pipelines encode a payload into the source image before transformations are applied. They retain encode metrics and then decode the transformed result. The baseline row represents the untransformed encoded image. This baseline is necessary because a method may fail during embedding or decoding even without an external transformation. The transformed rows then isolate the additional effect of the selected operation, subject to the implementation's own encode and decode behaviour.

The three watermark implementations do not have identical embedding mechanisms. TrustMark uses a learned model and a packet structure with error-correction information. LSB writes directly to a colour-channel bit plane. DCT uses differential relationships between frequency coefficients. Comparing their bit accuracies is useful only as a comparative experiment because the payload construction, decoder, and failure semantics differ. The report avoids claiming that a score is a universal measure of information-theoretic capacity or security.

### 3.9 Reproducibility controls

Reproducibility is addressed at several levels:

1. The transform definitions are centralised in one module rather than duplicated across pipeline scripts.
2. The image selection rule is deterministic and recorded in the project documentation.
3. Random transforms derive seeds from stable identifiers rather than relying on process-randomised language-level hashes.
4. Result rows include pipeline version and image metadata.
5. The validation script checks expected coverage and duplicate keys before analysis.
6. The raw CSVs are preserved separately from the summary and dashboard layers.
7. Analysis scripts generate threshold and ensemble artefacts from the result files rather than from manually copied table values.
8. The report identifies the model/software details that must be frozen for a final rerun.

These controls reduce accidental variation but do not prove that the experiment is independently reproducible. The source dataset must be the same, package versions can affect image processing, the TrustMark model must be the same, and temporary file behaviour must not alter outputs. The final evidence pack should therefore contain environment information and, where practicable, checksums for model and input artefacts.

### 3.10 Software-engineering decisions

The implementation favours a small number of explicit scripts over a large framework. This reduces indirection during experimental debugging and makes each output file's producer visible in the README. The shared transform module is a maintainability decision: if one script silently uses a different rotation or crop implementation, cross-method comparison becomes invalid. Centralising definitions creates a single point for inspection and reduces configuration drift.

CSV is used as the current interchange format because it is inspectable, portable, and sufficient for the completed result volume. It also makes the dashboard usable without a live database. The cost is weaker schema enforcement, potential type coercion, and less suitable concurrent access. The database migration script indicates a future persistence path, but because it has not been executed against a live PostgreSQL instance, database performance and operational security are outside the demonstrated scope.

The dashboard separates data loading and presentation through a FastAPI backend and a browser frontend. This supports per-image inspection and makes summary calculations visible to users. It does not yet provide authenticated signing, secure upload handling, access control, rate limiting, audit logging, or a certificate-backed provenance workflow. Treating those absent features as future engineering work avoids conflating a visual prototype with a deployable service.

### 3.11 Testing strategy

Testing in this project has three related meanings. Unit-level confidence comes from inspecting transform functions, checking dimensions and output types, and confirming deterministic seeding. Pipeline-level confidence comes from completing encode-transform-decode or hash-reference-transform comparisons across the selected matrix. Dataset-level confidence comes from row-count, image-coverage, and duplicate-key validation.

The validation script is deliberately strict about expected image count. This is useful because a partial larger run should fail loudly instead of being analysed as if it were complete. It also means the command argument is part of the evidence: validating with 100 cannot establish 1,200-image coverage. The same principle applies to the analysis scripts. A generated matrix can be numerically consistent with its input while the input itself is incomplete, so coverage validation must precede interpretation.

Additional checks are required for the final experiment. The result files should be checked for missing metric values, unexpected transform names, impossible bit lengths, duplicate image-condition keys, baseline rows, and inconsistent image manifests. The number of unique image IDs should be reported separately from the number of rows. A row count alone can be inflated by duplicated records and therefore is not sufficient evidence of coverage.

### 3.12 Statistical interpretation plan

The current report presents means and rates because those summaries are already produced or documented by the repository. Means are useful for identifying broad degradation patterns, but they can conceal individual-image failures and non-monotonic behaviour. The threshold analysis acknowledges that degradation is not always monotonic and records both first-crossed and worst observed intensities. This is preferable to assuming that every transform has a smooth response.

For a final larger analysis, the aggregation unit should be declared in advance. Image-level observations are not necessarily independent across methods because the same image is evaluated by every pipeline. Conditions also contain repeated measurements across images. A final report should distinguish pooled rows, per-image means, per-condition means, and rates calculated from binary decode flags. Dispersion and uncertainty should be reported alongside means where the data support it. No such additional numerical results are invented in this draft; they are specified as work required for the validated 1,200-image analysis.

## 4. Quality and Results

### 4.1 Quality assurance

Quality assurance was based on shared transform definitions, deterministic seeding, pipeline version fields, raw CSV preservation, row-count checks, duplicate-key validation, and separate analysis scripts. The design also retains baseline rows so that transformed performance can be distinguished from encode/decode behaviour without a transform. These controls improve reproducibility but do not replace independent replication or uncertainty analysis.

The reported results are descriptive. The current repository does not provide a complete inferential analysis with confidence intervals, a preregistered analysis plan, or a validated 1,200-image run. Claims are therefore limited to the selected images and tested conditions.

### 4.2 Completed coverage

The completed benchmark covers 100 images, 12 transform categories, 80 transform-intensity conditions, 64,000 hash rows, 8,100 TrustMark rows, 8,100 LSB rows, 8,100 DCT rows, and 80 ensemble rows. The result files are the evidence source for the numbers below. The 1,200-image manifest is not used to enlarge the sample size.

### 4.3 Perceptual-hash results

The current results report overall mean Hamming distances of 4.62 bits for pHash, 4.67 bits for dHash, 3.59 bits for aHash, and 40.47 bits for PDQ. The corresponding reported mean changed-bit percentages are 7.2%, 7.3%, 5.6%, and 15.8%, using the bit lengths applied by the analysis. These averages describe the current test matrix and should not be generalised beyond it.

Geometric conditions are among the most difficult cases in the reported summary. For centre cropping, PDQ is reported at 120.63 bits (47.1%) mean Hamming distance, while aHash and dHash are reported at 10.52 bits (16.4%) and 13.59 bits (21.2%). For rotation, PDQ is reported at 95.10 bits (37.1%). Under letterbox padding, the reported values are 9.03 bits (14.1%) for aHash, 9.79 bits (15.3%) for dHash, 9.40 bits (14.7%) for pHash, and 95.58 bits (37.3%) for PDQ. The cautious interpretation is that aHash was more stable than PDQ for this particular letterbox test; the result does not establish a general ranking.

### 4.4 TrustMark results

For the completed 100-image results, mean TrustMark bit accuracy is reported above 0.96 for brightness (0.9687), contrast (0.9689), Gaussian blur (0.9696), saturation (0.9929), and vibrancy (0.9663). Scaling is reported at 0.9946 mean bit accuracy and a 99% decode rate. JPEG compression is reported at 0.9028 mean bit accuracy and a 64% decode rate. Salt-and-pepper noise is reported at 0.8605 mean bit accuracy and a 32% decode rate.

Geometric conditions are weaker. Rotation is reported at 0.6453 mean bit accuracy and 26% decode presence; centre crop at 0.6578 and 27%; random crop at 0.6448 and 25%; and letterbox at 0.5775 and 13%. The grouped summary reports 0.9489 mean bit accuracy and 77% decode presence for non-geometric conditions, compared with 0.7096 and 39% for geometric conditions. These grouped values depend on the pooling choices in the analysis and must be regenerated if the experiment is expanded.

### 4.5 LSB and DCT results

Excluding the untransformed baseline, the reported LSB mean bit accuracy is 0.5949 and its overall decode rate is 6%. The reported DCT mean bit accuracy is 0.7134 and its overall decode rate is 14%. DCT retains more signal than LSB for several photometric and compression conditions, but both baselines approach the 0.5 decision boundary under important geometric conditions. These results justify their role as comparative baselines, not as recommended production methods.

### 4.6 Ensemble results

The ensemble decision matrix has 80 rows. Its reported pass-count summary is 56 conditions with all four methods passing, 21 with three passing, and 3 with two passing. LSB is reported as passing 75% of conditions and DCT 91.2%. The reported discussion identifies TrustMark as the best method in nearly all conditions and hash as the usual fallback; the CSV matrix remains authoritative if a prose summary differs. Pass rates depend on the specified thresholds and worst-hash rule and are not operational authentication accuracy.

### 4.7 Quality and implementation outcome

The dashboard makes method and transform trade-offs inspectable through overview, per-transform, ensemble, and per-image views. It is useful as a research demonstration and supports examination of individual result rows. However, the CSV-backed implementation, unexecuted database migration, and unvalidated sign/verify service mean that it should not be described as a production platform.

### 4.8 What must be replaced after the complete 1,200-image run

After all four pipelines have completed on 1,200 images and `validate_experiment.py --image-count 1200` has passed without duplicate-key or coverage errors, the following report content must be replaced, not merely supplemented:

1. The Abstract sample size, row counts, and every result summary currently labelled 100-image.
2. The Introduction scope correction and all statements describing 1,200 as configured or unvalidated.
3. Dataset, coverage, methodology, quality-assurance, and appendix manifest descriptions.
4. All hash, TrustMark, LSB, DCT, threshold, ensemble, and dashboard numerical tables and figures.
5. The Evaluation and Conclusion claims, including any uncertainty analysis based on the larger sample.
6. The data-needed list items that are satisfied by the final run, while retaining any unresolved limitations.

The replacement must include the final run log, matching manifest, package/model versions, corrected PDQ and raw TrustMark metric checks, missing-value and duplicate-key checks, and a reconciliation of every report table against the regenerated CSVs. Until those conditions are met, this report remains a final-report draft based on the completed 100-image evidence set.

### 4.9 Critical interpretation of the observed patterns

The results suggest that transformation semantics matter more than a simple method hierarchy. TrustMark performs strongly for several value and encoding changes but is less reliable when the relationship between watermark location and image coordinates is disrupted. LSB is expected to be sensitive to any operation that changes pixel values or resamples the image, and its low aggregate decode rate is consistent with that design. DCT retains more signal for some changes because coefficient relationships can be less directly affected by moderate value adjustments, but the baseline still depends on spatial correspondence and is weakened by crop, rotation, and scaling.

The hash results show why pooled rankings require caution. A pooled mean can be dominated by the majority of algorithms with the same bit length and can hide a weak member. The threshold analysis therefore uses a worst-algorithm view for ensemble decisions. This is conservative for a system that promises all configured hash checks, but it is not necessarily the correct rule for every application. A deployment that selects the best available hash could use a different rule; a deployment that requires agreement across all hashes may reasonably use the weakest-link rule. The report treats the current rule as an explicit experimental choice rather than an objective property of hashing.

The letterbox result is informative because it separates padding from content removal. The reported aHash distance is lower than the reported PDQ distance under this particular test, despite PDQ's longer representation. That observation is plausible as a condition-specific result, but several alternative explanations remain: the effect of the padding colour, aspect-ratio distribution in the sample, the implementation details of each hash, and aggregation across intensities. The result should therefore prompt controlled replication with multiple padding colours, image aspect ratios, and samples rather than be promoted to a general algorithmic conclusion.

The ensemble summary also needs careful interpretation. A condition can have several methods above their thresholds while still producing poor individual-image outcomes. Conversely, a method can have a mean below a threshold while some images decode correctly. The decision matrix is valuable for mapping broad operating regions, but it does not report calibration, confidence, or the cost of an incorrect decision. A future evaluation should include per-image confusion-style summaries and application-specific error costs before using the matrix to select a production method.

### 4.10 Encode quality and robustness are separate dimensions

PSNR and encode mean squared error appear in the watermark result files because an embedded signal should not be evaluated only by whether it survives. A method that decodes reliably but visibly damages an image may be unacceptable. Conversely, a high PSNR does not establish robustness, and a robust payload is not necessarily imperceptible to every observer or downstream model. The current report does not invent a new imperceptibility result; it records encode-quality fields and identifies final quality summaries as evidence still requiring explicit presentation.

This separation is especially important when comparing TrustMark with LSB and DCT. Their embedding processes, payload structures, and image distortions differ. A fair engineering comparison should place recovery and quality side by side, report the payload and image conditions, and state whether metrics are computed on all rows or only successful encodes. The final larger run should preserve these distinctions rather than collapse them into a single score.

### 4.11 Quality gates for table and figure publication

Before any table or figure is included in the final formatted report, it should pass four gates. First, the source CSV and the generating script must be identified. Second, the sample and row coverage must match the report's declared experiment. Third, the aggregation rule, baseline inclusion, and threshold must be stated in the caption or surrounding text. Fourth, the displayed values must be regenerated after the final run rather than manually edited from the 100-image draft.

For the current draft, captions should say **validated 100-image results** wherever they present the existing numerical outcomes. Once the complete larger run passes validation, captions and text should be replaced using the larger CSVs, and old values should not remain in nearby prose as a comparison unless the comparison is deliberately labelled. The exact replacement checklist is in Section 4.8 and Appendix G.

### 4.12 What the current results do and do not establish

The current results establish that the four implemented pipelines produce different measured responses under the current transformations and that geometric conditions are important failure cases. They establish that the pipeline can generate inspectable row-level evidence for the completed sample. They also establish that implementation details, such as PDQ representation and raw TrustMark measurement, materially affect interpretation.

They do not establish that TrustMark is universally superior, that aHash is generally preferable to PDQ, that an ensemble will identify authentic content, or that the system is resistant to adaptive attacks. They do not establish performance on the full MS-COCO validation split or on 1,200 images. This boundary is maintained throughout the report because the strongest contribution of the project is its auditability, not an unsupported universal claim.

## 5. Evaluation and Conclusion

### 5.1 Interpretation

The completed benchmark demonstrates a measurable difference among the tested neural watermark, perceptual hashes, and classical baselines under the implemented transformations. TrustMark generally retains higher raw bit accuracy than LSB and DCT in content-preserving conditions. Hashes retain relatively low average distance for many such conditions. Cropping, rotation, and letterbox padding expose important weaknesses, so the project cannot claim universal robustness.

The complementary design is more defensible than a single-method claim. A watermark can provide payload recovery, while a hash can provide a near-duplicate signal when the payload is unavailable. The ensemble is still only a thresholded analysis of this experiment; it is not a cryptographic trust system and cannot establish authenticity on its own.

### 5.2 Limitations

The completed evidence is limited to 100 mostly natural MS-COCO validation images selected by filename order. Results for medical, synthetic, text-heavy, or other image domains are unknown. Only one TrustMark implementation/model configuration was evaluated. Transformations were applied independently, so cascaded, adaptive, and adversarial attacks were not tested. Payload sizes were fixed, and the effects of payload variation are unknown. The report does not provide a complete inferential uncertainty analysis. The dashboard is CSV-backed, the database migration is unexecuted, and C2PA interoperability is not implemented.

The sample-size limitation is especially important. The presence of a 1,200-image manifest is not evidence that 1,200-image performance has been measured. The conclusion must remain tied to the completed 100-image CSVs until the replacement conditions in Section 4.8 are met.

### 5.3 Ethical and professional evaluation

The experiment does not involve human participants or new personal-data collection. Nevertheless, public images can depict people and have rights conditions. Future payloads containing user identifiers, timestamps, or locations would require explicit purpose, lawful-basis, retention, access, and deletion decisions. The BCS principles of public interest, competence, integrity, due care, privacy, and accurate performance representation are addressed by the report's scope correction, metric disclosure, and limitation statements [R6].

### 5.4 Ethics, legal, and BCS mapping

The ethical position is not that the dataset is automatically risk-free because it is public. The current work does not contact people, infer sensitive attributes, collect participant responses, or attach identities to the fixed test payloads. It nevertheless processes images that may contain recognisable people and copyrighted material. The appropriate control is to limit use to the documented research purpose, avoid unnecessary redistribution, preserve the dataset's terms, and obtain institutional confirmation of the ethics classification. If future payloads contain personal data, the Data Protection Act 2018 provides the legal context for the report's purpose, access, retention, and deletion controls [R26]. The declaration placeholder at the front of this report must be completed using the required institutional wording rather than replaced by an informal assertion.

The legal and governance boundary is similarly limited. The report does not provide advice on copyright, data protection, or lawful deployment. It records that dataset terms, dependency licences, and image-level rights must be checked before redistributing outputs or using real customer content. A future service that embeds a user identifier would need a documented purpose and lawful basis, data minimisation, retention and deletion rules, access controls, and a process for responding to misuse or incorrect verification. The current prototype does not implement those controls.

The BCS principles map to concrete engineering decisions. Public interest is addressed by discussing false confidence, surveillance-adjacent use, and the distinction between verification signal and truth. Professional competence and integrity are addressed by identifying the corrected TrustMark metric, the PDQ serialisation correction, and the incomplete larger run. Duty of care is addressed by not presenting a CSV dashboard as a production security service. Accurate representation is addressed by labelling all current results as validated 100-image results. Duty to the profession is addressed by preserving reproducibility information and acknowledging limitations rather than hiding them behind a favourable ranking [R6]. These choices are also consistent with the ACM requirements to avoid harm, respect privacy, and be honest about system limitations [R27].

### 5.5 Project-management reflection

The project used a phased but iterative management approach. Requirements and literature review established the intended role of the system. Implementation then proceeded through transform functions, hash comparison, watermark integration, baseline integration, analysis, dashboard construction, and reporting. The sequence was not strictly linear: metric inspection caused changes to the TrustMark measurement, and validation concerns caused the sample-size claim to be narrowed. This is a normal research-engineering interaction because a result cannot be treated as complete until the measurement procedure has been understood.

The strongest management decision was to separate artefact existence from task completion. A runner, manifest, or dashboard can exist before the underlying experiment is complete. The report therefore distinguishes code that can request 1,200 images from a result set that has been executed and validated on 1,200 images. This distinction prevented an attractive but unsupported completion claim.

The main management weakness was the late discovery that scaling the experiment created storage constraints and that the original metric did not represent the intended construct. Earlier milestone gates could have required: a pilot with known expected payload behaviour, a row schema review, storage estimation, a manifest-to-result coverage check, and a metric test against synthetic or untransformed examples. Those controls should be incorporated before the larger rerun. The project's current validation script is a useful correction, but it is strongest when invoked before analysis rather than after figures have been drafted.

The dashboard and database work also illustrates a prioritisation trade-off. A CSV-backed dashboard delivered inspectability without requiring database deployment and therefore supported the research objective within available time. The cost is that persistence, access control, concurrent use, and operational security remain unvalidated. The final project claim should reflect that trade-off: the software deliverable is a functioning research prototype, not a finished commercial system.

### 5.6 Threats to validity

**Construct validity.** The metrics are proxies for the constructs of interest. Hamming distance measures representation change, not authenticity. Raw bit accuracy measures decoder agreement with an expected packet, not user-perceived trust. Decode presence is an exact implementation outcome and may depend on error correction. PSNR measures one aspect of encode quality and does not replace visual or perceptual assessment. These limitations are mitigated by reporting multiple metrics, but they cannot be eliminated by aggregation.

**Internal validity.** The shared transform module and deterministic seeding reduce differences between pipelines. The two implementation corrections reduce known measurement error. However, the pipelines have different payload structures and embedding mechanisms, temporary JPEG processing depends on library behaviour, and image dimensions change under several operations. A method may be affected by the transform implementation rather than by an abstract attack category. Re-running with alternative libraries, codecs, interpolation choices, and fill policies would test the stability of these findings.

**External validity.** The current sample consists of 100 images from one validation split and is not representative of all media. Natural photographs may be easier or harder for a method than diagrams, text, screenshots, medical images, synthetic images, or video frames. The 1,200-image configuration would improve coverage within the same source domain, but it would not by itself validate performance across other domains.

**Statistical validity.** Means over rows can obscure per-image failures and can give disproportionate weight to conditions with more intensity steps. Decode rates and bit accuracies answer different questions. Thresholds were chosen for the current analysis and were not derived from a user-risk study. Consistent with the American Statistical Association's guidance on transparent methods, exploratory versus confirmatory work, multiple comparisons, and reproducibility [R23], the final experiment should document its aggregation unit, uncertainty treatment, and any multiple-comparison decisions before numerical tables are regenerated.

**Conclusion validity.** The observed hierarchy is conditional on implementation, payload, sample, and transform. A conclusion such as “TrustMark is robust” is too broad; the defensible statement is that TrustMark retained more measured signal than the baselines for specified conditions in the completed 100-image benchmark. The report deliberately uses this narrower form.

**Reproducibility validity.** Code and CSVs are available in the repository, but a complete independent reproduction still depends on obtaining the same source images, package versions, model files, and environment. The final evidence pack should record those dependencies and use checksums where possible. A successful local validation run is necessary but does not prove independent reproduction.

### 5.7 Future work

The first priority is the complete 1,200-image run. It should be executed serially or in a storage-aware design, produce complete outputs for all four pipelines, pass coverage and duplicate-key validation, and regenerate every affected analysis artefact. It should not simply append rows to the current CSVs without a manifest and version check. Section 4.8 gives the replacement procedure.

The second priority is a more informative analysis. Per-image distributions, dispersion, uncertainty intervals, and stratification by aspect ratio or image dimensions would show whether the mean patterns are driven by a small number of images. Threshold selection should be justified against an application cost model. If the ensemble is intended to make decisions, its false-acceptance and false-rejection behaviour should be evaluated on labelled positive and negative pairs rather than inferred from transform pass flags.

The third priority is attack and domain expansion. Cascaded operations such as rotation followed by JPEG compression, crop followed by scaling, and adaptive combinations would more closely test a hostile or lossy media pipeline. Additional image domains would test generality. Different payload lengths and payload types would expose the relationship between capacity, imperceptibility, and recovery. Multiple TrustMark configurations or independent watermark methods would prevent a method-specific result from being mistaken for a category-level result.

The fourth priority is provenance integration. A future implementation could study how a soft hash or watermark assists recovery of a manifest while still using a cryptographic binding for integrity. That work would need to follow the relevant C2PA version, use test keys and non-production identities, and report what the validator can actually establish. It would also need privacy-preserving payload design, key rotation and revocation procedures, audit logging, secure upload handling, and user-facing explanations of uncertainty. Any claim that a future AI-enabled verification service is compliant or high-assurance would additionally require a use-specific assessment against the governance, transparency, and oversight obligations introduced by the EU AI Act [R28].

The fifth priority is software hardening. The dashboard should gain schema validation, explicit error handling for corrupt or unsupported images, resource limits, authentication and authorisation if exposed beyond localhost, and security testing. These controls follow the secure-development and quality-evaluation concerns in NIST's SSDF [R24] and ISO/IEC 25010's product-quality model [R25]. Database deployment should be tested separately from the CSV path. These improvements would change the operational risk profile, but they would not change the current experimental results unless the data pipeline itself is altered and rerun.

### 5.8 Conclusion

Within the completed 100-image MS-COCO benchmark and its 80 independently applied transform conditions, TrustMark and perceptual hashing provide useful complementary verification signals, while LSB and DCT are weaker under several transformations. The evidence supports a research prototype and an auditable comparison, but not production-grade provenance, universal attack resistance, C2PA compatibility, or performance claims over 1,200 images. The work's most significant practical outcome is therefore not a universal method ranking, but a measured and reproducible account of where each tested signal succeeds, degrades, and requires further validation.

## References

The references below are limited to official standards, government publications, professional-body publications, and formally published peer-reviewed research. All are dated 2018 or later.

**[R1]** Coalition for Content Provenance and Authenticity (2023) *C2PA Technical Specification, Version 1.3*. Official specification. Available at: https://c2pa.org/specifications/specifications/1.3/specs/C2PA_Specification.html (accessed 10 August 2026).

**[R2]** Bui, T., Agarwal, S. and Collomosse, J. (2025) 'TrustMark: Robust Watermarking and Watermark Removal for Arbitrary Resolution Images', *Proceedings of the IEEE/CVF International Conference on Computer Vision (ICCV)*, pp. 18629-18639. Official open-access publication: https://openaccess.thecvf.com/content/ICCV2025/html/Bui_TrustMark_Robust_Watermarking_and_Watermark_Removal_for_Arbitrary_Resolution_Images_ICCV_2025_paper.html (accessed 10 August 2026).

**[R3]** National Institute of Standards and Technology (2023) *Artificial Intelligence Risk Management Framework (AI RMF 1.0)*, NIST AI 100-1. U.S. Department of Commerce. Available at: https://doi.org/10.6028/NIST.AI.100-1 (accessed 10 August 2026).

**[R4]** International Organization for Standardization and International Electrotechnical Commission (2023) *ISO/IEC 23894:2023 Information technology - Artificial intelligence - Guidance on risk management*. Official standard record: https://www.iso.org/standard/77304.html (accessed 10 August 2026).

**[R5]** International Organization for Standardization and International Electrotechnical Commission (2022) *ISO/IEC 27001:2022 Information security, cybersecurity and privacy protection - Information security management systems - Requirements*. Official standard record: https://www.iso.org/standard/82875.html (accessed 10 August 2026).

**[R6]** BCS, The Chartered Institute for IT (2026) *BCS Code of Conduct*. Official professional-body publication/page, current at the date of drafting. Available at: https://www.bcs.org/membership-and-registrations/become-a-member/bcs-code-of-conduct/ (accessed 10 August 2026).

**[R7]** An, B. et al. (2024) 'WAVES: Benchmarking the Robustness of Image Watermarks', *Proceedings of the 41st International Conference on Machine Learning*, 235, pp. 1456-1492. Available at: https://proceedings.mlr.press/v235/an24a.html (accessed 10 August 2026).

**[R8]** Zhao, X. et al. (2024) 'Invisible Image Watermarks Are Provably Removable Using Generative AI', *Advances in Neural Information Processing Systems*, 37. Available at: https://doi.org/10.52202/079017-0276 (accessed 10 August 2026).

**[R9]** Bui, T., Agarwal, S. and Collomosse, J. (2023) 'RoSteALS: Robust Steganography Using Autoencoder Latent Space', *Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition Workshops*, pp. 933-942. Available at: https://doi.org/10.1109/CVPRW59228.2023.00100 (accessed 10 August 2026).

**[R16]** Hayes, J. (2018) 'On Visible Adversarial Perturbations & Digital Watermarking', *2018 IEEE/CVF Conference on Computer Vision and Pattern Recognition Workshops (CVPRW)*, pp. 1678-1687. Available at: https://doi.org/10.1109/CVPRW.2018.00210 (accessed 11 August 2026).

**[R17]** Jia, X., Wei, X., Cao, X. and Han, X. (2020) 'Adv-watermark: A Novel Watermark Perturbation for Adversarial Examples', *Proceedings of the 28th ACM International Conference on Multimedia*, pp. 1579-1587. Available at: https://doi.org/10.1145/3394171.3413976 (accessed 11 August 2026).

**[R18]** Li, Q., Wang, X., Ma, B., Wang, X., Wang, C., Gao, S. and Shi, Y. (2022) 'Concealed Attack for Robust Watermarking Based on Generative Model and Perceptual Loss', *IEEE Transactions on Circuits and Systems for Video Technology*, 32(8), pp. 5695-5706. Available at: https://doi.org/10.1109/TCSVT.2021.3138795 (accessed 11 August 2026).

**[R19]** Jiang, Z., Zhang, J. and Gong, N. Z. (2023) 'Evading Watermark based Detection of AI-Generated Content', *Proceedings of the 2023 ACM SIGSAC Conference on Computer and Communications Security*, pp. 1168-1181. Available at: https://doi.org/10.1145/3576915.3623189 (accessed 11 August 2026).

**[R20]** Fernandez, P., Couairon, G., Jégou, H., Douze, M. and Furon, T. (2023) 'The Stable Signature: Rooting Watermarks in Latent Diffusion Models', *Proceedings of the IEEE/CVF International Conference on Computer Vision (ICCV)*, pp. 22466-22477. Official publisher record: https://openaccess.thecvf.com/content/ICCV2023/html/Fernandez_The_Stable_Signature_Rooting_Watermarks_in_Latent_Diffusion_Models_ICCV_2023_paper.html (accessed 11 August 2026).

**[R21]** Yang, Z., Zeng, K., Chen, K., Fang, H., Zhang, W. and Yu, N. (2024) 'Gaussian Shading: Provable Performance-Lossless Image Watermarking for Diffusion Models', *2024 IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR)*, pp. 12162-12171. Available at: https://doi.org/10.1109/CVPR52733.2024.01156 (accessed 11 August 2026).

**[R22]** Yuan, Z., Li, L., Wang, Z., Jiang, J. and Zhang, X. (2025) 'Watermark Removal Attack Against Text-to-Image Generative Model Watermarking', *IEEE Signal Processing Letters*, 32, pp. 1470-1474. Available at: https://doi.org/10.1109/LSP.2025.3554514 (accessed 11 August 2026).

**[R23]** American Statistical Association (2022) *Ethical Guidelines for Statistical Practice*. Official professional-body publication, approved 1 February 2022. Available at: https://www.amstat.org/your-career/ethical-guidelines-for-statistical-practice (accessed 11 August 2026).

**[R24]** Souppaya, M., Scarfone, K. and Dodson, D. (2022) *Secure Software Development Framework (SSDF) Version 1.1*, NIST SP 800-218. National Institute of Standards and Technology. Available at: https://doi.org/10.6028/NIST.SP.800-218 (accessed 11 August 2026).

**[R25]** International Organization for Standardization and International Electrotechnical Commission (2023) *ISO/IEC 25010:2023 Systems and software engineering - Systems and software Quality Requirements and Evaluation (SQuaRE) - Product quality model*. Official standard record. Available at: https://www.iso.org/standard/78176.html (accessed 11 August 2026).

**[R26]** United Kingdom (2018) *Data Protection Act 2018*. Official legislation. Available at: https://www.legislation.gov.uk/ukpga/2018/12/contents/enacted (accessed 11 August 2026).

**[R27]** Association for Computing Machinery (2018) *ACM Code of Ethics and Professional Conduct*. Official professional-body code. Available at: https://www.acm.org/code-of-ethics (accessed 11 August 2026).

**[R28]** European Parliament and Council of the European Union (2024) *Regulation (EU) 2024/1689 laying down harmonised rules on artificial intelligence (Artificial Intelligence Act)*. Official EUR-Lex publication. Available at: https://eur-lex.europa.eu/eli/reg/2024/1689/oj (accessed 11 August 2026).

## Appendices

### Appendix A: Repository evidence index

1. `README.md`: pipeline descriptions, result-file row counts, dataset statement, and 100-image commands.
2. `PROJECT_SUMMARY.md`: completed status, row-count summary, limitations, and incomplete extended-run statement.
3. `transforms.py`: authoritative transform definitions, intensity values, and deterministic seeding.
4. `transform_hash_robustness.py`: hash computation and result generation.
5. `trustmark_robustness.py`: TrustMark encoding, decoding, and raw accuracy generation.
6. `lsb_robustness.py` and `dct_robustness.py`: classical baseline implementations.
7. `ensemble_analysis.py`: threshold and ensemble decision generation.
8. `validate_experiment.py`: coverage, row-count, and duplicate-key validation.
9. `output/results/*.csv`: raw result artefacts used for the numerical discussion.
10. `dashboard/` and `dashboard_api.py`: CSV-backed visualisation prototype.

### Appendix B: Reproduction and validation record placeholder

The final submission should attach the terminal output and timestamp for the commands below, executed against the exact result set used in the report:

```text
python validate_experiment.py --image-count 100
python analyze_stats.py
python ensemble_analysis.py
```

The evidence pack should also preserve Python package versions, operating-system details, hardware information, TrustMark model/version details, the input manifest matching the 100-image CSVs, and the final Git working-tree state. The repository summary identifies TrustMark v0.9.1 and pipeline version `v2.0`; these should be checked against the final execution environment.

### Appendix C: Metric definitions and thresholds

- **Hash Hamming distance:** count of differing bits between transformed and reference hashes.
- **Hash bit-error fraction:** Hamming distance divided by the relevant hash length.
- **Raw bit accuracy:** expected TrustMark packet bits recovered before error correction.
- **Decode presence:** valid decoded payload flag returned by the implementation.
- **PSNR:** encoded-image quality measurement, not a robustness measurement.
- **Watermark success:** mean bit accuracy above 0.5 in the current threshold analysis.
- **Hash success:** mean bit-error fraction below 0.5 under the worst-algorithm rule.
- **Ensemble pass:** thresholded method outcome, not proof of authenticity.

### Appendix D: Transform and payload specification

This appendix should reproduce the final transform table from `transforms.py`, the payload definitions, image-selection rule, random-seed rule, and the exact software versions used. The current implementation uses the transform matrix specified in Section 3.2, fixed TrustMark payload `TM00001`, fixed LSB payload `LSB0001`, and the DCT payload generated by its implementation.

### Appendix E: Results artefact index

1. `output/results/hash_robustness_results.csv` - 64,000 current rows.
2. `output/results/trustmark_robustness_results.csv` - 8,100 current rows.
3. `output/results/lsb_robustness_results.csv` - 8,100 current rows.
4. `output/results/dct_robustness_results.csv` - 8,100 current rows.
5. `output/results/ensemble_decision_matrix.csv` - 80 current rows.
6. `output/threshold_analysis.md` - threshold and overlap analysis.
7. `output/figures/` - generated visualisations available for final figure selection.

All entries above describe the completed 100-image evidence set unless a later validated run explicitly replaces them.

### Appendix F: Ethics, licensing, and professional checklist

- Institutional ethics classification or approval: [attach required document].
- Non-plagiarism and authorship declaration: [complete institutional form].
- Dataset terms and intended use check: [record official terms and decision].
- Dependency licences and notices: [complete final software inventory].
- Payload privacy assessment for any future identifiers: [not applicable to current fixed test payloads; complete before deployment].
- C2PA interoperability claim: [not claimed by this prototype].
- Dashboard deployment/security review: [not completed; do not describe as production-ready].

### Appendix G: Evidence required after the 1,200-image experiment

Before replacing the 100-image results, retain:

1. A complete timestamped run log for all four pipelines and analysis steps.
2. An input manifest matching every image ID in every result file.
3. Successful `validate_experiment.py --image-count 1200` output with no coverage or duplicate-key failures.
4. Exact counts of unique images, rows, missing values, decode failures, and transform conditions.
5. Regenerated per-transform and per-intensity means, dispersion measures, and justified uncertainty estimates.
6. A fixed analysis plan stating baseline inclusion and geometric/non-geometric pooling.
7. Evidence that corrected PDQ serialisation and TrustMark raw-bit measurement were used.
8. Reproducible package, model, hardware, and operating-system details.
9. Reconciled final tables, figures, dashboard values, and raw CSV values.
10. Updated privacy, licensing, and institutional ethics confirmation if the experiment or payload scope changes.
