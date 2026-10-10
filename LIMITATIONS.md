# Limitations and evidence status

- This public research preview is documentation-only. It cannot run SKYNET and contains no public API implementation or public software test suite.
- The private baseline contains experimental implementations and recorded local checks. Those checks are not independently reproducible from this release and are not presented as public test results.
- PostgreSQL G3 authority verification remains **BLOCKED_ENVIRONMENT**. The required runtime was unavailable in the execution environment; migrations, roles, atomicity, concurrent replay and rollback were not verified by that attempt.
- Real sandbox/container/microVM isolation, provider behavior, end-to-end messaging/storage, runtime recovery and enforcement latency remain unverified where their external evidence is pending. No guarantee is inferred from mock tests or source inspection.
- Deterministic mock observations are fixtures, not external usage measurements, empirical quality metrics or capability benchmarks.
- Independent evaluation and uncertainty handling remain necessary. No result here proves AGI, ASI or superiority over human baselines.
- The private/public split does not reduce the need for independently reviewable authorization and security evidence.
- The repository owner selected MIT for public repository content; see the GitHub LICENSE file. Private, unpublished implementation remains outside this license. External runtime qualification remains outstanding.

A file-integrity check proves only consistency with a manifest. It does not prove security, truthful measurements, ownership or fitness for production.
