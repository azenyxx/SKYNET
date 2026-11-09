# SKYNET V3 — Capability-Driven Roadmap

**Program:** Autonomous Superintelligence Core  
**Public status:** Architecture planning; all V3 implementation and intelligence qualification milestones are pending.

The roadmap is organized around **observable capabilities and evidence**, not the number of modules shipped. The sequence may change after architecture challenge and owner approval.

| Stage | Planned deliverable | Evidence gate | Status |
| --- | --- | --- | --- |
| **V3-ARCH-001** | Executable architecture proposal, contracts, V2 compatibility, threat model, evaluation plan | Independent architecture challenge and owner sign-off | **In design** |
| **V3-001 — Intelligence Engine** | Reasoning, hypothesis generation, tool-mediated discovery, verification and metacognitive control | Unseen-task benchmark against strong baselines; ablations showing SKYNET contribution | Planned |
| **V3-002 — Autonomous Learning** | Persistent, controlled learning across episodes and restarts | Retention, forward transfer, forgetting and rollback tests | Planned |
| **V3-003 — Novel Problem Solving** | End-to-end unfamiliar-problem solving with constraint handling and replanning | Hidden tasks, reproducible solution verification and failure analysis | Planned |
| **V3-004 — Recursive Improvement** | Isolated proposal, evaluation, acceptance/rejection and rollback of method improvements | Independent before/after measurements; no safety or regression deterioration | Planned |
| **V3-005 — Superhuman Competition** | Competitive evaluation in a clearly defined challenging domain | Fair compute/time/cost budgets, frontier AI and specialist algorithm baselines, qualified human comparison where appropriate | Planned |
| **V3-006 — Independent Qualification** | External review and reproducibility package | Held-out tasks, evaluator isolation, leakage controls and independent replication | Planned |

## Qualification principles

- **No benchmark leakage:** separate training, validation and hidden evaluation; control exposure and preregister comparison rules.
- **Fair comparisons:** report both equal-budget and practically relevant maximum-budget results, with costs and uncertainty.
- **No cherry-picking:** publish task selection rules, failure rates, negative results, and ablations where disclosure is safe.
- **Independent evidence:** implementation tests do not automatically establish cognitive superiority; a separate evaluator must reproduce any superhuman claim.
- **Persistent learning:** distinguish useful retained adaptation from merely growing a memory store or repeatedly querying a frontier model.
- **Safe improvement:** isolated trials, explicit acceptance criteria, rollback, owner-held authority, and no unilateral modification of security controls.

## Proposed evidence levels

| Level | Qualification target | Current status |
| --- | --- | --- |
| I | Verified cognitive capability on unseen tasks with retained learning | Not awarded |
| II | Sustained, independently verified superhuman capability in a defined domain | Not awarded |
| III | Broad cross-domain superintelligence evidence, transfer and verified improvement | Not awarded |

**Program ambition:** earn Level II and establish initial Level III evidence through independent testing. No claim of full ASI is made.

## Dependencies and known V2 boundaries

The accepted V2 functional baseline is a foundation, not a production security or intelligence certification. V3 qualification must address evaluator/participant isolation (R-2), externally anchored journal rollback detection (R-1), bounded journal/resource growth (P2-1), and production provider/trust boundaries. These are independent engineering gates, not substitutes for cognitive evaluation.

**Related:** [V3 vision](README.md) · [Repository-wide roadmap](../ROADMAP.md)
