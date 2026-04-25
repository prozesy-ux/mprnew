import html
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import boto3
from botocore.config import Config
import requests


ROOT = Path(r"c:\Users\mpro\Desktop\mprnew\mpr-main")
ACCOUNT_ID = "20fe549097cc4110c9f9d5c4f4ed3760"
ACCESS_KEY = "b3b2985b2c3b441091df72f4aa376e6b"
SECRET_KEY = "85a1e9066e3bde3ad3d5011ae5293c1e976fec8747b857dd2b30a96652414365"
BUCKET_NAME = "videos"
CDN_BASE = "https://pub-ee9e9582bccd46678515d77c4ca44c3c.r2.dev"
FILE_GLOBS = ("*.html",)

RUNTIME_URL_RE = re.compile(
    r"https://cdn\.prod\.website-files\.com/(?P<site>[^/]+)/js/(?P<entry>design-monks\.[^\"'\s>]+\.js)",
    re.IGNORECASE,
)
CHUNK_HASH_RE = re.compile(r'"([0-9a-f]{8,32})"')


def iter_html_files():
    for glob in FILE_GLOBS:
        yield from ROOT.rglob(glob)


def runtime_local_path(site_id: str, filename: str) -> Path:
    return Path("local") / "external-code" / "cdn.prod.website-files.com" / site_id / "js" / filename


def runtime_r2_url(site_id: str, filename: str) -> str:
    return f"{CDN_BASE}/local/external-code/cdn.prod.website-files.com/{site_id}/js/{filename}"


def gather_runtime_urls():
    runtime_urls = {}
    file_contents = {}

    for fpath in iter_html_files():
        try:
            text = fpath.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        file_contents[fpath] = text
        for match in RUNTIME_URL_RE.finditer(html.unescape(text)):
            runtime_urls[match.group(0)] = (match.group("site"), match.group("entry"))

    return runtime_urls, file_contents


def download_file(url: str, dest: Path):
    dest.parent.mkdir(parents=True, exist_ok=True)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept": "application/javascript,text/javascript,*/*;q=0.8",
    }
    resp = requests.get(url, headers=headers, timeout=(10, 30))
    resp.raise_for_status()
    dest.write_bytes(resp.content)
    return resp.text


def parse_chunk_names(entry_text: str):
    hashes = []
    seen = set()
    for hash_value in CHUNK_HASH_RE.findall(entry_text):
        if len(hash_value) < 8:
            continue
        if hash_value in seen:
            continue
        seen.add(hash_value)
        hashes.append(hash_value)
    return [f"design-monks.achunk.{hash_value}.js" for hash_value in hashes]


def s3_client():
    endpoint = f"https://{ACCOUNT_ID}.r2.cloudflarestorage.com"
    return boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY,
        region_name="auto",
        config=Config(connect_timeout=10, read_timeout=60, retries={"max_attempts": 3, "mode": "standard"}),
    )


def upload_js_files(local_paths):
    client = s3_client()
    uploaded = 0
    for local_rel in sorted(local_paths):
        full = ROOT / local_rel
        client.put_object(
            Bucket=BUCKET_NAME,
            Key=local_rel.as_posix(),
            Body=full.read_bytes(),
            ContentType="application/javascript; charset=utf-8",
            CacheControl="public, max-age=31536000, immutable",
        )
        uploaded += 1
    return uploaded


def replace_runtime_urls(file_contents, replacements):
    updated_files = 0
    total_replacements = 0
    for fpath, text in file_contents.items():
        original = text
        for old, new in replacements.items():
            if old in text:
                count = text.count(old)
                text = text.replace(old, new)
                total_replacements += count
        if text != original:
            fpath.write_text(text, encoding="utf-8")
            updated_files += 1
    return updated_files, total_replacements


def main():
    runtime_urls, file_contents = gather_runtime_urls()
    print(f"Found {len(runtime_urls)} Webflow runtime entry URLs.")
    if not runtime_urls:
        print("Nothing to migrate.")
        return

    files_to_upload = set()
    replacements = {}
    chunk_total = 0
    manifest = {
        "migrated_at": datetime.now(timezone.utc).isoformat(),
        "entries": [],
        "chunks": [],
        "summary": {},
    }

    for entry_url, (site_id, entry_name) in sorted(runtime_urls.items()):
        entry_local = runtime_local_path(site_id, entry_name)
        entry_full_url = entry_url
        entry_text = download_file(entry_full_url, ROOT / entry_local)
        files_to_upload.add(entry_local)
        r2_entry_url = runtime_r2_url(site_id, entry_name)

        entry_record = {
            "original_url": entry_url,
            "r2_url": r2_entry_url,
            "local_path": entry_local.as_posix(),
            "chunks": [],
        }

        for chunk_name in parse_chunk_names(entry_text):
            chunk_url = f"https://cdn.prod.website-files.com/{site_id}/js/{chunk_name}"
            chunk_local = runtime_local_path(site_id, chunk_name)
            download_file(chunk_url, ROOT / chunk_local)
            files_to_upload.add(chunk_local)
            chunk_total += 1
            r2_chunk_url = runtime_r2_url(site_id, chunk_name)
            entry_record["chunks"].append(chunk_name)
            manifest["chunks"].append({
                "name": chunk_name,
                "original_url": chunk_url,
                "r2_url": r2_chunk_url,
                "local_path": chunk_local.as_posix(),
            })

        replacements[entry_url] = r2_entry_url
        manifest["entries"].append(entry_record)

    uploaded = upload_js_files(files_to_upload)
    updated_files, total_replacements = replace_runtime_urls(file_contents, replacements)

    manifest["summary"] = {
        "entries_migrated": len(runtime_urls),
        "chunks_downloaded": chunk_total,
        "js_files_uploaded": uploaded,
        "html_files_updated": updated_files,
        "url_replacements": total_replacements,
    }

    manifest_path = ROOT / "webflow_runtime_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print("\nDone.")
    print(f"Entry URLs migrated: {len(runtime_urls)}")
    print(f"Chunk files downloaded: {chunk_total}")
    print(f"JS files uploaded: {uploaded}")
    print(f"Updated files: {updated_files}")
    print(f"URL replacements: {total_replacements}")
    print(f"Manifest written: {manifest_path}")


if __name__ == "__main__":
    main()