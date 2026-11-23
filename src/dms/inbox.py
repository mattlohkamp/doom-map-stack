"""Notes from the mapper to Claude ("Send to Claude"), one inbox per map: build/<map>/inbox.jsonl.

Append-only JSON lines, so several writers (the board, the editor plugin, the game) can add to it
safely. Two kinds of line:

    {"event": "note", "id": 3, "time": ..., "source": "board", "text": "make this taller",
     "pos": [x, y], "target": {"kind": "sector", "index": 1, "gid": "platform_nw"}, ...}
    {"event": "close", "id": 3, "time": ..., "reply": "raised it to 32"}

A note's other fields depend on where it came from (the board adds the build it was clicked on; the
editor and game add what they know). Claude reads notes with `dms notes` / `dms watch` and closes them
with `dms notes <map> --close ID --reply "..."`; the board shows open and recently closed notes.
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

from dms.maps import MapInfo

FILENAME = "inbox.jsonl"
SOURCES = {"board": "the board", "editor": "the editor", "game": "the game", "claude": "Claude"}


def path(info: MapInfo, root: Path) -> Path:
    return info.build_dir(root) / FILENAME


def _now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _events(p: Path) -> list[dict]:
    if not p.exists():
        return []
    out = []
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue  # a half-written line from a writer that crashed; skip it
        if isinstance(ev, dict) and isinstance(ev.get("id"), int):
            out.append(ev)
    return out


def _append(p: Path, event: dict) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


def notes(info: MapInfo, root: Path) -> list[dict]:
    """All notes, oldest first, each with "status" ("open" | "closed") and, when closed, "reply" and
    "closed"."""
    by_id: dict[int, dict] = {}
    for ev in _events(path(info, root)):
        if ev.get("event") == "note":
            by_id[ev["id"]] = {**ev, "status": "open"}
        elif ev.get("event") == "close" and ev["id"] in by_id:
            by_id[ev["id"]].update(status="closed", reply=ev.get("reply", ""), closed=ev.get("time"))
    return [by_id[k] for k in sorted(by_id)]


def add(info: MapInfo, root: Path, text: str, source: str, **fields) -> dict:
    """Append a note; returns it (with its id)."""
    text = (text or "").strip()
    if not text:
        raise ValueError("a note needs some text")
    p = path(info, root)
    next_id = max((ev["id"] for ev in _events(p)), default=0) + 1
    note = {"event": "note", "id": next_id, "time": _now(), "map": info.name, "source": source, "text": text}
    note.update({k: v for k, v in fields.items() if v is not None})
    _append(p, note)
    return note


def close(info: MapInfo, root: Path, note_id: int, reply: str = "") -> dict:
    known = {n["id"]: n for n in notes(info, root)}
    if note_id not in known:
        raise KeyError(f"{info.name} has no note #{note_id}")
    _append(path(info, root), {"event": "close", "id": note_id, "time": _now(), "reply": reply.strip()})
    from dms import live

    if live.game_running(info, root):  # show the reply in the game, within a second (live.py)
        live.post(info, root, f"Claude, note #{note_id}: {reply.strip() or 'done'}")
        live.set_status(info, root, _working_on(info, root))  # the next open note, or clear
    return {**known[note_id], "status": "closed", "reply": reply.strip()}


# ---------------------------------------------------------------- notes from the game

# Lines the devtools mod (resources/devtools/zscript.zs) writes to the console log.
MARK_RE = re.compile(
    r"\[DMS-NOTE-MARK\] (?P<n>\d+) pos=(?P<x>-?[\d.]+),(?P<y>-?[\d.]+),(?P<z>-?[\d.]+) "
    r"angle=(?P<angle>-?[\d.]+) pitch=(?P<pitch>-?[\d.]+) sector=(?P<sector>-?\d+) hit=(?P<hit>.*?) "
    r"at=(?P<hx>-?[\d.]+),(?P<hy>-?[\d.]+),(?P<hz>-?[\d.]+)\s*$")
TEXT_RE = re.compile(r"\[DMS-NOTE-TEXT\] (?P<n>\d+) (?P<time>\d+) (?P<text>.*?)\s*$")
SHOT_TYPES = (".png", ".jpg", ".jpeg")
# The engine names things by class; TEXTMAP by Doom type number. The monsters (they move, so a hit
# can't always be matched by position). Lower-case class names.
CLASS_TYPES = {
    "zombieman": 3004, "shotgunguy": 9, "chaingunguy": 65, "wolfensteinss": 84, "doomimp": 3001,
    "demon": 3002, "spectre": 58, "lostsoul": 3006, "cacodemon": 3005, "hellknight": 69,
    "baronofhell": 3003, "arachnotron": 68, "painelemental": 71, "revenant": 66, "fatso": 67,
    "archvile": 64, "cyberdemon": 16, "spidermastermind": 7,
}


def shots_dir(info: MapInfo, root: Path) -> Path:
    """Where `dms play` points UZDoom's screenshots."""
    return info.build_dir(root) / "shots"


