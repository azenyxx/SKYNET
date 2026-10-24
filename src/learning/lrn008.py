"""Public example: consolidated readiness with no execution authorization."""
from dataclasses import dataclass

@dataclass(frozen=True)
class Readiness:
    stages_present: int
    unresolved_p1: int
    learning_authorized: bool = False
    production_authorized: bool = False

def audit(stages_present: int, unresolved_p1: int) -> Readiness:
    if not 0 <= stages_present <= 8 or unresolved_p1 < 0:
        raise ValueError("invalid inventory")
    return Readiness(stages_present, unresolved_p1)
