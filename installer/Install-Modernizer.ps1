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

$ModernizerVersion = "0.9.0-rc9-exodos-wav-init-fix"
$EngineVersion = "RC1-goldstandard + fullscreen cockpit + right-edge mirror + WAV CD-audio fallback + 4x3 parity"
$GoldWideSha256 = "1df66ba28020f08635773a992e1254ce1b746a11f7a4d77598aff236d7f8ddf6"
$Gold4x3Sha256 = "80dd90f4a74b6caaae19fb336cbd86e5ce0dc3058c509d0da691ecf1511dc9f7"
$PackageRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$MainDeltaRoot = Join-Path $PackageRoot "German\Main"
$SplatDeltaRoot = Join-Path $PackageRoot "German\Splat"
$DamageHudRoot = Join-Path $PackageRoot "DamageHUD"
$script:InstallTransactionActive = $false

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
        if ($script:InstallTransactionActive) { throw "Folder selection cancelled." }
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
                    # If the journal was written immediately before the move and
                    # the process died first, the original destination is intact.
                }
                elseif (Test-Path -LiteralPath $destination -PathType Leaf) {
                    Remove-Item -LiteralPath $destination -Force
                }
            }
            Remove-Item -LiteralPath $StateDir -Recurse -Force
            Write-Host "Previous state restored from the fast transaction journal." -ForegroundColor Green
            return
        }
        catch {
            Write-Host ("Transaction journal recovery failed: " + $_.Exception.Message) -ForegroundColor Red
            throw
        }
    }

    # Compatibility with earlier test builds.
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
                    Copy-Item -LiteralPath $backupPath -Destination $destination -Force
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

    $sourceFull = [System.IO.Path]::GetFullPath($SourceRoot).TrimEnd([char]92)
    $files = @(
        Get-ChildItem -LiteralPath $sourceFull -File -Recurse -Force |
        Where-Object {
            $relative = $_.FullName.Substring($sourceFull.Length).TrimStart([char]92)
            $first = ($relative -split '[\\/]', 2)[0]
            $first -ine ".dethrace-modernizer" -and $first -ine ".modernizer"
        }
    )

    [int64]$totalBytes = 0
    foreach ($file in $files) { $totalBytes += [int64]$file.Length }

    $totalFiles = $files.Count
    $totalMiB = if ($totalBytes -gt 0) { $totalBytes / 1MB } else { 0 }
    Write-Host ("  {0:N0} files, {1:N1} MB total." -f $totalFiles, $totalMiB)

    if ($totalFiles -eq 0) {
        Write-Host "  Nothing to copy."
        return
    }

    $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
    [int64]$copiedBytes = 0
    $copiedFiles = 0
    $lastConsoleUpdate = [TimeSpan]::Zero
    $buffer = New-Object byte[] (4MB)

    foreach ($file in $files) {
        $relative = $file.FullName.Substring($sourceFull.Length).TrimStart([char]92)
        $destination = Join-Path $DestinationRoot $relative
        $destinationParent = Split-Path -Parent $destination
        New-Item -ItemType Directory -Path $destinationParent -Force | Out-Null

        $input = [System.IO.File]::Open($file.FullName, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::Read)
        $output = [System.IO.File]::Open($destination, [System.IO.FileMode]::Create, [System.IO.FileAccess]::Write, [System.IO.FileShare]::None)
        try {
            while (($read = $input.Read($buffer, 0, $buffer.Length)) -gt 0) {
                $output.Write($buffer, 0, $read)
                $copiedBytes += $read

                $percent = if ($totalBytes -gt 0) { [Math]::Min(100, [Math]::Floor(($copiedBytes * 100.0) / $totalBytes)) } else { 0 }
                $elapsed = $stopwatch.Elapsed
                $speed = if ($elapsed.TotalSeconds -gt 0.25) { $copiedBytes / $elapsed.TotalSeconds } else { 0 }
                $remaining = [Math]::Max(0, $totalBytes - $copiedBytes)
                $eta = if ($speed -gt 0) { [TimeSpan]::FromSeconds($remaining / $speed) } else { [TimeSpan]::Zero }
                $status = ("{0,3}% | {1}/{2} files | {3:N1}/{4:N1} MB | elapsed {5:hh\:mm\:ss} | ETA {6:hh\:mm\:ss}" -f $percent, ($copiedFiles + 1), $totalFiles, ($copiedBytes / 1MB), $totalMiB, $elapsed, $eta)

                Write-Progress -Activity ("Copying " + $Label) -Status $status -PercentComplete $percent

                if (($elapsed - $lastConsoleUpdate).TotalSeconds -ge 3) {
                    Write-Host ("  " + $status)
                    $lastConsoleUpdate = $elapsed
                }
            }
        }
        finally {
            $output.Dispose()
            $input.Dispose()
        }

        try { [System.IO.File]::SetLastWriteTimeUtc($destination, $file.LastWriteTimeUtc) } catch {}
        try { [System.IO.File]::SetAttributes($destination, $file.Attributes) } catch {}
        $copiedFiles++
    }

    $stopwatch.Stop()
    Write-Progress -Activity ("Copying " + $Label) -Completed
    Write-Host ("  Done: {0:N0}/{0:N0} files, {1:N1} MB in {2:hh\:mm\:ss}." -f $totalFiles, $totalMiB, $stopwatch.Elapsed) -ForegroundColor Green
}

function Find-CutsceneSource([string[]]$Hints, [bool]$SplatPack = $false) {
    foreach ($hint in @($Hints)) {
        if ([string]::IsNullOrWhiteSpace($hint)) { continue }
        $root = Normalize-InputPath $hint
        if ($null -eq $root -or -not (Test-Path -LiteralPath $root -PathType Container)) { continue }

        if ($SplatPack) {
            $candidates = @(
                $root,
                (Join-Path $root "CUTSCENE"),
                (Join-Path $root "DATA\CUTSCENE"),
                (Join-Path $root "CARSPLAT\DATA\CUTSCENE")
            )
        }
        else {
            $candidates = @(
                $root,
                (Join-Path $root "CUTSCENE"),
                (Join-Path $root "DATA\CUTSCENE"),
                (Join-Path $root "CARMA\DATA\CUTSCENE")
            )
        }

        foreach ($candidate in $candidates) {
            if ((Test-Path -LiteralPath $candidate -PathType Container) -and
                @(Get-ChildItem -LiteralPath $candidate -Filter *.SMK -File -ErrorAction SilentlyContinue).Count -gt 0) {
                return [System.IO.Path]::GetFullPath($candidate)
            }
        }
    }
    return $null
}

function Find-FirstExistingFile([string[]]$Candidates) {
    foreach ($candidate in @($Candidates)) {
        if ([string]::IsNullOrWhiteSpace($candidate)) { continue }
        if (Test-Path -LiteralPath $candidate -PathType Leaf) {
            return [System.IO.Path]::GetFullPath($candidate)
        }
    }
    return $null
}

function Read-IsoBlock {
    param(
        [System.IO.FileStream]$Stream,
        [uint32]$Lba,
        [int]$SectorSize = 2352,
        [int]$UserDataOffset = 16,
        [uint32]$TrackStartSector = 0
    )

    $buffer = New-Object byte[] 2048
    $physicalSector = [uint64]$TrackStartSector + [uint64]$Lba
    $Stream.Position = ([int64]$physicalSector * [int64]$SectorSize) + [int64]$UserDataOffset
    $read = $Stream.Read($buffer, 0, 2048)
    if ($read -ne 2048) {
        throw "ISO sector $Lba could not be read completely."
    }
    return $buffer
}

