import sys

path = 'output/FPR_v1.4.md'
t = open(path, encoding='utf-8').read()

# Insert Section 4.12 (method comparison) before Section 5, after 4.11 content
sec5 = '## 5. Evaluation and Conclusion'
assert sec5 in t

sec412 = '''### 4.12 Method comparison workbook

A consolidated statistical comparison of the implemented channels is provided in `FPR_Method_Comparison.xlsx` (three sheets, two native charts, all values computed from the final1200 result files). The headline comparison of exact payload recovery over the 96,000 transformed observations is summarised in Table 13.

| Channel | Payload recovery, transformed (%) | Clean-image recovery (%) | Mean raw bit accuracy (%) |
|---|---|---|---|
| Hybrid two-layer (TrustMark OR fallback) - ours | 67.28 | 99.75 | not applicable (recovery metric) |
| TrustMark alone | 60.73 | 98.75 | 85.17 |
| DCT baseline | 15.26 | 34.33 | 71.98 |
| LSB baseline (context) | 4.90 | 100.00 (definitional) | 58.78 |

**Table 13: Method comparison at final1200 scale (1,200 images x 80 conditions; payload recovery = exact decode-present rate; mean raw bit accuracy reported separately as it does not imply recovery).**

Three findings follow. First, the hybrid two-layer channel improves exact payload recovery by 6.55 percentage points over TrustMark alone overall (67.28% vs 60.73%), with the rescue concentrated on dimension-preserving conditions and low-quality JPEG. Second, the DCT baseline's higher raw bit accuracy (71.98%) than its recovery rate (15.26%) illustrates why bit accuracy and payload recovery must never be conflated: error correction, not coefficient agreement, determines whether a message survives. Third, LSB's definitional 100% clean-image self-decode is retained in the table for transparency but carries no comparative meaning. The full per-transform breakdown, JPEG quality ladder, and native charts are in the workbook; recovery by transform is also tabulated in Table 11.

'''
t = t.replace(sec5, sec412 + sec5)

with open(path, 'w', encoding='utf-8') as f:
    f.write(t)
print('inserted 4.12 + Table 13 into md')
sys.stdout.flush()