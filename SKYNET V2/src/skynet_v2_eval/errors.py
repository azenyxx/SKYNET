"""Evaluation error codes. Extends (does not modify) the V2-001T catalogue; codes follow V2-000B/C taxonomy."""
from __future__ import annotations

from skynet_v2_trust.errors import CATALOG as TRUST_CATALOG
from skynet_v2_trust.errors import TrustError

EVAL_CATALOG: dict[str, tuple[str, bool, str]] = {
    "E-EVAL-001": ("S1", False, "FAIL_CLOSED"),  # missing independent attestation / certification not permitted
    "E-EVAL-002": ("S1", False, "FAIL_CLOSED"),  # frozen protocol modification / version conflict
    "E-EVAL-003": ("S1", False, "FAIL_CLOSED"),  # committed result replacement (append-only)
    "E-EVAL-010": ("S1", False, "FAIL_CLOSED"),  # evaluator-only / sealed information requested (leakage attempt)
    "E-EVAL-011": ("S1", False, "FAIL_CLOSED"),  # role/permission denied or cross-participant access
    "E-EVAL-020": ("S1", False, "FAIL_CLOSED"),  # prohibited claim (self-granted SUPERHUMAN_VERIFIED / ASI)
    "E-EVAL-021": ("S1", False, "FAIL_CLOSED"),  # promotion of internal/exploratory evidence to confirmatory
    "E-EVAL-030": ("S1", False, "FAIL_CLOSED"),  # reference integrity (cost below proven lower bound, missing ref)
    "E-EVAL-040": ("S2", False, "FAIL_CLOSED"),  # protocol / task / fixture invalid
    "E-EVAL-050": ("S2", False, "FAIL_CLOSED"),  # analysis method or threshold PENDING_APPROVAL for confirmatory use
    "E-EVAL-060": ("S2", True, "FAIL_CLOSED"),   # participant runner failure (process, timeout, protocol)
    "E-EVAL-070": ("S1", False, "FAIL_CLOSED"),  # illegal qualification state transition
}
assert not set(EVAL_CATALOG) & set(TRUST_CATALOG)


class EvalError(TrustError):
    def __init__(self, code: str, detail: str = "") -> None:
        cat = EVAL_CATALOG if code in EVAL_CATALOG else TRUST_CATALOG
        if code not in cat:
            code, detail, cat = "E-INT-001", f"unregistered error code {code!r}: {detail}", TRUST_CATALOG
        self.code, self.detail = code, detail
        self.severity, self.retryable, self.policy = cat[code]
        Exception.__init__(self, f"{code}: {detail}")
