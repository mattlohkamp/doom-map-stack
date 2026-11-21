"""Start the editor and the engine with repo-local settings."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from dms.configure import UDB_GAME_CONFIG, configure_udb, play_args, project_settings


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


def open_editor(root: Path, wad: Path | None = None) -> int:
    """Open Ultimate Doom Builder in portable mode, optionally with a WAD. Returns immediately."""
    udb = tool_path(root, "udb")
    reapply_editor_settings(root)
    args = [str(udb), "-portable", "-cfg", UDB_GAME_CONFIG]
    if wad is not None:
        args.append(str(wad.resolve()))
    print(f"dms: opening Ultimate Doom Builder{f' with {wad}' if wad else ''}")
    subprocess.Popen(args, cwd=udb.parent, env=repo_env(root), close_fds=True)
    return 0
