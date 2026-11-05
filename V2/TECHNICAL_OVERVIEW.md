# SKYNET V2.0 — Public Architecture Overview

This is a conceptual overview, not an implementation specification.

```text
Validated task → bounded cognitive planning → trust/authorization gate
      ↓                       ↓                      ↓
  task context          metacognitive checks     verified execution
      └───────────────────────┬──────────────────────┘
                              ↓
                 outcome verification and journal
                              ↓
                  durable scoped learning/memory
                              ↓
                guarded reuse or controller fallback
                              ↓
               bounded improvement proposal lifecycle
          observe → diagnose → propose → validate → evaluate
          → authorize → activate → monitor → retain/rollback
```

A proposed improvement can alter only a bounded guard parameter under the existing contract. Authorization uses Owner approval and a trusted capability boundary; the private engineering tests use disposable TEST keys. No self-editing of code, root keys or trust policy is authorized.

**Qualification boundary:** not every arrow was exercised end-to-end on qualifying real data. The real improvement candidate was rejected; activation and rollback are fixture-tested only.


# SKYNET V2.0 — Capability Matrix (Public Summary)

Status reflects evidence reported in the private V2-016 capability matrix.

| Capability | Status |
|---|---|
| Cognitive task representation | IMPLEMENTED_AND_TESTED |
| Bounded planning | IMPLEMENTED_AND_TESTED |
| Trusted action execution | IMPLEMENTED_AND_TESTED |
| Observation and outcome verification | IMPLEMENTED_AND_TESTED |
| Cognitive orchestration | IMPLEMENTED_AND_TESTED |
| Metacognitive monitoring | IMPLEMENTED_AND_TESTED |
| Durable experience and memory | IMPLEMENTED_AND_TESTED |
| Learning eligibility and scoped rule application | IMPLEMENTED_AND_TESTED |
| Distribution-shift response | IMPLEMENTED_NOT_QUALIFIED |
| Rule invalidation and fallback | IMPLEMENTED_AND_TESTED |
| Controlled improvement proposal | IMPLEMENTED_AND_TESTED |
| Candidate validation and rejection | IMPLEMENTED_AND_TESTED |
| Owner-authorized activation | IMPLEMENTED_NOT_QUALIFIED (fixture only) |
| Monitoring and rollback | IMPLEMENTED_NOT_QUALIFIED (fixture only) |
| Journal recovery and deterministic replay | IMPLEMENTED_AND_TESTED |
| Evidence provenance and integrity | IMPLEMENTED_AND_TESTED |
| Trust and governance enforcement | IMPLEMENTED_AND_TESTED |
| Permitted cross-domain transfer | BLOCKED_BY_CONTRACT |
| Registration of induced knowledge | BLOCKED (frozen KnowledgeState@1.0) |

**Counting note:** this table enumerates 19 individually listed capabilities. The private release summary groups some capabilities together and reports 13 implemented/tested, 3 implemented/not-qualified, and 2 blocked; those aggregate counts use grouped categories. This table retains the more granular source classifications rather than silently forcing a total.


# SKYNET V2.0 — Security Evidence and Boundaries

The V2-016 executor reported 12 targeted adversarial checks, all rejected or enforced: unauthorized activation, approval replay, expiry, digest substitution, cross-domain rule misuse, tampered evidence, corrupted journals, rollback/reactivation, budget bypass, canonicalization ambiguity, protected-policy mutation, and evaluation contamination.

The private test suite also exercised quorum, revocation, writer fencing, trusted time, canonical evidence and fail-closed behaviour. These are **engineering test results**, not a third-party security certification.

**Open trust limitations:** (R-1) whole-journal rollback is not detectable without an external monotonic reference; (R-2) evaluator and participant share a process/Unix user in the test setup. The Owner root key is intended to remain outside the runtime; tests used disposable TEST keys.

This public subset deliberately excludes security-sensitive internals, privileged code, internal journals, keys, and detailed private test fixtures. Please do not treat the public documents as a deployment security guarantee.


# Public Release Scope and Provenance

This package is intentionally curated from a larger private cumulative SKYNET V2-016 engineering release. **It does not contain the cognitive runtime.** It includes public-facing engineering summaries and a small independent manifest-checking utility. The private release SHA-256 is published as a provenance identifier only; the original archive remains private.

The public tool verifies checksums of this curated package; it does not validate the private engineering test claims. No internal source files, raw evidence, cryptographic key material, internal policies, or executable privileged components are published.

Before publishing, review `git status`, staged changes and the GitHub remote; Git history may retain previously published material even after removing it from the current branch.
