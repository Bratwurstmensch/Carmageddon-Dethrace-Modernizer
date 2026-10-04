# Carmageddon Dethrace Modernizer v1.0-rc1 — release notes

## Status

**Release candidate.** Runtime features are frozen around the tested RC9 behavior. The public source/build path has also been rebuilt through GitHub Actions and manually smoke-tested.

## Highlights

- true 16:9 gameplay at 854x480 in HiRes/OpenGL mode;
- separate original-aspect-ratio 4:3 Modernizer runtime;
- native analog Xbox/XInput steering;
- analog RT acceleration and LT brake/reverse;
- centered widescreen menus, videos, map and race overlays;
- corrected centered-menu mouse mapping;
- fullscreen 16:9 cockpit 3D world behind original 4:3 artwork;
- widened rear-view mirror placement;
- 500-unit HiRes draw distance;
- full-detail opponent cars retained at distance;
- reduced distant pedestrian/object pop-in while preserving stock gameplay activation distance;
- Carmageddon + Splat Pack support;
- GOG and tested eXoDOS-style source support;
- direct CUE/BIN SMK cutscene extraction;
- lossless Red Book CD-audio extraction to WAV;
- OGG-first / WAV-fallback CD-audio playback;
- source-verified 16:9 Damage HUD correction;
- optional experimental German/Uncut integration from user-owned data;
- non-destructive installer with rollback/uninstall handling.

## Validation

Reference manually tested RC9 runtimes:

- 16:9 SHA-256: `1df66ba28020f08635773a992e1254ce1b746a11f7a4d77598aff236d7f8ddf6`
- 4:3 SHA-256: `80dd90f4a74b6caaae19fb336cbd86e5ce0dc3058c509d0da691ecf1511dc9f7`

Reproducible GitHub Actions runtimes that were also manually smoke-tested:

- 16:9 SHA-256: `1300b268d5e0431d52853e3f73e864f971ff1c0879eefc5846cc83152d9e33b5`
- 4:3 SHA-256: `a5f5a25ca38d08fda7b3f934674c3e97371bb7f47daa879f0851f5f3c84b0f8b`

The Actions builds reproduced the relevant RC9 behavior.

## Known limitations

- **16:9 cockpit/look stability:** looking left/right in cockpit mode can still crash, especially when switching views near the beginning of a race. The 4:3 runtime remained stable in the same release-candidate testing and is recommended for cockpit-heavy play.
- The original cockpit artwork is fixed 4:3 artwork; no replacement art is generated.
- A keyboard is required for the initial player-name text entry. Normal driving/controller use works afterward.
- Action Replay remains keyboard/mouse-oriented.
- German/Uncut remains experimental and source-revision-specific.

## Game data

No original Carmageddon or Splat Pack game data is included. Users must provide their own legally obtained source data.

## Upstream

The Modernizer is not an official Dethrace project. Before the first public modified-binary release, the project is seeking clarification from Dethrace maintainers regarding the repository's mixed GPLv3 vs older README licensing wording and offering suitable changes as focused upstream contributions.
