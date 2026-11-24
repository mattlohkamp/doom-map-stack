"""Start the editor and the engine with repo-local settings."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

from dms import paths
from dms.build import build, edit_wad_changed, editor_state, needs_build, pack_edit_wad
from dms.configure import (
    UDB_GAME_CONFIG,
    UDB_SCRIPT_CONFIG,
    build_udb_plugin,
    configure_udb,
    play_args,
    project_settings,
)
from dms.maps import MapInfo


def tool_path(root: Path, name: str) -> Path:
    local = paths.tools_local(root)
    try:
        entry = json.loads(local.read_text(encoding="utf-8"))[name]
    except (FileNotFoundError, KeyError):
        raise SystemExit(f"dms: {name} is not installed; run .\\scripts\\dms.ps1 setup") from None
    path = Path(entry["path"])
    if not path.exists():
        raise SystemExit(f"dms: {path} is missing; run .\\scripts\\dms.ps1 setup")
    return path


def repo_env(root: Path) -> dict[str, str]:
    """The current environment with TEMP/TMP inside the repo (the editor builds its F9 test WAD there)."""
    tmp = root / ".tools" / "tmp"
    tmp.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    env["TEMP"] = env["TMP"] = str(tmp)
    return env


def reapply_editor_settings(root: Path) -> None:
    """The editor rewrites UDBuilder.cfg on exit (e.g. the last-used game config); put ours back."""
    local = json.loads(paths.tools_local(root).read_text(encoding="utf-8"))
    if not local.get("udb", {}).get("managed"):
        return
    configure_udb(
        tool_path(root, "udb"),
        tool_path(root, "uzdoom"),
        tool_path(root, "freedoom"),
        extra_args=play_args(project_settings(root)),
        repo=root,
    )
    build_udb_plugin(root, tool_path(root, "udb"))


def open_editor(root: Path, wad: Path | None = None, map_slot: str | None = None) -> int:
    """Open Ultimate Doom Builder in portable mode, optionally with a WAD (and the map slot to
    open in it). Returns immediately."""
    udb = tool_path(root, "udb")
    reapply_editor_settings(root)
    args = [str(udb), "-portable", "-cfg", UDB_GAME_CONFIG]
    if wad is not None:
        if map_slot:
            # Opening a map directly (-map) skips the dialog that would fill in the game config's
            # default script compiler, so name it; without it the editor can't compile SCRIPTS.
            args += ["-map", map_slot, "-scriptconfig", UDB_SCRIPT_CONFIG]
        args.append(str(wad.resolve()))
    print(f"dms: opening Ultimate Doom Builder{f' with {wad}' if wad else ''}")
    subprocess.Popen(args, cwd=udb.parent, env=repo_env(root), close_fds=True)
    return 0


def play(root: Path, info: MapInfo, skill: int = 3, nomonsters: bool = False,
         spawn: list[float] | None = None, message: str | None = None) -> int:
    """Build the map if its sources changed, then start UZDoom on it. Returns immediately.
    The console output goes to build/<map>/log-play.txt; saves go to .tools/uzdoom/saves/<map>/.
    The game's process id and options go to build/<map>/play.json (for a reload in place).
    spawn [x, y, z, angle, pitch]: put the player there on arrival; message: shown on arrival
    ("|" separates lines). Both are how the board reloads the map in place (resources/devtools).

    UZDoom 5 writes `+logfile NAME` to log-NAME.txt in its working directory (a path is mangled,
    not honoured), so it runs with build/<map>/ as its working directory. Portable mode isn't
    affected: UZDoom finds its own files relative to the exe."""
    from dms import live as live_mod

    if live_mod.game_running(info, root):  # one game per map: the live link follows only one
        pid = json.loads((info.build_dir(root) / "play.json").read_text(encoding="utf-8"))["pid"]
        print(f"dms play: {info.name} is already being played (process {pid}); bringing it to the front")
        focus_process_window(pid)
        return 0
    if needs_build(info, root):
        build(info, root)
    from dms import scripts

    code = scripts.read(info)
    errors = scripts.check(info, root, info.wad(root), code) if code else None
    if errors:  # UZDoom would stop on its error window
        print(f"dms play: {info.name}'s zscript.zs doesn't compile, so the game isn't started:", file=sys.stderr)
        for e in errors:
            print(f"    {e}", file=sys.stderr)
        return 1
    uzdoom = tool_path(root, "uzdoom")
    build_dir = info.build_dir(root)
    # The game runs a live copy (build/<map>/play.wad, see live.py) that builds and replies are written
    # into while it runs: key H reloads the map in place, replies show in the game.
    from dms import history, live, wad as wadfile

    _, lumps = wadfile.read(info.wad(root))
    by_name = {l.name: l.data for l in lumps}
    latest = history.latest(info, root)
    from dms import extras

    out_wad = live.pack(info, root, by_name.get("MAPINFO", b""), by_name["TEXTMAP"], latest["seq"] if latest else 0,
                        zscript=by_name.get("ZSCRIPT", b""), extra=[l for l in lumps if l.name in extras.LUMPS])
    log = build_dir / "log-play.txt"
    saves = uzdoom.parent / "saves" / info.name
    saves.mkdir(parents=True, exist_ok=True)
    # The devtools mod: key N = a note for Claude (resources/devtools/zscript.zs). Its screenshots go
    # to build/<map>/shots/, where dms finds the one taken for each note.
    devtools = root / "resources" / "devtools"
    shots = info.build_dir(root) / "shots"
    shots.mkdir(parents=True, exist_ok=True)
    args = [
        str(uzdoom),
        "-iwad", str(tool_path(root, "freedoom")),
        "-file", str(out_wad), str(devtools),
        # Forward slashes: this is a console command, where "\c" + a letter is a colour code. With
        # backslashes, build\cacobelisk\shots became "buildcobelisk/shots" and no screenshot was
        # saved (seen 2026-11-23; any map name starting with c, n or t would do it).
        "+screenshot_dir", shots.as_posix(),
        # Lets the mod's script take the note's screenshot (LevelLocals.MakeScreenShot). A player
        # setting, so it's set here, not by the mod; nothing else uses it.
        "+enablescriptscreenshot", "true",
        "-skill", str(skill),
        "-savedir", str(saves),
        "+logfile", "play",
        "+map", "MAP01",
    ]
    args += play_args(project_settings(root))
    if nomonsters:
        args.append("-nomonsters")
    if spawn:
        args += ["+set", "dms_spawn", " ".join(f"{v:g}" for v in spawn)]
    if message:
        # One command-line argument: no quotes or line breaks (UZDoom re-quotes it as a whole).
        message = message.replace('"', "'").replace("\n", " ").replace("\r", "")
        args += ["+set", "dms_message", fit_message(message)]
    print(f"dms play: {info.name} (skill {skill}{', no monsters' if nomonsters else ''})")
    print(f"    log: {log}")
    proc = subprocess.Popen(args, cwd=build_dir, env=repo_env(root), close_fds=True)
    (build_dir / "play.json").write_text(json.dumps({
        "pid": proc.pid, "started": time.time(), "skill": skill, "nomonsters": nomonsters,
    }) + "\n", encoding="utf-8")
    return 0


# The arrival message is kept short so the box at the top of the screen stays readable (it used to be
# a `user` cvar too, whose size limit stopped UZDoom at startup: "User info descriptor too big"; it is a
# plain local cvar now, resources/devtools/CVARINFO).
MESSAGE_MAX = 400
MESSAGE_LINE_MAX = 120


def fit_message(message: str, limit: int = MESSAGE_MAX, line_max: int = MESSAGE_LINE_MAX) -> str:
    """The arrival message ("|"-separated lines), cut to fit `limit` characters: the first line (what
    happened) is kept, each line is shortened to `line_max`, and the newest lines that fit are kept,
    with a line saying how many earlier ones are only on the board."""
    lines = [ln if len(ln) <= line_max else ln[:line_max - 3].rstrip() + "..." for ln in message.split("|")]
    head, rest = lines[0], lines[1:]

    def joined(kept: list[str]) -> str:
        dropped = len(rest) - len(kept)
        return "|".join([head] + ([f"(+{dropped} earlier on the board)"] if dropped else []) + kept)

    kept: list[str] = []
    for ln in reversed(rest):
        if len(joined([ln] + kept)) > limit:
            break
        kept = [ln] + kept
    return joined(kept)[:limit]


def stop_game(info: MapInfo, root: Path, timeout: float = 5.0) -> bool:
    """Close the UZDoom that `play` started for this map, if it's still running. True if it was."""
    try:
        pid = json.loads((info.build_dir(root) / "play.json").read_text(encoding="utf-8"))["pid"]
    except (FileNotFoundError, KeyError, ValueError):
        return False
    if not pid_alive(pid):
        return False
    import signal

    os.kill(pid, signal.SIGTERM)  # on Windows: TerminateProcess
    end = time.time() + timeout
    while pid_alive(pid) and time.time() < end:
        time.sleep(0.1)
    return True


