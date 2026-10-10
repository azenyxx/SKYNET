"""Offline-only CLI. Input is a local JSON file; no network calls."""
import argparse
import json
from pathlib import Path
from .protocol import MockRequest, MockResult, verify
from .sdk import make_request, run, inspect

MAX_FILE_BYTES = 16384

def load(path: str) -> str:
    p = Path(path)
    if p.stat().st_size > MAX_FILE_BYTES:
        raise ValueError("input file too large")
    return p.read_text(encoding="utf-8")

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="skynet-public")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("validate", "run", "verify", "inspect"):
        command = commands.add_parser(name)
        command.add_argument("input")
        if name == "verify":
            command.add_argument("receipt")
    commands.add_parser("self-test")
    args = parser.parse_args(argv)
    if args.command == "self-test":
        req = make_request("echo", 42)
        assert verify(req, run(req))
        print("PASS")
        return 0
    if args.command == "inspect":
        result = inspect(MockResult.model_validate_json(load(args.input)))
    else:
        request = MockRequest.model_validate_json(load(args.input))
        if args.command == "validate":
            result = {"valid": True}
        elif args.command == "run":
            result = run(request).model_dump()
        else:
            result = {"verified": verify(request, MockResult.model_validate_json(load(args.receipt)))}
    print(json.dumps(result, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
