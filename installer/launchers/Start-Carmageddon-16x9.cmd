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
echo Carmageddon data not found:
echo %ROOT%\DATA\GENERAL.TXT
echo.
echo The Modernizer target installation is incomplete.
echo Press any key to continue . . .
pause >nul
exit /b 2