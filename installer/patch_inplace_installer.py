#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit("usage: patch_inplace_installer.py <Install-Modernizer.ps1>")

path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8-sig")

old = r'''function Copy-DirectoryContents([string]$SourceRoot, [string]$DestinationRoot) {
    New-Item -ItemType Directory -Path $DestinationRoot -Force | Out-Null
    foreach ($item in @(Get-ChildItem -LiteralPath $SourceRoot -Force)) {
        if ($item.Name -ieq ".dethrace-modernizer" -or $item.Name -ieq ".modernizer") {
            continue
        }
        Copy-Item -LiteralPath $item.FullName -Destination $DestinationRoot -Recurse -Force
    }
}'''

new = r'''function Copy-DirectoryContents([string]$SourceRoot, [string]$DestinationRoot, [string]$Label = "game data") {
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
                $status = ("{0,3}% | {1}/{2} files | {3:N1}/{4:N1} MB | elapsed {5:hh\:mm\:ss}" -f $percent, ($copiedFiles + 1), $totalFiles, ($copiedBytes / 1MB), $totalMiB, $elapsed)

                Write-Progress -Activity ("Copying " + $Label) -Status $status -PercentComplete $percent

                if (($elapsed - $lastConsoleUpdate).TotalSeconds -ge 2) {
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
}'''

if old not in text:
    raise SystemExit("Copy-DirectoryContents anchor not found")

text = text.replace(old, new, 1)
text = text.replace('Copy-DirectoryContents $base.MainRoot $GameDir', 'Copy-DirectoryContents $base.MainRoot $GameDir "main game"', 1)
text = text.replace('Copy-DirectoryContents $base.SplatRoot $targetSplatRoot', 'Copy-DirectoryContents $base.SplatRoot $targetSplatRoot "Splat Pack"', 1)

path.write_text(text, encoding="utf-8")
print("Patched in-place copy progress.")
