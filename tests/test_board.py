import json
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

import pytest

from dms import board, build, history, maps


@pytest.fixture
def repo(tmp_path):
    (tmp_path / "maps").mkdir()
    return tmp_path


def _relight(info, light):
    text = info.generator.read_text()
    info.generator.write_text(text.replace("light=192", f"light={light}") if "light=192" in text
                              else text.replace("light=160", f"light={light}"))


def test_history_records_changes_and_notes_only(repo):
    info = maps.new(repo, "a")
    build.build(info, repo)  # first build: an entry, no diff
    build.build(info, repo)  # no change, no note: nothing
    build.build(info, repo, note="just a note")  # no change, but a note
    _relight(info, 160)
    build.build(info, repo, note="darker")
    es = history.entries(info, repo)
    assert [e["seq"] for e in es] == [3, 2, 1]
    newest, noted, first = es
    assert newest["note"] == "darker" and newest["changed"] and "diff.png" in newest["files"]
    assert "lightlevel" in newest["diff_text"]
    assert noted["note"] == "just a note" and not noted["changed"] and "diff.png" not in noted["files"]
    assert first["first"] and "diff.png" not in first["files"] and "render.png" in first["files"]
    assert first["counts"]["sectors"] == 1 and first["errors"] == 0


def test_history_keeps_the_newest(repo, monkeypatch):
    monkeypatch.setattr(history, "KEEP", 2)
    info = maps.new(repo, "a")
    for i in range(4):
        build.build(info, repo, note=f"n{i}")
    assert [e["note"] for e in history.entries(info, repo)] == ["n3", "n2"]


@pytest.fixture
def server(repo):
    srv = ThreadingHTTPServer(("127.0.0.1", 0), board.make_handler(repo))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_address[1]}"
    srv.shutdown()
    srv.server_close()


def _get(url):
    with urllib.request.urlopen(url, timeout=5) as r:
        return r.status, r.headers.get("Content-Type"), r.read()


def test_board_serves_page_api_and_history_files(repo, server):
    info = maps.new(repo, "a")
    build.build(info, repo, note="hello")
    (info.build_dir(repo) / "log-play.txt").write_text("Init complete.\nScript error, \"SCRIPTS\" line 3: oops\n")

    status, ctype, body = _get(server + "/")
    assert status == 200 and ctype.startswith("text/html") and b"dms board" in body

    ms = json.loads(_get(server + "/api/maps")[2])
    assert ms[0]["name"] == "a" and ms[0]["builds"] == 1

    d = json.loads(_get(server + "/api/map?name=a")[2])
    assert d["entries"][0]["note"] == "hello"
    assert d["editor"] == {"open": False, "unsaved": False, "saved_edits": False}
    assert d["play_log"]["problems"] == ['Script error, "SCRIPTS" line 3: oops']

    status, ctype, png = _get(f"{server}/history/a/{d['entries'][0]['dir']}/render.png")
    assert ctype == "image/png" and png.startswith(b"\x89PNG")


@pytest.mark.parametrize("path", [
    "/api/map?name=nope",
    "/api/map?name=../a",
    "/history/a/0001/entry.json",      # only the copied build files
    "/history/a/..%2F..%2Fmaps/render.png",
    "/history/A/0001/render.png",
])
def test_board_refuses_other_paths(repo, server, path):
    info = maps.new(repo, "a")
    build.build(info, repo)
    with pytest.raises(urllib.error.HTTPError) as e:
        _get(server + path)
    assert e.value.code == 404


def test_editor_marked_closed_when_its_process_is_gone(repo):
    info = maps.new(repo, "a")
    build.build(info, repo)
    state = {"open": True, "unsaved_changes": True, "pid": 999999999}
    (info.build_dir(repo) / "editor-state.json").write_text(json.dumps(state))
    assert board.editor_summary(info, repo) == {"open": False, "unsaved": False, "saved_edits": False}


