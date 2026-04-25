"""
cdn_prod_migrate.py
===================
Finds every direct https://cdn.prod.website-files.com image/media URL in all
HTML files, downloads missing files to the local mirror folder, uploads them
to Cloudflare R2, then rewrites every matching URL in every HTML file.

Pattern of substitution:
  https://cdn.prod.website-files.com/<rest>
  →  https://pub-ee9e9582bccd46678515d77c4ca44c3c.r2.dev/local/cdn.prod.website-files.com/<rest>

Local mirror path:
  <ROOT>/local/cdn.prod.website-files.com/<rest>
  (same as what already exists for previously-migrated assets)
"""

import os, re, sys, urllib.request, urllib.parse, time, mimetypes
from pathlib import Path

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

# ──────────────────────────────────────────────
# CONFIG
# ──────────────────────────────────────────────
ROOT        = Path(r'c:\Users\mpro\Desktop\mprnew\mpr-main')
LOCAL_DIR   = ROOT / 'local' / 'cdn.prod.website-files.com'

CDN_ORIGIN  = 'https://cdn.prod.website-files.com'
R2_PUBLIC   = 'https://pub-ee9e9582bccd46678515d77c4ca44c3c.r2.dev'
R2_MIRROR   = f'{R2_PUBLIC}/local/cdn.prod.website-files.com'

ACCOUNT_ID  = '20fe549097cc4110c9f9d5c4f4ed3760'
ACCESS_KEY  = 'b3b2985b2c3b441091df72f4aa376e6b'
SECRET_KEY  = '85a1e9066e3bde3ad3d5011ae5293c1e976fec8747b857dd2b30a96652414365'
BUCKET      = 'videos'
ENDPOINT    = f'https://{ACCOUNT_ID}.r2.cloudflarestorage.com'

# regex: direct cdn.prod URLs — stops only at whitespace, quotes, angle brackets
# (NOT at comma or parenthesis — URLs like file%20(2).avif are valid)
DIRECT_PAT = re.compile(
    r'https://cdn\.prod\.website-files\.com[^\s"\'<>]+',
    re.IGNORECASE,
)

MEDIA_EXT = re.compile(
    r'\.(jpg|jpeg|png|gif|svg|avif|webp|ico|mp4|webm|mov|avi|woff|woff2)(\?[^\s"\'<>]*)?$',
    re.IGNORECASE,
)

# ──────────────────────────────────────────────
# BOTO3 CLIENT
# ──────────────────────────────────────────────
s3 = boto3.client(
    's3',
    endpoint_url=ENDPOINT,
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY,
    region_name='auto',
    config=Config(
        connect_timeout=30,
        read_timeout=60,
        retries={'max_attempts': 3},
    ),
)

LOCAL_DIR.mkdir(parents=True, exist_ok=True)

# ──────────────────────────────────────────────
# STEP 1: collect all HTML files and unique URLs
# ──────────────────────────────────────────────
html_files = list(ROOT.rglob('*.html'))
print(f"Scanning {len(html_files)} HTML files …")

unique_urls: set[str] = set()
for f in html_files:
    try:
        text = f.read_text(encoding='utf-8', errors='ignore')
    except Exception:
        continue
    for m in DIRECT_PAT.finditer(text):
            url = m.group(0).rstrip(',')   # strip srcset trailing comma
            if MEDIA_EXT.search(url):
                unique_urls.add(url)

print(f"Unique direct cdn.prod image/media URLs found: {len(unique_urls)}")
if not unique_urls:
    print("Nothing to do. Exiting.")
    sys.exit(0)

# ──────────────────────────────────────────────
# STEP 2: download missing files to local mirror
# ──────────────────────────────────────────────
downloaded: dict[str, Path] = {}   # url -> local path
failed_download: list[tuple[str, str]] = []

for idx, url in enumerate(sorted(unique_urls), 1):
    # strip query string for local storage
    url_no_qs = url.split('?')[0]
    url_path  = urllib.parse.urlparse(url_no_qs).path.lstrip('/')   # e.g. 672a72b5.../file.avif
    url_path_decoded = urllib.parse.unquote(url_path)

    local_file = LOCAL_DIR / url_path_decoded

    if local_file.exists():
        print(f"  [{idx}/{len(unique_urls)}] SKIP (local): {url_path_decoded}")
        downloaded[url] = local_file
        continue

    local_file.parent.mkdir(parents=True, exist_ok=True)

    try:
        req = urllib.request.Request(
            url,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'},
        )
        with urllib.request.urlopen(req, timeout=45) as resp:
            data = resp.read()
        local_file.write_bytes(data)
        print(f"  [{idx}/{len(unique_urls)}] DL OK: {url_path_decoded}")
        downloaded[url] = local_file
    except Exception as e:
        print(f"  [{idx}/{len(unique_urls)}] DL FAIL: {url}  →  {e}")
        failed_download.append((url, str(e)))

