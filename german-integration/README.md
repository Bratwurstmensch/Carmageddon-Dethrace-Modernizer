# Reproducible German integration

This directory contains the reproducible German-localization work for the Modernizer.

## Confirmed final state

The currently validated installation has been reconstructed from the archived development packages and compared against a fresh inventory of the working installation.

- Carmageddon main game: **250 files** (229 FLI, 12 WAV, 9 TXT)
- Splat Pack: **275 files** (253 FLI, 12 WAV, 10 TXT)

Main target manifest identity:
`e78c70a2e403ff85731cd0fa377aab3b355a920c0faef31518f1b0557b181c83`

Splat target manifest identity:
`260ad711d576223d22ec2fc823d428a061d887547ffc403f7c050dc141b79c13`

## Splat reconstruction

The final Splat Pack localization decomposes cleanly into:

- **206 files** that are byte-identical to the validated German main-game set.
- **69 Splat-specific files** reconstructed from original Splat Pack source data.
  - 8 same-path text/config files differ from the main game.
  - 61 paths exist only in the Splat localization (60 FLI + DPOWERUP.TXT).

All 69 have corresponding files in the recovered original Splat source set.
A local source-verified delta proof of concept rebuilt all 275 targets and verified every SHA-256 successfully.

The binary delta payloads are intentionally not committed yet.
