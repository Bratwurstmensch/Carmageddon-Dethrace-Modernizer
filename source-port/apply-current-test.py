#!/usr/bin/env python3
"""Apply current Carmageddon Dethrace Modernizer test changes on top of
apply-v1.5-source-port.py against a clean Dethrace v0.10.1 tree.

Test scope:
- keep extended 16:9 detail changes (500 far plane, YonFactor 1.0,
  full opponent models, distant static pedestrian rendering, 1024 lollipops)
- keep right-anchored A/P/O damage HUD (+214)
- centre cockpit and full-screen map content in 854x480 (+107)
"""
from pathlib import Path
import sys

WIDE_WIDTH = 854
BASE_WIDTH = 640
WIDE_X_OFFSET = (WIDE_WIDTH - BASE_WIDTH) // 2  # 107
RIGHT_EDGE_OFFSET = WIDE_WIDTH - BASE_WIDTH     # 214


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)


def patch_loading(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = replace_once(
        text,
        "    gCamera_yon = GetAScalar(f);\n    gCamera_angle = GetAScalar(f);",
        "    gCamera_yon = GetAScalar(f);\n"
        "    /* Modernizer widescreen runtime: retain the validated 500-unit far plane. */\n"
        "    gCamera_yon = 500.f;\n"
        "    gCamera_angle = GetAScalar(f);",
        "500-unit camera far plane",
    )
    path.write_text(text, encoding="utf-8")


def patch_brucetrk(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = replace_once(
        text,
        "void SetYonFactor(br_scalar pNew) {\n\n    gYon_factor = pNew;\n}",
        "void SetYonFactor(br_scalar pNew) {\n\n"
        "    (void)pNew;\n"
        "    /* Modernizer widescreen runtime: always use the full configured far plane. */\n"
        "    gYon_factor = 1.0f;\n}",
        "YonFactor 1.0",
    )
    path.write_text(text, encoding="utf-8")


def patch_car(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    old = """            if (the_car->driver != eDriver_local_human && the_car->car_model_variable) {
                distance_from_camera = Vector3DistanceSquared(&the_car->car_master_actor->t.t.translate.t,
                                           (br_vector3*)gCamera_to_world.m[3])
                    / gCar_simplification_factor[gGraf_spec_index][gCar_simplification_level];
                if (gNet_mode != eNet_mode_none && gNet_players[gIt_or_fox].car == the_car) {
                    distance_from_camera = 0.f;
                }
                for (i = 0; i < the_car->car_actor_count; i++) {
                    if (the_car->car_model_actors[i].min_distance_squared <= distance_from_camera) {
                        SwitchCarActor(the_car, i);
                        break;
                    }
                }
            }"""
    new = """            if (the_car->driver != eDriver_local_human && the_car->car_model_variable) {
                /* Modernizer extended-detail runtime: keep opponents on their full principal model. */
                SwitchCarActor(the_car, the_car->principal_car_actor);
            }"""
    text = replace_once(text, old, new, "full-detail opponent cars")
    path.write_text(text, encoding="utf-8")


def patch_pedestrians(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = replace_once(
        text,
        "#define ACTIVE_PED_DXDZ 11.f\n",
        "#define ACTIVE_PED_DXDZ 11.f\n"
        "#define RENDER_PED_DXDZ 500.f\n",
        "pedestrian render-distance constant",
    )
    old = """            if (the_pedestrian->actor->parent == gDont_render_actor
                && (x_delta > ACTIVE_PED_DXDZ || z_delta > ACTIVE_PED_DXDZ)) {
                the_pedestrian->active = 0;
            } else if (the_pedestrian->hit_points == -100) {"""
    new = """            if (the_pedestrian->actor->parent == gDont_render_actor
                && (x_delta > ACTIVE_PED_DXDZ || z_delta > ACTIVE_PED_DXDZ)) {
                /*
                 * Keep gameplay/AI activation at the original 11 units, but still
                 * queue the current bitmap model for rendering out to the 500-unit
                 * Modernizer far plane. MungePedModel updates/queues the visual only;
                 * DoPedestrian is deliberately not called here.
                 */
                the_pedestrian->active = 0;
                if (x_delta <= RENDER_PED_DXDZ
                    && z_delta <= RENDER_PED_DXDZ
                    && (gPedestrians_on || the_pedestrian->ref_number >= 100)
                    && the_pedestrian->hit_points != -100) {
                    gCurrent_lollipop_index = -1;
                    MungePedModel(the_pedestrian);
                }
            } else if (the_pedestrian->hit_points == -100) {"""
    text = replace_once(text, old, new, "distant static pedestrian rendering")
    path.write_text(text, encoding="utf-8")


def patch_graphics_h(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = replace_once(text, "extern br_actor* gLollipops[100];", "extern br_actor* gLollipops[1024];", "lollipop declaration")
    path.write_text(text, encoding="utf-8")


def patch_graphics(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = replace_once(text, "br_actor* gLollipops[100];", "br_actor* gLollipops[1024];", "lollipop storage")
    text = replace_once(text, "    } else if (gNumber_of_lollipops >= 100) {", "    } else if (gNumber_of_lollipops >= 1024) {", "lollipop queue limit")

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
                    /* Centre the original 640x400 doubled map in the 854x480 framebuffer. */
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

    text = replace_once(
        text,
        "            gBack_screen,\n            -gCurrent_graf_data->cock_margin_x,\n            gScreen_wobble_x,\n            -gCurrent_graf_data->cock_margin_y,",
        "            gBack_screen,\n            -gCurrent_graf_data->cock_margin_x + (gBack_screen->width == 854 ? 107 : 0),\n            gScreen_wobble_x,\n            -gCurrent_graf_data->cock_margin_y,",
        "cockpit artwork centering (3dfx)",
    )
    text = replace_once(
        text,
        "                gBack_screen,\n                -gCurrent_graf_data->cock_margin_x,\n                gScreen_wobble_x,\n                -gCurrent_graf_data->cock_margin_y,",
        "                gBack_screen,\n                -gCurrent_graf_data->cock_margin_x + (gBack_screen->width == 854 ? 107 : 0),\n                gScreen_wobble_x,\n                -gCurrent_graf_data->cock_margin_y,",
        "cockpit artwork centering (software)",
    )

    text = replace_once(
        text,
        "        gRearview_screen->base_x = MAX(0, gScreen_wobble_x + gProgram_state.current_car.mirror_left);",
        "        gRearview_screen->base_x = MAX(0, gScreen_wobble_x + gProgram_state.current_car.mirror_left + (gBack_screen->width == 854 ? 107 : 0));",
        "rearview base X (fixed bugs)",
    )
    text = replace_once(
        text,
        "        gRearview_screen->base_x = gScreen_wobble_x + gProgram_state.current_car.mirror_left;",
        "        gRearview_screen->base_x = gScreen_wobble_x + gProgram_state.current_car.mirror_left + (gBack_screen->width == 854 ? 107 : 0);",
        "rearview base X",
    )
    text = replace_once(
        text,
        "                    gScreen_wobble_x + gProgram_state.current_car.mirror_left,",
        "                    gScreen_wobble_x + gProgram_state.current_car.mirror_left + (gBack_screen->width == 854 ? 107 : 0),",
        "rearview copy X",
    )

    path.write_text(text, encoding="utf-8")


def patch_init(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = replace_once(
        text,
        "        gProgram_state.current_render_left = gProgram_state.current_car.render_left[gProgram_state.cockpit_image_index];\n"
        "        gProgram_state.current_render_top = gProgram_state.current_car.render_top[gProgram_state.cockpit_image_index];\n"
        "        gProgram_state.current_render_right = gProgram_state.current_car.render_right[gProgram_state.cockpit_image_index];",
        "        gProgram_state.current_render_left = gProgram_state.current_car.render_left[gProgram_state.cockpit_image_index]\n"
        "            + (gGraf_specs[gGraf_spec_index].total_width == 854 ? 107 : 0);\n"
        "        gProgram_state.current_render_top = gProgram_state.current_car.render_top[gProgram_state.cockpit_image_index];\n"
        "        gProgram_state.current_render_right = gProgram_state.current_car.render_right[gProgram_state.cockpit_image_index]\n"
        "            + (gGraf_specs[gGraf_spec_index].total_width == 854 ? 107 : 0);",
        "cockpit 3D viewport centering",
    )
    text = replace_once(
        text,
        "            gProgram_state.current_car.mirror_left,\n            gProgram_state.current_car.mirror_top,",
        "            gProgram_state.current_car.mirror_left + (gBack_screen->width == 854 ? 107 : 0),\n"
        "            gProgram_state.current_car.mirror_top,",
        "rearview subpixelmap X",
    )
    path.write_text(text, encoding="utf-8")


def patch_displays(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = replace_once(
        text,
        "            gProgram_state.current_car.dim_left[dim_index][i],\n"
        "            gProgram_state.current_car.dim_top[dim_index][i],\n"
        "            gProgram_state.current_car.dim_right[dim_index][i],",
        "            gProgram_state.current_car.dim_left[dim_index][i] + ((dim_index && gBack_screen->width == 854) ? 107 : 0),\n"
        "            gProgram_state.current_car.dim_top[dim_index][i],\n"
        "            gProgram_state.current_car.dim_right[dim_index][i] + ((dim_index && gBack_screen->width == 854) ? 107 : 0),",
        "cockpit dim rectangle centering",
    )
    text = replace_once(
        text,
        "        the_wobble_x = gScreen_wobble_x;\n        the_wobble_y = gScreen_wobble_y;\n    } else {\n        the_wobble_x = gProgram_state.current_car.damage_x_offset;",
        "        the_wobble_x = gScreen_wobble_x + (gBack_screen->width == 854 ? 107 : 0);\n"
        "        the_wobble_y = gScreen_wobble_y;\n"
        "    } else {\n"
        "        the_wobble_x = gProgram_state.current_car.damage_x_offset + (gBack_screen->width == 854 ? 214 : 0);",
        "damage HUD X offsets",
    )
    text = replace_once(
        text,
        "                gProgram_state.current_car.damage_background_x,\n                gProgram_state.current_car.damage_background_y,",
        "                gProgram_state.current_car.damage_background_x + (gBack_screen->width == 854 ? 214 : 0),\n"
        "                gProgram_state.current_car.damage_background_y,",
        "damage HUD background X",
    )
    text = replace_once(
        text,
        "            the_wobble_x = gScreen_wobble_x;\n            the_wobble_y = gScreen_wobble_y;\n        } else {\n            the_wobble_x = 0;",
        "            the_wobble_x = gScreen_wobble_x + (gBack_screen->width == 854 ? 107 : 0);\n"
        "            the_wobble_y = gScreen_wobble_y;\n"
        "        } else {\n"
        "            the_wobble_x = 0;",
        "cockpit instrument X centering",
    )
    path.write_text(text, encoding="utf-8")


def main() -> int:
    if len(sys.argv) != 2:
        print(f"Usage: {Path(sys.argv[0]).name} /path/to/dethrace-v0.10.1", file=sys.stderr)
        return 2

    root = Path(sys.argv[1]).resolve()
    files = {
        "loading": root / "src/DETHRACE/common/loading.c",
        "brucetrk": root / "src/DETHRACE/common/brucetrk.c",
        "car": root / "src/DETHRACE/common/car.c",
        "pedestrn": root / "src/DETHRACE/common/pedestrn.c",
        "graphics_h": root / "src/DETHRACE/common/graphics.h",
        "graphics": root / "src/DETHRACE/common/graphics.c",
        "init": root / "src/DETHRACE/common/init.c",
        "displays": root / "src/DETHRACE/common/displays.c",
    }
    for path in files.values():
        if not path.is_file():
            raise FileNotFoundError(path)

    patch_loading(files["loading"])
    patch_brucetrk(files["brucetrk"])
    patch_car(files["car"])
    patch_pedestrians(files["pedestrn"])
    patch_graphics_h(files["graphics_h"])
    patch_graphics(files["graphics"])
    patch_init(files["init"])
    patch_displays(files["displays"])

    print("Applied current Modernizer extended-detail + cockpit/map centering test patch")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
