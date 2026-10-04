# Release Candidate — Carmageddon Dethrace Modernizer

This release candidate combines the validated **16:9 Goldstandard runtime**, the new **4:3 Modernizer parity runtime**, modern XInput controls and the polished target-first installer.

## Headline features

- true 16:9 Carmageddon/Splat Pack gameplay option;
- original-aspect-ratio 4:3 Modernizer runtime;
- native analog XInput steering;
- analog RT acceleration and LT braking/reverse;
- modern digital controller mapping with no external mapper required;
- 500-unit high-resolution draw distance;
- reduced distant pedestrian/object pop-in while preserving original gameplay activation distance;
- full-detail opponent car models at distance;
- centered widescreen menus, videos, map and race overlays;
- corrected widescreen mouse coordinates;
- source-verified 16:9 Damage HUD correction;
- Carmageddon and Splat Pack support;
- optional experimental German/Uncut integration;
- non-destructive target-first installation from legally owned source data.

## Which runtime should I use?

**16:9** is recommended for players who mainly use the third-person/external camera. It gives the most modern presentation.

**4:3** is recommended for players who mainly use cockpit view. Carmageddon's cockpit is fixed 2D artwork authored for 4:3, so its limitations become visible in widescreen—especially while looking left/right.

Both runtimes include the Modernizer draw-distance, distant-detail and XInput/analog-control improvements.

## Controller layout

| Input | Action |
| --- | --- |
| Left stick | Analog steering |
| RT | Analog accelerate |
| LT | Analog brake / reverse |
| A | Handbrake |
| B | Wheelspin |
| X | Repair |
| Y | Recover |
| Back / View | Map |
| Start / Menu | Escape / pause/menu |
| D-pad | Arrow keys / menu navigation |
| Right stick left/right | Look left/right |
| Right stick up | Look forward |
| LB / RB | Look left/right |
| Right-stick click | Toggle cockpit |
| Left-stick click | Horn |

## Installer improvements

The installer now validates selected source paths before the time-consuming copy/install phase begins.

If a wrong source path is selected, the user can choose another folder instead of restarting the full installation. German/Uncut is only requested when explicitly selected and is clearly marked experimental.

Installer performance has also been improved through:

- Windows Robocopy for the large source copy;
- cached SHA-256 results;
- reduced redundant whole-set re-hashing;
- append-only transaction journaling;
- same-volume move-based rollback backups where possible.

## Known limitations

### 16:9 cockpit artwork

The original cockpit is 2D 4:3 artwork. The Modernizer centers and adapts it for widescreen, but cannot create genuine missing 16:9 cockpit artwork. Side-looking views therefore make the 4:3 nature of the cockpit especially obvious.

For cockpit-heavy play, use the 4:3 runtime.

### Pre-countdown cockpit crash

In the 16:9 runtime, a crash can occur when switching into cockpit view before the race-start countdown and immediately looking left/right.

Workaround: wait until the countdown/race has started before rapidly changing cockpit/look views.

### German/Uncut — experimental

German/Uncut integration is functional but not as polished as the normal English path. Minor menu flicker and other small visual/localization imperfections remain.

## Release model

The installer is target-first. Original/English and optional German source installations remain untouched.

No complete original Carmageddon or Splat Pack game data is included.

## Validation status

Real-world testing has covered:

- 16:9 runtime;
- 16:9 + XInput;
- 4:3 runtime;
- 4:3 + XInput;
- Carmageddon main game;
- Splat Pack;
- experimental German/Uncut integration;
- invalid-path recovery during installer preflight.

The gameplay runtimes are feature-frozen for this release candidate unless a release-blocking issue is discovered.
