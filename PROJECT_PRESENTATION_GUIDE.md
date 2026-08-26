# MSc Viva Project Presentation Guide

## One-minute summary

This project evaluates whether different image-verification signals remain useful after common image transformations. It compares eight perceptual hashes, the neural TrustMark watermark, and two classical watermark baselines: least-significant-bit (LSB) and differential discrete cosine transform (DCT). The same deterministic MS-COCO 2017 image sample is passed through 12 transform types and 80 transform-intensity conditions. Hashing measures similarity; watermarking measures whether an embedded payload can be recovered. A two-layer TrustMark-plus-fallback arrangement tests whether complementary channels improve recovery.

The final evidence uses 1,200 images and 96,000 transformed observations per watermark channel. The two-layer JPEG recovery rate is 85.60%, compared with 63.52% for TrustMark alone. Therefore the proposed `>90% across JPEG and PNG` hypothesis was **not confirmed**: PNG was not implemented in the transform matrix. The deliverable is a reproducible research benchmark and dashboard, not an authenticity or provenance service.

## Problem

Images are routinely resized, recompressed, recoloured, blurred, cropped or rotated. A verifier therefore needs to know:

- whether an image is perceptually similar to a reference;
- whether an embedded message can still be recovered;
- which signal survives which transformation;
- how much confidence can reasonably be placed in each result.

A single score is inadequate. A low hash distance does not recover the original bytes, and a recovered watermark does not prove who created the image or that it has not been edited.

## Research question and hypothesis

**Research question:** How do perceptual hashes, neural watermarking and classical watermarking baselines degrade under graduated image transformations, and can complementary channels cover one another's weaknesses?

**Proposed hypothesis:** a hybrid TrustMark-plus-perceptual-hash pipeline would achieve payload recovery above 90% across JPEG and PNG.

**Result:** the hypothesis was not confirmed. In the final 1,200-image evidence, two-layer JPEG payload recovery was **85.60%** (`FPR_Method_Comparison.xlsx`, `remediation_two_layer.json`). **PNG was not implemented**, so no PNG conclusion is justified.

## Four distinct concepts

| Concept | Meaning in this project | What it does not establish |
|---|---|---|
| Similarity | Agreement between an original and transformed perceptual hash, measured by Hamming distance or normalised bit error | Byte-for-byte identity or authorship |
| Recovery | Exact recovery of the known embedded payload, recorded as `decode_present` | Authenticity, ownership or absence of editing |
| Integrity | Evidence that content or bytes have remained unchanged | A watermark's survival; recovery can occur after an edit |
| Provenance | An accountable record of origin and history, normally supported by signed claims and a trust chain | A hash match or watermark decode |

The project measures similarity and recovery. It does not establish integrity or provenance. In particular, **watermark recovery is not authenticity**.

## Experimental design

- Dataset: MS-COCO 2017 validation split; the final manifest records 1,200 deterministically selected images.
- Transform matrix: 12 named transforms and 80 intensity conditions.
- Final transformed observations: 1,200 x 80 = **96,000** per watermark channel.
- Watermark CSVs: **97,200** rows each, comprising 1,200 untransformed baselines plus 96,000 transformed rows.
- Hash evidence: **768,000** rows in the compressed final hash output, representing eight hash algorithms across the final matrix.
- Ensemble matrix: **80** transformed conditions.
- Transformations are applied independently, not as attack sequences.

The historical 100-image pilot and the final1200 evidence must not be pooled. Claims in this guide use the final evidence unless explicitly labelled otherwise.

## The four pipelines

### 1. Perceptual-hash pipeline

The original image is hashed once for reference. Each transformed image is hashed again and compared with the reference using Hamming distance. The eight variants are pHash, dHash, aHash, wHash, colorHash, vertical dHash, a simplified pHash variant and PDQ. PDQ uses 256 bits; the other reported hash representations use their recorded lengths. Lower distance means greater representation stability, not image recovery.

### 2. TrustMark pipeline

TrustMark v0.9.1, Q model and CPU-only execution, embeds the fixed payload `TM00001`. The transformed image is decoded. The pipeline records raw bit accuracy, whether the expected payload decodes, decoded content, encode MSE and PSNR.

### 3. LSB baseline

The payload `LSB0001` is written into the least-significant bit plane of the red channel. This is intentionally fragile and provides a lower-bound comparator. Pixel-value changes and spatial changes can destroy the signal.

### 4. DCT baseline

