# v1.0-rc1 release-candidate validation

This document records the **manually tested RC9 state** that is being prepared as Carmageddon Dethrace Modernizer **v1.0-rc1**.

## Reference runtimes

Base project: **Dethrace v0.10.1**

Reference SHA-256 values from the successful RC9 test package:

| Runtime | SHA-256 |
| --- | --- |
| 16:9 | `1df66ba28020f08635773a992e1254ce1b746a11f7a4d77598aff236d7f8ddf6` |
| 4:3 | `80dd90f4a74b6caaae19fb336cbd86e5ce0dc3058c509d0da691ecf1511dc9f7` |

The repository also contains a reproducible GitHub Actions pipeline. Compiler/toolchain metadata may make a rebuilt executable differ byte-for-byte even when the source patch chain is equivalent, so the hashes above are retained as the reference for the exact manually tested RC9 package.

## Reference installer source

The readable repository installer has been restored directly from the exact manually tested RC9 package and verified before commit.

- `installer/Install-Modernizer.ps1`
- size: **93,080 bytes**
- SHA-256: `4fbe060739a5a1a8fc64958229865f03f91df1e07162e094ddf68db79513cbcd`

The verification also confirmed the expected RC9 eXoDOS media markers (`cue-bin-audio`, `SPLAT PACK.CUE`, and WAV-track handling). Temporary compressed restore payloads were removed after the readable source was committed.

## RC9 validation matrix

| Area | Result | Notes |
| --- | --- | --- |
| Carmageddon 16:9 runtime | PASS WITH KNOWN LIMITATION | Stable outside the known cockpit/look crash described below |
| Splat Pack 16:9 runtime | PASS WITH KNOWN LIMITATION | Stable outside the known cockpit/look crash described below |
| Carmageddon 4:3 runtime | PASS | Stable in the final Actions-runtime smoke test |
| Splat Pack 4:3 runtime | PASS | Stable in the final Actions-runtime smoke test |
| Native analog XInput | PASS | Left-stick steering; analog RT/LT |
| Initial player-name text entry | KEYBOARD REQUIRED | XInput does not provide text entry; normally only needed during initial setup |
| 16:9 cockpit/look stability | KNOWN ISSUE | Looking left/right in cockpit can crash, particularly near the beginning of a race |
| 4:3 cockpit/look stability | PASS | No equivalent crash observed in the final smoke test |
| 500-unit HiRes draw distance | PASS | Goldstandard behavior |
| Full-detail opponent cars | PASS | Principal model retained at distance |
| Distant pedestrian/object rendering | PASS | Extended rendering without extending stock gameplay activation range |
| Centered menus/videos | PASS | 16:9 presentation |
| Centered-menu mouse mapping | PASS | 16:9 presentation |
| Full-frame 16:9 cockpit 3D world | PASS | 854×480 world behind original 4:3 artwork |
| 16:9 rear-view alignment | PASS | Right-edge-aligned final mirror chain |
| Damage HUD | PASS | Tested eXoDOS alternate encrypted data representation |
| Main-game CUE/BIN cutscenes | PASS | 9 SMK files extracted |
| Splat Pack CUE/BIN cutscenes | PASS | 11 SMK files extracted |
| Main-game Red Book audio extraction | PASS | 7 WAV tracks extracted |
| Splat Pack Red Book audio extraction | PASS | 7 WAV tracks extracted |
| Main-game WAV music playback | PASS | RC9 OGG-first/WAV-fallback runtime |
| Splat Pack WAV music playback | PASS | RC9 OGG-first/WAV-fallback runtime |
| Original source folders modified | NO | Sources treated as read-only |
| German/Uncut on tested eXoDOS Splat revision | NOT SUPPORTED | Installer safely declined the unverified revision |

## Reproducible GitHub Actions runtime smoke test

The release-candidate workflow was also built through GitHub Actions and the resulting executables were manually tested in the already validated RC9 installation.

Actions build SHA-256 values:

| Runtime | SHA-256 |
| --- | --- |
| 16:9 | `1300b268d5e0431d52853e3f73e864f971ff1c0879eefc5846cc83152d9e33b5` |
| 4:3 | `a5f5a25ca38d08fda7b3f934674c3e97371bb7f47daa879f0851f5f3c84b0f8b` |

Observed behavior matched the manually built RC9 baseline: the 4:3 runtime was stable, while the 16:9 runtime retained the known cockpit/look crash tendency, especially around race start. Outside that issue, the tested scenarios remained functional. This confirms that the public source/build path reproduces the relevant RC9 behavior even though compiler/toolchain metadata makes the executables byte-different from the manually built RC9 reference.

## Observed eXoDOS installer result

The successful media import reported:

```text
Main-game cutscenes: cue-bin-image
Splat Pack cutscenes: cue-bin-image
Main-game music: cue-bin-audio
Splat Pack music: cue-bin-audio
```

The tested media counts were:

- Carmageddon: **9 SMK** cutscenes and **7** Red Book audio tracks.
- Splat Pack: **11 SMK** cutscenes and **7** Red Book audio tracks.

The tested Damage HUD preflight/patch reported:

```text
Damage HUD files changed: 49
Already correct: 0
Alternate encrypted source files matched safely: 21
```

## RC9 CD-audio bug and fix

RC8 already extracted the original Red Book audio correctly to WAV, but music remained silent.

The cause was Dethrace's CD-audio initialization path: it treated CD audio as unavailable when `MUSIC/Track02.ogg` was absent, even though the later playback path had been extended to try WAV.

RC9 changes both relevant paths:

1. `AudioBackend_InitCDA()` succeeds when either `Track02.ogg` **or** `Track02.wav` exists.
2. `AudioBackend_PlayCDA()` prefers `Track0N.ogg`, then falls back to `Track0N.wav`.

The corresponding source patch is:

```text
source-port/apply-rc9-cdda-wav-fallback.py
```

This was confirmed in-game with both Carmageddon and Splat Pack.

## Damage HUD release-candidate rule

The manually tested RC9 package uses the installer's **source-verified data patch** for the 16:9 external Damage HUD, including the alternate encrypted eXoDOS representation.

An experimental later branch moved this correction into the engine. That later experiment is intentionally **not** the v1.0-rc1 reference until it receives equivalent real-game validation.

## Release blockers before v1.0

The runtime feature set is considered frozen unless a genuine regression is found.

Remaining release-preparation work:

- validate the reproducible GitHub Actions build;
- clarify Dethrace's mixed license wording with upstream before publishing modified binary releases;
- prepare release notes and the public release artifact;
- optionally improve the unsupported-Splat German/Uncut UX (for example, German main game only).

