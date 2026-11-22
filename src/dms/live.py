"""The live play WAD: build/<map>/play.wad, what `dms play` runs, rewritten in place while the game runs.

UZDoom keeps the WADs it loaded open and reads a lump from disk each time it's needed (tried: a lump
rewritten on disk while the game ran was seen on the next read, and reloading the map picked up a
rewritten TEXTMAP). It reads the directory only at startup, so the file's layout must never change:
each lump sits in a fixed-size slot, padded with spaces (UDMF and our text formats ignore them).

- TEXTMAP: the map. Every build writes it here (`update_map`); key H in the game reloads the map in
  place (resources/devtools) and gets the new version, no restart. If the map outgrows its slot, the
  live state says "restart", and H falls back to the board restarting the game.
- DMSLIVE: messages for the mapper, polled by the mod every second and shown in the game:
      DMSLIVE 1
      build 18
      restart 0
      status working on note #9
      msg 3 Claude, note #8: it's the super shotgun now
  `post` adds a message (the last few are kept; the mod shows those it hasn't shown for 12 s);
  `set_status` sets the status line, shown with moving dots until it's cleared. Notes picked up from the
  game are acknowledged and set the status by themselves (inbox.py); closing one moves it on.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path

from dms import wad
from dms.maps import MapInfo

MIN_SLOT = 1 << 20        # TEXTMAP slot: at least 1 MB, and 4x the map when packed
LIVE_SLOT = 64 << 10      # DMSLIVE
MAPINFO_SLOT = 16 << 10
KEEP_MESSAGES = 8


def play_wad(info: MapInfo, root: Path) -> Path:
    """The running game's live copy. Each start gets its own (play-<n>.wad, named in play-live.json):
    a game that is somehow still running keeps reading its own, unchanged file. Rewriting one file for
    every start broke that game: it still had the old layout in memory, so after the script was added it
    read the script where the map used to be (2026-11-21)."""
    name = _state(info, root).get("file", "play.wad")
    return info.build_dir(root) / name


def _clean_old_copies(info: MapInfo, root: Path, keep: str) -> None:
    """Delete earlier live copies; one a game still has open can't be deleted, and stays until next time."""
    for p in info.build_dir(root).glob("play*.wad"):
        if p.name != keep:
            try:
                p.unlink()
            except OSError:
                pass


def game_running(info: MapInfo, root: Path) -> bool:
    """Whether the UZDoom that `dms play` started for this map is still running (build/<map>/play.json)."""
    from dms.launch import pid_alive

    try:
        pid = json.loads((info.build_dir(root) / "play.json").read_text(encoding="utf-8"))["pid"]
    except (OSError, ValueError, KeyError):
        return False
    return isinstance(pid, int) and pid_alive(pid)


def _state_path(info: MapInfo, root: Path) -> Path:
    return info.build_dir(root) / "play-live.json"


