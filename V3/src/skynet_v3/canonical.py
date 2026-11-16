"""Canonical JSON (frozen contract): sorted keys (Unicode code point order), no
insignificant whitespace, UTF-8, NFC strings, integers only, no NaN/Infinity,
SHA-256 digests rendered as 'sha256:<hex>'."""
import hashlib
import json
import unicodedata

from .errors import invalid


class CanonicalError(ValueError):
    pass


def _check(obj, path="$"):
    if obj is None or isinstance(obj, bool):
        return
    if isinstance(obj, int):
        return
    if isinstance(obj, float):
        raise CanonicalError(f"floating-point value at {path}")
    if isinstance(obj, str):
        if unicodedata.normalize("NFC", obj) != obj:
            raise CanonicalError(f"non-NFC string at {path}")
        return
    if isinstance(obj, list):
        for i, v in enumerate(obj):
            _check(v, f"{path}[{i}]")
        return
    if isinstance(obj, dict):
        for k, v in obj.items():
            if not isinstance(k, str):
                raise CanonicalError(f"non-string key at {path}")
            _check(k, f"{path}.<key>")
            _check(v, f"{path}.{k}")
        return
    raise CanonicalError(f"unsupported type {type(obj).__name__} at {path}")


def canonical_bytes(obj) -> bytes:
    _check(obj)
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                      allow_nan=False).encode("utf-8")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def digest(obj) -> str:
    return "sha256:" + sha256_hex(canonical_bytes(obj))


MAX_JSON_DEPTH = 32


def json_depth(text: str, limit: int = MAX_JSON_DEPTH) -> int:
    """Bounded pre-parse nesting scan (string-aware). Returns early once limit exceeded."""
    depth = maxd = 0
    in_str = esc = False
    for ch in text:
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
        elif ch == '"':
            in_str = True
        elif ch in "[{":
            depth += 1
            if depth > maxd:
                maxd = depth
                if maxd > limit:
                    return maxd
        elif ch in "]}":
            depth -= 1
    return maxd


def strict_loads(raw: bytes):
    """Parse JSON rejecting duplicate keys, floats, NaN/Infinity and invalid UTF-8."""
    try:
        text = bytes(raw).decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        raise invalid("INVALID_UTF8", "$", "input is not valid UTF-8")

    if json_depth(text) > MAX_JSON_DEPTH:
        raise invalid("NESTING_TOO_DEEP", "$", f"nesting depth exceeds {MAX_JSON_DEPTH}")

    def pairs(items):
        d = {}
        for k, v in items:
            if k in d:
                raise invalid("DUPLICATE_KEY", "$", "duplicate object key")
            d[k] = v
        return d

    def no_float(_s):
        raise invalid("NON_INTEGER_NUMBER", "$", "floating-point numbers are not permitted")

    def no_const(_s):
        raise invalid("NON_FINITE_NUMBER", "$", "NaN/Infinity are not permitted")

    try:
        return json.loads(text, object_pairs_hook=pairs, parse_float=no_float, parse_constant=no_const)
    except json.JSONDecodeError:
        raise invalid("MALFORMED_JSON", "$", "input is not well-formed JSON")
    except RecursionError:
        raise invalid("NESTING_TOO_DEEP", "$", "input nesting too deep")
