#!/usr/bin/env python3
"""Pedestrian visibility test v23.

Start from stable v21 and extend only *human* pedestrian activation distance
from 11 to 60 units. Keep non-human pedestrian-system objects (powerups,
barrels/mines/etc.) on the original 11-unit threshold to avoid the flicker
introduced by the global v22 change.

The risky render-only distant-pedestrian path remains disabled. This uses the
normal DoPedestrian/MungePedModel path for humans only.
"""
from pathlib import Path
import sys


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected 1 match, found {count}")
    return text.replace(old, new, 1)


def main() -> int:
    if len(sys.argv) != 2:
        print(f"Usage: {Path(sys.argv[0]).name} /path/to/dethrace-v0.10.1", file=sys.stderr)
        return 2

    root = Path(sys.argv[1]).resolve()
    path = root / "src/DETHRACE/common/pedestrn.c"
    if not path.is_file():
        raise FileNotFoundError(path)

    text = path.read_text(encoding="utf-8")

    text = replace_once(
        text,
        "#define ACTIVE_PED_DXDZ 11.f\n",
        "#define ACTIVE_PED_DXDZ 11.f\n#define ACTIVE_HUMAN_DXDZ 60.f\n",
        "add human-only activation radius",
    )

    old = """            if ((the_pedestrian->actor->parent != gDont_render_actor || (x_delta <= ACTIVE_PED_DXDZ && z_delta <= ACTIVE_PED_DXDZ))
                && (gPedestrians_on || the_pedestrian->ref_number >= 100)
                && the_pedestrian->hit_points != -100) {"""
    new = """            if ((the_pedestrian->actor->parent != gDont_render_actor
                    || (x_delta <= (the_pedestrian->ref_number < 100 ? ACTIVE_HUMAN_DXDZ : ACTIVE_PED_DXDZ)
                        && z_delta <= (the_pedestrian->ref_number < 100 ? ACTIVE_HUMAN_DXDZ : ACTIVE_PED_DXDZ)))
                && (gPedestrians_on || the_pedestrian->ref_number >= 100)
                && the_pedestrian->hit_points != -100) {"""
    text = replace_once(text, old, new, "action replay activation split")

    old = """            if (the_pedestrian->actor->parent == gDont_render_actor
                && (x_delta > ACTIVE_PED_DXDZ || z_delta > ACTIVE_PED_DXDZ)) {
                the_pedestrian->active = 0;"""
    new = """            if (the_pedestrian->actor->parent == gDont_render_actor
                && (x_delta > (the_pedestrian->ref_number < 100 ? ACTIVE_HUMAN_DXDZ : ACTIVE_PED_DXDZ)
                    || z_delta > (the_pedestrian->ref_number < 100 ? ACTIVE_HUMAN_DXDZ : ACTIVE_PED_DXDZ))) {
                the_pedestrian->active = 0;"""
    text = replace_once(text, old, new, "normal activation split")

    text = replace_once(
        text,
        "            ped_respawn_animate = x_delta <= ACTIVE_PED_DXDZ && z_delta <= ACTIVE_PED_DXDZ;",
        "            ped_respawn_animate = x_delta <= ACTIVE_HUMAN_DXDZ && z_delta <= ACTIVE_HUMAN_DXDZ;",
        "human respawn visibility radius",
    )

    path.write_text(text, encoding="utf-8")
    print("Applied v23 human-only pedestrian activation radius: 60 units")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
