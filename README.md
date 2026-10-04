# Carmageddon Dethrace Modernizer

A Windows-focused quality-of-life and compatibility package for running the original **Carmageddon** and **Splat Pack** with [Dethrace](https://github.com/dethrace-labs/dethrace).

The project is developed and tested by **Bratwurstmensch** with extensive assistance from **ChatGPT by OpenAI**.

> **No original Carmageddon or Splat Pack game data is included.**
> You need your own legally obtained game data.

## v1.0 release-candidate status

The current public-preparation branch is **v1.0-rc1**. Runtime work is feature-frozen around the successfully tested **RC9** build.

Validated on Windows with Carmageddon and Splat Pack:

- true 16:9 gameplay at 854×480 in HiRes/OpenGL mode;
- original-aspect-ratio 4:3 Modernizer runtime;
- fullscreen 16:9 cockpit 3D viewport behind the original 4:3 cockpit artwork;
- right-edge-aligned 16:9 rear-view mirror;
- centered menus, map, videos and race overlays;
- corrected mouse mapping for the centered menu surface;
- native analog XInput steering;
- analog RT acceleration and LT brake/reverse;
- 500-unit high-resolution draw distance;
- full-detail opponent cars retained at distance;
- reduced distant pedestrian/object pop-in while preserving the original short gameplay activation radius;
- Carmageddon and Splat Pack launch paths;
- installer backup/rollback/uninstall handling;
- optional experimental German/Uncut integration from user-owned data;
- eXoDOS-style CUE/BIN cutscene extraction;
- eXoDOS-style Red Book CD-audio extraction to lossless WAV;
- Dethrace OGG-first / WAV-fallback CD-audio playback;
- source-verified 16:9 Damage HUD correction, including the tested alternate encrypted eXoDOS data representation.

## Tested RC9 runtime hashes

The successfully tested RC9 runtime executables have these SHA-256 hashes:

- **16:9:** `1df66ba28020f08635773a992e1254ce1b746a11f7a4d77598aff236d7f8ddf6`
- **4:3:** `80dd90f4a74b6caaae19fb336cbd86e5ce0dc3058c509d0da691ecf1511dc9f7`

The RC9 test used the eXoDOS-style Carmageddon source with both main-game and Splat Pack CUE/BIN images. Cutscenes, music playback and the 16:9 Damage HUD were all confirmed working.

See [docs/RELEASE-CANDIDATE.md](docs/RELEASE-CANDIDATE.md) for the validation matrix.

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
| D-pad | Menu / arrow-key navigation |
| Right stick left/right | Look left/right |
| Right stick up | Look forward |
| LB / RB | Look left/right |
| Right-stick click | Toggle cockpit |
| Left-stick click | Horn |

The normal driving layout intentionally does **not** remap Dethrace's larger Action Replay control scheme. Keyboard/mouse is recommended for Replay mode.

## 16:9 and 4:3

### 16:9

The widescreen runtime is the modern presentation path. It renders the 3D world across the complete 854×480 frame and keeps the original 640-wide 2D interface/cockpit assets centered where appropriate.

The cockpit artwork itself remains original 4:3 artwork, so looking left/right can still expose the limitations of the source assets.

### 4:3

The separate 4:3 runtime keeps the original presentation while retaining the Modernizer gameplay/detail improvements and native analog XInput support.

## GOG and eXoDOS-style sources

The installer supports normal loose-file/GOG-style installations and the tested eXoDOS layout.

For eXoDOS-style CUE/BIN sources it can:

- detect Carmageddon and Splat Pack CD images;
- parse supported MODE1/MODE2 data-track layouts;
- read ISO9660 directly from the BIN image;
- extract the original SMK cutscenes without mounting the disc;
- extract Red Book AUDIO tracks losslessly as 44.1 kHz / 16-bit / stereo WAV;
- install main-game music under `MUSIC\Track0N.wav`;
- install Splat Pack music under `CARSPLAT\MUSIC\Track0N.wav`.

The RC9 runtime keeps the existing GOG convention first: `Track0N.ogg` is preferred when present; otherwise `Track0N.wav` is used.

## German / Uncut

German/Uncut integration is **experimental** and works only with verified source revisions.

The public project does not redistribute original German game assets. The installer validates user-owned source data and applies local transformations.

A currently tested eXoDOS Splat Pack revision is not yet supported by the German localization transform. In that case the installer safely declines the unsupported German/Uncut path instead of applying an unverified patch.

## Installation

The release package is intended to be started with:

```text
Install-Modernizer.cmd
```

Default component selection is **16:9 + XInput**. The source installations are treated as read-only; the Modernizer creates its own finished installation and tracks rollback/uninstall state.

## Source-port structure

The repository contains reproducible source patchers against **Dethrace v0.10.1** in [source-port/](source-port/).

The tested RC9 CD-audio fix is documented and reproducible through:

```text
source-port/apply-rc9-cdda-wav-fallback.py
```

The historical development scripts are intentionally retained because they document how the final widescreen, cockpit, mirror, detail and controller behavior was reached. See [source-port/README.md](source-port/README.md).

## Upstream relevance

Several parts of the Modernizer directly overlap long-standing Dethrace feature requests, especially:

- native Xbox/XInput controller support;
- widescreen presentation;
- higher draw distance.

See [docs/UPSTREAM.md](docs/UPSTREAM.md) for the relevant upstream issues and which changes are suitable candidates for clean upstream pull requests.

## Known limitations

- Original cockpit artwork is fixed 4:3 artwork and cannot become native 16:9 without new art.
- German/Uncut integration remains experimental and source-revision-specific.
- Action Replay still uses its original keyboard/mouse-oriented control scheme.
- This project currently targets Windows for its tested installer/controller workflow.

## Relationship to Dethrace

This project builds on the work of the Dethrace contributors and has been developed against **Dethrace v0.10.1**.

It is **not an official Dethrace project**.

The repository is licensed under **GNU GPL v3.0**. Before the first public binary release, the project is also seeking a brief upstream clarification because Dethrace's repository currently contains a GPLv3 LICENSE while older README wording still references public-domain/non-commercial terms.

## Credits and legal

Carmageddon, Splat Pack, their assets, audio, text and artwork belong to their respective rights holders. No original game data is included here.

See [docs/CREDITS.md](docs/CREDITS.md) for attribution and [LICENSE](LICENSE) for the repository license.
