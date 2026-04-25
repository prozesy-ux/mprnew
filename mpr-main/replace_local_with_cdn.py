import os
import sys

# Usage: python replace_local_with_cdn.py https://pub-XXXX.r2.dev
# Or edit CDN_BASE directly below:
CDN_BASE = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else ""

if not CDN_BASE:
    print("ERROR: Provide the R2 public URL as an argument:")
    print("  python replace_local_with_cdn.py https://pub-XXXX.r2.dev")
    sys.exit(1)

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
EXTENSIONS = (".html", ".css", ".js")

total_files = 0
total_replacements = 0

for root, dirs, files in os.walk(PROJECT_ROOT):
    # Skip the local/ folder itself
    dirs[:] = [d for d in dirs if d != "local"]
    for fname in files:
        if not fname.endswith(EXTENSIONS):
            continue
        fpath = os.path.join(root, fname)
        with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        new_content = content.replace("/local/", f"{CDN_BASE}/local/")
        if new_content != content:
            count = content.count("/local/")
            with open(fpath, "w", encoding="utf-8") as f:
                f.write(new_content)
            total_files += 1
            total_replacements += count
            print(f"  Updated ({count}x): {os.path.relpath(fpath, PROJECT_ROOT)}")

print(f"\nDone. Updated {total_files} files, {total_replacements} replacements.")
print(f"All /local/ paths now point to: {CDN_BASE}/local/")
