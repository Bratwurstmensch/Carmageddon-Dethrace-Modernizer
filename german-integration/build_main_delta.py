#!/usr/bin/env python3
"""Build a source-verified German-main-game CGDX bundle.

Development helper. It expects a legally obtained German retail DATA tree plus the
privately validated final German target tree. The target assets are not stored in
this repository; only the generated binary deltas are suitable for release packaging.
"""

from __future__ import annotations
import argparse, hashlib, json, pathlib, shutil, struct, zlib

MAGIC=b"CGDX1\n"
EXPECTED_COUNT=250
EXPECTED_IDENTITY="7cb50ad5e3b1bfca6a021ccc8210b975f27419446286c8441e34800da971fd27"

def sha_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def sha_file(p: pathlib.Path) -> str:
    h=hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

def canonical_identity(root: pathlib.Path) -> tuple[int,str]:
    rows=[]
    for p in root.rglob("*"):
        if p.is_file():
            rel=str(p.relative_to(root)).replace("/","\\").lower()
            rows.append((rel,sha_file(p)))
    rows.sort(key=lambda x:x[0])
    payload="".join(f"{p}\t{h}\n" for p,h in rows).encode("utf-8")
    return len(rows),hashlib.sha256(payload).hexdigest()

def create_patch(source: bytes,target: bytes,path: str) -> bytes:
    x=bytes(target[i] ^ (source[i] if i<len(source) else 0) for i in range(len(target)))
    meta={
        "path":path,
        "codec":"xor+zlib",
        "source_size":len(source),
        "target_size":len(target),
        "source_sha256":sha_bytes(source),
        "target_sha256":sha_bytes(target),
    }
    hb=json.dumps(meta,separators=(",",":")).encode("utf-8")
    return MAGIC+struct.pack("<I",len(hb))+hb+zlib.compress(x,9)

def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--source-data",required=True,type=pathlib.Path)
    ap.add_argument("--target-data",required=True,type=pathlib.Path)
    ap.add_argument("--output",required=True,type=pathlib.Path)
    args=ap.parse_args()

    count,identity=canonical_identity(args.target_data)
    if count!=EXPECTED_COUNT or identity!=EXPECTED_IDENTITY:
        raise RuntimeError(f"private target is not the validated final set: {count} {identity}")

    if args.output.exists():
        shutil.rmtree(args.output)
    (args.output/"patches").mkdir(parents=True)

    entries=[]
    for target in sorted(args.target_data.rglob("*")):
        if not target.is_file():
            continue
        rel=target.relative_to(args.target_data)
        source=args.source_data/rel
        if not source.is_file():
            raise FileNotFoundError(f"German retail source file missing: {source}")
        sb=source.read_bytes()
        tb=target.read_bytes()
        entry={
            "path":str(rel).replace("/","\\"),
            "source_size":len(sb),
            "source_sha256":sha_bytes(sb),
            "target_size":len(tb),
            "target_sha256":sha_bytes(tb),
        }
        if sb==tb:
            entry["mode"]="copy"
        else:
            patch_rel=pathlib.Path("patches")/pathlib.Path(str(rel)+".cgdx")
            patch_path=args.output/patch_rel
            patch_path.parent.mkdir(parents=True,exist_ok=True)
            patch_path.write_bytes(create_patch(sb,tb,entry["path"]))
            entry["mode"]="cgdx"
            entry["patch"]=patch_rel.as_posix()
        entries.append(entry)

    manifest={
        "format":"carmageddon-main-german-delta-v0.1",
        "source_profile":"German retail DATA tree",
        "file_count":len(entries),
        "copy_count":sum(e["mode"]=="copy" for e in entries),
        "delta_count":sum(e["mode"]=="cgdx" for e in entries),
        "target_manifest_identity":EXPECTED_IDENTITY,
        "files":entries,
    }
    (args.output/"manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
    print(f"OK: {manifest['copy_count']} exact copies, {manifest['delta_count']} deltas.")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