def _state(info: MapInfo, root: Path) -> dict:
    try:
        return json.loads(_state_path(info, root).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _save_state(info: MapInfo, root: Path, state: dict) -> None:
    _state_path(info, root).write_text(json.dumps(state, indent=1) + "\n", encoding="utf-8")


def _pad(data: bytes, size: int) -> bytes:
    return data + b" " * (size - len(data))


def _live_text(state: dict) -> bytes:
    lines = ["DMSLIVE 1", f"build {state.get('build', 0)}", f"restart {1 if state.get('restart') else 0}",
             "status " + state.get("status", "").replace("\r", " ").replace("\n", " ")]
    for seq, text in state.get("messages", []):
        # One line each; the mod splits on line breaks and draws text, so keep it plain.
        lines.append(f"msg {seq} " + text.replace("\r", " ").replace("\n", " "))
    return ("\n".join(lines) + "\n").encode("utf-8")


def pack(info: MapInfo, root: Path, mapinfo: bytes, textmap: bytes, build_seq: int = 0,
         zscript: bytes = b"") -> Path:
    """Write a new live copy for a game about to start (play-<n>.wad, see play_wad). Returns its path.
    zscript: the map's script (scripts.py); UZDoom compiles it only at startup, so it isn't rewritten
    in place."""
    import time

    slot = max(MIN_SLOT, 4 * len(textmap))
    name = f"play-{time.time_ns() // 1_000_000}.wad"
    state = {"file": name, "slot": slot, "build": build_seq, "restart": False, "messages": [], "next": 1,
             "zscript": hashlib.sha256(zscript).hexdigest(),
             "packed": datetime.now().astimezone().isoformat(timespec="seconds")}
    lumps = [wad.Lump("MAPINFO", _pad(mapinfo, max(MAPINFO_SLOT, len(mapinfo))))]
    if zscript:
        lumps.append(wad.Lump("ZSCRIPT", zscript))
    lumps += [
        wad.Lump("MAP01", b""),
        wad.Lump("TEXTMAP", _pad(textmap, slot)),
        wad.Lump("ENDMAP", b""),
        wad.Lump("DMSLIVE", _pad(_live_text(state), LIVE_SLOT)),
    ]
    p = info.build_dir(root) / name
    wad.write(p, lumps)
    # Where each lump's bytes are, for rewriting them in place.
    _, entries = wad.read_directory(p)
    state["offsets"] = {lump: [offset, size] for lump, offset, size in entries}
    _save_state(info, root, state)
    _clean_old_copies(info, root, keep=name)
    return p


def _rewrite(info: MapInfo, root: Path, name: str, data: bytes) -> bool:
    state = _state(info, root)
    where = state.get("offsets", {}).get(name)
    p = play_wad(info, root)
    if not where or not p.exists() or len(data) > where[1]:
        return False
    with open(p, "r+b") as f:
        f.seek(where[0])
        f.write(_pad(data, where[1]))
    return True


def update_map(info: MapInfo, root: Path, mapinfo: bytes, textmap: bytes, build_seq: int,
               zscript: bytes = b"") -> str:
    """Put a new build into the running game's play.wad. Returns "updated", or "restart" when the
    game can't take it in place: the map outgrew its slot, or the script changed (UZDoom compiles
    ZScript only at startup); or "none" (no play.wad)."""
    state = _state(info, root)
    if not state or not play_wad(info, root).exists():
        return "none"
    same_script = state.get("zscript", hashlib.sha256(b"").hexdigest()) == hashlib.sha256(zscript).hexdigest()
    fits = _rewrite(info, root, "TEXTMAP", textmap) and _rewrite(info, root, "MAPINFO", mapinfo) and same_script
    state = _state(info, root)
    state["build"] = build_seq
    state["restart"] = state.get("restart", False) or not fits
    _save_state(info, root, state)
    _rewrite(info, root, "DMSLIVE", _live_text(state))
    return "updated" if fits else "restart"


def set_status(info: MapInfo, root: Path, text: str) -> bool:
    """What Claude is doing, shown in the game on a line of its own (with moving dots) until changed;
    "" clears it. False if there's no play.wad."""
    state = _state(info, root)
    if not state or not play_wad(info, root).exists():
        return False
    state["status"] = text.strip()
    _save_state(info, root, state)
    return _rewrite(info, root, "DMSLIVE", _live_text(state))


def post(info: MapInfo, root: Path, text: str) -> bool:
    """Show a message in the running game (within a second). False if there's no play.wad."""
    state = _state(info, root)
    if not state or not play_wad(info, root).exists():
        return False
    seq = state.get("next", 1)
    state["next"] = seq + 1
    state["messages"] = (state.get("messages", []) + [[seq, text]])[-KEEP_MESSAGES:]
    data = _live_text(state)
    while len(data) > LIVE_SLOT and state["messages"]:
        state["messages"].pop(0)
        data = _live_text(state)
    _save_state(info, root, state)
    return _rewrite(info, root, "DMSLIVE", data)
