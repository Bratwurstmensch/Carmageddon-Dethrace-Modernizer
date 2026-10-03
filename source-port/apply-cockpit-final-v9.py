#!/usr/bin/env python3
"""Final cockpit v9 visual polish on top of stable v8.

Only changes:
- hands: 6 game pixels further left (+202 instead of +208)
- digital tacho/rev bar: +75 game pixels in cockpit so it aligns under
  the already-correct green speed digits

No stability logic or any other validated positions are changed.
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
        "                    + (gBack_screen->width == 854 ? 208 : 0),",
        "                gProgram_state.current_car.lhands_x[hands_index] + gScreen_wobble_x\n"
        "                    + (gBack_screen->width == 854 ? 202 : 0),",
        "left hand +202",
    )

    text = replace_once(
        text,
        "                gProgram_state.current_car.rhands_x[hands_index] + gScreen_wobble_x\n"
        "                    + (gBack_screen->width == 854 ? 208 : 0),",
        "                gProgram_state.current_car.rhands_x[hands_index] + gScreen_wobble_x\n"
        "                    + (gBack_screen->width == 854 ? 202 : 0),",
        "right hand +202",
    )

    # Only the digital/linear tacho bar path. Analog tacho geometry is already
    # aligned by the shared cockpit wobble offset and should not move.
    text = replace_once(
        text,
        """                gBack_screen,
                the_wobble_x + gProgram_state.current_car.tacho_x[gProgram_state.cockpit_on],
                the_wobble_y + gProgram_state.current_car.tacho_y[gProgram_state.cockpit_on],
                gProgram_state.current_car.tacho_image[gProgram_state.cockpit_on],
                0,
                0,
                ((gCar_to_view->revs - 1.0) / (double)gCar_to_view->red_line * (double)gProgram_state.current_car.tacho_image[gProgram_state.cockpit_on]->width + 1.0),
                gProgram_state.current_car.tacho_image[gProgram_state.cockpit_on]->height);""",
        """                gBack_screen,
                the_wobble_x + gProgram_state.current_car.tacho_x[gProgram_state.cockpit_on]
                    + ((gProgram_state.cockpit_on && gBack_screen->width == 854) ? 75 : 0),
                the_wobble_y + gProgram_state.current_car.tacho_y[gProgram_state.cockpit_on],
                gProgram_state.current_car.tacho_image[gProgram_state.cockpit_on],
                0,
                0,
                ((gCar_to_view->revs - 1.0) / (double)gCar_to_view->red_line * (double)gProgram_state.current_car.tacho_image[gProgram_state.cockpit_on]->width + 1.0),
                gProgram_state.current_car.tacho_image[gProgram_state.cockpit_on]->height);""",
        "digital tacho bar +75",
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
    print("Applied v9 hand +202 and digital tacho-bar +75 polish")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
