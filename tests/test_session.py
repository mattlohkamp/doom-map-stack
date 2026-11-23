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
    monkeypatch.setattr(board, "open_pages", lambda url: got.append(("browser", url)))
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
        return info, {"browser": True, "editor": False, "game": True, "agent": ""}

    monkeypatch.setattr(picker, "pick_session", fake_window)
    assert cli.main(["session"]) == 0
    assert seen["defaults"] == {"browser": True, "editor": True, "game": True, "agent": "claude"}
    assert seen["agents"] == {"claude": "Claude Code"}
    # The board isn't a choice: it's started either way.
    assert calls == [("board", 8765), ("browser", "http://127.0.0.1:8765/#a"), ("play", "a")]
    assert _session(repo) == {"map": "a"}  # no agent


def test_start_session_cmd_runs_the_board_itself(repo, calls):
    maps.new(repo, "a")
    assert cli.main(["session", "a", "--board-here"]) == 0
    # No board window and no browser yet: the .cmd's own window becomes the board, which opens the page.
    assert calls == [("edit", "a", False), ("play", "a")]
    assert _session(repo) == {"map": "a", "board": "1", "browser": "1",
                              "launcher": "start-claude.bat", "title": "Claude Code - a"}
    assert cli.main(["session", "a", "--board-here", "--no-browser", "--no-agent"]) == 0
    assert _session(repo) == {"map": "a", "board": "1"}


def test_a_running_board_is_used_as_it_is(repo, calls, monkeypatch):
    maps.new(repo, "a")
    monkeypatch.setattr(board, "_running_here", lambda port, root: True)
    assert cli.main(["session", "a", "--board-here", "--no-agent"]) == 0
    assert calls[0] == ("browser", "http://127.0.0.1:8765/#a")  # straight away; no second board
    assert _session(repo) == {"map": "a"}  # nothing for the .cmd to run


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


def test_board_on_a_foreign_port_stops_the_session(repo, calls, monkeypatch):
    maps.new(repo, "a")
    monkeypatch.setattr(board, "_running_here", lambda port, root: False)
    with pytest.raises(maps.MapError, match="used by something else"):
        session.start(repo, maps.resolve(repo, "a"), session.defaults({}), board_here=True)
    assert calls == []  # checked before anything opens


def test_open_pages_opens_the_asset_browser_then_the_board(monkeypatch):
    opened = []
    monkeypatch.setattr(board.webbrowser, "open_new_tab", opened.append)
    monkeypatch.setattr(board.time, "sleep", lambda s: None)
    board.open_pages("http://127.0.0.1:8765/#a")
    assert opened == ["http://127.0.0.1:8765/assets", "http://127.0.0.1:8765/#a"]  # the board in front
