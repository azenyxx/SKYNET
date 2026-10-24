"""Public example: uncertainty-aware strategy comparison."""
from dataclasses import dataclass

@dataclass(frozen=True)
class Estimate:
    strategy: str
    lower: float
    upper: float

def compare(a: Estimate, b: Estimate) -> str:
    if a.lower > a.upper or b.lower > b.upper:
        return "NOT_QUALIFIED"
    if a.lower > b.upper:
        return a.strategy
    if b.lower > a.upper:
        return b.strategy
    return "INSUFFICIENT_EVIDENCE"
