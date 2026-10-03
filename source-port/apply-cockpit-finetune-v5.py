#!/usr/bin/env python3
"""Fine-tune the last two cockpit overlays.

Changes only:
- remove the extra +107 that was added to cockpit speed and gear in v4,
  returning them to the pre-v4 alignment (the cockpit-wide +107 from the
  shared instrument wobble remains in place)
- move cockpit damage-unit sprites 29 game pixels left relative to v4
  (+78 instead of +107), keeping the external-view damage HUD untouched
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

    # Damage overlay: keep a partial extra shift, but pull it left from +107 to +78.
    text = replace_once(
        text,
        "                the_wobble_x + gProgram_state.current_car.damage_units[i].x_coord\n"
        "                    + ((gProgram_state.cockpit_on && gBack_screen->width == 854) ? 107 : 0),",
        "                the_wobble_x + gProgram_state.current_car.damage_units[i].x_coord\n"
        "                    + ((gProgram_state.cockpit_on && gBack_screen->width == 854) ? 78 : 0),",
        "cockpit damage-unit fine X",
    )

    # Gear: undo v4's extra +107. the_wobble_x already contains the correct
    # cockpit centering offset from apply-current-test.py.
    text = replace_once(
        text,
        "                the_wobble_x + gProgram_state.current_car.gear_x[gProgram_state.cockpit_on]\n"
        "                    + ((gProgram_state.cockpit_on && gBack_screen->width == 854) ? 107 : 0),",
        "                the_wobble_x + gProgram_state.current_car.gear_x[gProgram_state.cockpit_on],",
        "cockpit gear restore pre-v4 X",
    )

    # Speed image paths (2 occurrences) and digital-number path (1 occurrence):
    # likewise remove only the v4 extra +107.
    old_speed = (
        "                    the_wobble_x + gProgram_state.current_car.speedo_x[gProgram_state.cockpit_on]\n"
        "                        + ((gProgram_state.cockpit_on && gBack_screen->width == 854) ? 107 : 0),"
    )
    new_speed = "                    the_wobble_x + gProgram_state.current_car.speedo_x[gProgram_state.cockpit_on],"
    text = replace_all_exact(text, old_speed, new_speed, 2, "cockpit speed image restore pre-v4 X")

    text = replace_once(
        text,
        "                the_wobble_x + gProgram_state.current_car.speedo_x[gProgram_state.cockpit_on]\n"
        "                    + ((gProgram_state.cockpit_on && gBack_screen->width == 854) ? 107 : 0),",
        "                the_wobble_x + gProgram_state.current_car.speedo_x[gProgram_state.cockpit_on],",
        "cockpit digital speed restore pre-v4 X",
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
    print("Applied final cockpit instrument/damage fine-tuning")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
