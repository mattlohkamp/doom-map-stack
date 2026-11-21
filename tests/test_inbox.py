import json
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

import pytest

from dms import board, build, cli, history, inbox, maps


@pytest.fixture
def repo(tmp_path, monkeypatch):
    (tmp_path / "maps").mkdir()
    monkeypatch.setattr(cli, "repo_root", lambda: tmp_path)
    return tmp_path


def test_add_list_close(repo):
    info = maps.new(repo, "a")
    a = inbox.add(info, repo, "make this taller", "board", pos=[64, 96], target={"kind": "sector", "index": 0, "gid": "room"})
    b = inbox.add(info, repo, "  more light  ", "editor")
    assert (a["id"], b["id"], b["text"]) == (1, 2, "more light")
    inbox.close(info, repo, 1, "raised it to 160")
    ns = inbox.notes(info, repo)
    assert [(n["id"], n["status"]) for n in ns] == [(1, "closed"), (2, "open")] and ns[0]["reply"] == "raised it to 160"
    text = inbox.describe(ns[0])
    assert text.startswith("[DMS-NOTE] a #1 from the board at (64, 96)") and "about: sector 0 (room)" in text
    assert '"make this taller"' in text and "closed: raised it to 160" in text
    with pytest.raises(ValueError):
        inbox.add(info, repo, "   ", "board")
    with pytest.raises(KeyError):
        inbox.close(info, repo, 9)


def test_a_broken_line_is_skipped(repo):
    info = maps.new(repo, "a")
    inbox.add(info, repo, "one", "board")
    with inbox.path(info, repo).open("a", encoding="utf-8") as f:
        f.write('{"event": "note", "id": 2, "te')  # a writer died mid-line
    assert [n["text"] for n in inbox.notes(info, repo)] == ["one"]


def test_notes_command(repo, capsys):
    info = maps.new(repo, "a")
    inbox.add(info, repo, "first", "board")
    inbox.add(info, repo, "second", "board")
    assert cli.main(["notes", "a", "--close", "1", "--reply", "done that"]) == 0
    capsys.readouterr()
    cli.main(["notes"])
    out = capsys.readouterr().out
    assert '"second"' in out and '"first"' not in out
    cli.main(["notes", "a", "--all"])
    assert '"first"' in capsys.readouterr().out


@pytest.fixture
def server(repo):
    srv = ThreadingHTTPServer(("127.0.0.1", 0), board.make_handler(repo))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield srv.server_address[1]
    srv.shutdown()
    srv.server_close()


def _post(port, body, headers):
    req = urllib.request.Request(f"http://127.0.0.1:{port}/api/note", data=json.dumps(body).encode(),
                                 headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=5) as r:
        return json.loads(r.read())


BOARD = {"Content-Type": "application/json", "X-DMS-Board": "1"}


def test_board_click_makes_a_note_about_what_is_there(repo, server):
    info = maps.new(repo, "a")
    info.generator.write_text(
        "def build(m):\n"
        "    m.room('room', 0, 0, 512, 512)\n"
        "    m.player_start(256, 256)\n"
        "    m.thing(2001, 400, 400, 'room.shotgun')\n")
    build.build(info, repo)
    entry = history.latest(info, repo)
    assert entry["views"]["render.png"]["scale"] > 0  # the board turns clicks back into map coordinates

    n = _post(server, {"map": "a", "text": "more of these", "pos": [410, 395], "build": 1, "image": "render.png"},
              {**BOARD, "Origin": f"http://127.0.0.1:{server}"})
    assert n["target"] == {"kind": "thing", "index": 1, "gid": "room.shotgun", "type": 2001}
    n = _post(server, {"map": "a", "text": "darker here", "pos": [100, 100]}, BOARD)
    assert n["target"]["kind"] == "sector" and n["target"]["gid"] == "room"
    assert [x["text"] for x in inbox.notes(info, repo)] == ["more of these", "darker here"]


@pytest.mark.parametrize("headers,body", [
    ({"Content-Type": "application/json"}, {"map": "a", "text": "x"}),                       # no board header
    ({"Content-Type": "text/plain", "X-DMS-Board": "1"}, {"map": "a", "text": "x"}),         # a form-style post
    ({**BOARD, "Origin": "http://evil.example"}, {"map": "a", "text": "x"}),                # another site
    (BOARD, {"map": "nope", "text": "x"}),                                                   # unknown map
    (BOARD, {"map": "a", "text": "   "}),                                                    # no text
])
def test_board_refuses_other_notes(repo, server, headers, body):
    maps.new(repo, "a")
    with pytest.raises(urllib.error.HTTPError) as e:
        _post(server, body, headers)
    assert e.value.code in (400, 403)
    assert inbox.notes(maps.resolve(repo, "a"), repo) == []


def test_board_console_announces_notes(repo):
    info = maps.new(repo, "a")
    build.build(info, repo)
    w = board.Watcher(repo)
    w.step()
    inbox.add(info, repo, "make this taller\nand wider", "editor")
    assert w.step() == ["a: note #1 from the editor: make this taller"]
    inbox.close(info, repo, 1, "raised to 192")
    assert w.step() == ["a: note #1 done: raised to 192"]


