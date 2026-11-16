# SKYNET V3 — Public Verification Utilities

This directory contains a limited public subset of engineering utilities and **eight standalone tests**. It does not contain the SKYNET cognitive engine or private evaluation harness.

## Contents

- `public_core/canonical.py`: deterministic JSON encoding, hashing and strict input parsing.
- `public_core/errors.py`: structured validation errors.
- `public_core/units.py`: integer quantity matching and exact, bounded scaling.
- `tests/test_public_core.py`: reproducible public unit tests.

Run from the repository root:

```bash
python3 -m unittest discover -s V3/tests -p 'test_*.py' -v
```

## What these tests establish

The public tests exercise the **published utilities only**. They do not reproduce the private cognitive-loop, adaptation, transfer, security-infrastructure or benchmark evaluations. Internal source code, schemas, operational parameters, credentials and unpublished evidence are not included.

This is a selective engineering disclosure, not an independently verified ASI claim. Licensing remains governed by the repository's applicable license, if any.

## Public Update 001

Additional public V3 utilities:

- skynet_v3/canonical.py — deterministic JSON serialization.
- skynet_v3/errors.py — validation errors.
- skynet_v3/units.py — integer quantity operations.
- tests/test_public_v3.py — 15 unit tests.

Run from the V3 directory:

    python3 -m unittest discover -s tests -p "test_*.py" -v
