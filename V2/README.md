# SKYNET v2.0 — Public Research Update

SKYNET is an **ASI-oriented research prototype**, not an ASI system. This selective public update summarizes recent engineering work without releasing the private cognitive core.

## Research progress (internal development)

- Adaptive planning and metacognitive control have been implemented and tested on synthetic tasks.
- Experience-guided planning showed a benefit on a deliberately learnable synthetic task family; it also exhibited negative transfer.
- Under distribution shift, both tested experience-based policies underperformed a no-experience baseline.
- A cost-sensitive policy reduced some losses under one reversal condition but did **not** solve distribution-shift robustness.
- Controlled knowledge revision is a planned next step, **not a completed capability** in this update.

## Evidence and limitations

These are **internal development results**, not independently confirmed capability claims. The test environment is synthetic, and production-grade evaluator/participant isolation is not established. No general intelligence or superhuman performance is claimed.

**Qualification:** `SUPERHUMAN_NOT_EVALUATED`.

## Public code

`examples/shift_demo.py` is a small, independently written educational illustration of negative transfer. It is **not** SKYNET's proprietary planner, learning implementation, evaluation harness, or benchmark. Run with `python3 V2/examples/shift_demo.py`.

No private algorithms, model weights, task seeds, evaluation internals, keys, or infrastructure configuration are included.
