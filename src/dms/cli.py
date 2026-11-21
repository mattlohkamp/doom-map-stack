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
    for info in targets:
        build.build(info, root, force=args.force)
    return 0


def pick_map(root: Path, given: str | None, action: str):
    """The map named on the command line or dropped onto a launcher; with none, the picker window.
    Returns None if the picker was cancelled."""
    from dms import maps, picker

    if given:
        info = maps.resolve(root, given)
        picker.remember(root, info.name)
        return info
    return picker.pick_map(root, action)


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
    p.set_defaults(func=cmd_build)

    p = sub.add_parser("play", help="build if needed, then play the map in UZDoom")
    p.add_argument("map", nargs="?", help=MAP_HELP + "; none: choose from a list")
    p.add_argument("--skill", type=int, choices=range(1, 6), default=3, help="1-5 (default 3, Hurt Me Plenty)")
    p.add_argument("--nomonsters", action="store_true")
    p.set_defaults(func=cmd_play)

    p = sub.add_parser("edit", help="open the map in Ultimate Doom Builder (as build/<map>/edit.wad)")
    p.add_argument("map", nargs="?", help=MAP_HELP + "; none: choose from a list")
    p.set_defaults(func=cmd_edit)

    return parser


def main(argv: list[str] | None = None) -> int:
    from dms.build import BuildError
    from dms.maps import MapError

    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return 0
    try:
        return args.func(args)
    except (BuildError, MapError) as e:
        print(f"dms: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
