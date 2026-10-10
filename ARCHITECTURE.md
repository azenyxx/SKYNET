# Architecture overview

This sanitized overview describes research boundaries, not deployment instructions or a complete implementation specification. It does not replace the project's approved internal architecture.

## Separation of responsibilities

| Area | Responsibility and boundary |
|---|---|
| Cognition | Propose objectives, plans and actions. Reasoning does not confer execution authority. |
| Knowledge and evidence | Preserve separate content, observation, provenance, claim and assessment identities. An assertion is not independently verified knowledge. |
| Trusted execution | Enforce authorized actions and record bounded execution observations. |
| Governance | Authorize actions and resource use under independent policy. |
| Independent assessment | Evaluate claims and capabilities without allowing the assessed component to award itself an authoritative result. |

Private implementation does not imply trusted implementation. Authorization must remain independently reviewable, and unavailable authority must not become an implicit permission.

## Interface principles

Potential public interfaces are versioned, narrowly scoped and separated from private implementation imports. Their conceptual responsibilities include identifying the request and exact input revision, referring to authorization, correlating execution and result, and linking evidence and provenance. No executable API schema or endpoint is released in this candidate. Consumers must not derive a wire protocol from this overview.

A cognitive proposal, execution authorization, result, usage observation and accounting decision are distinct objects. Results do not mint authorization. A resource reservation is an upper bound, not evidence of consumption. Uncertain outcomes require explicit representation and cannot silently become success or unused capacity.

Deterministic replay reconstructs recorded decisions or fixture outputs without creating new external effects. Fixture behavior is not evidence of real provider quality or host isolation.

## Public/private separation

Private scope includes cognitive mechanisms, metacognitive control, internal orchestration, capability-improvement mechanisms, proprietary learning/world adaptation and sensitive research parameters. This candidate exposes none of those implementations, schemas or parameters. Security-critical boundaries may be described and independently reviewed without disclosing private cognitive algorithms.

No operational topology, private policy configuration, deployment secret, migration or privileged invocation example is included. Real isolation and provider behavior require separate runtime evidence; they are not established by this diagram-free conceptual overview.
