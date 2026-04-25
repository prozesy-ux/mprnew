import hashlib
import html
import re
from pathlib import Path
from urllib.parse import unquote, urlparse

import boto3
from botocore.config import Config
import requests


ROOT = Path(r"c:\Users\mpro\Desktop\mprnew\mpr-main")
FILE_GLOBS = ("*.html", "*.css", "*.js")

ACCOUNT_ID = "20fe549097cc4110c9f9d5c4f4ed3760"
ACCESS_KEY = "b3b2985b2c3b441091df72f4aa376e6b"
SECRET_KEY = "85a1e9066e3bde3ad3d5011ae5293c1e976fec8747b857dd2b30a96652414365"
BUCKET_NAME = "videos"
CDN_BASE = "https://pub-ee9e9582bccd46678515d77c4ca44c3c.r2.dev"
SKIP_DOMAIN = "pub-ee9e9582bccd46678515d77c4ca44c3c.r2.dev"

URL_PATTERN = re.compile(r"https://[^\s\"'<>),]+", re.IGNORECASE)
WEBFLOW_RUNTIME_PATTERN = re.compile(r"/js/design-monks\.[^/]+\.js$", re.IGNORECASE)


def iter_project_files():
    for glob in FILE_GLOBS:
        yield from ROOT.rglob(glob)


def is_css_js_url(url: str) -> bool:
    parsed = urlparse(url)
    lower_path = parsed.path.lower()
    return lower_path.endswith(".css") or lower_path.endswith(".js")


def is_webflow_runtime_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.netloc.lower() == "cdn.prod.website-files.com" and bool(WEBFLOW_RUNTIME_PATTERN.search(parsed.path))


def build_local_path(url: str) -> Path:
    parsed = urlparse(url)
    host = parsed.netloc.replace(":", "_")

    path_part = unquote(parsed.path).lstrip("/")
    if not path_part:
        path_part = "asset"

    for ch in [":", "*", "?", '"', "<", ">", "|", "\\"]:
        path_part = path_part.replace(ch, "_")

    # Keep query variants unique while preserving extension.
    if parsed.query:
        p = Path(path_part)
        qhash = hashlib.sha1(parsed.query.encode("utf-8")).hexdigest()[:10]
        path_part = str(p.with_name(f"{p.stem}__q_{qhash}{p.suffix}"))

    return Path("local") / "external-code" / host / path_part


def gather_urls_and_contents():
    urls = {}
    file_contents = {}

    for fpath in iter_project_files():
        try:
            text = fpath.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        file_contents[fpath] = text

        for match in URL_PATTERN.finditer(text):
            raw = html.unescape(match.group(0))
            if SKIP_DOMAIN in raw:
                continue
            if raw.endswith("=") or "+" in raw:
                continue
            if is_webflow_runtime_url(raw):
                continue
            if is_css_js_url(raw):
                urls.setdefault(raw, build_local_path(raw))

    return urls, file_contents


def download_asset(url: str, dest: Path):
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        return True, "exists"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept": "text/css,application/javascript,text/javascript,*/*;q=0.8",
    }
    resp = requests.get(url, headers=headers, timeout=(10, 30))
    resp.raise_for_status()
    data = resp.content

    dest.write_bytes(data)
    return True, "downloaded"


def upload_assets(local_paths):
    endpoint = f"https://{ACCOUNT_ID}.r2.cloudflarestorage.com"
    s3 = boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY,
        region_name="auto",
        config=Config(connect_timeout=10, read_timeout=60, retries={"max_attempts": 3, "mode": "standard"}),
    )

    uploaded = 0
    failed = 0
    sorted_paths = sorted(local_paths)

    for idx, local_rel in enumerate(sorted_paths, start=1):
        full = ROOT / local_rel
        key = local_rel.as_posix()

        content_type = "application/javascript; charset=utf-8" if key.lower().endswith(".js") else "text/css; charset=utf-8"
        try:
            body = full.read_bytes()
            s3.put_object(
                Bucket=BUCKET_NAME,
                Key=key,
                Body=body,
                ContentType=content_type,
                CacheControl="public, max-age=31536000, immutable",
            )
            uploaded += 1
        except Exception:
            failed += 1
        if idx % 20 == 0 or idx == len(sorted_paths):
            print(f"Uploaded {idx}/{len(sorted_paths)}")

    return uploaded, failed


def replace_urls(file_contents, replacements):
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
    urls, file_contents = gather_urls_and_contents()
    print(f"Found {len(urls)} unique external CSS/JS URLs.")

    if not urls:
        print("Nothing to migrate.")
        return

    downloaded = 0
    already_local = 0
    failed = []

    for idx, (url, local_rel) in enumerate(sorted(urls.items()), start=1):
        try:
            _, state = download_asset(url, ROOT / local_rel)
            if state == "downloaded":
                downloaded += 1
            else:
                already_local += 1
        except Exception as exc:
            failed.append((url, str(exc)))
        if idx % 25 == 0 or idx == len(urls):
            print(f"Downloaded {idx}/{len(urls)}")

    if failed:
        print("\nDownload failures:")
        for url, err in failed[:100]:
            print(f"  {url} -> {err}")

    successful_urls = {u: p for u, p in urls.items() if u not in dict(failed)}
    uploaded, upload_failed = upload_assets(successful_urls.values())

    replacements = {
        old: f"{CDN_BASE}/{local_rel.as_posix()}"
        for old, local_rel in successful_urls.items()
    }
    updated_files, total_replacements = replace_urls(file_contents, replacements)

    print("\nDone.")
    print(f"Downloaded new: {downloaded}")
    print(f"Already local: {already_local}")
    print(f"Upload new: {uploaded}")
    print(f"Upload failed: {upload_failed}")
    print(f"Failed downloads: {len(failed)}")
    print(f"Updated files: {updated_files}")
    print(f"URL replacements: {total_replacements}")


if __name__ == "__main__":
    main()
