"""The `dms` command. Run it as `.\\dms.ps1 <command>` from the repo root."""

import argparse
import sys
from pathlib import Path

from dms import __version__
from dms.paths import repo_root

MAP_HELP = "map name (maps/<name>) or path to a map folder"


def cmd_setup(args: argparse.Namespace) -> int:
    from dms import setup

    return setup.run(repo_root(), upgrade=args.upgrade)


def cmd_editor(args: argparse.Namespace) -> int:
    from dms import launch

    return launch.open_editor(repo_root(), args.wad)


def cmd_new(args: argparse.Namespace) -> int:
    from dms import maps

    info = maps.new(repo_root(), args.name, kind=args.kind, title=args.title)
    print(f"dms new: created {info.folder} ({info.kind}, {info.source})")
    print(f"    next: .\\dms.ps1 build {info.name}")
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    from dms import maps

    found = maps.all_maps(repo_root())
    if not found:
        print("no maps yet (create one with `dms new <name>`)")
    for m in found:
        print(f"{m.name:24} {m.kind:8} {m.source:12} {m.title}")
    return 0


def cmd_build(args: argparse.Namespace) -> int:
    from dms import build, maps

    root = repo_root()
    targets = maps.all_maps(root) if args.all else [maps.resolve(root, args.map)]
    errors = 0
    for info in targets:
        errors += build.build(info, root, force=args.force, note=args.note).errors
    return 1 if errors else 0


def cmd_board(args: argparse.Namespace) -> int:
    from dms import board
    from dms.configure import project_settings

    root = repo_root()
    port = args.port or int(project_settings(root)["board"]["port"])
    auto_pull = bool(project_settings(root)["board"]["auto_pull"])
    return board.serve(root, port, open_browser=not args.no_browser, auto_pull=auto_pull)