def test_watcher_reports_builds_editor_and_play_sessions(repo):
    info = maps.new(repo, "a")
    build.build(info, repo)
    w = board.Watcher(repo)
    assert w.step() == ["a: latest build #1; editor closed"]
    assert w.step() == []

    _relight(info, 160)
    build.build(info, repo, note="darker\nsecond line")
    msgs = w.step()
    assert len(msgs) == 1 and "a #2: new build on the board (changed, " in msgs[0]  # no catalog here: 1 warning
    assert "Claude: darker" in msgs[0] and "second line" not in msgs[0]

    state = info.build_dir(repo) / "editor-state.json"
    import os
    state.write_text(json.dumps({"open": True, "unsaved_changes": True, "pid": os.getpid()}))
    assert w.step() == ["a: editor opened",
                        "a: editor has unsaved changes (new builds won't reload until they're saved or undone)"]
    state.write_text(json.dumps({"open": False, "unsaved_changes": False, "pid": os.getpid()}))
    assert w.step() == ["a: editor closed"]

    log = info.build_dir(repo) / "log-play.txt"
    log.write_text("Init complete.\n")
    assert w.step() == []          # still being written, maybe
    log.write_text("Init complete.\nScript error, line 3\n")
    assert w.step() == []
    assert [w.step() for _ in range(board.Watcher.SETTLE - 1)] == [[]] * (board.Watcher.SETTLE - 1)
    assert w.step() == ["a: play session logged, 1 problem line(s) in the log (see the board)"]
    assert w.step() == []


def _save_in_editor(info, repo, change):
    ew = build.pack_edit_wad(info, repo) if not info.edit_wad(repo).exists() else info.edit_wad(repo)
    from dms import udmf, wad
    _, lumps = wad.read(ew)
    i = wad.find(lumps, "TEXTMAP")
    tm = udmf.parse(lumps[i].data.decode("utf-8"))
    change(tm)
    lumps[i] = wad.Lump("TEXTMAP", udmf.dump(tm).encode("utf-8"))
    wad.write(ew, lumps)


def test_watcher_auto_pulls_a_tweak(repo):
    info = maps.new(repo, "a")
    build.build(info, repo)
    build.pack_edit_wad(info, repo)
    w = board.Watcher(repo, auto_pull=True)
    w.step()
    _save_in_editor(info, repo, lambda tm: tm.sectors[0].__setitem__("lightlevel", 99))
    assert w.step() == ["a: saved in the editor"]      # the save has to settle for one look
    msgs = w.step()
    assert msgs == ["a: pulled your editor save: 1 tweaked element(s)"]
    from dms import overrides
    assert overrides.load(info) == {"sector": {"room": {"lightlevel": 99}}}
    msgs = w.step()                                     # the rebuild shows up; no "cleared" line
    assert len(msgs) == 1 and msgs[0].startswith("a #2: new build on the board")
    assert w.step() == []


def test_watcher_leaves_structural_saves_for_claude(repo, server):
    info = maps.new(repo, "a")
    build.build(info, repo)
    build.pack_edit_wad(info, repo)
    w = board.Watcher(repo, auto_pull=True)
    w.step()
    from dms import udmf
    _save_in_editor(info, repo, lambda tm: tm.blocks.append(udmf.Block("thing", {"x": 64.0, "y": 64.0, "type": 2001})))
    w.step()
    msgs = w.step()
    assert len(msgs) == 1 and "1 structural change(s), e.g. new thing type 2001 at (64, 64)" in msgs[0]
    assert w.step() == [] and w.step() == []           # pulled once per save, not every look

    d = json.loads(_get(server + "/api/map?name=a")[2])
    assert d["pending"]["structural"] == 1 and "new thing type 2001" in d["pending"]["report"]
    url = d["pending"]["images"]["diff-edit.png"]
    assert _get(server + url)[2].startswith(b"\x89PNG")
