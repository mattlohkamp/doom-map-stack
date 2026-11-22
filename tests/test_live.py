import pytest

from dms import build, inbox, live, maps, wad


@pytest.fixture
def repo(tmp_path):
    (tmp_path / "maps").mkdir()
    return tmp_path


def _lump(path, name):
    _, lumps = wad.read(path)
    return lumps[wad.find(lumps, name)].data


def test_play_wad_is_rewritten_in_place(repo, monkeypatch):
    info = maps.new(repo, "a")
    build.build(info, repo)
    p = live.pack(info, repo, b'map MAP01 "A" {}', b'namespace = "zdoom";', 1)
    layout = wad.read_directory(p)[1]
    assert _lump(p, "DMSLIVE").decode().startswith("DMSLIVE 1\nbuild 1\nrestart 0\n")

    assert live.update_map(info, repo, b'map MAP01 "A" {}', b'namespace = "zdoom"; // v2', 2) == "updated"
    assert live.post(info, repo, "Claude, note #3: done") and live.post(info, repo, "second")
    assert wad.read_directory(p)[1] == layout                      # same layout: the game can keep reading it
    assert _lump(p, "TEXTMAP").rstrip() == b'namespace = "zdoom"; // v2'
    text = _lump(p, "DMSLIVE").decode().rstrip()
    assert "build 2" in text and "msg 1 Claude, note #3: done" in text and text.endswith("msg 2 second")

    big = b"x" * (live.MIN_SLOT + 1)                                 # outgrew its slot
    assert live.update_map(info, repo, b"", big, 3) == "restart"
    assert "restart 1" in _lump(p, "DMSLIVE").decode()
    assert wad.read_directory(p)[1] == layout


def test_closing_a_note_posts_to_a_running_game(repo, monkeypatch):
    info = maps.new(repo, "a")
    build.build(info, repo)
    live.pack(info, repo, b"", b'namespace = "zdoom";', 1)
    n = inbox.add(info, repo, "barrel here", "game")
    monkeypatch.setattr(live, "game_running", lambda i, r: False)
    inbox.close(info, repo, n["id"], "not shown: no game")
    assert "msg" not in _lump(live.play_wad(info, repo), "DMSLIVE").decode()
    n = inbox.add(info, repo, "and here", "game")
    monkeypatch.setattr(live, "game_running", lambda i, r: True)
    inbox.close(info, repo, n["id"], "added a barrel")
    assert f"Claude, note #{n['id']}: added a barrel" in _lump(live.play_wad(info, repo), "DMSLIVE").decode()


def test_a_build_updates_a_running_game(repo, monkeypatch, capsys):
    info = maps.new(repo, "a")
    build.build(info, repo)
    _, lumps = wad.read(info.wad(repo))
    live.pack(info, repo, lumps[0].data, lumps[2].data, 1)
    monkeypatch.setattr(live, "game_running", lambda i, r: True)
    info.generator.write_text(info.generator.read_text().replace("light=192", "light=100"))
    build.build(info, repo)
    assert b"lightlevel = 100" in _lump(live.play_wad(info, repo), "TEXTMAP")
    assert "press H in the game" in capsys.readouterr().out


def test_game_notes_are_acknowledged_and_shown_as_status(repo, monkeypatch):
    import time

    info = maps.new(repo, "a")
    build.build(info, repo)
    live.pack(info, repo, b"", b'namespace = "zdoom";', 1)
    monkeypatch.setattr(live, "game_running", lambda i, r: True)
    t = int(time.time())
    (info.build_dir(repo) / "log-play.txt").write_text(
        f"[DMS-NOTE-TEXT] 1 {t} put a barrel here\n[DMS-NOTE-TEXT] 2 {t} and a door\n")
    inbox.ingest_game_log(info, repo)
    text = _lump(live.play_wad(info, repo), "DMSLIVE").decode()
    assert 'Got note #1: "put a barrel here" - but Claude isn\'t watching' in text and 'Got note #2: "and a door"' in text
    assert "status 2 note(s) waiting, but Claude isn't watching" in text   # no dms watch running

    inbox.mark_listening(repo, None)                                      # now there is
    (info.build_dir(repo) / "log-play.txt").write_text(
        f"[DMS-NOTE-TEXT] 1 {t} put a barrel here\n[DMS-NOTE-TEXT] 2 {t} and a door\n[DMS-NOTE-TEXT] 3 {t} more light\n")
    inbox.ingest_game_log(info, repo)
    text = _lump(live.play_wad(info, repo), "DMSLIVE").decode()
    assert 'Got note #3: "more light"\n' in text and "status working on note #1 (2 more waiting)" in text
    inbox.close(info, repo, 3, "brighter")

    live.set_status(info, repo, "cutting the door")                      # Claude says what it's doing
    assert "status cutting the door" in _lump(live.play_wad(info, repo), "DMSLIVE").decode()
    inbox.close(info, repo, 1, "barrel added")
    assert "status working on note #2\n" in _lump(live.play_wad(info, repo), "DMSLIVE").decode()
    inbox.close(info, repo, 2, "door added")
    assert "status \n" in _lump(live.play_wad(info, repo), "DMSLIVE").decode()   # all done: cleared


def test_each_start_gets_its_own_live_copy(repo):
    """A game still running from an earlier start keeps reading its own file, never a rewritten one
    (2026-11-21: an old game read the new copy's script where its map used to be)."""
    import time

    info = maps.new(repo, "a")
    info.build_dir(repo).mkdir(parents=True)
    first = live.pack(info, repo, b"mapinfo", b'namespace = "zdoom";', 1)
    time.sleep(0.01)
    second = live.pack(info, repo, b"mapinfo", b'namespace = "zdoom";', 2, zscript=b'version "4.10"\n')
    assert first != second and live.play_wad(info, repo) == second
    assert not first.exists()  # nothing had it open: cleaned up


def test_play_does_not_start_a_second_game(repo, monkeypatch, capsys):
    from dms import launch

    info = maps.new(repo, "a")
    info.build_dir(repo).mkdir(parents=True)
    (info.build_dir(repo) / "play.json").write_text('{"pid": 4242}')
    monkeypatch.setattr(live, "game_running", lambda i, r: True)
    focused = []
    monkeypatch.setattr(launch, "focus_process_window", lambda pid: focused.append(pid) or True)
    assert launch.play(repo, info) == 0
    assert focused == [4242] and "already being played" in capsys.readouterr().out