def _gid(tm, kind: str, index: int):
    blocks = tm.of(kind)
    return blocks[index].get("user_gid") if 0 <= index < len(blocks) else None


def _looking_at(tm, hit: str) -> dict | None:
    m = re.match(r"wall line=(\d+) side=(\d+)", hit)
    if m:
        i = int(m.group(1))
        return {"kind": "linedef", "index": i, "gid": _gid(tm, "linedef", i), "side": "back" if m.group(2) == "1" else "front"}
    m = re.match(r"(floor|ceiling) sector=(\d+)", hit)
    if m:
        i = int(m.group(2))
        return {"kind": "sector", "index": i, "gid": _gid(tm, "sector", i), "part": m.group(1)}
    m = re.match(r"thing class=(\S+) at=(-?[\d.]+),(-?[\d.]+)(?: spawn=(-?[\d.]+),(-?[\d.]+) health=(-?\d+))?", hit)
    if m:
        x, y = float(m.group(2)), float(m.group(3))
        extra = {"class": m.group(1)}
        if m.group(6) is not None and int(m.group(6)) <= 0 and m.group(1).lower() in CLASS_TYPES:
            extra["dead"] = True
        if m.group(4) is not None:
            # Where the map placed it: the thing's own TEXTMAP position, exact even if it moved or died.
            sx, sy = float(m.group(4)), float(m.group(5))
            placed = [(i, t) for i, t in enumerate(tm.things)
                      if abs(t.get("x", 0) - sx) < 0.5 and abs(t.get("y", 0) - sy) < 0.5]
            if placed:
                i, t = placed[0]
                return {"kind": "thing", "index": i, "gid": t.get("user_gid"), "type": t.get("type"), **extra}
        # The engine doesn't know TEXTMAP's thing numbers; the one placed there is the one hit.
        near = [(abs(t.get("x", 0) - x) + abs(t.get("y", 0) - y), i, t) for i, t in enumerate(tm.things)]
        close = [n for n in near if n[0] <= 32]
        # Monsters move once the game runs: failing the position, the nearest thing of the same type.
        typ = CLASS_TYPES.get(m.group(1).lower())
        same = [n for n in near if typ is not None and n[2].get("type") == typ]
        pick = min(close or same, key=lambda n: n[0]) if (close or same) else None
        if pick:
            _, i, t = pick
            return {"kind": "thing", "index": i, "gid": t.get("user_gid"), "type": t.get("type"), **extra}
        return {"kind": "thing", **extra}
    return None


def _screenshot(info: MapInfo, root: Path, when: int) -> str | None:
    """The screenshot taken for a note: the newest one in the shots folder from up to a minute before
    the note was sent (the key takes it, then the mapper types)."""
    d = shots_dir(info, root)
    if not d.exists():
        return None
    shots = [p for p in d.iterdir() if p.suffix.lower() in SHOT_TYPES and when - 60 <= p.stat().st_mtime <= when + 2]
    if not shots:
        return None
    return str(max(shots, key=lambda p: p.stat().st_mtime).relative_to(root)).replace("\\", "/")


PREVIEW_WIDTH = 960


