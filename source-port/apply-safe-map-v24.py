#!/usr/bin/env python3
"""Safe v24 map-only alignment patch.

Starting from the known-stable pre-cockpit draw-distance baseline:
- center the full-screen map in 854x480;
- center map render/blip coordinates by +107 on 854-wide output;
- center the flashing checkpoint dim rectangle by +107.

Deliberately does NOT touch cockpit artwork, cockpit 3D viewport, rear-view
render targets, mirror placement, hands, instruments, damage HUD, draw
distance, pedestrian rendering, or controller mappings.
"""
from pathlib import Path
import sys


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected 1 match, found {count}")
    return text.replace(old, new, 1)


def patch_graphics(path: Path) -> None:
    text = path.read_text(encoding="utf-8")

    text = replace_once(
        text,
        "        gMap_render_x_i *= 2;\n        gMap_render_y_i = (gMap_render_y_i * 2) + HIRES_Y_OFFSET;",
        "        gMap_render_x_i *= 2;\n"
        "        if (gGraf_specs[gGraf_spec_index].total_width == 854) {\n"
        "            gMap_render_x_i += 107;\n"
        "        }\n"
        "        gMap_render_y_i = (gMap_render_y_i * 2) + HIRES_Y_OFFSET;",
        "map render inset X centering",
    )

    text = replace_once(
        text,
        "        map_pos.v[0] = map_pos.v[0] * 2.f;\n        map_pos.v[1] = map_pos.v[1] * 2.f + HIRES_Y_OFFSET;",
        "        map_pos.v[0] = map_pos.v[0] * 2.f + (gBack_screen->width == 854 ? 107.f : 0.f);\n"
        "        map_pos.v[1] = map_pos.v[1] * 2.f + HIRES_Y_OFFSET;",
        "map blip X centering",
    )

    text = replace_once(
        text,
        "            map_pos.v[0] = 2.f * map_pos.v[0];\n            map_pos.v[1] = 2.f * map_pos.v[1] + HIRES_Y_OFFSET;",
        "            map_pos.v[0] = 2.f * map_pos.v[0] + (gBack_screen->width == 854 ? 107.f : 0.f);\n"
        "            map_pos.v[1] = 2.f * map_pos.v[1] + HIRES_Y_OFFSET;",
        "small map blip X centering",
    )

    old_map = """            if (gReal_graf_data_index) {
                BrPixelmapRectangleFill(gBack_screen, 0, 0, 640, 40, 0);
                BrPixelmapRectangleFill(gBack_screen, 0, 440, 640, 40, 0);

                DRPixelmapDoubledCopy(
                    gBack_screen,
                    gCurrent_race.map_image,
                    gCurrent_race.map_image->width,
                    gCurrent_race.map_image->height,
                    0,
                    40);
            } else {"""
    new_map = """            if (gReal_graf_data_index) {
                if (gBack_screen->width == 854) {
                    BrPixelmapRectangleFill(gBack_screen, 0, 0, 854, 480, 0);
                } else {
                    BrPixelmapRectangleFill(gBack_screen, 0, 0, 640, 40, 0);
                    BrPixelmapRectangleFill(gBack_screen, 0, 440, 640, 40, 0);
                }

                DRPixelmapDoubledCopy(
                    gBack_screen,
                    gCurrent_race.map_image,
                    gCurrent_race.map_image->width,
                    gCurrent_race.map_image->height,
                    gBack_screen->width == 854 ? 107 : 0,
                    40);
            } else {"""
    text = replace_once(text, old_map, new_map, "full-screen map centering")

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
    graphics = root / "src/DETHRACE/common/graphics.c"
    if not graphics.is_file():
        raise FileNotFoundError(graphics)

    patch_graphics(graphics)
    print("Applied safe v24 map-only widescreen alignment")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
