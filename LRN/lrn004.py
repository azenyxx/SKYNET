"""Public example: retention regression diagnostics."""
def retention_gate(baseline: float | None, candidate: float | None, tolerance: float = 0.0) -> str:
    if baseline is None or candidate is None:
        return "INSUFFICIENT_EVIDENCE"
    if tolerance < 0:
        raise ValueError("negative tolerance")
    return "REGRESSION_DETECTED" if candidate < baseline - tolerance else "RETENTION_PRESERVED"
