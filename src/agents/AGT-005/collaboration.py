"""Public educational example; not the private SKYNET implementation."""

def assign(agents: dict[str, set[str]], capability: str) -> str | None:
    return next((agent for agent in sorted(agents) if capability in agents[agent]), None)
