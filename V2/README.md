# SKYNET V2.0 — Public Engineering Release

**Cyberdyne Systems | SKYNET | ASI-oriented cognitive system**

**Status:** `ENGINEERING_COMPLETE_WITH_LIMITATIONS`  
**Final acceptance:** `FINAL_ACCEPTANCE_PENDING` (V1.1 parity comparison and independent review)  
**Superhuman performance:** `SUPERHUMAN_NOT_EVALUATED`  
**Statistical superiority:** `NOT_ESTABLISHED`

This directory is a **curated public disclosure** of the SKYNET V2.0 engineering results. It is **not** the complete SKYNET runtime, a runnable cognitive system, or an independent certification. Internal source, private tests, detailed evidence, credentials, and privileged implementation are not included.

## What was built

The private V2.0 engineering release integrates bounded cognitive task processing and planning, trusted execution and outcome verification, metacognitive monitoring, durable experience and learning, scoped rule application, journal replay, and a constrained improvement proposal/validation/authorization mechanism. See [TECHNICAL_OVERVIEW.md](TECHNICAL_OVERVIEW.md) for architecture and capability boundaries.

## Reported results

- **388/388** tests passed in **12** groups in the V2-016 engineering regression (Python 3.12.3, Linux); results are reported by the project executor, not independently reproduced in this public package.
- **12/12** targeted adversarial security checks were enforced or rejected in that regression.
- **V2-015-R1:** a real evidence-derived improvement candidate was **rejected** because it added post-shift harm without reducing false abstentions. No safe candidate was activated on real data.
- **V2-014:** the post-shift evaluation reported a utility decrease of approximately **0.083**, and shift detection did not suspend the rule within 25 tasks.

## Public resources

- [TECHNICAL_OVERVIEW.md](TECHNICAL_OVERVIEW.md) — architecture, capabilities and security boundary
- [RELEASE_NOTES.md](RELEASE_NOTES.md) — results, limitations and roadmap
- `examples/canonical_metrics.py` — standalone public reference example of integer-only metric encoding and digesting; **not** production SKYNET code
- `tests/test_canonical_metrics.py` — executable tests of the public example
- `tools/verify_public_manifest.py` — package integrity verifier

## Try the public example

```bash
python3 -m unittest discover -s V2/tests -v
python3 V2/tools/verify_public_manifest.py
```

These tests validate **only the public example**. They do not reproduce the private V2 regression or prove cognitive performance.

## Provenance and disclosure

The private source release is `SKYNET-V2-016-FINAL-CONSOLIDATED-HARDENED-RELEASE.zip` (SHA-256 `e4989cf8489841eedfa5922cf2ebd069e1e21a70dfca0bcd637c32b618327ac0`). This public release is curated, not the runnable cognitive runtime. It excludes private algorithms, trust implementation, private evidence and internal test fixtures. No ASI, AGI, independent superiority or V1.1 parity is claimed.
