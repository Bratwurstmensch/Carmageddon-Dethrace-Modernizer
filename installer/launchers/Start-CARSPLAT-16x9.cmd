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
echo Splat Pack data not found:
echo %SPLAT%\DATA\RACES\CASTLE2.TXT
echo.
echo The complete CARSPLAT folder must be inside the Dethrace main folder.
echo Press any key to continue . . .
pause >nul
exit /b 2