def cmd_catalog(args: argparse.Namespace) -> int:
    from dms import catalog
    from dms.launch import tool_path

    root = repo_root()
    cat = catalog.from_iwad(tool_path(root, "freedoom"))
    for p in catalog.write(cat, root):
        print(f"dms catalog: wrote {p}")
    print(f"    {len(cat.textures)} textures, {len(cat.flats)} flats from {cat.source}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    from dms import build, maps, udmf

    root = repo_root()
    info = maps.resolve(root, args.map)
    if args.edit:
        tm = build.read_edit_wad_textmap(info, root)
        title, report_path = f"validate {info.name} (edit.wad)", info.build_dir(root) / "validate-edit.txt"
    else:
        if not info.textmap.exists():
            raise build.BuildError(f"{info.textmap} doesn't exist yet (run `dms build {info.name}`)")
        tm = udmf.parse(info.textmap.read_text(encoding="utf-8"))
        title, report_path = f"validate {info.name}", info.build_dir(root) / "validate.txt"
    print(f"dms {title}")
    issues = build.check(tm, root, "validate", report_path)
    return 1 if any(i.severity == "error" for i in issues) else 0


def pick_map(root: Path, given: str | None, action: str):
    """The map named on the command line or dropped onto a launcher; with none, the picker window.
    Returns None if the picker was cancelled."""
    from dms import maps, picker

    if given:
        info = maps.resolve(root, given)
        picker.remember(root, info.name)
        return info
    return picker.pick_map(root, action)


def cmd_render(args: argparse.Namespace) -> int:
    from dms import build, maps, udmf

    root = repo_root()
    info = maps.resolve(root, args.map)
    if not info.textmap.exists():
        raise build.BuildError(f"{info.textmap} doesn't exist yet (run `dms build {info.name}`)")
    source = udmf.parse(info.textmap.read_text(encoding="utf-8"))
    if args.edit:
        tm = build.read_edit_wad_textmap(info, root)
        print(f"dms render {info.name} (edit.wad: the mapper's saved editor version)")
        issues = build.check(tm, root, "validate", info.build_dir(root) / "validate-edit.txt")
        moves = build.check_movement(tm, info.build_dir(root) / "movement-edit.txt")
        build.draw(info, root, tm, issues + moves.issues, source, suffix="-edit",
                   diff_title=f"{info.name}: edit.wad compared with TEXTMAP", moves=moves)
    else:
        print(f"dms render {info.name}")
        issues = build.check(source, root, "validate", info.build_dir(root) / "validate.txt")
        moves = build.check_movement(source, info.build_dir(root) / "movement.txt")
        build.draw(info, root, source, issues + moves.issues, None, moves=moves)
    return 0


def cmd_play(args: argparse.Namespace) -> int:
    from dms import launch

    root = repo_root()
    info = pick_map(root, args.map, "Play")
    if info is None:
        return 0
    return launch.play(root, info, skill=args.skill, nomonsters=args.nomonsters)


def cmd_edit(args: argparse.Namespace) -> int:
    from dms import launch

    root = repo_root()
    info = pick_map(root, args.map, "Edit")
    if info is None:
        return 0
    return launch.edit(root, info)


def cmd_session(args: argparse.Namespace) -> int:
    from dms import maps, picker, session

    from dms.configure import project_settings

    root = repo_root()
    session.clear(root)
    settings = project_settings(root)
    choices = session.defaults(settings)
    if args.map:  # dropped onto the launcher, or from a terminal: no window, the defaults
        info = maps.resolve(root, args.map)
        for part in session.PARTS:
            if getattr(args, f"no_{part}"):
                choices[part] = False
        if args.no_agent:
            choices["agent"] = ""
    else:
        from dms import agents

        names = {k: a["name"] for k, a in session.agents(settings).items()}
        already = agents.running(root)
        note = (f"already running here (process {already[-1]['pid']}): it'll be told the map, not started again"
                if already else "its own window; not started twice")
        picked = picker.pick_session(root, choices, names, agent_note=note)
        if picked is None:
            print("dms session: cancelled")
            return 2
        info, choices = picked
    return session.start(root, info, choices, board_here=args.board_here)


def cmd_pull(args: argparse.Namespace) -> int:
    from dms import pull

    root = repo_root()
    info = pick_map(root, args.map, "Pull")
    if info is None:
        return 0
    return pull.pull(info, root, ported=args.ported)


def cmd_notes(args: argparse.Namespace) -> int:
    from dms import inbox, maps

    root = repo_root()
    targets = [maps.resolve(root, args.map)] if args.map else maps.all_maps(root)
    if args.close is not None:
        if not args.map:
            raise maps.MapError("--close needs the map name")
        try:
            n = inbox.close(targets[0], root, args.close, args.reply or "")
        except KeyError as e:
            raise maps.MapError(str(e.args[0])) from None
        print(f"dms notes: closed {targets[0].name} #{n['id']}" + (f": {n['reply']}" if n.get("reply") else ""))
        return 0
    if args.hook:
        return _notes_hook(root, targets)
    shown = 0
    for info in targets:
        inbox.ingest_game_log(info, root)
        for n in inbox.notes(info, root):
            if args.all or n["status"] == "open":
                print(inbox.describe(n))
                shown += 1
    if not shown:
        print("no open notes" if not args.all else "no notes")
    return 0


def cmd_agent_hook(args: argparse.Namespace) -> int:
    """Claude Code's hooks (.claude/settings.json): `start` (SessionStart), `prompt` (UserPromptSubmit),
    `end` (SessionEnd). Records the running session (agents.py); on start and prompt, prints what the
    agent should know (a Start Session request, open notes no watch delivered), which Claude Code adds
    to its context. Never fails: a broken hook must not get in the mapper's way."""
    import json as _json

    from dms import agents, maps

    root = repo_root()
    try:
        data = _json.loads(sys.stdin.read() or "{}")
    except (ValueError, OSError):
        data = {}
    session_id = str(data.get("session_id") or "") if isinstance(data, dict) else ""
    try:
        if args.event == "end":
            agents.unregister(root, session_id)
            return 0
        agents.register(root, "claude", session_id)
        req = agents.take_request(root)
        if req:
            print(agents.request_text(req))
        if args.event == "prompt":
            return _notes_hook(root, maps.all_maps(root))
    except Exception as e:  # noqa: BLE001
        print(f"dms: the agent hook failed ({e})")
    return 0


def _notes_hook(root: Path, targets) -> int:
    """For Claude Code's UserPromptSubmit hook (.claude/settings.json): whatever it prints is added to
    the mapper's message. Silent when nothing is open; in full when no `dms watch` delivered the notes.
    Never fails the prompt."""
    from dms import inbox

    try:
        unheard, heard = [], []
        for info in targets:
            inbox.ingest_game_log(info, root)
            open_ = [n for n in inbox.notes(info, root) if n["status"] == "open"]
            if not open_:
                continue
            if inbox.listening(root, info.name):
                heard.append(f"{info.name} " + ", ".join(f"#{n['id']}" for n in open_))
            else:
                unheard.append((info.name, open_))
        for name, open_ in unheard:
            print(f"dms: {len(open_)} open note(s) for {name} that no `dms watch` delivered. Act on them "
                  f"(AGENTS.md, Notes for Claude), and arm `dms watch {name}` with the Monitor tool:")
            for n in open_:
                print(inbox.describe(n))
        if heard:
            print("dms: open notes (already shown by dms watch): " + "; ".join(heard))
    except Exception as e:  # noqa: BLE001 - a broken hook must not block the mapper's message
        print(f"dms: the notes hook failed ({e}); run `dms notes` by hand")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    from dms import live, maps

    root = repo_root()
    info = maps.resolve(root, args.map)
    text = " ".join(args.text).strip()
    if not live.game_running(info, root):
        print(f"dms status: {info.name} isn't being played (start it with Play Map)")
        return 0
    live.set_status(info, root, text)
    print(f"dms status: {info.name}: " + (f"showing \"{text}\" in the game" if text else "cleared"))
    return 0


def cmd_watch(args: argparse.Namespace) -> int:
    import time

    from dms import agents, board, inbox, maps

    root = repo_root()
    seen: dict[str, set[int]] = {}
    saves_seen: set[str] = set()

    def targets():
        return [maps.resolve(root, args.map)] if args.map else maps.all_maps(root)

    first = True
    print(f"dms watch: notes for {args.map or 'every map'}; Ctrl+C stops", flush=True)
    try:
        while True:
            # Tell the board, the game and the editor that Claude is listening (inbox.listening).
            inbox.mark_listening(root, [maps.resolve(root, args.map).name] if args.map else None)
            req = agents.take_request(root)  # Start Session found this agent running (agents.py)
            if req:
                print(agents.request_text(req), flush=True)
            for info in targets():
                # An editor save with structural changes waits for Claude to port it (pull.txt): say so once.
                pending = board.pending_save(info, root, board.editor_summary(info, root))
                if pending and pending.get("structural") and pending["time"] not in saves_seen:
                    saves_seen.add(pending["time"])
                    print(f"[DMS-EDIT] {info.name}: an editor save ({pending['time']}) has {pending['structural']} "
                          f"structural change(s) waiting: port them into map.py (build/{info.name}/pull.txt), "
                          f"then `dms pull {info.name} --ported`", flush=True)
                inbox.ingest_game_log(info, root)  # notes typed in the game
                notes = inbox.notes(info, root)
                known = seen.setdefault(info.name, set())
                for n in notes:
                    if n["id"] in known:
                        continue
                    known.add(n["id"])
                    if not first or n["status"] == "open":
                        print(inbox.describe(n), flush=True)
            first = False
            time.sleep(args.interval)
    except KeyboardInterrupt:
        inbox.stop_listening(root)
        return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="dms", description="Doom map stack.")
    parser.add_argument("--version", action="version", version=f"dms {__version__}")
    sub = parser.add_subparsers(dest="command", metavar="<command>")

    p = sub.add_parser("setup", help="download and configure the Doom tools in .tools/")
    p.add_argument("--upgrade", metavar="TOOL", help="re-install TOOL after bumping tools.toml")
    p.set_defaults(func=cmd_setup)

    p = sub.add_parser("editor", help="open Ultimate Doom Builder (portable mode), optionally with a WAD")
    p.add_argument("wad", nargs="?", type=Path, help="WAD to open")
    p.set_defaults(func=cmd_editor)

    p = sub.add_parser("new", help="create a new map folder in maps/")
    p.add_argument("name", help="lowercase letters, digits and dashes, e.g. hello-room")
    p.add_argument("--kind", choices=("map", "test", "example"), default="map")
    p.add_argument("--title", help="display title (default: from the name)")
    p.set_defaults(func=cmd_new)

    p = sub.add_parser("list", help="list the maps in maps/")
    p.set_defaults(func=cmd_list)

    p = sub.add_parser("build", help="generate TEXTMAP (generated maps) and pack build/<map>/<map>.wad")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("map", nargs="?", help=MAP_HELP)
    g.add_argument("--all", action="store_true", help="build every map in maps/")
    p.add_argument("--force", action="store_true", help="overwrite hand edits to TEXTMAP / unsaved edit.wad changes")
    p.add_argument("--note", help="what changed and what to check; shown with this build on the board")
    p.set_defaults(func=cmd_build)

    p = sub.add_parser("board", help="serve the board (build history, editor state, play log) and open it in the browser")
    p.add_argument("--port", type=int, help="default: [board] port in dms.toml (8765)")
    p.add_argument("--no-browser", action="store_true", help="don't open the browser")
    p.set_defaults(func=cmd_board)

    p = sub.add_parser("catalog", help="list the IWAD's textures and flats into catalog/ (for the validator)")
    p.set_defaults(func=cmd_catalog)

    p = sub.add_parser("validate", help="check a map's TEXTMAP (or the editor's edit.wad) for problems")
    p.add_argument("map", help=MAP_HELP)
    p.add_argument("--edit", action="store_true", help="check build/<map>/edit.wad (the mapper's saved edits)")
    p.set_defaults(func=cmd_validate)

    p = sub.add_parser("render", help="draw build/<map>/render.png (+ .txt); --edit: the mapper's edit.wad, with a diff")
    p.add_argument("map", help=MAP_HELP)
    p.add_argument("--edit", action="store_true", help="render build/<map>/edit.wad and diff it against TEXTMAP")
    p.set_defaults(func=cmd_render)

    p = sub.add_parser("play", help="build if needed, then play the map in UZDoom")
    p.add_argument("map", nargs="?", help=MAP_HELP + "; none: choose from a list")
    p.add_argument("--skill", type=int, choices=range(1, 6), default=3, help="1-5 (default 3, Hurt Me Plenty)")
    p.add_argument("--nomonsters", action="store_true")
    p.set_defaults(func=cmd_play)

    p = sub.add_parser("edit", help="open the map in Ultimate Doom Builder (as build/<map>/edit.wad)")
    p.add_argument("map", nargs="?", help=MAP_HELP + "; none: choose from a list")
    p.set_defaults(func=cmd_edit)

    p = sub.add_parser("session", help="pick or create a map, then start the board and open the browser, editor and game for it")
    p.add_argument("map", nargs="?", help=MAP_HELP + "; none: the session window (choose, or start a new map)")
    for part in ("browser", "editor", "game", "agent"):
        p.add_argument(f"--no-{part}", action="store_true", help=f"with a map: don't open the {part}")
    p.add_argument("--board-here", action="store_true",
                   help="(Start Session.cmd) leave starting the board to the caller's window, via build/session.txt")
    p.set_defaults(func=cmd_session)

    p = sub.add_parser("agent-hook", help="(run by Claude Code's hooks, .claude/settings.json)")
    p.add_argument("event", choices=("start", "prompt", "end"))
    p.set_defaults(func=cmd_agent_hook)

    p = sub.add_parser("notes", help="list the mapper's notes (open ones by default), or close one")
    p.add_argument("map", nargs="?", help=MAP_HELP + "; none: every map")
    p.add_argument("--all", action="store_true", help="closed notes too")
    p.add_argument("--close", type=int, metavar="ID", help="mark note ID as dealt with")
    p.add_argument("--reply", help="with --close: what was done (shown on the board)")
    p.add_argument("--hook", action="store_true", help=argparse.SUPPRESS)  # Claude Code's prompt hook
    p.set_defaults(func=cmd_notes)

    p = sub.add_parser("status", help="show what Claude is doing in the running game (a line with moving dots)")
    p.add_argument("map", help=MAP_HELP)
    p.add_argument("text", nargs="*", help="e.g. cutting the hallway; nothing clears it")
    p.set_defaults(func=cmd_status)

    p = sub.add_parser("watch", help="print the mapper's notes as they arrive (open ones first)")
    p.add_argument("map", nargs="?", help=MAP_HELP + "; none: every map")
    p.add_argument("--interval", type=float, default=1.0, help=argparse.SUPPRESS)
    p.set_defaults(func=cmd_watch)

    p = sub.add_parser("pull", help="bring saved editor changes (build/<map>/edit.wad) back into the map's source")
    p.add_argument("map", nargs="?", help=MAP_HELP + "; none: choose from a list")
    p.add_argument("--ported", action="store_true",
                   help="the structural changes are now in map.py: write the tweaks and rebuild")
    p.set_defaults(func=cmd_pull)

    return parser


def main(argv: list[str] | None = None) -> int:
    from dms.build import BuildError
    from dms.maps import MapError
    from dms.pull import PullError

    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return 0
    try:
        return args.func(args)
    except (BuildError, MapError, PullError) as e:
        print(f"dms: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
