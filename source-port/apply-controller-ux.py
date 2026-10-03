#!/usr/bin/env python3
from pathlib import Path
import sys

def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)

def main() -> int:
    if len(sys.argv) != 2:
        print(f"Usage: {Path(sys.argv[0]).name} /path/to/dethrace-v0.10.1", file=sys.stderr)
        return 2

    root = Path(sys.argv[1]).resolve()
    path = root / "src/DETHRACE/common/intrface.c"
    if not path.is_file():
        raise FileNotFoundError(path)

    text = path.read_text(encoding="utf-8")

    replacements = [
        (
            "(PDKeyDown(KEY_LEFT) || PDKeyDown(KEY_KP_4) || last_press == KEY_LEFT)",
            "(PDKeyDown(KEY_LEFT) || PDKeyDown(KEY_KP_4) || PDKeyDown(KEY_DELETE) || last_press == KEY_LEFT)",
            "menu left",
        ),
        (
            "(PDKeyDown(KEY_RIGHT) || PDKeyDown(KEY_KP_6) || last_press == KEY_RIGHT)",
            "(PDKeyDown(KEY_RIGHT) || PDKeyDown(KEY_KP_6) || PDKeyDown(KEY_PAGEDOWN) || last_press == KEY_RIGHT)",
            "menu right",
        ),
        (
            "(PDKeyDown(KEY_UP) || PDKeyDown(KEY_KP_8) || last_press == KEY_UP)",
            "(PDKeyDown(KEY_UP) || PDKeyDown(KEY_KP_8) || PDKeyDown(KEY_END) || last_press == KEY_UP)",
            "menu up",
        ),
        (
            "(PDKeyDown(KEY_DOWN) || PDKeyDown(KEY_KP_2) || last_press == KEY_DOWN)",
            "(PDKeyDown(KEY_DOWN) || PDKeyDown(KEY_KP_2) || PDKeyDown(KEY_TAB) || last_press == KEY_DOWN)",
            "menu down",
        ),
    ]
    for old, new, label in replacements:
        text = replace_once(text, old, new, label)

    # A already maps to Space, which Dethrace natively accepts as menu confirm.
    # B maps to Z for wheelspin in-race; treat Z as Escape/Back in menus.
    # Keep Z typeable when an interface text field is active.
    text = replace_once(
        text,
        "        if (PDKeyDown(KEY_ESCAPE)) {",
        "        if (PDKeyDown(KEY_ESCAPE) || (gTyping_slot < 0 && PDKeyDown(KEY_Z))) {",
        "menu B/back",
    )

    path.write_text(text, encoding="utf-8")
    print("Applied Modernizer controller menu UX patch")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
