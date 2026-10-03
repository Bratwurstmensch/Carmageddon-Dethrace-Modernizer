#!/usr/bin/env python3
"""Add a lightweight Windows crash diagnostic for cockpit/render crashes.

No gameplay, visual, or controller behaviour is changed.

On an unhandled Windows exception the game writes cockpit-crash.log in the
current working directory with:
- exception code/address/module RVA
- last render stage
- cockpit/mirror/view state
- relevant render pixelmap pointers

This is intentionally small so it can stay enabled during normal testing.
"""
from pathlib import Path
import sys


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected 1 match, found {count}")
    return text.replace(old, new, 1)


def patch_graphics(path: Path) -> None:
    text = path.read_text(encoding="utf-8")

    text = replace_once(
        text,
        """#include <limits.h>
#include <stdlib.h>

#include <math.h>
""",
        """#include <limits.h>
#include <stdlib.h>
#include <stdio.h>

#ifdef _WIN32
#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#endif

#include <math.h>
""",
        "Windows crash diagnostic includes",
    )

    text = replace_once(
        text,
        """// GLOBAL: CARM95 0x00520040
int gPalette_munged;
""",
        """#ifdef _WIN32
static volatile LONG gModernizer_render_stage;
static int gModernizer_crash_filter_installed;

static LONG WINAPI Modernizer_CrashDiagnostic(EXCEPTION_POINTERS* exception_info) {
    HANDLE file;
    char buffer[2048];
    DWORD written;
    HMODULE module;
    uintptr_t module_base;
    uintptr_t exception_address;
    uintptr_t exception_rva;
    DWORD exception_code;
    int length;

    module = GetModuleHandleA(NULL);
    module_base = (uintptr_t)module;
    exception_code = exception_info != NULL && exception_info->ExceptionRecord != NULL
        ? exception_info->ExceptionRecord->ExceptionCode
        : 0;
    exception_address = exception_info != NULL && exception_info->ExceptionRecord != NULL
        ? (uintptr_t)exception_info->ExceptionRecord->ExceptionAddress
        : 0;
    exception_rva = exception_address >= module_base
        ? exception_address - module_base
        : 0;

    length = _snprintf(
        buffer,
        sizeof(buffer) - 1,
        "Carmageddon Modernizer cockpit crash diagnostic v14\\r\\n"
        "exception_code=0x%08lX\\r\\n"
        "exception_address=0x%p\\r\\n"
        "module_base=0x%p\\r\\n"
        "exception_rva=0x%p\\r\\n"
        "render_stage=%ld\\r\\n"
        "cockpit_on=%d\\r\\n"
        "cockpit_image_index=%d\\r\\n"
        "mirror_on=%d\\r\\n"
        "which_view=%d\\r\\n"
        "map_mode=%d\\r\\n"
        "back_screen=0x%p\\r\\n"
        "render_screen=0x%p\\r\\n"
        "depth_buffer=0x%p\\r\\n"
        "rearview_screen=0x%p\\r\\n"
        "rearview_depth_buffer=0x%p\\r\\n"
        "rearview_camera=0x%p\\r\\n",
        (unsigned long)exception_code,
        (void*)exception_address,
        (void*)module_base,
        (void*)exception_rva,
        gModernizer_render_stage,
        gProgram_state.cockpit_on,
        gProgram_state.cockpit_image_index,
        gProgram_state.mirror_on,
        (int)gProgram_state.which_view,
        gMap_mode,
        (void*)gBack_screen,
        (void*)gRender_screen,
        (void*)gDepth_buffer,
        (void*)gRearview_screen,
        (void*)gRearview_depth_buffer,
        (void*)gRearview_camera);

    if (length < 0) {
        length = 0;
    }
    if (length >= (int)sizeof(buffer)) {
        length = sizeof(buffer) - 1;
    }
    buffer[length] = '\\0';

    file = CreateFileA(
        "cockpit-crash.log",
        GENERIC_WRITE,
        FILE_SHARE_READ,
        NULL,
        CREATE_ALWAYS,
        FILE_ATTRIBUTE_NORMAL,
        NULL);
    if (file != INVALID_HANDLE_VALUE) {
        WriteFile(file, buffer, (DWORD)length, &written, NULL);
        FlushFileBuffers(file);
        CloseHandle(file);
    }

    return EXCEPTION_CONTINUE_SEARCH;
}

static void Modernizer_InstallCrashDiagnostic(void) {
    if (!gModernizer_crash_filter_installed) {
        SetUnhandledExceptionFilter(Modernizer_CrashDiagnostic);
        gModernizer_crash_filter_installed = 1;
    }
}

#define MODERNIZER_STAGE(N) (gModernizer_render_stage = (LONG)(N))
#else
#define Modernizer_InstallCrashDiagnostic() ((void)0)
#define MODERNIZER_STAGE(N) ((void)0)
#endif

// GLOBAL: CARM95 0x00520040
int gPalette_munged;
""",
        "crash diagnostic helper",
    )

    text = replace_once(
        text,
        """void RenderAFrame(int pDepth_mask_on) {
    int cat;
""",
        """void RenderAFrame(int pDepth_mask_on) {
    int cat;
""",
        "RenderAFrame anchor",
    )

    text = replace_once(
        text,
        """#ifdef DETHRACE_3DFX_PATCH
    if (gVoodoo_rush_mode >= 1) {
        gRender_screen->pixels = gBack_screen->pixels;
    }
#endif

    the_time = GetTotalTime();
""",
        """#ifdef DETHRACE_3DFX_PATCH
    if (gVoodoo_rush_mode >= 1) {
        gRender_screen->pixels = gBack_screen->pixels;
    }
#endif

    Modernizer_InstallCrashDiagnostic();
    MODERNIZER_STAGE(1);

    the_time = GetTotalTime();
""",
        "install diagnostic at frame start",
    )

    text = replace_once(
        text,
        """    cockpit_on = gProgram_state.cockpit_on
        && gProgram_state.cockpit_image_index >= 0
""",
        """    MODERNIZER_STAGE(2);
    cockpit_on = gProgram_state.cockpit_on
        && gProgram_state.cockpit_image_index >= 0
""",
        "stage cockpit state",
    )

    text = replace_once(
        text,
        """    {
        RenderShadows(gUniverse_actor, &gProgram_state.track_spec, gCamera, &gCamera_to_world);
        BrZbSceneRenderBegin(gUniverse_actor, gCamera, gRender_screen, gDepth_buffer);
        ProcessNonTrackActors(gRender_screen, gDepth_buffer, gCamera, &gCamera_to_world, &old_camera_matrix);
        ProcessTrack(gUniverse_actor, &gProgram_state.track_spec, gCamera, &gCamera_to_world, 0);
        RenderLollipops();
""",
        """    {
        MODERNIZER_STAGE(10);
        RenderShadows(gUniverse_actor, &gProgram_state.track_spec, gCamera, &gCamera_to_world);
        MODERNIZER_STAGE(11);
        BrZbSceneRenderBegin(gUniverse_actor, gCamera, gRender_screen, gDepth_buffer);
        MODERNIZER_STAGE(12);
        ProcessNonTrackActors(gRender_screen, gDepth_buffer, gCamera, &gCamera_to_world, &old_camera_matrix);
        MODERNIZER_STAGE(13);
        ProcessTrack(gUniverse_actor, &gProgram_state.track_spec, gCamera, &gCamera_to_world, 0);
        MODERNIZER_STAGE(14);
        RenderLollipops();
""",
        "main scene stages",
    )

    text = replace_once(
        text,
        """        if (!gAusterity_mode) {
            ProcessTrack(gUniverse_actor, &gProgram_state.track_spec, gCamera, &gCamera_to_world, 1);
        }
        RenderSplashes();
""",
        """        if (!gAusterity_mode) {
            MODERNIZER_STAGE(15);
            ProcessTrack(gUniverse_actor, &gProgram_state.track_spec, gCamera, &gCamera_to_world, 1);
        }
        MODERNIZER_STAGE(16);
        RenderSplashes();
""",
        "main scene later stages",
    )

    text = replace_once(
        text,
        """    if (gMirror_on__graphics) {
#ifdef DETHRACE_3DFX_PATCH
""",
        """    if (gMirror_on__graphics) {
        MODERNIZER_STAGE(20);
#ifdef DETHRACE_3DFX_PATCH
""",
        "mirror start stage",
    )

    text = replace_once(
        text,
        """        BrPixelmapFill(gRearview_depth_buffer, 0xFFFFFFFF);
        gRendering_mirror = 1;
        DoSpecialCameraEffect(gRearview_camera, &gRearview_camera_to_world);
        ConditionallyFillWithSky(gRearview_screen);
""",
        """        MODERNIZER_STAGE(21);
        BrPixelmapFill(gRearview_depth_buffer, 0xFFFFFFFF);
        gRendering_mirror = 1;
        MODERNIZER_STAGE(22);
        DoSpecialCameraEffect(gRearview_camera, &gRearview_camera_to_world);
        MODERNIZER_STAGE(23);
        ConditionallyFillWithSky(gRearview_screen);
""",
        "mirror setup stages",
    )

    text = replace_once(
        text,
        """        BrZbSceneRenderBegin(gUniverse_actor, gRearview_camera, gRearview_screen, gRearview_depth_buffer);
        ProcessNonTrackActors(
""",
        """        MODERNIZER_STAGE(24);
        BrZbSceneRenderBegin(gUniverse_actor, gRearview_camera, gRearview_screen, gRearview_depth_buffer);
        MODERNIZER_STAGE(25);
        ProcessNonTrackActors(
""",
        "mirror scene begin stages",
    )

    text = replace_once(
        text,
        """        ProcessTrack(gUniverse_actor, &gProgram_state.track_spec, gRearview_camera, &gRearview_camera_to_world, 0);
        RenderLollipops();
""",
        """        MODERNIZER_STAGE(26);
        ProcessTrack(gUniverse_actor, &gProgram_state.track_spec, gRearview_camera, &gRearview_camera_to_world, 0);
        MODERNIZER_STAGE(27);
        RenderLollipops();
""",
        "mirror track stages",
    )

    text = replace_once(
        text,
        """        if (!gAusterity_mode) {
            ProcessTrack(gUniverse_actor, &gProgram_state.track_spec, gRearview_camera, &gRearview_camera_to_world, 1);
        }
        RenderSplashes();
""",
        """        if (!gAusterity_mode) {
            MODERNIZER_STAGE(28);
            ProcessTrack(gUniverse_actor, &gProgram_state.track_spec, gRearview_camera, &gRearview_camera_to_world, 1);
        }
        MODERNIZER_STAGE(29);
        RenderSplashes();
""",
        "mirror late stages",
    )

    text = replace_once(
        text,
        """        if (cockpit_on) {
            CopyStripImage(
""",
        """        if (cockpit_on) {
            MODERNIZER_STAGE(30);
            CopyStripImage(
""",
        "cockpit bitmap stage",
    )

    text = replace_once(
        text,
        """            if (gMirror_on__graphics) {
                BrPixelmapRectangleCopy(
""",
        """            if (gMirror_on__graphics) {
                MODERNIZER_STAGE(31);
                BrPixelmapRectangleCopy(
""",
        "mirror blit stage",
    )

    text = replace_once(
        text,
        """        DimAFewBits();
        DoDamageScreen(the_time);
""",
        """        MODERNIZER_STAGE(32);
        DimAFewBits();
        MODERNIZER_STAGE(33);
        DoDamageScreen(the_time);
""",
        "damage stages",
    )

    text = replace_once(
        text,
        """            BrPixelmapFlush(gBack_screen);
            DoPratcam(the_time);
            DoHeadups(the_time);
        }
        DoInstruments(the_time);
        DoSteeringWheel(the_time);
""",
        """            BrPixelmapFlush(gBack_screen);
            MODERNIZER_STAGE(34);
            DoPratcam(the_time);
            MODERNIZER_STAGE(35);
            DoHeadups(the_time);
        }
        MODERNIZER_STAGE(36);
        DoInstruments(the_time);
        MODERNIZER_STAGE(37);
        DoSteeringWheel(the_time);
""",
        "overlay stages",
    )

    text = replace_once(
        text,
        """        if (!gAction_replay_mode || gAR_fudge_headups) {
            DrawPowerups(the_time);
        }
    }
""",
        """        if (!gAction_replay_mode || gAR_fudge_headups) {
            MODERNIZER_STAGE(38);
            DrawPowerups(the_time);
        }
    }
    MODERNIZER_STAGE(90);
""",
        "powerups/end stage",
    )

    path.write_text(text, encoding="utf-8")


def main() -> int:
    if len(sys.argv) != 2:
        print(f"Usage: {Path(sys.argv[0]).name} /path/to/dethrace-v0.10.1", file=sys.stderr)
        return 2

    root = Path(sys.argv[1]).resolve()
    graphics = root / "src/DETHRACE/common/graphics.c"
    if not graphics.is_file():
        raise FileNotFoundError(graphics)

    patch_graphics(graphics)
    print("Applied cockpit crash diagnostic v14 (no gameplay/visual changes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
