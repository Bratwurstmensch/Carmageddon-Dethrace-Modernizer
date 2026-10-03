#!/usr/bin/env python3
"""Final cockpit overlay alignment pass.

Only touches:
- cockpit speed display X
- cockpit gear display X
- cockpit damage-unit overlay X

Everything else from the validated overlay-alignment build is left unchanged.
"""
from pathlib import Path
import sys


def replace_all_exact(text: str, old: str, new: str, expected: int, label: str) -> str:
    count = text.count(old)
    if count != expected:
        raise RuntimeError(f"{label}: expected {expected} matches, found {count}")
    return text.replace(old, new)


def replace_once(text: str, old: str, new: str, label: str) -> str:
    return replace_all_exact(text, old, new, 1, label)


def patch_displays(path: Path) -> None:
    text = path.read_text(encoding="utf-8")

    text = replace_once(
        text,
        "                the_wobble_x + gProgram_state.current_car.damage_units[i].x_coord,",
        "                the_wobble_x + gProgram_state.current_car.damage_units[i].x_coord\n"
        "                    + ((gProgram_state.cockpit_on && gBack_screen->width == 854) ? 107 : 0),",
        "cockpit damage-unit X",
    )

    text = replace_once(
        text,
        "                the_wobble_x + gProgram_state.current_car.gear_x[gProgram_state.cockpit_on],",
        "                the_wobble_x + gProgram_state.current_car.gear_x[gProgram_state.cockpit_on]\n"
        "                    + ((gProgram_state.cockpit_on && gBack_screen->width == 854) ? 107 : 0),",
        "cockpit gear X",
    )

    old_speed = "                    the_wobble_x + gProgram_state.current_car.speedo_x[gProgram_state.cockpit_on],"
    new_speed = (
        "                    the_wobble_x + gProgram_state.current_car.speedo_x[gProgram_state.cockpit_on]\n"
        "                        + ((gProgram_state.cockpit_on && gBack_screen->width == 854) ? 107 : 0),"
    )
    text = replace_all_exact(text, old_speed, new_speed, 2, "cockpit speed image X")

    text = replace_once(
        text,
        "                the_wobble_x + gProgram_state.current_car.speedo_x[gProgram_state.cockpit_on],",
        "                the_wobble_x + gProgram_state.current_car.speedo_x[gProgram_state.cockpit_on]\n"
        "                    + ((gProgram_state.cockpit_on && gBack_screen->width == 854) ? 107 : 0),",
        "cockpit digital speed X",
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
    print("Applied final cockpit speed/gear/damage alignment")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
