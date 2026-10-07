# Carmageddon Dethrace Modernizer

A community project by **Bratwurstmensch** for making the original **Carmageddon** and **Splat Pack** more convenient to run through [Dethrace](https://github.com/dethrace-labs/dethrace).

The long-term goal is a reproducible, user-friendly modernizer that can combine:

- a tested 16:9 presentation path,
- centered menus and videos,
- corrected mouse coordinates in centered menus,
- centered race messages / bonus / checkpoint / countdown overlays,
- optional XInput controller support,
- and a guided integration path for legally owned German game data.

> **No original Carmageddon game data is included in this repository.**

## Release candidate

The current stabilized release-candidate branch is: `release/v1.0-rc1`.

RC1 uses a **target-first** installer: users choose a new/empty target directory, then select optional 16:9, XInput and German/Uncut components. Source installations are read-only. A standard Dethrace v0.10.1 4:3 runtime is included in every target, while the validated v1.5 widescreen runtime is installed only when 16:9 is selected.

The core `2`, `3`, `12` and `123` component paths have now passed real-world validation. RC2 is a release-cleanup build: the functional game and patch paths remain unchanged, while the remaining installer-facing text has been normalized to English.

## Stable validation update — 2026-10-07

The current tested baseline is intentionally frozen unless a new reproducible issue is found.

- Main game: complete-race smoke test passed.
- Splat Pack: complete-race smoke test passed.
- 16:9: stable after retiring the experimental pedestrian-completion guard.
- Cockpit: no further changes are planned for the validated baseline.
- 4:3: external Damage HUD background and flashing damage-unit overlays are restored when shared 16:9-shifted CAR data is detected.
- The historical `apply-ped-completion-guard-v18.py` and `apply-release-candidate-1.py` scripts remain in the repository for development history only and are not part of stable build workflows.

## Current status

**Source-port milestone: validated.** The widescreen/menu/mouse/HUD behavior has been confirmed in both Carmageddon and Splat Pack.

**Installer milestone: validated.** The Windows installer has completed a real install → main-game/Splat Pack launch → uninstall cycle successfully, including backup restoration and automatic Splat Pack detection.

The original private/tested **v1.5** proof-of-concept is functionally complete for the 16:9 and XInput work. Its behavior has been validated with both the main game and Splat Pack.

The v1.5 widescreen work has now also been reproduced as a **clean Dethrace v0.10.1 source port**, built successfully in GitHub Actions and visually validated with both Carmageddon and Splat Pack on Windows. The patched proof-of-concept executable itself is still not committed here.

### Confirmed in the v1.5 proof-of-concept

- 854-pixel-wide 16:9 output path in HiRes/OpenGL mode
- centered menu and video surfaces
- full-width interface clearing
- corrected mouse mapping for the centered 640-pixel menu surface
- centered event slots 4, 5, 6, 9, 10 and 11
- support for both Carmageddon and Splat Pack
- portable launchers using relative paths
- optional XInput-to-keyboard mapper for Xbox-compatible controllers

Technical details and hashes are documented in [docs/TECHNICAL.md](docs/TECHNICAL.md) and [patches/v1.5-patch-manifest.json](patches/v1.5-patch-manifest.json).

## German localization

German localization integration is a **project goal**, not yet a redistributable game-data package.

The intended public solution is to detect a user's legally owned German Carmageddon data and perform the required local integration/patching without redistributing copyrighted original assets.

## Repository layout

- `package/` — launcher/controller tooling intended for a future release package
- `patches/` — documentation of the validated v1.5 binary proof-of-concept
- `docs/` — technical notes, credits, legal boundaries and roadmap
- `LICENSE` — GPL-3.0

## Requirements

For actual gameplay, users will need their own legally obtained Carmageddon data. Splat Pack support similarly requires the user's own Splat Pack data.

Current controller tooling targets Windows and uses the system XInput and Win32 keyboard APIs.

## Relationship to Dethrace

This project is built around the work of the [Dethrace contributors](https://github.com/dethrace-labs/dethrace). Dethrace's project goals explicitly include modern-platform and quality-of-life improvements, and its contribution guide also welcomes creative forks that do not belong in the main project.

The validated proof-of-concept was investigated against **Dethrace v0.10.1**.

This repository is not an official Dethrace project.

## Development note

The 16:9 investigation, patch development, packaging and controller tooling were carried out by **Bratwurstmensch** with extensive assistance from **ChatGPT by OpenAI**, including binary analysis, scripting and documentation support.

## Legal / project boundaries

Carmageddon and related assets belong to their respective rights holders. This repository does not include original game data and is not affiliated with the Carmageddon rights holders.

See [docs/CREDITS.md](docs/CREDITS.md) for attribution details.

## License

Code and tooling in this repository are released under the **GNU General Public License v3.0**. See [LICENSE](LICENSE).

For the underlying Dethrace project, refer to its own repository and license notices.
