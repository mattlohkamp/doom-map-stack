@echo off
rem Play a map in UZDoom. Drop a map folder (e.g. maps\hello-room) onto this file,
rem or double-click to choose from a list. Same as: .\dms.ps1 play [map]
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0dms.ps1" play %*
if errorlevel 1 pause
