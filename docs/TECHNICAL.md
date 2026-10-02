# Technical notes

## Validated v1.5 proof-of-concept

The final private/tested v1.5 executable is byte-identical to the previously validated `v1.5b TEST` build. Only its filename and launcher references were changed during final packaging.

Reference hashes:

- base executable SHA-256: `595f9efecd8d6c63be0a1d310977680bdd052aff7530784d0b1182b2025158a8`
- validated v1.5 executable SHA-256: `132cbc140e73bb3e1d640be915c9269bc0b317e5d50a67105ccaa7a8d73a1ec4`

The binary itself is intentionally not committed to this repository.

## Confirmed behavior

The proof-of-concept was validated with the main game and Splat Pack.

It implements:

1. centered RGB565 menu/video copies,
2. centered indexed menu/video copies,
3. full-width interface clearing for the 854-pixel output,
4. corrected mouse-coordinate mapping for the centered 640-pixel menu surface,
5. centering of event/head-up slots 4, 5, 6, 9, 10 and 11 from x=320 to x=427 when the 854-pixel output path is active.

The on-disk HEADUP.TXT and CAR files are not rewritten by this mechanism.

## Dethrace source areas used during investigation

The work was investigated against **Dethrace v0.10.1**, especially:

- `common/displays.c`
  - `EarnCredits2`
  - `DoFancyHeadup`
- `common/structur.c`
  - checkpoint path leading to `DoFancyHeadup`
- `common/loading.c`
  - `LoadHeadups`
  - HEADUP anchor loading

The exact proof-of-concept RVA changes are preserved in [../patches/v1.5-patch-manifest.json](../patches/v1.5-patch-manifest.json).

## Public implementation plan

The preferred public form is **not** a mystery binary patch.

The goal is to:

1. reproduce the validated behavior as readable Dethrace source changes,
2. build the modified executable from source,
3. keep original Carmageddon data outside the repository,
4. provide a deterministic installer/packager that works from user-owned data,
5. publish source and release artifacts in a GPL-compliant way.

## Controller layer

The current Windows XInput helper is intentionally small and dependency-free. It reads controller slot 1 through `xinput1_4.dll` and generates the original keyboard controls through Win32 keyboard events.

The tested launcher configuration additionally uses:

`--fps=60 --physics-step-time=10`

The normal non-controller launchers use:

`-hires --opengl`
