"""The board: a small local web page with each map's build history (render + diff side by side,
Claude's note, validation), the editor's state and problems from the last play session.

`dms board` serves it on 127.0.0.1 only (port from dms.toml [board], default 8765) and opens the
browser; `Open Board.cmd` runs it. The page polls the server every couple of seconds, so new
builds appear by themselves. Python standard library only; nothing is written anywhere.
"""

from __future__ import annotations

import contextlib
import io
import json
import re
import sys
import threading
import time
import urllib.request
import webbrowser
from datetime import datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, urlparse

from dms import history, inbox
from dms.build import edit_wad_changed, editor_state
from dms.launch import pid_alive
from dms.maps import MapInfo, all_maps

NAME = re.compile(r"^[a-z0-9][a-z0-9-]*$")
# Lines in UZDoom's log worth showing. A heuristic: the log has no severity markers of its own.
LOG_PROBLEM = re.compile(r"\b(errors?|warnings?|unknown|not found|can't|cannot|could not|couldn't|missing|failed|bad)\b",
                         re.IGNORECASE)
LOG_COLOR = re.compile(r"\x1c(\[[^\]]*\]|.)")  # UZDoom's text colour escapes
# Key H in the game (resources/devtools): "reload the map in place here" (x y z angle pitch).
RELOAD_RE = re.compile(r"\[DMS-RELOAD\] (-?[\d.]+) (-?[\d.]+) (-?[\d.]+) (-?[\d.]+) (-?[\d.]+)")
MAX_LOG_LINES = 50


def editor_summary(info: MapInfo, root: Path) -> dict:
    state = editor_state(info, root)
    is_open = bool(state.get("open"))
    if is_open and isinstance(state.get("pid"), int) and not pid_alive(state["pid"]):
        is_open = False  # the editor quit without saying so (crash, killed)
    return {
        "open": is_open,
        "unsaved": is_open and bool(state.get("unsaved_changes")),
        "saved_edits": info.edit_wad(root).exists() and edit_wad_changed(info, root),
    }


def play_log(info: MapInfo, root: Path) -> dict | None:
    p = info.build_dir(root) / "log-play.txt"
    if not p.exists():
        return None
    lines = [LOG_COLOR.sub("", line).rstrip() for line in p.read_text(encoding="utf-8", errors="replace").splitlines()]
    problems = [line for line in lines if LOG_PROBLEM.search(line)]
    return {
        "time": datetime.fromtimestamp(p.stat().st_mtime).astimezone().isoformat(timespec="seconds"),
        "problems": problems[:MAX_LOG_LINES],
        "more": max(0, len(problems) - MAX_LOG_LINES),
    }


def map_list(root: Path) -> list[dict]:
    out = []
    for info in all_maps(root):
        entries = history.entries(info, root)
        out.append({
            "name": info.name,
            "title": info.title,
            "kind": info.kind,
            "builds": len(entries),
            "last": entries[0]["time"] if entries else None,
        })
    return out


EDIT_FILES = ("render-edit.png", "diff-edit.png", "diff-edit-before.png", "diff-edit-after.png",
              "render-edit.svg", "diff-edit.svg", "diff-edit-before.svg", "diff-edit-after.svg")


def _ctype(fname: str) -> str:
    return ("image/png" if fname.endswith(".png") else "image/svg+xml; charset=utf-8" if fname.endswith(".svg")
            else "text/plain; charset=utf-8")
STRUCTURAL_RE = re.compile(r"^structural changes \((\d+)\)", re.MULTILINE)


def pending_save(info: MapInfo, root: Path, editor: dict) -> dict | None:
    """The mapper's saved editor edits that aren't in the map's source yet, with pull's report and
    pictures when pull has looked at this save (build/<map>/pull.txt newer than edit.wad)."""
    if not editor["saved_edits"]:
        return None
    ew, rep = info.edit_wad(root), info.build_dir(root) / "pull.txt"
    saved = ew.stat().st_mtime
    out = {"time": datetime.fromtimestamp(saved).astimezone().isoformat(timespec="seconds"),
           "report": None, "structural": None, "images": {}}
    if rep.exists() and rep.stat().st_mtime >= saved:
        out["report"] = rep.read_text(encoding="utf-8")
        m = STRUCTURAL_RE.search(out["report"])
        out["structural"] = int(m.group(1)) if m else None
        for f in EDIT_FILES:
            p = info.build_dir(root) / f
            if p.exists() and p.stat().st_mtime >= saved:
                out["images"][f] = f"/edit/{info.name}/{f}?v={p.stat().st_mtime_ns}"
    return out