The payload `DCT0001` is differentially encoded into mid-frequency DCT coefficients. It is a semi-robust classical frequency-domain comparator. It is not treated as a production recommendation.

The two-layer experiment combines TrustMark with a separate DCT-domain fallback channel. It is a recovery rule, not a fifth independent primary pipeline: recovery is `TrustMark decode-present OR fallback decode-present`. The perceptual hash remains a separate similarity screen and does not carry the payload.

## Transform matrix

| Mechanism | Transforms and tested range/design |
|---|---|
| Pixel/value changes | Brightness (0.5 to 2.0, 6); contrast (0.5 to 2.0, 6); saturation (0.2 to 1.8, 8); vibrancy (0.2 to 1.8, 8) |
| Information loss | Gaussian blur (radius 0.5 to 5.0, 6); salt-and-pepper noise (density 0.01 to 0.15, 6); JPEG compression (quality 95 to 5, 8) |
| Geometry/layout | Rotation (1 to 90 degrees, 8); scaling (0.25x to 3.0x, 6); centre crop (10% to 80% removed, 8); random crop (10% to 80% removed, 8); letterbox (black and grey padding, 2) |

The matrix is a graduated robustness test, not a complete security taxonomy. Rotation, cropping and letterboxing can break the decoder's spatial alignment; this explains why a value-preserving operation can still destroy a spatially placed watermark.

## Two-layer fallback channel

The fallback carries a short BCH_SUPER-coded payload in the DCT domain. It uses repetition, interleaved block placement and majority voting before BCH correction. The implemented defaults are a 100-bit packet, five repetitions and strength 40; the fallback payload is capped at four printable ASCII characters. The fallback has no geometric registration, so it cannot generally repair a crop or rotation that destroys the expected spatial layout.

### Final two-layer results

All figures below are final1200 condition-level rates from `output/remediation_two_layer.json` and the workbook, not authenticity probabilities.

| Measure | TrustMark alone | Two-layer |
|---|---:|---:|
| Overall transformed recovery, 96,000 observations | 60.73% | 67.28% |
| Clean-image recovery, 1,200 images | 98.75% | 99.75% |
| JPEG recovery, 9,600 observations | 63.52% | 85.60% |

The two-layer arrangement improves overall transformed recovery by 6.55 percentage points over TrustMark alone. Its gains are concentrated in dimension-preserving changes and JPEG compression. Selected two-layer recovery by transform is: brightness 92.07%, contrast 91.21%, saturation 99.51%, vibrancy 94.13%, Gaussian blur 87.49%, salt-and-pepper noise 45.76%, JPEG 85.60%, rotation 25.62%, scaling 98.65%, centre crop 27.34%, random crop 26.60% and letterbox 10.42%.

The JPEG quality ladder is non-monotonic at the most severe settings: quality 5 gives 69.67%, quality 10 gives 32.17%, quality 20 gives 93.08%, quality 35 gives 96.17%, quality 50 gives 97.08%, quality 65 gives 98.00%, quality 80 gives 98.92% and quality 95 gives 99.75%. This is a codec-and-pipeline result, not a reason to claim that lower quality is always easier or harder.

## Metrics and interpretation

- **Hamming distance:** number of differing bits between reference and transformed hash.
- **Normalised hash error:** Hamming distance divided by the representation's bit length; useful for comparing lengths, but still representation-dependent.
- **Raw bit accuracy:** fraction of expected payload bits matching before error correction. It is not the same as exact recovery.
- **Exact payload recovery / `decode_present`:** whether the expected payload is recovered after decoding and error correction.
- **Clean-image recovery:** recovery on the encoded image without an external transform; it checks the embedding and decoding path.
- **MSE and PSNR:** encode-side pixel distortion measures. PSNR is reported; it is not a perceptual guarantee.
- **Two-layer recovery:** logical OR of TrustMark and fallback decode-present outcomes.
- **Threshold analysis:** identifies tested intensity points at which a method crosses a chosen performance threshold.
- **Ensemble decision matrix:** records the best and fallback method for each transform-intensity condition under the declared scoring rule.

The workbook's headline comparison is:

| Channel | Transformed payload recovery | Clean-image recovery | Mean raw bit accuracy |
|---|---:|---:|---:|
| Hybrid two-layer | 67.28% | 99.75% | Not applicable in the summary sheet |
| TrustMark | 60.73% | 98.75% | 85.17% |
| DCT | 15.26% | 34.33% | 71.98% |
| LSB | 4.90% | 100.00% | 58.78% |

