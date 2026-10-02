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

- main-game final German set: `e78c70a2e403ff85731cd0fa377aab3b355a920c0faef31518f1b0557b181c83`
- Splat Pack final German set: `260ad711d576223d22ec2fc823d428a061d887547ffc403f7c050dc141b79c13`

These are manifest identity hashes, not hashes of a ZIP archive.
