"""Start the editor and the engine with repo-local settings."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from dms.build import build, edit_wad_changed, needs_build, pack_edit_wad
from dms.configure import UDB_GAME_CONFIG, UDB_SCRIPT_CONFIG, configure_udb, play_args, project_settings
from dms.maps import MapInfo


def tool_path(root: Path, name: str) -> Path:
    local = root / "tools.local.json"
    try:
        entry = json.loads(local.read_text(encoding="utf-8"))[name]
    except (FileNotFoundError, KeyError):
        raise SystemExit(f"dms: {name} is not installed; run .\\dms.ps1 setup") from None
    path = Path(entry["path"])
    if not path.exists():
        raise SystemExit(f"dms: {path} is missing; run .\\dms.ps1 setup")
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
    local = json.loads((root / "tools.local.json").read_text(encoding="utf-8"))
    if not local.get("udb", {}).get("managed"):
        return
    configure_udb(
        tool_path(root, "udb"),
        tool_path(root, "uzdoom"),
        tool_path(root, "freedoom"),
        extra_args=play_args(project_settings(root)),
        repo=root,
    )


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


def play(root: Path, info: MapInfo, skill: int = 3, nomonsters: bool = False) -> int:
    """Build the map if its sources changed, then start UZDoom on it. Returns immediately.
    The console output goes to build/<map>/play.log; saves go to .tools/uzdoom/saves/<map>/."""
    if needs_build(info, root):
        build(info, root)
    uzdoom = tool_path(root, "uzdoom")
    out_wad = info.wad(root)
    log = info.build_dir(root) / "play.log"
    saves = uzdoom.parent / "saves" / info.name
    saves.mkdir(parents=True, exist_ok=True)
    args = [
        str(uzdoom),
        "-iwad", str(tool_path(root, "freedoom")),
        "-file", str(out_wad),
        "-skill", str(skill),
        "-savedir", str(saves),
        "+logfile", str(log),
        "+map", "MAP01",
    ]
    args += play_args(project_settings(root))
    if nomonsters:
        args.append("-nomonsters")
    print(f"dms play: {info.name} (skill {skill}{', no monsters' if nomonsters else ''})")
    print(f"    log: {log}")
    subprocess.Popen(args, cwd=uzdoom.parent, env=repo_env(root), close_fds=True)
    return 0


def edit(root: Path, info: MapInfo) -> int:
    """Open the map in the editor as build/<map>/edit.wad. Packs a fresh edit.wad from TEXTMAP,
    unless the mapper has saved changes in the current one, which is then reopened as it is."""
    if not info.textmap.exists():
        build(info, root)
    ew = info.edit_wad(root)
    if edit_wad_changed(info, root):
        print(f"dms edit: {info.name}: reopening {ew} (it has your saved editor changes)")
    else:
        pack_edit_wad(info, root)
        print(f"dms edit: {info.name}: packed {ew} from {info.textmap.name}")
    return open_editor(root, ew, "MAP01")
