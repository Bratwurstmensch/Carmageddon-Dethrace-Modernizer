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
    count = text.count(old16)
    if count != 2:
        raise SystemExit(f"strip source-y support: expected exactly two matches, found {count}")
    text = text.replace(old16, new16, 1)
    text = text.replace(old16, new16, 1)

    old_args = """            -gCurrent_graf_data->cock_margin_y,
            gScreen_wobble_y,
            gProgram_state.current_car.cockpit_images[gProgram_state.cockpit_image_index],
            0,
            0,
"""
    clip_expr = "MAX(0, gProgram_state.current_car.render_top[gProgram_state.cockpit_image_index] + gCurrent_graf_data->cock_margin_y)"
    new_args = f"""            -gCurrent_graf_data->cock_margin_y
                + (gBack_screen->width == 854 ? {clip_expr} : 0),
            gScreen_wobble_y,
            gProgram_state.current_car.cockpit_images[gProgram_state.cockpit_image_index],
            0,
            gBack_screen->width == 854 ? {clip_expr} : 0,
"""
    count = text.count(old_args)
    if count != 2:
        raise SystemExit(f"cockpit strip blit arguments: expected exactly two matches, found {count}")
    text = text.replace(old_args, new_args)

    path.write_text(text, encoding="utf-8")
    print("Applied experimental 16:9 cockpit top-overlay crop")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
