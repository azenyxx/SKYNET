#!/usr/bin/env python3
"""Idempotent, non-destructive V3 documentation update for SKYNET public repo.

Requires existing README.md and ROADMAP.md with the documented V2 section anchors.
Does not edit V2, implementation source, or Git state.
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]

README_SECTION = '''## V3 — Autonomous Superintelligence Core

**Cyberdyne Systems** is designing SKYNET V3 toward an executable, continuously learning cognitive system: one that can understand unfamiliar problems, discover and verify solutions, retain validated learning, transfer methods across domains, and safely test improvements to its own problem-solving methods.

The six planned capabilities are **autonomous problem understanding, novel solution discovery, superhuman problem solving, continuous learning, cross-domain generalization, and verified recursive improvement**. The intended loop is **Understand → Discover → Solve → Verify → Learn → Improve → Re-evaluate**.

The roadmap progresses through **V3-ARCH-001**, then **V3-001 Intelligence Engine**, **V3-002 Autonomous Learning**, **V3-003 Novel Problem Solving**, **V3-004 Recursive Improvement**, **V3-005 Superhuman Competition**, and **V3-006 Independent Qualification**. The ambition is to earn independently verified Level II superhuman domain capability and initial Level III cross-domain evidence. **Neither level, nor AGI/ASI, has been achieved or certified.**

**Explore:** [V3 vision](V3/README.md) · [V3 capability roadmap](V3/CAPABILITY_ROADMAP.md) · [Full roadmap](ROADMAP.md)

'''

ROADMAP_SECTION = '''## V3 — Autonomous Superintelligence Core | Architecture planning

**Mission:** build and independently evaluate operational intelligence that can solve unfamiliar problems, learn persistently, generalize across domains, and improve its own problem-solving methods under bounded authority. This is a future capability target, not an achieved ASI claim.

| Stage | Objective | Evidence required | Status |
| --- | --- | --- | --- |
| **V3-ARCH-001** | Architecture, contracts, V2 integration, threat model and evaluation protocol | Independent challenge and owner approval | In design |
| **V3-001 — Intelligence Engine** | Autonomous reasoning, discovery and verification | Hidden-task baselines and ablation studies | Planned |
| **V3-002 — Autonomous Learning** | Persistent validated learning | Retention, transfer, forgetting and regression tests | Planned |
| **V3-003 — Novel Problem Solving** | End-to-end solutions to unfamiliar tasks | Reproducible held-out task success | Planned |
| **V3-004 — Recursive Improvement** | Bounded proposal/test/rollback of method changes | Independent gains without safety regressions | Planned |
| **V3-005 — Superhuman Competition** | Competitive domain-level evaluation | Frontier AI, specialist algorithms and expert comparisons with fair budgets | Planned |
| **V3-006 — Independent Qualification** | External reproducibility and capability review | Isolated evaluator, leakage controls and independent replication | Planned |

### Evidence targets

- **Level I — Verified Cognitive Capability:** unseen-task solving, learning and retention.
- **Level II — Verified Superhuman Domain Capability:** sustained independently verified advantage in a defined complex domain.
- **Level III — Broad Superintelligence Evidence:** sustained advantages across distinct domains, transfer and verified improvement; not a universal ASI certificate.

**V3 objective:** earn Level II and initial Level III evidence. No levels are currently awarded. Security and operational qualifications remain separate from intelligence qualification.

**Current authorization:** architecture design only. Implementation begins only after independent Architecture Challenge Gate and owner approval.

**Read:** [V3 mission](V3/README.md) · [Detailed capability roadmap](V3/CAPABILITY_ROADMAP.md)

'''

def update_readme(src: str) -> str:
    if '| `V3/` |' not in src:
        marker = '| `V2/` | Selected V2 engineering source, tests and milestone documentation |'
        if marker not in src:
            raise ValueError('README repository layout anchor not found; refusing unsafe edit')
        src = src.replace(marker, marker + '\n| `V3/` | V3 vision, six capability targets and public development roadmap |', 1)
    start = src.find('## V3 — next architecture program')
    if start < 0:
        start = src.find('## V3 — Autonomous Superintelligence Core')
    end = src.find('## Support SKYNET', start)
    if start < 0 or end < 0 or start >= end:
        raise ValueError('README V3/Support section anchors not found; refusing unsafe edit')
    return src[:start] + README_SECTION + src[end:]

def update_roadmap(src: str) -> str:
    start = src.find('## V3 — Autonomous Superintelligence Core')
    end = src.find('## Publication policy', start)
    if start < 0 or end < 0 or start >= end:
        raise ValueError('ROADMAP V3/Publication anchors not found; refusing unsafe edit')
    return src[:start] + ROADMAP_SECTION + src[end:]

def main() -> int:
    try:
        updates = {}
        for name, transform in [('README.md', update_readme), ('ROADMAP.md', update_roadmap)]:
            path = ROOT / name
            original = path.read_text(encoding='utf-8')
            updated = transform(original)
            updates[path] = (original, updated)
        for path, (_, updated) in updates.items():
            path.write_text(updated, encoding='utf-8')
            print(f'UPDATED {path.relative_to(ROOT)}')
        return 0
    except (OSError, ValueError) as exc:
        print(f'ABORTED: {exc}', file=sys.stderr)
        return 1

if __name__ == '__main__':
    raise SystemExit(main())
