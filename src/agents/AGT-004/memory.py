"""Public educational example; not the private SKYNET implementation."""

def summarize(events: tuple[tuple[str, str], ...]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for kind, _ in events:
        counts[kind] = counts.get(kind, 0) + 1
    return counts
