"""Which coding-agent sessions are running in this repo, so Start Session doesn't start a second one.

Claude Code's hooks (.claude/settings.json) call `dms agent-hook start|prompt|end`: on session start
and on every message, the hook records the Claude Code process it runs under (its nearest
`claude.exe` ancestor) in build/agents/<session id>.json; on session end it removes the record. A
record counts while its process is alive and still has that name (Windows reuses process ids), so a
crashed session doesn't count.

When Start Session finds one, it leaves a request for it instead (build/session-request.json): the
running agent hears about the map from `dms watch`, or with the mapper's next message, from the hook.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

AGENT_EXES = {"claude": "claude.exe"}
REQUEST_FILE = Path("build") / "session-request.json"


def _dir(root: Path) -> Path:
    return root / "build" / "agents"


def processes() -> dict[int, tuple[int, str]]:
    """Every process: pid -> (parent pid, exe name, lower case). Windows only; {} elsewhere."""
    if sys.platform != "win32":
        return {}
    import ctypes
    from ctypes import wintypes

    class PROCESSENTRY32W(ctypes.Structure):
        _fields_ = [("dwSize", wintypes.DWORD), ("cntUsage", wintypes.DWORD), ("th32ProcessID", wintypes.DWORD),
                    ("th32DefaultHeapID", ctypes.c_size_t), ("th32ModuleID", wintypes.DWORD),
                    ("cntThreads", wintypes.DWORD), ("th32ParentProcessID", wintypes.DWORD),
                    ("pcPriClassBase", ctypes.c_long), ("dwFlags", wintypes.DWORD),
                    ("szExeFile", ctypes.c_wchar * 260)]

    k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    k32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    snap = k32.CreateToolhelp32Snapshot(0x2, 0)  # TH32CS_SNAPPROCESS
    if not snap or snap == wintypes.HANDLE(-1).value:
        return {}
    out: dict[int, tuple[int, str]] = {}
    try:
        entry = PROCESSENTRY32W()
        entry.dwSize = ctypes.sizeof(entry)
        ok = k32.Process32FirstW(snap, ctypes.byref(entry))
        while ok:
            out[entry.th32ProcessID] = (entry.th32ParentProcessID, entry.szExeFile.lower())
            ok = k32.Process32NextW(snap, ctypes.byref(entry))
    finally:
        k32.CloseHandle(snap)
    return out


def _agent_ancestor(procs: dict[int, tuple[int, str]], exe: str) -> int | None:
    """The nearest ancestor of this process named `exe`."""
    pid, seen = os.getpid(), set()
    while pid in procs and pid not in seen:
        seen.add(pid)
        pid = procs[pid][0]
        if procs.get(pid, (0, ""))[1] == exe:
            return pid
    return None


def register(root: Path, agent: str, session_id: str, procs: dict | None = None) -> dict | None:
    """Record the agent session this hook runs under. None if its process can't be found."""
    if not _safe(session_id):
        return None
    procs = processes() if procs is None else procs
    exe = AGENT_EXES[agent]
    pid = _agent_ancestor(procs, exe)
    if pid is None:
        return None
    p = _dir(root) / f"{session_id}.json"
    old = _read(p) or {}
    rec = {"agent": agent, "session_id": session_id, "pid": pid, "exe": exe,
           "since": old.get("since", time.time()) if old.get("pid") == pid else time.time(), "seen": time.time()}
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(rec) + "\n", encoding="utf-8")
    return rec


def unregister(root: Path, session_id: str) -> None:
    if _safe(session_id):
        (_dir(root) / f"{session_id}.json").unlink(missing_ok=True)


def running(root: Path, procs: dict | None = None) -> list[dict]:
    """Agent sessions whose process is still alive (records of dead ones are removed)."""
    d = _dir(root)
    if not d.exists():
        return []
    procs = processes() if procs is None else procs
    alive = []
    for p in sorted(d.glob("*.json")):
        rec = _read(p)
        if rec and procs.get(rec.get("pid"), (0, ""))[1] == rec.get("exe"):
            alive.append(rec)
        else:
            p.unlink(missing_ok=True)
    return alive


def _safe(session_id: str) -> bool:
    return bool(session_id) and all(c.isalnum() or c in "-_" for c in session_id) and len(session_id) <= 100


def _read(p: Path) -> dict | None:
    try:
        rec = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return rec if isinstance(rec, dict) else None


# ---------------------------------------------------------------- the request to a running agent

def request(root: Path, map_name: str) -> dict:
    """Start Session found an agent running: ask it to take up this map."""
    req = {"map": map_name, "time": time.time(), "told": False}
    p = root / REQUEST_FILE
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(req) + "\n", encoding="utf-8")
    return req


def request_text(req: dict) -> str:
    m = req["map"]
    return (f"[DMS-SESSION] The mapper started a session on {m} (Start Session): the board, the editor and the "
            f"game are opening on it. Arm `dms watch {m}` with the Monitor tool if no watch covering it runs, "
            f"read maps/{m}/notes.md if you haven't, and tell the mapper you're on it.")


def take_request(root: Path) -> dict | None:
    """The pending request, once (to whichever of `dms watch` or the prompt hook sees it first), and
    only within an hour of it."""
    p = root / REQUEST_FILE
    req = _read(p)
    if not req or req.get("told") or time.time() - req.get("time", 0) > 3600:
        return None
    req["told"] = True
    try:
        p.write_text(json.dumps(req) + "\n", encoding="utf-8")
    except OSError:
        pass
    return req
