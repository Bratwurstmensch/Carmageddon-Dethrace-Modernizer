@echo off
chcp 65001 >nul
setlocal
title Carmageddon Dethrace Modernizer Uninstaller
cd /d "%~dp0"

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Uninstall-Modernizer.ps1"
set "RC=%ERRORLEVEL%"

echo.
if not "%RC%"=="0" (
    echo Uninstaller exited with error code %RC%.
    echo Press any key to continue . . .
pause >nul
    exit /b %RC%
)

echo WARNING: After the next key press, the complete generated target directory will be deleted.
echo The source installations will NOT be deleted.
echo.
echo Press any key to continue . . .
pause >nul

set "TARGET=%~dp0"
set "CLEANUP=%TEMP%\dethrace-modernizer-target-cleanup-%RANDOM%%RANDOM%.cmd"
> "%CLEANUP%" echo @echo off
>> "%CLEANUP%" echo ping 127.0.0.1 -n 3 ^>nul
>> "%CLEANUP%" echo rmdir /s /q "%TARGET%" 2^>nul
>> "%CLEANUP%" echo del /q "%%~f0" 2^>nul
start "" /min cmd.exe /c "%CLEANUP%"
exit /b 0