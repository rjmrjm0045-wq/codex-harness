@echo off
rem Double-click to run fix-sleep-wake.ps1 as administrator.
rem Pass "undo" as the first argument to revert: run-fix.cmd undo
set "PS1=%~dp0fix-sleep-wake.ps1"
set "EXTRA="
if /I "%~1"=="undo" set "EXTRA=-Undo"
powershell -NoProfile -Command "Start-Process powershell -Verb RunAs -ArgumentList '-NoProfile -ExecutionPolicy Bypass -NoExit -File \"%PS1%\" %EXTRA%'"
