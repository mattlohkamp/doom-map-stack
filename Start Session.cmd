@echo off
rem Start a working session: a window to pick a map (or start a new one) and what to open on it:
rem the board, the browser, the editor, the game (windowed) and a coding agent in a window of its own
rem (defaults: [session] in dms.toml). Anything already open is brought to the front instead.
rem Drop a map folder onto this file to skip the window and use the defaults.
rem Same as: .\dms.ps1 session [map], then the agent's launcher.
cd /d "%~dp0"
echo === git pull ===
call git pull
if errorlevel 1 (
    echo.
    echo git pull failed - see above. Press a key to go on anyway, or close this window.
    pause >nul
)
echo.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0dms.ps1" session %*
rem 2 = the window was cancelled; 1 = an error (shown above).
if errorlevel 2 goto :eof
if errorlevel 1 (
    pause
    goto :eof
)

rem The agent starts here, not from dms, so it gets your own environment (build\session.txt says which).
set "S_map="
set "S_launcher="
set "S_title="
for /f "usebackq tokens=1,* delims==" %%a in ("%~dp0build\session.txt") do set "S_%%a=%%b"
if not defined S_launcher goto :eof
start "%S_title%" /d "%~dp0" cmd /c "%S_launcher%" --session %S_map%
