@echo off
chcp 65001 >nul
setlocal
title Carmageddon Dethrace Modernizer Uninstaller
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Uninstall-Modernizer.ps1"
set "RC=%ERRORLEVEL%"
echo.
if not "%RC%"=="0" echo Uninstaller beendet mit Fehlercode %RC%.
pause
exit /b %RC%
