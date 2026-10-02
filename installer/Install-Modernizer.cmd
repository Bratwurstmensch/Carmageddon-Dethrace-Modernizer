@echo off
chcp 65001 >nul
setlocal
title Carmageddon Dethrace Modernizer Installer
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Install-Modernizer.ps1" %*
set "RC=%ERRORLEVEL%"
echo.
if not "%RC%"=="0" echo Installer beendet mit Fehlercode %RC%.
pause
exit /b %RC%
