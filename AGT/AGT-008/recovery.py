"""Public educational example; not the private SKYNET implementation."""

def recovery_advice(status: str, uncertain: bool) -> str:
    if uncertain:
        return "escalate_to_host"
    if status == "failed":
        return "request_host_review"
    return "no_action"
