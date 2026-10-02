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
