"""Public educational example; not the private SKYNET implementation."""

def qualify(passed: int, errors: int, required: int) -> str:
    if min(passed, errors, required) < 0 or required == 0:
        raise ValueError("invalid counts")
    return "local_pass" if errors == 0 and passed >= required else "partial"
