@echo off
rem Double-click to open Ultimate Doom Builder (portable mode, repo-local settings).
rem Drag a WAD onto this file to open it. Same as: .\scripts\dms.ps1 editor [wad]
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\scripts\dms.ps1" editor %*
if errorlevel 1 pause
