# Public Atomic CAS Demo

A small standalone **synthetic** Python/SQLite example demonstrating revision-based compare-and-swap, unique operation/nonce, exact replay, atomic receipt/audit writes, rollback and competing writers. Standard library only.

This is a **new public teaching example**, not a copy of the private SKYNET BAA implementation. It includes **no private SKYNET protocols, production configuration, authority credentials, private keys, cryptographic approval system, or operational authorization**.

Run from this directory:

```bash
python3 -m unittest discover -s tests -v
```

Limitations: this demo has **no authentication or authorization**, no trusted clock, no revocation provenance, and no production execution capability. SQLite results do not establish PostgreSQL runtime correctness or crash/power-loss guarantees. Do not use as production security infrastructure.

MIT License. Copyright (c) 2026 SKYNET contributors.
