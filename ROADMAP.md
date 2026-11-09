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

**Mission:** build and independently evaluate operational intelligence that can solve unfamiliar problems, learn persistently, generalize across domains, and improve its own problem-solving methods under bounded authority. This is a future capability target, not an achieved ASI claim.

| Stage | Objective | Evidence required | Status |
| --- | --- | --- | --- |
| **V3-ARCH-001** | Architecture, contracts, V2 integration, threat model and evaluation protocol | Independent challenge and owner approval | In design |
| **V3-001 — Intelligence Engine** | Autonomous reasoning, discovery and verification | Hidden-task baselines and ablation studies | Planned |
| **V3-002 — Autonomous Learning** | Persistent validated learning | Retention, transfer, forgetting and regression tests | Planned |
| **V3-003 — Novel Problem Solving** | End-to-end solutions to unfamiliar tasks | Reproducible held-out task success | Planned |
| **V3-004 — Recursive Improvement** | Bounded proposal/test/rollback of method changes | Independent gains without safety regressions | Planned |
| **V3-005 — Superhuman Competition** | Competitive domain-level evaluation | Frontier AI, specialist algorithms and expert comparisons with fair budgets | Planned |
| **V3-006 — Independent Qualification** | External reproducibility and capability review | Isolated evaluator, leakage controls and independent replication | Planned |

### Evidence targets

- **Level I — Verified Cognitive Capability:** unseen-task solving, learning and retention.
- **Level II — Verified Superhuman Domain Capability:** sustained independently verified advantage in a defined complex domain.
- **Level III — Broad Superintelligence Evidence:** sustained advantages across distinct domains, transfer and verified improvement; not a universal ASI certificate.

**V3 objective:** earn Level II and initial Level III evidence. No levels are currently awarded. Security and operational qualifications remain separate from intelligence qualification.

**Current authorization:** architecture design only. Implementation begins only after independent Architecture Challenge Gate and owner approval.

**Read:** [V3 mission](V3/README.md) · [Detailed capability roadmap](V3/CAPABILITY_ROADMAP.md)

## Publication policy

Public code is a selected, audited engineering subset. Private cognitive algorithms, internal trust material and the complete unified runtime are intentionally withheld. Historical baselines remain immutable and separately retained.