def _preview(root: Path, shot: str | None) -> str | None:
    """A 960-wide JPEG copy of a note's screenshot, for Claude to look at: ~700 image tokens instead of
    ~1,800 for a 1920x1080 original (which stays, for the mapper or a closer look)."""
    if not shot:
        return None
    from PIL import Image

    src = root / shot
    dst = src.parent / "preview" / (src.stem + ".jpg")
    try:
        if not dst.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            with Image.open(src) as im:
                im = im.convert("RGB")
                if im.width > PREVIEW_WIDTH:
                    im = im.resize((PREVIEW_WIDTH, round(im.height * PREVIEW_WIDTH / im.width)), Image.LANCZOS)
                im.save(dst, quality=85)
    except OSError:
        return None
    return str(dst.relative_to(root)).replace("\\", "/")


class _Lock:
    """A lock file, so two processes (the board, dms watch) don't add the same game note twice."""

    def __init__(self, p: Path) -> None:
        self.p = p

    def __enter__(self):
        import os
        import time

        for _ in range(50):
            try:
                os.close(os.open(self.p, os.O_CREAT | os.O_EXCL | os.O_WRONLY))
                return self
            except PermissionError:
                # Windows: the other process's lock file is being deleted right now (it can't be
                # created again until that finishes). Seen 2026-11-22: it stopped `dms watch`.
                time.sleep(0.05)
            except FileExistsError:
                try:
                    if time.time() - self.p.stat().st_mtime > 10:  # left behind by a crash
                        self.p.unlink()
                except OSError:
                    pass
                time.sleep(0.05)
        raise TimeoutError(f"{self.p} is held")

    def __exit__(self, *exc):
        self.p.unlink(missing_ok=True)


def ingest_game_log(info: MapInfo, root: Path) -> list[dict]:
    """Add notes typed in the game (lines in build/<map>/log-play.txt) to the inbox, once each.
    Returns the notes added."""
    log = info.build_dir(root) / "log-play.txt"
    if not log.exists():
        return []
    text = log.read_text(encoding="utf-8", errors="replace")
    if "[DMS-NOTE-TEXT]" not in text:
        return []
    from dms import udmf

    marks, typed = {}, []
    for line in text.splitlines():
        if (m := MARK_RE.search(line)):
            marks[m["n"]] = m
        elif (m := TEXT_RE.search(line)):
            typed.append(m)
    added = []
    with _Lock(path(info, root).with_suffix(".lock")):
        have = {n.get("game_key") for n in notes(info, root)}
        tm = None
        for t in typed:
            key = f"{t['time']}:{t['n']}"
            if key in have or not t["text"]:
                continue
            if tm is None:
                try:
                    tm = udmf.parse(info.textmap.read_text(encoding="utf-8"))
                except (OSError, udmf.UdmfError):
                    tm = udmf.Textmap()
            mk = marks.get(t["n"])
            fields = {"game_key": key}
            if mk:
                sec = int(mk["sector"])
                fields.update(
                    pos=[float(mk["x"]), float(mk["y"]), float(mk["z"])],
                    angle=float(mk["angle"]), pitch=float(mk["pitch"]),
                    standing_in={"kind": "sector", "index": sec, "gid": _gid(tm, "sector", sec)},
                    looking_at=_looking_at(tm, mk["hit"]),
                    looking_at_point=[float(mk["hx"]), float(mk["hy"]), float(mk["hz"])],
                )
            fields["screenshot"] = _screenshot(info, root, int(t["time"]))
            fields["preview"] = _preview(root, fields["screenshot"])
            added.append(add(info, root, t["text"], "game", **fields))
    if added:
        from dms import live

        if live.game_running(info, root):  # tell the mapper, in the game, that it arrived
            heard = listening(root, info.name)
            for n in added:
                short = n["text"] if len(n["text"]) <= 60 else n["text"][:57] + "..."
                live.post(info, root, f"Got note #{n['id']}: \"{short}\"" + (
                    "" if heard else " - but Claude isn't watching notes: tell Claude to check them"))
            live.set_status(info, root, _working_on(info, root))
    return added


