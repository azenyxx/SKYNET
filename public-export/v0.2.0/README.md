# SKYNET — Public Evaluation Utilities

**Minor public update: v0.2.0 (2026-11-04)**

SKYNET is an ASI-oriented research and engineering prototype. **It is not an achieved AGI or ASI.** No superhuman performance has been independently verified.

This is a deliberately limited, reviewed **public subset**, not the complete SKYNET v2.0 runtime. It includes deterministic non-cryptographic test PRNG and basic statistical utilities (including Wilson confidence intervals) from the evaluation layer. The private cognitive core, planner, rule learning, adaptation, trust runtime, unreleased experimental datasets and internal architecture are **not included**.

## Current public status

- Engineering milestone V2-011-Q3 completed internally; experimental qualification **PARTIAL**.
- Q3: 3 beneficial and 1 harmful decision changes, with 146 unchanged; the sample of changed decisions was insufficient to establish improved decision quality.
- Hazard utility non-inferiority does **not** establish superiority; retention was **not exercised**.
- `SUPERHUMAN_NOT_EVALUATED`.

These statements are internal experimental reports, **not independently verified scientific claims**.

## Run tests

Python 3.12+ (standard library only):

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

## Scope and security

- No credentials, keys, secrets, production configuration or private repositories are included.
- The PRNG is **not suitable for cryptographic secrets**.
- No public interface is promised to be stable.
- Internal evidence and full experimental reproduction are not included in this selective export.

## License

All rights reserved unless a separate license is added by the owner. Public visibility does not grant permission to reuse or redistribute code.
