import pytest

from dms import board, cli, inbox, launch, live, maps, picker, session


@pytest.fixture
def repo(tmp_path, monkeypatch):
    (tmp_path / "maps").mkdir()
    (tmp_path / "start-claude.bat").write_text("@echo off\r\n")
    monkeypatch.setattr(cli, "repo_root", lambda: tmp_path)
    return tmp_path


@pytest.fixture
def calls(monkeypatch):
    """Stand-ins for everything that would open a window; records what was asked for."""
    got = []
    monkeypatch.setattr(session, "_start_board", lambda root, port: got.append(("board", port)) or True)
    monkeypatch.setattr(board, "_running_here", lambda port, root: None)
    monkeypatch.setattr(session.webbrowser, "open", lambda url: got.append(("browser", url)))
    monkeypatch.setattr(launch, "edit", lambda root, info, focus=True: got.append(("edit", info.name, focus)) or 0)
    monkeypatch.setattr(launch, "play", lambda root, info: got.append(("play", info.name)) or 0)
    monkeypatch.setattr(launch, "focus_process_window", lambda pid: got.append(("focus", pid)) or True)
    monkeypatch.setattr(launch, "needs_build", lambda info, root: False)
    return got


def _session(repo):
    return dict(line.split("=", 1) for line in (repo / session.SESSION_FILE).read_text().splitlines())


def test_dropped_map_opens_everything_by_default(repo, calls):
    maps.new(repo, "a")
    assert cli.main(["session", "a"]) == 0
    assert calls == [("board", 8765), ("browser", "http://127.0.0.1:8765/#a"), ("edit", "a", False), ("play", "a")]
    assert _session(repo) == {"map": "a", "launcher": "start-claude.bat", "title": "Claude Code - a"}
    assert (repo / "build" / "last-map.txt").read_text().strip() == "a"  # the window's next default


def test_window_choices_are_followed(repo, calls, monkeypatch):
    info = maps.new(repo, "a")
    seen = {}

    def fake_window(root, defaults, agents, agent_note=""):
        seen.update(defaults=defaults, agents=agents)
        return info, {"board": False, "browser": True, "editor": False, "game": True, "agent": ""}

    monkeypatch.setattr(picker, "pick_session", fake_window)
    assert cli.main(["session"]) == 0
    assert seen["defaults"] == {"board": True, "browser": True, "editor": True, "game": True, "agent": "claude"}
    assert seen["agents"] == {"claude": "Claude Code"}
    # No board running and none asked for: the browser is skipped too.
    assert calls == [("play", "a")]
    assert _session(repo) == {"map": "a"}  # no agent


def test_session_defaults_and_flags_from_dms_toml(repo, calls):
    maps.new(repo, "a")
    (repo / "dms.toml").write_text('[session]\ngame = false\nagent = ""\n')
    assert cli.main(["session", "a", "--no-editor"]) == 0
    assert [c[0] for c in calls] == ["board", "browser"]
    assert _session(repo) == {"map": "a"}


def test_session_reuses_a_running_game_and_agent(repo, calls, monkeypatch):
    info = maps.new(repo, "a")
    info.build_dir(repo).mkdir(parents=True)
    (info.build_dir(repo) / "play.json").write_text('{"pid": 4242}')
    monkeypatch.setattr(live, "game_running", lambda i, r: True)
    inbox.mark_listening(repo, ["a"])
    assert cli.main(["session", "a"]) == 0
    assert ("play", "a") not in calls and ("focus", 4242) in calls
    assert _session(repo) == {"map": "a"}  # an agent is already watching: none started


def test_a_running_agent_gets_the_map_instead_of_a_second_one(repo, calls, monkeypatch):
    from dms import agents

    maps.new(repo, "a")
    monkeypatch.setattr(agents, "running", lambda root: [{"pid": 777, "session_id": "s1"}])
    assert cli.main(["session", "a"]) == 0
    assert _session(repo) == {"map": "a"}  # nothing for the .cmd to start
    assert ("focus", 777) in calls
    assert agents.take_request(repo)["map"] == "a"


def test_cancelled_window_starts_nothing(repo, calls, monkeypatch):
    maps.new(repo, "a")
    (repo / "build").mkdir()
    (repo / session.SESSION_FILE).write_text("map=a\nlauncher=start-claude.bat\n")  # an earlier session's
    monkeypatch.setattr(picker, "pick_session", lambda root, defaults, agents, agent_note="": None)
    assert cli.main(["session"]) == 2
    assert calls == [] and not (repo / session.SESSION_FILE).exists()


@pytest.mark.parametrize("name", ["start other.bat", "..\\evil.bat", "start-x.exe", "missing.bat"])
def test_agent_launchers_are_checked(repo, name):
    with pytest.raises(maps.MapError):
        session.launcher(repo, {"name": "X", "launcher": name})


def test_board_on_a_foreign_port_is_reported(repo, monkeypatch, capsys):
    monkeypatch.setattr(board, "_running_here", lambda port, root: False)
    assert session._start_board(repo, 8765) is False
    assert "used by something else" in capsys.readouterr().out
