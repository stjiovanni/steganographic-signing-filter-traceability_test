from docx import Document

for path, label in [('24163800_OpaleyeToluwalope_DPP_v2.docx', 'DPP'),
                    ('24163800_Tolu_Opaleye_IPR_Report_V4.docx', 'IPR')]:
    d = Document(path)
    print('==== ' + label + ' ====')
    print('--- Objectives / Research Question / Hypothesis ---')
    for i, p in enumerate(d.paragraphs):
        t = p.text.strip()
        low = t.lower()
        if any(k in low for k in ('objective', 'research question', 'hypothesis', 'aim', 'scope',
                                  'the backend is implemented', 'stress-test', 'geometric', 'design a',
                                  'filter layer', 'register', 'payload recovery', 'ssim', 'psnr',
                                  'provenance', 'dashboard', 'web application', 'postgres', 'react')):
            if len(t) > 20:
                print(i, '|', t[:280])
    print()