def _working_on(info: MapInfo, root: Path) -> str:
    """The automatic status line: the oldest open note (Claude refines it with `dms status`), or, when
    no `dms watch` is running, that the notes are waiting unseen."""
    open_notes = [n for n in notes(info, root) if n["status"] == "open"]
    if not open_notes:
        return ""
    if not listening(root, info.name):
        return f"{len(open_notes)} note(s) waiting, but Claude isn't watching: tell Claude to check notes"
    more = f" ({len(open_notes) - 1} more waiting)" if len(open_notes) > 1 else ""
    return f"working on note #{open_notes[0]['id']}{more}"


# ---------------------------------------------------------------- is Claude listening?

# `dms watch` rewrites this every second or so; the board, the game's acknowledgements, the editor
# plugin and Claude Code's prompt hook read it. Stale (the watch was stopped or killed) = not listening.
WATCH_FILE = "claude-watch.json"
WATCH_FRESH = 10  # seconds


def watch_path(root: Path) -> Path:
    return root / "build" / WATCH_FILE


def mark_listening(root: Path, map_names: list[str] | None) -> None:
    """Called by `dms watch` on every look. map_names None = every map."""
    p = watch_path(root)
    p.parent.mkdir(parents=True, exist_ok=True)
    data = {"time": _now(), "maps": "*" if map_names is None else sorted(map_names)}
    try:
        p.write_text(json.dumps(data) + "\n", encoding="utf-8")
    except OSError:
        pass  # someone was reading it; next look


def stop_listening(root: Path) -> None:
    watch_path(root).unlink(missing_ok=True)


def listening(root: Path, map_name: str) -> bool:
    """Whether a `dms watch` covering this map has looked in the last WATCH_FRESH seconds."""
    import time

    p = watch_path(root)
    try:
        if time.time() - p.stat().st_mtime > WATCH_FRESH:
            return False
        maps_ = json.loads(p.read_text(encoding="utf-8")).get("maps")
    except (OSError, ValueError, AttributeError):
        return False
    return maps_ == "*" or (isinstance(maps_, list) and map_name in maps_)


def describe(n: dict) -> str:
    """One note as text, for `dms notes` and `dms watch` (and so for Claude)."""
    src = SOURCES.get(n.get("source"), n.get("source", "?"))
    where = []
    if n.get("build"):
        where.append(f"on build #{n['build']}")
    if n.get("pos"):
        x, y = n["pos"][:2]
        where.append(f"at ({x:g}, {y:g}" + (f", z {n['pos'][2]:g}" if len(n["pos"]) > 2 else "") + ")")
    if n.get("angle") is not None:
        where.append(f"facing {n['angle']:g}")
    head = f"[DMS-NOTE] {n.get('map', '?')} #{n['id']} from {src} {' '.join(where)}".rstrip()
    lines = [head]
    for key, label in (("standing_in", "standing in"), ("target", "about"), ("looking_at", "looking at")):
        t = n.get(key)
        if isinstance(t, dict):
            gid = f" ({t['gid']})" if t.get("gid") else ""
            extra = ", ".join(f"{k} {t[k]}" if t[k] is not True else k for k in ("part", "side", "class", "dead") if t.get(k))
            lines.append(f"  {label}: {t.get('kind', '?')} {t.get('index', '?')}{gid}" + (f", {extra}" if extra else ""))
    sel = n.get("selection")
    if isinstance(sel, list) and len(sel) > 1:
        rest = [f"{t.get('kind', '?')} {t.get('index', '?')}" + (f" ({t['gid']})" if t.get("gid") else "")
                for t in sel[1:] if isinstance(t, dict)]
        lines.append(f"  also selected ({len(rest)}): " + ", ".join(rest))
    if isinstance(n.get("props"), dict):
        lines.append("  as seen: " + ", ".join(f"{k} {v}" for k, v in n["props"].items()))
    if n.get("preview"):
        lines.append(f"  screenshot: {n['preview']} (full size: {n.get('screenshot')})")
    elif n.get("screenshot"):
        lines.append(f"  screenshot: {n['screenshot']}")
    lines.append(f"  \"{n['text']}\"")
    if n.get("status") == "closed":
        lines.append(f"  closed{': ' + n['reply'] if n.get('reply') else ''}")
    return "\n".join(lines)
