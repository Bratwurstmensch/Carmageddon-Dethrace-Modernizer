# v0.8.0-rc2 release notes

RC2 is a release-cleanup build based on the already validated RC1 code and installer paths.

## Changes since RC1

- completes the English-language installer experience;
- translates the two remaining Splat Pack XInput error messages;
- suppresses the localized Windows `pause` prompt and displays an English prompt instead;
- updates documentation to reflect completed RC validation;
- keeps the original German localization string `TRF.` unchanged.

## Functional status

The core component combinations have passed real-world testing:

- `2` — standard 4:3 + XInput;
- `3` — standard 4:3 + German/Uncut;
- `12` — 16:9 + XInput;
- `123` — 16:9 + XInput + German/Uncut.

The tested paths cover Carmageddon and Splat Pack where applicable, including XInput, German/Uncut integration, 16:9 behavior, source-verified Damage HUD patching and complete target-directory uninstall.

## Release model

The installer is target-first. Source installations are read-only, and no complete original Carmageddon or Splat Pack game data is included.
