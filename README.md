# SKYNET — ASI-Oriented Engineering Program

**Cyberdyne Systems · Cognitive systems, autonomous execution and verifiable evaluation**

SKYNET is an engineering program investigating components and foundations relevant to Artificial Superintelligence (ASI). The project combines cognitive architecture, planning, agent coordination, learning, bounded improvement, operational runtime and systematic validation. **SKYNET is not an achieved AGI or ASI system.**

## Repository layout

| Directory | Development program |
| --- | --- |
| `FOUNDATION/` | Cognitive Runtime V1 foundation |
| `COG/` | COG-001–020: cognitive contracts and processing |
| `AGT/` | AGT-001–010: agent systems |
| `LRN/` | LRN-001–008: learning and adaptation |
| `RSI/` | RSI-001–008: bounded improvement workflows |
| `SYS/` | SYS-001–008: runtime infrastructure |
| `VAL/` | VAL-001–010: capability validation |
| `V2/` | Selected V2 engineering source, tests and milestone documentation |
| `V3/` | V3 engineering progress, public-safe source subset, and bounded experimental evidence |

The original development program comprises **64 numbered stages**. Historical snapshots and audited runtime components are separate from the selected V2 public subset.

## Engineering progress

| Version | Milestone | Status |
| --- | --- | --- |
| V1.0 | 64-stage cognitive and runtime foundation | Completed engineering program |
| V1.1 | Hardened operational runtime and native integration | Historical hardened baseline |
| **V2.0** | **Unified operational + cognitive runtime** | **Functional baseline accepted, with qualification limitations** |
| V3 | Autonomous Superintelligence Core | Architecture planning |

### SKYNET V2.0 — final unified functional baseline

V2 integrated V1.1's operational scheduler, workers, transport, memory, authorization and recovery with bounded V2 cognitive execution, planning, learning and knowledge integration, metacognitive controls, agent coordination and parallel processing.

The final **V2-017R7** engineering baseline closed the documented delegation recovery and worker outcome-isolation defects. Its internal functional acceptance includes deterministic replay, fail-closed fault handling, agent supervision, provider isolation and a 22-scenario recovery matrix.

| Internal verification | Result |
| --- | ---: |
| V1.1 regression | **1,179 / 1,179 PASS** |
| Adversarial checks | **39 / 39 + 24 / 24 PASS** |
| V2 regression | **388 / 388 PASS** |
| Unified integration | **76 / 76 PASS** |
| Recovery acceptance | **22 / 22 PASS** |

These are **internal executor results**, not an external audit or independent intelligence qualification. The accepted baseline is a functional engineering milestone, not production certification. Known limitations include unanchored trailing-record rollback (R-1), evaluator co-location (R-2), TEST-only trust, unqualified external provider networking and V2 journal growth at SYS capacity (P2-1).

**Private accepted release:** `SKYNET-V2-017R7-FINAL-UNIFIED-HARDENED-BASELINE.zip`  
**SHA-256:** `57c6bc9be4a9c31fbec02a1840f62ed6454aab94f78ad6f92c0aa2cd0b83cdc2`

**Explore:** [V2 engineering report and public code](V2/README.md) · [Full roadmap](ROADMAP.md) · [Security policy](SECURITY.md)

## Working with the source

Python modules and tests are organized by research program. Historical audited runtime packages are under `SYS/runtime/src/` and `VAL/runtime/src/`, with tests in their respective runtime test directories. See `pyproject.toml` for original runtime tooling. Historical stages may require distinct imports and are not one installable package.

The `V2/` directory includes **selected executable modules and public tests**, not the full private SKYNET runtime. To run the public subset:

```bash
cd V2
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

## V3 — next architecture program

The proposed **SKYNET V3 — Autonomous Superintelligence Core** will prioritize adaptive generalization across unseen tasks, continual learning with retention safeguards, robust autonomous planning, evidence-backed bounded self-improvement, isolated evaluation and stronger operational trust. The first V3 milestone is **architecture and measurable acceptance criteria**, not an unverified claim of superior intelligence.

See [ROADMAP.md](ROADMAP.md) for stage gates, expected evidence and outstanding qualification requirements.

## Support SKYNET

Support independent engineering, evaluation infrastructure and long-term research through voluntary Bitcoin contributions.

**Bitcoin · Mainnet (BTC)**

### `bc1qrxegtdynmn2rnhnu24gqvljlsxn83h5jhhwkk9`

**Network:** Bitcoin mainnet only · **Asset:** BTC

> Send only native BTC over the Bitcoin mainnet. Always verify the complete address before sending. Contributions are voluntary and do not confer equity, ownership, governance or investment rights.

## License

See [LICENSE](LICENSE). Third-party and historically contributed code remains subject to applicable provenance and licensing terms.


## SKYNET V3 — Cognitive Integration Update (13 November 2026)

V3-003 integrates strategy selection, real task execution, counterexample refinement, typed composition, abstraction discovery and verified feedback in a bounded development loop. A previously learned candidate was retrieved and executed on held-out variants H1, H2 and H5. Across nine frozen variants, the integrated cognitive path matched both the built-in SKYNET and NAIVE baselines in terminal state and T1 result; **no performance advantage was demonstrated**. The M6 abstraction instances tested were behaviorally identical to existing methods. The latest reviewed internal candidate remained **PARTIAL (15 PASS / 1 FAIL)** due to a stale held-out fixture-count assertion.

The earlier V3-003 pilot observed strategy choice changing after failed execution, P1 recovery 3/3, and candidate-search caching reducing searches from 3 to 1 on one fixture. An earlier held-out T1 comparison scored 3/3 for all three paths, but none exercised learned-method replanning; it was not a demonstration of cognitive superiority.

See [V3/README.md](V3/README.md) for detailed boundaries, results, and public code. **This is not a claim of AGI, ASI, superhuman capability, independent qualification or production readiness.**
