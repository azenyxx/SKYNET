# Manual upload — keep R1/R2 untouched

Upload the contents of this archive **relative to the repository root**:

- `sdk/python/...`
- `.github/workflows/public-python-ci.yml`
- `EXPORT_REVIEW.md` (optional: place under `sdk/python/EXPORT_REVIEW.md` to avoid root clutter)

Do not upload the ZIP as a single file. Do not replace root `README.md`, `LICENSE`, `SECURITY.md`, or existing `examples/public-mock/`.

Suggested commit: `feat: add SKYNET PUBLIC-002-005 Python SDK and CI`

Before tagging v0.2.0, verify GitHub Actions runs on Python 3.11 and 3.12, and confirm the `main` branch has the expected files.

The pre-existing `feature/public-002-005` branch is **not** the authoritative source for this archive. Inspect or discard that branch separately; never merge it blindly.
