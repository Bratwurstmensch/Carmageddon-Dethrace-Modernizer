#!/usr/bin/env python3
"""Apply the Goldstandard common Modernizer features to the 4:3 runtime.

This is intentionally aspect-ratio neutral. It mirrors the gameplay/render-detail
features of the validated RC1 16:9 executable without applying any widescreen,
cockpit-position, map-position, HUD-position, mirror-position, or viewport edits.

Applied:
- 500-unit high-resolution draw distance
- ignore per-race Yon shortening in the Modernizer runtime
- full-detail opponent car models at distance
- render distant pedestrian/object sprites out to 500 units while preserving
  the original 11-unit gameplay activation radius
- expand the lollipop render queue from 100 to 1024

Native analog XInput is applied separately with apply-native-analog-xinput-v13.py.
"""
from pathlib import Path
import sys


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
        "    /* Modernizer 4:3 runtime: use the Goldstandard 500-unit far plane. */\n"
        "    if (gGraf_spec_index == 1) {\n"
        "        gCamera_yon = 500.f;\n"
        "    }\n"
        "    gCamera_angle = GetAScalar(f);",
        "500-unit camera far plane",
    )
    path.write_text(text, encoding="utf-8")


def patch_world(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = replace_once(
        text,
        """    if (gRace_file_version < 5) {
        gYon_multiplier = 1.0;
    } else {
        gYon_multiplier = GetAScalar(f);
    }""",
        """    if (gRace_file_version < 5) {
        gYon_multiplier = 1.0;
    } else {
        /* Read the value for file compatibility, but do not let an individual
         * race shorten the Modernizer high-resolution draw distance. */
        (void)GetAScalar(f);
        gYon_multiplier = gGraf_spec_index == 1 ? 1.0f : 1.0f;
    }""",
        "per-race Yon multiplier",
    )
    path.write_text(text, encoding="utf-8")


def patch_depth_and_camera(init_path: Path, depth_path: Path, brucetrk_path: Path) -> None:
    init_text = init_path.read_text(encoding="utf-8")

    old_init = "        camera_ptr->yon_z = gCamera_yon;"
    count = init_text.count(old_init)
    if count < 1:
        raise RuntimeError("draw distance: AllocateCamera yon assignment not found")
    init_text = init_text.replace(
        old_init,
        "        camera_ptr->yon_z = gGraf_spec_index == 1 ? 500.0f : gCamera_yon;",
    )

    init_text = replace_once(
        init_text,
        "        camera_ptr->yon_z = gYon_multiplier * gCamera_yon;",
        "        camera_ptr->yon_z = gGraf_spec_index == 1 ? 500.0f : gYon_multiplier * gCamera_yon;",
        "draw distance forward camera",
    )
    init_path.write_text(init_text, encoding="utf-8")

    depth_text = depth_path.read_text(encoding="utf-8")
    depth_text = replace_once(
        depth_text,
        "        camera_ptr->yon_z = gYon_multiplier * gCamera_yon;",
        "        camera_ptr->yon_z = gGraf_spec_index == 1 ? 500.0f : gYon_multiplier * gCamera_yon;",
        "draw distance AssertYons",
    )

    old_setyon = """            camera_ptr = gCamera_list[i]->type_data;
            camera_ptr->yon_z = pYon;"""
    new_setyon = """            camera_ptr = gCamera_list[i]->type_data;
            camera_ptr->yon_z = gGraf_spec_index == 1 ? 500.0f : pYon;"""
    depth_text = replace_once(depth_text, old_setyon, new_setyon, "draw distance SetYon")
    depth_path.write_text(depth_text, encoding="utf-8")

    bruce_text = brucetrk_path.read_text(encoding="utf-8")
    old_term = "camera->yon_z * gYon_factor"
    new_term = "camera->yon_z * (gGraf_spec_index == 1 ? 1.0f : gYon_factor)"
    count = bruce_text.count(old_term)
    if count != 3:
        raise RuntimeError(f"draw distance: expected 3 track yon-factor terms, found {count}")
    bruce_text = bruce_text.replace(old_term, new_term)
    brucetrk_path.write_text(bruce_text, encoding="utf-8")


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
                /* Goldstandard Modernizer: retain the full principal opponent model. */
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
                 * Match the 16:9 Goldstandard: keep AI/gameplay activation at
                 * the stock 11 units, but queue the current pedestrian/object
                 * sprite for rendering out to 500 units.
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
    text = replace_once(text, old, new, "distant pedestrian/object sprite rendering")
    path.write_text(text, encoding="utf-8")


def patch_graphics_h(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = replace_once(
        text,
        "extern br_actor* gLollipops[100];",
        "extern br_actor* gLollipops[1024];",
        "lollipop declaration",
    )
    path.write_text(text, encoding="utf-8")


def patch_graphics(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = replace_once(
        text,
        "br_actor* gLollipops[100];",
        "br_actor* gLollipops[1024];",
        "lollipop storage",
    )
    text = replace_once(
        text,
        "    } else if (gNumber_of_lollipops >= 100) {",
        "    } else if (gNumber_of_lollipops >= 1024) {",
        "lollipop queue limit",
    )
    path.write_text(text, encoding="utf-8")


def main() -> int:
    if len(sys.argv) != 2:
        print(f"Usage: {Path(sys.argv[0]).name} /path/to/dethrace-v0.10.1", file=sys.stderr)
        return 2

    root = Path(sys.argv[1]).resolve()
    files = {
        "loading": root / "src/DETHRACE/common/loading.c",
        "world": root / "src/DETHRACE/common/world.c",
        "init": root / "src/DETHRACE/common/init.c",
        "depth": root / "src/DETHRACE/common/depth.c",
        "brucetrk": root / "src/DETHRACE/common/brucetrk.c",
        "car": root / "src/DETHRACE/common/car.c",
        "pedestrn": root / "src/DETHRACE/common/pedestrn.c",
        "graphics_h": root / "src/DETHRACE/common/graphics.h",
        "graphics": root / "src/DETHRACE/common/graphics.c",
    }
    for path in files.values():
        if not path.is_file():
            raise FileNotFoundError(path)

    patch_loading(files["loading"])
    patch_world(files["world"])
    patch_depth_and_camera(files["init"], files["depth"], files["brucetrk"])
    patch_car(files["car"])
    patch_pedestrians(files["pedestrn"])
    patch_graphics_h(files["graphics_h"])
    patch_graphics(files["graphics"])

    print("Applied Goldstandard common Modernizer features to 4:3 runtime")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
