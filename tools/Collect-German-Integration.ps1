param(
    [string]$GameDir
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Fail([string]$Message) {
    Write-Host ""
    Write-Host "FEHLER: $Message" -ForegroundColor Red
    Write-Host ""
    exit 1
}

function Select-GameFolder {
    Add-Type -AssemblyName System.Windows.Forms
    $dialog = New-Object System.Windows.Forms.FolderBrowserDialog
    $dialog.Description = "Carmageddon / Dethrace Hauptordner auswaehlen"
    $dialog.ShowNewFolderButton = $false
    if ($dialog.ShowDialog() -ne [System.Windows.Forms.DialogResult]::OK) {
        exit 2
    }
    return $dialog.SelectedPath
}

function Get-RelativePath([string]$Base, [string]$Path) {
    $baseUri = New-Object System.Uri(($Base.TrimEnd('\') + '\'))
    $pathUri = New-Object System.Uri($Path)
    return [System.Uri]::UnescapeDataString($baseUri.MakeRelativeUri($pathUri).ToString()).Replace('/','\')
}

if ([string]::IsNullOrWhiteSpace($GameDir)) {
    $default = "E:\LaunchBox\Emulators\QuiverLauncher-win-Portable\Apps\Carmageddon-Dethrace"
    if (Test-Path -LiteralPath (Join-Path $default "DATA\GENERAL.TXT") -PathType Leaf) {
        $GameDir = $default
    }
    else {
        $GameDir = Select-GameFolder
    }
}

$GameDir = [System.IO.Path]::GetFullPath($GameDir.Trim('"'))
if (-not (Test-Path -LiteralPath (Join-Path $GameDir "DATA\GENERAL.TXT") -PathType Leaf)) {
    Fail "DATA\GENERAL.TXT wurde nicht gefunden."
}

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$outRoot = Join-Path $ScriptDir ("German-Integration-Diagnostic-" + $stamp)
$zipPath = $outRoot + ".zip"

New-Item -ItemType Directory -Path $outRoot -Force | Out-Null

$roots = @(
    [pscustomobject]@{ Label = "MAIN"; Path = (Join-Path $GameDir "DATA") }
)

$splatData = Join-Path $GameDir "CARSPLAT\DATA"
if (Test-Path -LiteralPath $splatData -PathType Container) {
    $roots += [pscustomobject]@{ Label = "SPLAT"; Path = $splatData }
}

$allRows = New-Object System.Collections.Generic.List[object]

Write-Host ""
Write-Host "Inventarisiere die vorhandenen Spieldaten..."
Write-Host "Es werden keine Spieldateien veraendert."
Write-Host ""

foreach ($root in $roots) {
    Write-Host ("[" + $root.Label + "] " + $root.Path)

    $files = Get-ChildItem -LiteralPath $root.Path -File -Recurse -Force
    $n = 0
    foreach ($file in $files) {
        $n++
        if (($n % 200) -eq 0) {
            Write-Host ("  " + $n + " Dateien...")
        }

        $relative = Get-RelativePath $root.Path $file.FullName
        $hash = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()

        $allRows.Add([pscustomobject]@{
            area = $root.Label
            relativePath = $relative
            extension = $file.Extension.ToLowerInvariant()
            size = $file.Length
            lastWriteTimeUtc = $file.LastWriteTimeUtc.ToString("yyyy-MM-ddTHH:mm:ss.fffZ")
            sha256 = $hash
        })
    }
}

$inventoryCsv = Join-Path $outRoot "inventory.csv"
$allRows | Sort-Object area, relativePath | Export-Csv -LiteralPath $inventoryCsv -NoTypeInformation -Encoding UTF8

$allRows |
    Group-Object area, extension |
    ForEach-Object {
        [pscustomobject]@{
            area = $_.Group[0].area
            extension = $_.Group[0].extension
            count = $_.Count
            totalBytes = ($_.Group | Measure-Object size -Sum).Sum
        }
    } |
    Sort-Object area, extension |
    Export-Csv -LiteralPath (Join-Path $outRoot "extension-summary.csv") -NoTypeInformation -Encoding UTF8

$allRows |
    Group-Object area, lastWriteTimeUtc |
    ForEach-Object {
        [pscustomobject]@{
            area = $_.Group[0].area
            lastWriteTimeUtc = $_.Group[0].lastWriteTimeUtc
            count = $_.Count
            sample = (($_.Group | Select-Object -First 8 | ForEach-Object relativePath) -join " | ")
        }
    } |
    Sort-Object area, @{Expression="count";Descending=$true}, lastWriteTimeUtc |
    Export-Csv -LiteralPath (Join-Path $outRoot "timestamp-groups.csv") -NoTypeInformation -Encoding UTF8

$main = @{}
foreach ($r in ($allRows | Where-Object area -eq "MAIN")) {
    $main[$r.relativePath.ToLowerInvariant()] = $r
}
$compare = New-Object System.Collections.Generic.List[object]
foreach ($s in ($allRows | Where-Object area -eq "SPLAT")) {
    $key = $s.relativePath.ToLowerInvariant()
    if ($main.ContainsKey($key)) {
        $m = $main[$key]
        $compare.Add([pscustomobject]@{
            relativePath = $s.relativePath
            mainSha256 = $m.sha256
            splatSha256 = $s.sha256
            identical = ($m.sha256 -eq $s.sha256)
            mainSize = $m.size
            splatSize = $s.size
        })
    }
}
$compare | Sort-Object relativePath | Export-Csv -LiteralPath (Join-Path $outRoot "main-vs-splat-common-files.csv") -NoTypeInformation -Encoding UTF8

$copyDir = Join-Path $outRoot "selected-text-and-config"
New-Item -ItemType Directory -Path $copyDir -Force | Out-Null

$interestingNames = @(
    "TEXT.TXT",
    "DARES.TXT",
    "KEYNAMES.TXT",
    "POWERUP.TXT",
    "DPOWERUP.TXT",
    "OPPONENT.TXT",
    "TRNSLATE.TXT",
    "TRANSLATE.TXT"
)

foreach ($root in $roots) {
    foreach ($name in $interestingNames) {
        $src = Join-Path $root.Path $name
        if (Test-Path -LiteralPath $src -PathType Leaf) {
            $destDir = Join-Path $copyDir $root.Label
            New-Item -ItemType Directory -Path $destDir -Force | Out-Null
            Copy-Item -LiteralPath $src -Destination (Join-Path $destDir $name) -Force
        }
    }
}

foreach ($rootFile in @("dethrace.ini","Dethrace.ini","README.txt","LIESMICH.txt")) {
    $src = Join-Path $GameDir $rootFile
    if (Test-Path -LiteralPath $src -PathType Leaf) {
        Copy-Item -LiteralPath $src -Destination (Join-Path $copyDir ("ROOT-" + $rootFile)) -Force
    }
}

$likely = $allRows | Where-Object {
    $_.extension -in @(".fli",".flc",".pix",".wav",".raw",".snd",".txt")
}

$likely |
    Sort-Object area, relativePath |
    Export-Csv -LiteralPath (Join-Path $outRoot "localization-candidates.csv") -NoTypeInformation -Encoding UTF8

$summary = @()
$summary += "Carmageddon Dethrace Modernizer - German integration diagnostic"
$summary += ("Created: " + (Get-Date).ToString("o"))
$summary += ("GameDir: " + $GameDir)
$summary += ("Main files: " + (($allRows | Where-Object area -eq "MAIN").Count))
$summary += ("Splat Pack detected: " + ($roots.Label -contains "SPLAT"))
if ($roots.Label -contains "SPLAT") {
    $summary += ("Splat files: " + (($allRows | Where-Object area -eq "SPLAT").Count))
}
$summary += ""
$summary += "This package contains inventories, hashes, timestamps and selected text/config files."
$summary += "It intentionally does not copy bulk FLI/PIX/sound assets."
$summary | Set-Content -LiteralPath (Join-Path $outRoot "SUMMARY.txt") -Encoding UTF8

if (Test-Path -LiteralPath $zipPath) {
    Remove-Item -LiteralPath $zipPath -Force
}
Compress-Archive -Path (Join-Path $outRoot "*") -DestinationPath $zipPath -Force

Write-Host ""
Write-Host "Fertig." -ForegroundColor Green
Write-Host "Bitte diese ZIP-Datei im Chat hochladen:"
Write-Host $zipPath
Write-Host ""
