param()

[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [Console]::OutputEncoding

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$GameDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$stateDir = Join-Path $GameDir ".dethrace-modernizer"
$legacyStateDir = Join-Path $GameDir ".modernizer"

if (-not (Test-Path -LiteralPath (Join-Path $stateDir "install.json") -PathType Leaf)) {
    if (Test-Path -LiteralPath (Join-Path $legacyStateDir "install.json") -PathType Leaf) {
        $stateDir = $legacyStateDir
    }
}

$manifestPath = Join-Path $stateDir "install.json"
$backupDir = Join-Path $stateDir "backup"

if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) {
    Write-Host ""
    Write-Host "Keine Modernizer-Installationsdaten gefunden." -ForegroundColor Yellow
    Write-Host "Es wurde nichts veraendert."
    exit 1
}

$manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
$files = @($manifest.files)

Write-Host ""
Write-Host "Carmageddon Dethrace Modernizer wird entfernt..."

$reverseFiles = @($files)
[array]::Reverse($reverseFiles)

foreach ($record in $reverseFiles) {
    $destination = Join-Path $GameDir ([string]$record.path)

    if ([bool]$record.existedBefore) {
        if ([string]::IsNullOrWhiteSpace([string]$record.backupPath)) {
            throw "Backup-Angabe fehlt fuer $($record.path)"
        }

        $backupPath = Join-Path $backupDir ([string]$record.backupPath)
        if (-not (Test-Path -LiteralPath $backupPath -PathType Leaf)) {
            throw "Backup-Datei fehlt: $backupPath"
        }

        New-Item -ItemType Directory -Path (Split-Path -Parent $destination) -Force | Out-Null
        Copy-Item -LiteralPath $backupPath -Destination $destination -Force
    }
    elseif (Test-Path -LiteralPath $destination -PathType Leaf) {
        Remove-Item -LiteralPath $destination -Force
    }
}

Remove-Item -LiteralPath $stateDir -Recurse -Force -ErrorAction SilentlyContinue

$controllerDir = Join-Path $GameDir "Controller"
if (Test-Path -LiteralPath $controllerDir -PathType Container) {
    $remaining = @(Get-ChildItem -LiteralPath $controllerDir -Force)
    if ($remaining.Count -eq 0) {
        Remove-Item -LiteralPath $controllerDir -Force
    }
}

Write-Host ""
Write-Host "Modernizer wurde entfernt; vorhandene Dateien wurden aus dem Backup wiederhergestellt." -ForegroundColor Green
Write-Host "Originale Spieldaten und die normale dethrace.exe wurden nicht veraendert."
Write-Host ""
