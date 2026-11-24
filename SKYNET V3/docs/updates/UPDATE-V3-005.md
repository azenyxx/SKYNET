# SKYNET V3 — Public Engineering Update (through V3-005)

**Cyberdyne Systems · 14 November 2026**

SKYNET is being developed toward the full engineering realization of Artificial Superintelligence (ASI). Current milestones build and test bounded cognitive mechanisms with reproducible evidence.

## Development results

- **V3-004:** Independent T2 verification distinguishes specification-declared constraints from realized environment conditions. A sealed observation exposed a precedence-lag violation that the original-spec verification did not capture. A source-learned method was actually executed on one of three held-out target instances; matched outcomes showed **0 wins, 3 ties, 0 losses**.
- **V3-005:** Typed `kind_eq` parameterization allowed a source method from F5 to bind to a `precedence` constraint in F3 and execute in a held-out replan, without hardcoded target variable names. The focused development suite reported **19 PASS / 0 FAIL / 0 ERROR**.
- **Adaptive recovery:** A bounded recovery attempt was executed after a sealed realized-lag failure. T2 remained `GOAL_FAILED`; recovery and cognitive advantage were **not demonstrated**. The matched single-instance comparison showed **0 wins, 1 tie, 0 losses**.
- **Knowledge integrity:** Canonical persistence round-trip and rejection of malformed, tampered, foreign-schema and trust-claiming records were demonstrated in the private development evaluation.

## Included public code and tests

This update publishes the **unchanged** V3 canonical JSON and typed-error primitives from the V3-005 cumulative baseline, together with public verification tests. Run:

```bash
cd V3
PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_public_*.py' -v
```

These public smoke tests cover canonical ordering, stable hashing, strict JSON rejection, nesting bounds and typed errors. They **do not reproduce** the private cognitive, transfer, recovery or benchmark experiments. Those require nonpublic coordinator logic, fixtures and sealed observations.

## Current engineering focus

V3-006 investigates constraint-aware repair: diagnosing realized-state failures, generating bounded corrective candidates and re-verifying outcomes through independent T2, compared with a strong solver baseline. **V3-006 results are not included in this update.**

The project's goal is the full engineering realization of ASI, with technical progress established through measurable, independently interpretable experiments.
