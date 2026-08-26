import sys

path = 'output/FPR_v1.3.md'
t = open(path, encoding='utf-8').read()

# Update promise-table rows that are now delivered (SSIM, React, custom payload, confidence, detect)
reps = [
    ('| SSIM imperceptibility | Not delivered | PSNR only; SSIM future work |',
     '| SSIM imperceptibility | Delivered (10-image sample) | `output/remediation_ssim.csv`; SSIM 0.88-0.97 |'),
    ('| Verification interface (web dashboard) | Delivered (Sign/Verify) | FastAPI dashboard |',
     '| Verification interface (web dashboard) | Delivered (Sign/Verify, React) | FastAPI + React frontend (`dashboard-react/`); upload/filter/sign/verify |'),
    ('| C2PA/manifest/authenticity | Explicitly out of scope | Not claimed |',
     '| C2PA/manifest/authenticity | Explicitly out of scope | Not claimed |'),
]
count = 0
for old, new in reps:
    if old in t:
        t = t.replace(old, new)
        count += 1
        print('replaced:', old[:45])
    else:
        print('NOT FOUND:', old[:45])

# Add rows for newly-delivered items if not present
additions = [
    '| React (JSX) frontend | Delivered | `dashboard-react/` (Vite + React) |',
    '| Custom payload (name/copyright) | Delivered (user-supplied) | Sign/Verify payload field; per-method capacity |',
    '| Watermark detection (two images) | Delivered | `/api/analyze`; Detect tab |',
    '| Confidence score output | Delivered | `/api/verify` returns confidence + definition |',
]
promise_anchor = '| C2PA/manifest/authenticity | Out of scope | Not claimed |'
if promise_anchor in t:
    idx = t.index(promise_anchor)
    insertion = '\n'.join(additions) + '\n'
    t = t[:idx] + insertion + t[idx:]
    print('inserted', len(additions), 'rows')
else:
    print('C2PA anchor still not found')

with open(path, 'w', encoding='utf-8') as f:
    f.write(t)
print('done')