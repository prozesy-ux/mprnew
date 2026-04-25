"""
Download external image/video/SVG/AVIF assets to /local folder
and replace URLs in all HTML/CSS/JS files.

SKIP: any URL from pub-ee9e9582bccd46678515d77c4ca44c3c.r2.dev
DOWNLOAD: all other external image/video/SVG/AVIF URLs
"""

import os
import re
import sys
import urllib.request
import urllib.parse
import hashlib
from pathlib import Path

# Config
ROOT = Path(r'c:\Users\mpro\Desktop\mprnew\mpr-main')
LOCAL_DIR = ROOT / 'local'
SKIP_DOMAIN = 'pub-ee9e9582bccd46678515d77c4ca44c3c.r2.dev'
EXTENSIONS = r'\.(jpg|jpeg|png|gif|svg|avif|webp|mp4|mov|webm|avi|ico|woff|woff2)'
FILE_TYPES = ('*.html', '*.css', '*.js')

# regex to match https:// URLs ending in media extensions (with optional query string)
# Exclude commas and spaces to avoid grabbing srcset multiple values
URL_PATTERN = re.compile(
    r'https://[^\s"\'<>),]+' + EXTENSIONS + r'(\?[^\s"\'<>),]*)?',
    re.IGNORECASE
)

LOCAL_DIR.mkdir(exist_ok=True)

# Step 1: Collect all files
all_files = []
for ext in ('*.html', '*.css', '*.js'):
    all_files.extend(ROOT.rglob(ext))

print(f"Scanning {len(all_files)} files...")

# Step 2: Find all unique external URLs (excluding skip domain)
url_to_local = {}  # url -> local relative path (from root)

for f in all_files:
    try:
        content = f.read_text(encoding='utf-8', errors='ignore')
    except Exception:
        continue
    for m in URL_PATTERN.finditer(content):
        url = m.group(0)
        # Skip r2.dev domain
        if SKIP_DOMAIN in url:
            continue
        # Skip data URIs (shouldn't match but safety check)
        if url.startswith('data:'):
            continue
        if url not in url_to_local:
            # Parse URL and build a safe local path
            parsed = urllib.parse.urlparse(url)
            # URL-decode the path to turn %2F -> / etc.
            path_part = urllib.parse.unquote(parsed.path).lstrip('/')
            # Sanitize: replace any remaining invalid Windows filename chars
            # Keep / as path separator so subdirs are preserved
            for ch in [':', '*', '?', '"', '<', '>', '|', '\\']:
                path_part = path_part.replace(ch, '_')
            # Use host + path to avoid collisions across domains
            safe_host = parsed.netloc.replace(':', '_')
            local_subpath = Path('local') / safe_host / path_part
            url_to_local[url] = local_subpath
            print(f"  FOUND: {url}")

print(f"\nTotal external assets to download: {len(url_to_local)}")

if len(url_to_local) == 0:
    print("No external assets found (excluding r2.dev). Nothing to do.")
    sys.exit(0)

# Step 3: Download each URL
downloaded = {}  # url -> actual local path used
failed = []

for url, local_subpath in url_to_local.items():
    local_full = ROOT / local_subpath
    local_full.parent.mkdir(parents=True, exist_ok=True)
    
    if local_full.exists():
        print(f"  SKIP (already exists): {local_subpath}")
        downloaded[url] = local_subpath
        continue
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
        local_full.write_bytes(data)
        print(f"  OK: {url} -> {local_subpath}")
        downloaded[url] = local_subpath
    except Exception as e:
        print(f"  FAILED: {url} -- {e}")
        failed.append((url, str(e)))

print(f"\nDownloaded: {len(downloaded)}, Failed: {len(failed)}")

# Step 4: Replace URLs in files
# Use forward slashes relative to root, with leading /
updated_files = 0
for f in all_files:
    try:
        content = f.read_text(encoding='utf-8', errors='ignore')
    except Exception:
        continue
    
    original = content
    
    def replace_url(m):
        url = m.group(0)
        if url in downloaded:
            rel = downloaded[url]
            # Convert to forward slashes with leading /
            return '/' + str(rel).replace('\\', '/')
        return url
    
    content = URL_PATTERN.sub(replace_url, content)
    
    if content != original:
        f.write_text(content, encoding='utf-8')
        updated_files += 1
        print(f"  UPDATED: {f.relative_to(ROOT)}")

print(f"\nUpdated {updated_files} files.")

if failed:
    print("\nFailed downloads:")
    for url, err in failed:
        print(f"  {url}: {err}")
