# Technical notes

## Release-candidate baseline

Carmageddon Dethrace Modernizer **v1.0-rc1** is based on **Dethrace v0.10.1**.

The current release candidate is tied to the manually validated **RC9** behavior rather than to every later experiment in the development branches.

Reference RC9 runtime hashes:

- 16:9: `1df66ba28020f08635773a992e1254ce1b746a11f7a4d77598aff236d7f8ddf6`
- 4:3: `80dd90f4a74b6caaae19fb336cbd86e5ce0dc3058c509d0da691ecf1511dc9f7`

See [RELEASE-CANDIDATE.md](RELEASE-CANDIDATE.md) for the full manual validation matrix.

## 16:9 presentation

The widescreen path changes the HiRes/OpenGL presentation to **854×480**.

Key behavior includes:

- Hor+ 3D presentation through the active render aspect;
- centered original 640-wide menu/video surfaces;
- full-width framebuffer clearing;
- corrected mouse-coordinate mapping for the centered 320×200 logical menu;
- repositioned/centered race and HUD elements;
- full-frame 854×480 3D cockpit world behind the original 4:3 cockpit artwork;
- final right-edge alignment of the 16:9 rear-view render surface.

The cockpit bitmap itself is original fixed 4:3 artwork. The Modernizer does not synthesize replacement art.

## Shared runtime improvements

Both 4:3 and 16:9 Modernizer runtimes include:

- 500-unit high-resolution far plane;
- protection against race data unexpectedly shortening that Modernizer far plane;
- full principal opponent-car models at distance;
- distant pedestrian/object sprite rendering out to the Modernizer distance while retaining the original short gameplay/AI activation radius;
- expanded lollipop render capacity;
- native analog XInput;
- RC9 CD-audio OGG/WAV compatibility.

## Native analog XInput

The release-candidate controller patch is:

```text
source-port/apply-native-analog-xinput-v13.py
```

Validated driving inputs:

- left stick: analog steering;
- RT: analog accelerate;
- LT: analog brake/reverse;
- face/shoulder/stick buttons: normal driving functions.

Action Replay remains intentionally keyboard/mouse-oriented. The game's initial player-name text entry also still requires a keyboard; the native XInput layer intentionally does not emulate text entry.

## Release-candidate stability finding

The reproducible GitHub Actions runtimes were manually smoke-tested after build. The 4:3 runtime remained stable in the tested main-game and Splat Pack scenarios. The 16:9 runtime reproduced the same remaining limitation as the RC9 baseline: cockpit left/right look and rapid cockpit/view switching can still crash, especially near the beginning of a race.

This is documented as a known v1.0-rc1 limitation rather than hidden by the release packaging. The recommended path for cockpit-heavy play is the 4:3 runtime.

## RC9 CD audio

Upstream Dethrace v0.10.1 follows the GOG convention and checks for `MUSIC/Track02.ogg`.

The Modernizer eXoDOS workflow extracts original Red Book audio as lossless PCM WAV, so RC9 makes two isolated runtime changes:

1. `AudioBackend_InitCDA()` accepts either `Track02.ogg` or `Track02.wav`.
2. `AudioBackend_PlayCDA()` tries `Track0N.ogg` first, then `Track0N.wav`.

Source patch:

```text
source-port/apply-rc9-cdda-wav-fallback.py
```

This behavior was confirmed in-game with both Carmageddon and Splat Pack.

## eXoDOS CUE/BIN installer work

The tested RC9 installer can discover common Carmageddon and Splat Pack CUE/BIN layouts, including the eXoDOS filename `SPLAT PACK.CUE`.

For supported MODE1/MODE2 layouts it:

- parses the CUE sheet;
- locates the data track and INDEX 01;
- reads ISO9660 directly from the BIN image;
- extracts SMK cutscenes;
- extracts Red Book AUDIO tracks losslessly to WAV;
- writes main-game music under `MUSIC`;
- writes Splat Pack music under `CARSPLAT\MUSIC`.

No virtual drive, Daemon Tools or external archive extractor is required for that path.

## Damage HUD

The **manually tested RC9** release-candidate behavior uses an installer-side, source-verified Damage HUD data correction.

The installer preflights applicable car data and recognizes both:

- the previously supported representation;
- the alternate encrypted representation confirmed by the eXoDOS source.

In the successful eXoDOS test it reported 49 changed files, including 21 files matched through the alternate encrypted representation.

A later development branch explored moving the same correction into the engine. That experiment is not the v1.0-rc1 reference until it receives equivalent real-game validation.

## German / Uncut

German integration is data-driven and remains experimental.

The installer only applies transformations to verified source revisions. Unsupported revisions are declined instead of being modified heuristically.

The public repository does not contain original Carmageddon German assets.

## Reproducible runtime build

The authoritative release-candidate pipeline is:

```text
.github/workflows/build-v1.0-rc1-runtimes.yml
```

It checks out clean Dethrace v0.10.1 trees, applies the release-candidate source chain and builds separate 4:3 and 16:9 Windows runtimes.

Historical source scripts are kept for traceability. The workflow, not the presence of an experimental script, defines what belongs to v1.0-rc1.

## Project boundary

The Modernizer deliberately separates generally useful Dethrace runtime changes from project-specific packaging/data handling.

Potential upstream engine changes are tracked in [UPSTREAM.md](UPSTREAM.md). Installer, localization and user-owned game-data transformations remain Modernizer-specific.
