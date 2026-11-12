"""Public, dependency-free paired evaluation evidence checks.

No statistical significance or superhuman claim is inferred from these summaries.
All scores are fixed-point Q6 integers; pairing prevents cherry-picked run sets.
"""
from __future__ import annotations

import hashlib
import json
from fractions import Fraction

Q6 = 1_000_000


class EvidenceError(ValueError):
    """Fail-closed validation error for incomplete or malformed evaluation evidence."""


def _integer(value: object, field: str, minimum: int = 0) -> int:
    if type(value) is not int or value < minimum:
        raise EvidenceError(f"{field} must be an integer >= {minimum}")
    return value


def _identifier(value: object, field: str) -> str:
    if not isinstance(value, str) or not value or len(value) > 128 or any(c.isspace() for c in value):
        raise EvidenceError(f"invalid {field}")
    return value


def _round_half_even(value: Fraction) -> int:
    q, r = divmod(value.numerator, value.denominator)
    return q + int(2 * r > value.denominator or (2 * r == value.denominator and q % 2 == 1))


def evaluate_pairs(records: list[dict], *, candidate: str, baseline: str) -> dict:
    """Compare exact matched task IDs, rejecting missing, repeated or invalid runs.

    Each record: {task_id, participant, score_q6, cost_units, status}.
    Only status='VERIFIED' is admissible. Higher score is better; lower cost
    is better. Cost is reported separately, never folded into quality.
    """
    _identifier(candidate, "candidate")
    _identifier(baseline, "baseline")
    if candidate == baseline:
        raise EvidenceError("candidate and baseline must differ")
    if not isinstance(records, list) or not records:
        raise EvidenceError("nonempty records list required")
    cells: dict[tuple[str, str], tuple[int, int]] = {}
    for record in records:
        if not isinstance(record, dict) or set(record) != {"task_id", "participant", "score_q6", "cost_units", "status"}:
            raise EvidenceError("invalid record schema")
        task = _identifier(record["task_id"], "task_id")
        who = _identifier(record["participant"], "participant")
        if who not in (candidate, baseline):
            raise EvidenceError("unexpected participant")
        if record["status"] != "VERIFIED":
            raise EvidenceError("only VERIFIED records are admissible")
        score = _integer(record["score_q6"], "score_q6")
        if score > Q6:
            raise EvidenceError("score_q6 exceeds Q6")
        cost = _integer(record["cost_units"], "cost_units", 1)
        key = (task, who)
        if key in cells:
            raise EvidenceError("duplicate participant/task cell")
        cells[key] = (score, cost)
    tasks = sorted({task for task, _ in cells})
    if any((task, who) not in cells for task in tasks for who in (candidate, baseline)):
        raise EvidenceError("unpaired tasks: missing candidate or baseline")
    differences = [cells[(task, candidate)][0] - cells[(task, baseline)][0] for task in tasks]
    candidate_cost = sum(cells[(task, candidate)][1] for task in tasks)
    baseline_cost = sum(cells[(task, baseline)][1] for task in tasks)
    wins = sum(d > 0 for d in differences)
    losses = sum(d < 0 for d in differences)
    canonical = [{"task_id": task, "candidate": cells[(task, candidate)], "baseline": cells[(task, baseline)]} for task in tasks]
    fingerprint = hashlib.sha256(json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return {
        "candidate": candidate, "baseline": baseline, "pairs": len(tasks),
        "wins": wins, "ties": len(tasks) - wins - losses, "losses": losses,
        "mean_score_delta_q6": _round_half_even(Fraction(sum(differences), len(tasks))),
        "candidate_total_cost_units": candidate_cost, "baseline_total_cost_units": baseline_cost,
        "evidence_sha256": fingerprint, "qualification": "NOT_ASSESSED",
    }
