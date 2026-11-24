"""Map folders: maps/<name>/ with map.toml, notes.md, map.py (generated mode) and TEXTMAP.

A map is named by its folder name (e.g. "hello-room"), never by slot. Commands take either that
name (looked up in the repo's maps/ folder) or a path to a map folder anywhere, so maps don't
have to live in this repo's maps/.
"""

from __future__ import annotations

import re
import tomllib
from dataclasses import dataclass
from pathlib import Path

KINDS = ("map", "test", "example")
SOURCE_MODES = ("generated", "hand-edited")
NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")


class MapError(Exception):
    pass


@dataclass
class MapInfo:
    name: str
    folder: Path
    title: str
    kind: str
    status: str
    source: str
    sky: str
    music: str

    @property
    def textmap(self) -> Path:
        return self.folder / "TEXTMAP"

    @property
    def generator(self) -> Path:
        return self.folder / "map.py"

    def build_dir(self, root: Path) -> Path:
        return root / "build" / self.name

    def wad(self, root: Path) -> Path:
        return self.build_dir(root) / f"{self.name}.wad"

    def edit_wad(self, root: Path) -> Path:
        return self.build_dir(root) / "edit.wad"


def maps_dir(root: Path) -> Path:
    return root / "maps"


def load(folder: Path) -> MapInfo:
    folder = folder.resolve()
    cfg_path = folder / "map.toml"
    if not cfg_path.exists():
        raise MapError(f"{folder} is not a map folder (no map.toml)")
    with cfg_path.open("rb") as f:
        cfg = tomllib.load(f)
    info = MapInfo(
        name=folder.name,
        folder=folder,
        title=cfg.get("title", folder.name),
        kind=cfg.get("kind", "map"),
        status=cfg.get("status", "draft"),
        source=cfg.get("source", "generated"),
        sky=cfg.get("sky", "SKY1"),
        music=cfg.get("music", ""),
    )
    if info.kind not in KINDS:
        raise MapError(f"{cfg_path}: kind must be one of {', '.join(KINDS)}")
    if info.source not in SOURCE_MODES:
        raise MapError(f"{cfg_path}: source must be one of {', '.join(SOURCE_MODES)}")
    return info


def resolve(root: Path, name_or_path: str | Path) -> MapInfo:
    """A map by name (maps/<name>) or by folder path (e.g. dropped onto a launcher)."""
    p = Path(name_or_path)
    if p.is_dir() and (p / "map.toml").exists():
        return load(p)
    by_name = maps_dir(root) / str(name_or_path)
    if (by_name / "map.toml").exists():
        return load(by_name)
    raise MapError(f"no map called {name_or_path!r} (looked for {by_name} and for a map folder at that path)")


def all_maps(root: Path) -> list[MapInfo]:
    d = maps_dir(root)
    if not d.is_dir():
        return []
    return [load(p) for p in sorted(d.iterdir()) if (p / "map.toml").exists()]


MAP_TOML = """\
title = "{title}"
kind = "{kind}"          # map | test | example
status = "draft"
source = "generated"   # generated (map.py is the source) | hand-edited (TEXTMAP is the source)
sky = "SKY1"
music = "D_RUNNIN"
"""

MAP_PY = '''\
"""{title}: the generator for this map. `.\\\\scripts\\\\dms.ps1 build {name}` turns it into TEXTMAP."""

from dms.gen import MapBuilder


def build(m: MapBuilder) -> None:
    # One 512 x 512 room, 128 high, with the player start in the middle facing north.
    m.room("room", 0, 0, 512, 512, floor=0, ceiling=128, light=192)
    m.player_start(256, 256, angle=90)
'''

NOTES_MD = """\
# {title}

## Design intent

## Feedback log
"""


def new(root: Path, name: str, kind: str = "map", title: str | None = None) -> MapInfo:
    if not NAME_RE.match(name):
        raise MapError(f"map names are lowercase letters, digits and dashes (got {name!r})")
    if kind not in KINDS:
        raise MapError(f"kind must be one of {', '.join(KINDS)}")
    folder = maps_dir(root) / name
    if folder.exists():
        raise MapError(f"{folder} already exists")
    title = title or name.replace("-", " ").capitalize()
    folder.mkdir(parents=True)
    for fname, template in (("map.toml", MAP_TOML), ("map.py", MAP_PY), ("notes.md", NOTES_MD)):
        (folder / fname).write_text(template.format(name=name, title=title, kind=kind), encoding="utf-8", newline="\n")
    return load(folder)
