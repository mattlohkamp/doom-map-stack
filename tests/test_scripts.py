import pytest

from dms import build, cli, launch, live, maps, scripts, wad

SCRIPT = b'''version "4.10"
// class Commented : EventHandler {}
class MapThing : EventHandler
{
}
class Helper : Actor {}
/* class AlsoCommented : EventHandler */
class Second:EventHandler {}
'''


@pytest.fixture
def repo(tmp_path, monkeypatch):
    (tmp_path / "maps").mkdir()
    monkeypatch.setattr(cli, "repo_root", lambda: tmp_path)
    return tmp_path


def test_handlers_are_found_outside_comments():
    assert scripts.handlers(SCRIPT) == ["MapThing", "Second"]
    assert scripts.handlers(None) == [] and scripts.handlers(b"") == []


def test_errors_are_read_from_the_log():
    log = ('LoadActors: Load actor definitions.\n'
           'Script error, "hello-room.wad:ZSCRIPT" line 28:\nUnexpected \'}\'\nExpecting \';\'\n\n'
           'Script error, "hello-room.wad:ZSCRIPT" line 40:\nUnknown identifier \'nope\'\n')
    assert scripts._errors(log) == ["zscript.zs line 28: Unexpected '}' Expecting ';'",
                                    "zscript.zs line 40: Unknown identifier 'nope'"]


def test_the_script_is_packed_and_registered_for_the_map_only(repo, monkeypatch):
    monkeypatch.setattr(scripts, "check", lambda info, root, w, code: [])
    info = maps.new(repo, "a")
    scripts.source(info).write_bytes(SCRIPT)
    build.build(info, repo)
    _, lumps = wad.read(info.wad(repo))
    by_name = {l.name: l.data for l in lumps}
    assert by_name["ZSCRIPT"] == SCRIPT
    mapinfo = by_name["MAPINFO"].decode()
    # Inside the map's own block, not GameInfo: it runs on this map only.
    assert 'EventHandlers = "MapThing", "Second"' in mapinfo.split("map MAP01")[1]
    # The editor's copy goes without (the editor doesn't run scripts).
    build.pack_edit_wad(info, repo)
    _, lumps = wad.read(info.edit_wad(repo))
    assert "ZSCRIPT" not in {l.name for l in lumps} and b"EventHandlers" not in lumps[0].data


def test_script_errors_fail_the_build(repo, monkeypatch, capsys):
    monkeypatch.setattr(scripts, "check", lambda info, root, w, code: ["zscript.zs line 3: Unexpected '}'"])
    info = maps.new(repo, "a")
    scripts.source(info).write_bytes(SCRIPT)
    assert build.build(info, repo).errors == 1
    assert "error: zscript.zs line 3" in capsys.readouterr().out


def test_without_uzdoom_the_check_is_skipped(repo):
    info = maps.new(repo, "a")
    scripts.source(info).write_bytes(SCRIPT)
    assert build.build(info, repo).errors == 0  # tools not set up in the test repo: not checked


def test_a_script_change_rebuilds(repo, monkeypatch):
    import os
    import time

    monkeypatch.setattr(scripts, "check", lambda info, root, w, code: [])
    info = maps.new(repo, "a")
    build.build(info, repo)
    assert not build.needs_build(info, repo)
    scripts.source(info).write_bytes(SCRIPT)
    later = time.time() + 5
    os.utime(scripts.source(info), (later, later))
    assert build.needs_build(info, repo)


def test_the_running_game_needs_a_restart_for_a_new_script(repo):
    info = maps.new(repo, "a")
    info.build_dir(repo).mkdir(parents=True)
    live.pack(info, repo, b"mapinfo", b'namespace = "zdoom";', 1, zscript=SCRIPT)
    assert live.update_map(info, repo, b"mapinfo", b'namespace = "zdoom";', 2, zscript=SCRIPT) == "updated"
    assert live.update_map(info, repo, b"mapinfo", b'namespace = "zdoom";', 3, zscript=SCRIPT + b"\n") == "restart"


def test_play_refuses_a_script_that_does_not_compile(repo, monkeypatch, capsys):
    info = maps.new(repo, "a")
    scripts.source(info).write_bytes(SCRIPT)
    monkeypatch.setattr(launch, "needs_build", lambda i, r: False)
    monkeypatch.setattr(scripts, "check", lambda i, r, w, code: ["zscript.zs line 3: Unexpected '}'"])
    assert launch.play(repo, info) == 1
    assert "doesn't compile" in capsys.readouterr().err
