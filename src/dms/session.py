"""`dms session` (Start Session.cmd): get everything ready to work on one map live.

The session window (picker.pick_session) picks the map, or creates one, and what to open: the browser
on the board's page for that map, the editor and the game (windowed, `[play] windowed`), and a coding
agent. Defaults: `[session]` in dms.toml. The board isn't a choice: it always runs (auto-pull and the
game's restart need it). From Start Session.cmd (`--board-here`), the .cmd's own window becomes the
board once everything else is open; from a terminal, it gets a console window of its own. Nothing is
started twice: an already-running board is used as it is, and a running game or agent is brought to
the front. The editor never is, new or already open: it's one of several windows opening (Edit Map
does bring it forward).

The agent is started by Start Session.cmd, outside dms's environment, from what this writes to
build/session.txt: the map, the agent's launcher (none if no agent was chosen or one is already
watching notes for the map), and whether the .cmd should run the board (`board=1`, `browser=1` when the
board should open the page once it's up). Agents are listed under `[agents]` in dms.toml.
"""

from __future__ import annotations

import re
import subprocess
import time
from pathlib import Path

from dms import maps

SESSION_FILE = Path("build") / "session.txt"
PARTS = ("browser", "editor", "game")


def agents(settings: dict) -> dict[str, dict]:
    """The agents in dms.toml [agents] with a name and a launcher."""
    return {k: v for k, v in settings.get("agents", {}).items()
            if isinstance(v, dict) and v.get("name") and v.get("launcher")}


def defaults(settings: dict) -> dict:
    s = settings.get("session", {})
    return {**{p: bool(s.get(p, True)) for p in PARTS}, "agent": str(s.get("agent", ""))}


def launcher(root: Path, agent: dict) -> str:
    """The agent's launcher: a .bat or .cmd file directly in the repo root, no spaces in its name
    (checked, since Start Session.cmd runs it through `cmd /c`, which drops the quotes)."""
    name = str(agent["launcher"])
    if not re.fullmatch(r"[A-Za-z0-9._-]+\.(bat|cmd)", name) or not (root / name).is_file():
        raise maps.MapError(f"agent launcher {name!r} must be a .bat or .cmd file in the repo root, no spaces")
    return name


def _start_board(root: Path, port: int) -> bool:
    """The board in a console window of its own (it lists what reaches it). True once it answers."""
    from dms import board

    flags = getattr(subprocess, "CREATE_NEW_CONSOLE", 0)
    subprocess.Popen(
        ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(root / "dms.ps1"),
         "board", "--no-browser"],
        cwd=root, creationflags=flags, close_fds=True)
    for _ in range(60):  # uv and Python take a few seconds to start
        time.sleep(0.25)
        if board._running_here(port, root):
            print(f"    board: started on port {port} (its own window)")
            return True
    print("    board: didn't answer within 15 s; check its window")
    return False


def start(root: Path, info: maps.MapInfo, choices: dict, board_here: bool = False) -> int:
    """Open what `choices` asks for ({"browser": bool, ..., "agent": key or ""}) on the map, and make
    sure the board runs. board_here: the caller (Start Session.cmd) runs the board in its own window
    afterwards, if build/session.txt says so; otherwise a board that isn't running gets a window of its own."""
    from dms import agents as agents_mod
    from dms import board, inbox, launch, live, picker
    from dms.configure import project_settings

    settings = project_settings(root)
    known = agents(settings)
    agent_key = choices.get("agent") or ""
    if agent_key and agent_key not in known:
        raise maps.MapError(f"no agent {agent_key!r} under [agents] in dms.toml")
    port = int(settings["board"]["port"])
    board_status = board._running_here(port, root)
    if board_status is False:  # checked before anything opens: the session needs the board
        raise maps.MapError(f"the board's port {port} is used by something else; set another under [board] in dms.toml")
    picker.remember(root, info.name)  # also the map the board's page opens on
    print(f"dms session: {info.name} ({info.title})")
    if (choices.get("editor") or choices.get("game")) and launch.needs_build(info, root):
        launch.build(info, root)

    lines = [f"map={info.name}"]
    if board_status:
        print(f"    board: already running on port {port} (in another window)")
        board_up = True
    elif board_here:
        lines.append("board=1")
        board_up = False  # not yet: it starts in this window once everything else is open
        print("    board: starts in this window once everything else is open")
    else:
        board_up = _start_board(root, port)
    if choices.get("browser"):
        if board_up:
            board.open_pages(f"http://127.0.0.1:{port}/#{info.name}")
            print("    browser: the board, on this map, and the asset browser")
        elif board_here:
            lines.append("browser=1")  # the board opens it once it's listening
        else:
            print("    browser: skipped, the board isn't running")

    if choices.get("editor"):
        launch.edit(root, info, focus=False)  # one of several windows: no need to pull it to the front

    if choices.get("game"):
        if live.game_running(info, root):
            pid = _play_pid(info, root)
            print(f"    game: already running{f' (process {pid})' if pid else ''}; bringing it to the front")
            if pid:
                launch.focus_process_window(pid)
        else:
            launch.play(root, info)

    if agent_key:
        agent = known[agent_key]
        already = agents_mod.running(root)
        if already:
            # Hand the map to the running session (`dms watch` or its next prompt passes it on).
            agents_mod.request(root, info.name)
            pids = ", ".join(str(a["pid"]) for a in already)
            print(f"    agent: already running in this repo (process {pids}); not starting another. It hears about")
            print(f"           {info.name} from its note watch, or with your next message to it.")
            launch.focus_process_window(already[-1]["pid"])
        elif inbox.listening(root, info.name):
            print(f"    agent: one is already watching notes for {info.name}; not starting {agent['name']}")
        else:
            lines += [f"launcher={launcher(root, agent)}", f"title={_plain(agent['name'])} - {info.name}"]
            print(f"    agent: starting {agent['name']} (its own window)")
    p = root / SESSION_FILE
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("\n".join(lines) + "\n", encoding="ascii")
    return 0


def _plain(text: str) -> str:
    """Safe in a cmd window title: ASCII letters, digits, spaces and a few marks."""
    return re.sub(r"[^A-Za-z0-9 ._-]", "", text) or "Agent"


def _play_pid(info: maps.MapInfo, root: Path) -> int | None:
    import json

    try:
        pid = json.loads((info.build_dir(root) / "play.json").read_text(encoding="utf-8")).get("pid")
    except (OSError, ValueError):
        return None
    return pid if isinstance(pid, int) else None


def clear(root: Path) -> None:
    """Forget the last session's answer, so a cancelled window doesn't start an agent on an old map."""
    (root / SESSION_FILE).unlink(missing_ok=True)
