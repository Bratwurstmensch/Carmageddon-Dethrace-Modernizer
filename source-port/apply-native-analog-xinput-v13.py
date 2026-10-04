#!/usr/bin/env python3
"""Add native analog XInput driving controls on top of stable cockpit v12.

Windows/XInput only:
- left stick X -> analog steering
- right trigger -> analog accelerator
- left trigger -> analog brake/reverse

Digital controller buttons remain handled by the existing PowerShell mapper.

Also fixes the original integer-division bug in analog braking.
"""
from pathlib import Path
import sys


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected 1 match, found {count}")
    return text.replace(old, new, 1)


def patch_controls(path: Path) -> None:
    text = path.read_text(encoding="utf-8")

    text = replace_once(
        text,
        "#include <stdlib.h>\n",
        """#include <stdlib.h>

#ifdef _WIN32
#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#endif
""",
        "Windows XInput include",
    )

    text = replace_once(
        text,
        "int _unittest_controls_lastGetPowerup = 0;\n",
        """int _unittest_controls_lastGetPowerup = 0;

#ifdef _WIN32
typedef struct tModernizer_xinput_gamepad {
    WORD wButtons;
    BYTE bLeftTrigger;
    BYTE bRightTrigger;
    SHORT sThumbLX;
    SHORT sThumbLY;
    SHORT sThumbRX;
    SHORT sThumbRY;
} tModernizer_xinput_gamepad;

typedef struct tModernizer_xinput_state {
    DWORD dwPacketNumber;
    tModernizer_xinput_gamepad Gamepad;
} tModernizer_xinput_state;

typedef DWORD(WINAPI* tModernizer_XInputGetState)(DWORD, tModernizer_xinput_state*);

static tModernizer_XInputGetState gModernizer_XInputGetState;
static int gModernizer_XInput_initialised;

static void Modernizer_InitXInput(void) {
    HMODULE module;

    if (gModernizer_XInput_initialised) {
        return;
    }
    gModernizer_XInput_initialised = 1;

    module = LoadLibraryA("xinput1_4.dll");
    if (module == NULL) {
        module = LoadLibraryA("xinput9_1_0.dll");
    }
    if (module == NULL) {
        module = LoadLibraryA("xinput1_3.dll");
    }
    if (module != NULL) {
        gModernizer_XInputGetState = (tModernizer_XInputGetState)GetProcAddress(module, "XInputGetState");
    }
}

static int Modernizer_MapStickMagnitude(int magnitude, int dead_zone, int maximum) {
    int value;

    if (magnitude <= dead_zone) {
        return 0;
    }
    value = (magnitude - dead_zone) * 65535 / (maximum - dead_zone);
    if (value < 0) {
        return 0;
    }
    if (value > 65535) {
        return 65535;
    }
    return value;
}

static int Modernizer_MapTrigger(BYTE trigger) {
    const int threshold = 30;
    int value;

    if (trigger <= threshold) {
        return -1;
    }

    value = ((int)trigger - threshold) * 65535 / (255 - threshold);
    if (value < 0) {
        return 0;
    }
    if (value > 65535) {
        return 65535;
    }
    return value;
}

static int Modernizer_ReadAnalogXInput(tJoystick* joystick) {
    const int stick_dead_zone = 8500;
    tModernizer_xinput_state state;
    int axis;
    int magnitude;

    Modernizer_InitXInput();
    if (gModernizer_XInputGetState == NULL) {
        return 0;
    }

    memset(&state, 0, sizeof(state));
    if (gModernizer_XInputGetState(0, &state) != 0) {
        return 0;
    }

    joystick->left = -1;
    joystick->right = -1;
    joystick->acc = Modernizer_MapTrigger(state.Gamepad.bRightTrigger);
    joystick->dec = Modernizer_MapTrigger(state.Gamepad.bLeftTrigger);

    axis = (int)state.Gamepad.sThumbLX;
    if (axis < -stick_dead_zone) {
        magnitude = -axis;
        joystick->left = Modernizer_MapStickMagnitude(magnitude, stick_dead_zone, 32768);
    } else if (axis > stick_dead_zone) {
        joystick->right = Modernizer_MapStickMagnitude(axis, stick_dead_zone, 32767);
    }

    return 1;
}
#endif
""",
        "native XInput helpers",
    )

    text = replace_once(
        text,
        """        if (gKey_mapping[49] < 115) {
            if (KeyIsDown(49) && !gRace_finished && !c->knackered && !gWait_for_it) {
                keys.dec = 1;
            }
        } else {
            joystick.dec = gJoy_array[gKey_mapping[49] - 115];
            if (joystick.dec > 0xFFFF) {
                joystick.dec = 0xFFFF;
            }
        }
        if (KeyIsDown(55) && c->gear >= 0) {""",
        """        if (gKey_mapping[49] < 115) {
            if (KeyIsDown(49) && !gRace_finished && !c->knackered && !gWait_for_it) {
                keys.dec = 1;
            }
        } else {
            joystick.dec = gJoy_array[gKey_mapping[49] - 115];
            if (joystick.dec > 0xFFFF) {
                joystick.dec = 0xFFFF;
            }
        }

#ifdef _WIN32
        /*
         * Modernizer native analog controls.
         *
         * Keep keyboard controls fully usable. Native XInput only takes over
         * an axis while that axis is actually being used.
         */
        {
            tJoystick native_joystick;
            native_joystick.left = -1;
            native_joystick.right = -1;
            native_joystick.acc = -1;
            native_joystick.dec = -1;

            if (Modernizer_ReadAnalogXInput(&native_joystick)) {
                if (!keys.left && !keys.right
                    && (native_joystick.left >= 0 || native_joystick.right >= 0)) {
                    joystick.left = native_joystick.left;
                    joystick.right = native_joystick.right;
                }

                if (!gRace_finished && !c->knackered && !gWait_for_it) {
                    if (!keys.acc && native_joystick.acc >= 0) {
                        joystick.acc = native_joystick.acc;
                    }
                    if (!keys.dec && native_joystick.dec >= 0) {
                        joystick.dec = native_joystick.dec;
                    }
                }
            }
        }
#endif

        if (KeyIsDown(55) && c->gear >= 0) {""",
        "native analog override in PollCarControls",
    )

    path.write_text(text, encoding="utf-8")


def patch_car(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = replace_once(
        text,
        "            brake_temp = (double)(c->joystick.dec / 0x10000) * c->brake_increase;",
        "            brake_temp = ((double)c->joystick.dec / 65535.0) * c->brake_increase;",
        "analog brake integer division",
    )
    path.write_text(text, encoding="utf-8")


def main() -> int:
    if len(sys.argv) != 2:
        print(f"Usage: {Path(sys.argv[0]).name} /path/to/dethrace-v0.10.1", file=sys.stderr)
        return 2

    root = Path(sys.argv[1]).resolve()
    controls = root / "src/DETHRACE/common/controls.c"
    car = root / "src/DETHRACE/common/car.c"

    for path in (controls, car):
        if not path.is_file():
            raise FileNotFoundError(path)

    patch_controls(controls)
    patch_car(car)
    print("Applied native analog XInput steering/throttle/brake support")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
