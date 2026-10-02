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


## Recovered validated payload structure

A read-only inventory of the user's currently working German/uncut installation was analysed on 2026-10-02.

The recovered payload structure is unusually clean:

### Carmageddon main game

Exactly **196 localization payload files** were identified:

- 175 FLI files
- 9 TXT files
- 12 WAV files

194 of these share the original German-integration installation timestamp; `RACES.TXT` and `TEXT.TXT` are the two later corrected text files. Together this reconstructs the previously known 196-file main-game payload exactly.

### Splat Pack

The working Splat Pack German integration contains **257 payload files**:

- 235 FLI files
- 10 TXT files
- 12 WAV files

This consists of:

- the same 196 logical localization paths used for the main game,
- plus **61 Splat-specific files**:
  - 60 FLI files,
  - `DPOWERUP.TXT`.

Of the 196 shared paths, **188 are byte-identical** between the working main-game and Splat Pack installs. Eight same-path text/config files are Splat-specific and must not simply be copied from the main game:

- `DARES.TXT`
- `NETRACES.TXT`
- `OPPONENT.TXT`
- `PEDRACES.TXT`
- `POWERUP.TXT`
- `RACES.TXT`
- `SOUND/SOUND.TXT`
- `TEXT.TXT`

The diagnostic also confirms that the Splat-specific text is genuinely adapted content rather than a blind copy; for example, the working `TEXT.TXT` contains Splat Pack-specific wording.

### Consequence for the public installer

The installer must therefore treat German integration as three layers:

1. reusable German Carmageddon assets that can be sourced from a user-owned German installation,
2. Splat-specific translated/configuration files,
3. Splat-specific FLI transformations.

The repository must not contain the original copyrighted game assets themselves. The intended public form is source detection/copying plus reproducible transformations or binary deltas generated against user-owned source data.
