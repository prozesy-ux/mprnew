import os, re

root = r'c:\Users\mpro\Desktop\mprnew\mpr-main'
pattern = 'cdn.prod.website-files.com'

results = {}
all_urls = set()

for dirpath, _, files in os.walk(root):
    for f in files:
        if f.endswith('.html'):
            fp = os.path.join(dirpath, f)
            c = open(fp, encoding='utf-8', errors='replace').read()
            lines = c.splitlines()
            hits = []
            for i, line in enumerate(lines, 1):
                if pattern in line:
                    hits.append((i, line.strip()))
                    found = re.findall(r'https://cdn\.prod\.website-files\.com[^\s"\'<>]+', line)
                    all_urls.update(found)
            if hits:
                rel = os.path.relpath(fp, root)
                results[rel] = hits

print(f'Files containing cdn.prod.website-files.com: {len(results)}')
print()

# Categorize by usage type
preconnect_files = 0
href_files = set()
src_files = set()
link_stylesheet = set()
other = set()

for dirpath, _, files in os.walk(root):
    for f in files:
        if f.endswith('.html'):
            fp = os.path.join(dirpath, f)
            rel = os.path.relpath(fp, root)
            c = open(fp, encoding='utf-8', errors='replace').read()
            lines = c.splitlines()
            for line in lines:
                if pattern not in line:
                    continue
                ls = line.strip()
                if 'rel="preconnect"' in ls or "rel='preconnect'" in ls:
                    preconnect_files += 1
                    break
            for line in lines:
                if pattern not in line:
                    continue
                ls = line.strip()
                if 'href=' in ls and pattern in ls and 'preconnect' not in ls and 'canonical' not in ls and 'alternate' not in ls:
                    href_files.add(rel)
                if 'src=' in ls and pattern in ls:
                    src_files.add(rel)
                if 'rel="stylesheet"' in ls and pattern in ls:
                    link_stylesheet.add(rel)

print(f'Preconnect tag occurrences: {preconnect_files}')
print(f'Files with href= (non-preconnect): {len(href_files)}')
print(f'Files with src=: {len(src_files)}')
print(f'Files with stylesheet link: {len(link_stylesheet)}')
print()

# Show unique URLs by type
href_urls = set()
src_urls = set()
stylesheet_urls = set()
preconnect_urls = set()

for dirpath, _, files in os.walk(root):
    for f in files:
        if f.endswith('.html'):
            fp = os.path.join(dirpath, f)
            c = open(fp, encoding='utf-8', errors='replace').read()
            for line in c.splitlines():
                if pattern not in line:
                    continue
                ls = line.strip()
                urls = re.findall(r'https://cdn\.prod\.website-files\.com[^\s"\'<>]+', ls)
                if 'rel="preconnect"' in ls:
                    preconnect_urls.update(urls)
                elif 'rel="stylesheet"' in ls:
                    stylesheet_urls.update(urls)
                elif 'href=' in ls:
                    href_urls.update(urls)
                elif 'src=' in ls:
                    src_urls.update(urls)

print('=== PRECONNECT (safe, keep) ===')
for u in sorted(preconnect_urls): print(' ', u)

print()
print('=== STYLESHEET <link> URLs ===')
for u in sorted(stylesheet_urls): print(' ', u)

print()
print('=== href= URLs (non-stylesheet) ===')
for u in sorted(href_urls): print(' ', u)

print()
print('=== src= URLs ===')
# Group by type
for u in sorted(src_urls): print(' ', u)
