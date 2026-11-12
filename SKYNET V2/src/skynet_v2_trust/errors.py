"""Unified structured errors (V2-000B ERROR-TAXONOMY + V2-000C deltas + V2-001T deltas)."""
from __future__ import annotations

# code -> (severity, retryable, policy). Every code listed here is fail-closed.
CATALOG: dict[str, tuple[str, bool, str]] = {
    "E-SCHEMA-001": ("S2", False, "FAIL_CLOSED"),  # schema violation
    "E-SCHEMA-002": ("S2", False, "FAIL_CLOSED"),  # unknown schema name/major
    "E-SCHEMA-003": ("S2", False, "FAIL_CLOSED"),  # minor unsupported
    "E-SCHEMA-004": ("S1", False, "FAIL_CLOSED"),  # schema binding mismatch
    "E-CANON-001": ("S2", False, "FAIL_CLOSED"),   # unsupported value (float, null, range, non-NFC, control)
    "E-CANON-002": ("S2", False, "FAIL_CLOSED"),   # noncanonical / malformed bytes
    "E-CANON-003": ("S2", False, "FAIL_CLOSED"),   # duplicate key
    "E-CANON-004": ("S1", False, "FAIL_CLOSED"),   # required Unicode version unavailable (V2-001T delta)
    "E-AUTH-001": ("S1", False, "FAIL_CLOSED"),    # authorization denied / quorum not met
    "E-AUTH-002": ("S3", False, "FAIL_CLOSED"),    # authorization expired / outside window / limits
    "E-AUTH-003": ("S1", False, "FAIL_CLOSED"),    # scope exceeded
    "E-AUTH-004": ("S1", False, "FAIL_CLOSED"),    # replay
    "E-AUTH-005": ("S1", False, "FAIL_CLOSED"),    # unknown signer (V2-001T delta)
    "E-AUTH-006": ("S1", False, "FAIL_CLOSED"),    # signer role not permitted (V2-001T delta)
    "E-AUTH-007": ("S1", False, "FAIL_CLOSED"),    # delegation expired (V2-001T delta)
    "E-AUTH-008": ("S1", False, "FAIL_CLOSED"),    # delegation scope insufficient (V2-001T delta)
    "E-TRUST-001": ("S1", False, "FAIL_CLOSED"),   # revoked key
    "E-TRUST-003": ("S1", False, "FAIL_CLOSED"),   # trust-event sequence gap/fork/replay
    "E-TRUST-004": ("S2", True, "FAIL_CLOSED"),    # trusted time unavailable / untrusted
    "E-TRUST-005": ("S1", False, "FAIL_CLOSED"),   # clock rollback
    "E-TRUST-006": ("S2", False, "FAIL_CLOSED"),   # time assertion invalid
    "E-TRUST-007": ("S1", False, "FAIL_CLOSED"),   # role-exclusivity conflict (V2-001T delta)
    "E-TRUST-008": ("S1", False, "FAIL_CLOSED"),   # invalid signature (V2-001T delta)
    "E-EVID-002": ("S1", False, "FAIL_CLOSED"),    # evidence conflicted / claim mismatch
    "E-EVID-003": ("S1", False, "FAIL_CLOSED"),    # required evidence invalid or missing (V2-001T delta)
    "E-INTEG-001": ("S1", False, "FAIL_CLOSED"),   # digest/signature/chain mismatch
    "E-INTEG-002": ("S1", False, "FAIL_CLOSED"),   # torn journal tail (V2-001T delta)
    "E-PERSIST-001": ("S2", True, "FAIL_CLOSED"),  # append failed
    "E-PERSIST-002": ("S1", False, "FAIL_CLOSED"), # stale fencing epoch
    "E-PERSIST-003": ("S2", False, "FAIL_CLOSED"), # lease held; takeover requires operator authorization (V2-001T delta)
    "E-INT-001": ("S2", False, "FAIL_CLOSED"),     # internal / unsupported state
}


class TrustError(Exception):
    """Structured, fail-closed security error."""

    def __init__(self, code: str, detail: str = "") -> None:
        if code not in CATALOG:
            code, detail = "E-INT-001", f"unregistered error code {code!r}: {detail}"
        self.code = code
        self.severity, self.retryable, self.policy = CATALOG[code]
        self.detail = detail
        super().__init__(f"{code}: {detail}")
