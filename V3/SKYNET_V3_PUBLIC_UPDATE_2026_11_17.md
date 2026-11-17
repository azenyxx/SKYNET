# SKYNET V3 — Minor Public Engineering Update

**Date:** 2026-11-17  
**Track:** Cognitive research infrastructure / P2  
**Status:** Research prototype; independent cognitive superiority not established

## Summary

The V3 research program has progressed from planning benchmarks to a reproducible, development-only learning-state transport experiment.

- Planning experiments across F3/F4/F5 recorded **134 eligible paired tasks and zero outcome disagreements** between the tested repair candidate and full re-solve baseline. The candidate required more solver calls. This is an **exploratory negative finding**, not proof of general algorithmic equivalence.
- Session 6 reported **L1 reproducibility: 24/24 matching semantic outcome digests** across separate evaluator processes.
- Session 6 reported **L2 persistence: passed**, including cross-process restore, integrity validation, and rejection of malformed or tampered snapshot artifacts.
- The isolated research adapter is constrained to `UNTRUSTED_DEV` state. The current test snapshot was **manually configured**, not learned from experience. Behavioral improvement, transfer, and statistical qualification remain untested.
- The development held-out sets remain sealed. P2 remains active; P3 has not begun.

## Runnable public example

This update includes **an original standalone reference example**, not a copy of SKYNET's private cognitive code or its internal snapshot interface:

- `examples/snapshot_integrity.py`: deterministic JSON state artifact, SHA-256 integrity check, strict version/trust enforcement, fail-closed verification.
- `tests/test_snapshot_integrity.py`: nine Python standard-library tests.

Run from the **repository root**:

```bash
python3 -m unittest discover -s V3/tests -p 'test_snapshot_integrity.py' -v
```

The example is deliberately small and does not implement learning, executive governance, production state promotion, or held-out evaluation.

## Research boundaries

This public update does **not** publish private Cognitive Core algorithms, full P1/P2 sources, checkpoint ZIPs, internal evidence, held-out data, credentials, security-sensitive interfaces, or the full experimental design. The benchmark and qualification numbers above are reported from internal development evidence; they have not been independently reproduced in this public example.

**Next research focus:** governed learning-state training, controlled memory-enabled versus memory-ablated validation, followed by transfer and independent qualification. Moving to P3 requires P2 review and formal baseline acceptance.