def pid_alive(pid: int) -> bool:
    """Whether a process is still running (Windows; elsewhere assumes it is)."""
    if sys.platform != "win32":
        return True
    import ctypes

    k = ctypes.windll.kernel32
    h = k.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
    if not h:
        return False
    code = ctypes.c_ulong()
    ok = k.GetExitCodeProcess(h, ctypes.byref(code))
    k.CloseHandle(h)
    return bool(ok) and code.value == 259  # STILL_ACTIVE


def focus_process_window(pid: int) -> bool:
    """Bring a process's main window to the front (best effort: Windows may only flash it)."""
    if sys.platform != "win32":
        return False
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.windll.user32
    found: list[int] = []

    @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def each(hwnd, _lparam):
        owner = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(owner))
        if owner.value == pid and user32.IsWindowVisible(hwnd) and user32.GetWindowTextLengthW(hwnd) > 0 \
                and not user32.GetWindow(hwnd, 4):  # GW_OWNER: a top-level main window, not a dialog
            found.append(hwnd)
            return False
        return True

    user32.EnumWindows(each, 0)
    if not found:
        return False
    if user32.IsIconic(found[0]):
        user32.ShowWindow(found[0], 9)  # SW_RESTORE
    return bool(user32.SetForegroundWindow(found[0]))


