#!/usr/bin/env python3
"""Experimental widescreen cockpit top-overlay crop.

Keeps the successful diagnostic full-height 3D opening and, only in 854-wide
cockpit mode, skips the cockpit strip-image rows that originally sit above the
car's defined 3D windshield opening. This reveals the already-rendered 3D world
instead of painting the cockpit's opaque top band over it.

4:3 calls continue to use source_y=0 and are unchanged.
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
        raise SystemExit("usage: apply-cockpit-top-overlay-crop-test.py <dethrace-source>")

    root = Path(sys.argv[1])
    path = root / "src" / "DETHRACE" / "common" / "graphics.c"
    text = path.read_text(encoding="utf-8")

    # The strip blitters historically ignore pSource_y. Teach both paths to
    # skip source rows when explicitly requested; every existing caller passes
    # zero, so this is inert outside the experimental cockpit call below.
    old16 = """    height = *(tU16*)pSource;
    pSource = pSource + 2;
    if (pDest_y + pOffset_y >= 0) {
"""
    new16 = """    height = *(tU16*)pSource;
    pSource = pSource + 2;
    if (pSource_y > 0) {
        if (pSource_y >= height) {
            return;
        }
        pSource = SkipLines(pSource, pSource_y);
        height -= pSource_y;
    }
    if (pDest_y + pOffset_y >= 0) {
"""
    text = replace_once(text, old16, new16, "16-bit strip source-y support")

    # Same code exists once more in the indexed path.
    text = replace_once(text, old16, new16, "8-bit strip source-y support")

    old_call = """        CopyStripImage(
            gBack_screen,
            -gCurrent_graf_data->cock_margin_x,
            gScreen_wobble_x,
            -gCurrent_graf_data->cock_margin_y,
            gScreen_wobble_y,
            gProgram_state.current_car.cockpit_images[gProgram_state.cockpit_image_index],
            0,
            0,
            gCurrent_graf_data->total_cock_width,
            gCurrent_graf_data->total_cock_height);
"""
    clip_expr = "MAX(0, gProgram_state.current_car.render_top[gProgram_state.cockpit_image_index] + gCurrent_graf_data->cock_margin_y)"
    new_call = f"""        CopyStripImage(
            gBack_screen,
            -gCurrent_graf_data->cock_margin_x,
            gScreen_wobble_x,
            -gCurrent_graf_data->cock_margin_y
                + (gBack_screen->width == 854 ? {clip_expr} : 0),
            gScreen_wobble_y,
            gProgram_state.current_car.cockpit_images[gProgram_state.cockpit_image_index],
            0,
            gBack_screen->width == 854 ? {clip_expr} : 0,
            gCurrent_graf_data->total_cock_width,
            gCurrent_graf_data->total_cock_height);
"""
    # There are two cockpit blit sites (3DFX and fallback); patch both.
    count = text.count(old_call)
    if count != 2:
        raise SystemExit(f"cockpit strip blit: expected exactly two matches, found {count}")
    text = text.replace(old_call, new_call)

    path.write_text(text, encoding="utf-8")
    print("Applied experimental 16:9 cockpit top-overlay crop")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
