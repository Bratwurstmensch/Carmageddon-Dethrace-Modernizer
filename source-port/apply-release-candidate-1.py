#!/usr/bin/env python3
"""Release Candidate 1: authoritative pedestrian completion.

On top of v18, make the actual live pedestrian array the authoritative
source for the "all pedestrians wasted" race-completion condition.

- If no live human pedestrian remains, complete the race normally.
- If counters claim completion early, keep racing and retain the v18
  one-time diagnostic for this RC.
- HUD counters remain unchanged.

No rendering, controller, cockpit, analog, physics, reward, or Pratcam
behaviour is changed.
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

    old = r'''    if (gProgram_state.peds_killed >= gTotal_peds) {
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
    }'''

    new = r'''    /*
     * RC1: the pedestrian array is authoritative. This preserves the
     * intended original win condition even if the HUD counters drift.
     */
    if (actual_total > 0 && actual_alive == 0) {
        NewTextHeadupSlot(eHeadupSlot_misc, 0, 5000, -kFont_MEDIUMHD, GetMiscString(kMiscString_EveryPedestrianWasted));
        RaceCompleted(eRace_over_peds);
        return;
    }

    /*
     * Keep the v18 diagnostic during the RC test only. If the legacy
     * counters claim completion while live pedestrians remain, suppress
     * that false finish and record the discrepancy once.
     */
    if (gProgram_state.peds_killed >= gTotal_peds && !logged_false_completion) {
        log_file = fopen("ped-completion-guard.log", "wt");
        if (log_file != NULL) {
            fprintf(log_file,
                "Carmageddon Modernizer pedestrian completion guard RC1\n"
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
    }'''

    text = replace_once(text, old, new, "authoritative pedestrian completion")
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
    print("Applied RC1 authoritative pedestrian completion")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
