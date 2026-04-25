import os

DST = r'c:\Users\mpro\Desktop\mprnew\mpr-main\blog\best-digital-marketing-agency-europe-top-10\index.html'

with open(DST, encoding='utf-8') as f:
    html = f.read()

# Fix title
html = html.replace(
    '<title>Enterprise Website Design: Strategy & Best Practices</title>',
    '<title>Best Digital Marketing Agency in Europe: Top 10 Agencies (2026)</title>'
)

# Fix H1
html = html.replace(
    '<h1 class="hero-title is-blog-details">Retargeting Like a Pro: Meta & Google Ads Customer Comeback</h1>',
    '<h1 class="hero-title is-blog-details">Best Digital Marketing Agency in Europe: Top 10 Agencies for 2026</h1>'
)

with open(DST, 'w', encoding='utf-8') as f:
    f.write(html)

print('Fixed title and H1.')
# Verify
for line in html.splitlines():
    if '<title>' in line or 'hero-title is-blog-details' in line:
        print(line.strip())
