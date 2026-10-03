#!/usr/bin/env python3
"""Apply the validated Carmageddon Dethrace Modernizer v1.5 widescreen behavior
to a clean Dethrace v0.10.1 source tree.

This intentionally touches only source code. It does not contain or generate
original Carmageddon game data.
"""

from pathlib import Path
import sys

WIDE_WIDTH = 854
BASE_WIDTH = 640
WIDE_X_OFFSET = (WIDE_WIDTH - BASE_WIDTH) // 2  # 107


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)


def patch_allsys(path: Path) -> None:
    text = path.read_text(encoding="utf-8")

    text = replace_once(
        text,
        '    { 8, 1, 0, 640, 480, 0, 0, "64X48X8", "VESA,W:640,H:480,B:8", 640, 640, 480, NULL }',
        '    { 8, 1, 0, 854, 480, 0, 0, "64X48X8", "VESA,W:640,H:480,B:8", 854, 854, 480, NULL }',
        "high-resolution graphics spec",
    )

    text = replace_once(
        text,
        "void Double8BitTo16BitPixelmap(br_pixelmap* pDst, br_pixelmap* pSrc, br_pixelmap* pPalette, tU16 pOff, tU16 pSrc_width, tU16 pSrc_height) {",
        "void Double8BitTo16BitPixelmap(br_pixelmap* pDst, br_pixelmap* pSrc, br_pixelmap* pPalette, tU16 pX_offset, tU16 pY_offset, tU16 pSrc_width, tU16 pSrc_height) {",
        "RGB565 doubled-copy signature",
    )
    text = replace_once(
        text,
        "        dst0 = (tU16*)((tU8*)pDst->pixels + pDst->row_bytes * (dst_y + pOff));\n"
        "        dst1 = (tU16*)((tU8*)pDst->pixels + pDst->row_bytes * (dst_y + pOff + 1));",
        "        dst0 = (tU16*)((tU8*)pDst->pixels + pDst->row_bytes * (dst_y + pY_offset)) + pX_offset;\n"
        "        dst1 = (tU16*)((tU8*)pDst->pixels + pDst->row_bytes * (dst_y + pY_offset + 1)) + pX_offset;",
        "RGB565 horizontal destination offset",
    )

    old_copy = """void ReallyCopyBackScreen(int pRendering_area_only, int pClear_top_and_bottom) {
    gAlready_copied = 1;
    if (pRendering_area_only) {
        BrPixelmapRectangleCopy(gScreen, gX_offset, gY_offset, gRender_screen, 0, 0, gWidth, gHeight);
    } else if (gReal_graf_data_index != gGraf_data_index) {
        BrPixelmapRectangleFill(gReal_back_screen, 0, 0, 640, 40, 0);
        BrPixelmapRectangleFill(gReal_back_screen, 0, 440, 640, 40, 0);
        if (gReal_back_screen->type == BR_PMT_RGB_565) {
            Double8BitTo16BitPixelmap(gReal_back_screen, gBack_screen, gCurrent_palette, 40, 320, 200);
        } else {
            DRPixelmapDoubledCopy(gReal_back_screen, gBack_screen, 320, 200, 0, 40);
        }
    }
}"""

    new_copy = """void ReallyCopyBackScreen(int pRendering_area_only, int pClear_top_and_bottom) {
    int interface_x;

    gAlready_copied = 1;
    if (pRendering_area_only) {
        BrPixelmapRectangleCopy(gScreen, gX_offset, gY_offset, gRender_screen, 0, 0, gWidth, gHeight);
    } else if (gReal_graf_data_index != gGraf_data_index) {
        interface_x = gReal_back_screen->width == 854 ? 107 : 0;

        if (gReal_back_screen->width == 854) {
            BrPixelmapRectangleFill(gReal_back_screen, 0, 0, 854, 480, 0);
        } else {
            BrPixelmapRectangleFill(gReal_back_screen, 0, 0, 640, 40, 0);
        }
        BrPixelmapRectangleFill(gReal_back_screen, 0, 440, gReal_back_screen->width, 40, 0);

        if (gReal_back_screen->type == BR_PMT_RGB_565) {
            Double8BitTo16BitPixelmap(gReal_back_screen, gBack_screen, gCurrent_palette, interface_x, 40, 320, 200);
        } else {
            DRPixelmapDoubledCopy(gReal_back_screen, gBack_screen, 320, 200, interface_x, 40);
        }
    }
}"""

    text = replace_once(text, old_copy, new_copy, "centered low-resolution interface copy")

    mouse_old = """        gHarness_platform.GetMousePosition(&mouse_x, &mouse_y);

        delta_x = gGraf_data[gGraf_data_index].width * mouse_x / gGraf_data[gReal_graf_data_index].width - gMouse_last_x_coord;"""

    mouse_new = """        gHarness_platform.GetMousePosition(&mouse_x, &mouse_y);

        /*
         * The 320x200 interface is doubled to 640x400 and centered inside
         * the 854x480 real back buffer. Keep its mouse coordinates in the
         * original 320x200 logical coordinate system.
         *
         * The OpenGL/RGB565 harness reports X in the historical 640-wide
         * coordinate space, so expand it to 854 before removing the 107px
         * pillar and halving the doubled interface coordinates.
         */
        if (gGraf_data_index == 0 && gReal_back_screen != NULL && gReal_back_screen->width == 854) {
            if (gReal_back_screen->type == BR_PMT_RGB_565) {
                mouse_x = mouse_x * 854 / 640;
            }
            *pX_coord = (mouse_x - 107) / 2;
            *pY_coord = (mouse_y - 40) / 2;
            return;
        }

        delta_x = gGraf_data[gGraf_data_index].width * mouse_x / gGraf_data[gReal_graf_data_index].width - gMouse_last_x_coord;"""

    text = replace_once(text, mouse_old, mouse_new, "centered interface mouse mapping")

    path.write_text(text, encoding="utf-8")


