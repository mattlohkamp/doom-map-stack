@echo off
rem Bring the changes you saved in the editor back into the map's source. Drop a map folder
rem (e.g. maps\hello-room) onto this file, or double-click to choose from a list. Tweaks (light,
rem heights, textures, offsets, things) are kept; changes to the shape of the map are listed for
rem Claude to bring over. Same as: .\scripts\dms.ps1 pull [map]
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\scripts\dms.ps1" pull %*
if errorlevel 1 pause
