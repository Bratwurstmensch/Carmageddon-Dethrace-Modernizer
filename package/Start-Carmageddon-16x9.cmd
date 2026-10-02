@echo off
setlocal
title Carmageddon Dethrace 16:9 v1.5
cd /d "%~dp0"
set "ROOT=%CD%"
set "PATH=%ROOT%;%PATH%"

if not exist "%ROOT%\DATA\GENERAL.TXT" goto missing

"%ROOT%\dethrace-16x9-v1.5.exe" --dir "%ROOT%" -hires --opengl
set "RC=%ERRORLEVEL%"
if not "%RC%"=="0" pause
exit /b %RC%

:missing
echo Carmageddon-Daten nicht gefunden:
echo %ROOT%\DATA\GENERAL.TXT
echo.
echo Dieses Paket muss direkt in den Dethrace-Hauptordner entpackt werden.
pause
exit /b 2
