import hashlib
import html
import io
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit

import boto3
import requests
from botocore.config import Config
from PIL import Image
import pillow_avif  # noqa: F401


ROOT = Path(r"c:\Users\mpro\Desktop\mprnew\mpr-main")
FILE_GLOBS = ("*.html", "*.css", "*.js")

ACCOUNT_ID = "20fe549097cc4110c9f9d5c4f4ed3760"
ACCESS_KEY = "b3b2985b2c3b441091df72f4aa376e6b"
SECRET_KEY = "85a1e9066e3bde3ad3d5011ae5293c1e976fec8747b857dd2b30a96652414365"
BUCKET_NAME = "videos"
CDN_BASE = "https://pub-ee9e9582bccd46678515d77c4ca44c3c.r2.dev"
ENDPOINT = f"https://{ACCOUNT_ID}.r2.cloudflarestorage.com"

# Match external PNG/JPG URLs with optional query string.
# Lookahead ensures URL ends at a quote/bracket/whitespace/comma — allows () in filenames.
URL_PATTERN = re.compile(
    r"https://[^\s\"'<>]+?\.(?:png|jpe?g)(?:\?[^\s\"'<>]*)?(?=[\"'<>\s,]|$)",
    re.IGNORECASE,
)
MANIFEST_PATH = ROOT / "avif_migration_manifest.json"


s3 = boto3.client(
    "s3",
    endpoint_url=ENDPOINT,
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY,
    region_name="auto",
    config=Config(connect_timeout=10, read_timeout=60, retries={"max_attempts": 3, "mode": "standard"}),
)


def iter_project_files():
    for pattern in FILE_GLOBS:
        yield from ROOT.rglob(pattern)


def gather_urls():
    urls = set()
    file_contents = {}
    for path in iter_project_files():
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        file_contents[path] = text
        for match in URL_PATTERN.finditer(text):
            urls.add(match.group(0))
    return sorted(urls), file_contents


def normalize_for_download(raw_url):
    return html.unescape(raw_url)


def download_bytes(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept": "image/*,*/*;q=0.8",
    }
    response = requests.get(url, timeout=30, headers=headers)
    response.raise_for_status()
    return response.content


def download_with_fallback(raw_url):
    decoded = normalize_for_download(raw_url)
    try:
        return download_bytes(decoded)
    except Exception:
        parts = urlsplit(decoded)
        if parts.query:
            stripped = parts._replace(query="").geturl()
            return download_bytes(stripped)
        raise


def to_avif(image_bytes):
    with Image.open(io.BytesIO(image_bytes)) as img:
        if img.mode == "P":
            img = img.convert("RGBA")
        elif img.mode not in ("RGB", "RGBA"):
            img = img.convert("RGB")

        output = io.BytesIO()
        img.save(output, format="AVIF", quality=55)
        return output.getvalue()


def build_object_key(raw_url):
    parsed = urlsplit(html.unescape(raw_url))
    base_name = Path(parsed.path).stem or "asset"
    safe_name = re.sub(r"[^A-Za-z0-9._-]+", "-", base_name).strip("-") or "asset"
    digest = hashlib.sha1(raw_url.encode("utf-8")).hexdigest()[:16]
    return f"converted-avif/{safe_name}-{digest}.avif"


def upload_avif(avif_bytes, key):
    s3.put_object(
        Bucket=BUCKET_NAME,
        Key=key,
        Body=avif_bytes,
        ContentType="image/avif",
        CacheControl="public, max-age=31536000, immutable",
    )


def replace_urls(file_contents, replacements):
    updated_files = 0
    total_replacements = 0

    for path, text in file_contents.items():
        original = text
        for old_url, new_url in replacements.items():
            if old_url in text:
                count = text.count(old_url)
                text = text.replace(old_url, new_url)
                total_replacements += count

        if text != original:
            path.write_text(text, encoding="utf-8")
            updated_files += 1
            rel = path.relative_to(ROOT).as_posix()
            print(f"UPDATED: {rel}")

    return updated_files, total_replacements


def main():
    urls, file_contents = gather_urls()
    print(f"Found {len(urls)} unique PNG/JPG URLs.")

    if not urls:
        print("No PNG/JPG URLs found. Nothing to do.")
        return

    if MANIFEST_PATH.exists():
        try:
            replacements = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        except Exception:
            replacements = {}
    else:
        replacements = {}

    if "--apply-only" in sys.argv:
        updated_files, total_replacements = replace_urls(file_contents, replacements)
        print("\nDone (apply-only).")
        print(f"Manifest entries: {len(replacements)}")
        print(f"Files updated: {updated_files}")
        print(f"URL replacements: {total_replacements}")
        return

    converted = 0
    failed = 0
    reused = 0

    interrupted = False
    try:
        for idx, raw_url in enumerate(urls, start=1):
            if raw_url in replacements:
                reused += 1
                continue
            try:
                image_bytes = download_with_fallback(raw_url)
                avif_bytes = to_avif(image_bytes)
                key = build_object_key(raw_url)
                upload_avif(avif_bytes, key)
                replacements[raw_url] = f"{CDN_BASE}/{key}"
                MANIFEST_PATH.write_text(json.dumps(replacements, indent=2), encoding="utf-8")
                converted += 1
                if idx % 10 == 0 or idx == len(urls):
                    print(f"Progress: {idx}/{len(urls)} (converted={converted}, reused={reused}, failed={failed})")
            except Exception as exc:
                failed += 1
                print(f"[{idx}/{len(urls)}] FAIL: {raw_url} -> {exc}")
    except KeyboardInterrupt:
        interrupted = True
        print("\nInterrupted. Applying current manifest replacements before exit...")

    if not replacements:
        print("No successful conversions/uploads, no URL changes made.")
        return

    updated_files, total_replacements = replace_urls(file_contents, replacements)

    print("\nDone.")
    if interrupted:
        print("Status: interrupted")
    print(f"Converted+uploaded: {converted}")
    print(f"Reused from manifest: {reused}")
    print(f"Failed: {failed}")
    print(f"Files updated: {updated_files}")
    print(f"URL replacements: {total_replacements}")


if __name__ == "__main__":
    main()
