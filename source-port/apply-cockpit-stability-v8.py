#!/usr/bin/env python3
"""Cockpit stability hardening for the Modernizer test build.

No visual/layout values are changed.

Guards transient race-start states that can otherwise dereference invalid
cockpit data:
- zero/out-of-range hand image counts (prevents hands_images[-1])
- null car-to-view / null gears image in instrument drawing
- null damage sprites and zero blink periods
- mirror render resources not allocated yet
- missing cockpit artwork during a transient initialization frame
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

    # 1) DoSteeringWheel: original code turns count==0 into hands_index==-1.
    text = replace_once(
        text,
        """void DoSteeringWheel(tU32 pThe_time) {
    br_pixelmap* hands_image;
    int hands_index;

    if (gProgram_state.current_car_index == gProgram_state.current_car.index && gProgram_state.cockpit_on && gProgram_state.cockpit_image_index >= 0 && gProgram_state.which_view == eView_forward) {
        hands_index = (int)floor(gProgram_state.current_car.number_of_hands_images * ((1.f - gProgram_state.current_car.steering_angle / 10.f) / 2.f));
        if (hands_index < 0) {
            hands_index = 0;
        } else if (hands_index >= gProgram_state.current_car.number_of_hands_images) {
            hands_index = gProgram_state.current_car.number_of_hands_images - 1;
        }""",
        """void DoSteeringWheel(tU32 pThe_time) {
    br_pixelmap* hands_image;
    int hands_index;
    int hands_count;

    if (gProgram_state.current_car_index == gProgram_state.current_car.index && gProgram_state.cockpit_on && gProgram_state.cockpit_image_index >= 0 && gProgram_state.which_view == eView_forward) {
        hands_count = gProgram_state.current_car.number_of_hands_images;

        /*
         * Race-start hardening: the original code maps count==0 to index -1
         * and immediately reads the hand-image arrays out of bounds.
         */
        if (hands_count <= 0) {
            return;
        }
        if (hands_count > COUNT_OF(gProgram_state.current_car.lhands_images)) {
            hands_count = COUNT_OF(gProgram_state.current_car.lhands_images);
        }

        hands_index = (int)floor(hands_count * ((1.f - gProgram_state.current_car.steering_angle / 10.f) / 2.f));
        if (hands_index < 0) {
            hands_index = 0;
        } else if (hands_index >= hands_count) {
            hands_index = hands_count - 1;
        }""",
        "safe steering-wheel hand index",
    )

    # 2) DoInstruments: don't dereference car-to-view during a transient frame.
    text = replace_once(
        text,
        """    if (gProgram_state.current_car_index == gProgram_state.current_car.index) {
        speed_mph = gCar_to_view->speedo_speed * WORLD_SCALE / 1600.0f * 3600000.0f;""",
        """    if (gProgram_state.current_car_index == gProgram_state.current_car.index) {
        if (gCar_to_view == NULL) {
            return;
        }
        speed_mph = gCar_to_view->speedo_speed * WORLD_SCALE / 1600.0f * 3600000.0f;""",
        "safe instrument car pointer",
    )

    # 3) DoInstruments: gear image can still be null while race assets settle.
    text = replace_once(
        text,
        """        if (!gProgram_state.cockpit_on || gProgram_state.cockpit_image_index < 0 || gProgram_state.which_view == eView_forward) {
            if (gCar_to_view->gear < 0) {""",
        """        if ((!gProgram_state.cockpit_on || gProgram_state.cockpit_image_index < 0 || gProgram_state.which_view == eView_forward)
            && gProgram_state.current_car.gears_image != NULL) {
            if (gCar_to_view->gear < 0) {""",
        "safe gear image",
    )

    # 4) DoDamageScreen: guard null sprites and zero periods before integer divide.
    text = replace_once(
        text,
        """    int the_step;
    int the_wobble_x;""",
        """    int the_step;
    int flash_period;
    int the_wobble_x;""",
        "damage flash period local",
    )
    text = replace_once(
        text,
        """        if (i != eDamage_driver) {
            the_image = the_damage->images;
            the_step = 5 * the_damage->damage_level / 100;
            y_pitch = (the_image->height / 2) / 5;
            DRPixelmapRectangleMaskedCopy(""",
        """        if (i != eDamage_driver) {
            the_image = the_damage->images;
            if (the_image == NULL) {
                continue;
            }
            the_step = 5 * the_damage->damage_level / 100;
            if (the_step < 0) {
                the_step = 0;
            } else if (the_step > 4) {
                the_step = 4;
            }
            flash_period = the_damage->periods[the_step];
            if (flash_period <= 0) {
                flash_period = 1;
            }
            y_pitch = (the_image->height / 2) / 5;
            if (y_pitch <= 0) {
                continue;
            }
            DRPixelmapRectangleMaskedCopy(""",
        "safe damage sprite data",
    )
    text = replace_once(
        text,
        "                y_pitch * (2 * the_step + ((pThe_time / the_damage->periods[the_step]) & 1)),",
        "                y_pitch * (2 * the_step + ((pThe_time / flash_period) & 1)),",
        "safe damage blink divide",
    )

    path.write_text(text, encoding="utf-8")


def patch_graphics(path: Path) -> None:
    text = path.read_text(encoding="utf-8")

    # Local cockpit flag must only be true if the corresponding artwork exists.
    text = replace_once(
        text,
        """    cockpit_on = gProgram_state.cockpit_on && gProgram_state.cockpit_image_index >= 0 && !gMap_mode;
    gMirror_on__graphics = gProgram_state.mirror_on && cockpit_on && gProgram_state.which_view == eView_forward;""",
        """    cockpit_on = gProgram_state.cockpit_on
        && gProgram_state.cockpit_image_index >= 0
        && gProgram_state.cockpit_image_index < COUNT_OF(gProgram_state.current_car.cockpit_images)
        && gProgram_state.current_car.cockpit_images[gProgram_state.cockpit_image_index] != NULL
        && !gMap_mode;
    gMirror_on__graphics = gProgram_state.mirror_on && cockpit_on && gProgram_state.which_view == eView_forward;

    /*
     * At race start the mirror flag can become active one frame before its
     * render targets are ready. Skip that transient frame instead of
     * dereferencing a null pixelmap/depth buffer.
     */
    if (gMirror_on__graphics
        && (gRearview_screen == NULL || gRearview_depth_buffer == NULL || gRearview_camera == NULL)) {
        gMirror_on__graphics = 0;
    }""",
        "safe cockpit/mirror frame state",
    )

    path.write_text(text, encoding="utf-8")


def patch_init(path: Path) -> None:
    text = path.read_text(encoding="utf-8")

    # BrPixelmapAllocateSub may fail; do not dereference the result.
    text = replace_once(
        text,
        """        gRearview_depth_buffer = gDepth_buffer;
        gRearview_screen->origin_x = gRearview_screen->width / 2;
        gRearview_screen->origin_y = gRearview_screen->height / 2;""",
        """        gRearview_depth_buffer = gDepth_buffer;
        if (gRearview_screen != NULL) {
            gRearview_screen->origin_x = gRearview_screen->width / 2;
            gRearview_screen->origin_y = gRearview_screen->height / 2;
        }""",
        "safe allocated rearview pixelmap",
    )

    # Don't calculate aspect from an invalid transient mirror rectangle.
    text = replace_once(
        text,
        """    camera_ptr = gRearview_camera->type_data;
    camera_ptr->field_of_view = BrDegreeToAngle(gProgram_state.current_car.rearview_camera_angle);
    camera_ptr->aspect = (gProgram_state.current_car.mirror_right - gProgram_state.current_car.mirror_left) / (float)(gProgram_state.current_car.mirror_bottom - gProgram_state.current_car.mirror_top);""",
        """    if (gRearview_camera == NULL || gRearview_camera->type_data == NULL) {
        return;
    }
    camera_ptr = gRearview_camera->type_data;
    camera_ptr->field_of_view = BrDegreeToAngle(gProgram_state.current_car.rearview_camera_angle);
    if (gProgram_state.current_car.mirror_bottom == gProgram_state.current_car.mirror_top) {
        return;
    }
    camera_ptr->aspect = (gProgram_state.current_car.mirror_right - gProgram_state.current_car.mirror_left) / (float)(gProgram_state.current_car.mirror_bottom - gProgram_state.current_car.mirror_top);""",
        "safe rearview camera initialization",
    )

    path.write_text(text, encoding="utf-8")


def main() -> int:
    if len(sys.argv) != 2:
        print(f"Usage: {Path(sys.argv[0]).name} /path/to/dethrace-v0.10.1", file=sys.stderr)
        return 2

    root = Path(sys.argv[1]).resolve()
    displays = root / "src/DETHRACE/common/displays.c"
    graphics = root / "src/DETHRACE/common/graphics.c"
    init = root / "src/DETHRACE/common/init.c"

    for path in (displays, graphics, init):
        if not path.is_file():
            raise FileNotFoundError(path)

    patch_displays(displays)
    patch_graphics(graphics)
    patch_init(init)

    print("Applied cockpit race-start stability guards; no visual offsets changed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
