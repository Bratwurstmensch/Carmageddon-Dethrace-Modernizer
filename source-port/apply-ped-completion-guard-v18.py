#!/usr/bin/env python3
"""Pedestrian completion guard v18.

Observed symptom on stage "Coole Crashs":
the race can finish with "Every pedestrian wasted" while the visible HUD
counter is still far below the stage total.

The original completion check trusts only:
    gProgram_state.peds_killed >= gTotal_peds

v18 keeps that counter check, but adds an independent verification against
the actual pedestrian array. The race may only end for pedestrians when no
live human pedestrian remains.

If the counter check fires early, the race continues and a one-time
ped-completion-guard.log is written with the relevant counts.

No rendering, cockpit, controller, analog, physics, or race reward logic is
otherwise changed.
"""
from pathlib import Path
import sys


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected 1 match, found {count}")
    return text.replace(old, new, 1)


def patch_pedestrn(path: Path) -> None:
    text = path.read_text(encoding="utf-8")

    text = replace_once(
        text,
        "#include <stdlib.h>\n#include <time.h>\n",
        "#include <stdlib.h>\n#include <stdio.h>\n#include <time.h>\n",
        "stdio include",
    )

    old = r'''void CheckLastPed(void) {

    if (gNet_mode == eNet_mode_none && gProgram_state.peds_killed >= gTotal_peds) {
        NewTextHeadupSlot(eHeadupSlot_misc, 0, 5000, -kFont_MEDIUMHD, GetMiscString(kMiscString_EveryPedestrianWasted));
        RaceCompleted(eRace_over_peds);
    }
}'''

    new = r'''void CheckLastPed(void) {
    int i;
    int actual_total;
    int actual_alive;
    int actual_dead;
    static int logged_false_completion;
    FILE* log_file;
    tPedestrian_data* pedestrian;

    if (gNet_mode != eNet_mode_none) {
        return;
    }

    actual_total = 0;
    actual_alive = 0;
    actual_dead = 0;

    /*
     * Independently verify the real pedestrian state. This deliberately
     * mirrors GetPedPosition()'s definition of a dead human pedestrian.
     */
    if (gPedestrian_array != NULL && gPed_count > 0) {
        for (i = 0; i < gPed_count; i++) {
            pedestrian = &gPedestrian_array[i];
            if (pedestrian->ref_number >= 100) {
                continue;
            }

            actual_total++;
            if (pedestrian->hit_points == -100
                || pedestrian->current_action == pedestrian->fatal_car_impact_action
                || pedestrian->current_action == pedestrian->fatal_ground_impact_action
                || pedestrian->current_action == pedestrian->giblets_action) {
                actual_dead++;
            } else {
                actual_alive++;
            }
        }
    }

    if (gProgram_state.peds_killed >= gTotal_peds) {
        if (actual_total > 0 && actual_alive == 0) {
            NewTextHeadupSlot(eHeadupSlot_misc, 0, 5000, -kFont_MEDIUMHD, GetMiscString(kMiscString_EveryPedestrianWasted));
            RaceCompleted(eRace_over_peds);
            return;
        }

        /*
         * Counter-based completion fired while real pedestrians are still
         * alive. Suppress the false finish and leave a compact diagnostic.
         */
        if (!logged_false_completion) {
            log_file = fopen("ped-completion-guard.log", "wt");
            if (log_file != NULL) {
                fprintf(log_file,
                    "Carmageddon Modernizer pedestrian completion guard v18\n"
                    "race_time=%u\n"
                    "peds_killed=%d\n"
                    "gTotal_peds=%d\n"
                    "gPed_count=%d\n"
                    "actual_total_humans=%d\n"
                    "actual_alive_humans=%d\n"
                    "actual_dead_humans=%d\n"
                    "gNumber_of_lollipops=%d\n",
                    (unsigned int)GetRaceTime(),
                    gProgram_state.peds_killed,
                    gTotal_peds,
                    gPed_count,
                    actual_total,
                    actual_alive,
                    actual_dead,
                    gNumber_of_lollipops);
                fclose(log_file);
            }
            logged_false_completion = 1;
        }
    }
}'''

    text = replace_once(text, old, new, "robust pedestrian completion guard")
    path.write_text(text, encoding="utf-8")


def main() -> int:
    if len(sys.argv) != 2:
        print(f"Usage: {Path(sys.argv[0]).name} /path/to/dethrace-v0.10.1", file=sys.stderr)
        return 2

    root = Path(sys.argv[1]).resolve()
    pedestrn = root / "src/DETHRACE/common/pedestrn.c"
    if not pedestrn.is_file():
        raise FileNotFoundError(pedestrn)

    patch_pedestrn(pedestrn)
    print("Applied v18 pedestrian completion guard + diagnostic")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
