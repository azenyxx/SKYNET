# SKYNET — Engineering & ASI-Oriented Research Roadmap

**Cyberdyne Systems** · Public milestones and qualification boundaries  
**Current engineering milestone:** V2.0 final unified functional baseline accepted  
**Next program:** V3 architecture design (not implementation-complete)

SKYNET is an ASI-oriented engineering program. A completed integration or passing regression suite is not evidence of AGI, ASI or superhuman capability. This roadmap separates **delivered engineering work**, **open qualification requirements**, and **future research objectives**.

## V1.0 — Foundation | Completed engineering program

The initial 64-stage program organized cognitive processing (`COG`), agent coordination (`AGT`), learning (`LRN`), bounded improvement (`RSI`), system infrastructure (`SYS`) and validation (`VAL`). It established reusable interfaces, runtime components, tests and evidence workflows.

## V1.1 — Operational and native cognitive integration | Hardened historical baseline

V1.1 provided the operational foundation: scheduler and workers, state and memory, journaled execution, authorization, leases, transport, recovery and security regression. Historical source and evidence archives remain separate from the V2 unified runtime.

## V2.0 — Unified cognitive engineering | Functional baseline accepted

**Final release:** V2-017R7  
**Private baseline SHA-256:** `57c6bc9be4a9c31fbec02a1840f62ed6454aab94f78ad6f92c0aa2cd0b83cdc2`

### Delivered

- Unified V1.1 operational runtime and V2 cognitive execution paths.
- Integrated bounded planning, knowledge, learning, metacognitive controls and supervised agents.
- Connected AGT-001–009 and COG-016 parallel execution to real runtime pathways.
- Added deterministic delegation journaling/replay, recovery checks and fail-closed error handling.
- Preserved authorization, lease fencing, provider isolation and approved vendored provenance.
- Closed identified delegation-recovery and worker-outcome isolation defects.

### Final internal evidence

| Test suite | Reported result |
| --- | ---: |
| V1.1 regression | 1,179 / 1,179 |
| Adversarial | 39 / 39 + 24 / 24 |
| V2 regression | 388 / 388 across 12 groups |
| Unified integration | 76 / 76 |
| Recovery acceptance A01–A22 | 22 / 22 |

These are internal executor results, not third-party qualification. The full private release is not published. See [`V2/README.md`](V2/README.md) for implementation details, public code and limitations.

### Outstanding qualification boundaries

- **R-1:** trusted anchoring required to detect unanchored trailing-record truncation.
- **R-2:** evaluator/participant isolation is not yet qualified.
- **Trust:** TEST-only profile; production trust unqualified.
- **Providers:** external network connectivity not qualified.
- **P2-1:** V2 journal growth after SYS capacity rejection requires bounded resource policy.
- **Capability:** no independently established AGI, ASI or superhuman performance.

## V3 — Autonomous Superintelligence Core | Architecture planning

**Goal:** design and subsequently evaluate components capable of measurable improvement in adaptive reasoning, learning and autonomous problem solving. The program name is aspirational; capabilities must be demonstrated experimentally.

| Workstream | Proposed objective | Required evidence before claiming success |
| --- | --- | --- |
| V3-ARCH | Freeze contracts, threat model, dependencies and acceptance gates | Owner-approved architecture and independent challenge review |
| Adaptive generalization | Transfer to unseen tasks and unexpected perturbations | Held-out evaluations versus strong preregistered baselines |
| Continual learning | Long-term adaptation without destructive forgetting | Retention, transfer and regression measurements |
| Autonomous planning | Robust multi-step replanning under constraints | Reproducible task-success and recovery comparisons |
| Verified improvement | Bounded proposal/test/rollback of self-modifications | Independent before/after evidence; safety and regression gates |
| Cognitive evaluation | Reduce leakage and evaluator interference | Isolated evaluation and external expert review |
| Trust hardening | Address R-1, R-2, provider and resource boundaries | Explicit production-security qualification, separately awarded |

### Proposed V3 stage gates

1. **Architecture baseline:** requirements, interfaces, algorithms and qualification standards defined.
2. **Architecture Challenge Gate:** adversarial design review; resolve critical findings before implementation.
3. **Owner approval:** freeze V3 architecture and authorize bounded implementation tasks.
4. **Engineering qualification:** repeatable functional and security tests, explicit failure cases and provenance.
5. **Capability qualification:** independent benchmarks and external review. `SUPERHUMAN_VERIFIED` is a target only; it is not awarded by passing integration tests.

**Current authorization:** V3 architecture planning. No V3 implementation, production readiness or ASI capability is claimed complete.

## Publication policy

Public code is a selected, audited engineering subset. Private cognitive algorithms, internal trust material and the complete unified runtime are intentionally withheld. Historical baselines remain immutable and separately retained.
