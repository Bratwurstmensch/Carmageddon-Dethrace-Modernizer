#!/usr/bin/env python3
"""Cockpit final v12 hand-only micro-adjustment on top of stable v11.

Only changes:
- left/right cockpit hand overlays: 4 game pixels further left
  (+192 instead of +196)

Everything else remains exactly as in stable v11.
"""
from pathlib import Path
import sys


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected 1 match, found {count}")
    return text.replace(old, new, 1)


def patch_displays(path: Path) -> None:
    text = path.read_text(encoding="utf-8")

    text = replace_once(
        text,
        "                gProgram_state.current_car.lhands_x[hands_index] + gScreen_wobble_x\n"
        "                    + (gBack_screen->width == 854 ? 196 : 0),",
        "                gProgram_state.current_car.lhands_x[hands_index] + gScreen_wobble_x\n"
        "                    + (gBack_screen->width == 854 ? 192 : 0),",
        "left hand +192",
    )

    text = replace_once(
        text,
        "                gProgram_state.current_car.rhands_x[hands_index] + gScreen_wobble_x\n"
        "                    + (gBack_screen->width == 854 ? 196 : 0),",
        "                gProgram_state.current_car.rhands_x[hands_index] + gScreen_wobble_x\n"
        "                    + (gBack_screen->width == 854 ? 192 : 0),",
        "right hand +192",
    )

    path.write_text(text, encoding="utf-8")


def main() -> int:
    if len(sys.argv) != 2:
        print(f"Usage: {Path(sys.argv[0]).name} /path/to/dethrace-v0.10.1", file=sys.stderr)
        return 2

    root = Path(sys.argv[1]).resolve()
    displays = root / "src/DETHRACE/common/displays.c"
    if not displays.is_file():
        raise FileNotFoundError(displays)

    patch_displays(displays)
    print("Applied v12 hand-only +192 alignment")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
