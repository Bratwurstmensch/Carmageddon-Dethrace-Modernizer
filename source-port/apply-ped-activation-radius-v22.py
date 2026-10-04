#!/usr/bin/env python3
"""Pedestrian visibility/activation A/B test v22.

Starting from stable v21:
- keep the risky render-only distant-pedestrian path disabled;
- keep the original 100-entry lollipop queue;
- expand only the normal pedestrian activation radius from 11 to 30 units.

This uses the game's normal DoPedestrian/MungePedModel path instead of a
separate render-only pass, so it should reduce obvious pop-in without the
BRender list corruption seen in v19/v20.
"""
from pathlib import Path
import sys

def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected 1 match, found {count}")
    return text.replace(old, new, 1)

def main() -> int:
    if len(sys.argv) != 2:
        print(f"Usage: {Path(sys.argv[0]).name} /path/to/dethrace-v0.10.1", file=sys.stderr)
        return 2
    root = Path(sys.argv[1]).resolve()
    path = root / "src/DETHRACE/common/pedestrn.c"
    if not path.is_file():
        raise FileNotFoundError(path)
    text = path.read_text(encoding="utf-8")
    text = replace_once(
        text,
        "#define ACTIVE_PED_DXDZ 11.f",
        "#define ACTIVE_PED_DXDZ 30.f",
        "pedestrian activation radius",
    )
    path.write_text(text, encoding="utf-8")
    print("Applied v22 normal pedestrian activation radius: 30 units")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
