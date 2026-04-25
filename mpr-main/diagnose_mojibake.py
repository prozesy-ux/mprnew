import os

patterns = {}
for root, dirs, files in os.walk('.'):
    dirs[:] = [d for d in dirs if d not in ['.git']]
    for f in files:
        if f.endswith('.html'):
            path = os.path.join(root, f)
            try:
                text = open(path, encoding='utf-8').read()
                checks = {
                    'ae_nbsp_rsq': '\u00e2\u20ac\u00a0\u2019',
                    'oe_ldq_ae_eu_bar': '\u00c5\u201c\u00e2\u20ac\u00a6',
                    'ae_eu_bar': '\u00e2\u20ac\u00a6',
                    'ae_eu_rdq': '\u00e2\u20ac\u201d',
                    'ae_eu_ldq': '\u00e2\u20ac\u201c',
                    'ae_eu_bul': '\u00e2\u20ac\u00a2',
                    'terms_euro_laq': '\u00e2\u201a\u00ac\u00e2\u20ac\u2039',
                    'ae_eu_tm': '\u00e2\u20ac\u2122',
                    'about_bullet': '\u00e2\u20ac\u00a2',
                    'country_bullet_full': '\u00e2\u20ac\u00a2',
                }
                for name, pat in checks.items():
                    cnt = text.count(pat)
                    if cnt:
                        patterns[name] = patterns.get(name, 0) + cnt
            except Exception as e:
                print(f'ERROR {path}: {e}')

for k, v in sorted(patterns.items(), key=lambda x: -x[1]):
    print(f'{v:4d}  {k}')
