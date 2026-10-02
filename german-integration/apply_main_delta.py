#!/usr/bin/env python3
"""Apply a German-main-game CGDX release bundle to verified German retail source data."""

from __future__ import annotations
import argparse, hashlib, json, pathlib, shutil, struct, sys, zlib

MAGIC=b"CGDX1\n"

def sha_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def sha_file(p: pathlib.Path) -> str:
    h=hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

def apply_patch(blob: bytes,source: bytes) -> bytes:
    if not blob.startswith(MAGIC):
        raise RuntimeError("bad CGDX1 magic")
    off=len(MAGIC)
    n=struct.unpack("<I",blob[off:off+4])[0]
    off+=4
    meta=json.loads(blob[off:off+n].decode("utf-8"))
    off+=n
    if len(source)!=meta["source_size"] or sha_bytes(source)!=meta["source_sha256"]:
        raise RuntimeError(f"source mismatch: {meta['path']}")
    x=zlib.decompress(blob[off:])
    if len(x)!=meta["target_size"]:
        raise RuntimeError(f"delta length mismatch: {meta['path']}")
    target=bytes(x[i] ^ (source[i] if i<len(source) else 0) for i in range(len(x)))
    if sha_bytes(target)!=meta["target_sha256"]:
        raise RuntimeError(f"target verification failed: {meta['path']}")
    return target

def canonical_identity(root: pathlib.Path) -> tuple[int,str]:
    rows=[]
    for p in root.rglob("*"):
        if p.is_file():
            rel=str(p.relative_to(root)).replace("/","\\").lower()
            rows.append((rel,sha_file(p)))
    rows.sort(key=lambda x:x[0])
    payload="".join(f"{p}\t{h}\n" for p,h in rows).encode("utf-8")
    return len(rows),hashlib.sha256(payload).hexdigest()

def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--source-data",required=True,type=pathlib.Path)
    ap.add_argument("--bundle",required=True,type=pathlib.Path)
    ap.add_argument("--output",required=True,type=pathlib.Path)
    args=ap.parse_args()

    manifest=json.loads((args.bundle/"manifest.json").read_text(encoding="utf-8"))
    if args.output.exists():
        shutil.rmtree(args.output)
    args.output.mkdir(parents=True)

    for e in manifest["files"]:
        rel=pathlib.Path(e["path"].replace("\\","/"))
        source=args.source_data/rel
        if not source.is_file():
            raise FileNotFoundError(source)
        sb=source.read_bytes()
        if len(sb)!=e["source_size"] or sha_bytes(sb)!=e["source_sha256"]:
            raise RuntimeError(f"source verification failed: {e['path']}")
        dest=args.output/rel
        dest.parent.mkdir(parents=True,exist_ok=True)
        if e["mode"]=="copy":
            dest.write_bytes(sb)
        else:
            dest.write_bytes(apply_patch((args.bundle/e["patch"]).read_bytes(),sb))
        if len(dest.read_bytes())!=e["target_size"] or sha_file(dest)!=e["target_sha256"]:
            raise RuntimeError(f"final file verification failed: {e['path']}")

    count,identity=canonical_identity(args.output)
    if count!=manifest["file_count"] or identity!=manifest["target_manifest_identity"]:
        raise RuntimeError(f"final set mismatch: {count} {identity}")
    print(f"OK: rebuilt {count} files; identity {identity}")
    return 0

if __name__=="__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}",file=sys.stderr)
        raise SystemExit(1)