def note_target(info: MapInfo, pos: list[float]) -> dict | None:
    """What a click at `pos` is about, in the map's current TEXTMAP: a thing within 24 units, else
    the sector there."""
    from dms import udmf
    from dms.validate import sector_at

    try:
        tm = udmf.parse(info.textmap.read_text(encoding="utf-8"))
    except (OSError, udmf.UdmfError):
        return None
    x, y = pos
    near = [(abs(t["x"] - x) + abs(t["y"] - y), i, t) for i, t in enumerate(tm.things) if "x" in t.fields]
    near = [n for n in near if n[0] <= 24]
    if near:
        _, i, t = min(near, key=lambda n: n[0])
        return {"kind": "thing", "index": i, "gid": t.get("user_gid"), "type": t.get("type")}
    s = sector_at(tm, x, y)
    if s is None:
        return None
    return {"kind": "sector", "index": s, "gid": tm.sectors[s].get("user_gid")}


MAX_NOTE = 2000


def map_detail(info: MapInfo, root: Path) -> dict:
    from dms import inbox

    editor = editor_summary(info, root)
    return {
        "name": info.name,
        "title": info.title,
        "kind": info.kind,
        "source": info.source,
        "editor": editor,
        "pending": pending_save(info, root, editor),
        "notes": list(reversed(inbox.notes(info, root)))[:50],
        "claude_listening": inbox.listening(root, info.name),  # a `dms watch` covers this map
        "play_log": play_log(info, root),
        "entries": history.entries(info, root),
    }


def _first_line(text: str, limit: int = 110) -> str:
    line = (text or "").strip().splitlines()[0] if (text or "").strip() else ""
    return line if len(line) <= limit else line[: limit - 3] + "..."


def _build_line(name: str, e: dict) -> str:
    status = (f"{e['errors']} error(s)" if e.get("errors") else
              f"{e['warnings']} warning(s)" if e.get("warnings") else "valid")
    kind = "first build" if e.get("first") else "changed" if e.get("changed") else "no map change"
    msg = f"{name} #{e['seq']}: new build on the board ({kind}, {status})"
    note = _first_line(e.get("note", ""))
    return msg + (f"\n           Claude: {note}" if note else "")


