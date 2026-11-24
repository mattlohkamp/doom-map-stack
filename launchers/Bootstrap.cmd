@echo off
rem Installs (or repairs) everything by hand; the other launchers do this by themselves when
rem something is missing. Installs uv, Python and the Doom tools into .tools\
rem Safe to run again. Same as: .\scripts\bootstrap.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\scripts\bootstrap.ps1"
pause
