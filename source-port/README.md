# Modernizer source-port patches

This directory contains reproducible source transformations against **Dethrace v0.10.1**.

The project started with the validated v1.5 widescreen proof-of-concept and then grew through iterative source-level work for draw distance, distant detail, cockpit rendering, mirror placement, native analog XInput and CD-audio compatibility.

## Release-candidate philosophy

The historical patch scripts are intentionally kept instead of being silently rewritten into one opaque mega-patch. They provide an audit trail for the development process.

For **v1.0-rc1**, the authoritative build order is encoded in:

```text
.github/workflows/build-v1.0-rc1-runtimes.yml
```

Do not assume that every experimental script in this directory belongs in the final runtime. The workflow is the release-candidate source of truth.

## 4:3 release-candidate chain

Starting from a clean Dethrace v0.10.1 checkout:

```text
apply-4x3-modernizer-parity.py
apply-native-analog-xinput-v13.py
apply-rc9-cdda-wav-fallback.py
```

The 4:3 parity patch keeps the original aspect ratio while adding the shared Modernizer runtime improvements:

- 500-unit HiRes far plane;
- no race-specific reduction of the Modernizer far plane;
- full principal opponent-car models at distance;
- distant pedestrian/object rendering while retaining the original gameplay activation radius;
- enlarged lollipop render queue.

## 16:9 release-candidate chain

The 16:9 runtime is built from the validated widescreen/Goldstandard progression:

```text
apply-v1.5-source-port.py
apply-current-test.py
apply-current-fixes-v2.py
apply-overlay-alignment-v3.py
apply-cockpit-final-overlays-v4.py
apply-cockpit-finetune-v5.py
apply-cockpit-finetune-v6.py
apply-cockpit-finetune-v7.py
apply-cockpit-stability-v8.py
apply-cockpit-final-v9.py
apply-cockpit-final-v10.py
apply-cockpit-stability-v11.py
apply-cockpit-final-v12.py
apply-native-analog-xinput-v13.py
apply-cockpit-crashdiag-v14.py
apply-pratcam-stability-v15.py
apply-pratcam-directblit-v16.py
apply-pratcam-directblit-lock-v17.py
apply-ped-completion-guard-v18.py
apply-release-candidate-1.py
apply-cockpit-top-normalization-test.py
apply-cockpit-top-overlay-crop-test.py
apply-mirror-final-alignment-test.py
apply-rc9-cdda-wav-fallback.py
```

Some filenames still contain `test` because they preserve their development history. Their content on the release branch corresponds to the final manually validated fullscreen-cockpit / mirror path.

## RC9 CD-audio patch

`apply-rc9-cdda-wav-fallback.py` is intentionally small and isolated.

It changes only the Dethrace CD-audio file lookup:

- `AudioBackend_InitCDA()`: CD audio is available when either `MUSIC/Track02.ogg` or `MUSIC/Track02.wav` exists.
- `AudioBackend_PlayCDA()`: prefer `Track0N.ogg`; if absent, try `Track0N.wav`.

This preserves normal GOG behavior and enables lossless WAV tracks extracted from original CUE/BIN CD images.

The patch was manually validated with both Carmageddon and Splat Pack in RC9.

## Native analog XInput

`apply-native-analog-xinput-v13.py` adds the tested controller path used by both release-candidate runtimes.

The normal driving layout includes analog steering and analog triggers. Action Replay remains keyboard/mouse-oriented because its control surface is substantially larger and conflicts with the normal driving layout.

## Widescreen notes

The 16:9 path uses a genuine 854×480 HiRes/OpenGL render target.

The original UI and cockpit art remains 4:3 source material. The Modernizer centers/adapts those 2D surfaces while allowing the 3D world to fill the widened frame.

The final cockpit path renders the 3D world across the complete 854×480 framebuffer behind the cockpit art. The final rear-view path right-aligns the 3D rear-view render surface.

## Installer-side work

Not every Modernizer feature belongs in the Dethrace runtime.

The Windows installer separately handles:

- source discovery and validation;
- backup/rollback/uninstall state;
- German/Uncut local data integration;
- GOG/loose-file media discovery;
- eXoDOS CUE/BIN ISO9660 cutscene extraction;
- Red Book audio extraction;
- source-verified Damage HUD data correction.

Those features should not be mixed into upstream Dethrace engine pull requests.

## Upstreamable pieces

See [../docs/UPSTREAM.md](../docs/UPSTREAM.md).

The strongest isolated upstream candidates are:

1. RC9 OGG-first/WAV-fallback CD audio;
2. native analog XInput;
3. focused draw-distance/LOD changes;
4. later, a consolidated widescreen patch series if upstream maintainers want it.
