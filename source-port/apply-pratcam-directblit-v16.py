#!/usr/bin/env python3
"""Pratcam direct-blit v16.

The v15 crash log symbolises to BRender OpenGL:
  GeometryStoredGLAllocate() -> gstored.c:168
where r->pixelmap->screen is dereferenced while DoPratcam renders its
driver portrait as a textured 3D quad.

Avoid that fragile GL geometry allocation path entirely. The portrait is
already backed by a normal pixelmap and Dethrace already has a direct
rectangle-copy path for non-devious 2D. Use that direct copy for the
Pratcam unconditionally in the 3DFX/OpenGL build.

Only Pratcam presentation changes. Cockpit geometry, analog input,
instrument positions, mirror, map, draw distance and videos are untouched.
"""
from pathlib import Path
import sys


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected 1 match, found {count}")
    return text.replace(old, new, 1)


def patch_pratcam(path: Path) -> None:
    text = path.read_text(encoding="utf-8")

    old = r'''#ifdef DETHRACE_3DFX_PATCH
    PDUnlockRealBackScreen(1);
    if (gDevious_2d
        && gPrat_model != NULL
        && gPrat_actor != NULL
        && gPrat_material != NULL
        && g2d_camera != NULL
        && gDepth_buffer != NULL) {
        gPrat_model->vertices[1].p.v[0] = gProgram_state.current_car.prat_left + offset;
        gPrat_model->vertices[0].p.v[0] = gProgram_state.current_car.prat_left + offset;
        gPrat_model->vertices[3].p.v[1] = -(y_offset + gProgram_state.current_car.prat_top);
        gPrat_model->vertices[0].p.v[1] = -(y_offset + gProgram_state.current_car.prat_top);

        gPrat_model->vertices[3].p.v[0] = gPrat_model->vertices[1].p.v[0] + 104.0f;
        gPrat_model->vertices[2].p.v[0] = gPrat_model->vertices[1].p.v[0] + 104.0f;

        gPrat_model->vertices[2].p.v[1] = gPrat_model->vertices[3].p.v[1] - 110.0f;
        gPrat_model->vertices[1].p.v[1] = gPrat_model->vertices[3].p.v[1] - 110.0f;
        BrModelUpdate(gPrat_model, BR_MODU_VERTEX_POSITIONS);
        gPrat_actor->render_style = BR_RSTYLE_FACES;
        gPrat_material->colour_map = gPrat_buffer;
        gPrat_buffer->map = gRender_palette;
        BrMapAdd(gPrat_buffer);
        BrMaterialUpdate(gPrat_material, BR_MATU_ALL);
        BrZbSceneRender(g2d_camera, g2d_camera, gBack_screen, gDepth_buffer);
        BrMapRemove(gPrat_buffer);
        gPrat_actor->render_style = BR_RSTYLE_NONE;
    } else {
        DRPixelmapRectangleCopy(
            gBack_screen,
            gProgram_state.current_car.prat_left + offset,
            gProgram_state.current_car.prat_top + y_offset,
            gPrat_buffer,
            0, 0,
            gPrat_buffer->width, gPrat_buffer->height);
    }
    PDLockRealBackScreen(1);
#else'''

    new = r'''#ifdef DETHRACE_3DFX_PATCH
    {
        int prat_copy_width;
        int prat_copy_height;

        /*
         * Modernizer v16:
         * Do not route the driver portrait through BrZbSceneRender.
         * The GL geometry-stored path can receive a renderer pixelmap whose
         * screen pointer is null, which crashes in GeometryStoredGLAllocate.
         *
         * The portrait FLIC already lives in gPrat_buffer, so use the normal
         * 2D blit path instead. If the backing texture was padded to a power
         * of two, copy only the logical portrait area.
         */
        prat_copy_width = (gGraf_data_index == 0) ? 52 : 104;
        prat_copy_height = (gGraf_data_index == 0) ? 46 : 110;

        if (prat_copy_width > gPrat_buffer->width) {
            prat_copy_width = gPrat_buffer->width;
        }
        if (prat_copy_height > gPrat_buffer->height) {
            prat_copy_height = gPrat_buffer->height;
        }

        PDUnlockRealBackScreen(1);
        if (prat_copy_width > 0 && prat_copy_height > 0) {
            DRPixelmapRectangleCopy(
                gBack_screen,
                gProgram_state.current_car.prat_left + offset,
                gProgram_state.current_car.prat_top + y_offset,
                gPrat_buffer,
                0, 0,
                prat_copy_width, prat_copy_height);
        }
        PDLockRealBackScreen(1);
    }
#else'''

    text = replace_once(text, old, new, "Pratcam GL quad -> direct blit")
    path.write_text(text, encoding="utf-8")


def main() -> int:
    if len(sys.argv) != 2:
        print(f"Usage: {Path(sys.argv[0]).name} /path/to/dethrace-v0.10.1", file=sys.stderr)
        return 2

    root = Path(sys.argv[1]).resolve()
    pratcam = root / "src/DETHRACE/common/pratcam.c"
    if not pratcam.is_file():
        raise FileNotFoundError(pratcam)

    patch_pratcam(pratcam)
    print("Applied v16 Pratcam direct-blit workaround")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
