import io
import json
import os

import pytest

from dms import agents, cli, inbox, maps


@pytest.fixture
def repo(tmp_path, monkeypatch):
    (tmp_path / "maps").mkdir()
    monkeypatch.setattr(cli, "repo_root", lambda: tmp_path)
    return tmp_path


def _tree(claude_pid=500):
    """A process list where this process runs under claude.exe (via a shell and powershell)."""
    me = os.getpid()
    return {me: (12, "python.exe"), 12: (11, "powershell.exe"), 11: (claude_pid, "cmd.exe"),
            claude_pid: (4, "claude.exe"), 4: (0, "explorer.exe")}


def test_register_finds_the_claude_process_and_running_checks_it(repo):
    procs = _tree()
    rec = agents.register(repo, "claude", "abc-123", procs)
    assert (rec["pid"], rec["exe"]) == (500, "claude.exe")
    assert [a["session_id"] for a in agents.running(repo, procs)] == ["abc-123"]
    # The process is gone, or its id now belongs to something else: not running, record removed.
    assert agents.running(repo, {**procs, 500: (4, "notepad.exe")}) == []
    assert not (repo / "build" / "agents" / "abc-123.json").exists()


def test_register_outside_claude_or_with_a_bad_id_does_nothing(repo):
    assert agents.register(repo, "claude", "abc", {os.getpid(): (1, "python.exe")}) is None
    assert agents.register(repo, "claude", "../evil", _tree()) is None
    assert agents.running(repo, _tree()) == []


def test_unregister(repo):
    agents.register(repo, "claude", "abc", _tree())
    agents.unregister(repo, "abc")
    assert agents.running(repo, _tree()) == []


def test_a_request_is_delivered_once(repo):
    agents.request(repo, "a")
    req = agents.take_request(repo)
    assert req["map"] == "a" and "dms watch a" in agents.request_text(req)
    assert agents.take_request(repo) is None


def test_prompt_hook_registers_and_passes_on_the_request(repo, monkeypatch, capsys):
    monkeypatch.setattr(agents, "processes", _tree)
    maps.new(repo, "a")
    agents.request(repo, "a")
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps({"session_id": "s1"})))
    assert cli.main(["agent-hook", "prompt"]) == 0
    out = capsys.readouterr().out
    assert "[DMS-SESSION]" in out and "dms watch a" in out
    assert [a["session_id"] for a in agents.running(repo, _tree())] == ["s1"]
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps({"session_id": "s1"})))
    assert cli.main(["agent-hook", "end"]) == 0
    assert agents.running(repo, _tree()) == []


def test_prompt_hook_never_fails(repo, monkeypatch, capsys):
    monkeypatch.setattr("sys.stdin", io.StringIO("not json"))  # unreadable input: nothing recorded, no error
    assert cli.main(["agent-hook", "prompt"]) == 0
    monkeypatch.setattr("sys.stdin", io.StringIO('{"session_id": "s1"}'))
    monkeypatch.setattr(agents, "processes", lambda: (_ for _ in ()).throw(OSError("boom")))
    assert cli.main(["agent-hook", "prompt"]) == 0
    assert "hook failed" in capsys.readouterr().out


def test_notes_still_reach_the_prompt_hook(repo, monkeypatch, capsys):
    monkeypatch.setattr(agents, "processes", _tree)
    info = maps.new(repo, "a")
    inbox.add(info, repo, "more light", "game")
    monkeypatch.setattr("sys.stdin", io.StringIO("{}"))
    cli.main(["agent-hook", "prompt"])
    assert '"more light"' in capsys.readouterr().out
