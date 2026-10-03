# Carmageddon / Dethrace - Portable XInput mapper
# Xbox / Xbox Elite controllers -> original Carmageddon keyboard controls.
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

    [DllImport("user32.dll", SetLastError=true)]
    private static extern void keybd_event(byte bVk, byte bScan, uint dwFlags, UIntPtr dwExtraInfo);

    private const uint KEYEVENTF_EXTENDEDKEY = 0x0001;
    private const uint KEYEVENTF_KEYUP = 0x0002;

    private static bool IsExtendedKey(int vk)
    {
        switch (vk)
        {
            case 0x21: // Page Up
            case 0x22: // Page Down
            case 0x23: // End
            case 0x24: // Home
            case 0x25: // Left
            case 0x26: // Up
            case 0x27: // Right
            case 0x28: // Down
            case 0x2D: // Insert
            case 0x2E: // Delete
                return true;
            default:
                return false;
        }
    }

    public static void KeyDown(int vk)
    {
        uint flags = IsExtendedKey(vk) ? KEYEVENTF_EXTENDEDKEY : 0;
        keybd_event((byte)vk, 0, flags, UIntPtr.Zero);
    }

    public static void KeyUp(int vk)
    {
        uint flags = KEYEVENTF_KEYUP;
        if (IsExtendedKey(vk)) {
            flags |= KEYEVENTF_EXTENDEDKEY;
        }
        keybd_event((byte)vk, 0, flags, UIntPtr.Zero);
    }
}
'@

Add-Type -TypeDefinition $code -Language CSharp

$root = Split-Path -Parent $PSScriptRoot
$exe = Join-Path $root "Runtime4x3\dethrace-4x3-v0.10.1.exe"

if (-not (Test-Path $exe)) {
    Add-Type -AssemblyName PresentationFramework
    [System.Windows.MessageBox]::Show(
        "dethrace-4x3-v0.10.1.exe was not found:`n$exe",
        "Carmageddon XInput Launcher"
    ) | Out-Null
    exit 1
}

$VK = @{
    ACCELERATE    = 0x68
    BRAKE         = 0x62
    LEFT          = 0x64
    RIGHT         = 0x66
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

$stickDeadZone = 8500
$lookDeadZone = 10000
$triggerThreshold = 30
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
        "Carmageddon XInput Launcher"
    ) | Out-Null
    exit 2
}

$argLine = '--dir "' + $root + '" -hires --opengl --fps=60 --physics-step-time=10'
$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = $exe
$psi.Arguments = $argLine
$psi.WorkingDirectory = $root
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

            if ($g.sThumbLX -lt -$stickDeadZone) { [void]$wanted.Add($VK.LEFT) }
            elseif ($g.sThumbLX -gt $stickDeadZone) { [void]$wanted.Add($VK.RIGHT) }

            if ($g.bRightTrigger -ge $triggerThreshold) { [void]$wanted.Add($VK.ACCELERATE) }
            if ($g.bLeftTrigger -ge $triggerThreshold) { [void]$wanted.Add($VK.BRAKE) }

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