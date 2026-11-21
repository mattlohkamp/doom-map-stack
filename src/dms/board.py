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
from urllib.parse import parse_qs, urlparse

from dms import history
from dms.build import edit_wad_changed, editor_state
from dms.launch import pid_alive
from dms.maps import MapInfo, all_maps

NAME = re.compile(r"^[a-z0-9][a-z0-9-]*$")
# Lines in UZDoom's log worth showing. A heuristic: the log has no severity markers of its own.
LOG_PROBLEM = re.compile(r"\b(errors?|warnings?|unknown|not found|can't|cannot|could not|couldn't|missing|failed|bad)\b",
                         re.IGNORECASE)
LOG_COLOR = re.compile(r"\x1c(\[[^\]]*\]|.)")  # UZDoom's text colour escapes
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


EDIT_FILES = ("render-edit.png", "diff-edit.png", "diff-edit-before.png", "diff-edit-after.png")
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


def map_detail(info: MapInfo, root: Path) -> dict:
    editor = editor_summary(info, root)
    return {
        "name": info.name,
        "title": info.title,
        "kind": info.kind,
        "source": info.source,
        "editor": editor,
        "pending": pending_save(info, root, editor),
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
        self.just_pulled: set[str] = set()

    @staticmethod
    def _sig(p: Path):
        st = p.stat() if p.exists() else None
        return (st.st_mtime_ns, st.st_size) if st else None

    def snapshot(self) -> dict:
        out = {}
        for info in all_maps(self.root):
            out[info.name] = {
                "info": info,
                "entry": history.latest(info, self.root),
                "editor": editor_summary(info, self.root),
                "log": self._sig(info.build_dir(self.root) / "log-play.txt"),
                "edit": self._sig(info.edit_wad(self.root)),
            }
        return out

    def step(self) -> list[str]:
        cur = self.snapshot()
        if self.prev is None:
            self.prev = cur
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
            # Auto-pull a save once edit.wad has stopped changing (one look), and only once per save.
            ed = c["editor"]
            if (self.auto_pull and p and ed["saved_edits"] and not ed["unsaved"]
                    and c["edit"] == p["edit"] and self.handled_saves.get(name) != c["edit"]):
                self.handled_saves[name] = c["edit"]
                msgs += self._pull(name, c["info"])
            # Play log: report once it has stopped changing, so a session gives one line.
            if c["log"] != (p["log"] if p else None):
                self.pending_logs[name] = 0
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
            out.append("editor opened")
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

        def do_GET(self) -> None:
            url = urlparse(self.path)
            parts = [p for p in url.path.split("/") if p]
            try:
                if not parts:
                    self._send(HTTPStatus.OK, PAGE.encode("utf-8"), "text/html; charset=utf-8")
                    if announce:
                        say("board opened in a browser")
                elif parts == ["api", "ping"]:
                    self._json({"dms_board": True, "root": str(root)})
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
                    self._send(HTTPStatus.OK, f.read_bytes(), "image/png", "max-age=31536000, immutable")
                elif len(parts) == 4 and parts[0] == "history":
                    # /history/<map>/<entry>/<file>: only the files history.record copies.
                    _, name, entry, fname = parts
                    info = _find(root, name)
                    if info is None or not entry.isdigit() or fname not in history.COPIED:
                        return self._missing()
                    f = history.history_dir(info, root) / entry / fname
                    if not f.is_file():
                        return self._missing()
                    ctype = "image/png" if fname.endswith(".png") else "text/plain; charset=utf-8"
                    self._send(HTTPStatus.OK, f.read_bytes(), ctype, "max-age=31536000, immutable")
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


def serve(root: Path, port: int, open_browser: bool = True, auto_pull: bool = True) -> int:
    url = f"http://127.0.0.1:{port}/"
    running = _running_here(port, root)
    if running:
        print(f"dms board: already running at {url}")
        if open_browser:
            webbrowser.open(url)
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
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


PAGE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>dms board</title>
<style>
  :root {
    --bg: #18181c; --panel: #212127; --panel2: #2a2a31; --line: #3a3a44;
    --text: #e4e4ea; --dim: #9a9aa8; --ok: #46dc64; --warn: #ffdc3c; --err: #ff4646; --accent: #8fb4ff;
  }
  * { box-sizing: border-box; }
  html, body { margin: 0; height: 100%; }
  body { background: var(--bg); color: var(--text); font: 14px/1.45 "Segoe UI", system-ui, sans-serif;
         display: grid; grid-template-columns: 220px 1fr; }
  aside { border-right: 1px solid var(--line); padding: 16px 12px; position: sticky; top: 0; height: 100vh;
          overflow: auto; }
  aside h1 { font-size: 15px; margin: 0 0 12px; letter-spacing: .04em; color: var(--dim); text-transform: uppercase; }
  .map { display: block; width: 100%; text-align: left; background: none; border: 0; color: var(--text);
         padding: 8px 10px; border-radius: 6px; cursor: pointer; font: inherit; }
  .map:hover { background: var(--panel); }
  .map.sel { background: var(--panel2); }
  .map small { display: block; color: var(--dim); font-size: 12px; }
  #conn { color: var(--err); font-size: 12px; margin-top: 16px; }
  /* Layout rule: the newest build's picture fits in the window without scrolling. Everything
     above it (header, the entry's top line, captions) adds up to at most --chrome. */
  :root { --chrome: 215px; }
  main { padding: 12px 24px 40px; overflow: auto; min-width: 0; }
  header .titlerow { display: flex; align-items: baseline; gap: 12px; flex-wrap: wrap; }
  header h2 { margin: 0; font-size: 20px; }
  header .sub { color: var(--dim); }
  .bar { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; margin: 8px 0 0; }
  .bar .spacer { flex: 1; }
  .chips { display: flex; flex-wrap: wrap; gap: 8px; }
  button.chip { font: inherit; font-size: 13px; color: inherit; cursor: pointer; }
  .chip { background: var(--panel); border: 1px solid var(--line); border-radius: 999px; padding: 3px 12px; font-size: 13px; }
  .chip.ok { border-color: #2f6b3c; } .chip.warn { border-color: #8a7420; color: var(--warn); }
  .chip.err { border-color: #8a2a2a; color: var(--err); }
  .panel { background: var(--panel); border: 1px solid var(--line); border-radius: 8px; padding: 10px 14px; margin: 10px 0; }
  .panel h3 { margin: 0 0 6px; font-size: 13px; color: var(--dim); font-weight: 600; }
  pre { margin: 0; white-space: pre-wrap; font: 12.5px/1.4 Consolas, "Cascadia Mono", monospace; color: var(--text); }
  .entry { background: var(--panel); border: 1px solid var(--line); border-radius: 10px; margin: 12px 0; padding: 10px 14px 12px; }
  .entry .body { display: grid; grid-template-columns: minmax(0, 1fr) minmax(260px, 340px); gap: 16px;
                 align-items: start; margin-top: 8px; }
  .entry .side > :first-child { margin-top: 0; }
  @media (max-width: 1100px) { .entry .body { grid-template-columns: minmax(0, 1fr); } }
  .entry.fresh { border-color: var(--accent); box-shadow: 0 0 0 1px var(--accent); }
  .entry.pending { border-color: #8a7420; box-shadow: 0 0 0 1px #8a7420; }
  .entry.pending .seq { color: var(--warn); }
  .note.warnnote { border-left-color: var(--warn); }
  .entry .top { display: flex; flex-wrap: wrap; align-items: baseline; gap: 6px 14px; }
  .entry .seq { font-weight: 700; font-size: 16px; }
  .entry .when { color: var(--dim); }
  .entry .counts { color: var(--dim); font-size: 13px; }
  .note { margin: 0 0 4px; padding: 8px 12px; border-left: 3px solid var(--accent); background: var(--panel2);
          border-radius: 0 6px 6px 0; white-space: pre-wrap; }
  .note b { color: var(--accent); font-weight: 600; }
  .pics { display: flex; gap: 12px; min-width: 0; }
  .pics figure { flex: 0 1 auto; min-width: 0; }
  .pics:not(.single) figure { flex: 1 1 0; }
  .viewbar { display: flex; align-items: center; gap: 10px; }
  .viewbar .dim { color: var(--dim); font-size: 13px; }
  .segs { display: inline-flex; border: 1px solid var(--line); border-radius: 7px; overflow: hidden; }
  .seg { background: var(--panel); color: var(--text); border: 0; padding: 5px 14px; font: inherit; font-size: 13px; cursor: pointer; }
  .seg + .seg { border-left: 1px solid var(--line); }
  .seg.on { background: var(--accent); color: #10131a; font-weight: 600; }
  figure { margin: 0; }
  figure img { display: block; width: auto; height: auto; max-width: 100%; max-height: calc(100vh - var(--chrome));
               border-radius: 6px; border: 1px solid var(--line); background: #000; }
  figcaption { color: var(--dim); font-size: 12px; margin-top: 4px; }
  .nodiff { display: grid; place-items: center; min-height: 120px; border: 1px dashed var(--line); border-radius: 6px;
            color: var(--dim); }
  .issues { margin: 10px 0 0; padding-left: 18px; }
  .issues li.error { color: var(--err); } .issues li.warning { color: var(--warn); }
  details { margin-top: 10px; } summary { cursor: pointer; color: var(--dim); }
  .empty { color: var(--dim); }
  a { color: var(--accent); }
</style>
</head>
<body>
<aside>
  <h1>dms board</h1>
  <nav id="maplist"></nav>
  <p id="conn"></p>
</aside>
<main id="main"><p class="empty">Loading...</p></main>
<script>
"use strict";
const POLL_MS = 2000;
let current = decodeURIComponent(location.hash.slice(1)) || localStorage.getItem("dms-board-map") || "";
let shown = new Set(), shownFor = null, firstLoad = true, lastDetail = null, logOpen = false, lastPending = "";
let viewMode = localStorage.getItem("dms-board-view") === "beforeafter" ? "beforeafter" : "changes";

function viewBar() {
  const btn = (mode, label) => el("button", { class: "seg" + (viewMode === mode ? " on" : ""), onclick: () => setView(mode) }, label);
  return el("div", { class: "viewbar" }, el("span", { class: "dim" }, "Show builds as"),
    el("div", { class: "segs" }, btn("changes", "Changes"), btn("beforeafter", "Before / after")));
}
function setView(mode) {
  if (mode === viewMode) return;
  viewMode = mode;
  localStorage.setItem("dms-board-view", mode);
  shownFor = null;  // rebuild the timeline in the new view
  if (lastDetail) renderMap(lastDetail);
}

function el(tag, attrs, ...kids) {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v === null || v === undefined || v === false) continue;
    if (k === "class") e.className = v; else if (k.startsWith("on")) e.addEventListener(k.slice(2), v);
    else e.setAttribute(k, v);
  }
  for (const k of kids.flat()) if (k !== null && k !== undefined && k !== false)
    e.append(k instanceof Node ? k : document.createTextNode(String(k)));
  return e;
}

function ago(iso) {
  if (!iso) return "";
  const s = Math.round((Date.now() - new Date(iso)) / 1000);
  if (s < 60) return "just now";
  if (s < 3600) return Math.round(s / 60) + " min ago";
  if (s < 86400) return Math.round(s / 3600) + " h ago";
  return Math.round(s / 86400) + " days ago";
}
function clock(iso) {
  const d = new Date(iso);
  return d.toLocaleString(undefined, { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

function select(name) {
  current = name;
  localStorage.setItem("dms-board-map", name);
  history.replaceState(null, "", "#" + encodeURIComponent(name));

  poll();
}

function renderMaps(maps) {
  const nav = document.getElementById("maplist");
  nav.replaceChildren(...maps.map(m => el("button", { class: "map" + (m.name === current ? " sel" : ""),
      onclick: () => select(m.name) },
    m.title, el("small", null, m.name + " · " + (m.builds ? m.builds + " build" + (m.builds > 1 ? "s" : "") +
      " · " + ago(m.last) : "no builds yet")))));
}

function headerFor(d) {
  const ed = d.editor, chips = [];
  if (!ed.open) chips.push(el("span", { class: "chip" }, "Editor: closed"));
  else if (ed.unsaved) chips.push(el("span", { class: "chip warn" }, "Editor: open, unsaved changes"));
  else chips.push(el("span", { class: "chip ok" }, "Editor: open, no unsaved changes"));
  if (ed.saved_edits) chips.push(el("span", { class: "chip warn" }, "Saved editor edits not brought back yet"));
  const latest = d.entries[0];
  if (latest) {
    if (latest.errors) chips.push(el("span", { class: "chip err" }, "Latest build: " + latest.errors + " error(s)"));
    else if (latest.warnings) chips.push(el("span", { class: "chip warn" }, "Latest build: " + latest.warnings + " warning(s)"));
    else chips.push(el("span", { class: "chip ok" }, "Latest build: valid"));
  }
  // The play log is one chip; its problems open in a panel on click (kept closed so the picture fits).
  const log = d.play_log;
  let logPanel = null;
  if (!log) chips.push(el("span", { class: "chip" }, "Not played yet"));
  else if (!log.problems.length)
    chips.push(el("span", { class: "chip ok", title: clock(log.time) }, "Last play " + ago(log.time) + ": no problems in the log"));
  else {
    const n = log.problems.length + log.more;
    chips.push(el("button", { class: "chip warn", title: clock(log.time), onclick: () => { logOpen = !logOpen; renderMap(lastDetail); } },
      "Last play " + ago(log.time) + ": " + n + " problem line(s) " + (logOpen ? "▴" : "▾")));
    if (logOpen) logPanel = el("div", { class: "panel" }, el("h3", null, "Last play session, " + clock(log.time)),
      el("pre", null, log.problems.join("\n") + (log.more ? "\n... and " + log.more + " more" : "")));
  }
  return el("header", null,
    el("div", { class: "titlerow" }, el("h2", null, d.title), el("span", { class: "sub" }, d.name + " · " + d.kind + " · " + d.source)),
    el("div", { class: "bar" }, el("div", { class: "chips" }, chips), el("span", { class: "spacer" }), viewBar()),
    logPanel);
}

function entryFor(d, e, fresh, newest) {
  const base = "/history/" + encodeURIComponent(d.name) + "/" + e.dir + "/";
  const has = f => e.files.includes(f);
  const counts = Object.entries(e.counts || {}).map(([k, n]) => n + " " + k).join(", ");
  const status = e.errors ? el("span", { class: "chip err" }, e.errors + " error(s)")
    : e.warnings ? el("span", { class: "chip warn" }, e.warnings + " warning(s)") : el("span", { class: "chip ok" }, "valid");
  const flags = [e.first ? "first build" : "", e.forced ? "built with --force" : "", e.changed || e.first ? "" : "no map change"]
    .filter(Boolean).join(" · ");
  const pic = (f, caption) => el("figure", null,
    el("a", { href: base + f, target: "_blank" }, el("img", { src: base + f, alt: caption, loading: "lazy" })),
    el("figcaption", null, caption));
  const none = el("figure", null, el("div", { class: "nodiff" }, e.first ? "First build: nothing to compare with" : "No map change"),
                  el("figcaption", null, "Before"));
  let pics;
  if (viewMode === "changes") {
    pics = has("diff.png")
      ? el("div", { class: "pics single" }, pic("diff.png", "Now, with the changes marked: green added, yellow changed, red removed"))
      : el("div", { class: "pics single" }, has("render.png") ? pic("render.png", e.first ? "First build" : "No map change") : null);
  } else if (has("diff-before.png") && has("diff-after.png")) {
    pics = el("div", { class: "pics" }, pic("diff-before.png", "Before: red removed, yellow changed"),
                                        pic("diff-after.png", "After: green added, yellow changed"));
  } else {  // the first build, an unchanged one, or an entry from before the before/after images
    pics = el("div", { class: "pics" }, has("diff.png") ? pic("diff.png", "Changes") : none,
                                        has("render.png") ? pic("render.png", "After") : null);
  }
  return el("article", { class: "entry" + (fresh ? " fresh" : ""), "data-dir": e.dir },
    el("div", { class: "top" }, el("span", { class: "seq" }, "#" + e.seq),
      el("span", { class: "when", title: e.time }, clock(e.time)), status, el("span", { class: "counts" }, counts),
      flags ? el("span", { class: "counts" }, flags) : null),
    el("div", { class: "body" }, pics,
      el("div", { class: "side" },
        e.note ? el("div", { class: "note" }, el("b", null, "Claude: "), e.note) : null,
        e.issues.length ? el("ul", { class: "issues" }, e.issues.map(i => el("li", { class: i.split(":")[0] }, i))) : null,
        e.diff_text ? el("details", { open: newest || null }, el("summary", null, "What changed (text)"), el("pre", null, e.diff_text)) : null)));
}

function pendingFor(p) {
  const img = (f, caption) => p.images[f] ? el("figure", null,
    el("a", { href: p.images[f], target: "_blank" }, el("img", { src: p.images[f], alt: caption })),
    el("figcaption", null, caption)) : null;
  let title, text;
  if (p.report === null) {
    title = "Editor save, not pulled yet";
    text = "Run Pull Map (or turn on auto_pull in dms.toml) to bring it into the map's source.";
  } else if (p.structural) {
    title = "Editor save waiting for Claude";
    text = p.structural + " structural change(s) need porting into map.py; tweaks and comments wait with them. " +
           "Ask Claude to pull it.";
  } else {
    title = "Editor save being pulled";
    text = "";
  }
  const pics = viewMode === "changes"
    ? el("div", { class: "pics single" }, img("diff-edit.png", "Your save, with its changes marked") || img("render-edit.png", "Your save"))
    : el("div", { class: "pics" }, img("diff-edit-before.png", "Before your save"), img("diff-edit-after.png", "Your save"));
  return el("article", { class: "entry pending" },
    el("div", { class: "top" }, el("span", { class: "seq" }, title),
      el("span", { class: "when", title: p.time }, "saved " + clock(p.time) + " (" + ago(p.time) + ")")),
    el("div", { class: "body" }, Object.keys(p.images).length ? pics : el("div"),
      el("div", { class: "side" }, text ? el("div", { class: "note warnnote" }, text) : null,
        p.report ? el("details", { open: true }, el("summary", null, "What's in the save"), el("pre", null, p.report)) : null)));
}

function renderMap(d) {
  const main = document.getElementById("main");
  lastDetail = d;
  if (shownFor !== d.name) {
    main.replaceChildren(el("div", { id: "head" }), el("div", { id: "pending" }), el("div", { id: "timeline" }));
    lastPending = "";
    shown = new Set(); shownFor = d.name; firstLoad = true;
  }
  document.getElementById("head").replaceChildren(headerFor(d));  // cheap; keeps "x min ago" current
  const pendingKey = JSON.stringify([d.pending, viewMode]);
  if (pendingKey !== lastPending) {  // only when it changes, so its pictures don't flicker
    document.getElementById("pending").replaceChildren(...(d.pending ? [pendingFor(d.pending)] : []));
    lastPending = pendingKey;
  }
  const tl = document.getElementById("timeline");
  const dirs = new Set(d.entries.map(e => e.dir));
  for (const node of [...tl.children]) if (!dirs.has(node.dataset.dir)) { node.remove(); shown.delete(node.dataset.dir); }
  const fresh = d.entries.filter(e => !shown.has(e.dir));
  for (const e of fresh.slice().reverse()) {
    const node = entryFor(d, e, !firstLoad, e.dir === d.entries[0].dir);
    tl.prepend(node); shown.add(e.dir);
    if (!firstLoad) setTimeout(() => node.classList.remove("fresh"), 15000);
  }
  if (!d.entries.length && !tl.children.length)
    tl.replaceChildren(el("p", { class: "empty" }, "No builds recorded yet. They appear here after the next `dms build`."));
  else { const p = tl.querySelector("p.empty"); if (p) p.remove(); }
  firstLoad = false;
}

async function poll() {
  try {
    const maps = await (await fetch("/api/maps")).json();
    if (!current || !maps.some(m => m.name === current)) current = maps.length ? maps[0].name : "";
    renderMaps(maps);
    if (current) {
      const r = await fetch("/api/map?name=" + encodeURIComponent(current));
      if (r.ok) renderMap(await r.json());
    } else document.getElementById("main").replaceChildren(el("p", { class: "empty" }, "No maps yet."));
    document.getElementById("conn").textContent = "";
  } catch (err) {
    document.getElementById("conn").textContent = "The board server isn't running. Start it again with Open Board.cmd.";
  }
}

window.addEventListener("hashchange", () => { const n = decodeURIComponent(location.hash.slice(1)); if (n && n !== current) select(n); });
poll();
setInterval(poll, POLL_MS);
</script>
</body>
</html>
"""
