param(
    [string]$GameDir
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$ModernizerVersion = "0.1-test"
$EngineVersion = "v1.5-source-port"
$PackageRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

function Fail([string]$Message) {
    Write-Host ""
    Write-Host "FEHLER: $Message" -ForegroundColor Red
    Write-Host ""
    exit 1
}

function Select-GameFolder {
    Add-Type -AssemblyName System.Windows.Forms

    $dialog = New-Object System.Windows.Forms.FolderBrowserDialog
    $dialog.Description = "Carmageddon / Dethrace Hauptordner auswählen"
    $dialog.ShowNewFolderButton = $false

    if ($dialog.ShowDialog() -ne [System.Windows.Forms.DialogResult]::OK) {
        exit 2
    }
    return $dialog.SelectedPath
}

if ([string]::IsNullOrWhiteSpace($GameDir)) {
    $GameDir = Select-GameFolder
}

$GameDir = [System.IO.Path]::GetFullPath($GameDir.Trim('"'))
$general = Join-Path $GameDir "DATA\GENERAL.TXT"

if (-not (Test-Path -LiteralPath $general -PathType Leaf)) {
    Fail "DATA\GENERAL.TXT wurde nicht gefunden. Bitte den Dethrace-Hauptordner auswählen."
}

$sourceExe = Join-Path $PackageRoot "dethrace-16x9-v1.5.exe"
if (-not (Test-Path -LiteralPath $sourceExe -PathType Leaf)) {
    Fail "dethrace-16x9-v1.5.exe fehlt im Modernizer-Paket."
}

$stateDir = Join-Path $GameDir ".modernizer"
$manifestPath = Join-Path $stateDir "install.json"

if (Test-Path -LiteralPath $manifestPath) {
    Fail "Der Modernizer ist in diesem Ordner bereits installiert. Bitte zuerst Uninstall-Modernizer.cmd ausführen."
}

$backupDir = Join-Path $stateDir "backup"
New-Item -ItemType Directory -Path $backupDir -Force | Out-Null

$splatDetected = Test-Path -LiteralPath (Join-Path $GameDir "CARSPLAT\DATA") -PathType Container

$payload = @(
    "dethrace-16x9-v1.5.exe",
    "Start-Carmageddon-16x9.cmd",
    "Start-Carmageddon-16x9-XInput.cmd",
    "Controller\Carmageddon-XInput.ps1",
    "Uninstall-Modernizer.ps1",
    "Uninstall-Modernizer.cmd"
)

if ($splatDetected) {
    $payload += @(
        "Start-CARSPLAT-16x9.cmd",
        "Start-CARSPLAT-16x9-XInput.cmd",
        "Controller\Carmageddon-SplatPack-XInput.ps1"
    )
}

$records = @()

try {
    foreach ($relative in $payload) {
        $source = Join-Path $PackageRoot $relative
        if (-not (Test-Path -LiteralPath $source -PathType Leaf)) {
            throw "Paketdatei fehlt: $relative"
        }

        $destination = Join-Path $GameDir $relative
        $destinationDir = Split-Path -Parent $destination
        New-Item -ItemType Directory -Path $destinationDir -Force | Out-Null

        $existed = Test-Path -LiteralPath $destination -PathType Leaf
        $backupRelative = $null

        if ($existed) {
            $backupRelative = $relative
            $backupPath = Join-Path $backupDir $backupRelative
            New-Item -ItemType Directory -Path (Split-Path -Parent $backupPath) -Force | Out-Null
            Copy-Item -LiteralPath $destination -Destination $backupPath -Force
        }

        Copy-Item -LiteralPath $source -Destination $destination -Force

        $records += [pscustomobject]@{
            path = $relative
            existedBefore = [bool]$existed
            backupPath = $backupRelative
        }
    }

    $exeHash = (Get-FileHash -LiteralPath (Join-Path $GameDir "dethrace-16x9-v1.5.exe") -Algorithm SHA256).Hash.ToLowerInvariant()

    $manifest = [pscustomobject]@{
        modernizerVersion = $ModernizerVersion
        engineVersion = $EngineVersion
        installedAt = (Get-Date).ToString("o")
        gameDir = $GameDir
        splatPackDetected = [bool]$splatDetected
        executableSha256 = $exeHash
        files = $records
    }

    $manifest | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $manifestPath -Encoding UTF8
}
catch {
    Write-Host ""
    Write-Host "Installation fehlgeschlagen. Bereits kopierte Dateien werden soweit möglich zurückgesetzt." -ForegroundColor Red

    foreach ($record in @($records) | Select-Object -Reverse) {
        $destination = Join-Path $GameDir $record.path
        if ($record.existedBefore -and $record.backupPath) {
            $backupPath = Join-Path $backupDir $record.backupPath
            if (Test-Path -LiteralPath $backupPath) {
                Copy-Item -LiteralPath $backupPath -Destination $destination -Force
            }
        }
        elseif (Test-Path -LiteralPath $destination) {
            Remove-Item -LiteralPath $destination -Force
        }
    }

    Remove-Item -LiteralPath $stateDir -Recurse -Force -ErrorAction SilentlyContinue
    throw
}

Write-Host ""
Write-Host "Carmageddon Dethrace Modernizer wurde installiert." -ForegroundColor Green
Write-Host "Ordner: $GameDir"
Write-Host "16:9 Source-Port: installiert"
Write-Host "XInput: installiert"
if ($splatDetected) {
    Write-Host "Splat Pack: erkannt und Starter installiert"
}
else {
    Write-Host "Splat Pack: nicht erkannt; Splat-Starter wurden nicht installiert"
}
Write-Host ""
Write-Host "Deine normale dethrace.exe und die Spieldaten wurden nicht verändert."
Write-Host ""
Write-Host "Start:"
Write-Host "  Start-Carmageddon-16x9.cmd"
Write-Host "  Start-Carmageddon-16x9-XInput.cmd"
if ($splatDetected) {
    Write-Host "  Start-CARSPLAT-16x9.cmd"
    Write-Host "  Start-CARSPLAT-16x9-XInput.cmd"
}
Write-Host ""
