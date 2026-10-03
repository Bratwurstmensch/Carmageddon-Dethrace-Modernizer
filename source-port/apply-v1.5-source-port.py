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


def patch_gl_video_context(device_h: Path, device_c: Path, devpmglf_c: Path, gstored_c: Path) -> None:
    text = device_h.read_text(encoding="utf-8")
    text = replace_once(
        text,
        """    /* Device clut */
    struct br_device_clut* clut;
""",
        """    /* Device clut */
    struct br_device_clut* clut;

    /*
     * Stable device-wide OpenGL VIDEO context.
     *
     * Stored-geometry allocation must not recover this through
     * renderer->pixelmap: crash diagnostics showed that pointer occasionally
     * becoming stale/corrupt during cockpit + mirror rendering.
     */
    HVIDEO video;
""",
        "device-wide GL video pointer",
    )
    device_h.write_text(text, encoding="utf-8")

    text = device_c.read_text(encoding="utf-8")
    text = replace_once(
        text,
        """    self->device = self;
    self->object_list = BrObjectListAllocate(self);
""",
        """    self->device = self;
    self->object_list = BrObjectListAllocate(self);
    self->video = NULL;
""",
        "initialize device-wide GL video pointer",
    )
    device_c.write_text(text, encoding="utf-8")

    text = devpmglf_c.read_text(encoding="utf-8")
    text = replace_once(
        text,
        """    if (VIDEO_Open(&self->asFront.video, pt.vertex_shader, pt.fragment_shader) == NULL) {
        /*
         * If this fails we can run our regular cleanup.
         */
        BrResFree(self);
        return NULL;
    }
    self->asFront.tex_white = DeviceGLBuildWhiteTexture();
""",
        """    if (VIDEO_Open(&self->asFront.video, pt.vertex_shader, pt.fragment_shader) == NULL) {
        /*
         * If this fails we can run our regular cleanup.
         */
        BrResFree(self);
        return NULL;
    }

    /*
     * VIDEO is device/context-wide. Cache its stable address on the device
     * instead of repeatedly reaching it through renderer->pixelmap->screen.
     */
    dev->video = &self->asFront.video;

    self->asFront.tex_white = DeviceGLBuildWhiteTexture();
""",
        "cache device-wide GL video pointer",
    )
    text = replace_once(
        text,
        """    VIDEO_Close(&self->asFront.video);

    // TODO: uncomment
""",
        """    if (self->device->video == &self->asFront.video) {
        self->device->video = NULL;
    }

    VIDEO_Close(&self->asFront.video);

    // TODO: uncomment
""",
        "clear device-wide GL video pointer",
    )
    devpmglf_c.write_text(text, encoding="utf-8")

    text = gstored_c.read_text(encoding="utf-8")
    text = replace_once(
        text,
        """br_geometry_stored* GeometryStoredGLAllocate(br_geometry_v1_model* gv1model, const char* id, br_renderer* r, struct v11model* model) {
    size_t total_vertices, total_faces;
    br_geometry_stored* self;

    self = BrResAllocate""",
        """br_geometry_stored* GeometryStoredGLAllocate(br_geometry_v1_model* gv1model, const char* id, br_renderer* r, struct v11model* model) {
    size_t total_vertices, total_faces;
    br_geometry_stored* self;

    /*
     * Use the device-owned GL context. Do not dereference r->pixelmap here:
     * the cockpit-crash dump showed that pointer holding a non-canonical
     * stale/corrupt value at this exact allocation site.
     */
    if (gv1model == NULL || gv1model->device == NULL || gv1model->device->video == NULL)
        return NULL;

    self = BrResAllocate""",
        "guard stable GL video context",
    )
    text = replace_once(
        text,
        """    self->gl_vao = create_vao(&r->pixelmap->screen->asFront.video, self->gl_vbo_posn, self->gl_vbo, self->gl_ibo);""",
        """    self->gl_vao = create_vao(gv1model->device->video, self->gl_vbo_posn, self->gl_vbo, self->gl_ibo);""",
        "stored geometry stable GL video context",
    )
    gstored_c.write_text(text, encoding="utf-8")


def main() -> int:
    if len(sys.argv) != 2:
        print(f"Usage: {Path(sys.argv[0]).name} /path/to/dethrace-v0.10.1", file=sys.stderr)
        return 2

    root = Path(sys.argv[1]).resolve()
    allsys = root / "src/DETHRACE/pc-all/allsys.c"
    grafdata = root / "src/DETHRACE/common/grafdata.c"
    loading = root / "src/DETHRACE/common/loading.c"
    device_h = root / "lib/BRender-v1.3.2/drivers/glrend/device.h"
    device_c = root / "lib/BRender-v1.3.2/drivers/glrend/device.c"
    devpmglf_c = root / "lib/BRender-v1.3.2/drivers/glrend/devpmglf.c"
    gstored_c = root / "lib/BRender-v1.3.2/drivers/glrend/gstored.c"

    for path in (allsys, grafdata, loading, device_h, device_c, devpmglf_c, gstored_c):
        if not path.is_file():
            raise FileNotFoundError(path)

    patch_allsys(allsys)
    patch_grafdata(grafdata)
    patch_loading(loading)
    patch_gl_video_context(device_h, device_c, devpmglf_c, gstored_c)

    print("Applied Modernizer v1.5 source port + cockpit renderer stability fix to Dethrace v0.10.1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
