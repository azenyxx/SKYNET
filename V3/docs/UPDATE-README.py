#!/usr/bin/env python3
"""Safely update a marked SKYNET V3 section; refuse ambiguous legacy sections."""
from pathlib import Path
import re
root = Path(__file__).resolve().parent
readme = root / 'README.md'
section = (root / 'README-V3-SECTION.md').read_text(encoding='utf-8').rstrip() + '\n'
start, end = '<!-- SKYNET-V3-START -->', '<!-- SKYNET-V3-END -->'
if not readme.is_file():
    raise SystemExit('README.md missing: run from the target repository root')
original = readme.read_text(encoding='utf-8')
if original.count(start) != original.count(end) or original.count(start) > 1:
    raise SystemExit('Ambiguous SKYNET V3 markers; edit README.md manually')
if start in original:
    a = original.index(start)
    b = original.index(end)
    if b < a:
        raise SystemExit('Malformed V3 markers')
    updated = original[:a] + start + '\n' + section + end + original[b+len(end):]
else:
    if re.search(r'(?im)^#{1,3}\s+.*(?:SKYNET\s*)?V3\b', original):
        raise SystemExit('Existing unmarked V3 heading found. Replace that section manually; no duplicate appended.')
    updated = original.rstrip() + '\n\n' + start + '\n' + section + end + '\n'
readme.write_text(updated, encoding='utf-8')
print('README updated; review git diff before staging')