def test_editor_note_as_the_plugin_writes_it(repo):
    # A line in the format DmsBridge.cs appends (selection of two sectors, with what the editor showed).
    info = maps.new(repo, "a")
    line = ('{"event": "note", "id": 1, "time": "2026-11-21T14:00:00-08:00", "map": "a", "source": "editor", '
            '"text": "make these \\"taller\\"", "pos": [128, 384], '
            '"target": {"kind": "sector", "index": 1, "gid": "platform_nw"}, '
            '"selection": [{"kind": "sector", "index": 1, "gid": "platform_nw"}, {"kind": "sector", "index": 2}], '
            '"props": {"floor": 16, "ceiling": 128, "light": 64, "floor_flat": "FLAT1", "ceiling_flat": "CEIL1"}}\n')
    inbox.path(info, repo).parent.mkdir(parents=True, exist_ok=True)
    inbox.path(info, repo).write_text(line, encoding="utf-8")
    inbox.add(info, repo, "and this", "board")  # ids carry on from the editor's
    ns = inbox.notes(info, repo)
    assert [n["id"] for n in ns] == [1, 2] and ns[0]["text"] == 'make these "taller"'
    text = inbox.describe(ns[0])
    assert "from the editor at (128, 384)" in text and "about: sector 1 (platform_nw)" in text
    assert "also selected (1): sector 2" in text and "as seen: floor 16, ceiling 128, light 64" in text


GAME_LOG = """\
Init complete.
MAP01 - Hello room
[DMS-NOTE-MARK] 1 pos=200.0,128.0,0.0 angle=90.0 pitch=-5.0 sector=0 hit=wall line=1 side=0 at=200.0,512.0,40.0
[DMS-NOTE-TEXT] 1 {t} this wall needs a window
[DMS-NOTE-MARK] 2 pos=256.0,256.0,0.0 angle=45.0 pitch=10.0 sector=0 hit=thing class=Shotgun at=400.0,400.0 at=400.0,400.0,0.0
[DMS-NOTE-CANCEL] 2
[DMS-NOTE-MARK] 3 pos=256.0,256.0,0.0 angle=45.0 pitch=10.0 sector=0 hit=thing class=Shotgun at=400.0,400.0 at=400.0,400.0,0.0
[DMS-NOTE-TEXT] 3 {t} two of these
"""


def test_notes_from_the_game_log(repo):
    import os
    import time

    info = maps.new(repo, "a")
    info.generator.write_text(
        "def build(m):\n"
        "    m.room('room', 0, 0, 512, 512)\n"
        "    m.player_start(256, 256)\n"
        "    m.thing(2001, 400, 400, 'room.shotgun')\n")
    build.build(info, repo)
    now = int(time.time())
    shots = inbox.shots_dir(info, repo)
    shots.mkdir(parents=True)
    shot = shots / "Screenshot_hello_0001.png"
    from PIL import Image

    Image.new("RGB", (1920, 1080), (40, 40, 40)).save(shot)
    os.utime(shot, (now - 5, now - 5))
    (info.build_dir(repo) / "log-play.txt").write_text(GAME_LOG.format(t=now))

    added = inbox.ingest_game_log(info, repo)
    assert [n["text"] for n in added] == ["this wall needs a window", "two of these"]
    wall, gun = added
    assert wall["pos"] == [200.0, 128.0, 0.0] and wall["angle"] == 90.0
    assert wall["standing_in"] == {"kind": "sector", "index": 0, "gid": "room"}
    assert wall["looking_at"] == {"kind": "linedef", "index": 1, "gid": "room.wall_n", "side": "front"}
    assert gun["looking_at"]["gid"] == "room.shotgun" and gun["looking_at"]["class"] == "Shotgun"
    assert wall["screenshot"] == "build/a/shots/Screenshot_hello_0001.png"
    assert wall["preview"] == "build/a/shots/preview/Screenshot_hello_0001.jpg"
    assert Image.open(repo / wall["preview"]).size == (960, 540)  # ~700 image tokens, not ~1,800
    text = inbox.describe(wall)
    assert "from the game at (200, 128, z 0) facing 90" in text and "looking at: linedef 1 (room.wall_n), side front" in text

    assert inbox.ingest_game_log(info, repo) == []          # once only
    assert len(inbox.notes(info, repo)) == 2


def test_a_monster_that_moved_is_matched_by_type():
    from dms.gen import MapBuilder

    m = MapBuilder()
    m.room("room", 0, 0, 512, 512)
    m.thing(3004, 136, 368, "platform_nw.zombieman")
    m.thing(2001, 400, 400, "room.shotgun")
    tm = m.textmap()
    hit = inbox._looking_at(tm, "thing class=Zombieman at=213.0,308.0")  # it walked 100 units
    assert hit["gid"] == "platform_nw.zombieman" and hit["type"] == 3004


def test_a_dead_monster_is_matched_by_where_it_was_placed():
    from dms.gen import MapBuilder

    m = MapBuilder()
    m.room("room", 0, 0, 512, 512)
    m.thing(3004, 136, 368, "zombie_a")
    m.thing(3004, 300, 300, "zombie_b")
    tm = m.textmap()
    # zombie_a walked right next to where zombie_b stands, then died there: its spawn point still says a.
    hit = inbox._looking_at(tm, "thing class=Zombieman at=298.0,302.0 spawn=136.0,368.0 health=-20")
    assert hit == {"kind": "thing", "index": 0, "gid": "zombie_a", "type": 3004, "class": "Zombieman", "dead": True}
    assert "thing 0 (zombie_a), class Zombieman, dead" in inbox.describe(
        {"id": 1, "map": "a", "source": "game", "text": "x", "looking_at": hit})