The DCT example is important: 71.98% raw bit accuracy does not imply 71.98% exact payload recovery; its recovery rate is 15.26%. LSB's 100.00% clean self-decode is a baseline property and does not make it robust after transformation.

## Final 1,200-image evidence

The final evidence is under `output/results/final1200/`. It includes the hash, TrustMark, LSB, DCT, fallback and ensemble outputs, the image manifest, threshold analysis, reproducibility records and uncertainty summary. The validated transformed population is 1,200 images x 80 conditions = 96,000 observations per channel. The final validation and manifest are separate from the earlier 100-image pilot.

The reported rates are descriptive aggregates over the declared conditions. The repository also generates bootstrap and Wilson interval summaries, but they should be presented as descriptive uncertainty for this fixed image set, not as proof of generalisation. The sample is not a random sample of all digital imagery.

## Dashboard demonstration

Use the final evidence explicitly rather than accidentally demonstrating the historical pilot:

1. Start the API with `python dashboard_api.py` and open `http://127.0.0.1:8000`.
2. Set `CSV_DIR=output/results/final1200` before starting it if CSV mode is being used.
3. On **Overview**, show the active evidence label, image count, transform count and hash algorithms.
4. On **Per-Transform**, select `jpeg_compression` and show recovery versus JPEG quality, including the two-layer comparison if available in the view.
5. Select `rotation` or `crop_center` to demonstrate the spatial-alignment boundary.
6. On **Ensemble Matrix**, explain that each cell is a tested condition with a best method and fallback, not a universal policy.
7. On **Per-Image**, select one image and show the traceable rows for hashes and watermark outcomes.
8. If demonstrating the interactive workflow, upload an image, apply a named filter, sign with a method, run a stress test, and verify. State that this is local research functionality and that a successful decode is payload recovery, not authentication.

The dashboard is FastAPI-backed, uses Chart.js in the frontend, and has CSV fallback. With `DATABASE_URL`, it can query the local PostgreSQL-backed evidence. The default CSV directory is the historical `output/results`, so the evidence label must be checked during the demo.

## PostgreSQL

The database work is a local Docker PostgreSQL 16 deployment, not a hosted production service. `migrate_to_db.py` creates indexed tables for `hash_results`, `watermark_results`, `fallback_results` and `ensemble_decision_matrix`, then loads the final evidence in batches and verifies counts. The reported verified counts are:

- `hash_results`: 768,000 rows;
- `watermark_results`: 291,600 rows, covering TrustMark, LSB and DCT;
- `fallback_results`: 97,200 rows;
- `ensemble_decision_matrix`: 80 rows.

The dashboard can serve database-backed queries when `DATABASE_URL` is set and falls back to CSV when the database is unavailable. This demonstrates persistence and query integration locally. It does not demonstrate production access control, deployment hardening, privacy governance, availability or database performance at scale.

## Ethics and limitations

- MS-COCO is public, but images may contain identifiable people and copyrighted material; public availability does not remove dataset terms or institutional responsibilities.
- No real customer identifiers are embedded. The confidence value is derived from measured decode metrics and is not an identity, timestamp or user identifier.
- Fixed payloads and one TrustMark configuration limit generalisation.
- The image selection is deterministic rather than representative of all media domains.
- Transformations are independent; cascaded, adaptive and adversarial edits were not tested.
- Negative-pair, false-acceptance, false-rejection and wrong-payload tests are not sufficient for an authenticity claim and remain gaps where not present in the final evidence.
- PNG, GIF/animation, video, audio, AI-generated media and full C2PA provenance manifests are outside the implemented benchmark.
- The system has no cryptographic keys, certificates, signed manifests or trust chain. The service's use of “sign” means watermark embedding, not cryptographic signing.
- A recovered watermark may be copied, replayed or survive an edit. It therefore cannot by itself prove authenticity or provenance.

## Promised versus delivered

| Proposal or delivery item | Honest status |
|---|---|
| Payload recovery above 90% across JPEG and PNG | **Not confirmed**: JPEG two-layer recovery was 85.60%; PNG was not implemented |
| TrustMark primary watermark | Delivered and benchmarked |
| Two-layer recovery arrangement | Delivered and benchmarked at final1200 scale |
| Four robustness pipelines | Delivered: hash, TrustMark, LSB and DCT |
| Transform matrix and ensemble analysis | Delivered for the named 12 transforms and 80 conditions |
| Dashboard | Delivered as a local research prototype with CSV and database-capable modes |
| PostgreSQL persistence | Delivered locally with verified row counts; not a production deployment |
| Cryptographic authenticity and provenance | Not delivered; C2PA manifests, signatures and trust chains were not implemented |
| PNG, GIF/animation handling and custom LUT filters | Not delivered |
| Universal security against attacks | Not promised by the evidence and not demonstrated |

