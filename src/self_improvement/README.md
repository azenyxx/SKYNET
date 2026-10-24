# SKYNET — RSI-001–008 (public research snapshot)

This repository contains the Python source and original test modules from the selected latest revisions of RSI-001–008. It is **not** a production-ready autonomous self-improvement system.

**Qualification:** `SERIES_CLOSED_PARTIAL`. Integration evidence is fixture-based; independent autonomous RSI, production deployment, actual rollback and full semantic validation are **not qualified**. All seven authorization flags are FALSE.

## Contents

- `src/01-RSI-001` through `src/08-RSI-008`: original Python implementation modules from the selected revisions.
- `tests/01-RSI-001` through `tests/08-RSI-008`: original test modules (not rewritten or artificially fixed).
- `docs/ARCHITECTURE.md`: stage-by-stage overview.
- `docs/TESTING.md`: testing guidance and dependency caveats.
- `docs/SECURITY.md`: limitations and disclosure policy.
- `SOURCE-MANIFEST.json`: hashes of the included source and test files.

The original test modules reference predecessor modules and in some cases **unbundled AGT/LRN components** such as `agent_contracts` or `integrated_qualification`. This snapshot therefore **does not claim the entire test suite is runnable standalone**. No tests were rerun during public packaging. See `docs/TESTING.md`.

Historical private release ZIPs, internal reports, logs, and audit documents are intentionally excluded. No license is granted by this archive; add a license only if you own the rights to all included code.
