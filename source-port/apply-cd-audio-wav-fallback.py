#!/usr/bin/env python3
"""Add a WAV fallback for Dethrace CD-audio music files.

Upstream Dethrace v0.10.1 looks only for MUSIC/Track0N.ogg. The installer can
losslessly extract Red Book CD audio from CUE/BIN images as 44.1 kHz stereo
16-bit WAV without any external encoder. Prefer the existing OGG convention,
then fall back to MUSIC/Track0N.wav.

This changes only CD-audio file lookup. Gameplay/rendering behavior is untouched.
"""
from pathlib import Path
import sys


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: apply-cd-audio-wav-fallback.py <dethrace-source>")

    root = Path(sys.argv[1])
    path = root / "src" / "harness" / "audio" / "miniaudio.c"
    text = path.read_text(encoding="utf-8")

    old = """    sprintf(path, "MUSIC/Track0%d.ogg", track);

    if (access(path, F_OK) == -1) {
        return eAB_error;
    }
"""

    new = """    sprintf(path, "MUSIC/Track0%d.ogg", track);

    if (access(path, F_OK) == -1) {
        sprintf(path, "MUSIC/Track0%d.wav", track);
        if (access(path, F_OK) == -1) {
            return eAB_error;
        }
    }
"""

    text = replace_once(text, old, new, "CD audio WAV fallback")
    path.write_text(text, encoding="utf-8")
    print("Applied CD-audio WAV fallback (OGG preferred, WAV fallback)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