def patch_grafdata(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = replace_once(
        text,
        "    { 640,\n        480,\n        21,",
        "    { 854,\n        480,\n        21,",
        "high-resolution graf data width",
    )
    path.write_text(text, encoding="utf-8")



def patch_displays(path: Path) -> None:
    text = path.read_text(encoding="utf-8")

    old_dubrey = """void DubreyBar(int pX_index, int pY, int pColour) {
    int x;

    x = gCurrent_graf_data->ps_bar_left - gCurrent_graf_data->ps_x_pitch * pX_index;
    BrPixelmapLine(gBack_screen, x, pY, x, gCurrent_graf_data->ps_bar_height + pY, pColour);
}"""

    new_dubrey = """void DubreyBar(int pX_index, int pY, int pColour) {
    int x;

    x = gCurrent_graf_data->ps_bar_left - gCurrent_graf_data->ps_x_pitch * pX_index;
    if (gCurrent_graf_data->width == 854) {
        x += 214;
    }
    BrPixelmapLine(gBack_screen, x, pY, x, gCurrent_graf_data->ps_bar_height + pY, pColour);
}"""

    text = replace_once(text, old_dubrey, new_dubrey, "widescreen A/P/O bars")

    old_power = """void DoPSPowerHeadup(int pY, int pLevel, char* pName, int pBar_colour) {
    char s[16];
    int i;

#ifdef DETHRACE_3DFX_PATCH
    if (gBack_screen->type == BR_PMT_RGB_565) {
        pBar_colour = PaletteEntry16Bit(gRender_palette, pBar_colour);
    }
#endif

    DimRectangle(gBack_screen, gCurrent_graf_data->ps_dim_left, pY, gCurrent_graf_data->ps_dim_right, gCurrent_graf_data->ps_dim_height + pY, 1);
    TransDRPixelmapText(gBack_screen, gCurrent_graf_data->ps_name_left, gCurrent_graf_data->ps_name_top_border + pY, gFonts + 6, pName, gBack_screen->width);"""

    new_power = """void DoPSPowerHeadup(int pY, int pLevel, char* pName, int pBar_colour) {
    char s[16];
    int i;
    int x_offset;

#ifdef DETHRACE_3DFX_PATCH
    if (gBack_screen->type == BR_PMT_RGB_565) {
        pBar_colour = PaletteEntry16Bit(gRender_palette, pBar_colour);
    }
#endif

    x_offset = gCurrent_graf_data->width == 854 ? 214 : 0;

    DimRectangle(gBack_screen, gCurrent_graf_data->ps_dim_left + x_offset, pY, gCurrent_graf_data->ps_dim_right + x_offset, gCurrent_graf_data->ps_dim_height + pY, 1);
    TransDRPixelmapText(gBack_screen, gCurrent_graf_data->ps_name_left + x_offset, gCurrent_graf_data->ps_name_top_border + pY, gFonts + 6, pName, gBack_screen->width);"""

    text = replace_once(text, old_power, new_power, "widescreen A/P/O labels and dim rectangles")
    path.write_text(text, encoding="utf-8")


def patch_loading(path: Path) -> None:
    text = path.read_text(encoding="utf-8")

    old = """        } else {
            pCar_spec->headup_slots[pIndex][j].dimmed_background = 0;
        }
    }
}

// IDA: void __usercall ReadNonCarMechanicsData"""

    new = """        } else {
            pCar_spec->headup_slots[pIndex][j].dimmed_background = 0;
        }

        /*
         * Modernizer widescreen layout.
         *
         * The original 640-wide HUD data is kept untouched on disk. For the
         * 854-wide output, shift the five right-side/top HUD slots by the
         * additional 107 pixels and move their dim rectangles with them.
         *
         * Centre-anchored event slots that use the original x=320 centre
         * instead use x=427. This covers misc/points, countdown, fancies,
         * race bonus, time bonus and time-award messages.
         */
        if (gReal_back_screen != NULL && gReal_back_screen->width == 854) {
            tHeadup_slot* headup_slot = &pCar_spec->headup_slots[pIndex][j];

            switch (j) {
            case eHeadupSlot_credits:
            case eHeadupSlot_ped_kills:
            case eHeadupSlot_timer:
            case eHeadupSlot_lap_count:
            case eHeadupSlot_cars_out_count:
                /*
                 * Older private Modernizer tests already changed these
                 * HEADUP.TXT X positions by +107. Values from the original
                 * 640-wide data cannot exceed 640, so only shift slots that
                 * are still in the original coordinate range. This keeps the
                 * source port compatible with both clean and already-patched
                 * local test data.
                 */
                if (headup_slot->x <= 640) {
                    headup_slot->x += 107;
                    if (headup_slot->dimmed_background) {
                        headup_slot->dim_left += 107;
                        headup_slot->dim_right += 107;
                    }
                }
                break;

            case eHeadupSlot_misc:
            case eHeadupSlot_countdown:
            case eHeadupSlot_fancies:
            case eHeadupSlot_race_bonus:
            case eHeadupSlot_time_bonus:
            case eHeadupSlot_time_award:
                if (headup_slot->justification == eJust_centre
                    && headup_slot->x == 320
                    && !headup_slot->dimmed_background) {
                    headup_slot->x = 427;
                }
                break;

            default:
                break;
            }
        }
    }
}

// IDA: void __usercall ReadNonCarMechanicsData"""

    text = replace_once(text, old, new, "widescreen head-up slot layout")
    path.write_text(text, encoding="utf-8")



def patch_extended_draw_distance(init_path: Path, depth_path: Path, brucetrk_path: Path) -> None:
    # Experimental Modernizer rendering-distance test for the 854-wide path.
    # Keep the original game/config values intact for 4:3, but use a very
    # generous far plane for the widescreen build and force track-column
    # selection to the earliest (1.0) YonFactor.
    init_text = init_path.read_text(encoding="utf-8")

    old_init = "        camera_ptr->yon_z = gCamera_yon;"
    new_init = "        camera_ptr->yon_z = gGraf_spec_index == 1 ? 500.0f : gCamera_yon;"
    count = init_text.count(old_init)
    if count < 1:
        raise RuntimeError("extended draw distance: AllocateCamera yon assignment not found")
    init_text = init_text.replace(old_init, new_init)

    init_text = replace_once(
        init_text,
        "        camera_ptr->yon_z = gYon_multiplier * gCamera_yon;",
        "        camera_ptr->yon_z = gGraf_spec_index == 1 ? 500.0f : gYon_multiplier * gCamera_yon;",
        "extended draw distance forward camera",
    )
    init_path.write_text(init_text, encoding="utf-8")

    depth_text = depth_path.read_text(encoding="utf-8")
    depth_text = replace_once(
        depth_text,
        "        camera_ptr->yon_z = gYon_multiplier * gCamera_yon;",
        "        camera_ptr->yon_z = gGraf_spec_index == 1 ? 500.0f : gYon_multiplier * gCamera_yon;",
        "extended draw distance AssertYons",
    )

    old_setyon = """            camera_ptr = gCamera_list[i]->type_data;
            camera_ptr->yon_z = pYon;"""
    new_setyon = """            camera_ptr = gCamera_list[i]->type_data;
            camera_ptr->yon_z = gGraf_spec_index == 1 ? 500.0f : pYon;"""
    depth_text = replace_once(depth_text, old_setyon, new_setyon, "extended draw distance SetYon")
    depth_path.write_text(depth_text, encoding="utf-8")

    bruce_text = brucetrk_path.read_text(encoding="utf-8")
    old_term = "camera->yon_z * gYon_factor"
    new_term = "camera->yon_z * (gGraf_spec_index == 1 ? 1.0f : gYon_factor)"
    count = bruce_text.count(old_term)
    if count != 3:
        raise RuntimeError(f"extended draw distance: expected 3 track yon-factor terms, found {count}")
    bruce_text = bruce_text.replace(old_term, new_term)
    brucetrk_path.write_text(bruce_text, encoding="utf-8")



def patch_extended_object_detail(car_path: Path, ped_path: Path, graphics_c_path: Path, graphics_h_path: Path) -> None:
    # Keep full opponent-car geometry at distance in the 854-wide Modernizer
    # path instead of switching to the original low-detail distance actors.
    car_text = car_path.read_text(encoding="utf-8")
    old_car = """            if (the_car->driver != eDriver_local_human && the_car->car_model_variable) {
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
    new_car = """            if (the_car->driver != eDriver_local_human && the_car->car_model_variable) {
                if (gGraf_spec_index == 1) {
                    /*
                     * Modernizer extended-detail mode: the original game
                     * swaps opponents to simplified car actors as distance
                     * increases. Keep the principal (0-distance) model for
                     * the 854-wide path so the longer draw distance does not
                     * expose low-detail car silhouettes.
                     */
                    if (the_car->current_car_actor != the_car->principal_car_actor) {
                        SwitchCarActor(the_car, the_car->principal_car_actor);
                    }
                } else {
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
                }
            }"""
    car_text = replace_once(car_text, old_car, new_car, "full-distance opponent car models")
    car_path.write_text(car_text, encoding="utf-8")

    # Pedestrians/pickups are normally only processed/rendered inside an
    # 11-unit X/Z square. Preserve that simulation radius, but enqueue a
    # camera-facing static sprite out to the 500-unit Modernizer far plane.
    ped_text = ped_path.read_text(encoding="utf-8")
    old_ped = """            if (the_pedestrian->actor->parent == gDont_render_actor
                && (x_delta > ACTIVE_PED_DXDZ || z_delta > ACTIVE_PED_DXDZ)) {
                the_pedestrian->active = 0;
            } else if (the_pedestrian->hit_points == -100) {"""
    new_ped = """            if (the_pedestrian->actor->parent == gDont_render_actor
                && (x_delta > ACTIVE_PED_DXDZ || z_delta > ACTIVE_PED_DXDZ)) {
                the_pedestrian->active = 0;

                /*
                 * Modernizer extended draw distance: render the already
                 * loaded pedestrian/pickup sprite at long range without
                 * running its AI/path simulation. Original gameplay still
                 * activates it only inside ACTIVE_PED_DXDZ.
                 */
                if (gGraf_spec_index == 1
                    && x_delta <= 500.0f
                    && z_delta <= 500.0f
                    && (gPedestrians_on || the_pedestrian->ref_number >= 100)
                    && the_pedestrian->hit_points != -100) {
                    gCurrent_lollipop_index = -1;
                    MungePedModel(the_pedestrian);
                }
            } else if (the_pedestrian->hit_points == -100) {"""
    ped_text = replace_once(ped_text, old_ped, new_ped, "long-distance pedestrian sprite rendering")
    ped_path.write_text(ped_text, encoding="utf-8")

    # Some Carmageddon races contain well over 100 pedestrian sprites (the
    # stock lollipop queue limit). A 500-unit render radius can legitimately
    # need several hundred in one frame.
    graphics_c = graphics_c_path.read_text(encoding="utf-8")
    graphics_c = replace_once(
        graphics_c,
        "br_actor* gLollipops[100];",
        "br_actor* gLollipops[1024];",
        "expanded lollipop queue storage",
    )
    graphics_c = replace_once(
        graphics_c,
        "    } else if (gNumber_of_lollipops >= 100) {",
        "    } else if (gNumber_of_lollipops >= COUNT_OF(gLollipops)) {",
        "expanded lollipop queue limit",
    )
    graphics_c_path.write_text(graphics_c, encoding="utf-8")

    graphics_h = graphics_h_path.read_text(encoding="utf-8")
    graphics_h = replace_once(
        graphics_h,
        "extern br_actor* gLollipops[100];",
        "extern br_actor* gLollipops[1024];",
        "expanded lollipop queue declaration",
    )
    graphics_h_path.write_text(graphics_h, encoding="utf-8")



def main() -> int:
    if len(sys.argv) != 2:
        print(f"Usage: {Path(sys.argv[0]).name} /path/to/dethrace-v0.10.1", file=sys.stderr)
        return 2

    root = Path(sys.argv[1]).resolve()
    allsys = root / "src/DETHRACE/pc-all/allsys.c"
    grafdata = root / "src/DETHRACE/common/grafdata.c"
    displays = root / "src/DETHRACE/common/displays.c"
    loading = root / "src/DETHRACE/common/loading.c"
    init = root / "src/DETHRACE/common/init.c"
    depth = root / "src/DETHRACE/common/depth.c"
    brucetrk = root / "src/DETHRACE/common/brucetrk.c"
    car = root / "src/DETHRACE/common/car.c"
    pedestrn = root / "src/DETHRACE/common/pedestrn.c"
    graphics_c = root / "src/DETHRACE/common/graphics.c"
    graphics_h = root / "src/DETHRACE/common/graphics.h"

    for path in (allsys, grafdata, displays, loading, init, depth, brucetrk, car, pedestrn, graphics_c, graphics_h):
        if not path.is_file():
            raise FileNotFoundError(path)

    patch_allsys(allsys)
    patch_grafdata(grafdata)
    patch_displays(displays)
    patch_loading(loading)
    patch_extended_draw_distance(init, depth, brucetrk)
    patch_extended_object_detail(car, pedestrn, graphics_c, graphics_h)

    print("Applied Modernizer v1.5 + 500-unit draw distance + full car LOD + distant sprites test")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
