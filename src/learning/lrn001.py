"""Public example: evidence intake and eligibility."""
from dataclasses import dataclass

@dataclass(frozen=True)
class Experience:
    identifier: str
    outcome: str
    verified: bool

def assess(item: Experience) -> str:
    if not item.identifier or item.outcome not in {"success", "failure"}:
        return "REJECTED"
    return "ELIGIBLE_FOR_EVALUATION" if item.verified else "REQUIRES_VERIFICATION"
