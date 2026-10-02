@echo off
chcp 65001 >nul
setlocal
title Carmageddon Dethrace Modernizer Uninstaller
cd /d "%~dp0"

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Uninstall-Modernizer.ps1"
set "RC=%ERRORLEVEL%"

echo.
if not "%RC%"=="0" (
    echo Uninstaller beendet mit Fehlercode %RC%.
    pause
    exit /b %RC%
)

echo Deinstallation erfolgreich.
echo.
pause

set "CLEANUP=%TEMP%\dethrace-modernizer-cleanup-%RANDOM%%RANDOM%.cmd"
> "%CLEANUP%" echo @echo off
>> "%CLEANUP%" echo ping 127.0.0.1 -n 2 ^>nul
>> "%CLEANUP%" echo del /q "%~dp0Uninstall-Modernizer.ps1" 2^>nul
>> "%CLEANUP%" echo del /q "%~f0" 2^>nul
>> "%CLEANUP%" echo del /q "%%~f0" 2^>nul
start "" /min cmd.exe /c "%CLEANUP%"
exit /b 0
