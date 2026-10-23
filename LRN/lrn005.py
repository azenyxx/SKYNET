"""Public example: explicit cross-domain capability matching."""
def compatibility(source: frozenset[str], target: frozenset[str]) -> str:
    if not target:
        return "INSUFFICIENT_EVIDENCE"
    if target <= source:
        return "COMPATIBLE_FOR_EVALUATION"
    if source & target:
        return "PARTIALLY_COMPATIBLE"
    return "INCOMPATIBLE"
