"""Public educational example; not the private SKYNET implementation."""

def progress(completed: int, total: int) -> float:
    if total <= 0 or not 0 <= completed <= total:
        raise ValueError("invalid progress")
    return completed / total