## Likely examiner questions and strong honest answers

### Why did the >90% hypothesis fail?

The final two-layer JPEG rate was 85.60%, below the stated target. PNG was not implemented, so the cross-format hypothesis could not be tested. The correct conclusion is non-confirmation, not failure of every aspect of the architecture: the fallback improved JPEG and other dimension-preserving conditions, but geometry remained a boundary.

### Why use both hashes and watermarks?

They answer different questions. A hash is a non-embedded similarity signal; a watermark tests recovery of a message embedded in the image. Their failure modes differ, so an ensemble can improve screening coverage, but it must report the signals separately.

### Why is raw bit accuracy not the primary result?

A decoder can have many correct bits while still failing exact payload recovery. Error correction and the detection rule determine `decode_present`. The DCT result demonstrates this: 71.98% raw bit accuracy but only 15.26% transformed exact recovery.

### Does the watermark prove the image is genuine?

No. It shows that the detector recovered the expected payload under the tested conditions. It does not prove origin, ownership, unchanged content, exclusive possession of a secret, or a valid provenance history.

### Why are crops and rotations difficult?

The fallback places repeated data in expected spatial blocks but has no geometric registration. A crop removes blocks and a rotation changes their coordinates and interpolation. Without synchronisation, redundancy cannot reliably reconstruct a layout that the decoder no longer knows.

### Why was PNG not tested?

The implemented transform matrix includes JPEG compression but not PNG re-encoding as a condition. It would be misleading to infer a PNG result from JPEG or from the file format of intermediate artefacts. PNG should be added as a separately defined and validated transform in future work.

### Is 1,200 images enough to generalise?

It is a stronger final benchmark than the 100-image pilot and is reproducible through the manifest, but it is still one deterministic sample from MS-COCO. It does not establish performance for medical, synthetic, text-heavy or other domains. Image-level uncertainty is descriptive for this fixed sample.

### Why include weak LSB and DCT baselines?

They provide interpretable reference points. LSB illustrates a fragile spatial channel; DCT illustrates a simple frequency-domain channel. They help show what robustness is gained by the neural method and by combining signals, without pretending that a baseline is production-ready.

### What is the contribution if no new watermark algorithm was invented?

The contribution is an auditable comparison framework: shared transforms, deterministic data selection, four comparable pipelines, explicit metrics, a two-layer recovery analysis, validation checks, a dashboard and database-backed evidence path. The contribution is methodological and engineering-focused, not a claim of a new watermark construction.

### Is the dashboard production-ready?

No. It is a local research prototype. It supports inspection, upload/filter/sign/verify demonstrations and CSV or local database access, but production authentication, key management, calibration, access control, monitoring and threat testing are outside the demonstrated scope.

### What would you do next?

Add PNG and composed attacks; test unrelated negatives and wrong payloads; calibrate thresholds and confidence; use paired image-level analysis; stratify by dimensions and aspect ratio; evaluate more domains, payloads and independent implementations; and add cryptographically signed provenance if provenance is the actual requirement.

## Five-minute presentation script

**0:00-0:40 - Aim.** “My project evaluates robust image verification under common transformations. It compares perceptual similarity signals with embedded watermark recovery, rather than treating one detector as proof of authenticity.”

**0:40-1:20 - Question and scope.** “The research question is whether the signals degrade gracefully and whether complementary methods cover one another's weaknesses. The proposed hypothesis was above 90% payload recovery across JPEG and PNG. I need to state the outcome clearly: it was not confirmed. JPEG two-layer recovery was 85.60%, and PNG was not implemented.”

**1:20-2:05 - Method.** “I used 1,200 deterministically selected MS-COCO validation images, 12 transforms and 80 intensity conditions. The four pipelines were eight perceptual hashes, TrustMark, an LSB baseline and a DCT baseline. Each watermark pipeline embeds, transforms and decodes; the hash pipeline compares reference and transformed hashes.”

