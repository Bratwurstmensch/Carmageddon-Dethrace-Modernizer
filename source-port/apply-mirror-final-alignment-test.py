#!/usr/bin/env python3
"""Final micro-alignment test for the 16:9 cockpit rear-view render area.

The validated widescreen chain currently uses a +173 logical-pixel X offset for
the OpenGL/3DFX rear-view render surface. User testing shows the 3D mirror image
is still very slightly left of the cockpit mirror frame.

This isolated test moves only the 16:9 rear-view render surface 3 logical pixels
to the right: +173 -> +176. 4:3 and all other rendering are untouched.
"""
from pathlib import Path
import sys


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: apply-mirror-final-alignment-test.py <dethrace-source>")

    root = Path(sys.argv[1])
    path = root / "src" / "DETHRACE" / "common" / "graphics.c"
    text = path.read_text(encoding="utf-8")

    text = replace_once(
        text,
        "        gRearview_screen->base_x = MAX(0, gScreen_wobble_x + gProgram_state.current_car.mirror_left\n"
        "            + (gBack_screen->width == 854 ? 173 : 0));",
        "        gRearview_screen->base_x = MAX(0, gScreen_wobble_x + gProgram_state.current_car.mirror_left\n"
        "            + (gBack_screen->width == 854 ? 176 : 0));",
        "rearview fixed-bugs X micro-alignment",
    )

    text = replace_once(
        text,
        "        gRearview_screen->base_x = gScreen_wobble_x + gProgram_state.current_car.mirror_left\n"
        "            + (gBack_screen->width == 854 ? 173 : 0);",
        "        gRearview_screen->base_x = gScreen_wobble_x + gProgram_state.current_car.mirror_left\n"
        "            + (gBack_screen->width == 854 ? 176 : 0);",
        "rearview legacy X micro-alignment",
    )

    path.write_text(text, encoding="utf-8")
    print("Applied final rear-view 16:9 X micro-alignment: +173 -> +176")


if __name__ == "__main__":
    raise SystemExit(main())
