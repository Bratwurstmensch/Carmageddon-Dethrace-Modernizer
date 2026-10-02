# German integration inventory tool

This read-only diagnostic inventories the user's existing Carmageddon/Dethrace data so the German-localization workflow can be reproduced without redistributing original game assets.

It records:

- every file under `DATA` and, when present, `CARSPLAT/DATA`,
- relative path, size, timestamp and SHA-256,
- extension/timestamp summaries,
- a main-vs-Splat comparison for same-path files,
- a candidate list for FLI/PIX/sound/text localization assets,
- selected localization text/config files.

It does **not** modify game data and intentionally does not copy bulk FLI/PIX/sound assets into the diagnostic ZIP.

## Recovered validated final German state

The user's currently working German/uncut installation was inventoried and then cross-checked against the complete archived patch history on 2026-10-02.

This corrected reconstruction supersedes the earlier intermediate 196/257-file count.

### Carmageddon main game: 250 final files

The exact current main-game state is reproduced by this confirmed stack:

1. `Carmageddon-German-Uncut-Dethrace-v1.6`
2. `v1.6a-RaceCards`
3. `v1.6b-Resttext`
4. `v1.6c-PartsShop`

Unique final files:

- 229 FLI
- 12 WAV
- 9 TXT
- **250 files total**

Every one of these 250 reconstructed target hashes matches the current working installation.

The later `v1.6d`, `v1.6d2` and `v1.6d3` umlaut packages were experiments/tests and are **not** part of the current validated final installation.

### Splat Pack: 275 final files

The exact current Splat Pack state is reproduced by the archived Splat Germanization sequence through `v0.13-FinalGraphics`.

Unique final files:

- 253 FLI
- 12 WAV
- 10 TXT
- **275 files total**

Every one of these 275 reconstructed target hashes matches the current working installation.

### Main/Splat relationship

Comparing the two final logical payload sets:

- 214 paths exist in both
- **206 are byte-identical**
  - 193 FLI
  - 12 WAV
  - 1 TXT
- **8 same-path files are intentionally different** between main game and Splat Pack:
  - `DARES.TXT`
  - `NETRACES.TXT`
  - `OPPONENT.TXT`
  - `PEDRACES.TXT`
  - `POWERUP.TXT`
  - `RACES.TXT`
  - `SOUND/SOUND.TXT`
  - `TEXT.TXT`
- 36 files are main-game-only, all FLI race-card graphics
- 61 files are Splat-only:
  - 60 FLI
  - `DPOWERUP.TXT`

This gives a clean public-integration strategy: reuse the 206 identical localized files, keep the eight game-specific text/config files separate, and generate/patch only the game-specific graphics/text from user-owned source data.

### Recovered source provenance

The archived `Carmageddon-SplatPack-SourceForGermanPatch-v2` source set was also recovered. All **69** Splat-specific/different final files (the eight different shared paths plus the 61 Splat-only files) have corresponding original Splat source files.

Therefore the Splat German integration can be made reproducible without shipping the finished copyrighted assets:

1. reuse the 206 final files shared with the main-game German integration,
2. verify the user's original Splat source files by SHA-256,
3. transform/patch the remaining 69 Splat files,
4. verify every produced target by SHA-256.

### Final-state identity

For deterministic auditing, the sorted path+SHA-256 target sets have these aggregate identifiers:

- main-game final German set: `7cb50ad5e3b1bfca6a021ccc8210b975f27419446286c8441e34800da971fd27`
- Splat Pack final German set: `19832c80860d00393b20ade338c09f8f30f65a614243a10d59d71a18544964fe`

These are manifest identity hashes, not hashes of a ZIP archive.


## Delta proof of concept

A source-verified binary-delta proof of concept has now been completed for the **69 Splat-specific files**.

Starting from:
- the validated 250-file German main-game target set, and
- the recovered original `Carmageddon-SplatPack-SourceForGermanPatch-v2` source set,

the prototype rebuilt:
- 206 Splat files by exact byte reuse from the main-game German set,
- 69 Splat files by source-verified binary delta,

for a total of **275 Splat target files**.

Every generated file passed its individual SHA-256 check and the resulting complete target set matched manifest identity:

`19832c80860d00393b20ade338c09f8f30f65a614243a10d59d71a18544964fe`

The current experimental delta format is `CGDX1`: exact-source SHA-256 validation, a compressed XOR delta, then exact-target SHA-256 validation. The reference implementation is in `german-integration/cgdx.py`.


## Canonical identity definition

The final-set identity is computed from all reconstructed files after overlaying the known-good private development stack. Paths are converted to lower-case backslash form, sorted, and serialized as:

`path<TAB>sha256<LF>`

The SHA-256 of that serialization is the manifest identity. A local audit rebuild has verified both complete target sets:

- main: 250 files -> `7cb50ad5e3b1bfca6a021ccc8210b975f27419446286c8441e34800da971fd27`
- Splat: 275 files -> `19832c80860d00393b20ade338c09f8f30f65a614243a10d59d71a18544964fe`


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

Uninstall completed successfully. The full v0.2b install -> main game -> Splat Pack -> XInput -> uninstall cycle is validated on the already-localized working installation.


### Remaining release-gate test

The validated runtime cycle above used an installation whose German/Uncut main and Splat targets were already correct, so the installer correctly verified them without rewriting them.

The **clean-source transformation path still requires one Windows end-to-end test**: German retail source -> 250 main targets and original Splat source -> 275 Splat targets through the actual PowerShell installer. The underlying delta reconstruction has already been verified independently; this final test is specifically for the installer wiring before a public release candidate.
