"""Public educational example; not the private SKYNET implementation."""

def valid_transition(before: str, after: str, approved: bool) -> bool:
    edges = {("created", "ready"), ("ready", "running"), ("running", "completed"), ("running", "paused")}
    return approved and (before, after) in edges
