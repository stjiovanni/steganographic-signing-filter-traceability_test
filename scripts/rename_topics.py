import io

path = 'study-companion/data.js'
t = io.open(path, encoding='utf-8').read()

reps = [
    ('id: 1, title: "Verification Signals", heading: "Introduction \u2014 what problem is being solved?"',
     'id: 1, title: "Introduction", heading: "What problem is being solved? (FPR Chapter 1)"'),
    ('id: 2, title: "Hashes & Watermarks", heading: "Background \u2014 three signals, three different jobs"',
     'id: 2, title: "Literature Review", heading: "Three signals, three different jobs (FPR Chapter 2)"'),
    ("id: 3, title: \"The Transform Matrix\", heading: \"Background \u2014 controlling what 'distorted' means\"",
     "id: 3, title: \"Methodology \u2014 The Transform Matrix\", heading: \"Controlling what 'distorted' means (FPR Chapter 3)\""),
    ('id: 4, title: "The Pipelines", heading: "Method \u2014 four channels, one harness"',
     'id: 4, title: "Methodology \u2014 The Pipelines", heading: "Four channels, one harness (FPR Chapter 3)"'),
    ('id: 5, title: "The Two-Layer Hybrid", heading: "Contribution \u2014 a second payload channel"',
     'id: 5, title: "Results \u2014 The Two-Layer Hybrid", heading: "A second payload channel \u2014 our contribution (FPR Sections 4.7/4.11)"'),
    ('id: 6, title: "Metrics That Must Not Be Conflated", heading: "Method \u2014 what each number actually means"',
     'id: 6, title: "Methodology \u2014 Metrics & Measurement", heading: "What each number actually means (FPR Section 3.5)"'),
    ('id: 7, title: "Scale & Validation", heading: "Experiment \u2014 evidence you can trust"',
     'id: 7, title: "Methodology \u2014 Scale & Validation", heading: "Evidence you can trust (FPR Chapters 3\u20134)"'),
    ('id: 8, title: "Results & Comparison", heading: "Findings \u2014 what the data actually shows"',
     'id: 8, title: "Results \u2014 Method Comparison", heading: "What the data actually shows (FPR Chapter 4)"'),
    ('id: 9, title: "The Sign/Verify Interface", heading: "Artefact \u2014 the workflow in practice"',
     'id: 9, title: "Artefact \u2014 Sign/Verify Dashboard", heading: "The workflow in practice (FPR Section 4.1)"'),
    ('id: 10, title: "Ethics, Limits & Honesty", heading: "Evaluation \u2014 what this project does and does not claim"',
     'id: 10, title: "Evaluation \u2014 Ethics, Limits & Honesty", heading: "What this project does and does not claim (FPR Chapter 5)"'),
]

ok = 0
for old, new in reps:
    if old in t:
        t = t.replace(old, new)
        ok += 1
    else:
        print('MISS:', old[:70])

with io.open(path, 'w', encoding='utf-8') as f:
    f.write(t)
print(f'{ok}/10 titles updated')