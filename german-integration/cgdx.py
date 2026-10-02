#!/usr/bin/env python3
"""CGDX1 source-verified binary delta helper."""

from __future__ import annotations
import argparse
import hashlib
import json
import pathlib
import struct
import sys
import zlib

MAGIC = b"CGDX1\n"

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def create_patch(source: bytes, target: bytes, path: str) -> bytes:
    xor_stream = bytes(
        target[i] ^ (source[i] if i < len(source) else 0)
        for i in range(len(target))
    )
    header = {
        "path": path,
        "codec": "xor+zlib",
        "source_size": len(source),
        "target_size": len(target),
        "source_sha256": sha256_bytes(source),
        "target_sha256": sha256_bytes(target)
    }
    header_bytes = json.dumps(
        header, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return (
        MAGIC
        + struct.pack("<I", len(header_bytes))
        + header_bytes
        + zlib.compress(xor_stream, 9)
    )

def apply_patch(patch: bytes, source: bytes):
    if not patch.startswith(MAGIC):
        raise ValueError("not a CGDX1 patch")
    offset = len(MAGIC)
    if len(patch) < offset + 4:
        raise ValueError("truncated header")
    header_size = struct.unpack("<I", patch[offset:offset + 4])[0]
    offset += 4
    header = json.loads(patch[offset:offset + header_size].decode("utf-8"))
    offset += header_size
    if len(source) != header["source_size"]:
        raise ValueError("source size mismatch")
    if sha256_bytes(source) != header["source_sha256"]:
        raise ValueError("source SHA-256 mismatch")
    xor_stream = zlib.decompress(patch[offset:])
    if len(xor_stream) != header["target_size"]:
        raise ValueError("delta length mismatch")
    target = bytes(
        xor_stream[i] ^ (source[i] if i < len(source) else 0)
        for i in range(len(xor_stream))
    )
    if sha256_bytes(target) != header["target_sha256"]:
        raise ValueError("target SHA-256 mismatch")
    return header, target

def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    create = sub.add_parser("create")
    create.add_argument("source")
    create.add_argument("target")
    create.add_argument("patch")
    create.add_argument("--path", default="")
    apply = sub.add_parser("apply")
    apply.add_argument("patch")
    apply.add_argument("source")
    apply.add_argument("target")
    args = parser.parse_args()

    if args.command == "create":
        source = pathlib.Path(args.source).read_bytes()
        target = pathlib.Path(args.target).read_bytes()
        pathlib.Path(args.patch).write_bytes(
            create_patch(source, target, args.path)
        )
        return 0

    patch = pathlib.Path(args.patch).read_bytes()
    source = pathlib.Path(args.source).read_bytes()
    _, target = apply_patch(patch, source)
    target_path = pathlib.Path(args.target)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_bytes(target)
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print("ERROR:", exc, file=sys.stderr)
        sys.exit(1)
