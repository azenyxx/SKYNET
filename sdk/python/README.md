# SKYNET Public SDK — PUBLIC-002–005

Standalone Python package for **deterministic, offline research fixtures**. It extends the public R2 mock; it does not implement or connect to the private SKYNET Cognitive Core, Governance, Trusted Gateway, PostgreSQL admission, provider systems, or production sandbox.

## Run locally

Requires Python 3.11+.

```bash
cd sdk/python
python -m pip install -e '.[test]'
python -m pytest -q
python -m skynet_public.cli self-test
```

## Python API

```python
from skynet_public import make_request, run, verify
request = make_request("echo", 42)
receipt = run(request)
assert verify(request, receipt)
print(receipt.output_json)
```

## CLI

Generate JSON request and receipt files using the Python API:

```python
from pathlib import Path
from skynet_public import make_request, run
request = make_request("echo", 42)
Path("request.json").write_text(request.model_dump_json())
Path("receipt.json").write_text(run(request).model_dump_json())
```

Then:

```bash
skynet-public validate request.json
skynet-public run request.json
skynet-public verify request.json receipt.json
skynet-public inspect receipt.json
skynet-public self-test
```

## Limits

- `echo` and `noop` only; integer fixture values in [-1,000,000, 1,000,000].
- SHA-256 receipts are local deterministic integrity checks, **not authenticated attestations**.
- No networking, keys, credentials, production execution, or private imports.
- G3 PostgreSQL runtime verification is still `BLOCKED_ENVIRONMENT`.
- No claim of achieved AGI/ASI.
