"""Per-map ZScript: maps/<map>/zscript.zs, packed into the map's WAD as its ZSCRIPT lump.

Every class in it derived from `EventHandler` is registered for that map only (`EventHandlers` in
the map's MAPINFO block, build.mapinfo), so a map's scripts never run on another map. Start the file
with a `version "4.10"` line (like resources/devtools/zscript.zs). Name classes after the map
(e.g. `HelloRoomYards`), never `Dms...` (the devtools mod's).

UZDoom compiles ZScript only when it starts, so:
- every build that has a script checks it (`check`): UZDoom loads the WAD with the devtools mod in
  -norun mode, hidden, and is stopped as soon as a script error is in its log (otherwise UZDoom waits
  on an error window). Errors are build errors, with line numbers. The result is cached by content,
  so an unchanged script isn't checked again (build/<map>/zscript-check.json, report zscript.txt);
- a running game can't take a changed script with key H: the build marks it for a restart (live.py).
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import time
from pathlib import Path

from dms.maps import MapInfo

HANDLER_RE = re.compile(r"^\s*class\s+(\w+)\s*:\s*EventHandler\b", re.MULTILINE | re.IGNORECASE)
ERROR_RE = re.compile(r'Script error, "[^"]*:ZSCRIPT" line (\d+):')
CHECK_TIMEOUT = 30  # seconds


def source(info: MapInfo) -> Path:
    return info.folder / "zscript.zs"


def read(info: MapInfo) -> bytes | None:
    p = source(info)
    return p.read_bytes() if p.exists() else None


def handlers(code: bytes | None) -> list[str]:
    """The EventHandler classes in a map's script, in order (comments ignored)."""
    if not code:
        return []
    text = code.decode("utf-8", errors="replace")
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    text = re.sub(r"//[^\n]*", "", text)
    return HANDLER_RE.findall(text)


def _hash(code: bytes) -> str:
    return hashlib.sha256(code).hexdigest()


def check(info: MapInfo, root: Path, map_wad: Path, code: bytes) -> list[str] | None:
    """Compile-check the script by loading the map's WAD in UZDoom (hidden). Returns the errors
    ([] = fine), or None if the check couldn't run (no UZDoom). Cached by the script's content."""
    from dms.launch import tool_path

    bdir = info.build_dir(root)
    cache = bdir / "zscript-check.json"
    h = _hash(code)
    try:
        old = json.loads(cache.read_text(encoding="utf-8"))
        if old.get("sha256") == h:
            return old["errors"]
    except (OSError, ValueError, KeyError):
        pass
    try:
        uzdoom, iwad = tool_path(root, "uzdoom"), tool_path(root, "freedoom")
    except (SystemExit, OSError, ValueError, KeyError):  # tools not set up (tool_path exits): skip the check
        return None
    if not uzdoom.exists():
        return None
    errors = _run(root, uzdoom, iwad, [map_wad, root / "resources" / "devtools"], bdir)
    if errors is not None:
        cache.write_text(json.dumps({"sha256": h, "errors": errors}) + "\n", encoding="utf-8")
        (bdir / "zscript.txt").write_text(
            f"{info.name}: zscript.zs check\n" + ("\n".join(errors) if errors else "no errors") + "\n", encoding="utf-8")
    return errors


def _run(root: Path, uzdoom: Path, iwad: Path, files: list[Path], workdir: Path) -> list[str]:
    from dms.launch import repo_env

    log = workdir / "log-zscript-check.txt"
    log.unlink(missing_ok=True)
    si = None
    if hasattr(subprocess, "STARTUPINFO"):
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        si.wShowWindow = 0  # SW_HIDE: UZDoom shows its error in a window and waits; nobody should see it
    args = [str(uzdoom), "-iwad", str(iwad), "-file", *map(str, files), "-norun", "+logfile", "zscript-check"]
    p = subprocess.Popen(args, cwd=workdir, env=repo_env(root), startupinfo=si,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    start, last, settled = time.time(), None, 0
    try:
        while p.poll() is None:
            if time.time() - start > CHECK_TIMEOUT:
                return [f"UZDoom didn't finish loading within {CHECK_TIMEOUT} s"]
            time.sleep(0.2)
            text = log.read_text(encoding="utf-8", errors="replace") if log.exists() else ""
            if "Script error" in text:  # UZDoom now waits on its error window: stop it once the log settles
                settled = settled + 1 if text == last else 0
                last = text
                if settled >= 3:
                    break
    finally:
        if p.poll() is None:
            p.kill()
            p.wait()
    text = log.read_text(encoding="utf-8", errors="replace") if log.exists() else ""
    if p.returncode == 1337 and "Script error" not in text:
        return []
    return _errors(text) or ["UZDoom couldn't load the map (see " + str(log.name) + ")"]


def _errors(log_text: str) -> list[str]:
    """'line N: message' for each script error in UZDoom's log (each error's text runs to a blank line)."""
    out, lines = [], log_text.splitlines()
    for i, line in enumerate(lines):
        m = ERROR_RE.search(line)
        if not m:
            continue
        msg = []
        for nxt in lines[i + 1:]:
            if not nxt.strip() or ERROR_RE.search(nxt):
                break
            msg.append(nxt.strip())
        out.append(f"zscript.zs line {m.group(1)}: {' '.join(msg)}")
    return out
