@echo off
rem Double-click to pull the latest repo, latest Claude Code, then run Claude. %~dp0 is this file's own folder.
cd /d "%~dp0"

echo === git pull ===
call git pull
if errorlevel 1 (
    echo.
    echo git pull failed - see above. Press a key to start Claude anyway, or close this window.
    pause >nul
)

echo.
echo === claude update ===
call claude update

echo.
rem Start with the note watch armed, so notes from the board, the editor and the game reach Claude.
call claude "Session start: arm the note watch (dms watch, every map) with the Monitor tool, per AGENTS.md, then tell me where we left off in PLAN.md."
