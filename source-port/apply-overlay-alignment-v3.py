#!/usr/bin/env python3
"""Fine-tune remaining widescreen overlays after the validated draw-distance/video build.

Only touches:
- cockpit hand X placement
- rear-view mirror framebuffer X placement
- flashing map checkpoint X placement

Does NOT touch the 16:9 world viewport, cockpit artwork, damage HUD, A/P/O,
draw distance, controller mappings, or cutscenes.
"""
from pathlib import Path
import sys


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)


def patch_displays(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = replace_once(
        text,
        "                gProgram_state.current_car.lhands_x[hands_index] + gScreen_wobble_x\n"
        "                    + (gBack_screen->width == 854 ? 107 : 0),",
        "                gProgram_state.current_car.lhands_x[hands_index] + gScreen_wobble_x\n"
        "                    + (gBack_screen->width == 854 ? 214 : 0),",
        "left cockpit hand X",
    )
    text = replace_once(
        text,
        "                gProgram_state.current_car.rhands_x[hands_index] + gScreen_wobble_x\n"
        "                    + (gBack_screen->width == 854 ? 107 : 0),",
        "                gProgram_state.current_car.rhands_x[hands_index] + gScreen_wobble_x\n"
        "                    + (gBack_screen->width == 854 ? 214 : 0),",
        "right cockpit hand X",
    )
    path.write_text(text, encoding="utf-8")


def patch_graphics(path: Path) -> None:
    text = path.read_text(encoding="utf-8")

    text = replace_once(
        text,
        "        gRearview_screen->base_x = MAX(0, gScreen_wobble_x + gProgram_state.current_car.mirror_left\n"
        "            + (gBack_screen->width == 854 ? 107 : 0));",
        "        gRearview_screen->base_x = MAX(0, gScreen_wobble_x + gProgram_state.current_car.mirror_left\n"
        "            + (gBack_screen->width == 854 ? 173 : 0));",
        "rearview fixed-bugs X alignment",
    )
    text = replace_once(
        text,
        "        gRearview_screen->base_x = gScreen_wobble_x + gProgram_state.current_car.mirror_left\n"
        "            + (gBack_screen->width == 854 ? 107 : 0);",
        "        gRearview_screen->base_x = gScreen_wobble_x + gProgram_state.current_car.mirror_left\n"
        "            + (gBack_screen->width == 854 ? 173 : 0);",
        "rearview legacy X alignment",
    )

    old_cp = """                DimRectangle(gBack_screen,
                    2 * gCurrent_race.checkpoints[pIndex].map_left[0],
                    2 * gCurrent_race.checkpoints[pIndex].map_top[0] + HIRES_Y_OFFSET,
                    2 * gCurrent_race.checkpoints[pIndex].map_right[0],
                    2 * gCurrent_race.checkpoints[pIndex].map_bottom[0] + HIRES_Y_OFFSET,
                    0);"""
    new_cp = """                DimRectangle(gBack_screen,
                    2 * gCurrent_race.checkpoints[pIndex].map_left[0] + (gBack_screen->width == 854 ? 107 : 0),
                    2 * gCurrent_race.checkpoints[pIndex].map_top[0] + HIRES_Y_OFFSET,
                    2 * gCurrent_race.checkpoints[pIndex].map_right[0] + (gBack_screen->width == 854 ? 107 : 0),
                    2 * gCurrent_race.checkpoints[pIndex].map_bottom[0] + HIRES_Y_OFFSET,
                    0);"""
    text = replace_once(text, old_cp, new_cp, "flashing map checkpoint X alignment")

    path.write_text(text, encoding="utf-8")


def main() -> int:
    if len(sys.argv) != 2:
        print(f"Usage: {Path(sys.argv[0]).name} /path/to/dethrace-v0.10.1", file=sys.stderr)
        return 2

    root = Path(sys.argv[1]).resolve()
    displays = root / "src/DETHRACE/common/displays.c"
    graphics = root / "src/DETHRACE/common/graphics.c"

    for path in (displays, graphics):
        if not path.is_file():
            raise FileNotFoundError(path)

    patch_displays(displays)
    patch_graphics(graphics)

    print("Applied cockpit hand, rear-view mirror and flashing map checkpoint alignment fixes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