function Read-IsoExtent {
    param(
        [System.IO.FileStream]$Stream,
        [uint32]$Lba,
        [uint32]$Size,
        [int]$SectorSize = 2352,
        [int]$UserDataOffset = 16,
        [uint32]$TrackStartSector = 0
    )

    $result = New-Object byte[] $Size
    $written = 0
    $block = 0
    while ($written -lt $Size) {
        $data = Read-IsoBlock -Stream $Stream -Lba ($Lba + $block) `
            -SectorSize $SectorSize -UserDataOffset $UserDataOffset -TrackStartSector $TrackStartSector
        $count = [Math]::Min(2048, $Size - $written)
        [Array]::Copy($data, 0, $result, $written, $count)
        $written += $count
        $block++
    }
    return $result
}

function Get-IsoDirectoryEntries {
    param(
        [System.IO.FileStream]$Stream,
        [uint32]$Lba,
        [uint32]$Size,
        [int]$SectorSize = 2352,
        [int]$UserDataOffset = 16,
        [uint32]$TrackStartSector = 0
    )

    $data = Read-IsoExtent -Stream $Stream -Lba $Lba -Size $Size `
        -SectorSize $SectorSize -UserDataOffset $UserDataOffset -TrackStartSector $TrackStartSector
    $offset = 0
    $entries = @()

    while ($offset -lt $data.Length) {
        $recordLength = $data[$offset]
        if ($recordLength -eq 0) {
            $offset = ([Math]::Floor($offset / 2048) + 1) * 2048
            continue
        }
        if (($offset + $recordLength) -gt $data.Length) { break }

        $extent = [BitConverter]::ToUInt32($data, $offset + 2)
        $length = [BitConverter]::ToUInt32($data, $offset + 10)
        $flags = $data[$offset + 25]
        $nameLength = $data[$offset + 32]
        $nameBytes = New-Object byte[] $nameLength
        [Array]::Copy($data, $offset + 33, $nameBytes, 0, $nameLength)

        if ($nameLength -eq 1 -and $nameBytes[0] -eq 0) {
            $name = "."
        }
        elseif ($nameLength -eq 1 -and $nameBytes[0] -eq 1) {
            $name = ".."
        }
        else {
            $name = [System.Text.Encoding]::ASCII.GetString($nameBytes)
            $name = $name -replace ';1$', ''
        }

        $entries += [pscustomobject]@{
            Name = $name
            LBA = $extent
            Size = $length
            IsDirectory = (($flags -band 2) -ne 0)
        }
        $offset += $recordLength
    }
    return $entries
}

function Export-IsoFile {
    param(
        [System.IO.FileStream]$Stream,
        $Entry,
        [string]$Destination,
        [int]$SectorSize = 2352,
        [int]$UserDataOffset = 16,
        [uint32]$TrackStartSector = 0
    )

    New-Item -ItemType Directory -Path (Split-Path -Parent $Destination) -Force | Out-Null
    $out = [System.IO.File]::Create($Destination)
    try {
        [uint32]$remaining = [uint32]$Entry.Size
        $block = 0
        while ($remaining -gt 0) {
            $data = Read-IsoBlock -Stream $Stream -Lba ([uint32]($Entry.LBA + $block)) `
                -SectorSize $SectorSize -UserDataOffset $UserDataOffset -TrackStartSector $TrackStartSector
            $count = [Math]::Min(2048, $remaining)
            $out.Write($data, 0, $count)
            $remaining = [uint32]($remaining - $count)
            $block++
        }
    }
    finally {
        $out.Dispose()
    }
}

function Convert-CueTimeToSector([string]$Timestamp) {
    if ($Timestamp -notmatch '^(\d+):(\d+):(\d+)$') {
        throw "Unsupported CUE timestamp: $Timestamp"
    }

    $minutes = [int]$Matches[1]
    $seconds = [int]$Matches[2]
    $frames = [int]$Matches[3]
    return [uint32](($minutes * 60 * 75) + ($seconds * 75) + $frames)
}

function Get-CueDataTrackInfo([string]$CuePath) {
    $cueFull = [System.IO.Path]::GetFullPath($CuePath)
    $cueDir = Split-Path -Parent $cueFull
    $currentFile = $null
    $currentTrackType = $null
    $selectedFile = $null
    $selectedType = $null
    $selectedIndex = $null

    foreach ($rawLine in @(Get-Content -LiteralPath $cueFull -ErrorAction Stop)) {
        $line = $rawLine.Trim()
        if ([string]::IsNullOrWhiteSpace($line) -or $line.StartsWith("REM ", [System.StringComparison]::OrdinalIgnoreCase)) {
            continue
        }

        if ($line -match '^(?i)FILE\s+"([^"]+)"\s+\S+') {
            $currentFile = $Matches[1]
            continue
        }
        if ($line -match '^(?i)FILE\s+(\S+)\s+\S+') {
            $currentFile = $Matches[1]
            continue
        }

        if ($line -match '^(?i)TRACK\s+\d+\s+(\S+)') {
            $currentTrackType = $Matches[1].ToUpperInvariant()
            continue
        }

        if ($line -match '^(?i)INDEX\s+01\s+(\d+:\d+:\d+)$') {
            if ($null -eq $selectedFile -and
                $currentTrackType -in @("MODE1/2352", "MODE1/2048", "MODE2/2352", "MODE2/2336")) {
                $selectedFile = $currentFile
                $selectedType = $currentTrackType
                $selectedIndex = $Matches[1]
            }
        }
    }

    if ([string]::IsNullOrWhiteSpace($selectedFile) -or
        [string]::IsNullOrWhiteSpace($selectedType) -or
        [string]::IsNullOrWhiteSpace($selectedIndex)) {
        throw "No supported ISO data track was found in CUE: $cueFull"
    }

    $imagePath = Join-Path $cueDir $selectedFile
    if (-not (Test-Path -LiteralPath $imagePath -PathType Leaf)) {
        throw "CUE data file is missing: $imagePath"
    }

    switch ($selectedType) {
        "MODE1/2352" {
            $sectorSize = 2352
            $userDataOffset = 16
        }
        "MODE1/2048" {
            $sectorSize = 2048
            $userDataOffset = 0
        }
        "MODE2/2352" {
            # Common CD-ROM XA Form 1 layout: 12 sync + 4 header + 8 subheader.
            $sectorSize = 2352
            $userDataOffset = 24
        }
        "MODE2/2336" {
            # 2336-byte image omits the 16-byte raw sync/header.
            $sectorSize = 2336
            $userDataOffset = 8
        }
        default {
            throw "Unsupported CUE data-track mode: $selectedType"
        }
    }

    return [pscustomobject]@{
        CuePath = $cueFull
        ImagePath = [System.IO.Path]::GetFullPath($imagePath)
        TrackType = $selectedType
        TrackStartSector = (Convert-CueTimeToSector $selectedIndex)
        SectorSize = $sectorSize
        UserDataOffset = $userDataOffset
    }
}


function Get-CueTrackTable([string]$CuePath) {
    $cueFull = [System.IO.Path]::GetFullPath($CuePath)
    $cueDir = Split-Path -Parent $cueFull
    $tracks = New-Object System.Collections.Generic.List[object]
    $currentFile = $null
    $currentTrack = $null

    foreach ($rawLine in @(Get-Content -LiteralPath $cueFull -ErrorAction Stop)) {
        $line = $rawLine.Trim()
        if ([string]::IsNullOrWhiteSpace($line) -or
            $line.StartsWith("REM ", [System.StringComparison]::OrdinalIgnoreCase)) {
            continue
        }

        if ($line -match '^(?i)FILE\s+"([^"]+)"\s+\S+') {
            $currentFile = $Matches[1]
            continue
        }
        if ($line -match '^(?i)FILE\s+(\S+)\s+\S+') {
            $currentFile = $Matches[1]
            continue
        }

        if ($line -match '^(?i)TRACK\s+(\d+)\s+(\S+)') {
            $currentTrack = [pscustomobject]@{
                Number = [int]$Matches[1]
                Type = $Matches[2].ToUpperInvariant()
                File = $currentFile
                Index01 = $null
            }
            [void]$tracks.Add($currentTrack)
            continue
        }

        if ($null -ne $currentTrack -and $line -match '^(?i)INDEX\s+01\s+(\d+:\d+:\d+)$') {
            $currentTrack.Index01 = [uint32](Convert-CueTimeToSector $Matches[1])
        }
    }

    $result = New-Object System.Collections.Generic.List[object]
    foreach ($track in $tracks) {
        if ([string]::IsNullOrWhiteSpace([string]$track.File) -or $null -eq $track.Index01) {
            continue
        }

        $imagePath = Join-Path $cueDir ([string]$track.File)
        if (-not (Test-Path -LiteralPath $imagePath -PathType Leaf)) {
            throw "CUE track file is missing: $imagePath"
        }

        [void]$result.Add([pscustomobject]@{
            Number = [int]$track.Number
            Type = [string]$track.Type
            ImagePath = [System.IO.Path]::GetFullPath($imagePath)
            Index01 = [uint32]$track.Index01
        })
    }

    return @($result | Sort-Object Number)
}

function Test-CddaNeedsByteSwap {
    param(
        [System.IO.FileStream]$Stream,
        [uint32]$StartSector
    )

    $sampleBytes = 2352 * 8
    $remaining = $Stream.Length - ([int64]$StartSector * 2352)
    if ($remaining -le 0) { return $false }
    if ($remaining -lt $sampleBytes) { $sampleBytes = [int]$remaining }
    $sampleBytes -= ($sampleBytes % 4)
    if ($sampleBytes -lt 8) { return $false }

    $buffer = New-Object byte[] $sampleBytes
    $Stream.Position = [int64]$StartSector * 2352
    $read = $Stream.Read($buffer, 0, $buffer.Length)
    $read -= ($read % 4)
    if ($read -lt 8) { return $false }

    [double]$littleScore = 0
    [double]$bigScore = 0
    $havePrev = $false
    [int]$prevLL = 0
    [int]$prevLR = 0
    [int]$prevBL = 0
    [int]$prevBR = 0

    for ($i = 0; $i -lt $read; $i += 4) {
        [int]$uLL = ([int]$buffer[$i]) -bor (([int]$buffer[$i + 1]) -shl 8)
        [int]$uLR = ([int]$buffer[$i + 2]) -bor (([int]$buffer[$i + 3]) -shl 8)
        [int]$uBL = ([int]$buffer[$i + 1]) -bor (([int]$buffer[$i]) -shl 8)
        [int]$uBR = ([int]$buffer[$i + 3]) -bor (([int]$buffer[$i + 2]) -shl 8)
        [int]$ll = $(if ($uLL -ge 32768) { $uLL - 65536 } else { $uLL })
        [int]$lr = $(if ($uLR -ge 32768) { $uLR - 65536 } else { $uLR })
        [int]$bl = $(if ($uBL -ge 32768) { $uBL - 65536 } else { $uBL })
        [int]$br = $(if ($uBR -ge 32768) { $uBR - 65536 } else { $uBR })

        if ($havePrev) {
            $littleScore += [Math]::Abs($ll - $prevLL) + [Math]::Abs($lr - $prevLR)
            $bigScore += [Math]::Abs($bl - $prevBL) + [Math]::Abs($br - $prevBR)
        }

        $prevLL = $ll
        $prevLR = $lr
        $prevBL = $bl
        $prevBR = $br
        $havePrev = $true
    }

    # Real music is normally much smoother sample-to-sample than byte-swapped
    # PCM. If the scores are too close (silence/degenerate sample), keep bytes
    # unchanged rather than guessing.
    if ($bigScore -gt 0 -and $bigScore -lt ($littleScore * 0.80)) {
        return $true
    }
    return $false
}

function Write-CddaTrackAsWav {
    param(
        [string]$ImagePath,
        [uint32]$StartSector,
        [uint32]$EndSector,
        [string]$Destination
    )

    if ($EndSector -le $StartSector) {
        throw "Invalid CD-audio sector range: $StartSector .. $EndSector"
    }

    [uint64]$dataLength64 = ([uint64]$EndSector - [uint64]$StartSector) * 2352
    if ($dataLength64 -gt [uint32]::MaxValue) {
        throw "CD-audio track is too large for a WAV file."
    }
    [uint32]$dataLength = [uint32]$dataLength64

    New-Item -ItemType Directory -Path (Split-Path -Parent $Destination) -Force | Out-Null

    $input = [System.IO.File]::OpenRead($ImagePath)
    try {
        $swap = Test-CddaNeedsByteSwap -Stream $input -StartSector $StartSector
        $input.Position = [int64]$StartSector * 2352

        $output = [System.IO.File]::Create($Destination)
        try {
            $writer = New-Object System.IO.BinaryWriter($output, [System.Text.Encoding]::ASCII, $true)
            try {
                $writer.Write([System.Text.Encoding]::ASCII.GetBytes("RIFF"))
                $writer.Write([uint32](36 + $dataLength))
                $writer.Write([System.Text.Encoding]::ASCII.GetBytes("WAVE"))
                $writer.Write([System.Text.Encoding]::ASCII.GetBytes("fmt "))
                $writer.Write([uint32]16)
                $writer.Write([uint16]1)
                $writer.Write([uint16]2)
                $writer.Write([uint32]44100)
                $writer.Write([uint32]176400)
                $writer.Write([uint16]4)
                $writer.Write([uint16]16)
                $writer.Write([System.Text.Encoding]::ASCII.GetBytes("data"))
                $writer.Write([uint32]$dataLength)
            }
            finally {
                $writer.Dispose()
            }

            $buffer = New-Object byte[] (2352 * 32)
            [uint64]$remaining = $dataLength64
            while ($remaining -gt 0) {
                $want = [int][Math]::Min([uint64]$buffer.Length, $remaining)
                $read = $input.Read($buffer, 0, $want)
                if ($read -le 0) {
                    throw "Unexpected end of BIN while extracting CD audio."
                }

                if ($swap) {
                    for ($i = 0; $i + 1 -lt $read; $i += 2) {
                        $tmp = $buffer[$i]
                        $buffer[$i] = $buffer[$i + 1]
                        $buffer[$i + 1] = $tmp
                    }
                }

                $output.Write($buffer, 0, $read)
                $remaining -= [uint64]$read
            }
        }
        finally {
            $output.Dispose()
        }
    }
    finally {
        $input.Dispose()
    }
}

function Install-CueBinMusic {
    param(
        [string]$CuePath,
        [string]$RelativeDestination,
        [string]$Label,
        [string]$StageRoot
    )

    $tracks = @(Get-CueTrackTable $CuePath)
    $audioTracks = @($tracks | Where-Object { $_.Type -eq "AUDIO" })
    if ($audioTracks.Count -eq 0) {
        Write-Host "$Label music: no AUDIO tracks found in CUE." -ForegroundColor Yellow
        return 0
    }

    Write-Host ""
    Write-Host "$Label music: extracting $($audioTracks.Count) CD-audio tracks losslessly to WAV..." -ForegroundColor Cyan

    $labelFolder = $Label -replace '[^A-Za-z0-9_-]', '_'
    $tempRoot = Join-Path $StageRoot ("Music\" + $labelFolder)
    New-Item -ItemType Directory -Path $tempRoot -Force | Out-Null

    $installed = 0
    for ($i = 0; $i -lt $tracks.Count; $i++) {
        $track = $tracks[$i]
        if ($track.Type -ne "AUDIO") { continue }

        [uint32]$startSector = $track.Index01
        $sameFileNext = $null
        for ($j = $i + 1; $j -lt $tracks.Count; $j++) {
            if ($tracks[$j].ImagePath -ieq $track.ImagePath) {
                $sameFileNext = $tracks[$j]
                break
            }
        }

        if ($null -ne $sameFileNext) {
            [uint32]$endSector = $sameFileNext.Index01
        }
        else {
            $length = (Get-Item -LiteralPath $track.ImagePath).Length
            [uint32]$endSector = [uint32][Math]::Floor($length / 2352)
        }

        $fileName = "Track0$($track.Number).wav"
        $temp = Join-Path $tempRoot $fileName
        Write-Host "  Extracting track $($track.Number) -> $fileName"
        Write-CddaTrackAsWav -ImagePath $track.ImagePath -StartSector $startSector -EndSector $endSector -Destination $temp
        Install-One $temp (Join-Path $RelativeDestination $fileName)
        $installed++
    }

    Write-Host "$Label music: installed $installed lossless WAV tracks." -ForegroundColor Green
    return $installed
}

function Get-IsoCutsceneEntries {
    param(
        [System.IO.FileStream]$Stream,
        [int]$SectorSize,
        [int]$UserDataOffset,
        [uint32]$TrackStartSector
    )

    $pvd = Read-IsoBlock -Stream $Stream -Lba 16 `
        -SectorSize $SectorSize -UserDataOffset $UserDataOffset -TrackStartSector $TrackStartSector
    $signature = [System.Text.Encoding]::ASCII.GetString($pvd, 1, 5)
    if ($signature -ne "CD001") {
        throw "No supported ISO9660 filesystem was found in the selected data track."
    }

    $rootLba = [BitConverter]::ToUInt32($pvd, 158)
    $rootSize = [BitConverter]::ToUInt32($pvd, 166)
    $root = Get-IsoDirectoryEntries -Stream $Stream -Lba $rootLba -Size $rootSize `
        -SectorSize $SectorSize -UserDataOffset $UserDataOffset -TrackStartSector $TrackStartSector

    # Most Carmageddon CDs keep the movies in DATA\CUTSCENE. Some repacks may
    # expose CUTSCENE directly at disc root, so support both layouts.
    $cutsceneDir = $null
    $dataDir = $root | Where-Object { $_.IsDirectory -and $_.Name -ieq "DATA" } | Select-Object -First 1
    if ($null -ne $dataDir) {
        $dataEntries = Get-IsoDirectoryEntries -Stream $Stream -Lba $dataDir.LBA -Size $dataDir.Size `
            -SectorSize $SectorSize -UserDataOffset $UserDataOffset -TrackStartSector $TrackStartSector
        $cutsceneDir = $dataEntries | Where-Object { $_.IsDirectory -and $_.Name -ieq "CUTSCENE" } | Select-Object -First 1
    }

    if ($null -eq $cutsceneDir) {
        $cutsceneDir = $root | Where-Object { $_.IsDirectory -and $_.Name -ieq "CUTSCENE" } | Select-Object -First 1
    }

    if ($null -eq $cutsceneDir) {
        throw "CUTSCENE directory missing in the ISO9660 data track."
    }

    $movies = @(Get-IsoDirectoryEntries -Stream $Stream -Lba $cutsceneDir.LBA -Size $cutsceneDir.Size `
        -SectorSize $SectorSize -UserDataOffset $UserDataOffset -TrackStartSector $TrackStartSector |
        Where-Object { -not $_.IsDirectory -and $_.Name -like "*.SMK" } |
        Sort-Object Name)

    if ($movies.Count -eq 0) {
        throw "No SMK cutscenes were found in the ISO9660 data track."
    }

    return $movies
}

function Install-IsoCutscenes {
    param(
        [string]$ImagePath,
        [string]$RelativeDestination,
        [string]$Label,
        [string]$StageRoot,
        [int]$SectorSize = 2352,
        [int]$UserDataOffset = 16,
        [uint32]$TrackStartSector = 0,
        [string]$SourceDescription = "CD image"
    )

    Write-Host ""
    Write-Host "$Label cutscenes: extracting from $SourceDescription..." -ForegroundColor Cyan
    Write-Host "  $ImagePath"

    $fs = [System.IO.File]::OpenRead($ImagePath)
    try {
        $movies = @(Get-IsoCutsceneEntries -Stream $fs `
            -SectorSize $SectorSize -UserDataOffset $UserDataOffset -TrackStartSector $TrackStartSector)

        $labelFolder = $Label -replace '[^A-Za-z0-9_-]', '_'
        $tempRoot = Join-Path $StageRoot ("Cutscenes\" + $labelFolder)
        New-Item -ItemType Directory -Path $tempRoot -Force | Out-Null

        foreach ($movie in $movies) {
            Write-Host "  Extracting $($movie.Name)"
            $temp = Join-Path $tempRoot $movie.Name
            Export-IsoFile -Stream $fs -Entry $movie -Destination $temp `
                -SectorSize $SectorSize -UserDataOffset $UserDataOffset -TrackStartSector $TrackStartSector
            Install-One $temp (Join-Path $RelativeDestination $movie.Name)
        }

        Write-Host "$Label cutscenes: installed $($movies.Count) SMK files from $SourceDescription." -ForegroundColor Green
        return $movies.Count
    }
    finally {
        $fs.Dispose()
    }
}

function Install-GogCutscenes {
    param(
        [string]$ImagePath,
        [string]$RelativeDestination,
        [string]$Label,
        [string]$StageRoot
    )

    return Install-IsoCutscenes -ImagePath $ImagePath `
        -RelativeDestination $RelativeDestination -Label $Label -StageRoot $StageRoot `
        -SectorSize 2352 -UserDataOffset 16 -TrackStartSector 0 `
        -SourceDescription "GOG CD image"
}

function Install-CueBinCutscenes {
    param(
        [string]$CuePath,
        [string]$RelativeDestination,
        [string]$Label,
        [string]$StageRoot
    )

    $track = Get-CueDataTrackInfo $CuePath

    Write-Host ""
    Write-Host "$Label cutscene source detected:" -ForegroundColor Cyan
    Write-Host "  CUE:  $($track.CuePath)"
    Write-Host "  BIN:  $($track.ImagePath)"
    Write-Host "  Mode: $($track.TrackType), INDEX 01 sector $($track.TrackStartSector)"

    return Install-IsoCutscenes -ImagePath $track.ImagePath `
        -RelativeDestination $RelativeDestination -Label $Label -StageRoot $StageRoot `
        -SectorSize $track.SectorSize -UserDataOffset $track.UserDataOffset `
        -TrackStartSector $track.TrackStartSector -SourceDescription "CUE/BIN CD image"
}

function Import-LooseCutscenes {
    param(
        [string]$RelativeDestination,
        [string[]]$Hints,
        [bool]$SplatPack,
        [string]$Label
    )

    $destination = Join-Path $GameDir $RelativeDestination
    $already = @()
    if (Test-Path -LiteralPath $destination -PathType Container) {
        $already = @(Get-ChildItem -LiteralPath $destination -Filter *.SMK -File -ErrorAction SilentlyContinue)
    }
    if ($already.Count -gt 0) {
        Write-Host "$Label cutscenes: $($already.Count) SMK files already copied from the original source." -ForegroundColor Green
        return "source-copy"
    }

    $source = Find-CutsceneSource -Hints $Hints -SplatPack $SplatPack
    if ($null -eq $source) {
        Write-Host "$Label cutscenes: no loose SMK source found." -ForegroundColor Yellow
        return "not-found"
    }

    $movies = @(Get-ChildItem -LiteralPath $source -Filter *.SMK -File)
    foreach ($movie in $movies) {
        Install-One $movie.FullName (Join-Path $RelativeDestination $movie.Name)
    }
    Write-Host "$Label cutscenes: imported $($movies.Count) loose SMK files from $source" -ForegroundColor Green
    return "loose-files"
}


# ---------------------------------------------------------------------------
# User-facing launcher shortcuts live one level above the internal _Modernizer
# payload/game directory. This keeps normal users out of the technical folder.
# Windows filenames cannot contain ":", therefore 4x3 / 16x9 are used.
# ---------------------------------------------------------------------------

$ShortcutRoot = [System.IO.Path]::GetFullPath((Split-Path -Parent $PackageRoot))
$ModernizerShortcutNames = @(
    "Carmageddon - 4x3 - Keyboard + Mouse",
    "Carmageddon - 4x3 - XInput",
    "Carmageddon - 16x9 - Keyboard + Mouse",
    "Carmageddon - 16x9 - XInput",
    "Splat Pack - 4x3 - Keyboard + Mouse",
    "Splat Pack - 4x3 - XInput",
    "Splat Pack - 16x9 - Keyboard + Mouse",
    "Splat Pack - 16x9 - XInput",
    "Uninstall Carmageddon Dethrace Modernizer"
)

function Remove-ModernizerShortcuts {
    foreach ($name in $ModernizerShortcutNames) {
        $linkPath = Join-Path $ShortcutRoot ($name + ".lnk")
        Remove-Item -LiteralPath $linkPath -Force -ErrorAction SilentlyContinue
    }
}

function New-ModernizerShortcut {
    param(
        [object]$Shell,
        [string]$Name,
        [string]$TargetRelative,
        [string]$Description,
        [string]$IconRelative
    )

    $targetPath = Join-Path $GameDir $TargetRelative
    if (-not (Test-Path -LiteralPath $targetPath -PathType Leaf)) {
        return $null
    }

    $linkPath = Join-Path $ShortcutRoot ($Name + ".lnk")
    $shortcut = $Shell.CreateShortcut($linkPath)
    $shortcut.TargetPath = $targetPath
    $shortcut.WorkingDirectory = $GameDir
    $shortcut.Description = $Description

    if (-not [string]::IsNullOrWhiteSpace($IconRelative)) {
        $iconPath = Join-Path $GameDir $IconRelative
        if (Test-Path -LiteralPath $iconPath -PathType Leaf) {
            $shortcut.IconLocation = $iconPath + ",0"
        }
    }

    $shortcut.Save()
    return $Name
}

function Create-ModernizerShortcuts {
    $created = New-Object System.Collections.Generic.List[string]

    try {
        Remove-ModernizerShortcuts
        $shell = New-Object -ComObject WScript.Shell

        $name = New-ModernizerShortcut $shell `
            "Carmageddon - 4x3 - Keyboard + Mouse" `
            "Start-Carmageddon.cmd" `
            "Carmageddon 4:3 - Keyboard + Mouse Controls" `
            "Runtime4x3\dethrace-4x3-v0.10.1.exe"
        if ($null -ne $name) { [void]$created.Add($name) }

        if ($InstallXInput) {
            $name = New-ModernizerShortcut $shell `
                "Carmageddon - 4x3 - XInput" `
                "Start-Carmageddon-XInput.cmd" `
                "Carmageddon 4:3 - XInput Controls" `
                "Runtime4x3\dethrace-4x3-v0.10.1.exe"
            if ($null -ne $name) { [void]$created.Add($name) }
        }

        if ($Install16x9) {
            $name = New-ModernizerShortcut $shell `
                "Carmageddon - 16x9 - Keyboard + Mouse" `
                "Start-Carmageddon-16x9.cmd" `
                "Carmageddon 16:9 - Keyboard + Mouse Controls" `
                "dethrace-16x9-v1.5.exe"
            if ($null -ne $name) { [void]$created.Add($name) }

            if ($InstallXInput) {
                $name = New-ModernizerShortcut $shell `
                    "Carmageddon - 16x9 - XInput" `
                    "Start-Carmageddon-16x9-XInput.cmd" `
                    "Carmageddon 16:9 - XInput Controls" `
                    "dethrace-16x9-v1.5.exe"
                if ($null -ne $name) { [void]$created.Add($name) }
            }
        }

        if ($splatDetected) {
            $name = New-ModernizerShortcut $shell `
                "Splat Pack - 4x3 - Keyboard + Mouse" `
                "Start-CARSPLAT.cmd" `
                "Splat Pack 4:3 - Keyboard + Mouse Controls" `
                "Runtime4x3\dethrace-4x3-v0.10.1.exe"
            if ($null -ne $name) { [void]$created.Add($name) }

            if ($InstallXInput) {
                $name = New-ModernizerShortcut $shell `
                    "Splat Pack - 4x3 - XInput" `
                    "Start-CARSPLAT-XInput.cmd" `
                    "Splat Pack 4:3 - XInput Controls" `
                    "Runtime4x3\dethrace-4x3-v0.10.1.exe"
                if ($null -ne $name) { [void]$created.Add($name) }
            }

            if ($Install16x9) {
                $name = New-ModernizerShortcut $shell `
                    "Splat Pack - 16x9 - Keyboard + Mouse" `
                    "Start-CARSPLAT-16x9.cmd" `
                    "Splat Pack 16:9 - Keyboard + Mouse Controls" `
                    "dethrace-16x9-v1.5.exe"
                if ($null -ne $name) { [void]$created.Add($name) }

                if ($InstallXInput) {
                    $name = New-ModernizerShortcut $shell `
                        "Splat Pack - 16x9 - XInput" `
                        "Start-CARSPLAT-16x9-XInput.cmd" `
                        "Splat Pack 16:9 - XInput Controls" `
                        "dethrace-16x9-v1.5.exe"
                    if ($null -ne $name) { [void]$created.Add($name) }
                }
            }
        }

        $name = New-ModernizerShortcut $shell `
            "Uninstall Carmageddon Dethrace Modernizer" `
            "Uninstall-Modernizer.cmd" `
            "Remove the installed Carmageddon Dethrace Modernizer game data" `
            $(if ($Install16x9) { "dethrace-16x9-v1.5.exe" } else { "Runtime4x3\dethrace-4x3-v0.10.1.exe" })
        if ($null -ne $name) { [void]$created.Add($name) }
    }
    catch {
        Write-Host ""
        Write-Host ("Warning: Windows shortcuts could not be created: " + $_.Exception.Message) -ForegroundColor Yellow
    }

    return @($created)
}

# ---------------------------------------------------------------------------
# In-place flow: the folder containing this installer becomes the game folder.
# ---------------------------------------------------------------------------

$GameDir = [System.IO.Path]::GetFullPath($PackageRoot)
if (-not [string]::IsNullOrWhiteSpace($TargetDir)) {
    $requestedTarget = Normalize-InputPath $TargetDir
    if ($null -ne $requestedTarget -and $requestedTarget -ne $GameDir) {
        Write-Host "TargetDir is ignored by this in-place build." -ForegroundColor Yellow
        Write-Host "Installation folder: $GameDir"
    }
}

$selection = Read-ComponentSelection $Components
$Install16x9 = [bool]$selection.Wide
$InstallXInput = [bool]$selection.XInput
$InstallGerman = [bool]$selection.German
if (-not $Install16x9 -and -not $InstallXInput -and -not $InstallGerman) {
    Fail "No component was selected."
}

Write-Host ""
Write-Host "Installation mode: IN-PLACE" -ForegroundColor Cyan
Write-Host "  This Modernizer folder becomes the finished game installation."
Write-Host "  Folder: $GameDir"
Write-Host ""
Write-Host "Selected:" -ForegroundColor Cyan
Write-Host ("  16:9:        " + $(if ($Install16x9) { "YES" } else { "no" }))
Write-Host ("  XInput:      " + $(if ($InstallXInput) { "YES" } else { "no" }))
Write-Host ("  German:      " + $(if ($InstallGerman) { "YES (experimental)" } else { "no" }))

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
        $retry = Read-Host "ENTER = folder picker, paste another path, C = cancel"
        if ($retry -match '^[Cc]$') { exit 2 }
        if ([string]::IsNullOrWhiteSpace($retry)) {
            $OriginalSource = $null
        }
        else {
            $OriginalSource = $retry
        }
    }
}

if ((Test-PathInside $GameDir $base.MainRoot) -or (Test-PathInside $base.MainRoot $GameDir)) {
    Fail "The Modernizer folder and original source must not be inside one another."
}
if ($null -ne $base.SplatRoot) {
    if ((Test-PathInside $GameDir $base.SplatRoot) -or (Test-PathInside $base.SplatRoot $GameDir)) {
        Fail "The Modernizer folder and Splat Pack source must not be inside one another."
    }
}

Write-Host ""
Write-Host "Original source detected:" -ForegroundColor Cyan
Write-Host "  Main game: $($base.MainRoot)"
if ($null -ne $base.SplatRoot) {
    Write-Host "  Splat Pack: $($base.SplatRoot)"
}
else {
    Write-Host "  Splat Pack: not found"
}

# Resolve every optional source before the first large copy starts.
$mainManifest = $null
$splatManifest = $null
$sourceRoot = $null
$splatSourceRoot = $null
if ($InstallGerman) {
    Write-Host ""
    Write-Host "German/Uncut is experimental." -ForegroundColor Yellow
    Write-Host "Known minor menu/localization visual issues may remain."
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
            $answer = Read-Host "ENTER = folder picker, paste another path, S = skip German/Uncut, C = cancel"
            if ($answer -match '^[Cc]$') { exit 2 }
            if ($answer -match '^[Ss]$') {
                $InstallGerman = $false
                $GermanSource = $null
                $mainManifest = $null
                $splatManifest = $null
                break
            }
            if ([string]::IsNullOrWhiteSpace($answer)) {
                $GermanSource = $null
            }
            else {
                $GermanSource = $answer
            }
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

# Verify both runtimes before touching original game data.
$baseExe = Join-Path $PackageRoot "Runtime4x3\dethrace-4x3-v0.10.1.exe"
if (-not (Test-Path -LiteralPath $baseExe -PathType Leaf)) {
    Fail "Runtime4x3\dethrace-4x3-v0.10.1.exe is missing from the Modernizer package."
}
$package4x3Hash = Get-Sha256 $baseExe
if ($package4x3Hash -ne $Gold4x3Sha256) {
    Fail "The 4:3 executable is not the approved parity build.`nExpected: $Gold4x3Sha256`nActual:   $package4x3Hash"
}
if ($Install16x9) {
    $sourceExe = Join-Path $PackageRoot "dethrace-16x9-v1.5.exe"
    if (-not (Test-Path -LiteralPath $sourceExe -PathType Leaf)) {
        Fail "dethrace-16x9-v1.5.exe is missing from the Modernizer package."
    }
    $packageWideHash = Get-Sha256 $sourceExe
    if ($packageWideHash -ne $GoldWideSha256) {
        Fail "The 16:9 executable is not the approved fullscreen-cockpit + right-edge-mirror Goldstandard build.`nExpected: $GoldWideSha256`nActual:   $packageWideHash"
    }
}

Write-Host ""
Write-Host "Preflight complete:" -ForegroundColor Cyan
Write-Host "  Original:     $($base.MainRoot)"
Write-Host ("  Splat Pack:   " + $(if ($null -ne $base.SplatRoot) { $base.SplatRoot } else { "not found" }))
Write-Host "  4:3 base:     YES - parity build verified"
Write-Host ("  16:9:         " + $(if ($Install16x9) { "YES - Goldstandard + fullscreen cockpit + aligned mirror" } else { "no" }))
Write-Host ("  XInput:       " + $(if ($InstallXInput) { "YES" } else { "no" }))
Write-Host ("  German:       " + $(if ($InstallGerman) { "YES - experimental ($sourceRoot)" } else { "no" }))
Write-Host ""
$continue = Read-Host "Start installation now? [Y/n]"
if ($continue -match '^[Nn]') { exit 2 }

$mainData = Join-Path $GameDir "DATA"
$splatData = Join-Path $GameDir "CARSPLAT\DATA"
$splatDetected = ($null -ne $base.SplatRoot)

$stateDir = Join-Path $GameDir ".dethrace-modernizer"
$backupDir = Join-Path $stateDir "backup"
$stageDir = Join-Path $stateDir "staging"
$transactionPath = Join-Path $stateDir "transaction.journal"
$legacyTransactionPath = Join-Path $stateDir "transaction.json"
$existingManifestPath = Join-Path $stateDir "install.json"

if (Test-Path -LiteralPath $existingManifestPath -PathType Leaf) {
    Fail "This folder already contains a completed Modernizer installation. Run Uninstall-Modernizer.cmd before installing again."
}
if ((Test-Path -LiteralPath $transactionPath -PathType Leaf) -or
    (Test-Path -LiteralPath $legacyTransactionPath -PathType Leaf)) {
    Restore-StaleInstall $GameDir $stateDir $PackageRoot $null $null
}
elseif (Test-Path -LiteralPath $stateDir -PathType Container) {
    Fail "A Modernizer state directory exists without a valid install or transaction manifest: $stateDir"
}

New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
New-Item -ItemType Directory -Path $stageDir -Force | Out-Null
$records = New-Object System.Collections.Generic.List[object]
$script:InstallTransactionActive = $true

$journalEncoding = New-Object System.Text.UTF8Encoding($false)

function Append-TransactionRecord($Record) {
    $json = $Record | ConvertTo-Json -Compress
    [System.IO.File]::AppendAllText($transactionPath, $json + [Environment]::NewLine, $journalEncoding)
}

function Add-InstallRecord([string]$RelativePath, [bool]$ExistedBefore, [string]$BackupRelative) {
    $record = [pscustomobject]@{
        path = $RelativePath
        existedBefore = $ExistedBefore
        backupPath = $BackupRelative
    }
    [void]$records.Add($record)
    Append-TransactionRecord $record
    return $record
}

function Install-One([string]$Source, [string]$RelativePath) {
    $destination = Join-Path $GameDir $RelativePath
    $destinationDir = Split-Path -Parent $destination
    New-Item -ItemType Directory -Path $destinationDir -Force | Out-Null

    $existed = Test-Path -LiteralPath $destination -PathType Leaf
    $backupRelative = $null
    $backupPath = $null
    if ($existed) {
        $recordNumber = $records.Count + 1
        $backupRelative = Join-Path ("{0:D6}" -f $recordNumber) $RelativePath
        $backupPath = Join-Path $backupDir $backupRelative
        New-Item -ItemType Directory -Path (Split-Path -Parent $backupPath) -Force | Out-Null
    }

    [void](Add-InstallRecord $RelativePath ([bool]$existed) $backupRelative)

    if ($existed) {
        # Backup is inside the same installation volume. Moving is essentially
        # instantaneous and avoids copying the original data a second time.
        Move-Item -LiteralPath $destination -Destination $backupPath -Force
    }
    Copy-Item -LiteralPath $Source -Destination $destination -Force
}

function Install-SourceTree([string]$SourceRoot, [string]$RelativePrefix = "") {
    $sourceFull = ([System.IO.Path]::GetFullPath($SourceRoot)).TrimEnd([char]92)
    $destinationRoot = if ([string]::IsNullOrWhiteSpace($RelativePrefix)) { $GameDir } else { Join-Path $GameDir $RelativePrefix }
    $label = if ([string]::IsNullOrWhiteSpace($RelativePrefix)) { "main game" } else { "Splat Pack" }
    New-Item -ItemType Directory -Path $destinationRoot -Force | Out-Null

    $copyList = New-Object System.Collections.Generic.List[object]
    [int64]$totalBytes = 0
    foreach ($file in @(Get-ChildItem -LiteralPath $sourceFull -File -Recurse -Force)) {
        $relative = $file.FullName.Substring($sourceFull.Length).TrimStart([char]92)
        if ([string]::IsNullOrWhiteSpace($relative)) { continue }
        if ($relative.StartsWith(".dethrace-modernizer\", [System.StringComparison]::OrdinalIgnoreCase) -or
            $relative.StartsWith(".modernizer\", [System.StringComparison]::OrdinalIgnoreCase)) {
            continue
        }
        $targetRelative = if ([string]::IsNullOrWhiteSpace($RelativePrefix)) { $relative } else { Join-Path $RelativePrefix $relative }
        $destination = Join-Path $GameDir $targetRelative
        if (Test-Path -LiteralPath $destination -PathType Leaf) {
            continue
        }
        [void]$copyList.Add([pscustomobject]@{
            RelativePath = $targetRelative
            Destination = $destination
            Length = [int64]$file.Length
        })
        $totalBytes += [int64]$file.Length
    }

    Write-Host ("  {0:N0} new files, {1:N1} MB to copy." -f $copyList.Count, ($totalBytes / 1MB))
    if ($copyList.Count -eq 0) { return }

    # Register all missing files before Robocopy starts. If copying is interrupted,
    # rollback simply removes whichever registered files were actually created.
    foreach ($item in $copyList) {
        [void](Add-InstallRecord $item.RelativePath $false $null)
    }

    $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
    $robocopy = Get-Command robocopy.exe -ErrorAction SilentlyContinue
    if ($null -ne $robocopy) {
        & $robocopy.Source $sourceFull $destinationRoot /E /COPY:DAT /DCOPY:T /R:1 /W:1 /NFL /NDL /NJH /NJS /NP /XC /XN /XO /XD ".dethrace-modernizer" ".modernizer"
        $code = $LASTEXITCODE
        if ($code -ge 8) {
            throw "Robocopy failed while copying $label (exit code $code)."
        }
    }
    else {
        foreach ($item in $copyList) {
            $relativeWithinSource = if ([string]::IsNullOrWhiteSpace($RelativePrefix)) {
                $item.RelativePath
            } else {
                $item.RelativePath.Substring($RelativePrefix.Length).TrimStart([char]92)
            }
            $src = Join-Path $sourceFull $relativeWithinSource
            New-Item -ItemType Directory -Path (Split-Path -Parent $item.Destination) -Force | Out-Null
            Copy-Item -LiteralPath $src -Destination $item.Destination -Force
        }
    }

    foreach ($item in $copyList) {
        if (-not (Test-Path -LiteralPath $item.Destination -PathType Leaf) -or
            (Get-Item -LiteralPath $item.Destination).Length -ne $item.Length) {
            throw "Original source copy verification failed: $($item.RelativePath)"
        }
    }
    $stopwatch.Stop()
    Write-Host ("  Done in {0:hh\:mm\:ss}." -f $stopwatch.Elapsed) -ForegroundColor Green
}

try {
    Write-Host ""
    Write-Host "Copying the original version into this Modernizer folder..."
    Install-SourceTree $base.MainRoot

    if ($null -ne $base.SplatRoot -and -not (Test-PathInside $base.SplatRoot $base.MainRoot)) {
        Install-SourceTree $base.SplatRoot "CARSPLAT"
    }

    $general = Join-Path $mainData "GENERAL.TXT"
    if (-not (Test-Path -LiteralPath $general -PathType Leaf)) {
        throw "The base copy is incomplete: DATA\\GENERAL.TXT is missing."
    }

    $splatDetected = Test-Path -LiteralPath (Join-Path $splatData "RACES\CASTLE2.TXT") -PathType Leaf

    $mainGog = Find-FirstExistingFile @(
        (Join-Path $OriginalSource "CARMA\GAME.GOG"),
        (Join-Path $OriginalSource "GAME.GOG"),
        (Join-Path $base.MainRoot "GAME.GOG")
    )
    $mainCutsceneStatus = "not-found"
    $mainCue = $null
    if ($null -ne $mainGog) {
        [void](Install-GogCutscenes -ImagePath $mainGog -RelativeDestination "DATA\CUTSCENE" -Label "Main game" -StageRoot $stageDir)
        $mainCutsceneStatus = "gog-image"
    }
    else {
        $mainCueCandidates = @(
            (Join-Path $OriginalSource "cd\CARMAGEDDON.CUE"),
            (Join-Path $OriginalSource "CARMAGEDDON.CUE"),
            (Join-Path $OriginalSource "cd\CARMA.CUE"),
            (Join-Path $OriginalSource "CARMA.CUE")
        )
        $mainSourceParent = Split-Path -Parent $base.MainRoot
        if (-not [string]::IsNullOrWhiteSpace($mainSourceParent)) {
            $mainCueCandidates += @(
                (Join-Path $mainSourceParent "cd\CARMAGEDDON.CUE"),
                (Join-Path $mainSourceParent "CARMAGEDDON.CUE")
            )
        }

        $mainCue = Find-FirstExistingFile $mainCueCandidates
        if ($null -ne $mainCue) {
            try {
                [void](Install-CueBinCutscenes -CuePath $mainCue -RelativeDestination "DATA\CUTSCENE" -Label "Main game" -StageRoot $stageDir)
                $mainCutsceneStatus = "cue-bin-image"
            }
            catch {
                Write-Host ""
                Write-Host ("Main game CUE/BIN cutscene import could not be used: " + $_.Exception.Message) -ForegroundColor Yellow
                Write-Host "Falling back to loose-SMK discovery." -ForegroundColor Yellow
                $mainCutsceneStatus = Import-LooseCutscenes -RelativeDestination "DATA\CUTSCENE" -Hints @($OriginalSource, $base.MainRoot) -SplatPack $false -Label "Main game"
            }
        }
        else {
            $mainCutsceneStatus = Import-LooseCutscenes -RelativeDestination "DATA\CUTSCENE" -Hints @($OriginalSource, $base.MainRoot) -SplatPack $false -Label "Main game"
        }
    }

    $mainMusicStatus = "not-found"
    $existingMainOgg = Join-Path $GameDir "MUSIC\Track02.ogg"
    $existingMainWav = Join-Path $GameDir "MUSIC\Track02.wav"
    if ((Test-Path -LiteralPath $existingMainOgg -PathType Leaf) -or
        (Test-Path -LiteralPath $existingMainWav -PathType Leaf)) {
        $mainMusicStatus = "source-copy"
    }
    elseif ($null -ne $mainCue) {
        try {
            $musicCount = Install-CueBinMusic -CuePath $mainCue -RelativeDestination "MUSIC" -Label "Main game" -StageRoot $stageDir
            if ($musicCount -gt 0) { $mainMusicStatus = "cue-bin-audio" }
        }
        catch {
            Write-Host ("Main game CD-audio import could not be used: " + $_.Exception.Message) -ForegroundColor Yellow
        }
    }

    $splatCutsceneStatus = "not-detected"
    $splatCue = $null
    if ($splatDetected) {
        $splatGogCandidates = @(
            (Join-Path $OriginalSource "CARSPLAT\SPLAT.GOG")
        )
        if ($null -ne $base.SplatRoot) {
            $splatGogCandidates += (Join-Path $base.SplatRoot "SPLAT.GOG")
        }
        $splatGog = Find-FirstExistingFile $splatGogCandidates
        if ($null -ne $splatGog) {
            [void](Install-GogCutscenes -ImagePath $splatGog -RelativeDestination "CARSPLAT\DATA\CUTSCENE" -Label "Splat Pack" -StageRoot $stageDir)
            $splatCutsceneStatus = "gog-image"
        }
        else {
            $splatCueCandidates = @(
                (Join-Path $OriginalSource "cd\SPLAT PACK.CUE"),
                (Join-Path $OriginalSource "SPLAT PACK.CUE"),
                (Join-Path $OriginalSource "cd\SPLATPACK.CUE"),
                (Join-Path $OriginalSource "SPLATPACK.CUE"),
                (Join-Path $OriginalSource "cd\SPLAT.CUE"),
                (Join-Path $OriginalSource "SPLAT.CUE")
            )
            $splatSourceParent = if ($null -ne $base.SplatRoot) { Split-Path -Parent $base.SplatRoot } else { $null }
            if (-not [string]::IsNullOrWhiteSpace($splatSourceParent)) {
                $splatCueCandidates += @(
                    (Join-Path $splatSourceParent "cd\SPLAT PACK.CUE"),
                    (Join-Path $splatSourceParent "SPLAT PACK.CUE"),
                    (Join-Path $splatSourceParent "cd\SPLATPACK.CUE"),
                    (Join-Path $splatSourceParent "SPLATPACK.CUE")
                )
            }

            $splatCue = Find-FirstExistingFile $splatCueCandidates

            # Robust fallback for repacks that use slightly different names
            # (for example eXoDOS "SPLAT PACK.CUE"). Prefer a CUE whose name
            # contains "splat" instead of requiring one exact filename.
            if ($null -eq $splatCue) {
                $cueSearchRoots = New-Object System.Collections.Generic.List[string]
                foreach ($candidateRoot in @(
                    (Join-Path $OriginalSource "cd"),
                    $OriginalSource,
                    $(if ($null -ne $splatSourceParent) { Join-Path $splatSourceParent "cd" } else { $null }),
                    $splatSourceParent
                )) {
                    if (-not [string]::IsNullOrWhiteSpace($candidateRoot) -and
                        (Test-Path -LiteralPath $candidateRoot -PathType Container)) {
                        [void]$cueSearchRoots.Add($candidateRoot)
                    }
                }

                foreach ($cueRoot in $cueSearchRoots) {
                    $discoveredCue = Get-ChildItem -LiteralPath $cueRoot -Filter "*.cue" -File -ErrorAction SilentlyContinue |
                        Where-Object { $_.BaseName -match '(?i)splat' } |
                        Sort-Object Name |
                        Select-Object -First 1
                    if ($null -ne $discoveredCue) {
                        $splatCue = $discoveredCue.FullName
                        break
                    }
                }
            }

            if ($null -ne $splatCue) {
                try {
                    [void](Install-CueBinCutscenes -CuePath $splatCue -RelativeDestination "CARSPLAT\DATA\CUTSCENE" -Label "Splat Pack" -StageRoot $stageDir)
                    $splatCutsceneStatus = "cue-bin-image"
                }
                catch {
                    Write-Host ""
                    Write-Host ("Splat Pack CUE/BIN cutscene import could not be used: " + $_.Exception.Message) -ForegroundColor Yellow
                    Write-Host "Falling back to loose-SMK discovery." -ForegroundColor Yellow
                    $splatCutsceneStatus = Import-LooseCutscenes -RelativeDestination "CARSPLAT\DATA\CUTSCENE" -Hints @($OriginalSource, $base.SplatRoot) -SplatPack $true -Label "Splat Pack"
                }
            }
            else {
                $splatCutsceneStatus = Import-LooseCutscenes -RelativeDestination "CARSPLAT\DATA\CUTSCENE" -Hints @($OriginalSource, $base.SplatRoot) -SplatPack $true -Label "Splat Pack"
            }
        }
    }

    $splatMusicStatus = "not-detected"
    if ($splatDetected) {
        $existingSplatOgg = Join-Path $GameDir "CARSPLAT\MUSIC\Track02.ogg"
        $existingSplatWav = Join-Path $GameDir "CARSPLAT\MUSIC\Track02.wav"
        if ((Test-Path -LiteralPath $existingSplatOgg -PathType Leaf) -or
            (Test-Path -LiteralPath $existingSplatWav -PathType Leaf)) {
            $splatMusicStatus = "source-copy"
        }
        elseif ($null -ne $splatCue) {
            try {
                $musicCount = Install-CueBinMusic -CuePath $splatCue -RelativeDestination "CARSPLAT\MUSIC" -Label "Splat Pack" -StageRoot $stageDir
                if ($musicCount -gt 0) { $splatMusicStatus = "cue-bin-audio" }
                else { $splatMusicStatus = "not-found" }
            }
            catch {
                Write-Host ("Splat Pack CD-audio import could not be used: " + $_.Exception.Message) -ForegroundColor Yellow
                $splatMusicStatus = "not-found"
            }
        }
        else {
            $splatMusicStatus = "not-found"
        }
    }

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
    # Always provide the original-aspect-ratio XInput launcher.
    $payload += @("Start-Carmageddon-XInput.cmd", "Controller\Carmageddon-XInput-Native.ps1")
    if ($splatDetected) {
        $payload += @("Start-CARSPLAT-XInput.cmd", "Controller\Carmageddon-SplatPack-XInput-Native.ps1")
    }

    # If widescreen is installed, provide the native-analog 16:9 launcher too.
    if ($Install16x9) {
        $payload += @("Start-Carmageddon-16x9-XInput.cmd", "Controller\Carmageddon-XInput.ps1")
        if ($splatDetected) {
            $payload += @("Start-CARSPLAT-16x9-XInput.cmd", "Controller\Carmageddon-SplatPack-XInput.ps1")
        }
    }
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
    $items = New-Object System.Collections.Generic.List[object]
    foreach ($parsedItem in $manifest.files) {
        [void]$items.Add($parsedItem)
    }

    $clean = 0
    $already = 0
    $alternateClean = 0
    $alternateAlready = 0
    $unsupported = New-Object System.Collections.Generic.List[string]
    $modeByPath = @{}

    # Preflight every applicable file before modifying any of them.
    foreach ($item in $items) {
        $relative = [string]$item.relative_path
        if ($relative.StartsWith("CARSPLAT\", [System.StringComparison]::OrdinalIgnoreCase) -and -not $splatDetected) {
            continue
        }

        $destination = Join-Path $GameDir $relative
        if (-not (Test-Path -LiteralPath $destination -PathType Leaf)) {
            [void]$unsupported.Add("$relative (missing)")
            continue
        }

        $current = Get-Sha256 $destination
        $cleanHash = ([string]$item.clean_sha256).ToLowerInvariant()
        $patchedHash = ([string]$item.patched_sha256).ToLowerInvariant()

        if ($current -eq $cleanHash) {
            $modeByPath[$relative] = "exact-clean"
            $clean++
            continue
        }
        if ($current -eq $patchedHash) {
            $modeByPath[$relative] = "exact-patched"
            $already++
            continue
        }

        [byte[]]$data = [System.IO.File]::ReadAllBytes($destination)
        $allAltOld = $true
        $allAltNew = $true
        foreach ($patch in $item.patches) {
            if ($null -eq $patch.alternate_old_b64 -or $null -eq $patch.alternate_new_b64) {
                $allAltOld = $false
                $allAltNew = $false
                break
            }

            [byte[]]$altOld = [Convert]::FromBase64String([string]$patch.alternate_old_b64)
            [byte[]]$altNew = [Convert]::FromBase64String([string]$patch.alternate_new_b64)
            $oldCount = @(Find-ByteSequencePositions $data $altOld).Count
            $newCount = @(Find-ByteSequencePositions $data $altNew).Count
            if ($oldCount -ne 1 -or $newCount -ne 0) { $allAltOld = $false }
            if ($oldCount -ne 0 -or $newCount -ne 1) { $allAltNew = $false }
        }

        if ($allAltOld) {
            $modeByPath[$relative] = "alternate-clean"
            $alternateClean++
        }
        elseif ($allAltNew) {
            $modeByPath[$relative] = "alternate-patched"
            $alternateAlready++
        }
        else {
            [void]$unsupported.Add("$relative (SHA-256 $current)")
        }
    }

    if ($unsupported.Count -gt 0) {
        return [pscustomobject]@{
            supported = $false
            changed = 0
            alreadyPatched = ($already + $alternateAlready)
            alternateMatched = $alternateClean
            unsupportedFiles = @($unsupported | ForEach-Object { $_ })
        }
    }

    $changed = 0
    foreach ($item in $items) {
        $relative = [string]$item.relative_path
        if ($relative.StartsWith("CARSPLAT\", [System.StringComparison]::OrdinalIgnoreCase) -and -not $splatDetected) {
            continue
        }

        $mode = [string]$modeByPath[$relative]
        if ($mode -eq "exact-patched" -or $mode -eq "alternate-patched") {
            continue
        }

        $destination = Join-Path $GameDir $relative
        [byte[]]$data = [System.IO.File]::ReadAllBytes($destination)

        $patchIndex = 0
        foreach ($patch in $item.patches) {
            $patchIndex++
            if ($mode -eq "alternate-clean") {
                [byte[]]$oldBytes = [Convert]::FromBase64String([string]$patch.alternate_old_b64)
                [byte[]]$newBytes = [Convert]::FromBase64String([string]$patch.alternate_new_b64)
            }
            else {
                [byte[]]$oldBytes = [Convert]::FromBase64String([string]$patch.old_b64)
                [byte[]]$newBytes = [Convert]::FromBase64String([string]$patch.new_b64)
            }
            $label = "$relative / patch $patchIndex / $mode"
            [byte[]]$data = Replace-ByteSequenceExactlyOnce $data $oldBytes $newBytes $label
        }

        $tempPath = Join-Path $stageDir ("DamageHUD\" + $relative)
        New-Item -ItemType Directory -Path (Split-Path -Parent $tempPath) -Force | Out-Null
        [System.IO.File]::WriteAllBytes($tempPath, $data)

        if ($mode -eq "exact-clean") {
            $patchedHash = ([string]$item.patched_sha256).ToLowerInvariant()
            $tempHash = Get-Sha256 $tempPath
            if ($tempHash -ne $patchedHash) {
                throw "Damage HUD source patch produced an unexpected target hash: $relative`nExpected: $patchedHash`nActual:   $tempHash"
            }
        }
        else {
            # Alternate encrypted revision: verify the exact replacement
            # signatures are now present before committing the file.
            foreach ($patch in $item.patches) {
                [byte[]]$altNew = [Convert]::FromBase64String([string]$patch.alternate_new_b64)
                if (@(Find-ByteSequencePositions $data $altNew).Count -ne 1) {
                    throw "Alternate Damage HUD verification failed: $relative"
                }
            }
        }

        Install-One $tempPath $relative
        $changed++
    }

    return [pscustomobject]@{
        supported = $true
        changed = $changed
        alreadyPatched = ($already + $alternateAlready)
        alternateMatched = $alternateClean
        unsupportedFiles = @()
    }
}

    foreach ($relative in $payload) {
        $source = Join-Path $PackageRoot $relative
        if (-not (Test-Path -LiteralPath $source -PathType Leaf)) {
            throw "Package file missing: $relative"
        }
        # In-place mode: package files already are at their final paths.
    }

    if ($mainStatus -eq "generated") {
        foreach ($entry in @($mainManifest.files)) {
            $relative = "DATA\" + ([string]$entry.path)
            $source = Join-Path $mainStage ([string]$entry.path)
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
        Write-Host ""
        Write-Host "Verifying installed German file structure..."
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
        Write-Host "  German file structure verified." -ForegroundColor Green
        Write-Host "Finalizing localization..."
    }

    if ($Install16x9) {
        Write-Host ""
        Write-Host "Checking the source-verified 16:9 Damage HUD right-edge correction..."
        $damageResult = Install-DamageHudRightEdge
        if ([bool]$damageResult.supported) {
            if ($damageResult.changed -gt 0) {
                $damageHudStatus = "patched"
            }
            else {
                $damageHudStatus = "already-correct"
            }
            Write-Host ("  Damage HUD files changed: " + $damageResult.changed)
            Write-Host ("  Already correct: " + $damageResult.alreadyPatched)
            if ($damageResult.alternateMatched -gt 0) {
                Write-Host ("  Alternate encrypted source files matched safely: " + $damageResult.alternateMatched) -ForegroundColor Green
            }
        }
        else {
            $damageHudStatus = "skipped-unsupported-source-revision"
            Write-Host "  Alternate/unsupported game-data revision detected." -ForegroundColor Yellow
            Write-Host "  The optional 16:9 Damage HUD source-data correction will be skipped." -ForegroundColor Yellow
            Write-Host "  All engine-side 16:9 Modernizer features remain installed." -ForegroundColor Yellow
            $firstUnsupported = @($damageResult.unsupportedFiles | Select-Object -First 1)
            if ($firstUnsupported.Count -gt 0) {
                Write-Host ("  First unmatched file: " + $firstUnsupported[0]) -ForegroundColor DarkYellow
            }
        }
    }

    $exeHash = $null
    if ($Install16x9) {
        $exeHash = Get-Sha256 (Join-Path $GameDir "dethrace-16x9-v1.5.exe")
        if ($exeHash -ne $GoldWideSha256) {
            throw "Fullscreen-cockpit + right-edge-mirror Goldstandard 16:9 executable verification failed after installation.`nExpected: $GoldWideSha256`nActual:   $exeHash"
        }
    }
    if ($InstallGerman) {
        Write-Host "  Localization finalized." -ForegroundColor Green
    }

    [object[]]$recordArray = @($records | ForEach-Object { $_ })

    $manifest = [pscustomobject]@{
        modernizerVersion = $ModernizerVersion
        engineVersion = $EngineVersion
        installedAt = (Get-Date).ToString("o")
        gameDir = $GameDir
        targetFirst = $false
        inPlace = $true
        installationMode = "in-place"
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
        mainCutsceneStatus = $mainCutsceneStatus
        splatCutsceneStatus = $splatCutsceneStatus
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
        Write-Host "The Modernizer package folder was restored as far as possible."
    }
    catch {
        Write-Host ("Additional rollback error: " + $_.Exception.Message) -ForegroundColor Red
    }
    $script:InstallTransactionActive = $false
    exit 1
}

$script:InstallTransactionActive = $false
$createdShortcuts = @(Create-ModernizerShortcuts)
Write-Host ""
Write-Host "Carmageddon Dethrace Modernizer was installed in-place." -ForegroundColor Green
Write-Host "Original source: untouched"
if ($InstallGerman) {
    Write-Host "German source: untouched"
}
Write-Host ""
Write-Host "Base Dethrace 4:3 runtime: installed"
Write-Host ("16:9 Goldstandard + fullscreen cockpit + aligned mirror runtime: " + $(if ($Install16x9) { "installed + verified" } else { "not selected" }))
Write-Host ("XInput: " + $(if ($InstallXInput) { "installed" } else { "not selected" }))
if ($Install16x9) {
    if ($damageHudStatus -eq "patched" -or $damageHudStatus -eq "already-correct") {
        Write-Host "Damage HUD right-edge correction: installed"
    }
    elseif ($damageHudStatus -eq "skipped-unsupported-source-revision") {
        Write-Host "Damage HUD right-edge correction: skipped (alternate source revision)" -ForegroundColor Yellow
    }
}
if ($InstallGerman) {
    Write-Host "German/Uncut main game: built and verified"
    if ($splatDetected) {
        Write-Host "German Splat Pack: built and verified"
    }
}
else {
    Write-Host "German/Uncut: not selected"
}
Write-Host ""
Write-Host ("Main-game cutscenes: " + $mainCutsceneStatus)
if ($splatDetected) { Write-Host ("Splat Pack cutscenes: " + $splatCutsceneStatus) }
Write-Host ("Main-game music: " + $mainMusicStatus)
if ($splatDetected) { Write-Host ("Splat Pack music: " + $splatMusicStatus) }
Write-Host ""
if ($createdShortcuts.Count -gt 0) {
    Write-Host "Ready-to-use shortcuts were created here:" -ForegroundColor Cyan
    Write-Host "  $ShortcutRoot"
    foreach ($shortcutName in $createdShortcuts) {
        Write-Host ("  - " + $shortcutName)
    }
}
else {
    Write-Host "The game is installed, but Windows shortcuts could not be created." -ForegroundColor Yellow
}
Write-Host ""
Write-Host "You do not need to open the internal _Modernizer folder for normal use."
Write-Host "Action Replay: use keyboard/mouse controls; the normal XInput layout is intentionally not remapped for Replay mode."
Write-Host ""
