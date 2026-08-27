from pathlib import Path
import textwrap

import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from PIL import Image


ROOT = Path(__file__).resolve().parent
FIGURES = ROOT / "output" / "figures"
OUT = ROOT / "PROJECT_PRESENTATION_GUIDE.pdf"


PAGES = [
    ("STUDY / PRESENTATION GUIDE", "Steganographic Signing\nand Filter Traceability", [
        "A clear route through the robustness benchmark, its evidence, and its limits",
        "MSc Computer Science project | Opaleye Toluwalope Abayomi | 24163800",
        "Evidence baseline: validated final1200 evidence set",
        "Core question: Which verification signals remain useful after controlled image transformations?",
        "Reading rule: every result is conditional on the implementation, dataset, transform, metric, and validation state. A recovered signal is not proof of truth, identity, or provenance.",
    ], "fpr_transform_taxonomy.png", "Figure 1. Transform taxonomy used to organise the robustness study."),
    ("1. EXECUTIVE OVERVIEW", "The central message", [
        "This project benchmarks complementary image-verification signals rather than searching for one universal authenticity detector.",
        "TrustMark is generally strong against value and encoding changes in the tested evidence, while rotation, cropping, and letterbox padding expose important weaknesses.",
        "Perceptual hashes provide a separate similarity signal. LSB and DCT provide useful baselines but are not production recommendations.",
        "The ensemble is a decision aid, not a trust system.",
        "Suggested opening: Images are routinely resized, recompressed, filtered, cropped, and re-encoded. This project asks whether several verification signals degrade gracefully under those operations.",
    ], None, None),
    ("2. STUDY DESIGN", "A shared, deterministic experiment", [
        "Dataset: MS-COCO 2017 validation images, selected deterministically by filename order.",
        "Evidence scale: validated final1200 run; image is the statistical unit for uncertainty summaries.",
        "Transform matrix: 12 transform families and 80 transform-intensity conditions.",
        "Hash layer: eight perceptual-hash variants; reference-to-transformed Hamming distance.",
        "Watermark layer: TrustMark, LSB, and differential DCT baselines with fixed payloads.",
        "Analysis: threshold crossings, a worst-algorithm hash rule, and best/fallback ensemble choices.",
        "Transform families: photometric; encoding/noise; geometric; and black or grey letterbox layout changes.",
    ], "fpr_method_comparison.png", "Figure 2. Method-comparison view framing the complementary roles of hashes and watermarking."),
    ("3. SIGNALS AND METRICS", "What each number means", [
        "Perceptual hashes: Hamming distance counts changed bits; bit-error fraction normalises distance by hash length. PDQ is represented as 256 bits.",
        "TrustMark uses a learned encoder and decoder. LSB writes to the red-channel least-significant bit plane. DCT uses differential mid-frequency coefficients.",
        "Raw bit accuracy is recovered payload bits before error correction. Decode presence is whether the implementation reports a valid decoded payload.",
        "PSNR and MSE describe encode quality, not robustness or security.",
        "Watermark success is mean bit accuracy above 0.5. Hash success is mean bit-error fraction below 0.5.",
        "The 0.5 boundary is an analysis convention, not a security proof or user-validated operating point.",
    ], None, None),
    ("4. FINDINGS TO PRESENT", "Geometry exposes the failure surface", [
        "Brightness and contrast: LSB crosses the 50% boundary at selected settings; hash and TrustMark remain below their critical thresholds in the reported table.",
        "JPEG: LSB crosses at quality 20; DCT remains the more informative classical comparator in this study.",
        "Rotation: DCT crosses at 1 degree; the worst-hash rule at 70 degrees; LSB at 90 degrees.",
        "Scaling: LSB crosses at 0.25x; DCT crosses at 0.25x, with a non-monotonic worst crossing at 3.0x.",
        "Centre and random crop: worst-hash crossings occur at 0.7 and 0.6 removal respectively; baselines cross earlier.",
        "Letterbox padding changes layout without removing source content, making it a useful condition-specific test.",
    ], "ensemble_heatmap.png", "Figure 3. Ensemble heatmap showing method choices across transform-intensity conditions."),
    ("5. EVIDENCE WALKTHROUGH", "Recommended presentation sequence", [
        "1. Problem: show the transform taxonomy and explain routine edits versus geometric disruption.",
        "2. Design: show the shared pipeline and four signal families.",
        "3. Metrics: explain Hamming distance, raw bit accuracy, decode presence, and PSNR.",
        "4. Results: use the comparison and heatmap to contrast failure regions.",
        "5. Dashboard: open overview, per-transform, ensemble, and per-image views.",
        "6. Boundary: state what the results do not establish.",
        "The dashboard is a CSV-backed research visualisation and evidence browser, not a production signing service.",
    ], "dashboard_fig2_interface.png", "Figure 4. Dashboard interface for navigating the benchmark evidence."),
    ("6. QUALITY AND REPRODUCIBILITY", "Controls that support trust in the measurements", [
        "Transform definitions are centralised in transforms.py; image selection and random seeds are deterministic.",
        "Validation checks coverage, expected rows, duplicate keys, missing values, and baseline records before interpretation.",
        "Raw CSV outputs are retained separately from summaries and dashboard views.",
        "Uncertainty summaries use image-level aggregation, fixed-seed percentile bootstrap intervals for continuous metrics, and Wilson intervals for decode proportions.",
        "Corrections retained in the evidence: PDQ serialisation uses one bit per dimension; TrustMark records raw decoder output separately from exact payload presence.",
        "A configured larger run is not completed evidence until all pipelines pass validation.",
    ], "fpr_payload_ecc_dev_sweep.png", "Figure 5. Payload and error-correction development sweep used to motivate configuration choices."),
    ("7. RESPONSIBLE USE", "Limitations and safe wording", [
        "The evidence is tied to selected MS-COCO images and does not establish performance on medical, synthetic, text-heavy, or customer imagery.",
        "Transformations are isolated; compound, adaptive, and adversarial attacks are outside the demonstrated scope.",
        "The ensemble is comparative thresholded evidence, not calibrated authentication accuracy or decision cost.",
        "C2PA manifests, certificates, signed claims, key management, identity, and a trust chain are not implemented.",
        "Public images may contain recognisable people or copyrighted material. Future payloads containing identifiers require purpose, lawful basis, retention, access, and deletion controls.",
        "Prefer: ‘useful signal under the tested condition’. Avoid: ‘proves the image is authentic’.",
    ], "dashboard_fig4_verify_hybrid.png", "Figure 6. Hybrid verification view illustrating complementary signal inspection."),
    ("8. QUESTIONS AND SHORT ANSWERS", "Defensible answers for discussion", [
        "Why not only a watermark? A watermark and a hash measure different relationships; a hybrid can preserve evidence when one signal degrades.",
        "Why is geometry difficult? Rotation, crop, scaling, and padding alter coordinate relationships.",
        "Does high bit accuracy mean security? No. It reports recovery under tested conditions; security also needs a threat model, key management, and attack evaluation.",
        "Why report raw accuracy and decode presence? Error correction can make exact decoding succeed even when raw bits are wrong.",
        "Why use the worst hash? A pooled mean can hide a weak algorithm; the weakest-link rule makes that choice explicit.",
        "What next? Complete validated larger-run evidence, add compound and adaptive attacks, report per-image uncertainty and error costs, and evaluate provenance controls separately.",
    ], None, None),
    ("APPENDIX A. SOURCE MAP", "Repository evidence used", [
        "Project scope and pipeline components: PROJECT_SUMMARY.md; README.md",
        "Method definitions and limitations: output/final_project_report_draft.md",
        "Final-run uncertainty method: output/results/final1200/uncertainty_summary.md",
        "Threshold crossings: output/results/final1200/threshold_analysis.md",
        "Figures: output/figures/*.png; each included figure has an asset caption.",
        "Evidence and submission context: SUBMISSION_MANIFEST.md; CITATIONS.md",
        "Status: this is a study and presentation document derived from repository evidence. It is not a replacement for the formal project report or a signed provenance implementation.",
    ], None, None),
    ("APPENDIX B. GLOSSARY (1/2)", "Terms as used in this guide", [
        "Authenticity — claim that content is true/attributed; not proven by recovery.",
        "BCH — error-correcting code in watermark packets.",
        "Bit accuracy — recovered bits before correction.",
        "Decode presence — valid payload reported; distinct from raw accuracy.",
        "DCT — frequency-domain baseline in mid-frequency coefficients.",
        "ECC — converts partial recovery into valid messages.",
        "Ensemble — per-condition best/fallback matrix.",
        "False acceptance — accepting unrelated image as verified.",
        "Hamming distance — differing bits between hashes.",
        "Integrity — unchanged bytes; needs hard binding.",
        "Letterbox — padding for aspect ratio, separate from crop.",
    ], None, None),
    ("APPENDIX B. GLOSSARY (cont.) (2/2)", "Terms as used (continued)", [
        "LSB — fragile spatial-domain baseline.",
        "MSE — pixel distortion measure.",
        "Payload — fixed test message, not an identifier.",
        "Perceptual hash — content-derived representation vs distance.",
        "pHash/dHash — hash variants among eight tested.",
        "Provenance — signed accountable record; needs manifests/trust chain.",
        "PSNR — imperceptibility metric, not robustness.",
        "Recovery — payload decodes (decode presence).",
        "TrustMark — learned neural watermark candidate.",
        "Two-layer fallback — second BCH DCT layer; OR recovery.",
        "Transform intensity — named condition param, only within-family comparable.",
    ], None, None),
]


