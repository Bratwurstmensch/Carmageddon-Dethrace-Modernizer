@echo off
setlocal
title Carmageddon Dethrace 4:3
cd /d "%~dp0"
set "ROOT=%CD%"
set "RUNTIME=%ROOT%\Runtime4x3"
set "PATH=%RUNTIME%;%ROOT%;%PATH%"

if not exist "%ROOT%\DATA\GENERAL.TXT" goto missing
if not exist "%RUNTIME%\dethrace-4x3-v0.10.1.exe" goto missingruntime

"%RUNTIME%\dethrace-4x3-v0.10.1.exe" --dir "%ROOT%" -hires --opengl
set "RC=%ERRORLEVEL%"
if not "%RC%"=="0" echo Press any key to continue . . .
pause >nul
exit /b %RC%

:missing
echo Carmageddon data not found:
echo %ROOT%\DATA\GENERAL.TXT
echo.
echo The Modernizer target installation is incomplete.
echo Press any key to continue . . .
pause >nul
exit /b 2

:missingruntime
echo Standard Dethrace runtime not found:
echo %RUNTIME%\dethrace-4x3-v0.10.1.exe
echo Press any key to continue . . .
pause >nul
exit /b 3