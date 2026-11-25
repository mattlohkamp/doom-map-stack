"""Projects: where maps live, outside the tool if need be (docs/projects.md).

A project is a folder with a `dms-project.toml`, its maps in `maps/<name>/`, its themes in `themes/` and
everything generated in `build/`. The tool repo is a project too (its example maps): the default one,
and the only one without a `dms-project.toml` (nothing new goes in its root).

Which project: `dms --project PATH`, else `DMS_PROJECT`, else the folder the command runs in (or the
nearest above it with a `dms-project.toml`), else the tool repo. The command line works that out once
(`cli.main`, `choose`) and puts it in `DMS_PROJECT`, so everything below, and every program dms starts
(the board, the game's watchers), reads the same answer from there and never from the current folder.
"""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

PROJECT_FILE = "dms-project.toml"
ENV = "DMS_PROJECT"


class ProjectError(Exception):
    pass


@dataclass(frozen=True)
class Project:
    path: Path
    title: str = ""
    settings: dict = field(default_factory=dict, compare=False, hash=False)

    @property
    def maps(self) -> Path:
        return self.path / "maps"

    @property
    def build(self) -> Path:
        return self.path / "build"

    @property
    def themes(self) -> Path:
        return self.path / "themes"


def is_project(folder: Path) -> bool:
    return (folder / PROJECT_FILE).is_file()


def find_from(start: Path) -> Path | None:
    """The nearest folder at or above `start` with a dms-project.toml."""
    start = start.resolve()
    for p in (start, *start.parents):
        if is_project(p):
            return p
    return None


def choose(root: Path, given: str | Path | None = None) -> Path:
    """Works out the project for this command (see the module's notes) and records it in DMS_PROJECT."""
    if given:
        p = Path(given).resolve()
        if not is_project(p) and p != root.resolve():
            raise ProjectError(f"{p} isn't a project (no {PROJECT_FILE})")
    elif os.environ.get(ENV):
        p = Path(os.environ[ENV]).resolve()
        if not is_project(p) and p != root.resolve():
            raise ProjectError(f"{ENV}={p} isn't a project (no {PROJECT_FILE})")
    else:
        p = find_from(Path.cwd()) or root.resolve()
    os.environ[ENV] = str(p)
    return p


def path(root: Path) -> Path:
    """The project this command acts on: DMS_PROJECT once `choose` has run; else `root` (also how tests and
    library callers that pass their own root get theirs)."""
    env = os.environ.get(ENV)
    return Path(env) if env else root


def build_dir(root: Path) -> Path:
    """The project's build folder (everything generated)."""
    return path(root) / "build"


def load(folder: Path) -> Project:
    f = folder / PROJECT_FILE
    try:
        data = tomllib.loads(f.read_text(encoding="utf-8")) if f.is_file() else {}
    except tomllib.TOMLDecodeError as e:
        raise ProjectError(f"{f}: {e}") from None
    return Project(folder, str(data.get("title") or folder.name), data)


def current(root: Path) -> Project:
    return load(path(root))


def of_map(folder: Path) -> Path:
    """The project a map folder belongs to: the folder above its maps/; else (a map folder kept somewhere
    else) the nearest project above it; else the current one."""
    folder = folder.resolve()
    if folder.parent.name == "maps":
        return folder.parent.parent
    return find_from(folder.parent) or Path(os.environ.get(ENV) or folder.parent)