print(f"\nDownloaded: {len(downloaded)}  |  Failed: {len(failed_download)}")

# ──────────────────────────────────────────────
# STEP 3: upload each file to R2
# ──────────────────────────────────────────────
uploaded_count   = 0
skipped_r2       = 0
failed_upload: list[tuple[str, str]] = []

def guess_content_type(path: Path) -> str:
    mt, _ = mimetypes.guess_type(path.name)
    if mt:
        return mt
    ext = path.suffix.lower()
    mapping = {
        '.avif': 'image/avif',
        '.webp': 'image/webp',
        '.svg':  'image/svg+xml',
        '.ico':  'image/x-icon',
        '.woff': 'font/woff',
        '.woff2': 'font/woff2',
    }
    return mapping.get(ext, 'application/octet-stream')

for url, local_file in sorted(downloaded.items(), key=lambda x: x[0]):
    url_no_qs    = url.split('?')[0]
    url_path     = urllib.parse.urlparse(url_no_qs).path.lstrip('/')
    url_path_dec = urllib.parse.unquote(url_path)
    r2_key       = f'local/cdn.prod.website-files.com/{url_path_dec}'

    # Check if already in R2
    try:
        s3.head_object(Bucket=BUCKET, Key=r2_key)
        skipped_r2 += 1
        continue
    except ClientError as e:
        if e.response['Error']['Code'] != '404':
            print(f"  R2 HEAD ERROR: {r2_key} → {e}")
            failed_upload.append((r2_key, str(e)))
            continue

    try:
        ct = guess_content_type(local_file)
        s3.upload_file(
            str(local_file),
            BUCKET,
            r2_key,
            ExtraArgs={'ContentType': ct},
        )
        uploaded_count += 1
        print(f"  R2 UP: {r2_key}")
    except Exception as e:
        print(f"  R2 FAIL: {r2_key} → {e}")
        failed_upload.append((r2_key, str(e)))

print(f"\nR2 Uploaded: {uploaded_count}  |  Skipped (already in R2): {skipped_r2}  |  Failed: {len(failed_upload)}")

# ──────────────────────────────────────────────
# STEP 4: replace URLs in all HTML files
# ──────────────────────────────────────────────
# Build replacement map: original url → r2 mirror url
# Handles URL-encoded variants: replace both encoded and decoded forms

def build_r2_url(url: str) -> str:
    """Turn direct cdn.prod URL into R2 mirror URL, preserving trailing commas."""
    # Strip trailing comma if any (srcset artifact), restore after
    suffix = ''
    stripped = url.rstrip(',')
    if len(stripped) < len(url):
        suffix = url[len(stripped):]
    after_origin = stripped[len(CDN_ORIGIN):]   # everything after cdn.prod.website-files.com
    return f'{R2_MIRROR}{after_origin}{suffix}'

# We replace ALL direct cdn.prod image/media occurrences in HTML files,
# including ones where download/upload may have failed (they'll still resolve
# via the R2 local mirror that was previously populated).
replaced_files  = 0
replaced_total  = 0

for f in html_files:
    try:
        content = f.read_text(encoding='utf-8', errors='ignore')
    except Exception:
        continue

    def _replace(m: re.Match) -> str:
        url = m.group(0)
        # strip trailing comma to check if it's a media URL
        url_clean = url.rstrip(',')
        if MEDIA_EXT.search(url_clean):
            return build_r2_url(url)   # build_r2_url handles the comma suffix
        return url  # non-media — leave as-is

    new_content, n = DIRECT_PAT.subn(_replace, content)

    # Only write if something changed
    if new_content != content:
        f.write_text(new_content, encoding='utf-8')
        replaced_files += 1
        replaced_total += n
        print(f"  HTML patched ({n}x): {f.relative_to(ROOT)}")

print(f"\nHTML files updated: {replaced_files}  |  URL replacements: {replaced_total}")

# ──────────────────────────────────────────────
# SUMMARY
# ──────────────────────────────────────────────
print("\n" + "="*60)
print("SUMMARY")
print("="*60)
print(f"  Unique URLs found:       {len(unique_urls)}")
print(f"  Downloaded (new):        {len(downloaded) - sum(1 for u, p in downloaded.items() if not p.exists())}")
print(f"  R2 Uploaded (new):       {uploaded_count}")
print(f"  R2 Skipped (existed):    {skipped_r2}")
print(f"  HTML files patched:      {replaced_files}")
print(f"  URL replacements:        {replaced_total}")
if failed_download:
    print(f"\n  FAILED DOWNLOADS ({len(failed_download)}):")
    for u, e in failed_download:
        print(f"    {u}  →  {e}")
if failed_upload:
    print(f"\n  FAILED R2 UPLOADS ({len(failed_upload)}):")
    for k, e in failed_upload:
        print(f"    {k}  →  {e}")
print("="*60)
