"""Run standalone examples without exposing private implementation."""
from pathlib import Path
import subprocess
import sys

base = Path(__file__).resolve().parent
for folder in sorted(base.glob("AGT-*")):
    if not folder.is_dir():
        continue
    print(f"\n== {folder.name} ==", flush=True)
    result = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", str(folder), "-p", "test_*.py"], check=False)
    if result.returncode:
        sys.exit(result.returncode)
print("All public example tests passed.")
