# Carmageddon Splat Pack / Dethrace - Portable XInput mapper
# Xbox / Xbox Elite controller mapper.
# Steering + RT/LT are read natively/analog by the v13 EXE; this script handles digital buttons only.
# No AntiMicroX required.

$ErrorActionPreference = "Stop"

$code = @'
using System;
using System.Runtime.InteropServices;

public static class CarmaXInput
{
    [StructLayout(LayoutKind.Sequential)]
    public struct XINPUT_GAMEPAD
    {
        public ushort wButtons;
        public byte bLeftTrigger;
        public byte bRightTrigger;
        public short sThumbLX;
        public short sThumbLY;
        public short sThumbRX;
        public short sThumbRY;
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct XINPUT_STATE
    {
        public uint dwPacketNumber;
        public XINPUT_GAMEPAD Gamepad;
    }

    [DllImport("xinput1_4.dll", EntryPoint="XInputGetState")]
    public static extern uint XInputGetState(uint dwUserIndex, out XINPUT_STATE pState);

    [StructLayout(LayoutKind.Sequential)]
    private struct INPUT
    {
        public uint type;
        public INPUTUNION U;
    }

    [StructLayout(LayoutKind.Explicit)]
    private struct INPUTUNION
    {
        [FieldOffset(0)]
        public KEYBDINPUT ki;

        // Keep the union at the native INPUT size on both x86 and x64.
        // Without MOUSEINPUT the managed union would be only 24 bytes on x64,
        // making INPUT 32 instead of the Win32-required 40 bytes and causing
        // SendInput to fail with ERROR_INVALID_PARAMETER.
        [FieldOffset(0)]
        public MOUSEINPUT mi;
    }

    [StructLayout(LayoutKind.Sequential)]
    private struct MOUSEINPUT
    {
        public int dx;
        public int dy;
        public uint mouseData;
        public uint dwFlags;
        public uint time;
        public UIntPtr dwExtraInfo;
    }

    [StructLayout(LayoutKind.Sequential)]
    private struct KEYBDINPUT
    {
        public ushort wVk;
        public ushort wScan;
        public uint dwFlags;
        public uint time;
        public UIntPtr dwExtraInfo;
    }

    [DllImport("user32.dll", SetLastError=true)]
    private static extern uint SendInput(uint nInputs, INPUT[] pInputs, int cbSize);

    [DllImport("user32.dll")]
    private static extern uint MapVirtualKey(uint uCode, uint uMapType);

    private const uint INPUT_KEYBOARD = 1;
    private const uint MAPVK_VK_TO_VSC = 0;
    private const uint KEYEVENTF_EXTENDEDKEY = 0x0001;
    private const uint KEYEVENTF_KEYUP = 0x0002;
    private const uint KEYEVENTF_SCANCODE = 0x0008;

    private static bool IsExtendedKey(int vk)
    {
        switch (vk)
        {
            case 0x21: // Page Up
            case 0x22: // Page Down
            case 0x23: // End
            case 0x24: // Home
            case 0x25: // Left  = E0 4B
            case 0x26: // Up    = E0 48
            case 0x27: // Right = E0 4D
            case 0x28: // Down  = E0 50
            case 0x2D: // Insert = E0 52 (Recovery)
            case 0x2E: // Delete
                return true;
            default:
                return false;
        }
    }

    private static void SendScanCode(int vk, bool keyUp)
    {
        ushort scan = (ushort)(MapVirtualKey((uint)vk, MAPVK_VK_TO_VSC) & 0xFF);
        if (scan == 0) {
            throw new InvalidOperationException("Could not map virtual key 0x" + vk.ToString("X2") + " to a scan code.");
        }

        uint flags = KEYEVENTF_SCANCODE;
        if (IsExtendedKey(vk)) {
            flags |= KEYEVENTF_EXTENDEDKEY;
        }
        if (keyUp) {
            flags |= KEYEVENTF_KEYUP;
        }

        INPUT input = new INPUT();
        input.type = INPUT_KEYBOARD;
        input.U.ki.wVk = 0;
        input.U.ki.wScan = scan;
        input.U.ki.dwFlags = flags;
        input.U.ki.time = 0;
        input.U.ki.dwExtraInfo = UIntPtr.Zero;

        INPUT[] inputs = new INPUT[] { input };
        if (SendInput(1, inputs, Marshal.SizeOf(typeof(INPUT))) != 1) {
            throw new System.ComponentModel.Win32Exception(Marshal.GetLastWin32Error(), "SendInput failed");
        }
    }

    public static void KeyDown(int vk)
    {
        SendScanCode(vk, false);
    }

