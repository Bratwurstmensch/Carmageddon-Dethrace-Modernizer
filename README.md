# Carmageddon Dethrace Modernizer

**Carmageddon Dethrace Modernizer** is a Windows-focused quality-of-life package for running the original **Carmageddon** and **Splat Pack** through [Dethrace](https://github.com/dethrace-labs/dethrace).

It combines a true widescreen presentation option, modern XInput controls, increased draw distance, improved distant detail, an original-aspect-ratio 4:3 runtime, optional German/Uncut integration, and a guided target-first installer.

> **No original Carmageddon or Splat Pack game data is included.**  
> You need your own legally obtained game data.

## Highlights

- **True 16:9 gameplay mode** at 854×480 in HiRes/OpenGL mode.
- **Original 4:3 mode** for players who prefer the classic presentation.
- **Modern XInput controller support** for Xbox-compatible controllers.
- **Native analog steering** on the left stick.
- **Analog acceleration and braking/reverse** on the right and left triggers.
- **500-unit high-resolution draw distance**.
- **Reduced distant pedestrian/object pop-in** while keeping the original short gameplay/AI activation radius.
- **Full-detail opponent car models** retained at distance instead of switching to simplified models.
- **Centered 16:9 menus, map, videos and race overlays**.
- **Corrected 16:9 mouse coordinates** in centered menu surfaces.
- **Source-verified 16:9 Damage HUD correction**.
- **Carmageddon + Splat Pack support**.
- **Optional German/Uncut integration (experimental)** from the user's own legally owned German data.
- **Non-destructive target-first installer**: source installations remain untouched.

## 16:9 or 4:3?

Both runtimes are included because they serve different preferences.

### 16:9 — recommended for third-person / external-camera play

The 16:9 runtime is the more modern presentation and is recommended if you normally drive using the external camera.

It provides the full widescreen view together with the Modernizer draw-distance, detail and controller improvements.

### 4:3 — recommended for cockpit-focused play

Carmageddon's cockpit artwork was authored as **2D 4:3 artwork**. It cannot be cleanly expanded into genuine 16:9 without inventing image data that does not exist in the original assets.

The Modernizer centers and adapts the cockpit as far as practical, but the underlying 4:3 nature is still visible—especially when looking left or right.

If the cockpit view is your preferred way to play, the **4:3 runtime is recommended**. It still includes the Modernizer's increased draw distance, distant-detail improvements and modern XInput/analog controls.

## Controller layout

The XInput launchers use the same modern layout in both the 16:9 and 4:3 runtimes.

| Controller input | Action |
| --- | --- |
| Left stick | Analog steering |
| Right trigger | Analog accelerate |
| Left trigger | Analog brake / reverse |
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
| Right-stick click | Toggle cockpit view |
| Left-stick click | Horn |

No AntiMicroX or external controller-mapping application is required.

## Known limitations

### 16:9 cockpit

The cockpit is based on fixed 4:3 2D artwork. The Modernizer can center and position it for widescreen play, but it cannot turn the original cockpit artwork into native 16:9 artwork.

The limitation is most obvious while looking left or right. For players who primarily use cockpit view, the 4:3 runtime gives the most coherent presentation.

### Pre-countdown cockpit crash

A crash can occur in the 16:9 runtime if you switch into cockpit view **before the race-start countdown has begun** and immediately look left or right.

Current workaround: wait until the countdown/race has started before rapidly changing cockpit/look views.

This issue has not been observed during normal driving after the race has begun in current testing.

### German/Uncut localization is experimental

The German/Uncut option works by validating and locally transforming data from the user's own supported German Carmageddon installation.

It is intentionally marked **experimental**. Minor visual/localization issues remain, including some menu flicker or imperfect presentation in places. The normal English installation is the recommended default.

## Installation

Run:

```text
Install-Modernizer.cmd
```

The installer uses a **target-first** workflow:

1. choose a new/empty target folder;
2. choose the desired components;
3. select the original/English Carmageddon installation;
4. if German/Uncut was selected, select the supported German installation;
5. all selected source paths are validated **before the large copy/install phase begins**;
6. review the preflight summary and start installation.

If an invalid source folder is selected, the installer lets you choose another folder instead of forcing you to restart the complete installation.

The source installations are treated as read-only.

### Component selection

- **1** — 16:9 widescreen runtime
- **2** — XInput controller support
- **3** — German/Uncut localization (**experimental**)

Examples:

- `12` — 16:9 + XInput
- `123` — 16:9 + XInput + German/Uncut
- `2` — 4:3 + XInput

Pressing **Enter** at component selection defaults to **16:9 + XInput**.

## Installed launchers

Depending on selected components and detected Splat Pack data, the target folder can contain:

- `Start-Carmageddon.cmd` — 4:3
- `Start-Carmageddon-XInput.cmd` — 4:3 + XInput
- `Start-Carmageddon-16x9.cmd` — 16:9
- `Start-Carmageddon-16x9-XInput.cmd` — 16:9 + XInput
- equivalent `Start-CARSPLAT...` launchers for Splat Pack

The package deliberately contains **two game runtimes**:

- `Runtime4x3\dethrace-4x3-v0.10.1.exe` — original-aspect-ratio Modernizer runtime
- `dethrace-16x9-v1.5.exe` — validated 16:9 Goldstandard runtime

This keeps the stable 16:9 implementation isolated from the 4:3 presentation while allowing both to share the same Modernizer gameplay/detail improvements.

## What the Modernizer changes

### Draw distance

The high-resolution runtime uses a **500-unit far plane** and prevents individual race settings from unexpectedly shortening the Modernizer draw distance.

### Distant pedestrians and objects

The original short gameplay/AI activation distance is preserved, while distant pedestrian/object sprites can still be rendered farther away. This reduces obvious pop-in without extending their gameplay activation range.

### Opponent car detail

Opponent cars retain their full principal model instead of switching to lower-detail car actors based on distance.

### 16:9 presentation

The widescreen runtime includes the validated work for:

- 854×480 HiRes/OpenGL output;
- centered 640-wide menu/video content;
- corrected mouse mapping;
- centered map and race overlays;
- cockpit positioning;
- rear-view placement;
- right-edge A/P/O and Damage HUD alignment.

## Carmageddon and Splat Pack

The installer automatically detects supported Splat Pack data when present and installs the matching launchers and integration.

You do not need to select separate main-game and Splat Pack folders manually when they are part of a supported installation layout.

## Project status

The gameplay/runtime work is considered **feature-frozen for the release candidate**. The 16:9 Goldstandard and the 4:3 parity runtime have both been real-world tested.

The remaining release work is installer/documentation validation rather than additional gameplay experimentation, unless a genuine release-blocking problem is discovered.

## Relationship to Dethrace

This project builds on the work of the [Dethrace contributors](https://github.com/dethrace-labs/dethrace) and has been developed against **Dethrace v0.10.1**.

This repository is not an official Dethrace project.

## Credits

The Modernizer project is by **Bratwurstmensch**.

Investigation, scripting, packaging and documentation were developed with extensive assistance from **ChatGPT by OpenAI**.

See [docs/CREDITS.md](docs/CREDITS.md) for additional attribution.

## Legal

Carmageddon and related assets belong to their respective rights holders. This repository is not affiliated with the Carmageddon rights holders and does not distribute original Carmageddon/Splat Pack game data.

## License

Modernizer code and tooling in this repository are released under the **GNU General Public License v3.0**. See [LICENSE](LICENSE).

For Dethrace itself, refer to its repository and license notices.
