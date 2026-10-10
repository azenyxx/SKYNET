# R2 release review

- Source baseline: SKYNET-005-G2-HANDOFF, expected SHA-256 `1916a76262fda022e7fa8e9a3b138a51f2ad2fe81360739adfe8db44522ebdd3`.
- This package is **new standalone public mock code**, inspired by the approved G2 deterministic fixture concept. It is **not** a direct export or wire-compatible subset of private Gateway DTOs.
- Excluded: `grant_id`, `lease_id`, `fence`, `stop_epoch`, `reservation_id`, internal phases, protected SQL, Cognitive Core, governance, execution services, private tests, credentials, private Git history.
- Python package imports only Python standard library and Pydantic. Tests additionally require pytest.
- No PostgreSQL runtime, host sandbox, external providers or network execution exercised.
- MIT license included following project owner's confirmation of rights and public-component licensing. Third-party dependencies retain their own licenses.
- Security/IP review is scoped to this generated package, not a guarantee against all risks.
- Upload files to the existing repository as an additional commit, not by replacing R1 files. The `README.md` and `LICENSE` in this ZIP are reference materials; reconcile them with existing root files before merging.
