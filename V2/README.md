# SKYNET V2 — Public Engineering Release

**Cyberdyne Systems · SKYNET V2.0 · Public code subset**

This directory replaces the previous public `V2/` contents. It documents the completed V2 functional integration milestone and publishes **real, selected source files from the accepted V2-017R7 release**, together with a standalone read-only archive verification utility and executable tests. This is not the full private runtime.

## Engineering milestone

SKYNET V2 integrated the V1.1 operational infrastructure (scheduler, workers, journaled state, recovery, authorization and transport) with V2 cognitive components (planning, knowledge, learning, metacognition, supervised agents and parallel execution). The integration program closed with V2-017R7, following fixes to delegation replay, deterministic failure handling, worker outcome isolation and recovery verification.

**Internal acceptance evidence, reported by the implementation executor:** V1.1 1,179/1,179; adversarial 39/39 + 24/24; V2 388/388; unified 76/76; recovery matrix A01–A22 22/22. These figures are *internal regression results*, not independent external certification. The private runtime and full test corpus are not distributed here.

Accepted private release reference: `SKYNET-V2-017R7-FINAL-UNIFIED-HARDENED-BASELINE.zip`  
SHA-256: `57c6bc9be4a9c31fbec02a1840f62ed6454aab94f78ad6f92c0aa2cd0b83cdc2`

## Published code

- `src/skynet_v2_eval/prng.py` — SHA-256 counter-mode deterministic pseudo-random generator for repeatable experiments. **Not suitable for secrets.**
- `src/skynet_v2_eval/stats.py` — exact-arithmetic statistics, confidence intervals, deterministic bootstrap and evaluation summaries.
- `src/skynet_v2_eval/scoring.py` — reference-based A+ evaluation scoring with integer arithmetic.
- `src/skynet_v2_eval/errors.py` — structured evaluation errors.
- `src/skynet_v2_trust/ids.py` — ULID-format and deterministic identifiers.
- `src/skynet_v2_trust/errors.py` — fail-closed structured error taxonomy.
- `tools/verify_release.py` — independent, read-only archive verifier (new public utility; not copied from private runtime).
- `tests/test_public.py` — standalone smoke and negative tests for this published subset.

The six Python source modules under `src/` are byte-for-byte selected from the accepted V2-017R7 archive. No proprietary planner, learning policy, metacognitive controller, agent execution runtime, internal trust keys or complete production orchestration is published.

## Run locally

Python 3.13 recommended; the public tests use only the standard library.

```bash
cd V2
PYTHONPATH=src python -m unittest discover -s tests -v
python tools/verify_release.py /path/to/release.zip --sha256 EXPECTED_SHA256
```

The verifier checks the archive digest, CRC, normalized paths, duplicate entries, symlinks and the `MANIFEST.sha256` inventory. It does not extract or execute the archive. The CLI expects a single `MANIFEST.sha256` whose entries cover every other file, relative to the manifest directory.

## Trust and capability boundary

This is an **ASI-oriented engineering prototype**, not an achieved AGI or ASI system. No independent superhuman performance claim is made. The accepted V2 baseline is a **functional engineering baseline**, not a production security certification. Known limitations include unanchored trailing journal truncation (R-1), evaluator/participant process and Unix-user co-location (R-2), TEST-only trust qualification, unqualified external provider connectivity, and unbounded V2 journal growth following rejected SYS commands at capacity (P2-1).

V3 architecture work will address stronger independent evaluation, more robust operational trust boundaries, adaptive generalization, continual learning and evidence-backed autonomous improvement. Public artifacts remain intentionally scoped to avoid disclosing private cognitive core implementations.

## Repository scope

Only the contents of this `V2/` directory are intended for replacement. Do not delete or rewrite other repository directories. This public subset is illustrative and is not a standalone deployment of the full SKYNET unified runtime.
