@echo off
chcp 65001 >nul
setlocal
title Carmageddon Dethrace Modernizer v0.8.0 RC1 Installer
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Install-Modernizer.ps1" %*
set "RC=%ERRORLEVEL%"
echo.
if not "%RC%"=="0" echo Installer exited with error code %RC%.
pause
exit /b %RC%