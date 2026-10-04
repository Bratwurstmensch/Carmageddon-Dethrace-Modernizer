# Release Candidate — Carmageddon Dethrace Modernizer

This release candidate combines the validated **16:9 Goldstandard runtime**, the new **4:3 Modernizer parity runtime**, modern XInput controls and the polished target-first installer.

## Headline features

- true 16:9 Carmageddon/Splat Pack gameplay option;
- fullscreen 16:9 cockpit 3D rendering across the complete 854×480 frame;
- removal of artificial cockpit top/bottom black bars from the old 4:3 render window;
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

**16:9** now includes fullscreen cockpit 3D rendering as well as the modern widescreen presentation. The 3D world fills the complete 854×480 frame even in cockpit view.

**4:3** remains available for players who prefer the completely original cockpit framing.

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

The 3D world now renders across the complete 854×480 frame behind the cockpit, removing the old top/bottom black bars.

The original cockpit itself is still 2D 4:3 artwork. Side-looking views therefore still expose the limits of the original assets.

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
- fullscreen 16:9 cockpit rendering in both Carmageddon and Splat Pack;
- 16:9 + XInput;
- 4:3 runtime;
- 4:3 + XInput;
- Carmageddon main game;
- Splat Pack;
- experimental German/Uncut integration;
- invalid-path recovery during installer preflight.

The gameplay runtimes are feature-frozen for this release candidate unless a release-blocking issue is discovered.
