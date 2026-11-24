"""Public illustrative Cognitive PoC budget validation; no internal SKYNET imports."""
from collections import Counter
from dataclasses import dataclass
from typing import Mapping

CATEGORIES = ("research", "infrastructure", "reviews_reserve")

@dataclass(frozen=True)
class BudgetItem:
    name: str
    category: str
    usd: int

@dataclass(frozen=True)
class Scenario:
    name: str
    months: int
    target_usd: int
    items: tuple[BudgetItem, ...]


def verify(scenario: Scenario) -> dict[str, int]:
    if not scenario.name or not isinstance(scenario.months, int) or isinstance(scenario.months, bool) or scenario.months <= 0:
        raise ValueError("invalid scenario identity or duration")
    if type(scenario.target_usd) is not int or scenario.target_usd <= 0:
        raise ValueError("invalid target")
    names = [item.name for item in scenario.items]
    if not names or any(not n or not n.strip() for n in names) or len(names) != len(set(names)):
        raise ValueError("missing/duplicate line item")
    totals = dict.fromkeys(CATEGORIES, 0)
    for item in scenario.items:
        if item.category not in totals or type(item.usd) is not int or item.usd < 0:
            raise ValueError("invalid expense")
        totals[item.category] += item.usd
    if sum(totals.values()) != scenario.target_usd:
        raise ValueError("budget does not reconcile")
    return totals


def _make(name: str, months: int, target: int, research: tuple[int, ...], infra: tuple[int, ...], reviews: tuple[int, ...]) -> Scenario:
    rows = []
    for cat, values in zip(CATEGORIES, (research, infra, reviews)):
        rows.extend(BudgetItem(f"{cat}-{i}", cat, usd) for i, usd in enumerate(values, 1))
    return Scenario(name, months, target, tuple(rows))

SCENARIOS: Mapping[str, Scenario] = {
    "lean": _make("Lean", 3, 140_000, (36_000, 27_000, 21_000), (6_000, 8_000, 4_000), (12_000, 8_000, 18_000)),
    "base": _make("Base", 4, 320_000, (64_000, 96_000, 40_000), (12_000, 18_000, 10_000), (25_000, 15_000, 40_000)),
    "extended": _make("Extended", 6, 550_000, (108_000, 156_000, 72_000), (22_000, 45_000, 18_000), (45_000, 30_000, 54_000)),
}

if __name__ == "__main__":
    for scenario in SCENARIOS.values():
        print(f"{scenario.name}: ${sum(verify(scenario).values()):,} / {scenario.months} months")
