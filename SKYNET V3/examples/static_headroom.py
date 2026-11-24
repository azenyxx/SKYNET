"""Public demonstration: per-task oracle versus best fixed policy.

Inputs are synthetic or externally supplied boolean local-repair outcomes.
This is not a SKYNET engine or qualification implementation.
"""
from collections.abc import Mapping, Sequence


def static_headroom(outcomes: Mapping[str, Sequence[bool]]) -> dict[str, object]:
    """Return counts for the best fixed strategy and the per-task oracle.

    Every policy must have one strict boolean outcome per identical task.
    No arbitrary tie-breaking using observed rewards is needed for the count.
    """
    if not outcomes:
        raise ValueError("at least one policy required")
    names = list(outcomes)
    if any(not isinstance(name, str) or not name for name in names):
        raise ValueError("policy names must be nonempty strings")
    lengths = [len(outcomes[name]) for name in names]
    if not lengths or lengths[0] == 0 or len(set(lengths)) != 1:
        raise ValueError("policies must evaluate identical nonempty task sets")
    for values in outcomes.values():
        if any(type(value) is not bool for value in values):
            raise ValueError("all outcomes must be booleans")
    totals = {name: sum(outcomes[name]) for name in names}
    best = max(totals.values())
    oracle = sum(any(outcomes[name][i] for name in names) for i in range(lengths[0]))
    return {"tasks": lengths[0], "best_fixed_successes": best,
            "oracle_successes": oracle, "headroom_tasks": oracle-best,
            "best_fixed_policies": tuple(sorted(k for k, v in totals.items() if v == best))}
