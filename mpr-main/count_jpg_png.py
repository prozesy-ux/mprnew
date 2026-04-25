"""Count all JPG/PNG references in HTML files and local files."""
import re
from pathlib import Path

ROOT = Path(r"c:\Users\mpro\Desktop\mprnew\mpr-main")
pattern = re.compile(r'https?://[^\s"\'<>]+\.(?:jpg|jpeg|png)(?:\?[^\s"\'<>]*)?', re.IGNORECASE)

all_urls = set()
for fpath in ROOT.rglob("*.html"):
    text = fpath.read_text(encoding="utf-8", errors="ignore")
    for m in pattern.finditer(text):
        all_urls.add(m.group(0))

r2_jpg_png   = sorted(u for u in all_urls if "r2.dev" in u)
webflow_urls = sorted(u for u in all_urls if "website-files.com" in u and "r2.dev" not in u)
other_urls   = sorted(u for u in all_urls if "r2.dev" not in u and "website-files.com" not in u)

# Also check R2 URLs that point to jpg/png (not yet converted to avif)
r2_still_jpg_png = [u for u in r2_jpg_png]

local_jpg  = list(ROOT.rglob("*.jpg")) + list(ROOT.rglob("*.jpeg"))
local_png  = list(ROOT.rglob("*.png"))

print("=== JPG/PNG URL REFERENCES IN HTML ===")
print(f"Total unique jpg/png URLs:            {len(all_urls)}")
print(f"  On R2 (r2.dev) - still jpg/png:     {len(r2_jpg_png)}")
print(f"  Still on Webflow CDN (bare):         {len(webflow_urls)}")
print(f"  Other external:                      {len(other_urls)}")
print()

if webflow_urls:
    print("Webflow CDN jpg/png (bare, not on R2):")
    for u in webflow_urls[:30]:
        print(" ", u)
    if len(webflow_urls) > 30:
        print(f"  ... and {len(webflow_urls)-30} more")
    print()

if other_urls:
    print("Other external jpg/png:")
    for u in other_urls:
        print(" ", u)
    print()

print("=== R2 URLs still referencing jpg/png (candidates to convert to avif) ===")
for u in r2_jpg_png[:30]:
    print(" ", u)
if len(r2_jpg_png) > 30:
    print(f"  ... and {len(r2_jpg_png)-30} more")

print()
print("=== LOCAL JPG/PNG FILES ===")
print(f"  .jpg/.jpeg files: {len(local_jpg)}")
print(f"  .png files:       {len(local_png)}")
print(f"  Total local:      {len(local_jpg)+len(local_png)}")
