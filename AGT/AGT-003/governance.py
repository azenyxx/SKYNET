"""Public educational example; not the private SKYNET implementation."""

def authorize(requested: set[str], allowed: set[str], stopped: bool = False) -> bool:
    return not stopped and requested <= allowed
