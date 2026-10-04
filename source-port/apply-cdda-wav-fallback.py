#!/usr/bin/env python3
"""Allow Dethrace CD-audio fallback to WAV tracks.

Dethrace v0.10.1 expects GOG-style MUSIC/Track02.ogg etc. The Modernizer
installer can losslessly extract Red Book CD audio from CUE/BIN images as
44.1 kHz stereo 16-bit PCM WAV without requiring an external encoder.

Behavior after this patch:
- prefer existing TrackNN.ogg (GOG-compatible behavior unchanged)
- otherwise use TrackNN.wav
- fail exactly as before when neither exists
"""
from pathlib import Path
import sys


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: apply-cdda-wav-fallback.py <dethrace-source>")

    root = Path(sys.argv[1])
    path = root / "src" / "harness" / "audio" / "miniaudio.c"
    text = path.read_text(encoding="utf-8")

    text = replace_once(
        text,
        '''tAudioBackend_error_code AudioBackend_InitCDA(void) {
    // check if music files are present or not
    if (access("MUSIC/Track02.ogg", F_OK) == -1) {
        return eAB_error;
    }
    return eAB_success;
}''',
        '''tAudioBackend_error_code AudioBackend_InitCDA(void) {
    // Prefer the existing GOG OGG convention, but also accept lossless WAV
    // tracks extracted directly from original CUE/BIN CD images.
    if (access("MUSIC/Track02.ogg", F_OK) == -1
        && access("MUSIC/Track02.wav", F_OK) == -1) {
        return eAB_error;
    }
    return eAB_success;
}''',
        "CD audio init fallback",
    )

    text = replace_once(
        text,
        '''    sprintf(path, "MUSIC/Track0%d.ogg", track);

    if (access(path, F_OK) == -1) {
        return eAB_error;
    }''',
        '''    sprintf(path, "MUSIC/Track0%d.ogg", track);
    if (access(path, F_OK) == -1) {
        sprintf(path, "MUSIC/Track0%d.wav", track);
        if (access(path, F_OK) == -1) {
            return eAB_error;
        }
    }''',
        "CD audio play fallback",
    )

    path.write_text(text, encoding="utf-8")
    print("Applied CD-audio WAV fallback (OGG remains preferred)")


if __name__ == "__main__":
    raise SystemExit(main())
