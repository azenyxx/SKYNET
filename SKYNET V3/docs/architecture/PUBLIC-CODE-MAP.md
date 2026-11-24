# SKYNET V3 — Public Code Map

The current repository publishes a **selected executable subset**, not the private cognitive engine.

| Public path | Contents | Interpretation |
| --- | --- | --- |
| [`public_core/`](../../public_core/) | Canonical JSON, errors and exact unit arithmetic | Generic real Python utilities |
| [`skynet_v3/`](../../skynet_v3/) | Canonicalization, validation errors and units | Historical public utilities |
| [`src/skynet_v3/`](../../src/skynet_v3/) | Additional canonicalization and error utilities | Separate historical subset; interfaces must be reviewed before merging |
| [`examples/`](../../examples/) | Replanning-capture contract, continuation accounting, statistics, snapshot integrity, static headroom, PoC budget and milestone gates | Runnable bounded examples, **not** full private implementations |
| [`tests/`](../../tests/) | Standalone tests for public functions and examples | Public verification only |
| [`evidence/`](../../evidence/) | Selected disclosed verification outputs | Not the complete private research evidence |
| [`docs/updates/`](../updates/) | Archived dated public updates | Historical reports, not current qualification |

## Module consolidation policy

Modules with matching names in `public_core/`, `skynet_v3/` and `src/skynet_v3/` must **not** be deleted or merged solely because their names look similar. First check imports, API signatures, semantics, regression tests and any independent consumers. Structural consolidation is a separate engineering task.

## What is not published

Protected P1 implementation, private P2 research source and benchmarks, trained state, unpublished datasets, secret credentials, sensitive operational details and complete Cognitive Core algorithms.

## Tests

From repository root:

```bash
PYTHONPATH="$PWD/SKYNET V3:$PWD" \
python3 -m unittest discover -s "SKYNET V3/tests" -p 'test_*.py' -v
```

Successful public unit tests are **not** evidence of qualified ASI, generalizable learning, or private runtime security.
