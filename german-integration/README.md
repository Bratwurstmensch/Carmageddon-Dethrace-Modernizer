# Reproducible German integration

This directory contains the reproducible German-localization work for the Modernizer.

## Confirmed final state

The currently validated installation has been reconstructed from the archived development packages and compared against a fresh inventory of the working installation.

- Carmageddon main game: **250 files** (229 FLI, 12 WAV, 9 TXT)
- Splat Pack: **275 files** (253 FLI, 12 WAV, 10 TXT)

Main target manifest identity:
`7cb50ad5e3b1bfca6a021ccc8210b975f27419446286c8441e34800da971fd27`

Splat target manifest identity:
`19832c80860d00393b20ade338c09f8f30f65a614243a10d59d71a18544964fe`

## Splat reconstruction

The final Splat Pack localization decomposes cleanly into:

- **206 files** that are byte-identical to the validated German main-game set.
- **69 Splat-specific files** reconstructed from original Splat Pack source data.
  - 8 same-path text/config files differ from the main game.
  - 61 paths exist only in the Splat localization (60 FLI + DPOWERUP.TXT).

All 69 have corresponding files in the recovered original Splat source set.
A local source-verified delta proof of concept rebuilt all 275 targets and verified every SHA-256 successfully.

The binary delta payloads are intentionally not committed yet.


## Canonical manifest identity

For audit builds the identity is SHA-256 over the complete sorted target set. Each line is:

`lowercase-relative-path<TAB>file-sha256<LF>`

This makes the identity independent of ZIP timestamps, archive ordering or compression.
The private archived development packages are not part of the public repository; `reconstruct_from_archives.py` consumes them locally and verifies the complete rebuilt target set.


## German retail source profile

The original `exoDOS Version` archive used during the project was recovered and inspected.
Its `DATA` tree is the German retail/censored source: decoded `TEXT.TXT` contains the original German localization including the Android censorship wording.

All **250** validated final main-game localization paths exist in this German retail source.

Against the final target:

- 48 files are already byte-identical and can be copied directly.
- 202 files require a CGDX delta.
- the generated main-game delta payload is about **4.2 MiB** before outer ZIP packaging.
- a full local rebuild from the German retail source reproduced all 250 final files byte-for-byte and matched the canonical final identity.

This means the public German-main-game integration does not need to redistribute complete German assets and does not require an English/GOG source for those 250 localized paths. The Modernizer can keep an uncut Dethrace/GOG installation as the gameplay/data base and transform only the verified localization paths from user-owned German retail source data.


## v0.2b integrated installer runtime validation

Validated on 2026-10-02 against the user's working Carmageddon/Dethrace installation:

- installer recovery from an incomplete prior install: passed
- Modernizer install: passed
- German/Uncut main-game target verification: passed
- German Splat Pack target verification: passed
- Start-Carmageddon-16x9.cmd: passed
- Start-CARSPLAT-16x9.cmd: passed
- Start-Carmageddon-16x9-XInput.cmd: passed
- Start-CARSPLAT-16x9-XInput.cmd: passed

Uninstall confirmation is tracked separately before calling the full v0.2b install/run/uninstall cycle complete.
