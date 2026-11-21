"""Public-only diagnostic: validate paired replanning-state evidence.

This illustrates an evidence contract, NOT real SKYNET instrumentation.
"""
from collections.abc import Mapping, Sequence


def comparison_eligible(feasibility: str, captures: Mapping[str, Sequence[str]],
                        outcomes: Mapping[str, bool]) -> tuple[bool, str]:
    """Return (eligible, reason), fail-closed on missing or ambiguous evidence.

    captures maps policy IDs to 1-element sequences of replanning-state digests.
    outcomes maps the same policy IDs to strict boolean repair outcomes.
    """
    if feasibility not in ("FEASIBLE", "INFEASIBLE", "UNKNOWN", "INVALID"):
        raise ValueError("unsupported feasibility classification")
    if feasibility != "FEASIBLE":
        return False, "CONTINUATION_NOT_VERIFIED"
    if not captures or not outcomes or set(captures) != set(outcomes):
        return False, "POLICY_SET_MISMATCH"
    for policy, states in captures.items():
        if not isinstance(policy, str) or not policy:
            raise ValueError("invalid policy name")
        if (isinstance(states, (str, bytes)) or len(states) != 1
                or not isinstance(states[0], str) or not states[0]):
            return False, "MISSING_OR_AMBIGUOUS_STATE"
    if any(type(value) is not bool for value in outcomes.values()):
        return False, "INVALID_OUTCOME"
    if len({states[0] for states in captures.values()}) != 1:
        return False, "STATE_MISMATCH"
    return True, "ELIGIBLE"
