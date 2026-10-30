# SKYNET — Native Cognitive Intelligence (NCI)

**Public research code · SKYNET v1.1 · NCI-006**

SKYNET is an open research initiative exploring architectures and evaluation methods relevant to artificial superintelligence (ASI). **SKYNET is not a demonstrated AGI or ASI system.** This directory publishes a limited, auditable subset of the Native Cognitive Intelligence (NCI) evaluation work; it does not publish the private cognitive runtime.

## What is included

| File | Purpose |
| --- | --- |
| `eval/eval_planning.py` | Independent planning task generation, reference search, simulation, and evaluation. |
| `eval/eval_learning.py` | Learning evaluation across generated tasks with comparative baselines. |
| `eval/eval_autonomy_adversarial.py` | Autonomy evaluation and adversarial control probes. |
| `tests/nci006/test_nci006_audit.py` | Regression assertions for independently examined NCI behaviors. |

These files are selected from the **NCI-006 evidence package** within the SKYNET v1.1 Final Cognitive Release. They are published without modifying their evaluation logic.

## Research coverage

The NCI work investigates bounded native planning, experience-based learning, autonomous execution, verification of execution evidence, and adversarial evaluation. The published code shows *how selected capabilities are evaluated*; it does not establish general intelligence, broad generalization, or deployment readiness.

## What was demonstrated internally

The source release records a historical **Q1** qualification and reports a **1,142-test passing regression baseline** and **39 adversarial probes**. These are historical project-reported results, **not results reproduced by this public package**. Planning, learning, and autonomy remain bounded; metacognitive capability remains partial. Some trust-boundary and learning limitations were still open at the v1.1 baseline.

## Reproducibility and limitations

The evaluation scripts import private SKYNET runtime packages (`skynet_native_planning`, `skynet_native_learning`, `skynet_native_autonomy`, and other integration components). **They will not execute standalone from this public repository.** No private runtime, model weights, secrets, internal attestations, operational credentials, or full audit evidence are included. Public review can inspect the test logic, task definitions, and evaluation methodology; independent execution requires a compatible runtime made available separately.

The repository's existing top-level license and security policy apply. Security concerns should be reported through the repository's `SECURITY.md` rather than by publishing sensitive details.

## Research status

**NCI-006: evaluation methodology published.** This is a selective public research release, not a certification of SKYNET v1.1 and not a claim of AGI/ASI achievement. Further hardening and independent qualification are ongoing.
