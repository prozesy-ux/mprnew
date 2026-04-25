import html
import re
import sys
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlsplit, urlunsplit
from urllib.request import Request, urlopen

PROJECT_ROOT = Path(__file__).resolve().parent
TARGET_PREFIX = "https://pub-ee9e9582bccd46678515d77c4ca44c3c.r2.dev"
FILE_EXTENSIONS = {".html", ".css", ".js"}
ATTR_PATTERN = re.compile(r"([:\w-]+)\s*=\s*([\"'])(.*?)\2", re.IGNORECASE | re.DOTALL)
TIMEOUT = 8
MAX_WORKERS = 16


def normalize_url(raw_url: str) -> str:
    raw_url = html.unescape(raw_url.strip())
    parts = urlsplit(raw_url)
    encoded_path = quote(parts.path, safe="/%._-~!$&'()*+,;=:@")
    encoded_query = quote(parts.query, safe="=&%._-~!$'()*+,;:@/?")
    return urlunsplit((parts.scheme, parts.netloc, encoded_path, encoded_query, parts.fragment))


def extract_urls_from_attr(attr_name: str, attr_value: str):
    value = html.unescape(attr_value.strip())
    candidates = []

    if attr_name in {"srcset", "imagesrcset"}:
        for chunk in value.split(","):
            chunk = chunk.strip()
            if TARGET_PREFIX not in chunk:
                continue
            cleaned = re.sub(r"\s+\d+(?:\.\d+)?[wx]$", "", chunk).strip()
            if cleaned:
                candidates.append(cleaned)
        return candidates

    if attr_name in {"data-video-urls"}:
        for chunk in value.split(","):
            chunk = chunk.strip()
            if chunk.startswith(TARGET_PREFIX):
                candidates.append(chunk)
        return candidates

    if attr_name == "style":
        candidates.extend(re.findall(re.escape(TARGET_PREFIX) + r'[^"\')]+', value))
        return candidates

    if TARGET_PREFIX in value:
        candidates.append(value)
    return candidates


def extract_urls():
    url_locations = defaultdict(list)
    for path in PROJECT_ROOT.rglob("*"):
        if path.suffix.lower() not in FILE_EXTENSIONS:
            continue
        if "local" in path.parts:
            continue
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for match in ATTR_PATTERN.finditer(content):
            attr_name = match.group(1).lower()
            attr_value = match.group(3)
            line_no = content.count("\n", 0, match.start()) + 1
            for raw_url in extract_urls_from_attr(attr_name, attr_value):
                if raw_url.startswith(TARGET_PREFIX):
                    url_locations[raw_url].append((path.relative_to(PROJECT_ROOT).as_posix(), line_no))
    return url_locations


def check_url(url: str):
    normalized = normalize_url(url)
    methods = ["HEAD", "GET"]
    last_error = None
    for method in methods:
        req = Request(normalized, method=method, headers={"User-Agent": "Mozilla/5.0", "Accept": "*/*"})
        if method == "GET":
            req.add_header("Range", "bytes=0-0")
        try:
            with urlopen(req, timeout=TIMEOUT) as response:
                return response.status, response.headers.get_content_type(), normalized, None
        except HTTPError as exc:
            if method == "HEAD" and exc.code in {403, 405, 501}:
                last_error = exc
                continue
            if method == "GET" and exc.code == 416:
                return 200, None, normalized, None
            return exc.code, exc.headers.get_content_type() if exc.headers else None, normalized, str(exc)
        except URLError as exc:
            last_error = exc
            continue
    return None, None, normalized, str(last_error) if last_error else "unknown error"


def main():
    only_svg = "--svg-only" in sys.argv
    url_locations = extract_urls()
    urls = sorted(url_locations)
    if only_svg:
        urls = [url for url in urls if ".svg" in url.lower()]

    print(f"Found {len(urls)} unique {'SVG ' if only_svg else ''}URLs to check.")
    status_counts = Counter()
    failures = []
    content_types = Counter()

    future_to_url = {}
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        for url in urls:
            future_to_url[executor.submit(check_url, url)] = url

        for idx, future in enumerate(as_completed(future_to_url), start=1):
            url = future_to_url[future]
            status, content_type, normalized, error = future.result()
            key = status if status is not None else "error"
            status_counts[key] += 1
            if content_type:
                content_types[content_type] += 1
            if status != 200:
                failures.append((url, normalized, status, error, url_locations[url]))
            if idx % 50 == 0 or idx == len(urls):
                print(f"Checked {idx}/{len(urls)}")

    print("\nStatus summary:")
    for key, count in sorted(status_counts.items(), key=lambda item: str(item[0])):
        print(f"  {key}: {count}")

    if content_types:
        print("\nTop content types:")
        for content_type, count in content_types.most_common(10):
            print(f"  {content_type}: {count}")

    if failures:
        print(f"\nFailures: {len(failures)}")
        for url, normalized, status, error, locations in failures[:100]:
            refs = ", ".join(f"{file}:{line}" for file, line in locations[:3])
            print(f"  status={status} url={url}")
            if normalized != url:
                print(f"    normalized={normalized}")
            if error:
                print(f"    error={error}")
            print(f"    refs={refs}")
        return 1

    print("\nAll checked URLs returned HTTP 200.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
