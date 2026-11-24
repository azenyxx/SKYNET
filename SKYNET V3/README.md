# SKYNET V3 — Cognitive Engineering Research

**An executable, ASI-oriented research program. Not a completed AGI or ASI system.**

SKYNET V3 investigates how autonomous software can plan under constraints, execute safely, verify outcomes, retain research state and use feedback to inform subsequent decisions. A validated learning advantage over strong fixed strategies remains an open research objective.

## Engineering capability map

| Area | Current status | Where to look |
| --- | --- | --- |
| Task planning, execution and replanning | Implemented in the **private** research runtime | [Architecture](docs/architecture/ARCHITECTURE.md) |
| Deterministic validation, canonical encoding and bounded units | Public executable utilities | [`public_core/`](public_core/) |
| Public canonicalization and structured errors | Public executable modules | [`skynet_v3/`](skynet_v3/) and [`src/skynet_v3/`](src/skynet_v3/) |
| Replanning capture, statistical accounting and snapshot integrity | Standalone **public examples**, not the full private harness | [`examples/`](examples/) |
| Public verification tests | Executable tests for disclosed code only | [`tests/`](tests/) |
| Internal research results and negative findings | Publicly documented summaries; raw private evidence not released | [Research status](docs/research/RESEARCH-STATUS.md) |

## Cognitive pipeline

```mermaid
flowchart LR
    A["Task"] --> B["Plan"]
    B --> C["Execute"]
    C --> D["Verify"]
    D --> E["Feedback"]
    E --> F["Evaluate Strategy"]
    F --> G["Persist / Re-evaluate"]
```

Stages reflect the **research architecture**, not a claim that all stages have been independently qualified as one self-improving system.

## Research snapshot — 24 November 2026

- **24/24** matching independent-process semantic results reported in limited L1 testing.
- **40/52** successful tasks in a previous planning pilot, with **no success-rate advantage** over the baseline.
- **16** novel AST forms produced experimentally; **new useful skill acquisition not demonstrated**.
- **0/38** historical observations showed neighborhood-selection improvement over the strongest fixed strategy in the tested method space.
- **140/140** internally reported tests in the Session 22 current P2 regression partition; this is **not** the public test count.
- **L3–L6 not qualified; Security 002B open; P3 not authorized.**

[Full research status](docs/research/RESEARCH-STATUS.md) · [Architecture](docs/architecture/ARCHITECTURE.md) · [Public code map](docs/architecture/PUBLIC-CODE-MAP.md) · [Updates](docs/updates/)

## Run public tests

From repository root:

```bash
PYTHONPATH="$PWD/SKYNET V3:$PWD" \
python3 -m unittest discover -s "SKYNET V3/tests" -p 'test_*.py' -v
```

Tests verify only **published** Python modules and examples. No private implementation, protected evaluation data or internal snapshots are supplied.

## Research boundaries

The next target is a reproducible **Planning → Execution → Verification → Feedback → Behavioral Adaptation → Persistent State → Re-evaluation** demonstration and a statistically defensible comparison with fixed baselines. No learning advantage is asserted in advance.

**[SKYNET home](../README.md)** · **[Project website](https://cyberdynesystem.cc/)**
