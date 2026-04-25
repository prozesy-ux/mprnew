import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urlparse
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


ROOT = Path(r"c:\Users\mpro\Desktop\mprnew\mpr-main")
FILE_GLOBS = ("*.html", "*.css", "*.js")
URL_PATTERN = re.compile(r"https://[^\s\"'<>),]+", re.IGNORECASE)
MAX_WORKERS = 16
TIMEOUT = 12


def iter_files():
    for glob in FILE_GLOBS:
        for path in ROOT.rglob(glob):
            if "local" in path.parts:
                continue
            yield path


def is_css_js(url: str) -> bool:
    if "${" in url or "+" in url or url.endswith("="):
        return False
    parsed = urlparse(url)
    lower_path = parsed.path.lower()
    return lower_path.endswith(".css") or lower_path.endswith(".js")


def gather_urls():
    urls = set()
    for fpath in iter_files():
        try:
            text = fpath.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for m in URL_PATTERN.finditer(text):
            url = m.group(0)
            if is_css_js(url):
                urls.add(url)
    return sorted(urls)


def check_url(url: str):
    for method in ("HEAD", "GET"):
        req = Request(url, method=method, headers={"User-Agent": "Mozilla/5.0", "Accept": "*/*"})
        if method == "GET":
            req.add_header("Range", "bytes=0-0")
        try:
            with urlopen(req, timeout=TIMEOUT) as resp:
                return url, resp.status, None
        except HTTPError as exc:
            if method == "HEAD" and exc.code in {403, 405, 501}:
                continue
            if method == "GET" and exc.code == 416:
                return url, 200, None
            return url, exc.code, str(exc)
        except URLError as exc:
            if method == "HEAD":
                continue
            return url, None, str(exc)
    return url, None, "unknown error"


def main():
    urls = gather_urls()
    print(f"Found {len(urls)} CSS/JS URLs to validate.")
    if not urls:
        return

    failures = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(check_url, u) for u in urls]
        for i, fut in enumerate(as_completed(futures), start=1):
            url, status, err = fut.result()
            if status != 200:
                failures.append((url, status, err))
            if i % 50 == 0 or i == len(urls):
                print(f"Checked {i}/{len(urls)}")

    if failures:
        print(f"\nFailures: {len(failures)}")
        for url, status, err in failures[:200]:
            print(f"  status={status} url={url}")
            if err:
                print(f"    error={err}")
        raise SystemExit(1)

    print("All CSS/JS URLs returned HTTP 200.")


if __name__ == "__main__":
    main()
