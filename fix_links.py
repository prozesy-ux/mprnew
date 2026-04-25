"""
Fix all external links across all HTML files in mpr-main.
Changes:
1. All WhatsApp numbers → +13138803417 (keep only this one)
2. TidyCal URL → tidycal.com/prozesymedia/lets-discuss
3. Figma links → href="#" (remove external)
4. designmonks.ae/ and www.designmonks.co/* → prozesy.com equivalents
5. Affiliate links (framer, lemonsqueezy) → href="#"
6. Noman personal social links → href="#"
"""

import os
import re

ROOT = r"c:\Users\mpro\Desktop\mprnew\mpr-main"

# --- Simple string replacements ---
SIMPLE_REPLACEMENTS = [
    # 1. WhatsApp: redirect all 4 other numbers to +13138803417
    ("https://wa.me/+971522057100",  "https://wa.me/+13138803417"),
    ("https://wa.me/+17165036335",   "https://wa.me/+13138803417"),
    ("https://wa.me/+35794068727",   "https://wa.me/+13138803417"),
    ("https://wa.me/+393892941226",  "https://wa.me/+13138803417"),

    # 2. TidyCal booking URL
    ("https://tidycal.com/designmonks/lets-discuss",
     "https://tidycal.com/prozesymedia/lets-discuss"),

    # 4a. designmonks.ae → prozesy.com
    ("https://designmonks.ae/",       "https://prozesy.com/"),

    # 4b. designmonks.co industry/success paths → prozesy.com
    ("https://www.designmonks.co/industry/cybersecurity", "https://prozesy.com/industry/cybersecurity"),
    ("https://www.designmonks.co/industry/edtech",        "https://prozesy.com/industry/edtech"),
    ("https://www.designmonks.co/industry/fintech",       "https://prozesy.com/industry/fintech"),
    ("https://www.designmonks.co/industry/fitness-gym",   "https://prozesy.com/industry/fitness-gym"),
    ("https://www.designmonks.co/success",                "https://prozesy.com/success"),
    # 4c. bare designmonks.co root (must come AFTER specific paths)
    ("https://www.designmonks.co/",   "https://prozesy.com/"),
]

# --- href value replacements (old_href → new_href) ---
# These will match href="<old>" and replace the href value only with "#"
HREF_REMOVE = [
    # 3. Figma links
    r"https://www\.figma\.com/design/[^\"']+",
    r"https://www\.figma\.com/proto/[^\"']+",

    # 5. Affiliate / referral links
    r"https://startio\.framer\.website/[^\"']*",
    r"https://www\.framer\.com/pricing[^\"']*",
    r"https://designmonks1\.lemonsqueezy\.com/buy/[^\"']+",

    # 6. Noman personal social links
    r"https://www\.facebook\.com/anoman1234/[^\"']*",
    r"https://www\.instagram\.com/nomandigital/[^\"']*",
    r"https://www\.linkedin\.com/in/nomandigital/[^\"']*",
]

# Compile href-remove patterns to match href="..." or href='...'
HREF_REMOVE_PATTERNS = [
    re.compile(r'href=["\'](' + p + r')["\']', re.IGNORECASE)
    for p in HREF_REMOVE
]


def process_file(filepath):
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    original = content

    # Apply simple string replacements
    for old, new in SIMPLE_REPLACEMENTS:
        content = content.replace(old, new)

    # Apply href removals (replace full href value with #)
    for pattern in HREF_REMOVE_PATTERNS:
        content = pattern.sub('href="#"', content)

    if content != original:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    return False


def main():
    changed = 0
    total = 0
    for dirpath, dirnames, filenames in os.walk(ROOT):
        for filename in filenames:
            if filename.endswith(".html"):
                total += 1
                filepath = os.path.join(dirpath, filename)
                if process_file(filepath):
                    changed += 1
                    print(f"  UPDATED: {os.path.relpath(filepath, ROOT)}")

    print(f"\nDone. {changed}/{total} files updated.")


if __name__ == "__main__":
    main()
