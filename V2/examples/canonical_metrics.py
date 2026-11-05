"""Public reference example, NOT the SKYNET V2 private runtime.

Illustrates strict integer-only canonical metrics and SHA-256 evidence digest.
"""
import hashlib
import json


def canonical_metrics(*, covered: int, total: int, utility_q6: int) -> dict:
    """Construct exact coverage fraction and q6 utility without floats."""
    values = (covered, total, utility_q6)
    if any(type(x) is not int for x in values):
        raise TypeError("metrics must be exact integers")
    if total <= 0 or not (0 <= covered <= total):
        raise ValueError("invalid coverage counters")
    if not (0 <= utility_q6 <= 1_000_000):
        raise ValueError("utility_q6 outside [0, 1_000_000]")
    return {"coverage_numerator": covered,
            "coverage_denominator": total,
            "utility_q6": utility_q6}


def evidence_digest(metrics: dict) -> str:
    """Reject unexpected fields/types before deterministic serialization."""
    if type(metrics) is not dict or set(metrics) != {
        "coverage_numerator", "coverage_denominator", "utility_q6"
    }:
        raise ValueError("unexpected metric schema")
    normalized = canonical_metrics(
        covered=metrics["coverage_numerator"],
        total=metrics["coverage_denominator"],
        utility_q6=metrics["utility_q6"])
    payload = json.dumps(normalized, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=False, allow_nan=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()
