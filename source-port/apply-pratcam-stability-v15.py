#!/usr/bin/env python3
"""Fix Pratcam sequence bounds and harden its render path.

The v14 crash log placed the access violation inside DoPratcam (render stage 34).
The stock NextPratcamChunk logic increments gCurrent_pratcam_chunk but compares
number_of_chunks against the *old* chunk index. At the end of a sequence this
allows one-past-the-end access to chunks[gCurrent_pratcam_chunk].

This patch:
- fixes that off-by-one transition
- validates sequence/chunk/alternative/flic indices
- prevents zero-sound random ranges
- adds null guards around Pratcam render resources

No cockpit positions, controller mappings, physics, or analog response values
are changed.
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

    old_next = r'''void NextPratcamChunk(void) {
    int i;
    int random_number;
    int count;
    tPrat_alternative* current_alternative;

    if (gCurrent_pratcam_index == -1) {
        gCurrent_pratcam_index = gCurrent_ambient_prat_sequence;
    } else {
        EndFlic(&gPrat_flic);
    }
    count = gCurrent_pratcam_chunk;
    gCurrent_pratcam_chunk++;
    if (gPratcam_sequences[gCurrent_pratcam_index].number_of_chunks <= count) {
        if (gPending_ambient_prat == -1) {
            ChangeAmbientPratcamNow(gCurrent_ambient_prat_sequence, gPratcam_sequences[gCurrent_pratcam_index].repeat_chunk);
        } else {
            ChangeAmbientPratcamNow(gPending_ambient_prat, 0);
        }
    } else {
        gLast_pratcam_frame_time = 0;
        random_number = IRandomBetween(0, 99);
        for (i = 0; i < gPratcam_sequences[gCurrent_pratcam_index].chunks[gCurrent_pratcam_chunk].number_of_alternatives; i++) {
            current_alternative = &gPratcam_sequences[gCurrent_pratcam_index].chunks[gCurrent_pratcam_chunk].alternatives[i];
            random_number -= current_alternative->chance;
            if (random_number <= 0) {
                gCurrent_pratcam_alternative = i;
                gPrat_flic.data_start = NULL;
                StartFlic(NULL, -1, &gPrat_flic, gPratcam_flics[current_alternative->ref].data_length,
                    (tS8*)gPratcam_flics[current_alternative->ref].data, gPrat_buffer, 0, 0, 0);
                if (current_alternative->sound_chance == 0) {
                    return;
                }
                if (!PercentageChance(current_alternative->sound_chance)) {
                    return;
                }
                if (gCurrent_pratcam_precedence == 0 && DRS3OutletSoundsPlaying(gDriver_outlet)) {
                    return;
                }
                DRS3StartSound(gDriver_outlet, current_alternative->sound_ids[IRandomBetween(0, current_alternative->number_of_sounds - 1)]);
                return;
            }
        }
        NextPratcamChunk();
    }
}'''

    new_next = r'''void NextPratcamChunk(void) {
    int i;
    int random_number;
    int next_sequence;
    tPrat_alternative* current_alternative;
    tPrat_sequence* current_sequence;

    if (gPratcam_sequences == NULL || gPratcam_flics == NULL
        || gNumber_of_prat_sequences <= 0 || gNumber_of_prat_flics <= 0
        || gPrat_buffer == NULL) {
        gCurrent_pratcam_index = -1;
        return;
    }

    if (gCurrent_pratcam_index == -1) {
        if (gCurrent_ambient_prat_sequence < 0
            || gCurrent_ambient_prat_sequence >= gNumber_of_prat_sequences) {
            return;
        }
        gCurrent_pratcam_index = gCurrent_ambient_prat_sequence;
    } else {
        if (gCurrent_pratcam_index < 0 || gCurrent_pratcam_index >= gNumber_of_prat_sequences) {
            gCurrent_pratcam_index = -1;
            return;
        }
        EndFlic(&gPrat_flic);
    }

    current_sequence = &gPratcam_sequences[gCurrent_pratcam_index];
    gCurrent_pratcam_chunk++;

    /*
     * Original Dethrace compared number_of_chunks with the previous chunk
     * index, then indexed using the incremented value. That permits a
     * one-past-the-end chunks[] access when the current flic finishes.
     */
    if (gCurrent_pratcam_chunk >= current_sequence->number_of_chunks) {
        if (gPending_ambient_prat == -1) {
            next_sequence = gCurrent_ambient_prat_sequence;
            if (next_sequence < 0 || next_sequence >= gNumber_of_prat_sequences) {
                gCurrent_pratcam_index = -1;
                return;
            }
            ChangeAmbientPratcamNow(next_sequence, current_sequence->repeat_chunk);
        } else {
            next_sequence = gPending_ambient_prat;
            if (next_sequence < 0 || next_sequence >= gNumber_of_prat_sequences) {
                gPending_ambient_prat = -1;
                gCurrent_pratcam_index = -1;
                return;
            }
            ChangeAmbientPratcamNow(next_sequence, 0);
        }
        return;
    }

    if (gCurrent_pratcam_chunk < 0
        || current_sequence->chunks[gCurrent_pratcam_chunk].number_of_alternatives <= 0
        || current_sequence->chunks[gCurrent_pratcam_chunk].number_of_alternatives
            > COUNT_OF(current_sequence->chunks[gCurrent_pratcam_chunk].alternatives)) {
        NextPratcamChunk();
        return;
    }

    gLast_pratcam_frame_time = 0;
    random_number = IRandomBetween(0, 99);

    for (i = 0; i < current_sequence->chunks[gCurrent_pratcam_chunk].number_of_alternatives; i++) {
        current_alternative = &current_sequence->chunks[gCurrent_pratcam_chunk].alternatives[i];
        random_number -= current_alternative->chance;
        if (random_number > 0) {
            continue;
        }

        if (current_alternative->ref < 0 || current_alternative->ref >= gNumber_of_prat_flics
            || gPratcam_flics[current_alternative->ref].data == NULL
            || gPratcam_flics[current_alternative->ref].data_length <= 0) {
            NextPratcamChunk();
            return;
        }

        gCurrent_pratcam_alternative = i;
        gPrat_flic.data_start = NULL;
        StartFlic(NULL, -1, &gPrat_flic,
            gPratcam_flics[current_alternative->ref].data_length,
            (tS8*)gPratcam_flics[current_alternative->ref].data,
            gPrat_buffer, 0, 0, 0);

        if (current_alternative->sound_chance == 0) {
            return;
        }
        if (!PercentageChance(current_alternative->sound_chance)) {
            return;
        }
        if (gCurrent_pratcam_precedence == 0 && DRS3OutletSoundsPlaying(gDriver_outlet)) {
            return;
        }
        if (current_alternative->number_of_sounds <= 0
            || current_alternative->number_of_sounds > COUNT_OF(current_alternative->sound_ids)) {
            return;
        }

        DRS3StartSound(
            gDriver_outlet,
            current_alternative->sound_ids[
                IRandomBetween(0, current_alternative->number_of_sounds - 1)]);
        return;
    }

    NextPratcamChunk();
}'''
    text = replace_once(text, old_next, new_next, "NextPratcamChunk safe transition")

    text = replace_once(
        text,
        r'''    if (gAusterity_mode) {
        return;
    }
    right_image = gProgram_state.current_car.prat_cam_right;''',
        r'''    if (gAusterity_mode) {
        return;
    }
    if (gBack_screen == NULL || gPrat_buffer == NULL
        || gPrat_buffer->pixels == NULL
        || gPrat_flic.frame_period == 0) {
        return;
    }
    right_image = gProgram_state.current_car.prat_cam_right;''',
        "DoPratcam base resource guards",
    )

    text = replace_once(
        text,
        r'''#ifdef DETHRACE_3DFX_PATCH
    PDUnlockRealBackScreen(1);
    if (gDevious_2d) {
        gPrat_model->vertices[1].p.v[0] = gProgram_state.current_car.prat_left + offset;''',
        r'''#ifdef DETHRACE_3DFX_PATCH
    PDUnlockRealBackScreen(1);
    if (gDevious_2d
        && gPrat_model != NULL
        && gPrat_actor != NULL
        && gPrat_material != NULL
        && g2d_camera != NULL
        && gDepth_buffer != NULL) {
        gPrat_model->vertices[1].p.v[0] = gProgram_state.current_car.prat_left + offset;''',
        "DoPratcam 2D object guards",
    )

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
    print("Applied v15 Pratcam sequence/bounds stability fix")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
