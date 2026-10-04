#!/usr/bin/env python3
"""Experimental 16:9 cockpit viewport-top normalization.

The validated Goldstandard already expands the cockpit 3D viewport to the full
854-pixel width but deliberately keeps each car's original render_top value.

Splat Pack cockpit data can use a substantially lower windshield opening than
the main-game Eagle/Hawk data, producing an extra black band in widescreen.
For this diagnostic test only, force the widescreen cockpit render_top to 0 pixels.

4:3 behavior is untouched.
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
        raise SystemExit("usage: apply-cockpit-top-normalization-test.py <dethrace-source>")

    root = Path(sys.argv[1])
    path = root / "src" / "DETHRACE" / "common" / "init.c"
    text = path.read_text(encoding="utf-8")

    old = """        if (gGraf_specs[gGraf_spec_index].total_width == 854) {
            /* Render the 3D world across the full 16:9 width behind the
             * centred 640-wide cockpit artwork. Keep the original vertical
             * cockpit opening so the dashboard still masks the scene. */
            gProgram_state.current_render_left = 0;
            gProgram_state.current_render_top = gProgram_state.current_car.render_top[gProgram_state.cockpit_image_index];
            gProgram_state.current_render_right = gGraf_specs[gGraf_spec_index].total_width;
        } else {
"""

    new = """        if (gGraf_specs[gGraf_spec_index].total_width == 854) {
            int cockpit_render_top;

            /* Render the 3D world across the full 16:9 width behind the
             * centred 640-wide cockpit artwork.
             *
             * Splat Pack cockpit data can define a noticeably lower top edge
             * than the main-game cockpit, leaving an additional black strip in
             * widescreen. Keep car-specific values that are already 50 or less,
             * and force the 3D render viewport to begin at the very top of the 854x480 frame.
             * The 4:3 path below remains completely unchanged. */
            cockpit_render_top = gProgram_state.current_car.render_top[gProgram_state.cockpit_image_index];

            gProgram_state.current_render_left = 0;
            gProgram_state.current_render_top = 0;
            gProgram_state.current_render_right = gGraf_specs[gGraf_spec_index].total_width;
        } else {
"""

    text = replace_once(text, old, new, "16:9 cockpit viewport block")
    path.write_text(text, encoding="utf-8")
    print("Applied diagnostic 16:9 cockpit render-top test (forced 0px)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
