#!/usr/bin/env python3
"""Run all published COG-001..007 unittest suites, offline and fail-closed.

This is a developer test launcher, not a security sandbox. It runs the
repository's Python tests and does not install packages or access providers.
"""
from __future__ import annotations

import argparse
import os
import re
from pathlib import Path
import subprocess
import sys

MODULES = tuple(f"cog{number:03d}" for number in range(1, 8))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent,
                        help="Path to cognitive-runtime (default: script directory)")
    args = parser.parse_args()
    root = args.root.resolve()
    paths = [root / name for name in MODULES]
    if any(not path.is_dir() for path in paths):
        print("ERROR: missing COG directory; expected cog001 through cog007", file=sys.stderr)
        return 2
    # Public modules import one another by module name; do not depend on the
    # caller's shell PYTHONPATH or on package discovery across directories.
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join(str(path) for path in paths)
    failures = []
    for name, path in zip(MODULES, paths):
        tests = sorted(path.glob("test_*.py"))
        if not tests:
            print(f"ERROR: {name} contains no test_*.py files", file=sys.stderr)
            failures.append(name)
            continue
        print(f"\n=== {name}: {len(tests)} test file(s) ===", flush=True)
        command = [sys.executable, "-m", "unittest", "discover", "-s", str(path),
                   "-p", "test_*.py", "-v"]
        result = subprocess.run(command, cwd=root, env=env, check=False,
                                capture_output=True, text=True)
        output = result.stdout + result.stderr
        print(output, end="" if output.endswith("\n") else "\n", flush=True)
        counts = re.findall(r"Ran (\d+) tests? in ", output)
        if result.returncode != 0 or not counts or int(counts[-1]) == 0:
            failures.append(name)
    if failures:
        print("\nFAIL: " + ", ".join(failures), file=sys.stderr)
        return 1
    print("\nPASS: all seven public COG test suites completed successfully")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
