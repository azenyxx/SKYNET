# SKYNET v1.0

**Open research and engineering toward Artificial Superintelligence (ASI).**

SKYNET v1.0 brings together a 64-stage research and development program covering cognitive architectures, agent execution, learning interfaces, recursive improvement workflows, distributed runtime infrastructure and systematic validation.

## Repository layout

| Directory | Development program |
| --- | --- |
| `FOUNDATION/` | Cognitive Runtime V1 foundation |
| `COG/` | COG-001–020: cognitive contracts and processing |
| `AGT/` | AGT-001–010: agent systems |
| `LRN/` | LRN-001–008: learning and adaptation |
| `RSI/` | RSI-001–008: recursive improvement workflows |
| `SYS/` | SYS-001–008: runtime infrastructure |
| `VAL/` | VAL-001–010: capability validation |

**Total: 64 numbered development stages.** Each technical section contains source code, tests and one README explaining its role. Historical stage snapshots and the audited runtime are distinguished by directory.

## Engineering status

The v1.0 audited runtime includes task coordination, controlled execution, versioned memory, authorization, evidence and qualification infrastructure. Research components include cognitive plan validation, agent execution contracts, learning evaluation and improvement assessment. Development continues toward deeper integration and native cognitive capabilities.

## Working with the source

Python modules and tests are organized by research program. The audited runtime packages are under `SYS/runtime/src/` and `VAL/runtime/src/`; tests are under the corresponding `runtime/tests/` directories. See `pyproject.toml` for the original runtime tooling. Historical stage snapshots may have distinct import requirements and are not represented as a single installable Python package.

## Roadmap

See [ROADMAP.md](ROADMAP.md) for the ongoing research direction, and [SECURITY.md](SECURITY.md) for vulnerability reporting.

## Support SKYNET

Independent research and development can be supported with Bitcoin donations.

**BTC (Bitcoin mainnet):** `bc1qrxegtdynmn2rnhnu24gqvljlsxn83h5jhhwkk9`

Send only BTC over the Bitcoin mainnet. Donations do not grant ownership or investment rights.

## License

See [LICENSE](LICENSE). Third-party and historically contributed code remains subject to its applicable provenance and licensing terms.
