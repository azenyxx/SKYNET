# SKYNET V3 — Public Engineering Update

**Cyberdyne Systems | 13 November 2026 | V3-003 internal candidate: PARTIAL**

SKYNET is an ASI-oriented engineering effort developing bounded cognitive mechanisms and independently evaluable evidence. This directory provides a deliberately limited, public-safe subset of real V3 infrastructure code plus a summary of internal development experiments. It **does not** contain the private cognitive core.

## Implemented internally (not published here)

The development coordinator links M3 counterexample refinement, M4 typed composition, M5 adaptive strategy selection and M6 abstraction discovery to the real M9 → M8 → OR-Tools replanning path with T1 checks. Invalid candidates are rejected, and learned-method execution is tracked through provenance and feedback. The system remains `UNTRUSTED_DEV`.

## Reported development evidence

| Experiment | Observation | Boundary |
|---|---|---|
| M5 adaptation | After a bad method received reward 0, later choices favored the successful method | Small tuning pilot; no broad generalization claim |
| M3 refinement | P1 recovery 3/3; P3 later recovered after binding-aware pre-screening | Tuning-context result |
| M4 synthesis | Composed candidate executed in a real context with `T1_PASS` | T1 is not verified task completion |
| M6 discovery | Discovered candidate instances executed on held-out H2/H7 | Instances duplicated existing method behavior |
| Candidate cache | Searches 3 → 1, P1 recovery 3/3 unchanged | One fixture; 66.7% fewer searches, not a measured runtime speedup |
| Early held-out baseline | T1 3/3 for cognitive, built-in and NAIVE | No learned replan invoked on those tasks |
| Later held-out evaluation | Learned candidate used on H1, H2, H5; 9 frozen variants | Same terminal states and T1 results as both baselines; **no win** |
| Focused integration tests | 15 PASS, 1 FAIL, 0 ERROR | Remaining stale assertion expects four held-out tags instead of nine |

The latest internal report labels H5 a feasible terminal outcome, but its recorded terminal state is `UNVERIFIED_CANDIDATE`; goal completion should not be treated as independently proven from the T1 flag alone. The later held-out set consists of variants of only two base specifications. These findings are internal executor-reported development evidence, **not independent qualification**.

## Public source code

- `src/skynet_v3/canonical.py` — **unmodified selected source** from the internal V3-003 cumulative archive; strict canonical JSON encoding and validation.
- `src/skynet_v3/errors.py` — **unmodified selected source**; typed validation errors.
- `tests/test_public_canonical.py` — standalone public smoke tests authored for this release.
- `evidence/RESULTS.json` — sanitized, hand-curated aggregate from internal milestone reports (not raw execution traces).

No private coordinator, strategy-selection algorithm, refinement/search logic, abstraction-discovery implementation, proprietary fixtures, internal execution traces, credentials or full runtime are included. The public subset is **not a runnable SKYNET cognitive engine**.

### Run the public smoke tests

```bash
cd V3
PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_public_*.py' -v
```

## Qualification boundary and next steps

The V3-003 development candidate is still partial, and there is no demonstrated advantage against matched baselines. Future work targets genuinely distinct task families, nontrivial abstraction generalization, goal-level verification, stronger baseline comparisons and independent evaluation. **SKYNET is not a demonstrated AGI, ASI or superhuman system.**
