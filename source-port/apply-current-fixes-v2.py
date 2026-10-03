#!/usr/bin/env python3
"""Repair the current Modernizer test after apply-current-test.py.

This patch deliberately restores the exact draw-distance implementation from
the previously successful draw-distance-500-test branch, corrects the
rear-view mirror X placement, and forces local SMK cutscenes to be attempted
for this test build.
"""
from pathlib import Path
import sys


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)


def patch_draw_distance(init_path: Path, depth_path: Path, brucetrk_path: Path) -> None:
    # This is intentionally the same camera/track visibility patch used by the
    # earlier Dethrace-16x9-DrawDistance500-Test build that rendered landscapes
    # far into the distance.
    init_text = init_path.read_text(encoding="utf-8")

    old_init = "        camera_ptr->yon_z = gCamera_yon;"
    new_init = "        camera_ptr->yon_z = gGraf_spec_index == 1 ? 500.0f : gCamera_yon;"
    count = init_text.count(old_init)
    if count < 1:
        raise RuntimeError("draw distance: AllocateCamera yon assignment not found")
    init_text = init_text.replace(old_init, new_init)

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


def patch_mirror(init_path: Path, graphics_path: Path) -> None:
    init_text = init_path.read_text(encoding="utf-8")

    # Keep the mirror sub-pixelmap geometry in its original car-data coordinate
    # system. The +107 widescreen translation belongs at the final framebuffer
    # render/copy stage, not here.
    init_text = replace_once(
        init_text,
        "            gProgram_state.current_car.mirror_left + (gBack_screen->width == 854 ? 107 : 0),\n"
        "            gProgram_state.current_car.mirror_top,",
        "            gProgram_state.current_car.mirror_left,\n"
        "            gProgram_state.current_car.mirror_top,",
        "rearview subpixelmap restore original X",
    )
    init_path.write_text(init_text, encoding="utf-8")

    graphics_text = graphics_path.read_text(encoding="utf-8")
    graphics_text = replace_once(
        graphics_text,
        "        gRearview_screen->base_x = MAX(0, gScreen_wobble_x + gProgram_state.current_car.mirror_left);",
        "        gRearview_screen->base_x = MAX(0, gScreen_wobble_x + gProgram_state.current_car.mirror_left\n"
        "            + (gBack_screen->width == 854 ? 107 : 0));",
        "rearview base X fixed-bugs path",
    )
    graphics_text = replace_once(
        graphics_text,
        "        gRearview_screen->base_x = gScreen_wobble_x + gProgram_state.current_car.mirror_left;",
        "        gRearview_screen->base_x = gScreen_wobble_x + gProgram_state.current_car.mirror_left\n"
        "            + (gBack_screen->width == 854 ? 107 : 0);",
        "rearview base X legacy path",
    )
    # apply-current-test.py already added +107 to the explicit mirror copy path.
    graphics_path.write_text(graphics_text, encoding="utf-8")


def patch_cutscenes(cutscene_path: Path) -> None:
    text = cutscene_path.read_text(encoding="utf-8")

    # For this test build, always attempt cutscene playback when a cutscene
    # function is called. This removes both legacy suppression flags from the
    # equation while we validate the locally imported GOG SMK files.
    text = replace_once(
        text,
        "    if (!gSound_override && !gCut_scene_override) {",
        "    if (1) {",
        "force cutscene playback test",
    )

    # The GOG Carmageddon disc image provides MIX_INTR.SMK but no LOGO.SMK.
    # Force the known full-game intro name so game-mode auto-detection cannot
    # accidentally turn the opening intro into an empty filename.
    text = replace_once(
        text,
        """void DoOpeningAnimation(void) {

    PlaySmackerFile("LOGO.SMK");
    PlaySmackerFile(harness_game_info.defines.INTRO_SMK_FILE);
    WaitForNoKeys();
}""",
        """void DoOpeningAnimation(void) {

    PlaySmackerFile("MIX_INTR.SMK");
    WaitForNoKeys();
}""",
        "force GOG Carmageddon intro",
    )
    cutscene_path.write_text(text, encoding="utf-8")


def main() -> int:
    if len(sys.argv) != 2:
        print(f"Usage: {Path(sys.argv[0]).name} /path/to/dethrace-v0.10.1", file=sys.stderr)
        return 2

    root = Path(sys.argv[1]).resolve()
    init_path = root / "src/DETHRACE/common/init.c"
    depth_path = root / "src/DETHRACE/common/depth.c"
    brucetrk_path = root / "src/DETHRACE/common/brucetrk.c"
    graphics_path = root / "src/DETHRACE/common/graphics.c"
    cutscene_path = root / "src/DETHRACE/common/cutscene.c"

    for path in (init_path, depth_path, brucetrk_path, graphics_path, cutscene_path):
        if not path.is_file():
            raise FileNotFoundError(path)

    patch_draw_distance(init_path, depth_path, brucetrk_path)
    patch_mirror(init_path, graphics_path)
    patch_cutscenes(cutscene_path)

    print("Applied restored draw distance + mirror + forced cutscene test fixes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
