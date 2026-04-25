import os, re

root = r'c:\Users\mpro\Desktop\mprnew\mpr-main'

# Find all unique preconnect lines
preconnects = set()
for dirpath, _, files in os.walk(root):
    for f in files:
        if f.endswith('.html'):
            fp = os.path.join(dirpath, f)
            c = open(fp, encoding='utf-8', errors='replace').read()
            for line in c.splitlines():
                if 'preconnect' in line:
                    preconnects.add(line.strip())

print('=== ALL UNIQUE PRECONNECT TAGS ===')
for p in sorted(preconnects):
    print(p)
