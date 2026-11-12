"""Statistical analysis (E7). Exact integer/Fraction arithmetic; deterministic bootstrap (seeded DetRNG).

Thresholds are never invented: success thresholds come from the protocol and may be PENDING_APPROVAL.
"""
from __future__ import annotations

from decimal import Decimal, getcontext
from fractions import Fraction

from .prng import DetRNG

Z = {900000: Decimal("1.6448536269514722"), 950000: Decimal("1.9599639845400538"),
     990000: Decimal("2.5758293035489004")}


def q6_round(x: Fraction) -> int:
    """Round half to even to an integer number of Q6 units."""
    q, r = divmod(x.numerator, x.denominator)
    if 2 * r > x.denominator or (2 * r == x.denominator and q % 2):
        q += 1
    return q


def wilson_q6(k: int, n: int, level_q6: int) -> dict:
    if n == 0:
        return {"k": 0, "n": 0}
    getcontext().prec = 50
    z, nn, p = Z[level_q6], Decimal(n), Decimal(k) / Decimal(n)
    den = 1 + z * z / nn
    center = (p + z * z / (2 * nn)) / den
    half = z * ((p * (1 - p) / nn + z * z / (4 * nn * nn)).sqrt()) / den
    to = lambda d: int((max(Decimal(0), min(Decimal(1), d)) * 1_000_000).to_integral_value(rounding="ROUND_HALF_EVEN"))
    return {"k": k, "n": n, "rate_q6": q6_round(Fraction(k * 1_000_000, n)), "lo_q6": to(center - half),
            "hi_q6": to(center + half)}


def bootstrap_mean_q6(values: list[int], resamples: int, seed: bytes, level_q6: int, label: str) -> dict:
    n = len(values)
    if n == 0:
        return {"n": 0}
    rng = DetRNG(seed, "bootstrap:" + label)
    means = sorted(q6_round(Fraction(sum(values[rng.below(n)] for _ in range(n)), n)) for _ in range(resamples))
    alpha = Fraction(1_000_000 - level_q6, 1_000_000)
    lo = alpha / 2 * resamples
    hi = (1 - alpha / 2) * resamples
    lo_i = lo.numerator // lo.denominator
    hi_i = min(resamples - 1, max(0, -(-hi.numerator // hi.denominator) - 1))
    return {"n": n, "mean_q6": q6_round(Fraction(sum(values), n)), "lo_q6": means[lo_i], "hi_q6": means[hi_i],
            "method": "PERCENTILE_BOOTSTRAP", "resamples": resamples}


def summarize(values: list[int]) -> dict:
    if not values:
        return {"n": 0}
    s = sorted(values)
    mid = len(s) // 2
    med = Fraction(s[mid]) if len(s) % 2 else Fraction(s[mid - 1] + s[mid], 2)
    return {"n": len(s), "min": s[0], "max": s[-1], "median_q6": q6_round(med * 1_000_000),
            "mean_q6": q6_round(Fraction(sum(s) * 1_000_000, len(s)))}


def analyze(runs: list[dict], plan: dict, expected: list[tuple[str, str]], baseline_ids: list[str]) -> dict:
    """runs: participant-keyed summaries; expected: (participant_key, instance_public_id) design cells.

    Output uses lists (not dicts keyed by participant) so it is valid CR-1 (keys are snake_case only).
    """
    level, B, seed = plan["ci_level_q6"], plan["bootstrap_resamples"], bytes.fromhex(plan["analysis_seed"])
    by_cell = {(r["participant_key"], r["instance_public_id"]): r for r in runs}
    out = {"participants": [], "missing": [], "comparisons": [],
           "missing_data_policy": plan["missing_data_policy"]}
    participants = sorted({p for p, _ in expected})
    for p in participants:
        cells = [(p, t) for q, t in expected if q == p]
        present = [by_cell[c] for c in cells if c in by_cell]
        missing = [c[1] for c in cells if c not in by_cell]
        out["missing"] += [{"participant": p, "instance_public_id": t} for t in missing]
        scored = [r for r in present if r["score_status"] == "SCORED"]
        scores = [r["score_q6"] for r in scored] + [0] * len(missing)      # COUNT_AS_FAILURE
        succ = sum(r["outcome"] == "SUCCESS" for r in present)
        n = len(cells)
        perturbed = [r for r in present if r["perturbations_encountered"] > 0]
        entry = {
            "participant": p, "cells": n, "present": len(present), "missing": len(missing),
            "excluded_no_reference": sum(r["score_status"] == "EXCLUDED" for r in present),
            "success": wilson_q6(succ, n, level),
            "outcomes": [{"outcome": o, "count": sum(r["outcome"] == o for r in present)}
                         for o in sorted({r["outcome"] for r in present})],
            "score": bootstrap_mean_q6(scores, B, seed, level, p),
            "cost_solved": summarize([r["cost"] for r in present if r["outcome"] == "SUCCESS"]),
            "recovery": {"runs_with_perturbation": len(perturbed),
                         "recovered": wilson_q6(sum(r["outcome"] == "SUCCESS" for r in perturbed), len(perturbed), level)},
            "efficiency_logical_steps": summarize([r["steps"] for r in present]),
            "efficiency_wall_ms_nondeterministic": summarize([r["wall_ms"] for r in present]),
        }
        if n:
            entry["failure_rate_q6"] = q6_round(Fraction((n - succ) * 1_000_000, n))
        out["participants"].append(entry)
    for s in [p for p in participants if p not in baseline_ids]:
        for b in baseline_ids:
            tasks = sorted({t for q, t in expected if q == s} & {t for q, t in expected if q == b})
            diffs = []
            for t in tasks:
                a, c = by_cell.get((s, t)), by_cell.get((b, t))
                sa = a["score_q6"] if a and a["score_status"] == "SCORED" else 0
                sb = c["score_q6"] if c and c["score_status"] == "SCORED" else 0
                diffs.append(sa - sb)
            out["comparisons"].append({"system": s, "baseline": b, "paired_tasks": len(tasks),
                                       "diff": bootstrap_mean_q6(diffs, B, seed, level, f"{s}|{b}")})
    return out
