# v1.5 source port

This directory converts the already tested v1.5 binary proof-of-concept into reproducible source changes against **Dethrace v0.10.1**.

The source port has passed CI compilation and real-game visual/runtime testing with both Carmageddon and Splat Pack on Windows.

## What the patcher changes

The patcher edits three upstream files:

- `src/DETHRACE/pc-all/allsys.c`
  - changes the high-resolution graphics spec from 640×480 to 854×480,
  - centers the doubled 640×400 low-resolution interface at x=107,
  - clears the complete 854×480 interface destination before drawing,
  - maps mouse coordinates back into the centered 320×200 logical menu.
- `src/DETHRACE/common/grafdata.c`
  - changes the high-resolution graphics-data width from 640 to 854 so `CalcGrafDataIndex()` continues to match the selected graphics mode.
- `src/DETHRACE/common/loading.c`
  - shifts the five top/right HUD slots by +107 at load time,
  - shifts their dim rectangles together with them,
  - changes centre-anchored event slots 4, 5, 6, 9, 10 and 11 from x=320 to x=427.

No CAR-file damage-coordinate modification is included. That earlier experiment was reverted during development and is not part of the stable v1.5 behavior.

## Why 854×480 is Hor+

Dethrace already derives the 3D camera aspect from the active render width and height. Once the high-resolution mode is genuinely 854×480, the camera therefore uses the wider aspect without requiring a separate FOV override.

## Applying locally

Start from a clean checkout of Dethrace v0.10.1, then run:

```text
python apply-v1.5-source-port.py <path-to-clean-dethrace-v0.10.1>
```

The script intentionally checks that every expected v0.10.1 source fragment occurs exactly once. It aborts rather than silently patching an unexpected source revision.

## Data files

The source port accepts both original HEADUP data and the already modified HEADUP files created by the earlier private Modernizer tests. For the five right-side HUD slots it detects whether the X coordinate is still inside the original 640-wide range before applying the +107 shift, so those local test files are not shifted twice.

For a future public release, original/unmodified game data remains the preferred input. Original Carmageddon and Splat Pack data are not part of this repository.


## Validation result

Validated on 2026-10-02:

- clean Dethrace v0.10.1 source checkout patched successfully,
- Windows x64 build completed successfully in GitHub Actions,
- main game test passed,
- Splat Pack test passed,
- menus/videos, mouse mapping, 16:9 presentation and HUD/race-message placement matched the expected v1.5 behavior.

The source port is therefore considered the confirmed implementation of the v1.5 widescreen work.
