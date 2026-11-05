#!/usr/bin/env python3
"""Verify the curated SKYNET V2 public package manifest; standard library only."""
import hashlib
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "SHA256SUMS.txt"

def main() -> int:
    expected = {}
    for line in MANIFEST.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        digest, sep, rel = line.partition("  ")
        if not sep or len(digest) != 64 or any(c not in '0123456789abcdef' for c in digest):
            raise ValueError("Invalid manifest entry")
        path = Path(rel)
        if path.is_absolute() or '..' in path.parts or rel in expected:
            raise ValueError("Unsafe or duplicate manifest entry")
        expected[rel] = digest
    actual = {p.relative_to(ROOT).as_posix() for p in ROOT.rglob('*') if p.is_file() and p != MANIFEST}
    if actual != set(expected):
        print('FAIL: manifest coverage mismatch', file=sys.stderr)
        return 1
    for rel, digest in expected.items():
        if hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() != digest:
            print(f'FAIL: checksum mismatch: {rel}', file=sys.stderr)
            return 1
    print(f'PASS: {len(expected)} files verified; full coverage')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
