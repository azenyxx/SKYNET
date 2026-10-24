"""Public educational example; not the private SKYNET implementation."""

def next_status(current: str, event: str) -> str:
    transitions = {("created", "approve"): "ready", ("ready", "start"): "running", ("running", "finish"): "completed"}
    if (current, event) not in transitions:
        raise ValueError("transition not allowed")
    return transitions[(current, event)]
