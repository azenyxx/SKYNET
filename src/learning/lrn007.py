"""Public example: fail-closed learning validation."""
def validate(provenance_independent: bool, regression_clear: bool, unresolved_p1: bool) -> str:
    if unresolved_p1:
        return "POLICY_BLOCKED"
    if not provenance_independent:
        return "REQUIRES_INDEPENDENT_EVIDENCE"
    if not regression_clear:
        return "REGRESSION_BLOCKED"
    return "QUALIFIED_FOR_FURTHER_VALIDATION"
