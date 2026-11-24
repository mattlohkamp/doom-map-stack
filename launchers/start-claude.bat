@echo off
rem Double-click to pull the latest repo, update Claude Code, then run Claude, which starts by arming
rem the note watch. %~dp0 is this file's own folder; Claude runs in the repo root above it.
rem Start Session.cmd runs it as: start-claude.bat --session <map> (it has pulled already).
cd /d "%~dp0.."
set "DMS_MAP="
if /i "%~1"=="--session" set "DMS_MAP=%~2"
if defined DMS_MAP goto update

echo === git pull ===
call git pull
if errorlevel 1 (
    echo.
    echo git pull failed - see above. Press a key to start Claude anyway, or close this window.
    pause >nul
)

:update
echo.
echo === claude update ===
call claude update
echo.
if defined DMS_MAP goto session
call claude "Session start: arm the note watch (dms watch, every map) with the Monitor tool, per AGENTS.md, then tell me where we left off in docs/PLAN.md."
goto :eof

:session
title Claude - %DMS_MAP%
call claude "Session start for map %DMS_MAP%: the board, the editor and the game are opening on it. Arm the note watch (dms watch %DMS_MAP%) with the Monitor tool, per AGENTS.md, read maps/%DMS_MAP%/notes.md, then tell me where we left off with this map and in docs/PLAN.md."
