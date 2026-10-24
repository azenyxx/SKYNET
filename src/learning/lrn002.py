"""Public example: deterministic, non-executing evidence replay."""
from dataclasses import dataclass

@dataclass(frozen=True)
class ReplayItem:
    identifier: str
    sequence: int
    verified: bool

def select(items: tuple[ReplayItem, ...], limit: int) -> tuple[ReplayItem, ...]:
    if limit < 0:
        raise ValueError("negative limit")
    unique = {item.identifier: item for item in items}
    if len(unique) != len(items):
        raise ValueError("duplicate identifier")
    return tuple(sorted(unique.values(), key=lambda x: (x.sequence, x.identifier))[:limit])
