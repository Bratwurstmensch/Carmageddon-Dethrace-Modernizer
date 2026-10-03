#!/usr/bin/env python3
"""Pratcam direct-blit lock fix v17.

v16 correctly bypassed the crashing GL quad path, but it unlocked the real
backbuffer immediately before DRPixelmapRectangleCopy. In the OpenGL/3DFX
path that leaves gBack_screen->pixels NULL, so the 8->16-bit copy crashes.

v17 keeps the CPU backbuffer locked for the direct blit. No visual positions,
analog controls, cockpit logic or Pratcam timing are changed.
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

    old = r'''        PDUnlockRealBackScreen(1);
        if (prat_copy_width > 0 && prat_copy_height > 0) {
            DRPixelmapRectangleCopy(
                gBack_screen,
                gProgram_state.current_car.prat_left + offset,
                gProgram_state.current_car.prat_top + y_offset,
                gPrat_buffer,
                0, 0,
                prat_copy_width, prat_copy_height);
        }
        PDLockRealBackScreen(1);'''

    new = r'''        /*
         * DRPixelmapRectangleCopy converts INDEX_8 -> RGB_565 on the CPU.
         * Therefore gBack_screen->pixels must be valid. v16 unlocked the
         * backbuffer here, which made pixels NULL and caused an immediate
         * access violation in Copy8BitTo16BitRectangle.
         */
        PDLockRealBackScreen(1);
        if (gBack_screen->pixels != NULL
            && prat_copy_width > 0
            && prat_copy_height > 0) {
            DRPixelmapRectangleCopy(
                gBack_screen,
                gProgram_state.current_car.prat_left + offset,
                gProgram_state.current_car.prat_top + y_offset,
                gPrat_buffer,
                0, 0,
                prat_copy_width, prat_copy_height);
        }'''

    text = replace_once(text, old, new, "Pratcam direct blit lock")
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
    print("Applied v17 Pratcam direct-blit backbuffer lock fix")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
