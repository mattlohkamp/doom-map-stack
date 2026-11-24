"""A map's own textures: optional text lumps packed into its WAD beside the map.

maps/<map>/textures.txt becomes the TEXTURES lump and maps/<map>/animdefs.txt the ANIMDEFS lump (UZDoom's
text formats): new textures composed from the game's own (turned, cut, recoloured, layered), and how
they animate. Only text is committed: the pictures are put together by the engine from what the IWAD
has, so no graphics enter the repo. They go into the game's WAD, the live copy the game runs
(live.py) and edit.wad (the editor shows them). UZDoom reads them only at startup, so a change means a
restart of the running game, like a script change. The validator learns the names from textures.txt.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

from dms import wad
from dms.maps import MapInfo

FILES = (("textures.txt", "TEXTURES"), ("animdefs.txt", "ANIMDEFS"))
LUMPS = tuple(name for _, name in FILES)
# WallTexture "NAME", 64, 128   /   Flat NAME, 64, 64   /   Texture "NAME", ...
DEFINITION = re.compile(r'^\s*(walltexture|texture|flat)\s+(?:optional\s+)?"?([A-Za-z0-9_\-\[\]\\^]+)"?\s*,\s*(\d+)\s*,\s*(\d+)',
                        re.IGNORECASE | re.MULTILINE)


def folder(info: MapInfo) -> Path:
    return info.textmap.parent


def lumps(info: MapInfo) -> list[wad.Lump]:
    """The map's extra lumps, in a fixed order; none when it has no such files."""
    out = []
    for fname, lump in FILES:
        f = folder(info) / fname
        if f.is_file():
            out.append(wad.Lump(lump, f.read_bytes()))
    return out


def digest(extra: list[wad.Lump]) -> str:
    """Changes when any extra lump does (the running game must restart to see it)."""
    h = hashlib.sha256()
    for lump in extra:
        h.update(lump.name.encode("ascii") + b"\0" + lump.data + b"\0")
    return h.hexdigest()


def textures(info: MapInfo) -> tuple[dict[str, tuple[int, int]], set[str]]:
    """(wall textures: NAME -> (width, height), flats) the map's textures.txt defines."""
    f = folder(info) / "textures.txt"
    walls: dict[str, tuple[int, int]] = {}
    flats: set[str] = set()
    if not f.is_file():
        return walls, flats
    text = re.sub(r"//[^\n]*", "", f.read_text(encoding="utf-8"))
    for kind, name, w, h in DEFINITION.findall(text):
        if kind.lower() == "flat":
            flats.add(name.upper())
        else:
            walls[name.upper()] = (int(w), int(h))
    return walls, flats
