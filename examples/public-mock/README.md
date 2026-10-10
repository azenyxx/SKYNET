# SKYNET R2 — Public Developer Foundation

A standalone, MIT-licensed deterministic mock protocol for contributors to the [SKYNET research project](https://github.com/azenyxx/SKYNET). This **is not** the internal Trusted Gateway contract and is not wire-compatible with the private runtime.

This public example supports canonical JSON fixtures, bounded echo/noop operations, SHA-256 request/output binding, replay and verification. It contains **no** protected grant or lease fields, production execution, provider connections, sandbox isolation, internal cognitive algorithms or private source history.

## Quick start

```bash
python -m pip install -e '.[test]'
python -m pytest tests -q
```

## Research status

SKYNET explores architectural foundations of advanced AI and ASI. **No AGI or ASI capability has been demonstrated.** PostgreSQL G3 verification remains blocked by the original execution environment. Tests in this package do not establish production security.

## License

MIT — see [LICENSE](LICENSE). Copyright (c) 2026 Aleksandr Kravtsov. Only this released public package is covered; private SKYNET components are not distributed here.
