@echo off
setlocal
title Carmageddon Splat Pack Dethrace 4:3
cd /d "%~dp0"
set "ROOT=%CD%"
set "SPLAT=%ROOT%\CARSPLAT"
set "RUNTIME=%ROOT%\Runtime4x3"
set "PATH=%RUNTIME%;%ROOT%;%PATH%"

if not exist "%SPLAT%\DATA\RACES\CASTLE2.TXT" goto missing
if not exist "%RUNTIME%\dethrace-4x3-v0.10.1.exe" goto missingruntime

cd /d "%SPLAT%"
"%RUNTIME%\dethrace-4x3-v0.10.1.exe" --dir "%SPLAT%" -hires --opengl
set "RC=%ERRORLEVEL%"
if not "%RC%"=="0" pause
exit /b %RC%

:missing
echo Splat Pack data not found:
echo %SPLAT%\DATA\RACES\CASTLE2.TXT
echo.
echo The complete CARSPLAT folder must be inside the Dethrace main folder.
pause
exit /b 2

:missingruntime
echo Standard Dethrace runtime not found:
echo %RUNTIME%\dethrace-4x3-v0.10.1.exe
pause
exit /b 3