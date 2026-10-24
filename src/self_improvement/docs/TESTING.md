# Tests and reproducibility

The original `test_*.py` files are included unchanged. Packaging verified Python syntax only, **not runtime behavior**. Historical reported tests are not independent reruns.

Prerequisites: Python 3.12+ and original AGT/LRN predecessor modules where referenced. These missing modules are **not** substituted with stubs, because doing so would misrepresent integration.

Example after providing legitimate predecessor modules and arranging `PYTHONPATH` to include each stage's `src` and `tests` directories:

```bash
python -m unittest discover -s tests/01-RSI-001 -p 'test_*.py' -v
```

Some tests import tests from previous stages or unbundled modules. Without those dependencies, import errors are expected. Review imports and provide the original predecessor modules before running the complete suite. Do not interpret an import failure as a test of RSI semantics.

For dependency-free static syntax validation:

```bash
python - <<'PY'
import ast, pathlib
files = sorted(pathlib.Path('.').rglob('*.py'))
for p in files:
    ast.parse(p.read_text(encoding='utf-8'), filename=str(p))
print(f'Parsed {len(files)} Python files')
PY
```
