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
