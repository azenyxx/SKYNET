# Architecture overview

The internal SKYNET SYS series is organized into the following local reference subsystems:

1. SYS-001 — Runtime foundation and contracts
2. SYS-002 — Cognitive message bus and event transport
3. SYS-003 — Task scheduling and parallel cognition
4. SYS-004 — Shared memory, state, and provenance
5. SYS-005 — Worker orchestration and isolation
6. SYS-006 — Verification, decision policies, and conflict resolution
7. SYS-007 — Observability, fault tolerance, and recovery (incomplete)
8. SYS-008 — End-to-end integration and qualification (incomplete)

The design emphasizes deterministic local behavior, explicit authorization, auditability, bounded resources, and fail-closed behavior. These are architectural goals and local test properties, not a claim of production security.
