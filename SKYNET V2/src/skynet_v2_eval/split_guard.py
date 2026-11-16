"""Fail-closed train/evaluation split separation for public experiment metadata.

This checks declared IDs only. It does not prove semantic novelty or prevent
contamination through external model training or undisclosed data sources.
"""
from __future__ import annotations

import hashlib
from collections.abc import Iterable

from .paired_evidence import EvidenceError


def _validate(items: Iterable[str], label: str) -> set[str]:
    if isinstance(items, (str, bytes)):
        raise EvidenceError(f"{label} must be an iterable of IDs")
    try:
        values = list(items)
    except TypeError as exc:
        raise EvidenceError(f"{label} must be iterable") from exc
    if any(not isinstance(x, str) or not x or len(x) > 128 or any(c.isspace() for c in x) for x in values):
        raise EvidenceError(f"invalid ID in {label}")
    if len(set(values)) != len(values):
        raise EvidenceError(f"duplicate IDs in {label}")
    return set(values)


def validate_splits(train: Iterable[str], validation: Iterable[str], hidden: Iterable[str]) -> dict:
    """Require nonempty, pairwise-disjoint split IDs; produce a stable fingerprint."""
    splits = {"train": _validate(train, "train"), "validation": _validate(validation, "validation"), "hidden": _validate(hidden, "hidden")}
    if any(not v for v in splits.values()):
        raise EvidenceError("each split must contain at least one ID")
    for left, right in (("train", "validation"), ("train", "hidden"), ("validation", "hidden")):
        if splits[left] & splits[right]:
            raise EvidenceError(f"overlap between {left} and {right}")
    serialized = "\n".join(f"{name}:{item}" for name in sorted(splits) for item in sorted(splits[name]))
    return {"counts": {k: len(v) for k, v in splits.items()}, "split_sha256": hashlib.sha256(serialized.encode()).hexdigest(), "status": "ID_DISJOINT_ONLY"}
