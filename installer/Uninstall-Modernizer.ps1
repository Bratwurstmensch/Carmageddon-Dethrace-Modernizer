param()

[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [Console]::OutputEncoding
$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$GameDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$stateDir = Join-Path $GameDir ".dethrace-modernizer"
$manifestPath = Join-Path $stateDir "install.json"

if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) {
    Write-Host ""
    Write-Host "No Modernizer installation data was found." -ForegroundColor Yellow
    Write-Host "Nothing was changed."
    exit 1
}

$manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
if (-not [bool]$manifest.targetFirst) {
    throw "This uninstaller is intended only for a target-first installation."
}

Write-Host ""
Write-Host "This installation was created by the Modernizer in its own target directory." -ForegroundColor Cyan
Write-Host "After confirmation, the complete target directory will be removed:" -ForegroundColor Yellow
Write-Host $GameDir
Write-Host ""
Write-Host "The original/English source and any German source remain untouched."
Write-Host ""
exit 0