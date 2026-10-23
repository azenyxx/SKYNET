"""Run the public example tests without pytest or third-party packages."""
from pathlib import Path
import runpy
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
passed = 0
for path in sorted((Path(__file__).resolve().parent / "tests").glob("test_lrn*.py")):
    namespace = runpy.run_path(str(path))
    for name, fn in sorted(namespace.items()):
        if name.startswith("test_") and callable(fn):
            fn()
            passed += 1
print(f"{passed} public demonstration tests passed")
