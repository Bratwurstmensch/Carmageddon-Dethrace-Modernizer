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

## Source-port validation

The v1.5 behavior has now been reproduced from clean **Dethrace v0.10.1** source using the source-port patcher in this repository.

Validation status:

- GitHub Actions Windows x64 build: **passed**
- Carmageddon main game visual/runtime test: **passed**
- Splat Pack visual/runtime test: **passed**
- 16:9 3D presentation: **passed**
- centered menus/videos: **passed**
- corrected centered-menu mouse mapping: **passed**
- centered countdown/checkpoint/bonus/points messages: **passed**
- top HUD positioning: **passed**

## Public implementation plan

The preferred public form is **not** a mystery binary patch.

The remaining goals are:

1. keep the validated source port reproducible,
2. keep original Carmageddon data outside the repository,
3. provide a deterministic installer/packager that works from user-owned data,
4. integrate the German-data workflow without redistributing original copyrighted assets,
5. publish source and release artifacts in a GPL-compliant way.

## Controller layer

The current Windows XInput helper is intentionally small and dependency-free. It reads controller slot 1 through `xinput1_4.dll` and generates the original keyboard controls through Win32 keyboard events.

The tested launcher configuration additionally uses:

`--fps=60 --physics-step-time=10`

The normal non-controller launchers use:

`-hires --opengl`


## Installer validation

The v0.1 Windows installer was validated on 2026-10-02 against an existing Carmageddon/Dethrace installation that already contained earlier Modernizer files.

Observed result:

- installation completed successfully,
- `DATA/GENERAL.TXT` detection passed,
- Splat Pack was detected automatically,
- main-game and Splat Pack launchers remained functional,
- pre-existing Modernizer files were treated as replaceable/backup-managed files,
- uninstall completed successfully,
- the installer state directory was removed after uninstall,
- original `dethrace.exe` and original game data were left untouched.

File timestamps are not used as installation-state evidence; the installer tracks prior existence and backups in its install manifest.


## 854-wide A/P/O HUD alignment

The original high-resolution graphics data positions the Armour / Power / Offense block against the right edge of a 640-pixel surface. With the Modernizer 854-pixel widescreen graphics width, leaving those compiled coordinates unchanged makes the A/P/O block appear too far toward the center.

The source port therefore adds the same 107-pixel widescreen offset to:

- the A/P/O dim rectangle,
- the A/P/O letter X position,
- and every A/P/O bar X position.

The adjustment is conditional on the 854-pixel graphics width, so the standard 4:3 runtime is unchanged.