**2:05-2:50 - Measurement.** “I separate Hamming distance, raw bit accuracy and exact payload recovery. Recovery means the expected message decoded; it does not mean integrity or authenticity. The two-layer rule is TrustMark OR a BCH_SUPER-coded DCT fallback. The final run contains 96,000 transformed observations per watermark channel, with clean-image baselines retained.”

**2:50-3:35 - Results.** “The workbook reports 67.28% transformed recovery for the hybrid, 60.73% for TrustMark, 15.26% for DCT and 4.90% for LSB. Clean recovery is 99.75% for the hybrid and 98.75% for TrustMark. On JPEG, the hybrid reaches 85.60% versus 63.52% for TrustMark alone. The fallback helps with colour changes and compression, but not reliably with rotation, cropping or letterboxing.”

**3:35-4:15 - Software and evidence.** “The dashboard provides overview, per-transform, ensemble-matrix and per-image views. It can use final1200 CSVs or local PostgreSQL. The migration creates indexed result tables and verifies 768,000 hash rows, 291,600 watermark rows, 97,200 fallback rows and 80 ensemble rows. The dashboard is a research prototype, not a production service.”

**4:15-4:45 - Ethics and limitations.** “The sample is one public dataset and is not representative of all images. I did not test PNG, composed or adaptive attacks, wrong-payload cases or full provenance. There are no cryptographic keys, manifests or trust chains. A recovered watermark is therefore not authenticity.”

**4:45-5:00 - Conclusion.** “The delivered result is a reproducible, transformation-aware evidence framework. It shows measurable benefit from a second recovery channel, but also identifies clear geometric and assurance limits. The honest next step is calibrated, negative-pair and provenance-aware evaluation rather than claiming universal verification.”

## Glossary

- **Authenticity:** confidence that an asset is genuine or from a claimed source; not established here by recovery alone.
- **BCH:** Bose-Chaudhuri-Hocquenghem error-correcting code used to add redundancy to a payload.
- **Bit accuracy:** proportion of decoded bits matching expected bits before or alongside correction, as explicitly defined.
- **Decode-present:** binary result that the expected payload was recovered by the decoder.
- **DCT:** discrete cosine transform; represents image blocks using spatial-frequency coefficients.
- **ECC:** error-correcting code; redundancy used to correct some bit errors.
- **Ensemble:** combination of multiple signals or methods under an explicit decision rule.
- **False acceptance:** accepting an image or payload that should not be accepted; it requires negative or wrong-payload tests.
- **Hamming distance:** count of positions at which two equal-length binary strings differ.
- **Integrity:** evidence that data has not changed from a trusted state.
- **Letterbox:** padding an image, here with black or grey regions, to alter its canvas geometry.
- **LSB:** least-significant bit; the lowest-value bit in a pixel channel.
- **MSE:** mean squared error between corresponding pixel values.
- **Payload:** the message embedded in a watermark.
- **Perceptual hash:** compact image representation intended to remain relatively stable for selected visual changes.
- **pHash/dHash/aHash/wHash/colorHash/PDQ:** named perceptual-hash algorithms or variants evaluated by this project.
- **Provenance:** an accountable record of origin, transformations and claims, normally backed by signatures and trust relationships.
- **PSNR:** peak signal-to-noise ratio, reported in decibels as an encode-distortion measure.
- **Recovery:** successful extraction of the expected embedded payload under the declared rule.
- **TrustMark:** the selected neural watermark implementation used for the primary channel.
- **Two-layer fallback:** TrustMark primary channel plus a separate fallback watermark, with recovery defined as logical OR.
- **Transform intensity:** the parameter controlling the severity of a named image operation.

## Evidence paths

- `FPR_Method_Comparison.xlsx` - workbook used for the headline method comparison, transform breakdown and JPEG ladder.
- `output/remediation_two_layer.json` - machine-readable two-layer recovery, baseline, transform and JPEG figures.
- `output/results/final1200/` - validated final evidence directory.
- `output/results/final1200/image_manifest.json` - selected-image manifest.
- `output/results/final1200/reproducibility_record.json` and `reproducibility_record.md` - final-run provenance and execution record.
- `output/results/final1200/uncertainty_summary.csv` and `uncertainty_summary.md` - descriptive uncertainty summaries.
- `transforms.py` - single source of truth for the transform definitions and intensity steps.
- `dashboard_api.py` and `dashboard/` - dashboard backend and frontend.
- `migrate_to_db.py` - local PostgreSQL schema, loading and count verification.
