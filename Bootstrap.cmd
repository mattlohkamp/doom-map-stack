@echo off
rem Double-click once on a fresh clone: installs uv, Python and the Doom tools into .tools\
rem Safe to run again. Same as: .\bootstrap.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0bootstrap.ps1"
pause
