"""
Verify all design-monks JS files exist locally and return HTTP 200 from R2.
"""
import os
import requests

ROOT = r"c:\Users\mpro\Desktop\mprnew\mpr-main"
LOCAL_DIR = os.path.join(ROOT, "local", "external-code", "cdn.prod.website-files.com", "672a72b52eb5f37692d645a9", "js")
R2_BASE = "https://pub-ee9e9582bccd46678515d77c4ca44c3c.r2.dev/local/external-code/cdn.prod.website-files.com/672a72b52eb5f37692d645a9/js"

files = sorted(os.listdir(LOCAL_DIR))
print(f"Checking {len(files)} files...\n")

all_ok = True
for f in files:
    local_path = os.path.join(LOCAL_DIR, f)
    local_size = os.path.getsize(local_path)
    r2_url = f"{R2_BASE}/{f}"
    try:
        resp = requests.head(r2_url, timeout=15)
        r2_status = resp.status_code
        r2_ok = r2_status == 200
    except Exception as e:
        r2_status = str(e)
        r2_ok = False
    status_icon = "OK" if r2_ok else "FAIL"
    if not r2_ok:
        all_ok = False
    print(f"  [{status_icon}] local={local_size:>8,}B  r2={r2_status}  {f}")

print()
if all_ok:
    print(f"All {len(files)} files confirmed: local + R2 OK.")
else:
    print("WARNING: Some files are missing or broken on R2!")
