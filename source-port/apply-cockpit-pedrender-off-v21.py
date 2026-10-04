#!/usr/bin/env python3
"""Cockpit stability diagnostic v21.

On top of v20, disable only the Modernizer's extra distant-pedestrian render
path. Keep the 500-unit world draw distance, full opponent-car detail, original
100-entry lollipop queue, native analog XInput, widescreen/cockpit fixes, and
all later stability/gameplay patches.

Reason: the latest v20 crash is in BRender BrSimpleRemove while
number_of_lollipops == 100. RenderLollipops repeatedly BrActorRelink()s queued
actors, so this A/B test isolates the extra distant-pedestrian relinking load.
"""
from pathlib import Path
import sys


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected 1 match, found {count}")
    return text.replace(old, new, 1)


def patch_pedestrians(path: Path) -> None:
    text = path.read_text(encoding="utf-8")

    text = replace_once(
        text,
        "#define ACTIVE_PED_DXDZ 11.f\n#define RENDER_PED_DXDZ 500.f\n",
        "#define ACTIVE_PED_DXDZ 11.f\n",
        "remove distant pedestrian render-distance constant",
    )

    old = """            if (the_pedestrian->actor->parent == gDont_render_actor
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

    new = """            if (the_pedestrian->actor->parent == gDont_render_actor
                && (x_delta > ACTIVE_PED_DXDZ || z_delta > ACTIVE_PED_DXDZ)) {
                the_pedestrian->active = 0;
            } else if (the_pedestrian->hit_points == -100) {"""

    text = replace_once(text, old, new, "disable distant pedestrian render queue")
    path.write_text(text, encoding="utf-8")


def main() -> int:
    if len(sys.argv) != 2:
        print(f"Usage: {Path(sys.argv[0]).name} /path/to/dethrace-v0.10.1", file=sys.stderr)
        return 2

    root = Path(sys.argv[1]).resolve()
    pedestrn = root / "src/DETHRACE/common/pedestrn.c"
    if not pedestrn.is_file():
        raise FileNotFoundError(pedestrn)

    patch_pedestrians(pedestrn)
    print("Applied v21 diagnostic: distant pedestrian rendering disabled")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
