"""Build history, for the board: one folder per build that changed the map.

build/<map>/history/<seq>/ holds copies of that build's render.png/.txt, diff.png/.txt (when there
was a previous build) and validate.txt, plus entry.json (time, Claude's note, counts, issues).
Builds that change nothing add no entry unless they carry a note. The oldest entries beyond KEEP
are removed. Everything is under build/, so it's git-ignored and safe to delete.
"""

from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path

from dms.maps import MapInfo
from dms.validate import Issue

KEEP = 100
COPIED = ("render.png", "render.txt", "diff.png", "diff-before.png", "diff-after.png", "diff.txt", "validate.txt")


def history_dir(info: MapInfo, root: Path) -> Path:
    return info.build_dir(root) / "history"


def _seqs(hist: Path) -> list[int]:
    if not hist.exists():
        return []
    return sorted(int(p.name) for p in hist.iterdir() if p.is_dir() and p.name.isdigit())


def record(info: MapInfo, root: Path, *, changed: bool, counts: dict[str, int], issues: list[Issue],
           note: str | None = None, forced: bool = False) -> Path | None:
    """Add an entry for the build just made (its files are in build/<map>/). Returns its folder,
    or None when nothing changed and there's no note."""
    hist = history_dir(info, root)
    seqs = _seqs(hist)
    if seqs and not changed and not note:
        return None
    seq = seqs[-1] + 1 if seqs else 1
    d = hist / f"{seq:04d}"
    d.mkdir(parents=True)
    src = info.build_dir(root)
    files = []
    for name in COPIED:
        if name.startswith("diff") and not (changed and seqs):
            continue  # an unchanged build's diff files describe nothing; the first build has none
        if (src / name).exists():
            shutil.copy2(src / name, d / name)
            files.append(name)
    entry = {
        "seq": seq,
        "time": datetime.now().astimezone().isoformat(timespec="seconds"),
        "note": note or "",
        "changed": changed,
        "first": not seqs,
        "forced": forced,
        "counts": counts,
        "errors": sum(1 for i in issues if i.severity == "error"),
        "warnings": sum(1 for i in issues if i.severity != "error"),
        "issues": [str(i) for i in sorted(issues, key=lambda i: i.severity != "error")],
        "files": files,
    }
    (d / "entry.json").write_text(json.dumps(entry, indent=2) + "\n", encoding="utf-8", newline="\n")
    for old in seqs[: max(0, len(seqs) + 1 - KEEP)]:
        shutil.rmtree(hist / f"{old:04d}", ignore_errors=True)
    return d


def latest(info: MapInfo, root: Path) -> dict | None:
    """The newest entry (without the texts), or None. Cheap: reads one entry.json."""
    hist = history_dir(info, root)
    for seq in reversed(_seqs(hist)):
        try:
            return json.loads((hist / f"{seq:04d}" / "entry.json").read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            continue
    return None


def entries(info: MapInfo, root: Path) -> list[dict]:
    """All entries, newest first. Each has a "dir" (the folder name) and the texts inlined."""
    hist = history_dir(info, root)
    out = []
    for seq in reversed(_seqs(hist)):
        d = hist / f"{seq:04d}"
        try:
            entry = json.loads((d / "entry.json").read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            continue
        entry["dir"] = d.name
        if (d / "diff.txt").exists():
            entry["diff_text"] = (d / "diff.txt").read_text(encoding="utf-8")
        out.append(entry)
    return out
