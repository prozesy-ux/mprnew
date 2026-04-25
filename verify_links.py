import os

root = r'c:\Users\mpro\Desktop\mprnew\mpr-main'
checks = {
    'Old wa.me +971522057100': 'wa.me/+971522057100',
    'Old wa.me +17165036335': 'wa.me/+17165036335',
    'Old wa.me +35794068727': 'wa.me/+35794068727',
    'Old wa.me +393892941226': 'wa.me/+393892941226',
    'Old tidycal designmonks': 'tidycal.com/designmonks',
    'New tidycal prozesymedia': 'tidycal.com/prozesymedia',
    'Figma href remaining': 'href="https://www.figma.com',
    'designmonks.co remaining': 'href="https://www.designmonks.co',
    'designmonks.ae remaining': 'href="https://designmonks.ae',
    'LemonSqueezy remaining': 'href="https://designmonks1.lemonsqueezy',
    'Framer remaining': 'href="https://startio.framer',
    'Framer pricing remaining': 'href="https://www.framer.com/pricing',
    'Noman linkedin': 'href="https://www.linkedin.com/in/nomandigital',
    'Noman instagram': 'href="https://www.instagram.com/nomandigital',
    'Noman facebook': 'href="https://www.facebook.com/anoman1234',
    'prozesy.com links added': 'href="https://prozesy.com/',
}

for label, pattern in checks.items():
    count = 0
    for dirpath, _, files in os.walk(root):
        for f in files:
            if f.endswith('.html'):
                c = open(os.path.join(dirpath, f), encoding='utf-8', errors='replace').read()
                count += c.count(pattern)
    print(f'{label}: {count}')
