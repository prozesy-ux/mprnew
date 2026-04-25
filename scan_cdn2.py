import os, re

root = r'c:\Users\mpro\Desktop\mprnew\mpr-main'
pattern = 'cdn.prod.website-files.com'

all_unique_lines = set()
preconnect_count = 0
file_count = 0

for dirpath, _, files in os.walk(root):
    for f in files:
        if f.endswith('.html'):
            fp = os.path.join(dirpath, f)
            c = open(fp, encoding='utf-8', errors='replace').read()
            if pattern in c:
                file_count += 1
                for line in c.splitlines():
                    if pattern in line:
                        stripped = line.strip()
                        all_unique_lines.add(stripped)
                        if 'preconnect' in stripped:
                            preconnect_count += 1

print(f'Files containing cdn.prod.website-files.com: {file_count}')
print(f'Unique line patterns found: {len(all_unique_lines)}')
print()

# Categorize
preconnect_lines = set()
stylesheet_lines = set()
src_lines = set()
href_only_lines = set()
other_lines = set()

for line in all_unique_lines:
    if 'preconnect' in line:
        preconnect_lines.add(line)
    elif 'rel="stylesheet"' in line or "rel='stylesheet'" in line:
        stylesheet_lines.add(line)
    elif 'src=' in line:
        src_lines.add(line)
    elif 'href=' in line:
        href_only_lines.add(line)
    else:
        other_lines.add(line)

print('=== 1. PRECONNECT TAGS (safe to keep, just performance hints) ===')
for l in sorted(preconnect_lines):
    print(' ', l[:150])

print()
print('=== 2. STYLESHEET <link> TAGS ===')
for l in sorted(stylesheet_lines):
    print(' ', l[:200])

print()
print('=== 3. src= USAGES ===')
# Extract unique src URL patterns
src_urls = set()
for line in src_lines:
    found = re.findall(r'src=["\']([^"\']+cdn\.prod\.website-files\.com[^"\']*)["\']', line)
    src_urls.update(found)
for u in sorted(src_urls):
    print(' ', u[:200])

print()
print('=== 4. href= USAGES (non-stylesheet) ===')
href_urls = set()
for line in href_only_lines:
    found = re.findall(r'href=["\']([^"\']+cdn\.prod\.website-files\.com[^"\']*)["\']', line)
    href_urls.update(found)
for u in sorted(href_urls):
    print(' ', u[:200])

print()
print('=== 5. OTHER USAGES ===')
for l in sorted(other_lines):
    print(' ', l[:200])
