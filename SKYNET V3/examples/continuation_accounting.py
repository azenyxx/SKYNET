"""Public, standalone example of conservative experiment accounting.

Not SKYNET internal source code. No runtime, optimizer, or cognitive algorithms.
Uses Python's standard library only.
"""
from collections import Counter
from dataclasses import dataclass
from typing import Iterable

ALLOWED = frozenset({"feasible", "infeasible", "unknown", "no_replan", "invalid"})


@dataclass(frozen=True)
class TaskObservation:
    task_id: str
    feasibility: str
    strategy_states_match: bool = False
    outcomes: tuple[bool, ...] = ()


def summarize(observations: Iterable[TaskObservation]) -> dict[str, object]:
    """Count feasibility, eligibility and sensitivity without guessing missing data.

    Eligibility requires verified continuation feasibility, a verified match of
    starting states across compared strategies, and >=2 observed repair outcomes.
    """
    counts: Counter[str] = Counter()
    seen: set[str] = set()
    eligible = sensitive = 0
    for row in observations:
        if not isinstance(row, TaskObservation):
            raise TypeError("expected TaskObservation")
        if not isinstance(row.task_id, str) or not row.task_id:
            raise ValueError("missing task id")
        if row.task_id in seen:
            raise ValueError("duplicate task id")
        seen.add(row.task_id)
        if row.feasibility not in ALLOWED:
            raise ValueError("unsupported feasibility classification")
        if type(row.strategy_states_match) is not bool:
            raise TypeError("state agreement must be boolean")
        if type(row.outcomes) is not tuple or any(type(x) is not bool for x in row.outcomes):
            raise TypeError("outcomes must be a tuple of booleans")
        counts[row.feasibility] += 1
        if (row.feasibility == "feasible" and row.strategy_states_match
                and len(row.outcomes) >= 2):
            eligible += 1
            sensitive += len(set(row.outcomes)) > 1
    return {
        "total": len(seen),
        "by_feasibility": {name: counts[name] for name in sorted(ALLOWED)},
        "repair_eligible": eligible,
        "method_sensitive": sensitive,
        "verdict": "NOT_EVALUABLE" if eligible == 0 else "DESCRIPTIVE_ONLY",
    }
