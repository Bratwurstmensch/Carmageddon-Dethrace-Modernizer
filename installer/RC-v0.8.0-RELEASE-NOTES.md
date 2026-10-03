# v0.8.0-rc1 release notes

This release candidate consolidates the previously validated installer, German integration, portable runtime, XInput tooling and widescreen fixes into a target-first package intended for broader testing.

## Changes since v0.7b

- adds a standard Dethrace v0.10.1 4:3 runtime in an isolated `Runtime4x3` directory;
- makes the standard Dethrace runtime part of every generated target installation;
- allows XInput-only installs to work without an existing `dethrace.exe` in the original source;
- makes German/Uncut-only targets directly runnable through Dethrace;
- keeps the already validated 16:9 runtime and its SDL runtime isolated from the new 4:3 runtime;
- retains the source-verified 49-file Damage HUD patch method introduced in v0.7b;
- retains the English installer UI and target-first, read-only source model.

## Already validated before RC1

The v0.7b package passed real-world `12` and `123` installs, main-game and Splat Pack launches, XInput, widescreen HUD placement, and target deletion through the uninstaller.

## RC1 validation focus

The two newly relevant standalone paths are:

- `2` — XInput on the standard 4:3 runtime;
- `3` — German/Uncut on the standard 4:3 runtime.

The previously validated `12` and `123` paths are intentionally kept as close as possible to v0.7b.