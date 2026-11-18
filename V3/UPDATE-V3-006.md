# SKYNET V3 — Public Research Update 006

**Date:** 2026-11-18  
**Track:** P2 — Cognitive Benchmark & Qualification  
**Focus:** Statistical recovery, paired evaluation, reproducible research reporting  
**Status:** Research milestone; P2 not yet accepted

## Engineering work

The P2 research program completed a bounded recovery pass on its existing four-arm L3 method-learning pilot. A schema mismatch in the analysis tooling was resolved without repeating the experimental evaluations or modifying the underlying recorded outcomes. A separate, versioned comparison of observed behaviour was introduced to avoid mistaking arm-specific metadata for an execution difference.

This update publishes only an **independent, small statistical teaching example**, not the internal analysis implementation, cognitive core, method library, synthesis pipeline, snapshots, or evaluation datasets.

## Reported research outcomes

| Measure | Development/validation result |
|---|---|
| Validation tasks | 52 tasks per arm, 4 arms (208 records) |
| Tasks eligible for paired local-repair analysis | 29 |
| C versus B local-repair outcomes | 17 both successful; 12 neither successful; 0 discordant |
| Exact two-sided McNemar | p = 1.0 |
| Final goal satisfaction | 40/52 in each arm |
| Replan solver calls | Baseline A: 31; candidates B/C/D: 71 each |
| Selected synthesized method | None |
| Synthesized method use in validation | 0 |
| L3 qualification | **NOT QUALIFIED** |

For zero observed disagreements, a **Wilson 95% interval on the disagreement probability** is approximately [0, 0.117]. It is **not** a confidence interval for the paired success-rate difference and does not establish algorithmic equivalence. The preregistered percentile bootstrap for the paired difference was degenerate at [0, 0]; it likewise does not prove zero uncertainty.

These are **exploratory pilot findings**, not evidence that SKYNET has achieved autonomous learning, AGI, or ASI. Previously reported L1/L2 results concern limited snapshot reproducibility and persistence only. L4–L6 remain unqualified. Held-out evaluation was not performed.

## Public verification example

The included standard-library Python module implements four general statistical utilities using **no internal SKYNET imports**:

- Matching paired boolean outcomes by task ID.
- Exact two-sided McNemar test.
- Wilson interval for a binomial disagreement rate.
- Holm multiple-comparison adjustment.

From the repository root:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s V3/tests -p 'test_paired_research_stats.py' -v
```

The accompanying test suite verifies ordinary and edge cases using synthetic fixtures. These public tests are **not** the private P2 regression suite, and passing them does not independently reproduce the reported SKYNET pilot.

## Disclosure boundary

No private P1/P2 source code, method ASTs, CML programs, agent algorithms, internal logs, raw task IDs, hidden evaluation sets, training snapshots, credentials, or cumulative checkpoint archives are included. This public example is independently authored for demonstration and inspection.

**Next:** P2 qualification matrix, reproducibility evidence index, independent review and Owner decision before P3 Adaptive Planning.
