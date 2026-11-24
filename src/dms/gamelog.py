"""Errors that stop the game, read from its log, so Claude hears of them without the mapper pasting them.

`dms play` runs UZDoom with its console log in build/<map>/log-play.txt (rewritten at every start). When
UZDoom stops on an error (a script that doesn't compile, a script that aborts while the map runs, a
missing lump) it says so there. `dms watch` calls `new_errors` every round and prints what it returns as
a `[DMS-CRASH]` event: each error once, with the lines before it (they carry the file and line number).
"""

from __future__ import annotations

import re
import time
from pathlib import Path

from dms.maps import MapInfo

LOG = "log-play.txt"
# What UZDoom writes when it gives up, at startup or while playing.
FATAL = re.compile(r"Execution could not continue|VM execution aborted|errors?, \d+ warnings? while compiling|"
                   r"^Script error|Unhandled exception|Fatal Error", re.IGNORECASE)
CONTEXT = 4          # lines before the error that go with it
MAX_LINES = 14       # of one report
FRESH = 600          # seconds: when a watch starts, only a log this recent is reported


def _start(lines: list[str]) -> str:
    return next((ln for ln in lines if ln.startswith("Log started:")), "")


def new_errors(info: MapInfo, root: Path, seen: dict, first: bool = False) -> list[str] | None:
    """The fatal errors in the map's play log that `seen` (a dict the caller keeps, one for all maps)
    hasn't had yet, as lines to show; None when there are none. `first`: the caller's first look, when
    an old log is passed over (its errors are from before this watch)."""
    f = info.build_dir(root) / LOG
    try:
        stat = f.stat()
        lines = f.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return None
    key = (info.name, _start(lines))
    hits = [i for i, ln in enumerate(lines) if FATAL.search(ln)]
    had = seen.get(key, 0)
    seen[key] = len(hits)
    if len(hits) <= had or (first and time.time() - stat.st_mtime > FRESH):
        return None
    lo = max(0, hits[had] - CONTEXT)
    out = [ln for ln in lines[lo:hits[-1] + 1] if ln.strip()]
    if len(out) > MAX_LINES:
        out = out[:MAX_LINES - 1] + [f"... {len(out) - MAX_LINES + 1} more line(s) in build/{info.name}/{LOG}"]
    return out
