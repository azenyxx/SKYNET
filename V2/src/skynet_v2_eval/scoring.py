"""APLUS-SCORING@1.0 (V2-000C APLUS-SCORING-STANDARD). Exact integer arithmetic; FLOOR_Q6 rounding."""
from __future__ import annotations

from .errors import EvalError

SCORED_CLASSES = {"OPTIMAL_PROVEN", "BEST_KNOWN"}


def score(outcome: str, cost: int, reference: dict) -> dict:
    """Score depends only on this run and the frozen reference (never on other participants)."""
    cls = reference["class"]
    if cls not in SCORED_CLASSES:
        return {"status": "EXCLUDED", "reference_class": cls, "reason": "no verified reference solution"}
    c_ref, lb = reference.get("c_ref"), reference.get("lb")
    if c_ref is None:
        raise EvalError("E-EVAL-030", "reference class requires c_ref")   # never silently substituted
    if outcome != "SUCCESS":
        return {"status": "SCORED", "value_q6": 0, "reference_class": cls, "label": "UNSOLVED_OR_FAILED"}
    if cost <= 0:
        raise EvalError("E-EVAL-030", "successful run with non-positive cost")
    if lb is not None and cost < lb:
        raise EvalError("E-EVAL-030", f"cost {cost} below proven lower bound {lb}")
    if cls == "OPTIMAL_PROVEN" and cost < c_ref:
        raise EvalError("E-EVAL-030", f"cost {cost} below proven optimum {c_ref}")
    out = {"status": "SCORED", "value_q6": c_ref * 1_000_000 // cost, "reference_class": cls,
           "label": "OPTIMALITY_RATIO" if cls == "OPTIMAL_PROVEN" else "REFERENCE_RELATIVE"}
    if cls == "BEST_KNOWN":
        out["beats_reference"] = cost < c_ref
        if lb is not None:  # uncertainty: true optimality ratio lies in [lb/cost, min(1, c_ref/cost)]
            out["optimality_ratio_bounds_q6"] = {"lo": lb * 1_000_000 // cost,
                                                 "hi": min(1_000_000, c_ref * 1_000_000 // cost)}
    return out
