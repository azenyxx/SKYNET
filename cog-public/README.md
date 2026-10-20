# SKYNET COG — Public Reference Edition

A small, **independently written educational reference** illustrating a bounded, deterministic cognitive task workflow in Python.

This repository is **not** the SKYNET Cognitive Foundation source release. It does not include internal architecture, production runtime, private interfaces, project roadmap, evidence infrastructure, operational configurations, or unpublished research.

## What is included

- Immutable task and result objects
- A tiny allowlisted, local-only task dispatcher
- Deterministic SHA-256 commitments for illustrative inputs/outputs
- Unit tests

## Quick start

Python 3.10+; no third-party dependencies.

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
PYTHONPATH=src python3 -m cog_public.demo
```

## Security and scope

This is an educational demonstration, **not** an autonomous agent, independently verified evidence system, cryptographic attestation, production-ready runtime, or claim of AGI/ASI capability. Input/output hashes alone do not prove correctness, independence, or authenticity.

No external services, API keys, network access, or private datasets are required.

## Release boundary

Public example code is newly authored for this release. Private SKYNET COG-001–020 artifacts are deliberately **not included**.

## License

All rights reserved unless a separate license is granted. Public visibility does not itself grant reuse rights.
