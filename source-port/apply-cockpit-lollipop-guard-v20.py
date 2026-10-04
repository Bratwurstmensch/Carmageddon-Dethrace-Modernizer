#!/usr/bin/env python3
"""Cockpit stability diagnostic v20.

Keep the full v19 runtime, but restore the original 100-entry lollipop queue
limit while retaining the 500-unit distant pedestrian render attempt.

Reason: the Modernizer widened gLollipops and its queue limit from 100 to 1024.
Both observed cockpit crashes manifest as corruption inside BRender renderer
objects after the extended-detail changes. This test isolates renderer pressure
from the widened pedestrian/lollipop queue without removing the other v19
features.

Also record gNumber_of_lollipops in cockpit-crash.log.
"""
from pathlib import Path
import sys


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected 1 match, found {count}")
    return text.replace(old, new, 1)


def patch_graphics_h(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = replace_once(
        text,
        "extern br_actor* gLollipops[1024];",
        "extern br_actor* gLollipops[100];",
        "restore lollipop declaration limit",
    )
    path.write_text(text, encoding="utf-8")


def patch_graphics(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = replace_once(
        text,
        "br_actor* gLollipops[1024];",
        "br_actor* gLollipops[100];",
        "restore lollipop storage limit",
    )
    text = replace_once(
        text,
        "    } else if (gNumber_of_lollipops >= 1024) {",
        "    } else if (gNumber_of_lollipops >= 100) {",
        "restore lollipop queue limit",
    )

    text = replace_once(
        text,
        '        "rearview_camera=0x%p\\r\\n",',
        '        "rearview_camera=0x%p\\r\\n"\n'
        '        "number_of_lollipops=%d\\r\\n",',
        "crash log lollipop format",
    )
    text = replace_once(
        text,
        "        (void*)gRearview_depth_buffer,\n"
        "        (void*)gRearview_camera);",
        "        (void*)gRearview_depth_buffer,\n"
        "        (void*)gRearview_camera,\n"
        "        gNumber_of_lollipops);",
        "crash log lollipop value",
    )
    path.write_text(text, encoding="utf-8")


def main() -> int:
    if len(sys.argv) != 2:
        print(f"Usage: {Path(sys.argv[0]).name} /path/to/dethrace-v0.10.1", file=sys.stderr)
        return 2

    root = Path(sys.argv[1]).resolve()
    graphics_h = root / "src/DETHRACE/common/graphics.h"
    graphics = root / "src/DETHRACE/common/graphics.c"

    for path in (graphics_h, graphics):
        if not path.is_file():
            raise FileNotFoundError(path)

    patch_graphics_h(graphics_h)
    patch_graphics(graphics)
    print("Applied v20 original 100-entry lollipop queue diagnostic")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
