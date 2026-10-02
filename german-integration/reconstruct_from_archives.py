#!/usr/bin/env python3
"""Reconstruct the validated German target sets from private archived patch packages.

Development/audit helper only. The patch ZIPs contain game assets and are intentionally
not stored in the public repository. This script overlays their Payload/DATA files in
known-good order and verifies the complete result by a canonical manifest identity.
"""
from __future__ import annotations
import argparse, hashlib, pathlib, shutil, sys, zipfile

MAIN_STACK = [
    "Carmageddon-German-Uncut-Dethrace-v1.6.zip",
    "Carmageddon-German-Uncut-v1.6a-RaceCards.zip",
    "Carmageddon-German-Uncut-v1.6b-Resttext.zip",
    "Carmageddon-German-Uncut-v1.6c-PartsShop.zip",
]
SPLAT_STACK = [
    "Carmageddon-SplatPack-German-Uncut-v0.1-Core.zip",
    "Carmageddon-SplatPack-German-Uncut-v0.1a-SoundRestore.zip",
    "Carmageddon-SplatPack-German-Uncut-v0.2-KeynamesFix.zip",
    "Carmageddon-SplatPack-German-Uncut-v0.2-Repair-Reapply.zip",
    "Carmageddon-SplatPack-German-Uncut-v0.3-Rennen.zip",
    "Carmageddon-SplatPack-German-Uncut-v0.4-Opponents.zip",
    "Carmageddon-SplatPack-German-Uncut-v0.5-Powerups.zip",
    "Carmageddon-SplatPack-German-Uncut-v0.6-Keynames.zip",
    "Carmageddon-SplatPack-German-Uncut-v0.7-TextCleanup.zip",
    "Carmageddon-SplatPack-German-Uncut-v0.8-RaceCards.zip",
    "Carmageddon-SplatPack-German-Uncut-v0.9-GermanSpeech.zip",
    "Carmageddon-SplatPack-German-Uncut-v0.10-PartsShop.zip",
    "Carmageddon-SplatPack-German-Uncut-v0.11-TransitionCleanup.zip",
    "Carmageddon-SplatPack-German-Uncut-v0.12-SpecialScreens.zip",
    "Carmageddon-SplatPack-German-Uncut-v0.13-FinalGraphics.zip",
]

MAIN_IDENTITY = "7cb50ad5e3b1bfca6a021ccc8210b975f27419446286c8441e34800da971fd27"
SPLAT_IDENTITY = "19832c80860d00393b20ade338c09f8f30f65a614243a10d59d71a18544964fe"

def sha256_file(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def payload_rel(name: str):
    n = name.replace("\\", "/")
    if n.endswith("/") or "/Payload/" not in "/" + n:
        return None
    tail = ("/" + n).split("/Payload/", 1)[1]
    up = tail.upper()
    if up.startswith("DATA/"):
        tail = tail[5:]
    elif up.startswith("CARSPLAT/DATA/"):
        tail = tail[len("CARSPLAT/DATA/"):]
    else:
        return None
    return pathlib.PurePosixPath(tail)

def overlay(stack_dir: pathlib.Path, stack: list[str], output: pathlib.Path) -> None:
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    for name in stack:
        zpath = stack_dir / name
        if not zpath.is_file():
            raise FileNotFoundError(zpath)
        with zipfile.ZipFile(zpath) as z:
            for member in z.namelist():
                rel = payload_rel(member)
                if rel is None:
                    continue
                dest = output / pathlib.Path(*rel.parts)
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(z.read(member))

def canonical_identity(output: pathlib.Path) -> tuple[int, str]:
    rows = []
    for p in output.rglob("*"):
        if p.is_file():
            rel = str(p.relative_to(output)).replace("/", "\\").lower()
            rows.append((rel, sha256_file(p)))
    rows.sort(key=lambda x: x[0])
    payload = "".join(f"{rel}\t{sha}\n" for rel, sha in rows).encode("utf-8")
    return len(rows), hashlib.sha256(payload).hexdigest()

def verify_identity(output: pathlib.Path, expected_count: int, expected_identity: str) -> None:
    count, identity = canonical_identity(output)
    if count != expected_count:
        raise RuntimeError(f"file-count mismatch: expected {expected_count}, got {count}")
    if identity != expected_identity:
        raise RuntimeError(
            f"manifest identity mismatch: expected {expected_identity}, got {identity}"
        )
    print(f"Verified {count} files; manifest identity {identity}")

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("package_dir", type=pathlib.Path)
    ap.add_argument("output_dir", type=pathlib.Path)
    args = ap.parse_args()

    main_out = args.output_dir / "MAIN"
    splat_out = args.output_dir / "SPLAT"
    overlay(args.package_dir, MAIN_STACK, main_out)
    overlay(args.package_dir, SPLAT_STACK, splat_out)
    verify_identity(main_out, 250, MAIN_IDENTITY)
    verify_identity(splat_out, 275, SPLAT_IDENTITY)
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
