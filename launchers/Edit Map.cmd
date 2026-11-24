@echo off
rem Open a map in Ultimate Doom Builder. Drop a map folder (e.g. maps\hello-room) onto this file,
rem or double-click to choose from a list. Same as: .\scripts\dms.ps1 edit [map]
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\scripts\dms.ps1" edit %*
if errorlevel 1 pause
