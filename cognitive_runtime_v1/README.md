# SKYNET Cognitive Runtime V1 — Public Review Candidate

This repository snapshot is a **deterministic, isolated educational/runtime prototype**, not a production autonomous agent, trusted execution environment, or ASI.

Modules: COG-001 task lifecycle; COG-002 structured planner; COG-003 allowlisted local SHA256_TEXT_V1; COG-004 evidence recomputation; COG-005 unpersisted knowledge proposal; COG-006 bounded orchestrator; COG-007 evaluation harness.

No model-provider calls, production authorization, durable replay/CAS, Memory or World Model persistence, trusted evidence provenance, or authenticated external execution are implemented. The included benchmark evaluates bounded deterministic functionality, **not intelligence or real-world security**.

## Run tests

Requires Python 3.12+ (standard library only). From this directory:

```sh
export PYTHONPATH="$(pwd)/cog001:$(pwd)/cog002:$(pwd)/cog003:$(pwd)/cog004:$(pwd)/cog005:$(pwd)/cog006:$(pwd)/cog007"
for i in 001 002 003 004 005 006 007; do
  python3 -m unittest discover -s "cog$i" -p 'test_*.py' -q || exit 1
done
```

## Publication status

**PUBLIC ISOLATED BASELINE — OWNER-AUTHORIZED SOURCE RELEASE.** This implementation is not production-ready and carries no trusted execution authority. No license has been granted.
