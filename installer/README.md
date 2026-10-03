# Modernizer installer v0.1 (test)

This installer is intentionally conservative.

It installs the validated v1.5 source-port executable, launchers and XInput helpers into an existing Carmageddon/Dethrace folder. It does **not** modify original game data and it does **not** overwrite the normal `dethrace.exe`.

## Installation behavior

The installer:

1. asks for the existing Dethrace/Carmageddon folder,
2. verifies `DATA/GENERAL.TXT`,
3. detects `CARSPLAT/DATA`,
4. backs up any files that would be replaced,
5. installs the Modernizer executable and launchers,
6. stores an uninstall manifest under `.dethrace-modernizer/`.

Splat Pack launchers are only installed when `CARSPLAT/DATA` exists.

## Uninstall

Run `Uninstall-Modernizer.cmd` from the game folder.

Files that existed before installation are restored from the backup. Files created by the Modernizer are removed.

## Not included yet

The German localization integration is deliberately not part of this first installer test. That workflow will be added separately after the base installer has been validated.


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
