"""Apply R1, R3, R4 to the FPR md: two-layer hybrid in abstract and conclusion,
contribution statement in 1.5, salt-pepper explanation in 4.11."""

import sys

path = 'output/FPR_v1.4.md'
t = open(path, encoding='utf-8').read()
count = 0

# ---- R1a: Abstract — add two-layer hybrid sentence ----
old = ('The main contribution is an auditable, transformation-aware verification framework in which '
       'signal recovery, image similarity, integrity, and provenance are reported as distinct constructs.')
new = ('The main contribution is an auditable, transformation-aware verification framework in which '
       'signal recovery, image similarity, integrity, and provenance are reported as distinct constructs. '
       'The project also contributes a two-layer hybrid payload-recovery channel (TrustMark OR a BCH-coded '
       'DCT fallback watermark) that improves exact payload recovery from 60.7% to 67.3% over 96,000 '
       'transformed observations, with the largest gains on dimension-preserving and low-quality JPEG conditions.')
if old in t and new not in t:
    t = t.replace(old, new)
    count += 1
    print('R1a: abstract updated')

# ---- R1b: Conclusion — name the two-layer hybrid result ----
old = ('The evidence supports a conditional engineering conclusion: the tested neural watermark and '
       'perceptual hashes provide complementary signals under many named conditions, while geometric '
       'changes and simple baselines expose important weaknesses.')
new = ('The evidence supports a conditional engineering conclusion: the tested neural watermark and '
       'perceptual hashes provide complementary signals under many named conditions, while geometric '
       'changes and simple baselines expose important weaknesses. The project\u2019s own two-layer hybrid '
       '(TrustMark OR fallback watermark) improves exact payload recovery to 67.3% over TrustMark\u2019s '
       '60.7%, with the rescue concentrated on dimension-preserving and compression conditions; the '
       'honest limit is that geometric conditions remain near chance without registration.')
if old in t and new not in t:
    t = t.replace(old, new)
    count += 1
    print('R1b: conclusion updated')

# ---- R3: One-sentence contribution statement in §1.5 ----
old = ('The strongest defensible contribution is therefore an auditable, transformation-aware '
       'verification framework with explicit evidence limits')
if old not in t:
    # try alternate phrasing
    old = 'The project\u2019s narrower contribution is practical auditability across complementary signal types.'
if old in t:
    new = old + ' In a single sentence: this project delivers a reproducible, validated benchmark that measures how perceptual hashes and watermark payloads survive named image transforms, introduces a two-layer hybrid recovery channel that improves exact recovery by 6.6 percentage points over the primary watermark alone, and reports every result with the evidence status, denominator, and aggregation rule an auditor needs to verify it.'
    t = t.replace(old, new)
    count += 1
    print('R3: contribution statement added')
else:
    print('R3: anchor not found, skipping')

# ---- R4: Salt-pepper fallback failure explanation in §4.11 ----
old = ('It cannot rescue dimension-changing conditions (rotation 25.6%, centre crop 27.3%, '
       'random crop 26.6%) because it has no geometric registration; letterbox (10.4%) and scaling '
       '(98.7% via TrustMark alone) show the same spatial-alignment boundary.')
if old in t:
    add = (' The salt-and-pepper result (fallback 33.5%, two-layer 45.8%) has a different cause: impulsive '
           'noise corrupts individual DCT coefficients directly, so the majority vote loses votes even '
           'though the block grid remains aligned \u2014 a failure mode orthogonal to the geometric one.')
    t = t.replace(old, old + add)
    count += 1
    print('R4: salt-pepper explanation added')
else:
    print('R4: anchor not found, skipping')

with open(path, 'w', encoding='utf-8') as f:
    f.write(t)
print(f'Done: {count} edits applied')
sys.stdout.flush()