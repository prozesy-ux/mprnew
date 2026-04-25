import os, re

NEW_OG = "https://pub-ee9e9582bccd46678515d77c4ca44c3c.r2.dev/bn7hv4jk0i9632znlj5k%5B1%5D.avif"

pattern = re.compile(r'(<meta\s+content=")[^"]*("\s+property="og:image"/>)')

total_files = 0
for root, dirs, files in os.walk('.'):
    dirs[:] = [d for d in dirs if d not in ['.git']]
    for f in files:
        if f.endswith('.html'):
            path = os.path.join(root, f)
            try:
                text = open(path, encoding='utf-8').read()
                new_text, count = pattern.subn(lambda m: m.group(1) + NEW_OG + m.group(2), text)
                if count:
                    open(path, 'w', encoding='utf-8').write(new_text)
                    total_files += 1
                    print(f'Fixed {path}')
            except Exception as e:
                print(f'ERROR {path}: {e}')

print(f'\nDone: og:image updated in {total_files} files')