class Watcher:
    """Turns what changed since the last look (builds, editor state, play logs) into status lines
    for the board's console window."""

    SETTLE = 3  # looks without a change before a play log counts as finished (UZDoom writes as it goes)

    def __init__(self, root: Path, auto_pull: bool = False) -> None:
        self.root = root
        self.auto_pull = auto_pull
        self.prev: dict | None = None
        self.pending_logs: dict[str, int] = {}
        self.handled_saves: dict[str, tuple] = {}  # map -> edit.wad (mtime, size) already auto-pulled
        self.reloads_seen: dict[str, tuple] = {}   # map -> (play session, reload requests acted on)
        self.just_pulled: set[str] = set()

    @staticmethod
    def _sig(p: Path):
        st = p.stat() if p.exists() else None
        return (st.st_mtime_ns, st.st_size) if st else None

    def snapshot(self) -> dict:
        out = {}
        for info in all_maps(self.root):
            inbox.ingest_game_log(info, self.root)  # notes typed in the game -> the inbox
            out[info.name] = {
                "info": info,
                "entry": history.latest(info, self.root),
                "editor": editor_summary(info, self.root),
                "log": self._sig(info.build_dir(self.root) / "log-play.txt"),
                "edit": self._sig(info.edit_wad(self.root)),
                "notes": {n["id"]: n for n in inbox.notes(info, self.root)},
            }
        return out

    def step(self) -> list[str]:
        cur = self.snapshot()
        if self.prev is None:
            self.prev = cur
            for name, c in cur.items():
                self._check_reloads(name, c["info"], first=True)
            return [self._summary(name, c) for name, c in cur.items()] or ["no maps yet"]
        msgs: list[str] = []
        for name, c in cur.items():
            p = self.prev.get(name)
            if p is None:
                msgs.append(f"{name}: new map")
            ce, pe = c["entry"], p["entry"] if p else None
            if ce and (pe is None or ce["seq"] != pe["seq"]):
                msgs.append(_build_line(name, ce))
            if p:
                msgs += [f"{name}: {m}" for m in self._editor_changes(name, p["editor"], c["editor"])]
            if p:
                for nid, n in c["notes"].items():
                    old = p["notes"].get(nid)
                    if old is None:
                        src = inbox.SOURCES.get(n.get("source"), n.get("source"))
                        msgs.append(f"{name}: note #{nid} from {src}: {_first_line(n['text'], 90)}")
                        if not inbox.listening(self.root, name):
                            msgs.append(f"{name}: Claude isn't watching notes (no dms watch): tell Claude to check them")
                    elif old["status"] == "open" and n["status"] == "closed":
                        msgs.append(f"{name}: note #{nid} done" + (f": {_first_line(n['reply'], 90)}" if n.get("reply") else ""))
            # Auto-pull a save once edit.wad has stopped changing (one look), and only once per save.
            ed = c["editor"]
            if (self.auto_pull and p and ed["saved_edits"] and not ed["unsaved"]
                    and c["edit"] == p["edit"] and self.handled_saves.get(name) != c["edit"]):
                self.handled_saves[name] = c["edit"]
                msgs += self._pull(name, c["info"])
            # Play log: report once it has stopped changing, so a session gives one line.
            if c["log"] != (p["log"] if p else None):
                self.pending_logs[name] = 0
                msgs += self._check_reloads(name, c["info"])  # key H in the game: reload in place
            elif name in self.pending_logs:
                self.pending_logs[name] += 1
                if self.pending_logs[name] >= self.SETTLE:
                    del self.pending_logs[name]
                    msgs.append(self._play_line(name, c["info"]))
        for name in self.prev.keys() - cur.keys():
            msgs.append(f"{name}: map removed")
        self.prev = cur
        return msgs

    def _summary(self, name: str, c: dict) -> str:
        e, ed = c["entry"], c["editor"]
        builds = f"latest build #{e['seq']}" if e else "no builds on the board yet"
        editor = ("editor open, unsaved changes" if ed["unsaved"] else "editor open" if ed["open"] else "editor closed")
        extra = ", saved editor edits waiting to be brought back" if ed["saved_edits"] else ""
        return f"{name}: {builds}; {editor}{extra}"

    def _editor_changes(self, name: str, p: dict, c: dict) -> list[str]:
        out = []
        if c["open"] and not p["open"]:
            out.append("editor opened (select something, then Ctrl+Shift+N or Ctrl+right click, to send Claude a note)")
        if c["unsaved"] and not p["unsaved"]:
            out.append("editor has unsaved changes (new builds won't reload until they're saved or undone)")
        if c["saved_edits"] and not p["saved_edits"]:
            out.append("saved in the editor" + ("" if self.auto_pull else
                       "; those edits aren't in the map's source yet (run Pull Map to bring them back)"))
        elif p["unsaved"] and not c["unsaved"] and c["open"]:
            out.append("editor: no unsaved changes")
        if p["saved_edits"] and not c["saved_edits"]:
            if name in self.just_pulled:
                self.just_pulled.discard(name)
            else:
                out.append("saved editor edits cleared")
        if p["open"] and not c["open"]:
            out.append("editor closed")
        return out

    # ------------------------------------------------------------ reload in place (key H in the game)

    def _reload_requests(self, info: MapInfo) -> tuple[str, list[list[float]]]:
        """(this play session's id, positions of every reload request in its log so far)."""
        log = info.build_dir(self.root) / "log-play.txt"
        try:
            text = log.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return "", []
        m = re.search(r"^Log started: (.*)$", text, re.MULTILINE)
        found = [[float(v) for v in r.groups()] for r in RELOAD_RE.finditer(text)]
        return (m.group(1) if m else ""), found

    def _check_reloads(self, name: str, info: MapInfo, first: bool = False) -> list[str]:
        """Reload the game if its log has a reload request we haven't acted on. Requests already in the
        log when the board started don't count; a new play session starts its own count."""
        session, requests = self._reload_requests(info)
        prev = self.reloads_seen.get(name)
        self.reloads_seen[name] = (session, len(requests))
        if first or prev is None:
            return []
        prev_session, prev_count = prev
        new = len(requests) - (prev_count if session == prev_session else 0)
        return self._reload(name, info, requests[-1]) if new > 0 else []

    def _reload(self, name: str, info: MapInfo, spawn: list[float]) -> list[str]:
        from dms import build as b
        from dms import launch

        try:
            started = json.loads((info.build_dir(self.root) / "play.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            started = {}
        since = started.get("started", 0)
        out: list[str] = []
        buf = io.StringIO()
        rebuilt = None
        try:
            with _say_lock, contextlib.redirect_stdout(buf):
                if b.needs_build(info, self.root) and not b.edit_wad_changed(info, self.root):
                    b.build(info, self.root, note="Rebuilt for a reload in place from the game.")
                    rebuilt = history.latest(info, self.root)
        except Exception as e:  # noqa: BLE001 - reload anyway, with the WAD as it is
            out.append(f"{name}: the rebuild failed ({e}); reloading the game with the map as it was")

        # What to tell the mapper on arrival: replies since this game started, and notes still open.
        lines = [f"Reloaded in place" + (f" (build #{rebuilt['seq']})" if rebuilt else "")]
        for n in inbox.notes(info, self.root):
            closed = n.get("closed")
            if n["status"] == "closed" and closed and datetime.fromisoformat(closed).timestamp() >= since:
                lines.append(f"Claude, note #{n['id']}: {n.get('reply') or 'done'}")
            elif n["status"] == "open" and n.get("source") == "game":
                lines.append(f"Note #{n['id']} ({_first_line(n['text'], 40)}): Claude is still on it")
        if len(lines) == 1:
            lines.append("No replies from Claude since the last start.")

        # A script that doesn't compile would stop the new game at startup (launch.play refuses to start
        # it): keep the running game rather than close it and leave the mapper with nothing.
        from dms import scripts

        code = scripts.read(info)
        errors = scripts.check(info, self.root, info.wad(self.root), code) if code else None
        if errors:
            out.append(f"{name}: not restarting the game: zscript.zs doesn't compile ({errors[0]}); "
                       "it keeps the build it has until Claude fixes the script")
            return out

        launch.stop_game(info, self.root)
        with _say_lock, contextlib.redirect_stdout(io.StringIO()):
            launch.play(self.root, info, skill=started.get("skill", 3), nomonsters=started.get("nomonsters", False),
                        spawn=spawn, message="|".join(lines))
        out.append(f"{name}: reloaded the game in place at ({spawn[0]:g}, {spawn[1]:g})"
                   + (f" with build #{rebuilt['seq']}" if rebuilt else "")
                   + f"; {len(lines) - 1} message line(s) shown on arrival")
        return out

    def _pull(self, name: str, info: MapInfo) -> list[str]:
        """Pull an editor save, with pull's own output kept out of the console."""
        from dms import pull

        buf = io.StringIO()
        try:
            with _say_lock, contextlib.redirect_stdout(buf):
                out = pull.run(info, self.root)
        except pull.PullError as e:
            return [f"{name}: couldn't pull the editor save: {e}"]
        except Exception as e:  # noqa: BLE001 - report it and keep the board running
            return [f"{name}: pulling the editor save failed: {e} (try Pull Map to see the details)"]
        ch = out.changes
        if out.status == "waiting":
            n = len(ch.structural)
            return [f"{name}: your editor save has {n} structural change(s), e.g. {ch.structural[0]}\n"
                    f"           They need Claude to bring them into map.py; the save is waiting on the board.\n"
                    f"           (Claude: `dms pull {name} --ported` once ported. Its tweaks and comments wait with it.)"]
        if out.status != "pulled":
            return []
        self.just_pulled.add(name)
        parts = [f"{len(ch.tweaks)} tweaked element(s)" if ch.tweaks else "",
                 f"{len(ch.requests)} comment(s) added to notes.md" if ch.requests else ""]
        line = f"{name}: pulled your editor save: " + (", ".join(p for p in parts if p) or "nothing to keep")
        if not out.matches:
            line += f"\n           but the rebuild differs from the save; see build/{name}/pull.txt"
        if out.errors:
            line += f"\n           the rebuild has {out.errors} validation error(s); see the board"
        return [line] + [f"           comment: {r}" for r in ch.requests]

    def _play_line(self, name: str, info: MapInfo) -> str:
        log = play_log(info, self.root)
        n = (len(log["problems"]) + log["more"]) if log else 0
        return f"{name}: play session logged, " + (f"{n} problem line(s) in the log (see the board)" if n else "no problems in the log")


_say_lock = threading.Lock()


def say(msg: str) -> None:
    stamp = datetime.now().strftime("%H:%M:%S")
    with _say_lock:
        print(f"[{stamp}] {msg}", flush=True)


def _watch(watcher: Watcher, interval: float = 1.0) -> None:
    failed = False
    while True:
        try:
            for msg in watcher.step():
                say(msg)
            failed = False
        except Exception as e:  # keep serving the board even if a look fails (a file mid-write)
            if not failed:
                say(f"(couldn't check for updates: {e})")
            failed = True
        time.sleep(interval)


def _find(root: Path, name: str) -> MapInfo | None:
    if not NAME.match(name):
        return None
    return next((m for m in all_maps(root) if m.name == name), None)


def make_handler(root: Path, announce: bool = False):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format, *args):  # keep the console quiet
            pass

        def _send(self, status: int, body: bytes, ctype: str, cache: str = "no-store") -> None:
            self.send_response(status)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", cache)
            self.end_headers()
            self.wfile.write(body)

        def _json(self, data) -> None:
            self._send(HTTPStatus.OK, json.dumps(data).encode("utf-8"), "application/json; charset=utf-8")

        def _missing(self) -> None:
            self._send(HTTPStatus.NOT_FOUND, b"not found", "text/plain; charset=utf-8")

        def do_POST(self) -> None:
            from dms import inbox

            path = urlparse(self.path).path
            if path not in ("/api/note", "/api/assets/favorites"):
                return self._missing()
            # Only the board's own pages may post (notes are instructions Claude acts on). They send
            # JSON with this header; another web page can't, without a CORS preflight this server
            # never answers. Origin, when sent, must be this server.
            port = self.server.server_address[1]
            origin = self.headers.get("Origin")
            if (self.headers.get("X-DMS-Board") != "1"
                    or not (self.headers.get("Content-Type") or "").startswith("application/json")
                    or origin not in (None, f"http://127.0.0.1:{port}", f"http://localhost:{port}")):
                return self._send(HTTPStatus.FORBIDDEN, b"not from the board", "text/plain; charset=utf-8")
            if path == "/api/assets/favorites":
                return self._favorite()
            try:
                length = int(self.headers.get("Content-Length") or 0)
                if not 0 < length <= 16384:
                    raise ValueError("bad length")
                data = json.loads(self.rfile.read(length))
                info = _find(root, str(data.get("map", "")))
                text = str(data.get("text", "")).strip()[:MAX_NOTE]
                pos = data.get("pos")
                if pos is not None:
                    pos = [round(float(pos[0]), 1), round(float(pos[1]), 1)]
                build = int(data["build"]) if data.get("build") is not None else None
                image = str(data.get("image")) if data.get("image") in history.COPIED else None
                if info is None or not text:
                    raise ValueError("needs a known map and some text")
            except (ValueError, TypeError, KeyError, IndexError, json.JSONDecodeError) as e:
                return self._send(HTTPStatus.BAD_REQUEST, f"bad note: {e}".encode(), "text/plain; charset=utf-8")
            note = inbox.add(info, root, text, "board", pos=pos, build=build, image=image,
                             target=note_target(info, pos) if pos else None)
            self._json(note)

        def _favorite(self) -> None:
            """The asset browser stars or unstars an asset: {category, name, on}."""
            from dms import resources

            try:
                length = int(self.headers.get("Content-Length") or 0)
                if not 0 < length <= 4096:
                    raise ValueError("bad length")
                data = json.loads(self.rfile.read(length))
                category, name = str(data["category"]), str(data["name"])
                if not re.fullmatch(r"[a-z]{1,20}", category) or not 0 < len(name) <= 64:
                    raise ValueError("bad category or name")
            except (ValueError, TypeError, KeyError, json.JSONDecodeError) as e:
                return self._send(HTTPStatus.BAD_REQUEST, f"bad favourite: {e}".encode(), "text/plain; charset=utf-8")
            self._json(resources.set_favorite(root, category, name, bool(data.get("on"))))

        def do_GET(self) -> None:
            url = urlparse(self.path)
            parts = [p for p in url.path.split("/") if p]
            try:
                if not parts:
                    self._send(HTTPStatus.OK, page().encode("utf-8"), "text/html; charset=utf-8")
                    if announce:
                        say("board opened in a browser")
                elif parts == ["api", "ping"]:
                    # "page": board.html's version, so an open board reloads itself when it changes.
                    self._json({"dms_board": True, "root": str(root), "page": PAGE_FILE.stat().st_mtime_ns})
                elif parts == ["themes"]:
                    # The theme viewer (docs/themes.md): its own page, same server, read on every request.
                    self._send(HTTPStatus.OK, THEMES_FILE.read_text(encoding="utf-8").encode("utf-8"),
                               "text/html; charset=utf-8")
                elif parts == ["api", "themes"]:
                    from dms import themes

                    self._json(themes.for_page(root))
                elif parts == ["assets"]:
                    # The asset browser (docs/asset-browser.md): its own page, same server.
                    self._send(HTTPStatus.OK, ASSETS_FILE.read_text(encoding="utf-8").encode("utf-8"),
                               "text/html; charset=utf-8")
                elif parts == ["assets-synth.js"]:
                    self._send(HTTPStatus.OK, SYNTH_FILE.read_bytes(), "text/javascript; charset=utf-8")
                elif parts == ["api", "assets", "favorites"]:
                    from dms import resources

                    self._json(resources.favorites(root))
                elif parts == ["api", "assets", "progress"]:
                    # How far the first indexing has got (the page's loading bar); never waits for it.
                    from dms import resources

                    self._json(resources.progress())
                elif parts == ["api", "assets", "custom"]:
                    # The maps' own assets (textures.txt, zscript.zs), marked with their map (mapassets.py).
                    from dms import mapassets

                    self._json(mapassets.custom(root))
                elif parts == ["api", "assets", "usage"]:
                    # What each map uses, and how often: the page puts those first.
                    from dms import mapassets

                    self._json(mapassets.usage(root))
                elif len(parts) == 3 and parts[0] == "asset-custom":
                    # /asset-custom/<map>/<NAME>.png: one of a map's own pictures (the URL carries ?v=<mtime>).
                    from dms import mapassets

                    got = mapassets.picture_file(root, parts[1], parts[2])
                    if got is None:
                        return self._missing()
                    self._send(HTTPStatus.OK, got[0], got[1], "max-age=31536000, immutable")
                elif len(parts) == 3 and parts[:2] == ["api", "assets"]:
                    from dms import resources

                    _, index, _ = resources.load(root)
                    if parts[2] == "index":
                        self._json({"key": index.key, "counts": index.counts()})
                    elif parts[2] in index.categories:
                        self._json({"key": index.key, "items": index.categories[parts[2]]})
                    else:
                        self._missing()
                elif len(parts) == 4 and parts[0] == "asset":
                    # /asset/<key>/<kind>/<NAME.ext>: converted on first request, cached in build/assets/<key>/.
                    from dms import resources

                    got = resources.asset_file(root, parts[2], parts[3])
                    if got is None:
                        return self._missing()
                    self._send(HTTPStatus.OK, got[0], got[1], "max-age=31536000, immutable")
                elif parts == ["api", "maps"]:
                    self._json(map_list(root))
                elif parts == ["api", "map"]:
                    info = _find(root, parse_qs(url.query).get("name", [""])[0])
                    self._json(map_detail(info, root)) if info else self._missing()
                elif len(parts) == 3 and parts[0] == "edit":
                    # /edit/<map>/<file>: pull's pictures of the mapper's save (URLs carry ?v=<mtime>).
                    _, name, fname = parts
                    info = _find(root, name)
                    f = info.build_dir(root) / fname if info and fname in EDIT_FILES else None
                    if f is None or not f.is_file():
                        return self._missing()
                    self._send(HTTPStatus.OK, f.read_bytes(), _ctype(fname), "max-age=31536000, immutable")
                elif len(parts) == 4 and parts[0] == "history":
                    # /history/<map>/<entry>/<file>: only the files history.record copies.
                    _, name, entry, fname = parts
                    info = _find(root, name)
                    if info is None or not entry.isdigit() or fname not in history.COPIED:
                        return self._missing()
                    f = history.history_dir(info, root) / entry / fname
                    if not f.is_file():
                        return self._missing()
                    self._send(HTTPStatus.OK, f.read_bytes(), _ctype(fname), "max-age=31536000, immutable")
                else:
                    self._missing()
            except (ConnectionError, OSError):
                pass  # the browser went away mid-response

    return Handler


def _running_here(port: int, root: Path) -> bool | None:
    """True: our board for this repo is already on the port; False: something else is; None: free."""
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/ping", timeout=1) as r:
            data = json.loads(r.read())
        return bool(data.get("dms_board")) and Path(data.get("root", "")) == root
    except (OSError, ValueError):
        return None


def _page_url(root: Path, url: str) -> str:
    """The board's page, on the map last chosen (Start Session and the map pickers remember it)."""
    from dms import picker

    last = picker._last(root)
    return url + (f"#{quote(last)}" if last else "")


def open_pages(board_url: str) -> None:
    """Opens the board in the browser. Only the board: its banner links to the other pages (the asset
    browser, and whatever tools come later), which the mapper opens when wanted (mapper, 2026-11-24;
    the asset browser used to open in a tab of its own every time)."""
    webbrowser.open_new_tab(board_url)


def serve(root: Path, port: int, open_browser: bool = True, auto_pull: bool = True) -> int:
    url = f"http://127.0.0.1:{port}/"
    running = _running_here(port, root)
    if running:
        print(f"dms board: already running at {url}")
        if open_browser:
            open_pages(_page_url(root, url))
        return 0
    try:
        server = ThreadingHTTPServer(("127.0.0.1", port), make_handler(root, announce=True))
    except OSError as e:
        print(f"dms board: can't use port {port} ({e.strerror or e}); set another under [board] in dms.toml",
              file=sys.stderr)
        return 1
    server.daemon_threads = True
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")  # notes may hold characters the console can't show
    print(f"dms board: {url}")
    print("    This window keeps the board running and lists what reaches it (builds, editor, play sessions).")
    print("    Close it (or press Ctrl+C) to stop the board.")
    if auto_pull:
        print("    Saves in the editor are pulled automatically (dms.toml [board] auto_pull).")
    print()
    threading.Thread(target=_watch, args=(Watcher(root, auto_pull=auto_pull),), daemon=True).start()
    if open_browser:
        open_pages(_page_url(root, url))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


PAGE_FILE = Path(__file__).with_name("board.html")
ASSETS_FILE = Path(__file__).with_name("assets.html")
SYNTH_FILE = Path(__file__).with_name("assets-synth.js")
THEMES_FILE = Path(__file__).with_name("themes.html")


def page() -> str:
    """The board page (HTML, CSS and script in one file). Read on every request, so a change to it
    shows up with a browser refresh; changes to this Python file still need the board restarted."""
    return PAGE_FILE.read_text(encoding="utf-8")

