# Modernizer installer — v1.0-rc1

The v1.0 release-candidate installer is a non-destructive, target-first Windows installer. It builds a finished Modernizer installation from the user's own legally obtained source data and leaves the source installation untouched.

## Current installation behavior

The installer:

1. selects/validates the target directory;
2. selects and validates the original/English Carmageddon source;
3. detects main-game and optional Splat Pack data automatically;
4. offers independent 16:9, XInput and experimental German/Uncut components;
5. installs separate 4:3 and optional 16:9 Modernizer runtimes;
6. imports supported loose/GOG media and tested eXoDOS-style CUE/BIN media;
7. extracts SMK cutscenes directly from supported BIN/ISO9660 layouts;
8. extracts Red Book AUDIO tracks losslessly to WAV;
9. applies the source-verified 16:9 Damage HUD correction when appropriate;
10. creates launchers/shortcuts and keeps rollback/uninstall state.

The tested RC9 path supports both Carmageddon and Splat Pack and does not require mounting the original CD image.

## v1.0-rc1 final smoke-test findings

- 4:3 main game and Splat Pack: stable in the final smoke test.
- 16:9 main game and Splat Pack: generally functional, with a documented cockpit/look crash tendency when looking left/right, especially near race start.
- Native analog XInput: working.
- Initial player-name text entry: keyboard required; controller text entry is not implemented.
- Videos, WAV CD audio and the 16:9 Damage HUD path were confirmed in the tested eXoDOS-style RC9 installation.

## Uninstall

Run `Uninstall-Modernizer.cmd` from the game folder.

Files that existed before installation are restored from the backup. Files created by the Modernizer are removed.

## German / Uncut

German/Uncut integration is included as an **experimental** optional component and is applied only to verified source revisions. Unsupported revisions are declined rather than patched heuristically. Original German game assets are not redistributed.


## Uninstaller user experience

The uninstaller restores/removes managed files first, prints the final result and waits for user acknowledgement. Only after the user closes the success prompt are the two Modernizer uninstaller files cleaned up by a temporary helper.


## Real-world validation

The v0.1 installer completed a full real-world install/uninstall cycle successfully on 2026-10-02, including automatic Splat Pack detection and restoration of pre-existing Modernizer-managed files.

The installation-state directory exists only while the Modernizer is installed. Its absence after a successful uninstall is expected.


## Planned component selection

The public installer must not require the German localization.

The user first selects the Carmageddon installation to modernize, then chooses independent components:

- 16:9 source port
- XInput controller support
- German/Uncut localization

16:9 and XInput must work without any German source files.

Only when German/Uncut localization is selected does the installer request additional source installations:

1. German Carmageddon installation
2. Original/English Carmageddon installation

For both source installations the installer automatically detects:

- main game: DATA
- Splat Pack: CARSPLAT/DATA

Splat Pack support is applied only when the required Splat data is present; the user should not have to select separate main/Splat source folders manually.


## Target-first installation model

The public installer should use a target-first, non-destructive workflow.

1. **Target directory**
   - The user selects where the finished Modernizer installation should live.
   - This is the only directory the installer writes to.
   - Prefer a new/empty folder; an existing supported target may be used only after validation and backup.

2. **Original/English source installation**
   - Read-only source for the base Carmageddon data.
   - The installer automatically detects both `DATA` and optional `CARSPLAT/DATA`.
   - The source installation is never modified.

3. **German source installation (optional)**
   - Requested only when German/Uncut is selected.
   - Also treated read-only.
   - The installer automatically detects main-game and Splat Pack data.

4. **Component selection**
   - 16:9 source port
   - XInput support
   - German/Uncut localization

All selected components are assembled into the target directory. Source installations remain untouched.


## Public installer language and 16:9 HUD data

The public installer UI, launcher error messages, controller error messages and uninstaller should use **English by default** for an international audience. Documentation may remain multilingual (for example README.md + README.de.md).

The 16:9 component must also install the previously validated Damage HUD right-edge correction. The target-first copy otherwise restores the original centered Damage HUD coordinates.

Validated correction coverage:

- 21 main-game high-resolution CAR files
- 28 Splat Pack high-resolution CAR files
- 49 files total
- damage X offset: +214
- damage background X: +214
- first external damage dim rectangle left/right: +214

For the development test package this validated payload is bundled directly. Before a public release candidate, prefer converting it to source-verified generated deltas/transformations so complete modified game-data files are not published in the repository.


## v0.6b validation

The target-first installer model has now passed real-world validation for both principal installation paths.

Validated on 2026-10-03:

- `12` = 16:9 + XInput
  - target-first copy from an original/English Carmageddon Max Pack installation
  - main game launches
  - Splat Pack launches
  - XInput launchers work
  - portable SDL runtime works in a fresh target directory
  - validated 16:9 Damage HUD right-edge correction is applied successfully
  - `Uninstall-Modernizer.cmd` removes the generated target installation successfully

- `123` = 16:9 + XInput + German/Uncut
  - German main-game integration succeeds
  - German Splat Pack integration succeeds
  - main game and Splat Pack launch successfully
  - XInput works
  - 16:9 HUD correction remains correct
  - `Uninstall-Modernizer.cmd` removes the generated target installation successfully

The source installations remained untouched in both tests.

### Remaining release hardening

Before a public release candidate, replace the temporary full-file Damage HUD test payload with a source-verified patch/delta method so the public package does not redistribute complete modified game-data files. Also keep the installer UI in English for the international release.


## v0.7b source-patch validation

Validated successfully on 2026-10-03:

- target-first install path `12` (16:9 + XInput)
- original/English Carmageddon Max Pack source
- main game and Splat Pack launch successfully
- source-verified Damage HUD patch applies successfully
- all 49 supported CAR files are patched from verified source hashes
- resulting HUD files match the known validated target hashes
- Damage HUD remains correctly aligned to the right edge in-game
- no complete modified Damage HUD game-data files are shipped in the test package

This confirms the release-hardened Damage HUD patch path in real-world use.


## v0.8.0 RC1

The release-candidate installer source is now integrated under `installer/`.

RC1 always installs an isolated standard Dethrace v0.10.1 4:3 runtime under `Runtime4x3/`. Optional 16:9 installs the separately validated v1.5 widescreen runtime at the target root. This avoids DLL/runtime conflicts and makes XInput-only and German/Uncut-only targets directly runnable without requiring a pre-existing `dethrace.exe` in the user's source installation.

The release package keeps source installations read-only and contains no complete original Carmageddon game data. The 49-file widescreen Damage HUD correction is performed from exact source hashes using minimal source-verified replacements and exact target-hash verification.


## RC1 final validation

Validated successfully in real-world testing:

- `2` = standard 4:3 Dethrace + XInput
- `3` = standard 4:3 Dethrace + German/Uncut
- `12` = 16:9 + XInput
- `123` = 16:9 + XInput + German/Uncut

For the tested paths, both Carmageddon and Splat Pack launch successfully where applicable, XInput works, German/Uncut integration works, the source-verified 16:9 Damage HUD correction remains correct, and the target-first uninstaller removes the generated target installation successfully.

This completes validation of the core RC1 component combinations.


## v0.8.0 RC2

RC2 is a release-cleanup build based on the validated RC1 functionality.

Changes:
- the two remaining Splat Pack XInput error messages are now English;
- command-window pause prompts are explicitly English instead of inheriting the Windows UI language;
- package documentation reflects the completed validation of `2`, `3`, `12` and `123`;
- the original German localization string `TRF.` remains unchanged by design.

No gameplay, widescreen, XInput, German/Uncut or Damage HUD patch logic was intentionally changed.