    public static void KeyUp(int vk)
    {
        SendScanCode(vk, true);
    }
}
'@

Add-Type -TypeDefinition $code -Language CSharp

$root = Split-Path -Parent $PSScriptRoot
$exe = Join-Path $root "Runtime4x3\dethrace-4x3-v0.10.1.exe"
$splat = Join-Path $root "CARSPLAT"

if (-not (Test-Path $exe)) {
    Add-Type -AssemblyName PresentationFramework
    [System.Windows.MessageBox]::Show(
        "The 4:3 Modernizer executable was not found:`n$exe",
        "Carmageddon Splat Pack XInput Launcher"
    ) | Out-Null
    exit 1
}

if (-not (Test-Path (Join-Path $splat "DATA"))) {
    Add-Type -AssemblyName PresentationFramework
    [System.Windows.MessageBox]::Show(
        "CARSPLAT\\DATA was not found:`n$splat`n`nCopy the complete CARSPLAT folder into the Dethrace main folder first.",
        "Carmageddon Splat Pack XInput Launcher"
    ) | Out-Null
    exit 1
}

$VK = @{
    HANDBRAKE     = 0x20
    REPAIR        = 0x08
    RECOVER       = 0x2D
    WHEELSPIN     = 0x5A
    COCKPIT       = 0x43
    LOOKLEFT      = 0x51
    LOOKFORWARD   = 0x57
    LOOKRIGHT     = 0x45
    MAP           = 0x09
    CURSOR_LEFT   = 0x25
    CURSOR_UP     = 0x26
    CURSOR_RIGHT  = 0x27
    CURSOR_DOWN   = 0x28
    ESCAPE        = 0x1B
    HORN          = 0x48
}

$BTN = @{
    DPAD_UP    = 0x0001
    DPAD_DOWN  = 0x0002
    DPAD_LEFT  = 0x0004
    DPAD_RIGHT = 0x0008
    START      = 0x0010
    BACK       = 0x0020
    LTHUMB     = 0x0040
    RTHUMB     = 0x0080
    LB         = 0x0100
    RB         = 0x0200
    A          = 0x1000
    B          = 0x2000
    X          = 0x4000
    Y          = 0x8000
}

$lookDeadZone = 10000
$held = New-Object 'System.Collections.Generic.HashSet[int]'

function Set-KeyState([System.Collections.Generic.HashSet[int]] $wanted) {
    foreach ($key in @($held)) {
        if (-not $wanted.Contains($key)) {
            [CarmaXInput]::KeyUp($key)
            [void]$held.Remove($key)
        }
    }
    foreach ($key in $wanted) {
        if (-not $held.Contains($key)) {
            [CarmaXInput]::KeyDown($key)
            [void]$held.Add($key)
        }
    }
}

function Release-All {
    foreach ($key in @($held)) {
        [CarmaXInput]::KeyUp($key)
    }
    $held.Clear()
}

$state = New-Object CarmaXInput+XINPUT_STATE
$result = [CarmaXInput]::XInputGetState(0, [ref]$state)

if ($result -ne 0) {
    Add-Type -AssemblyName PresentationFramework
    [System.Windows.MessageBox]::Show(
        "No XInput controller was found in slot 1.`n`nConnect/enable the controller and start again.",
        "Carmageddon Splat Pack XInput Launcher"
    ) | Out-Null
    exit 2
}

$argLine = '--dir "' + $splat + '" -hires --opengl --fps=60 --physics-step-time=10'
$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = $exe
$psi.Arguments = $argLine
$psi.WorkingDirectory = $splat
$psi.UseShellExecute = $true
$game = [System.Diagnostics.Process]::Start($psi)

try {
    while (-not $game.HasExited) {
        $state = New-Object CarmaXInput+XINPUT_STATE
        $result = [CarmaXInput]::XInputGetState(0, [ref]$state)
        $wanted = New-Object 'System.Collections.Generic.HashSet[int]'

        if ($result -eq 0) {
            $g = $state.Gamepad
            $buttons = [int]$g.wButtons

            if (($buttons -band $BTN.A) -ne 0) { [void]$wanted.Add($VK.HANDBRAKE) }
            if (($buttons -band $BTN.B) -ne 0) { [void]$wanted.Add($VK.WHEELSPIN) }
            if (($buttons -band $BTN.X) -ne 0) { [void]$wanted.Add($VK.REPAIR) }
            if (($buttons -band $BTN.Y) -ne 0) { [void]$wanted.Add($VK.RECOVER) }
            if (($buttons -band $BTN.BACK) -ne 0) { [void]$wanted.Add($VK.MAP) }
            if (($buttons -band $BTN.START) -ne 0) { [void]$wanted.Add($VK.ESCAPE) }
            if (($buttons -band $BTN.DPAD_LEFT) -ne 0) { [void]$wanted.Add($VK.CURSOR_LEFT) }
            if (($buttons -band $BTN.DPAD_UP) -ne 0) { [void]$wanted.Add($VK.CURSOR_UP) }
            if (($buttons -band $BTN.DPAD_RIGHT) -ne 0) { [void]$wanted.Add($VK.CURSOR_RIGHT) }
            if (($buttons -band $BTN.DPAD_DOWN) -ne 0) { [void]$wanted.Add($VK.CURSOR_DOWN) }

            if ($g.sThumbRX -lt -$lookDeadZone) { [void]$wanted.Add($VK.LOOKLEFT) }
            elseif ($g.sThumbRX -gt $lookDeadZone) { [void]$wanted.Add($VK.LOOKRIGHT) }
            elseif ($g.sThumbRY -gt $lookDeadZone) { [void]$wanted.Add($VK.LOOKFORWARD) }

            if (($buttons -band $BTN.LB) -ne 0) { [void]$wanted.Add($VK.LOOKLEFT) }
            if (($buttons -band $BTN.RB) -ne 0) { [void]$wanted.Add($VK.LOOKRIGHT) }
            if (($buttons -band $BTN.RTHUMB) -ne 0) { [void]$wanted.Add($VK.COCKPIT) }
            if (($buttons -band $BTN.LTHUMB) -ne 0) { [void]$wanted.Add($VK.HORN) }
        }

        Set-KeyState $wanted
        Start-Sleep -Milliseconds 8
        $game.Refresh()
    }
}
finally {
    Release-All
}