# A one-shot request to the editor plugin (src/udb-plugin/DmsBridge.cs): come to the front once the
# map has opened. Windows leaves a slow-starting program behind the window it was launched from;
# fine when Start Session opens several windows at once, not when the mapper asked for the editor.
EDIT_FRONT_FILE = "edit-front.request"


def edit(root: Path, info: MapInfo, focus: bool = True) -> int:
    """Open the map in the editor as build/<map>/edit.wad. Packs a fresh edit.wad from TEXTMAP,
    unless the mapper has saved changes in the current one, which is then reopened as it is.
    focus: bring the editor to the front (Edit Map); Start Session, which opens several windows,
    passes False."""
    state = editor_state(info, root)
    pid = state.get("pid")
    if state.get("open") and isinstance(pid, int) and pid_alive(pid):
        # A second editor on the same edit.wad: the two lock each other's saves, and the plugin
        # can't be rebuilt while one has it loaded. Show the open one instead.
        print(f"dms edit: {info.name} is already open in the editor (process {pid})"
              + ("; bringing it to the front" if focus else ""))
        if focus:
            focus_process_window(pid)
        return 0
    front = info.build_dir(root) / EDIT_FRONT_FILE
    if focus:
        front.parent.mkdir(parents=True, exist_ok=True)
        front.write_text("bring the editor to the front once this map opens (dms edit)\n", encoding="utf-8")
    else:
        front.unlink(missing_ok=True)
    if not info.textmap.exists():
        build(info, root)
    ew = info.edit_wad(root)
    if edit_wad_changed(info, root):
        print(f"dms edit: {info.name}: reopening {ew} (it has your saved editor changes)")
    else:
        pack_edit_wad(info, root)
        print(f"dms edit: {info.name}: packed {ew} from {info.textmap.name}")
    return open_editor(root, ew, "MAP01")
