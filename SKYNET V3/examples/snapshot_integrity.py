"""Public, standalone example of deterministic state-artifact integrity checks.

This is not SKYNET's private cognitive core or production snapshot adapter.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

SCHEMA = "skynet.public.state-demo"
VERSION = 1
TRUST = "UNTRUSTED_DEV"


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def make_artifact(state: dict[str, int]) -> bytes:
    """Build a deterministic example artifact (no timestamps or process IDs)."""
    if not isinstance(state, dict) or not state or any(
        not isinstance(k, str) or not k or type(v) is not int or v < 0
        for k, v in state.items()
    ):
        raise ValueError("invalid state")
    payload = {"schema": SCHEMA, "version": VERSION, "trust": TRUST, "state": state}
    wrapper = {"payload": payload, "sha256": hashlib.sha256(_canonical(payload)).hexdigest()}
    return _canonical(wrapper)


def verify_artifact(raw: bytes) -> dict[str, int]:
    """Fail closed on corruption, incompatible schema/version, or noncanonical bytes."""
    try:
        wrapper = json.loads(raw.decode("utf-8"), object_pairs_hook=_reject_duplicates)
        if not isinstance(wrapper, dict) or set(wrapper) != {"payload", "sha256"}:
            raise ValueError("invalid envelope")
        payload, digest = wrapper["payload"], wrapper["sha256"]
        if not isinstance(payload, dict) or set(payload) != {"schema", "version", "trust", "state"}:
            raise ValueError("invalid payload")
        if payload["schema"] != SCHEMA or type(payload["version"]) is not int or payload["version"] != VERSION:
            raise ValueError("unsupported schema/version")
        if payload["trust"] != TRUST or type(digest) is not str or len(digest) != 64:
            raise ValueError("invalid trust/digest")
        state = payload["state"]
        if not isinstance(state, dict) or not state or any(
            not isinstance(k, str) or not k or type(v) is not int or v < 0
            for k, v in state.items()
        ):
            raise ValueError("invalid state")
        if raw != _canonical(wrapper):
            raise ValueError("noncanonical bytes")
        if hashlib.sha256(_canonical(payload)).hexdigest() != digest:
            raise ValueError("digest mismatch")
        return dict(state)
    except (UnicodeError, json.JSONDecodeError, TypeError, KeyError, OverflowError) as exc:
        raise ValueError("corrupt artifact") from exc


def _reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    out = {}
    for key, value in pairs:
        if key in out:
            raise ValueError("duplicate JSON key")
        out[key] = value
    return out
