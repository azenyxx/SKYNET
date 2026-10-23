"""Public example: bounded advisory strategy selection."""
from dataclasses import dataclass

@dataclass(frozen=True)
class Strategy:
    name: str
    declared_cost: int
    verified: bool

def propose(strategies: tuple[Strategy, ...]) -> str:
    eligible = [s for s in strategies if s.verified and s.declared_cost >= 0]
    if not eligible:
        return "NOT_QUALIFIED"
    return min(eligible, key=lambda s: (s.declared_cost, s.name)).name
