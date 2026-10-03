#!/usr/bin/env python3
"""Cockpit stability v11 on top of visual-final v10.

No visual coordinates are changed.

Adds bounds/validity guards around instrument drawing paths that can be
entered immediately after switching into cockpit view:
- clamp digital tacho copy width and reject invalid redline/image geometry
- validate gear source rectangle before copying
- reject invalid analog speedometer max-speed geometry
- require valid destination screen for cockpit overlays
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
        """    int gear;
    int gear_height; /* Added by dethrace. */
    double the_angle;""",
        """    int gear;
    int gear_height; /* Added by dethrace. */
    int tacho_width;
    double the_angle;""",
        "instrument tacho width local",
    )

    text = replace_once(
        text,
        """    if (gProgram_state.current_car_index == gProgram_state.current_car.index) {
        if (gCar_to_view == NULL) {
            return;
        }""",
        """    if (gProgram_state.current_car_index == gProgram_state.current_car.index) {
        if (gCar_to_view == NULL || gBack_screen == NULL) {
            return;
        }""",
        "instrument destination guard",
    )

    old_tacho = """        } else if (tacho_image != NULL) {
#ifdef DETHRACE_3DFX_PATCH
            DRPixelmapRectangleCopy(
#else
            BrPixelmapRectangleCopy(
#endif
                gBack_screen,
                the_wobble_x + gProgram_state.current_car.tacho_x[gProgram_state.cockpit_on]
                    + ((gProgram_state.cockpit_on && gBack_screen->width == 854) ? 75 : 0),
                the_wobble_y + gProgram_state.current_car.tacho_y[gProgram_state.cockpit_on],
                gProgram_state.current_car.tacho_image[gProgram_state.cockpit_on],
                0,
                0,
                ((gCar_to_view->revs - 1.0) / (double)gCar_to_view->red_line * (double)gProgram_state.current_car.tacho_image[gProgram_state.cockpit_on]->width + 1.0),
                gProgram_state.current_car.tacho_image[gProgram_state.cockpit_on]->height);
        }"""
    new_tacho = """        } else if (tacho_image != NULL
            && tacho_image->width > 0
            && tacho_image->height > 0
            && gCar_to_view->red_line > 0.f) {
            /*
             * During the first frames after entering cockpit view, revs can be
             * outside their normal range. The retail expression feeds the raw
             * result straight to the rectangle-copy width, which can become
             * negative or larger than the source image.
             */
            tacho_width = (int)(((gCar_to_view->revs - 1.0)
                / (double)gCar_to_view->red_line
                * (double)tacho_image->width) + 1.0);
            if (tacho_width < 0) {
                tacho_width = 0;
            } else if (tacho_width > tacho_image->width) {
                tacho_width = tacho_image->width;
            }

            if (tacho_width > 0) {
#ifdef DETHRACE_3DFX_PATCH
                DRPixelmapRectangleCopy(
#else
                BrPixelmapRectangleCopy(
#endif
                    gBack_screen,
                    the_wobble_x + gProgram_state.current_car.tacho_x[gProgram_state.cockpit_on]
                        + ((gProgram_state.cockpit_on && gBack_screen->width == 854) ? 75 : 0),
                    the_wobble_y + gProgram_state.current_car.tacho_y[gProgram_state.cockpit_on],
                    tacho_image,
                    0,
                    0,
                    tacho_width,
                    tacho_image->height);
            }
        }"""
    text = replace_once(text, old_tacho, new_tacho, "safe digital tacho copy")

    old_gear = """            gear_height = gGraf_spec_index ? GEAR_HEIGHT_HIRES : GEAR_HEIGHT;
            DRPixelmapRectangleMaskedCopy(
                gBack_screen,
                the_wobble_x + gProgram_state.current_car.gear_x[gProgram_state.cockpit_on]
                    + ((gProgram_state.cockpit_on && gBack_screen->width == 854) ? 75 : 0),
                the_wobble_y + gProgram_state.current_car.gear_y[gProgram_state.cockpit_on],
                gProgram_state.current_car.gears_image,
                0,
                (gear + 1) * gear_height,
                gProgram_state.current_car.gears_image->width,
                gear_height);"""
    new_gear = """            gear_height = gGraf_spec_index ? GEAR_HEIGHT_HIRES : GEAR_HEIGHT;
            if (gear_height > 0
                && gProgram_state.current_car.gears_image->width > 0
                && (gear + 1) >= 0
                && ((gear + 2) * gear_height) <= gProgram_state.current_car.gears_image->height) {
                DRPixelmapRectangleMaskedCopy(
                    gBack_screen,
                    the_wobble_x + gProgram_state.current_car.gear_x[gProgram_state.cockpit_on]
                        + ((gProgram_state.cockpit_on && gBack_screen->width == 854) ? 75 : 0),
                    the_wobble_y + gProgram_state.current_car.gear_y[gProgram_state.cockpit_on],
                    gProgram_state.current_car.gears_image,
                    0,
                    (gear + 1) * gear_height,
                    gProgram_state.current_car.gears_image->width,
                    gear_height);
            }"""
    text = replace_once(text, old_gear, new_gear, "safe gear source rectangle")

    text = replace_once(
        text,
        """        if (gProgram_state.current_car.speedo_radius_2[gProgram_state.cockpit_on] >= 0) {
            if (speedo_image && (!gProgram_state.cockpit_on || gProgram_state.cockpit_image_index < 0)) {""",
        """        if (gProgram_state.current_car.speedo_radius_2[gProgram_state.cockpit_on] >= 0) {
            if (gProgram_state.current_car.max_speed <= 0) {
                return;
            }
            if (speedo_image && (!gProgram_state.cockpit_on || gProgram_state.cockpit_image_index < 0)) {""",
        "safe analog speedometer maximum",
    )

    text = replace_once(
        text,
        """    if (gProgram_state.current_car_index == gProgram_state.current_car.index && gProgram_state.cockpit_on && gProgram_state.cockpit_image_index >= 0 && gProgram_state.which_view == eView_forward) {
        hands_count = gProgram_state.current_car.number_of_hands_images;""",
        """    if (gProgram_state.current_car_index == gProgram_state.current_car.index && gProgram_state.cockpit_on && gProgram_state.cockpit_image_index >= 0 && gProgram_state.which_view == eView_forward) {
        if (gBack_screen == NULL) {
            return;
        }
        hands_count = gProgram_state.current_car.number_of_hands_images;""",
        "steering-wheel destination guard",
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
    print("Applied v11 cockpit instrument bounds guards; visual coordinates unchanged")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
