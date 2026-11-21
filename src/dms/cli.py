"""The `dms` command. Run it as `.\\dms.ps1 <command>` from the repo root."""

import argparse
import sys

from dms import __version__
from dms.paths import repo_root


def cmd_setup(args: argparse.Namespace) -> int:
    from dms import setup

    return setup.run(repo_root(), upgrade=args.upgrade)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="dms", description="Doom map stack.")
    parser.add_argument("--version", action="version", version=f"dms {__version__}")
    sub = parser.add_subparsers(dest="command", metavar="<command>")

    setup = sub.add_parser("setup", help="download and configure the Doom tools in .tools/")
    setup.add_argument("--upgrade", metavar="TOOL", help="re-install TOOL after bumping tools.toml")
    setup.set_defaults(func=cmd_setup)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return 0
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
