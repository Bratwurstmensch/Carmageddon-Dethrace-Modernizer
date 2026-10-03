@echo off
setlocal
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Import-Cutscenes-from-Original.ps1" -GameDir "%~dp0"
set "RC=%ERRORLEVEL%"
echo.
if not "%RC%"=="0" echo Cutscene import ended with error code %RC%.
pause
exit /b %RC%
