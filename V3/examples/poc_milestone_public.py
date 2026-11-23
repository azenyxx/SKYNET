"""Minimal public milestone evidence checker; no private SKYNET dependencies."""
from dataclasses import dataclass
from enum import Enum
from typing import Iterable

class Verdict(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    MISSING = "MISSING"

@dataclass(frozen=True)
class Check:
    key: str
    verdict: Verdict
    evidence_digest: str | None = None

REQUIRED_LOOP_CHECKS = (
    "plan_valid", "action_authorized", "feedback_recorded",
    "next_choice_traceable", "state_restored", "independent_replay",
)


def assess(checks: Iterable[Check], required: tuple[str, ...] = REQUIRED_LOOP_CHECKS) -> dict[str, object]:
    if not required or len(required) != len(set(required)) or any(not name for name in required):
        raise ValueError("invalid required check set")
    seen: dict[str, Check] = {}
    for check in checks:
        if not check.key or check.key in seen:
            raise ValueError("missing or duplicate key")
        if not isinstance(check.verdict, Verdict):
            raise ValueError("invalid verdict")
        if check.verdict == Verdict.PASS and (not check.evidence_digest or not check.evidence_digest.strip()):
            raise ValueError("PASS needs evidence digest")
        seen[check.key] = check
    missing = tuple(k for k in required if k not in seen or seen[k].verdict == Verdict.MISSING)
    failed = tuple(k for k in required if k in seen and seen[k].verdict == Verdict.FAIL)
    passed = tuple(k for k in required if k in seen and seen[k].verdict == Verdict.PASS)
    return {"status": "PASS" if not missing and not failed else "NOT_QUALIFIED", "passed": passed, "failed": failed, "missing": missing}


if __name__ == "__main__":
    example = [Check("plan_valid", Verdict.PASS, "illustrative-digest")]
    print(assess(example))
