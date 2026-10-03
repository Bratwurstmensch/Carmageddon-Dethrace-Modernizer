#!/usr/bin/env python3
"""Final v6 cockpit fine-tune.

Only changes:
- cockpit gear X: +75 game pixels
- cockpit speed display X: +75 game pixels
- cockpit damage-unit overlay X: +70 instead of +78

All other validated Modernizer fixes remain untouched.
"""
from pathlib import Path
import sys


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected 1 match, found {count}")
    return text.replace(old, new, 1)


def replace_all_exact(text: str, old: str, new: str, expected: int, label: str) -> str:
    count = text.count(old)
    if count != expected:
        raise RuntimeError(f"{label}: expected {expected} matches, found {count}")
    return text.replace(old, new)


def patch_displays(path: Path) -> None:
    text = path.read_text(encoding="utf-8")

    text = replace_once(
        text,
        "                the_wobble_x + gProgram_state.current_car.damage_units[i].x_coord\n"
        "                    + ((gProgram_state.cockpit_on && gBack_screen->width == 854) ? 78 : 0),",
        "                the_wobble_x + gProgram_state.current_car.damage_units[i].x_coord\n"
        "                    + ((gProgram_state.cockpit_on && gBack_screen->width == 854) ? 70 : 0),",
        "cockpit damage-unit X +70",
    )

    text = replace_once(
        text,
        "                the_wobble_x + gProgram_state.current_car.gear_x[gProgram_state.cockpit_on],",
        "                the_wobble_x + gProgram_state.current_car.gear_x[gProgram_state.cockpit_on]\n"
        "                    + ((gProgram_state.cockpit_on && gBack_screen->width == 854) ? 75 : 0),",
        "cockpit gear X +75",
    )

    old_speed_image = "                    the_wobble_x + gProgram_state.current_car.speedo_x[gProgram_state.cockpit_on],"
    new_speed_image = (
        "                    the_wobble_x + gProgram_state.current_car.speedo_x[gProgram_state.cockpit_on]\n"
        "                        + ((gProgram_state.cockpit_on && gBack_screen->width == 854) ? 75 : 0),"
    )
    text = replace_all_exact(
        text,
        old_speed_image,
        new_speed_image,
        2,
        "cockpit speed image X +75",
    )

    text = replace_once(
        text,
        "                the_wobble_x + gProgram_state.current_car.speedo_x[gProgram_state.cockpit_on],",
        "                the_wobble_x + gProgram_state.current_car.speedo_x[gProgram_state.cockpit_on]\n"
        "                    + ((gProgram_state.cockpit_on && gBack_screen->width == 854) ? 75 : 0),",
        "cockpit digital speed X +75",
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
    print("Applied v6 cockpit speed/gear +75 and damage +70 fine-tune")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
