# SKYNET V3 — Research Status and Evidence Boundaries

**As of:** 24 November 2026  
**Classification:** Public summary of internal research  
**Program:** P2 — ACTIVE; full qualification pending

## What the internal prototype can do

Within bounded scheduling/planning environments it can create plans, execute under policy constraints, respond to resource perturbations, attempt replanning, validate outcomes, produce reproducible evidence and restore persistent state. Experimental mechanisms can synthesize candidate methods and update strategy evaluations using feedback.

The complete private runtime is not published in this repository.

## Evidence table

| Finding | Reported result | Limit |
| --- | --- | --- |
| L1 reproducibility | **24/24** matching results | Limited independent-process semantic evaluation |
| Cross-process state persistence | Internally tested | Does not prove learned experience improves future success |
| Planning pilot | **40/52** successes | Fixed baseline and experimental arms tied on task success |
| Candidate method generation | **16** new AST forms | New useful skills were not established |
| Feedback-conditioned behavior | Method selection changed after unsuccessful action and negative reward in a bounded pilot | Single controlled demonstration is not statistical superiority |
| Neighborhood static headroom | **0/38** improvements in historical tested space | Does not preclude headroom in a different configuration space |
| Current P2 internal regression tests (Session 22) | **140/140** PASS as reported | Not an independent security audit or public test result |

The negative headroom result is important: an adaptive selector cannot outperform a strong fixed configuration if available strategies have no exploitable task-specific differences. A new precondition study is planned to measure that possibility in an extended configuration space.

## Formal qualification

| Gate | Status |
| --- | --- |
| L1 | Limited internal evidence |
| L2 | Limited internal evidence |
| L3 — behavioral improvement | **NOT QUALIFIED** |
| L4 — transfer | **NOT QUALIFIED** |
| L5 — statistical qualification | **NOT QUALIFIED** |
| L6 — safe improvement | **NOT QUALIFIED** |
| Security 002B | **OPEN** |
| Held-out | **SEALED** |
| P3 | **NOT AUTHORIZED** |

## Next verifiable milestone

1. Freeze a defensible headroom protocol before running the static R1 study.
2. Evaluate whether at least two supported strategies create measurable task-conditioned opportunities to outperform a fixed configuration.
3. Only if positive, test an adaptive selector against fixed, memory-ablated and shuffled controls.
4. Independently demonstrate and replay a bounded end-to-end cognitive-loop trace, explicitly separating feedback-conditioned behavior from proven learning.

**Claim boundary:** SKYNET is ASI-*oriented*, not an achieved ASI/AGI. Technical controls, test counts and prototype integration are important engineering milestones but do not establish general intelligence or ongoing self-improvement.
