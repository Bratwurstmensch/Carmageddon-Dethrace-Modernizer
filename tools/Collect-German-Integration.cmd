@echo off
setlocal
title Carmageddon German Integration Diagnostic
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Collect-German-Integration.ps1" %*
set "RC=%ERRORLEVEL%"
echo.
if not "%RC%"=="0" echo Diagnose beendet mit Fehlercode %RC%.
pause
exit /b %RC%
