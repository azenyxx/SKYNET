"""ULID-format identifiers (26 chars, Crockford base32)."""
from __future__ import annotations

import hashlib
import os

_ALPHA = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"


def ulid_from_bytes(raw16: bytes) -> str:
    n = int.from_bytes(raw16[:16].rjust(16, b"\0"), "big")
    out = []
    for _ in range(26):
        out.append(_ALPHA[n & 31])
        n >>= 5
    s = "".join(reversed(out))
    return "0" + s[1:] if s[0] not in "01234567" else s  # keep within 128-bit ULID range


def new_id() -> str:
    return ulid_from_bytes(os.urandom(16))


def id_from_text(text: str) -> str:
    return ulid_from_bytes(hashlib.sha256(text.encode("utf-8")).digest()[:16])
