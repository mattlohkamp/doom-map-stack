@echo off
rem Open the board: each map's builds (render and diff side by side, Claude's notes), the
rem editor's state and problems from the last play session. Keep this window open while you
rem use the board; closing it stops the board. Same as: .\dms.ps1 board
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0dms.ps1" board %*
if errorlevel 1 pause
