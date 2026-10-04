# Roadmap

## Completed for v1.0-rc1

- [x] reproduce the original widescreen proof-of-concept as source changes against Dethrace v0.10.1;
- [x] validate Carmageddon and Splat Pack;
- [x] center menus/videos and correct centered-menu mouse mapping;
- [x] align widescreen HUD/race overlays;
- [x] render the 16:9 cockpit 3D world across the complete 854×480 frame;
- [x] align the 16:9 rear-view render surface;
- [x] provide a separate 4:3 Modernizer runtime;
- [x] increase HiRes draw distance to 500 units;
- [x] retain full-detail opponent cars at distance;
- [x] reduce distant pedestrian/object pop-in without extending stock gameplay activation;
- [x] implement native analog XInput steering and triggers;
- [x] build a non-destructive Windows installer with backup/rollback/uninstall behavior;
- [x] integrate supported user-owned German/Uncut data without redistributing original assets;
- [x] detect and import eXoDOS-style CUE/BIN cutscenes;
- [x] extract Red Book CD audio losslessly from CUE/BIN;
- [x] add RC9 OGG-first/WAV-fallback CD-audio playback;
- [x] support the verified alternate encrypted eXoDOS Damage HUD data representation;
- [x] record the successful RC9 manual validation;
- [x] add a reproducible v1.0-rc1 runtime build workflow.

## Before the first public binary release

- [x] synchronize the repository installer source byte-for-byte with the manually tested RC9 package;
- [x] run/inspect the new v1.0-rc1 GitHub Actions runtime build;
- [x] smoke-test the reproducibly built runtimes and document expected byte/hash differences plus the reproduced 16:9 cockpit limitation;
- [ ] ask Dethrace maintainers for clarification on the repository's mixed GPLv3 vs older README licensing wording;
- [ ] prepare final v1.0-rc1 release notes and artifact;
- [ ] perform one final clean-source install / launch / uninstall smoke test from the publishable package.

## Upstream work

- [ ] introduce the Modernizer in a Dethrace Discussion;
- [ ] offer the small RC9 WAV fallback as an isolated upstream change;
- [ ] discuss native analog XInput in the context of Dethrace issue #343;
- [ ] answer/share findings for widescreen issues #349 / #518;
- [ ] answer/share the tested draw-distance work in #457;
- [ ] consolidate the historical widescreen patch chain before proposing any large upstream PR.

See [UPSTREAM.md](UPSTREAM.md).

## Post-v1.0 ideas

- [ ] improve the unsupported-Splat German/Uncut UX, e.g. allow German main game + English uncut Splat Pack;
- [ ] verify additional source revisions;
- [ ] reduce/consolidate historical patch scripts once the release source is permanently tagged;
- [ ] consider additional platforms after the Windows release is stable.
