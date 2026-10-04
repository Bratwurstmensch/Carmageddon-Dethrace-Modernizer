# Upstream relevance

The Modernizer is a separate community project, but several independently developed changes overlap directly with long-standing requests in the upstream [Dethrace](https://github.com/dethrace-labs/dethrace) project.

This file records the most relevant upstream issues as of **2026-10-04** and helps keep potential upstream contributions small and reviewable.

## #343 — Xbox gamepad / XInput support

https://github.com/dethrace-labs/dethrace/issues/343

Status: **open**

The request asks for proper Xbox/XInput gamepad support, including practical couch-friendly control.

The Modernizer already has a tested native analog implementation with:

- left-stick analog steering;
- RT analog acceleration;
- LT analog brake/reverse;
- normal driving actions mapped to Xbox-compatible buttons;
- Carmageddon and Splat Pack support.

Relevant Modernizer source work:

```text
source-port/apply-native-analog-xinput-v13.py
```

**Upstream potential:** high. The controller code should be proposed separately from Modernizer-specific installer and widescreen work.

## #349 — Widescreen support

https://github.com/dethrace-labs/dethrace/issues/349

Status: **open**

The issue explicitly discusses 16:9 support and the difficulty of handling original cockpit artwork outside the 4:3 frame.

The Modernizer demonstrates a tested 854×480 Hor+ path with:

- centered 640-wide UI/video surfaces;
- corrected menu mouse coordinates;
- centered race overlays;
- full-width 3D rendering;
- full-frame cockpit 3D rendering behind original 4:3 artwork;
- rear-view positioning adapted for the widened framebuffer.

**Upstream potential:** medium/high, but the current implementation grew through a long experimental patch chain. Before proposing it upstream, it should be consolidated into a smaller clean patch series.

## #518 — Change resolution in OpenGL Mode

https://github.com/dethrace-labs/dethrace/issues/518

Status: **open**

This overlaps with the broader widescreen/high-resolution discussion. Another community fork is already referenced in that issue.

The Modernizer should therefore not be presented as the first or only widescreen solution. Its useful contribution is the specific tested combination of widescreen layout, cockpit/mirror handling, controller support, installer integration and compatibility work.

**Upstream potential:** mostly as supporting evidence / implementation reference rather than a duplicate feature claim.

## #457 — draw-distance question

https://github.com/dethrace-labs/dethrace/issues/457

Status: **open**

The issue asks, among other things, whether draw distance can be increased.

The Modernizer's high-resolution path uses a **500-unit far plane**, prevents race-specific Yon data from unexpectedly shortening it, keeps opponent cars at full principal-model detail, and renders distant pedestrian/object sprites farther away while retaining the original short gameplay/AI activation radius.

Relevant source work includes:

```text
source-port/apply-4x3-modernizer-parity.py
source-port/apply-current-test.py
source-port/apply-current-fixes-v2.py
```

**Upstream potential:** medium/high. Draw-distance and LOD behavior should be split into focused changes rather than submitted as one Modernizer mega-patch.

## CD audio / WAV fallback

Upstream Dethrace uses the GOG convention `MUSIC/Track02.ogg`, `Track03.ogg`, etc.

The Modernizer's eXoDOS/CUE-BIN installer can losslessly extract original Red Book audio as PCM WAV. RC9 therefore adds an OGG-first/WAV-fallback lookup while leaving existing GOG behavior unchanged.

Relevant source patch:

```text
source-port/apply-rc9-cdda-wav-fallback.py
```

No current open eXoDOS/CUE-BIN-specific upstream issue was found during the 2026-10-04 review.

**Upstream potential:** high as a very small isolated patch.

## Proposed upstream approach

Do **not** submit the entire Modernizer as one pull request.

A better sequence is:

1. open a Dethrace Discussion introducing the project and asking for license/maintainer guidance;
2. offer the small CD-audio WAV fallback separately;
3. offer native analog XInput as its own focused contribution;
4. answer the open draw-distance/widescreen issues with links and tested observations;
5. only then prepare clean, minimal widescreen/draw-distance PRs if maintainers want them.

This keeps Dethrace reviewable and avoids tying generally useful engine changes to Windows installer, localization or eXoDOS packaging logic.
