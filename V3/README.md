# SKYNET V3 — Public Foundation Update 001

A deliberately limited public code sample from the SKYNET V3 research prototype by Cyberdyne Systems.

## Included

- `skynet_v3/canonical.py`: deterministic JSON encoding, SHA-256 digests, strict JSON parsing and nesting checks.
- `skynet_v3/errors.py`: structured error types.
- `skynet_v3/units.py`: exact integer scale semantics and rejection of unsupported conversions.
- `tests/test_public_v3.py`: 15 deterministic standard-library unit tests.

These three implementation modules are selected from the cumulative V3 engineering baseline. The public tests are newly authored for this subset. This release intentionally omits cognitive algorithms, learning and self-improvement internals, evaluation-private fixtures, operational security modules, keys, configuration and infrastructure.

## Run tests

Requires Python 3.10+; no third-party packages.

From the repository root:

```bash
cd V3
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

## Scope and evidence

This update demonstrates selected foundational utilities, **not** AGI, ASI, autonomous self-improvement, independent security qualification or production readiness. Passing these tests validates only the included public subset; it does not replace the private V3 regression or security gates.

Source provenance: selected from `SKYNET-V3-SECURITY-CORRECTIVE-002A.zip`, SHA-256 `16777eb41ffd6ef8d57319234b9e09bb452235d3e5a4b95470b6b07215694029`. No private repository contents are included.

Copyright and license: no new license grant is provided by this folder; repository licensing governs reuse where applicable.
