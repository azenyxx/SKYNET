#!/usr/bin/env python3
"""Read-only SHA-256, ZIP safety, CRC and manifest verifier for SKYNET-style releases.

No extraction or execution of archived content. Standard library only.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import pathlib
import posixpath
import stat
import sys
import zipfile


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def inspect_archive(path: pathlib.Path, expected_sha: str | None = None) -> dict:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    actual = digest.hexdigest()
    errors = []
    if expected_sha and actual.lower() != expected_sha.lower():
        errors.append("archive SHA-256 mismatch")
    paths = set()
    files = {}
    manifests = []
    with zipfile.ZipFile(path) as archive:
        for entry in archive.infolist():
            name = entry.filename
            norm = posixpath.normpath(name.rstrip("/"))
            if (not name or name.startswith("/") or "\\" in name or
                norm == ".." or norm.startswith("../") or
                any(part in ("", ".", "..") for part in name.rstrip("/").split("/"))):
                errors.append(f"unsafe path: {name}")
                continue
            if norm in paths:
                errors.append(f"duplicate path: {norm}")
                continue
            paths.add(norm)
            mode = entry.external_attr >> 16
            if stat.S_ISLNK(mode):
                errors.append(f"symlink: {name}")
                continue
            if entry.is_dir():
                continue
            with archive.open(entry) as stream:
                h = hashlib.sha256()
                for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                    h.update(chunk)
                files[norm] = h.hexdigest()
            if norm.endswith("/MANIFEST.sha256") or norm == "MANIFEST.sha256":
                manifests.append(norm)
        if archive.testzip() is not None:
            errors.append("CRC failure")
        if len(manifests) != 1:
            errors.append(f"expected exactly one MANIFEST.sha256; found {len(manifests)}")
        else:
            manifest_path = manifests[0]
            prefix = posixpath.dirname(manifest_path)
            listed = set()
            for line in archive.read(manifest_path).decode("utf-8").splitlines():
                if not line.strip():
                    continue
                if len(line) < 67 or line[64:66] != "  ":
                    errors.append("malformed manifest line")
                    continue
                digest, rel = line[:64], line[66:]
                if len(digest) != 64 or any(c not in "0123456789abcdefABCDEF" for c in digest):
                    errors.append("invalid manifest digest")
                    continue
                full = posixpath.normpath(posixpath.join(prefix, rel))
                if full in listed:
                    errors.append(f"duplicate manifest entry: {rel}")
                listed.add(full)
                if full not in files:
                    errors.append(f"missing manifest file: {rel}")
                elif files[full].lower() != digest.lower():
                    errors.append(f"manifest hash mismatch: {rel}")
            expected = set(files) - {manifest_path}
            if listed != expected:
                errors.append(f"manifest coverage mismatch: missing={len(expected-listed)}, extra={len(listed-expected)}")
    return {"archive": path.name, "sha256": actual, "size": path.stat().st_size,
            "file_count": len(files), "manifest_count": len(manifests),
            "ok": not errors, "errors": errors}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=pathlib.Path)
    parser.add_argument("--sha256", help="expected release SHA-256")
    args = parser.parse_args()
    try:
        result = inspect_archive(args.archive, args.sha256)
    except (OSError, ValueError, zipfile.BadZipFile, UnicodeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, indent=2))
        return 2
    print(json.dumps(result, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
