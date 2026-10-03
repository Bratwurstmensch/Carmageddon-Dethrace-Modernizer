#!/usr/bin/env python3
"""Final v7 cockpit micro-adjustment.

Only changes:
- move both cockpit hand overlays 6 game pixels left (+208 instead of +214)
- move cockpit damage-unit overlay 4 game pixels right (+74 instead of +70)

Speed/gear and all other validated fixes remain untouched.
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
        "                    + (gBack_screen->width == 854 ? 214 : 0),",
        "                gProgram_state.current_car.lhands_x[hands_index] + gScreen_wobble_x\n"
        "                    + (gBack_screen->width == 854 ? 208 : 0),",
        "left cockpit hand X +208",
    )

    text = replace_once(
        text,
        "                gProgram_state.current_car.rhands_x[hands_index] + gScreen_wobble_x\n"
        "                    + (gBack_screen->width == 854 ? 214 : 0),",
        "                gProgram_state.current_car.rhands_x[hands_index] + gScreen_wobble_x\n"
        "                    + (gBack_screen->width == 854 ? 208 : 0),",
        "right cockpit hand X +208",
    )

    text = replace_once(
        text,
        "                the_wobble_x + gProgram_state.current_car.damage_units[i].x_coord\n"
        "                    + ((gProgram_state.cockpit_on && gBack_screen->width == 854) ? 70 : 0),",
        "                the_wobble_x + gProgram_state.current_car.damage_units[i].x_coord\n"
        "                    + ((gProgram_state.cockpit_on && gBack_screen->width == 854) ? 74 : 0),",
        "cockpit damage-unit X +74",
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
    print("Applied v7 cockpit hand +208 and damage +74 micro-adjustment")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
