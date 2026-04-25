import os, re

fixes = [
    ('Â©', '©'),
    ('Â®', '®'),
    ('Â·', '·'),
    ('Â\u00a0', ' '),  # Â + non-breaking space -> space
    ('Â ', ' '),        # Â + regular space -> space
    ('Â<', '<'),        # Â before HTML tag
    ('Â\n', '\n'),      # Â at end of line
    ('Â', ''),          # any remaining Â -> remove
    # Also fix â€™ -> ' (right single quote)
    ('â€™', '\u2019'),
    # â€œ -> " (left double quote)
    ('â€œ', '\u201c'),
    # â€ -> " (right double quote)  
    ('â€\x9d', '\u201d'),
    # â€˜ -> ' (left single quote)
    ('â€˜', '\u2018'),
    # don€™t style
    ('don\u20ac\u2122t', "don't"),
    ('can\u20ac\u2122t', "can't"),
    ('won\u20ac\u2122t', "won't"),
    ('it\u20ac\u2122s', "it's"),
    ('that\u20ac\u2122s', "that's"),
    ('we\u20ac\u2122re', "we're"),
    ('you\u20ac\u2122re', "you're"),
    ('they\u20ac\u2122re', "they're"),
    ('\u20ac\u2122', '\u2019'),  # general €™ -> '
    ('\u20ac\u201c', '\u201c'),  # €" -> "
    ('\u20ac\u201d', '\u201d'),
    # â€¢ -> • (bullet U+2022): bytes E2 80 A2 -> U+2022
    ('\u00e2\u20ac\u00a2', '\u2022'),
    # â€¦ -> … (ellipsis U+2026): bytes E2 80 A6 -> U+2026
    # Fix longer pattern Å"â€¦ -> ŕ… first (OE ligature + ellipsis)
    ('\u00c5\u201c\u00e2\u20ac\u00a6', '\u0153\u2026'),
    # Then standalone â€¦ -> …
    ('\u00e2\u20ac\u00a6', '\u2026'),
    # â€ NBSP ' -> — (em dash U+2014): bytes E2 80 A0 92 (mangled)
    ('\u00e2\u20ac\u00a0\u2019', '\u2014'),
    # â€" -> — (em dash, where " is U+201D): bytes E2 80 94
    ('\u00e2\u20ac\u201d', '\u2014'),
    # â€" -> – (en dash, where " is U+201C): bytes E2 80 93
    ('\u00e2\u20ac\u201c', '\u2013'),
]

def fix_emoji_mojibake(text):
    """Fix double-encoded emoji sequences (Windows-1252 bytes re-encoded as UTF-8, twice)."""
    # Pattern: sequences starting with Ã° Å¸ (double-encoded F0 9F = emoji range)
    # These need TWO rounds of windows-1252 decode to restore
    emoji_pattern = re.compile(r'Ã°Å¸[^\s<"\']{4,14}')
    
    def try_double_decode(m):
        s = m.group(0)
        try:
            # First decode round
            mid = s.encode('windows-1252').decode('utf-8')
            # Second decode round
            final = mid.encode('windows-1252').decode('utf-8')
            return final
        except Exception:
            try:
                return s.encode('windows-1252').decode('utf-8')
            except Exception:
                return s
    
    return emoji_pattern.sub(try_double_decode, text)

total_files = 0
total_replacements = 0

for root, dirs, files in os.walk('.'):
    dirs[:] = [d for d in dirs if d not in ['local', '.git']]
    for f in files:
        if f.endswith('.html'):
            path = os.path.join(root, f)
            try:
                text = open(path, encoding='utf-8').read()
                original = text
                count = 0
                for old, new in fixes:
                    occurrences = text.count(old)
                    if occurrences:
                        text = text.replace(old, new)
                        count += occurrences
                # Fix double-encoded emojis
                fixed_emoji = fix_emoji_mojibake(text)
                if fixed_emoji != text:
                    count += len(re.findall(r'Ã°', text))
                    text = fixed_emoji
                if text != original:
                    open(path, 'w', encoding='utf-8').write(text)
                    total_files += 1
                    total_replacements += count
                    print(f'Fixed {count} in {path}')
            except Exception as e:
                print(f'ERROR {path}: {e}')

print(f'\nDone: {total_replacements} replacements across {total_files} files')
