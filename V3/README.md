# SKYNET V3 — Public Formal Specification & IR Subset

**Cyberdyne Systems | SKYNET V3**

This repository contains a deliberately limited, runnable public code sample from the SKYNET V3 development line, based on the E-05 cumulative baseline. It is **not** the full SKYNET cognitive engine, an autonomous agent, or an ASI implementation.

## Included

- Canonical JSON validation and SHA-256 content digests.
- Typed error handling, integer domains and fixed-point unit/scale helpers.
- SKYSPEC v1 formal input validation (M1) and deterministic typed IR compilation (M3).
- Eight public example specifications (F1–F8), serialization golden vectors, and executable regression tests.

## Not included

Solver and solution search (M6), belief and adaptation algorithms (M7/M8), executive/recovery (M9), private simulation/evaluator configuration (M10), evidence/trust infrastructure, independent verification (T2/T3), credentials, and internal architecture or qualification reports.

## Requirements

Python 3.12+ (standard library only for this public subset). The original private development environment used Python 3.12.3; compatibility on every Python version/platform is not claimed.

## Run tests

From this directory:

```bash
python3 -m unittest discover -s tests -p 'test_tser.py' -v
```

## Minimal example

```python
from pathlib import Path
from skynet_v3.m1_ingest_formal import ingest
from skynet_v3.m3_ir import compile_ir

spec = ingest(Path('fixtures/F1_linear_feasibility.json').read_bytes())
ir = compile_ir(spec)
print(spec['spec_digest'])
print(ir['ir_digest'])
```

This subset parses and compiles formal tasks; **it does not solve them**.

## Verification boundaries

Public test success validates only the included formal parsing, canonicalization and IR transformations. It does not demonstrate autonomous cognition, independently verified feasibility, superhuman performance or artificial superintelligence. No independent T2/T3 qualification is bundled.

## Provenance

Curated from `SKYNET-V3-001-E05-CUMULATIVE-BASELINE.zip` (source SHA-256 `1c708916b90f6b71db4e2f510fc52c63bbeb6c891430ae867779aef42073777f`). Public subset deliberately excludes private implementation components. Source files are preserved without modifications except the package initializer, which is replaced by a public-scope declaration.

## License

Copyright (c) 2026 Cyberdyne Systems. All rights reserved. No open-source license is granted by this package. Add a license only after the project owner explicitly chooses one.
