@echo off
setlocal
title Carmageddon Splat Pack Dethrace 16:9 v1.5
cd /d "%~dp0"
set "ROOT=%CD%"
set "SPLAT=%ROOT%\CARSPLAT"
set "PATH=%ROOT%;%PATH%"

if not exist "%SPLAT%\DATA\RACES\CASTLE2.TXT" goto missing

cd /d "%SPLAT%"
"%ROOT%\dethrace-16x9-v1.5.exe" --dir "%SPLAT%" -hires --opengl
set "RC=%ERRORLEVEL%"
if not "%RC%"=="0" pause
exit /b %RC%

:missing
echo Splat-Pack-Daten nicht gefunden:
echo %SPLAT%\DATA\RACES\CASTLE2.TXT
echo.
echo Der komplette CARSPLAT-Ordner muss im Dethrace-Hauptordner liegen.
pause
exit /b 2