def draw_page(pdf, index, title, subtitle, lines, image_name, caption):
    fig = plt.figure(figsize=(8.27, 11.69), facecolor="#F8FAFB")
    ax = fig.add_axes([0, 0, 1, 1])
    ax.axis("off")
    ax.text(0.09, 0.955, "STEGANOGRAPHIC SIGNING AND FILTER TRACEABILITY", fontsize=7.5, weight="bold", color="#0C6E72")
    ax.text(0.09, 0.89, title, fontsize=20, weight="bold", color="#17324D")
    ax.text(0.09, 0.85, subtitle, fontsize=12, weight="bold", color="#0C6E72")
    y = 0.80
    for line in lines:
        wrapped = textwrap.wrap(line, width=86)
        ax.text(0.105, y, "• " + wrapped[0], fontsize=10, color="#172033", va="top")
        y -= 0.027
        for continuation in wrapped[1:]:
            ax.text(0.135, y, continuation, fontsize=10, color="#172033", va="top")
            y -= 0.024
        y -= 0.012
    if image_name:
        path = FIGURES / image_name
        if path.exists():
            image = Image.open(path)
            image.thumbnail((1050, 430))
            ax_img = fig.add_axes([0.10, 0.08, 0.80, 0.29])
            ax_img.imshow(image)
            ax_img.axis("off")
            ax.text(0.50, 0.055, caption, ha="center", fontsize=8, style="italic", color="#425466")
    ax.text(0.91, 0.025, f"Page {index}", ha="right", fontsize=8, color="#425466")
    pdf.savefig(fig, facecolor=fig.get_facecolor())
    plt.close(fig)


with PdfPages(OUT) as pdf:
    for index, page in enumerate(PAGES, 1):
        draw_page(pdf, index, *page)
print(OUT)
