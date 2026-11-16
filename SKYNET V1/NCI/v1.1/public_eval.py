"""Public, standalone illustrative evaluation harness for bounded planning.

This is newly written reference code, NOT SKYNET's private cognitive runtime.
Python 3.10+; standard library only.
"""
from collections import deque
from dataclasses import dataclass
from typing import FrozenSet, Iterable, Mapping, Optional, Tuple

@dataclass(frozen=True)
class Action:
    name: str
    requires: FrozenSet[str]
    adds: FrozenSet[str]
    removes: FrozenSet[str] = frozenset()

def apply(state: FrozenSet[str], action: Action) -> Optional[FrozenSet[str]]:
    if not action.requires <= state:
        return None
    return (state - action.removes) | action.adds

def bounded_plan(start: Iterable[str], goal: Iterable[str], actions: Iterable[Action],
                 forbidden: Iterable[str] = (), max_depth: int = 12,
                 max_states: int = 10000) -> Optional[Tuple[str, ...]]:
    """Shortest safe plan by breadth-first search; None means no plan found WITHIN limits."""
    if max_depth < 0 or max_states < 1:
        raise ValueError("invalid resource limit")
    initial, target, blocked = frozenset(start), frozenset(goal), frozenset(forbidden)
    if initial & blocked:
        return None
    ordered = tuple(sorted(actions, key=lambda a: a.name))
    queue = deque([(initial, ())]); seen = {initial}
    while queue:
        state, path = queue.popleft()
        if target <= state:
            return path
        if len(path) >= max_depth:
            continue
        for action in ordered:
            next_state = apply(state, action)
            if next_state is None or next_state & blocked or next_state in seen:
                continue
            if len(seen) >= max_states:
                return None
            seen.add(next_state)
            queue.append((next_state, path + (action.name,)))
    return None

def demo() -> Mapping[str, object]:
    actions = (
        Action("collect_key", frozenset({"at_start"}), frozenset({"has_key"})),
        Action("open_door", frozenset({"has_key"}), frozenset({"door_open"})),
        Action("enter", frozenset({"door_open"}), frozenset({"at_goal"})),
        Action("unsafe_shortcut", frozenset({"at_start"}), frozenset({"at_goal", "unsafe"})),
    )
    plan = bounded_plan({"at_start"}, {"at_goal"}, actions, forbidden={"unsafe"})
    return {"reference_plan": list(plan) if plan is not None else None,
            "safe": plan is not None and "unsafe_shortcut" not in plan,
            "note": "Public illustrative benchmark, not SKYNET runtime evidence"}

if __name__ == "__main__":
    import json
    print(json.dumps(demo(), indent=2))
