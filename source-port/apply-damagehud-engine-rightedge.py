#!/usr/bin/env python3
"""Move the 16:9 external Damage HUD correction into the engine.

Older Modernizer test installers modified every CAR data file by +214 pixels.
That made the installer unnecessarily dependent on exact game-data hashes.

This final patch keeps all source CAR data untouched and performs the same
placement at render time:
- external Damage HUD wobble X: +214 in 854-wide mode
- external damage background X: +214 in 854-wide mode
- external dim rectangles: +214 in 854-wide mode
- cockpit dim rectangles keep their existing +107 centering
- 4:3 behavior is unchanged
"""
from pathlib import Path
import sys


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: apply-damagehud-engine-rightedge.py <dethrace-source>")

    root = Path(sys.argv[1])
    path = root / "src" / "DETHRACE" / "common" / "displays.c"
    text = path.read_text(encoding="utf-8")

    text = replace_once(
        text,
        """            gProgram_state.current_car.dim_left[dim_index][i] + ((dim_index && gBack_screen->width == 854) ? 107 : 0),
            gProgram_state.current_car.dim_top[dim_index][i],
            gProgram_state.current_car.dim_right[dim_index][i] + ((dim_index && gBack_screen->width == 854) ? 107 : 0),""",
        """            gProgram_state.current_car.dim_left[dim_index][i]
                + (gBack_screen->width == 854 ? (dim_index ? 107 : 214) : 0),
            gProgram_state.current_car.dim_top[dim_index][i],
            gProgram_state.current_car.dim_right[dim_index][i]
                + (gBack_screen->width == 854 ? (dim_index ? 107 : 214) : 0),""",
        "Damage HUD dim rectangles",
    )

    text = replace_once(
        text,
        """        /* External damage coordinates are already shifted +214 by the
         * installer's source-verified CAR-data patch. Do not double-shift. */
        the_wobble_x = gProgram_state.current_car.damage_x_offset;""",
        """        /* Modernizer: keep CAR data original and right-anchor the
         * external Damage HUD at render time in 854-wide mode. */
        the_wobble_x = gProgram_state.current_car.damage_x_offset
            + (gBack_screen->width == 854 ? 214 : 0);""",
        "Damage HUD external wobble X",
    )

    text = replace_once(
        text,
        """                gProgram_state.current_car.damage_background_x,
                gProgram_state.current_car.damage_background_y,""",
        """                gProgram_state.current_car.damage_background_x
                    + (gBack_screen->width == 854 ? 214 : 0),
                gProgram_state.current_car.damage_background_y,""",
        "Damage HUD external background X",
    )

    path.write_text(text, encoding="utf-8")
    print("Applied engine-side 16:9 Damage HUD right-edge correction")


if __name__ == "__main__":
    raise SystemExit(main())
