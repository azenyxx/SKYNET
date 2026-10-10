# SKYNET PUBLIC-002–005 — Export review

Status: **local candidate for owner review and manual GitHub publication**.

- Based on the previously approved **public R2 fixture protocol**, not a wholesale export of the private SKYNET-005-G2 baseline.
- Includes standalone SDK helper, deterministic fixture runtime (`replay`), offline CLI, tests and CI.
- Excludes private Cognitive Core, Gateway implementation, SQL, credentials, Git history, and provider adapters.
- This review is a source-level boundary check, not an independent penetration test.
- Do not claim production readiness, external sandbox verification, or PostgreSQL G3 completion.
- LICENSE is governed by the existing repository root MIT license. Confirm repository root LICENSE before publishing.
- The older `examples/public-mock/` is retained unchanged; SDK lives under `sdk/python/`.
- CI is configured but GitHub-hosted execution has not been observed.
