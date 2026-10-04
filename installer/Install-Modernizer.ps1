param(
    [string]$TargetDir,
    [string]$Components,
    [string]$OriginalSource,
    [string]$GermanSource
)

[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [Console]::OutputEncoding

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$ModernizerVersion = "0.9.0-rc2-installer-polish"
$EngineVersion = "v1.5-goldstandard-rc1"
$PackageRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$MainDeltaRoot = Join-Path $PackageRoot "German\Main"
$SplatDeltaRoot = Join-Path $PackageRoot "German\Splat"
$DamageHudRoot = Join-Path $PackageRoot "DamageHUD"

function Fail([string]$Message) {
    Write-Host ""
    Write-Host "ERROR: $Message" -ForegroundColor Red
    Write-Host ""
    exit 1
}

function Select-Folder([string]$Description) {
    Add-Type -AssemblyName System.Windows.Forms
    $dialog = New-Object System.Windows.Forms.FolderBrowserDialog
    $dialog.Description = $Description
    $dialog.ShowNewFolderButton = $true
    if ($dialog.ShowDialog() -ne [System.Windows.Forms.DialogResult]::OK) {
        exit 2
    }
    return $dialog.SelectedPath
}

$script:HashCache = @{}

function Get-Sha256([string]$Path) {
    $item = Get-Item -LiteralPath $Path
    $full = [System.IO.Path]::GetFullPath($item.FullName)
    $cacheKey = $full + "|" + $item.Length + "|" + $item.LastWriteTimeUtc.Ticks

    if ($script:HashCache.ContainsKey($cacheKey)) {
        return [string]$script:HashCache[$cacheKey]
    }

    $hash = (Get-FileHash -LiteralPath $full -Algorithm SHA256).Hash.ToLowerInvariant()
    $script:HashCache[$cacheKey] = $hash
    return $hash
}

function Get-Manifest([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "Manifest missing: $Path"
    }
    return (Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json)
}

function Restore-StaleInstall([string]$GameDir, [string]$StateDir, [string]$PackageRoot, $MainManifest, $SplatManifest) {
    $backupRoot = Join-Path $StateDir "backup"
    Write-Host ""
    Write-Host "An incomplete previous Modernizer installation was found." -ForegroundColor Yellow
    Write-Host "Restoring the previous state first..."

    $journalFile = Join-Path $StateDir "transaction.journal"
    if (Test-Path -LiteralPath $journalFile -PathType Leaf) {
        try {
            $journalRecords = New-Object System.Collections.Generic.List[object]
            foreach ($line in @(Get-Content -LiteralPath $journalFile -ErrorAction Stop)) {
                if ([string]::IsNullOrWhiteSpace($line)) { continue }
                [void]$journalRecords.Add(($line | ConvertFrom-Json))
            }

            [object[]]$transactionRecords = @($journalRecords | ForEach-Object { $_ })
            [array]::Reverse($transactionRecords)
            foreach ($record in $transactionRecords) {
                $destination = Join-Path $GameDir ([string]$record.path)
                if ([bool]$record.existedBefore -and $record.backupPath) {
                    $backupPath = Join-Path $backupRoot ([string]$record.backupPath)
                    if (Test-Path -LiteralPath $backupPath -PathType Leaf) {
                        New-Item -ItemType Directory -Path (Split-Path -Parent $destination) -Force | Out-Null
                        if (Test-Path -LiteralPath $destination -PathType Leaf) {
                            Remove-Item -LiteralPath $destination -Force
                        }
                        Move-Item -LiteralPath $backupPath -Destination $destination -Force
                    }
                    # If the journal entry was appended immediately before the
                    # move and the process died first, the original destination
                    # is still intact and there is nothing to restore.
                }
                elseif (Test-Path -LiteralPath $destination -PathType Leaf) {
                    Remove-Item -LiteralPath $destination -Force
                }
            }
            Remove-Item -LiteralPath $StateDir -Recurse -Force
            Write-Host "Previous state restored from the transaction journal." -ForegroundColor Green
            return
        }
        catch {
            Write-Host ("Transaction journal recovery failed: " + $_.Exception.Message) -ForegroundColor Red
            throw
        }
    }

    # Compatibility with earlier test installers.
    $transactionFile = Join-Path $StateDir "transaction.json"
    if (Test-Path -LiteralPath $transactionFile -PathType Leaf) {
        try {
            $transaction = Get-Content -LiteralPath $transactionFile -Raw | ConvertFrom-Json
            [object[]]$transactionRecords = @($transaction.files | ForEach-Object { $_ })
            [array]::Reverse($transactionRecords)
            foreach ($record in $transactionRecords) {
                $destination = Join-Path $GameDir ([string]$record.path)
                if ([bool]$record.existedBefore -and $record.backupPath) {
                    $backupPath = Join-Path $backupRoot ([string]$record.backupPath)
                    if (-not (Test-Path -LiteralPath $backupPath -PathType Leaf)) {
                        throw "Backup file missing: $backupPath"
                    }
                    New-Item -ItemType Directory -Path (Split-Path -Parent $destination) -Force | Out-Null
                    if (Test-Path -LiteralPath $destination -PathType Leaf) {
                        Remove-Item -LiteralPath $destination -Force
                    }
                    Move-Item -LiteralPath $backupPath -Destination $destination -Force
                }
                elseif (Test-Path -LiteralPath $destination -PathType Leaf) {
                    Remove-Item -LiteralPath $destination -Force
                }
            }
            Remove-Item -LiteralPath $StateDir -Recurse -Force
            Write-Host "Previous state restored from the transaction journal." -ForegroundColor Green
            return
        }
        catch {
            Write-Host ("Transaction recovery failed: " + $_.Exception.Message) -ForegroundColor Red
            throw
        }
    }

    if (Test-Path -LiteralPath $backupRoot -PathType Container) {
        foreach ($backup in @(Get-ChildItem -LiteralPath $backupRoot -File -Recurse -Force)) {
            $relative = $backup.FullName.Substring($backupRoot.Length).TrimStart([char]92)
            $destination = Join-Path $GameDir $relative
            New-Item -ItemType Directory -Path (Split-Path -Parent $destination) -Force | Out-Null
            Copy-Item -LiteralPath $backup.FullName -Destination $destination -Force
        }
    }

    # v0.2-test could fail after copying files but before install.json existed.
    # If a known installer-created file has no backup and still exactly matches
    # this package, it did not exist before that interrupted run and can be
    # removed safely. Files with a backup have already been restored above.
    $knownPackageFiles = @(
        "dethrace-16x9-v1.5.exe",
        "Start-Carmageddon-16x9.cmd",
        "Start-Carmageddon-16x9-XInput.cmd",
        "Start-Carmageddon-XInput.cmd",
        "Controller\Carmageddon-XInput.ps1",
        "Controller\Carmageddon-XInput-Native.ps1",
        "Uninstall-Modernizer.ps1",
        "Uninstall-Modernizer.cmd",
        "Start-CARSPLAT-16x9.cmd",
        "Start-CARSPLAT-16x9-XInput.cmd",
        "Start-CARSPLAT-XInput.cmd",
        "Controller\Carmageddon-SplatPack-XInput.ps1",
        "Controller\Carmageddon-SplatPack-XInput-Native.ps1"
    )
    foreach ($relative in $knownPackageFiles) {
        $backup = Join-Path $backupRoot $relative
        if (Test-Path -LiteralPath $backup -PathType Leaf) { continue }
        $destination = Join-Path $GameDir $relative
        $packageFile = Join-Path $PackageRoot $relative
        if ((Test-Path -LiteralPath $destination -PathType Leaf) -and
            (Test-Path -LiteralPath $packageFile -PathType Leaf) -and
            ((Get-Sha256 $destination) -eq (Get-Sha256 $packageFile))) {
            Remove-Item -LiteralPath $destination -Force
        }
    }

    Remove-Item -LiteralPath $StateDir -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "Previous state restored." -ForegroundColor Green
}

function Test-TargetSet([string]$Root, $Manifest) {
    if (-not (Test-Path -LiteralPath $Root -PathType Container)) { return $false }
    foreach ($entry in @($Manifest.files)) {
        $path = Join-Path $Root ([string]$entry.path)
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { return $false }
        if ((Get-Item -LiteralPath $path).Length -ne [int64]$entry.target_size) { return $false }
        if ((Get-Sha256 $path) -ne ([string]$entry.target_sha256).ToLowerInvariant()) { return $false }
    }
    return $true
}

function Test-MainSourceSet([string]$Root, $Manifest) {
    if (-not (Test-Path -LiteralPath $Root -PathType Container)) { return $false }
    foreach ($entry in @($Manifest.files)) {
        $path = Join-Path $Root ([string]$entry.path)
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { return $false }
        if ((Get-Item -LiteralPath $path).Length -ne [int64]$entry.source_size) { return $false }
        if ((Get-Sha256 $path) -ne ([string]$entry.source_sha256).ToLowerInvariant()) { return $false }
    }
    return $true
}

function Test-SplatSourceSet([string]$Root, $Manifest) {
    if (-not (Test-Path -LiteralPath $Root -PathType Container)) { return $false }
    foreach ($entry in @($Manifest.files | Where-Object { $_.mode -eq "xor_from_splat" })) {
        $path = Join-Path $Root ([string]$entry.path)
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { return $false }
        if ((Get-Item -LiteralPath $path).Length -ne [int64]$entry.source_size) { return $false }
        if ((Get-Sha256 $path) -ne ([string]$entry.source_sha256).ToLowerInvariant()) { return $false }
    }
    return $true
}

function Normalize-InputPath([string]$Value) {
    if ([string]::IsNullOrWhiteSpace($Value)) { return $null }
    $v = $Value.Trim().Trim('"')
    if ([string]::IsNullOrWhiteSpace($v)) { return $null }
    return [System.IO.Path]::GetFullPath($v)
}

function Read-PathOrBrowse([string]$Prompt, [string]$Description) {
    Write-Host ""
    Write-Host $Prompt
    Write-Host "Paste a path directly, or press ENTER to open the folder picker."
    $value = Read-Host "Path"
    if ([string]::IsNullOrWhiteSpace($value)) {
        return Select-Folder $Description
    }
    return Normalize-InputPath $value
}

function Get-DataCandidates([string]$Selected) {
    $root = Normalize-InputPath $Selected
    if ($null -eq $root -or -not (Test-Path -LiteralPath $root -PathType Container)) { return @() }

    $items = @(
        $root,
        (Join-Path $root "DATA"),
        (Join-Path $root "CARMA\DATA"),
        (Join-Path $root "CARSPLAT\DATA")
    )
    foreach ($child in @(Get-ChildItem -LiteralPath $root -Directory -ErrorAction SilentlyContinue)) {
        $items += (Join-Path $child.FullName "DATA")
        $items += (Join-Path $child.FullName "CARSPLAT\DATA")
    }

    $result = @()
    foreach ($item in $items) {
        if ((Test-Path -LiteralPath $item -PathType Container) -and ($result -notcontains $item)) {
            $result += [System.IO.Path]::GetFullPath($item)
        }
    }
    return $result
}

function Resolve-MainSourceRoot([string]$Selected, $Manifest) {
    foreach ($candidate in @(Get-DataCandidates $Selected)) {
        if (Test-MainSourceSet $candidate $Manifest) { return $candidate }
    }
    return $null
}

function Resolve-SplatSourceRoot([string]$Selected, $Manifest) {
    foreach ($candidate in @(Get-DataCandidates $Selected)) {
        if (Test-SplatSourceSet $candidate $Manifest) { return $candidate }
    }
    return $null
}

function Read-ComponentSelection([string]$Preset) {
    if (-not [string]::IsNullOrWhiteSpace($Preset)) { $choice = $Preset }
    else {
        Write-Host ""
        Write-Host "Which components do you want to install?" -ForegroundColor Cyan
        Write-Host "  [1] 16:9 widescreen source port"
        Write-Host "  [2] XInput controller support"
        Write-Host "  [3] German/Uncut localization (experimental)"
        Write-Host ""
        Write-Host "Examples: 12 = 16:9 + XInput, 123 = everything, 3 = German/Uncut only"
        Write-Host "ENTER = 16:9 + XInput"
        $choice = Read-Host "Selection"
        if ([string]::IsNullOrWhiteSpace($choice)) { $choice = "12" }
    }
    $choice = $choice.ToLowerInvariant()
    return [pscustomobject]@{
        Wide = ($choice -match '1|16x9|wide')
        XInput = ($choice -match '2|xinput|pad')
        German = ($choice -match '3|german|deutsch')
    }
}

if (-not ("ModernizerXor" -as [type])) {
    Add-Type -TypeDefinition @"
using System;
using System.IO;
public static class ModernizerXor {
    public static void Apply(string sourcePath, string patchPath, string targetPath) {
        byte[] source = File.ReadAllBytes(sourcePath);
        byte[] patch = File.ReadAllBytes(patchPath);
        byte[] target = new byte[patch.Length];
        for (int i = 0; i < patch.Length; i++) {
            byte s = i < source.Length ? source[i] : (byte)0;
            target[i] = (byte)(patch[i] ^ s);
        }
        string parent = Path.GetDirectoryName(targetPath);
        if (!String.IsNullOrEmpty(parent)) Directory.CreateDirectory(parent);
        File.WriteAllBytes(targetPath, target);
    }
}
"@
}

function Build-MainStage([string]$SourceRoot, [string]$StageRoot, $Manifest) {
    if (Test-Path -LiteralPath $StageRoot) { Remove-Item -LiteralPath $StageRoot -Recurse -Force }
    New-Item -ItemType Directory -Path $StageRoot -Force | Out-Null
    $index = 0
    foreach ($entry in @($Manifest.files)) {
        $index++
        if (($index % 25) -eq 0) { Write-Host "  Main game: $index / $($Manifest.counts.total)" }
        $src = Join-Path $SourceRoot ([string]$entry.path)
        $dst = Join-Path $StageRoot ([string]$entry.path)
        if ((Get-Sha256 $src) -ne ([string]$entry.source_sha256).ToLowerInvariant()) {
            throw "German source file does not match the supported profile: $($entry.path)"
        }
        New-Item -ItemType Directory -Path (Split-Path -Parent $dst) -Force | Out-Null
        if ($entry.mode -eq "copy") {
            Copy-Item -LiteralPath $src -Destination $dst -Force
        }
        elseif ($entry.mode -eq "xor") {
            $patch = Join-Path $MainDeltaRoot ([string]$entry.patch)
            [ModernizerXor]::Apply($src, $patch, $dst)
        }
        else {
            throw "Unknown main-game delta mode: $($entry.mode)"
        }
        if ((Get-Item -LiteralPath $dst).Length -ne [int64]$entry.target_size -or
            (Get-Sha256 $dst) -ne ([string]$entry.target_sha256).ToLowerInvariant()) {
            throw "Main-game target file could not be verified: $($entry.path)"
        }
    }
}

function Build-SplatStage([string]$MainFinalRoot, [string]$SplatSourceRoot, [string]$StageRoot, $Manifest) {
    if (Test-Path -LiteralPath $StageRoot) { Remove-Item -LiteralPath $StageRoot -Recurse -Force }
    New-Item -ItemType Directory -Path $StageRoot -Force | Out-Null
    $index = 0
    foreach ($entry in @($Manifest.files)) {
        $index++
        if (($index % 25) -eq 0) { Write-Host "  Splat Pack: $index / $($Manifest.counts.total)" }
        $dst = Join-Path $StageRoot ([string]$entry.path)
        New-Item -ItemType Directory -Path (Split-Path -Parent $dst) -Force | Out-Null
        if ($entry.mode -eq "copy_from_main") {
            $src = Join-Path $MainFinalRoot ([string]$entry.path)
            if (-not (Test-Path -LiteralPath $src -PathType Leaf)) { throw "Main-game file required by Splat Pack is missing: $($entry.path)" }
            if ((Get-Sha256 $src) -ne ([string]$entry.target_sha256).ToLowerInvariant()) {
                throw "Main-game file required by Splat Pack does not match: $($entry.path)"
            }
            Copy-Item -LiteralPath $src -Destination $dst -Force
        }
        elseif ($entry.mode -eq "xor_from_splat") {
            $src = Join-Path $SplatSourceRoot ([string]$entry.path)
            if ((Get-Sha256 $src) -ne ([string]$entry.source_sha256).ToLowerInvariant()) {
                throw "Splat Pack source file does not match the supported profile: $($entry.path)"
            }
            $patch = Join-Path $SplatDeltaRoot ([string]$entry.patch)
            [ModernizerXor]::Apply($src, $patch, $dst)
        }
        else {
            throw "Unknown Splat Pack delta mode: $($entry.mode)"
        }
        if ((Get-Item -LiteralPath $dst).Length -ne [int64]$entry.target_size -or
            (Get-Sha256 $dst) -ne ([string]$entry.target_sha256).ToLowerInvariant()) {
            throw "Splat Pack target file could not be verified: $($entry.path)"
        }
    }
}

function Resolve-BaseInstallation([string]$Selected) {
    $root = Normalize-InputPath $Selected
    if ($null -eq $root -or -not (Test-Path -LiteralPath $root -PathType Container)) {
        return $null
    }

    $mainCandidates = New-Object System.Collections.Generic.List[string]

    if ((Split-Path -Leaf $root) -ieq "DATA") {
        [void]$mainCandidates.Add($root)
    }
    [void]$mainCandidates.Add((Join-Path $root "DATA"))
    [void]$mainCandidates.Add((Join-Path $root "CARMA\DATA"))

    foreach ($child in @(Get-ChildItem -LiteralPath $root -Directory -ErrorAction SilentlyContinue)) {
        [void]$mainCandidates.Add((Join-Path $child.FullName "DATA"))
    }

    $mainData = $null
    foreach ($candidate in @($mainCandidates | ForEach-Object { $_ })) {
        if (Test-Path -LiteralPath (Join-Path $candidate "GENERAL.TXT") -PathType Leaf) {
            $mainData = [System.IO.Path]::GetFullPath($candidate)
            break
        }
    }
    if ($null -eq $mainData) { return $null }

    $mainRoot = Split-Path -Parent $mainData

    $splatCandidates = New-Object System.Collections.Generic.List[string]
    [void]$splatCandidates.Add((Join-Path $root "CARSPLAT\DATA"))
    [void]$splatCandidates.Add((Join-Path $mainRoot "CARSPLAT\DATA"))

    $mainParent = Split-Path -Parent $mainRoot
    if (-not [string]::IsNullOrWhiteSpace($mainParent)) {
        [void]$splatCandidates.Add((Join-Path $mainParent "CARSPLAT\DATA"))
    }

    foreach ($child in @(Get-ChildItem -LiteralPath $root -Directory -ErrorAction SilentlyContinue)) {
        [void]$splatCandidates.Add((Join-Path $child.FullName "CARSPLAT\DATA"))
        if ($child.Name -ieq "CARSPLAT") {
            [void]$splatCandidates.Add((Join-Path $child.FullName "DATA"))
        }
    }

    $splatData = $null
    foreach ($candidate in @($splatCandidates | ForEach-Object { $_ })) {
        if (Test-Path -LiteralPath (Join-Path $candidate "RACES\CASTLE2.TXT") -PathType Leaf) {
            $splatData = [System.IO.Path]::GetFullPath($candidate)
            break
        }
    }

    $splatRoot = $null
    if ($null -ne $splatData) {
        $splatRoot = Split-Path -Parent $splatData
    }

    return [pscustomobject]@{
        SelectedRoot = $root
        MainRoot = $mainRoot
        MainData = $mainData
        SplatRoot = $splatRoot
        SplatData = $splatData
    }
}

function Test-PathInside([string]$Child, [string]$Parent) {
    $childFull = ([System.IO.Path]::GetFullPath($Child)).TrimEnd([char]92) + "\"
    $parentFull = ([System.IO.Path]::GetFullPath($Parent)).TrimEnd([char]92) + "\"
    return $childFull.StartsWith($parentFull, [System.StringComparison]::OrdinalIgnoreCase)
}

function Copy-DirectoryContents([string]$SourceRoot, [string]$DestinationRoot, [string]$Label = "game data") {
    New-Item -ItemType Directory -Path $DestinationRoot -Force | Out-Null
    $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()

    $robocopy = Get-Command robocopy.exe -ErrorAction SilentlyContinue
    if ($null -ne $robocopy) {
        Write-Host ("Copying " + $Label + " with Windows Robocopy...")
        & $robocopy.Source $SourceRoot $DestinationRoot /E /COPY:DAT /DCOPY:T /R:1 /W:1 /NFL /NDL /NJH /NJS /NP /XD ".dethrace-modernizer" ".modernizer"
        $code = $LASTEXITCODE
        if ($code -ge 8) {
            throw "Robocopy failed while copying $Label (exit code $code)."
        }
    }
    else {
        Write-Host ("Copying " + $Label + "...")
        foreach ($item in @(Get-ChildItem -LiteralPath $SourceRoot -Force)) {
            if ($item.Name -ieq ".dethrace-modernizer" -or $item.Name -ieq ".modernizer") {
                continue
            }
            Copy-Item -LiteralPath $item.FullName -Destination $DestinationRoot -Recurse -Force
        }
    }

    $stopwatch.Stop()
    Write-Host ("  Done in {0:hh\:mm\:ss}." -f $stopwatch.Elapsed) -ForegroundColor Green
}

# ---------------------------------------------------------------------------
# Target-first flow
# ---------------------------------------------------------------------------

if ([string]::IsNullOrWhiteSpace($TargetDir)) {
    $TargetDir = Read-PathOrBrowse `
        "Target directory for the finished Modernizer installation:" `
        "Select the target directory for the finished Modernizer installation"
}
$GameDir = Normalize-InputPath $TargetDir

if (-not (Test-Path -LiteralPath $GameDir -PathType Container)) {
    New-Item -ItemType Directory -Path $GameDir -Force | Out-Null
}

$existingItems = @(Get-ChildItem -LiteralPath $GameDir -Force -ErrorAction SilentlyContinue)
if ($existingItems.Count -gt 0) {
    Fail "The target directory is not empty. For this target-first test, please choose a new or empty folder."
}

$selection = Read-ComponentSelection $Components
$Install16x9 = [bool]$selection.Wide
$InstallXInput = [bool]$selection.XInput
$InstallGerman = [bool]$selection.German
if (-not $Install16x9 -and -not $InstallXInput -and -not $InstallGerman) {
    Fail "No component was selected."
}

Write-Host ""
Write-Host "Selected:" -ForegroundColor Cyan
Write-Host ("  16:9:        " + $(if ($Install16x9) { "YES" } else { "no" }))
Write-Host ("  XInput:      " + $(if ($InstallXInput) { "YES" } else { "no" }))
Write-Host ("  German:      " + $(if ($InstallGerman) { "YES (experimental)" } else { "no" }))

if ($InstallGerman) {
    Write-Host ""
    Write-Host "German/Uncut is experimental." -ForegroundColor Yellow
    Write-Host "Known minor menu/localization visual issues may remain."
}

# Validate the package runtimes before touching any game data.
$baseExe = Join-Path $PackageRoot "Runtime4x3\dethrace-4x3-v0.10.1.exe"
if (-not (Test-Path -LiteralPath $baseExe -PathType Leaf)) {
    Fail "Runtime4x3\dethrace-4x3-v0.10.1.exe is missing from the Modernizer package."
}
if ($Install16x9) {
    $sourceExe = Join-Path $PackageRoot "dethrace-16x9-v1.5.exe"
    if (-not (Test-Path -LiteralPath $sourceExe -PathType Leaf)) {
        Fail "dethrace-16x9-v1.5.exe is missing from the Modernizer package."
    }
}

# Resolve the original source now, before any large copy starts.
$base = $null
while ($null -eq $base) {
    if ([string]::IsNullOrWhiteSpace($OriginalSource)) {
        $OriginalSource = Read-PathOrBrowse `
            "Original/English Carmageddon installation (source; remains untouched):" `
            "Select the original / English Carmageddon installation"
    }

    $OriginalSource = Normalize-InputPath $OriginalSource
    $base = Resolve-BaseInstallation $OriginalSource
    if ($null -eq $base) {
        Write-Host ""
        Write-Host "The selected folder is not a supported Carmageddon installation." -ForegroundColor Red
        $retry = Read-Host "Press ENTER to choose another folder, or type C to cancel"
        if ($retry -match '^[Cc]') { exit 2 }
        $OriginalSource = $null
    }
}

if ((Test-PathInside $GameDir $base.MainRoot) -or (Test-PathInside $base.MainRoot $GameDir)) {
    Fail "Target directory and original source must not be inside one another."
}
if ($null -ne $base.SplatRoot) {
    if ((Test-PathInside $GameDir $base.SplatRoot) -or (Test-PathInside $base.SplatRoot $GameDir)) {
        Fail "Target directory and Splat Pack source must not be inside one another."
    }
}

$mainManifest = $null
$splatManifest = $null
$sourceRoot = $null
$splatSourceRoot = $null

if ($InstallGerman) {
    $mainManifest = Get-Manifest (Join-Path $MainDeltaRoot "manifest.json")
    $splatManifest = Get-Manifest (Join-Path $SplatDeltaRoot "manifest.json")

    while ($InstallGerman -and $null -eq $sourceRoot) {
        if ([string]::IsNullOrWhiteSpace($GermanSource)) {
            $GermanSource = Read-PathOrBrowse `
                "German Carmageddon installation (experimental source; remains untouched):" `
                "Select the German Carmageddon installation"
        }

        $GermanSource = Normalize-InputPath $GermanSource
        $sourceRoot = Resolve-MainSourceRoot $GermanSource $mainManifest
        if ($null -eq $sourceRoot) {
            Write-Host ""
            Write-Host "The selected folder is not the supported German Carmageddon version." -ForegroundColor Red
            $answer = Read-Host "ENTER = choose another folder, S = skip German/Uncut, C = cancel"
            if ($answer -match '^[Cc]') { exit 2 }
            if ($answer -match '^[Ss]') {
                $InstallGerman = $false
                $GermanSource = $null
                $mainManifest = $null
                $splatManifest = $null
                break
            }
            $GermanSource = $null
        }
    }

    if ($InstallGerman -and $null -ne $base.SplatRoot) {
        $splatSourceRoot = Resolve-SplatSourceRoot $OriginalSource $splatManifest
        if ($null -eq $splatSourceRoot) {
            Write-Host ""
            Write-Host "The detected Splat Pack revision is not supported by the experimental German patch." -ForegroundColor Red
            $answer = Read-Host "S = continue without German/Uncut, C = cancel"
            if ($answer -match '^[Ss]') {
                $InstallGerman = $false
                $GermanSource = $null
                $sourceRoot = $null
                $mainManifest = $null
                $splatManifest = $null
            }
            else {
                exit 2
            }
        }
    }
}

Write-Host ""
Write-Host "Preflight complete:" -ForegroundColor Cyan
Write-Host "  Target:       $GameDir"
Write-Host "  Main source:  $($base.MainRoot)"
Write-Host ("  Splat Pack:   " + $(if ($null -ne $base.SplatRoot) { $base.SplatRoot } else { "not found" }))
Write-Host ("  16:9:         " + $(if ($Install16x9) { "YES" } else { "no" }))
Write-Host ("  XInput:       " + $(if ($InstallXInput) { "YES" } else { "no" }))
Write-Host ("  German:       " + $(if ($InstallGerman) { "YES - experimental ($sourceRoot)" } else { "no" }))
Write-Host ""
$continue = Read-Host "Start installation now? [Y/n]"
if ($continue -match '^[Nn]') { exit 2 }

Write-Host ""
Write-Host "Copying the original version into the target directory..."
Copy-DirectoryContents $base.MainRoot $GameDir "main game"

# Some layouts (for example CARMA + sibling CARSPLAT) keep Splat outside the
# main-game root. Copy that sibling into the conventional target location.
if ($null -ne $base.SplatRoot -and -not (Test-PathInside $base.SplatRoot $base.MainRoot)) {
    $targetSplatRoot = Join-Path $GameDir "CARSPLAT"
    Copy-DirectoryContents $base.SplatRoot $targetSplatRoot "Splat Pack"
}

$mainData = Join-Path $GameDir "DATA"
$general = Join-Path $mainData "GENERAL.TXT"
if (-not (Test-Path -LiteralPath $general -PathType Leaf)) {
    Fail "The base copy is incomplete: DATA\GENERAL.TXT is missing from the target."
}

$splatData = Join-Path $GameDir "CARSPLAT\DATA"
$splatDetected = Test-Path -LiteralPath (Join-Path $splatData "RACES\CASTLE2.TXT") -PathType Leaf

$stateDir = Join-Path $GameDir ".dethrace-modernizer"
$backupDir = Join-Path $stateDir "backup"
$stageDir = Join-Path $stateDir "staging"
$transactionPath = Join-Path $stateDir "transaction.journal"
New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
New-Item -ItemType Directory -Path $stageDir -Force | Out-Null

$mainStatus = "not-selected"
$splatStatus = "not-selected"
$damageHudStatus = "not-selected"
$mainFinalRoot = $mainData
$mainStage = Join-Path $stageDir "MAIN"
$splatStage = Join-Path $stageDir "SPLAT"

if ($InstallGerman) {
    Write-Host ""
    Write-Host "German main-game source detected: $sourceRoot"
    Write-Host "Building the validated German main-game set..."
    Build-MainStage $sourceRoot $mainStage $mainManifest
    if (-not (Test-TargetSet $mainStage $mainManifest)) {
        throw "Main-game staging could not be fully verified."
    }
    $mainFinalRoot = $mainStage
    $mainStatus = "generated"

    if ($splatDetected) {
        Write-Host ""
        Write-Host "Original Splat Pack source detected: $splatSourceRoot"
        Write-Host "Building the validated German Splat Pack set..."
        Build-SplatStage $mainFinalRoot $splatSourceRoot $splatStage $splatManifest
        if (-not (Test-TargetSet $splatStage $splatManifest)) {
            throw "Splat Pack staging could not be fully verified."
        }
        $splatStatus = "generated"
    }
    else {
        $splatStatus = "not-detected"
    }
}

$payload = @(
    "Uninstall-Modernizer.ps1",
    "Uninstall-Modernizer.cmd",
    "Runtime4x3\dethrace-4x3-v0.10.1.exe",
    "Runtime4x3\SDL.dll",
    "Runtime4x3\SDL2.dll",
    "Runtime4x3\SDL3.dll",
    "Start-Carmageddon.cmd"
)
if ($splatDetected) { $payload += "Start-CARSPLAT.cmd" }

if ($Install16x9) {
    $payload += @(
        "dethrace-16x9-v1.5.exe",
        "SDL.dll",
        "SDL2.dll",
        "SDL3.dll",
        "Start-Carmageddon-16x9.cmd"
    )
    if ($splatDetected) { $payload += "Start-CARSPLAT-16x9.cmd" }
}
if ($InstallXInput) {
    # 4:3 + XInput is always available for users who prefer the original aspect ratio.
    $payload += @("Start-Carmageddon-XInput.cmd", "Controller\Carmageddon-XInput-Native.ps1")
    if ($splatDetected) {
        $payload += @("Start-CARSPLAT-XInput.cmd", "Controller\Carmageddon-SplatPack-XInput-Native.ps1")
    }

    # When widescreen is selected, add the native-analog 16:9 XInput launchers as well.
    if ($Install16x9) {
        $payload += @("Start-Carmageddon-16x9-XInput.cmd", "Controller\Carmageddon-XInput.ps1")
        if ($splatDetected) {
            $payload += @("Start-CARSPLAT-16x9-XInput.cmd", "Controller\Carmageddon-SplatPack-XInput.ps1")
        }
    }
}

$records = New-Object System.Collections.Generic.List[object]
$journalEncoding = New-Object System.Text.UTF8Encoding($false)

function Append-TransactionRecord($Record) {
    $json = $Record | ConvertTo-Json -Compress
    [System.IO.File]::AppendAllText($transactionPath, $json + [Environment]::NewLine, $journalEncoding)
}

function Install-One([string]$Source, [string]$RelativePath) {
    $destination = Join-Path $GameDir $RelativePath
    $destinationDir = Split-Path -Parent $destination
    New-Item -ItemType Directory -Path $destinationDir -Force | Out-Null

    $existed = Test-Path -LiteralPath $destination -PathType Leaf
    $backupRelative = $null
    $backupPath = $null
    if ($existed) {
        $backupRelative = $RelativePath
        $backupPath = Join-Path $backupDir $backupRelative
        New-Item -ItemType Directory -Path (Split-Path -Parent $backupPath) -Force | Out-Null
    }

    $record = [pscustomobject]@{
        path = $RelativePath
        existedBefore = [bool]$existed
        backupPath = $backupRelative
    }
    [void]$records.Add($record)
    Append-TransactionRecord $record

    if ($existed) {
        # The backup lives on the same target volume. Moving the original file
        # is effectively instantaneous and avoids copying the whole game twice.
        Move-Item -LiteralPath $destination -Destination $backupPath -Force
    }

    Copy-Item -LiteralPath $Source -Destination $destination -Force
}


function Find-ByteSequencePositions([byte[]]$Data, [byte[]]$Needle) {
    $positions = New-Object System.Collections.Generic.List[int]
    if ($Needle.Length -eq 0 -or $Data.Length -lt $Needle.Length) {
        return $positions
    }

    for ($i = 0; $i -le ($Data.Length - $Needle.Length); $i++) {
        $match = $true
        for ($j = 0; $j -lt $Needle.Length; $j++) {
            if ($Data[$i + $j] -ne $Needle[$j]) {
                $match = $false
                break
            }
        }
        if ($match) {
            [void]$positions.Add($i)
        }
    }
    return $positions
}

function Replace-ByteSequenceExactlyOnce([byte[]]$Data, [byte[]]$OldBytes, [byte[]]$NewBytes, [string]$Label) {
    $positions = @(Find-ByteSequencePositions $Data $OldBytes)
    if ($positions.Count -ne 1) {
        throw "HUD source patch '$Label' expected exactly one match, found $($positions.Count)."
    }

    $index = $positions[0]
    $newLength = $Data.Length - $OldBytes.Length + $NewBytes.Length
    $result = New-Object byte[] $newLength

    if ($index -gt 0) {
        [System.Buffer]::BlockCopy($Data, 0, $result, 0, $index)
    }

    [System.Buffer]::BlockCopy($NewBytes, 0, $result, $index, $NewBytes.Length)

    $sourceTail = $index + $OldBytes.Length
    $destTail = $index + $NewBytes.Length
    $tailLength = $Data.Length - $sourceTail
    if ($tailLength -gt 0) {
        [System.Buffer]::BlockCopy($Data, $sourceTail, $result, $destTail, $tailLength)
    }

    return $result
}

function Install-DamageHudRightEdge {
    $itemsPath = Join-Path $DamageHudRoot "patch-manifest.json"
    if (-not (Test-Path -LiteralPath $itemsPath -PathType Leaf)) {
        throw "Damage HUD source-patch manifest missing: $itemsPath"
    }

    $manifest = Get-Content -LiteralPath $itemsPath -Raw | ConvertFrom-Json

    # PowerShell 5.1: explicitly expand the JSON array.
    $items = New-Object System.Collections.Generic.List[object]
    foreach ($parsedItem in $manifest.files) {
        [void]$items.Add($parsedItem)
    }

    $clean = 0
    $already = 0

    # Preflight: every applicable file must be an exact supported clean source
    # or the exact already-patched target.
    foreach ($item in $items) {
        $relative = [string]$item.relative_path
        if ($relative.StartsWith("CARSPLAT\", [System.StringComparison]::OrdinalIgnoreCase) -and -not $splatDetected) {
            continue
        }

        $destination = Join-Path $GameDir $relative
        if (-not (Test-Path -LiteralPath $destination -PathType Leaf)) {
            throw "Damage HUD source file missing: $relative"
        }

        $current = Get-Sha256 $destination
        $cleanHash = ([string]$item.clean_sha256).ToLowerInvariant()
        $patchedHash = ([string]$item.patched_sha256).ToLowerInvariant()

        if ($current -eq $cleanHash) {
            $clean++
        }
        elseif ($current -eq $patchedHash) {
            $already++
        }
        else {
            throw "Unsupported Damage HUD source revision: $relative`nSHA-256: $current"
        }
    }

    $changed = 0
    foreach ($item in $items) {
        $relative = [string]$item.relative_path
        if ($relative.StartsWith("CARSPLAT\", [System.StringComparison]::OrdinalIgnoreCase) -and -not $splatDetected) {
            continue
        }

        $destination = Join-Path $GameDir $relative
        $current = Get-Sha256 $destination
        $patchedHash = ([string]$item.patched_sha256).ToLowerInvariant()
        if ($current -eq $patchedHash) {
            continue
        }

        [byte[]]$data = [System.IO.File]::ReadAllBytes($destination)

        $patchIndex = 0
        foreach ($patch in $item.patches) {
            $patchIndex++
            [byte[]]$oldBytes = [Convert]::FromBase64String([string]$patch.old_b64)
            [byte[]]$newBytes = [Convert]::FromBase64String([string]$patch.new_b64)
            $label = "$relative / patch $patchIndex"
            [byte[]]$data = Replace-ByteSequenceExactlyOnce $data $oldBytes $newBytes $label
        }

        $tempPath = Join-Path $stageDir ("DamageHUD\" + $relative)
        New-Item -ItemType Directory -Path (Split-Path -Parent $tempPath) -Force | Out-Null
        [System.IO.File]::WriteAllBytes($tempPath, $data)

        $tempHash = Get-Sha256 $tempPath
        if ($tempHash -ne $patchedHash) {
            throw "Damage HUD source patch produced an unexpected target hash: $relative`nExpected: $patchedHash`nActual:   $tempHash"
        }

        Install-One $tempPath $relative

        if ((Get-Sha256 $destination) -ne $patchedHash) {
            throw "Damage HUD verification failed after installation: $relative"
        }
        $changed++
    }

    return [pscustomobject]@{
        changed = $changed
        alreadyPatched = $already
    }
}

try {
    foreach ($relative in $payload) {
        $source = Join-Path $PackageRoot $relative
        if (-not (Test-Path -LiteralPath $source -PathType Leaf)) {
            throw "Package file missing: $relative"
        }
        Install-One $source $relative
    }

    if ($mainStatus -eq "generated") {
        foreach ($entry in @($mainManifest.files)) {
            $relative = "DATA\" + ([string]$entry.path)
            $source = Join-Path $mainStage ([string]$entry.path)
            # Target-first installation starts from the validated original copy.
            # Do not hash every English destination just to prove it is not
            # already the German target; replace it directly from verified stage.
            Install-One $source $relative
        }
    }

    if ($splatStatus -eq "generated") {
        foreach ($entry in @($splatManifest.files)) {
            $relative = "CARSPLAT\DATA\" + ([string]$entry.path)
            $source = Join-Path $splatStage ([string]$entry.path)
            Install-One $source $relative
        }
    }

    if ($InstallGerman) {
        # Stage outputs were already SHA-256 verified. After the local copy we
        # only need a fast structural check here; re-hashing the complete set
        # would read the same ~GB of data yet again.
        foreach ($entry in @($mainManifest.files)) {
            $installed = Join-Path $mainData ([string]$entry.path)
            if (-not (Test-Path -LiteralPath $installed -PathType Leaf) -or
                (Get-Item -LiteralPath $installed).Length -ne [int64]$entry.target_size) {
                throw "Installed German main-game file is missing or has the wrong size: $($entry.path)"
            }
        }
        if ($splatDetected) {
            foreach ($entry in @($splatManifest.files)) {
                $installed = Join-Path $splatData ([string]$entry.path)
                if (-not (Test-Path -LiteralPath $installed -PathType Leaf) -or
                    (Get-Item -LiteralPath $installed).Length -ne [int64]$entry.target_size) {
                    throw "Installed German Splat Pack file is missing or has the wrong size: $($entry.path)"
                }
            }
        }
    }

    if ($Install16x9) {
        Write-Host ""
        Write-Host "Applying the source-verified 16:9 Damage HUD right-edge correction..."
        $damageResult = Install-DamageHudRightEdge
        $damageHudStatus = "patched"
        Write-Host ("  Damage HUD files changed: " + $damageResult.changed)
        Write-Host ("  Already correct: " + $damageResult.alreadyPatched)
    }

    $exeHash = $null
    if ($Install16x9) {
        $exeHash = Get-Sha256 (Join-Path $GameDir "dethrace-16x9-v1.5.exe")
    }

    [object[]]$recordArray = @($records | ForEach-Object { $_ })

    $manifest = [pscustomobject]@{
        modernizerVersion = $ModernizerVersion
        engineVersion = $EngineVersion
        installedAt = (Get-Date).ToString("o")
        gameDir = $GameDir
        targetFirst = $true
        originalSource = $OriginalSource
        splatPackDetected = [bool]$splatDetected
        components = [pscustomobject]@{
            baseDethrace4x3 = $true
            widescreen16x9 = [bool]$Install16x9
            xinput = [bool]$InstallXInput
            germanUncut = [bool]$InstallGerman
        }
        germanMainStatus = $mainStatus
        germanSplatStatus = $splatStatus
        damageHudStatus = $damageHudStatus
        executableSha256 = $exeHash
        files = $recordArray
    }

    $manifest | ConvertTo-Json -Depth 8 |
        Set-Content -LiteralPath (Join-Path $stateDir "install.json") -Encoding UTF8

    Remove-Item -LiteralPath $transactionPath -Force -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath $stageDir -Recurse -Force -ErrorAction SilentlyContinue
}
catch {
    $originalError = $_
    Write-Host ""
    Write-Host "Installation failed. Rolling back Modernizer changes." -ForegroundColor Red
    Write-Host ("Cause: " + $originalError.Exception.Message) -ForegroundColor Red

    try {
        [object[]]$rollbackRecords = @($records | ForEach-Object { $_ })
        [array]::Reverse($rollbackRecords)
        foreach ($record in $rollbackRecords) {
            $destination = Join-Path $GameDir ([string]$record.path)
            if ([bool]$record.existedBefore -and $record.backupPath) {
                $backupPath = Join-Path $backupDir ([string]$record.backupPath)
                if (Test-Path -LiteralPath $backupPath -PathType Leaf) {
                    New-Item -ItemType Directory -Path (Split-Path -Parent $destination) -Force | Out-Null
                    if (Test-Path -LiteralPath $destination -PathType Leaf) {
                        Remove-Item -LiteralPath $destination -Force
                    }
                    Move-Item -LiteralPath $backupPath -Destination $destination -Force
                }
            }
            elseif (Test-Path -LiteralPath $destination -PathType Leaf) {
                Remove-Item -LiteralPath $destination -Force
            }
        }
        Remove-Item -LiteralPath $stateDir -Recurse -Force -ErrorAction SilentlyContinue
        Write-Host "Modernizer changes were rolled back." -ForegroundColor Yellow
        Write-Host "The original version previously copied into the target remains in place."
    }
    catch {
        Write-Host ("Additional rollback error: " + $_.Exception.Message) -ForegroundColor Red
    }
    exit 1
}

Write-Host ""
Write-Host "Carmageddon Dethrace Modernizer was created in the target directory." -ForegroundColor Green
Write-Host "Target: $GameDir"
Write-Host "Original source: untouched"
if ($InstallGerman) {
    Write-Host "German source: untouched"
}
Write-Host ""
Write-Host "Base Dethrace 4:3 runtime: installed"
Write-Host ("16:9 source port: " + $(if ($Install16x9) { "installed" } else { "not selected" }))
Write-Host ("XInput: " + $(if ($InstallXInput) { "installed" } else { "not selected" }))
if ($Install16x9) { Write-Host "Damage HUD right-edge correction: installed" }
if ($InstallGerman) {
    Write-Host ("German/Uncut main game: " + $(if ($mainStatus -eq "already-final") { "already correct" } else { "built and verified" }))
    if ($splatDetected) {
        Write-Host ("German Splat Pack: " + $(if ($splatStatus -eq "already-final") { "already correct" } else { "built and verified" }))
    }
}
else {
    Write-Host "German/Uncut: not selected"
}
Write-Host ""
Write-Host "Installed launchers:"
Write-Host "  Start-Carmageddon.cmd"
if ($splatDetected) { Write-Host "  Start-CARSPLAT.cmd" }
if ($Install16x9) {
    Write-Host "  Start-Carmageddon-16x9.cmd"
    if ($splatDetected) { Write-Host "  Start-CARSPLAT-16x9.cmd" }
}
if ($InstallXInput) {
    if ($Install16x9) {
        Write-Host "  Start-Carmageddon-16x9-XInput.cmd"
        if ($splatDetected) { Write-Host "  Start-CARSPLAT-16x9-XInput.cmd" }
    }
    else {
        Write-Host "  Start-Carmageddon-XInput.cmd"
        if ($splatDetected) { Write-Host "  Start-CARSPLAT-XInput.cmd" }
    }
}
Write-Host ""
Write-Host "Uninstall-Modernizer.cmd removes the generated target installation after confirmation."
Write-Host ""