# SKYNET V3 — Public Release Checklist

- [ ] Review the complete staged diff and confirm no private module, internal schema, execution parameters or proprietary comments are exposed.
- [ ] Confirm public results against archived experiment evidence; do not generalize from single scenarios.
- [ ] Run the eight standalone tests and verify SHA-256 manifest.
- [ ] Run a secret scanner on staged files and inspect git history if sensitive data was ever committed.
- [ ] Confirm the repository license and disclosure permissions.
- [ ] Check README has exactly one V3 section; do not append a duplicate legacy section.
- [ ] Confirm production witness deployment and Python 3.13.15 are NOT represented as verified.
- [ ] Owner approval of the final staged diff before push.
