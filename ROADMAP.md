# Research and public release roadmap

This roadmap lists **research and verification gates**, not dates or performance promises.

1. **R1 — Architecture & Research Preview:** sanitized documentation, research questions, boundaries, contribution guidelines, and limitations.
2. **PostgreSQL authority verification:** execute blocked G3 checks in an authorized disposable PostgreSQL 17 environment. Record actual outcomes and preserve remaining runtime debt.
3. **Public developer interfaces:** independently review minimal API contracts and their complete dependency chains; publish only after owner approval.
4. **Reproducible demonstrations:** add nonsensitive deterministic fixtures and tests that run without private Cognitive Core dependencies.
5. **Independent runtime qualification:** separately test sandbox isolation, provider behavior, messaging/storage, recovery, and control enforcement before making corresponding security claims.
6. **Research evaluation:** develop independently assessable experiments and meaningful human baselines before claiming advanced capabilities.

Private SKYNET engineering tasks continue separately. Passing a local test or completing an architectural milestone does not demonstrate AGI or ASI.

## October 2026 engineering checkpoint

The current private implementation milestone is SKYNET-006:
Scheduler and Parallel Cognition.

The immediate engineering sequence is:

1. Complete implementation and local verification.
2. Conduct an independent implementation review.
3. Execute PostgreSQL 17 runtime verification.
4. Reassess public release eligibility for selected interfaces.

See [PUBLIC-006](docs/updates/PUBLIC-006.md).

These are engineering gates, not promised release dates.
