# SKYNET — Learning & Adaptation (LRN)

Public educational/reference implementations of eight concepts from the SKYNET LRN research series. **This directory is newly authored demonstration code, not a copy or release of the private SKYNET implementation.** It contains no production connectors, model weights, proprietary datasets, private evidence, deployment configuration, or authorization mechanisms.

## Modules

| Stage | Public demonstration |
|---|---|
| LRN-001 | Experience assessment and evidence eligibility |
| LRN-002 | Deterministic selection and replay ordering (no execution) |
| LRN-003 | Advisory strategy choice using declared costs |
| LRN-004 | Baseline/retention regression comparison |
| LRN-005 | Explicit cross-domain capability compatibility |
| LRN-006 | Strategy comparison using uncertainty intervals |
| LRN-007 | Fail-closed validation gates |
| LRN-008 | Readiness inventory with disabled authorizations |

## Run tests

Python 3.10+; no runtime dependencies. With pytest installed, from repository root:

```bash
python3 -m pytest -q LRN/tests
```

Alternatively, no third-party test runner is needed:

```bash
python3 LRN/run_tests.py
```

## SKYNET research status (2026-10)

The private LRN-001–008 research implementation has eight reported stages, covering evidence intake, diagnostic replay, strategy evaluation, retention diagnostics, transfer eligibility, meta-strategy assessment, validation, and qualification inventory. Its reported status is **CLOSED PARTIAL**. Historical internal test reports list **270 passing tests** across the stages; those are **not independently reproduced by this public package**. There are at least **26 tracked P1/P2 findings**, including provenance and measurement gaps. Full AGT/COG inherited findings are not consolidated here.

**Not established:** independently verified source provenance, real-world learning effectiveness, autonomous training, reliable cross-domain generalization, durable replay guarantees, or production readiness. The internal architecture's learning/model/policy/production authorizations remain disabled. These demo modules must not be used as security or production controls.

## Disclosure boundary

This public subset intentionally excludes private source, original release archives, full test evidence, security findings details, internal policies and infrastructure. For provenance and disclosure questions, see `PUBLIC-SCOPE.md`.
