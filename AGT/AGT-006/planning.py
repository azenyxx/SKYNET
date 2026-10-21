"""Public educational example; not the private SKYNET implementation."""

def plan_order(tasks: dict[str, tuple[str, ...]]) -> list[str]:
    pending = set(tasks)
    result: list[str] = []
    while pending:
        ready = sorted(k for k in pending if set(tasks[k]) <= set(result))
        if not ready:
            raise ValueError("cycle or missing dependency")
        result.extend(ready)
        pending.difference_update(ready)
    return result
