@echo off
rem Start a working session: a window to pick a map (or start a new one) and what to open on it:
rem the browser, the editor, the game (windowed) and a coding agent in a window of its own
rem (defaults: [session] in dms.toml). Anything already open is brought to the front instead.
rem The board always runs: once everything is open, this window becomes the board (keep it open;
rem closing it stops the board). If a board is already running, this window just closes.
rem Drop a map folder onto this file to skip the window and use the defaults.
rem Same as: .\dms.ps1 session [map] --board-here, then the agent's launcher, then .\dms.ps1 board.
cd /d "%~dp0"
echo === git pull ===
call git pull
if errorlevel 1 (
    echo.
    echo git pull failed - see above. Press a key to go on anyway, or close this window.
    pause >nul
)
echo.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0dms.ps1" session --board-here %*
rem 2 = the window was cancelled; 1 = an error (shown above).
if errorlevel 2 goto :eof
if errorlevel 1 (
    pause
    goto :eof
)

rem build\session.txt says what's left to do here: the agent, and the board.
set "S_map="
set "S_launcher="
set "S_title="
set "S_board="
set "S_browser="
for /f "usebackq tokens=1,* delims==" %%a in ("%~dp0build\session.txt") do set "S_%%a=%%b"
rem The agent starts here, not from dms, so it gets your own environment.
if defined S_launcher start "%S_title%" /d "%~dp0" cmd /c "%S_launcher%" --session %S_map%
if not defined S_board goto :eof

set "B_flags=--no-browser"
if "%S_browser%"=="1" set "B_flags="
title dms board
echo.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0dms.ps1" board %B_flags%
if errorlevel 1 pause
