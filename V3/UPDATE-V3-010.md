# SKYNET V3 — Public Update 010

**Date:** 2026-11-22  
**Topic:** Cognitive PoC planning — auditable scenario accounting

This minor public update provides a dependency-free, illustrative budget validator for three preliminary Cognitive Proof-of-Concept funding scenarios: **Lean ($140K / 3 months)**, **Base ($320K / 4 months)** and **Extended ($550K / 6 months)**. These are *proposed planning estimates*, not raised capital, approved purchase orders or externally confirmed vendor prices.

The example verifies that each scenario balances across personnel, compute/infrastructure, and reviews/reserve. It includes explicit line items, avoids floats for USD accounting, and rejects malformed or duplicated expense keys. Run `python3 -m unittest discover -s V3/tests -p 'test_poc_budget_public.py' -v` from repository root.

The original $2.1M pre-seed is an **unfunded proposed raise** distinct from these optional PoC scenarios. No new cognitive capability or qualification is claimed. Private SKYNET implementations and experiment evidence are not distributed.
