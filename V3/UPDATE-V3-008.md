# SKYNET V3 — Public Update 008 (2026-11-20)

## Static-control headroom: negative research evidence

This update documents the producer-reported Session 20 Go/No-Go finding. Across 38 previously observed continuation-feasible scheduling tasks, the retrospective per-task oracle over the evaluated repair strategies had **0/38 additional local-repair successes** compared with the best single fixed strategy. The analysis is **post-hoc**, on a small sample, and is **not** a confirmation that the underlying learning architecture is incapable of improving.

The engineering takeaway is that comparing learned-method choice only against the built-in narrow repair neighbourhood is insufficient: a fixed wider-neighbourhood control is required. A useful learning claim would require gains over a predeclared static control, not just over an artificially weak baseline.

This public package includes `examples/static_headroom.py`, a dependency-free demonstration of how to measure *oracle over best fixed strategy* headroom from abstract boolean outcomes, and corresponding synthetic unit tests. It does not contain internal SKYNET implementations or experimental records.

**Status:** P2 ACTIVE — FULL QUALIFICATION PENDING. Q5/L3 NOT QUALIFIED. Security 002B OPEN. P3 NOT AUTHORIZED. This is a research update, not an ASI/AGI capability claim.
