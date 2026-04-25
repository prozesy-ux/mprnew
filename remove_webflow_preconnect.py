import os, re

root = r'c:\Users\mpro\Desktop\mprnew\mpr-main'

# Two exact variants found
REMOVE = [
    '<link href="https://cdn.prod.website-files.com" rel="preconnect" crossorigin="anonymous"/>',
    '<link rel="preconnect" href="https://cdn.prod.website-files.com" crossorigin/>',
]

changed = 0
total = 0

for dirpath, _, files in os.walk(root):
    for f in files:
        if f.endswith('.html'):
            total += 1
            fp = os.path.join(dirpath, f)
            c = open(fp, encoding='utf-8', errors='replace').read()
            original = c
            for tag in REMOVE:
                # Remove the line containing the tag (including newline)
                c = re.sub(r'[ \t]*' + re.escape(tag) + r'[ \t]*\r?\n?', '', c)
            if c != original:
                open(fp, 'w', encoding='utf-8').write(c)
                changed += 1
                print(f'  UPDATED: {os.path.relpath(fp, root)}')

print(f'\nDone. {changed}/{total} files updated.')
