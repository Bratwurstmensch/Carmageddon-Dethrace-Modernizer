#!/usr/bin/env python3
"""Cockpit renderer stability v19.

On top of the full RC1 patch chain, avoid dereferencing renderer->pixelmap
inside GeometryStoredGLAllocate(). A captured cockpit/mirror crash showed
renderer->pixelmap containing a non-canonical stale/corrupt value at the
exact gstored.c allocation site.

Cache the device-wide OpenGL VIDEO context on br_device when the front
pixelmap opens it, and use that stable pointer when creating stored-geometry
VAOs.

No gameplay, HUD, controller, draw-distance, cockpit positioning, Pratcam,
pedestrian-completion, or localization behaviour is intentionally changed.
"""
from pathlib import Path
import sys


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected 1 match, found {count}")
    return text.replace(old, new, 1)


def patch_device_h(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = replace_once(
        text,
        """    /* Device clut */
    struct br_device_clut* clut;
""",
        """    /* Device clut */
    struct br_device_clut* clut;

    /*
     * Device-wide OpenGL VIDEO context.
     *
     * Stored geometry must not recover this through renderer->pixelmap:
     * cockpit crash diagnostics captured that pointer in a stale/corrupt
     * state at GeometryStoredGLAllocate().
     */
    HVIDEO video;
""",
        "device-wide GL video pointer",
    )
    path.write_text(text, encoding="utf-8")


def patch_device_c(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
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
    path.write_text(text, encoding="utf-8")


def patch_devpmglf(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
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
     * instead of reaching it through renderer->pixelmap->screen.
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
    path.write_text(text, encoding="utf-8")


def patch_gstored(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
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
     * The OpenGL VIDEO context belongs to the device. Do not dereference
     * r->pixelmap here: the cockpit/mirror crash dump showed that pointer
     * holding a non-canonical stale/corrupt value at this exact site.
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
    path.write_text(text, encoding="utf-8")


def main() -> int:
    if len(sys.argv) != 2:
        print(f"Usage: {Path(sys.argv[0]).name} /path/to/dethrace-v0.10.1", file=sys.stderr)
        return 2

    root = Path(sys.argv[1]).resolve()
    device_h = root / "lib/BRender-v1.3.2/drivers/glrend/device.h"
    device_c = root / "lib/BRender-v1.3.2/drivers/glrend/device.c"
    devpmglf_c = root / "lib/BRender-v1.3.2/drivers/glrend/devpmglf.c"
    gstored_c = root / "lib/BRender-v1.3.2/drivers/glrend/gstored.c"

    for path in (device_h, device_c, devpmglf_c, gstored_c):
        if not path.is_file():
            raise FileNotFoundError(path)

    patch_device_h(device_h)
    patch_device_c(device_c)
    patch_devpmglf(devpmglf_c)
    patch_gstored(gstored_c)

    print("Applied cockpit renderer stability v19")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
