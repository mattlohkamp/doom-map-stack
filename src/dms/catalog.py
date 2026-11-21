"""`dms catalog`: the wall textures and flats in the pinned IWAD, as committed text files.

    catalog/textures.tsv   name, width, height (from TEXTURE1/TEXTURE2)
    catalog/flats.txt      flat names (between F_START and F_END)

Each file starts with a comment naming the IWAD and its sha256, so it's clear which file the
catalog was built from (PLAN.md decision D3). Only names and sizes are stored, never graphics.
"""

from __future__ import annotations

import hashlib
import struct
from dataclasses import dataclass, field
from pathlib import Path

from dms import wad

CATALOG_DIR = "catalog"


@dataclass
class Catalog:
    textures: dict[str, tuple[int, int]] = field(default_factory=dict)  # NAME -> (width, height)
    flats: set[str] = field(default_factory=set)
    source: str = ""

    def has_texture(self, name: str) -> bool:
        return name.upper() in self.textures

    def has_flat(self, name: str) -> bool:
        return name.upper() in self.flats


def _texture_lump(data: bytes) -> dict[str, tuple[int, int]]:
    """Parse a TEXTURE1/TEXTURE2 lump: count, offsets, then maptexture entries."""
    (count,) = struct.unpack_from("<i", data, 0)
    offsets = struct.unpack_from(f"<{count}i", data, 4)
    out = {}
    for off in offsets:
        name = data[off : off + 8].rstrip(b"\0").decode("ascii", "replace").upper()
        width, height = struct.unpack_from("<hh", data, off + 12)
        out[name] = (width, height)
    return out


def from_iwad(iwad: Path) -> Catalog:
    _, lumps = wad.read(iwad)
    cat = Catalog(source=f"{iwad.name} sha256 {hashlib.sha256(iwad.read_bytes()).hexdigest()}")
    for lump_name in ("TEXTURE1", "TEXTURE2"):
        i = wad.find(lumps, lump_name)
        if i >= 0:
            cat.textures.update(_texture_lump(lumps[i].data))
    start, end = wad.find(lumps, "F_START"), wad.find(lumps, "F_END")
    if start < 0 or end < start:
        start, end = wad.find(lumps, "FF_START"), wad.find(lumps, "FF_END")
    for lump in lumps[start + 1 : end]:
        if lump.data and not lump.name.upper().endswith(("_START", "_END")):
            cat.flats.add(lump.name.upper())
    return cat


def write(cat: Catalog, root: Path) -> list[Path]:
    d = root / CATALOG_DIR
    d.mkdir(exist_ok=True)
    header = f"# Built by `dms catalog` from {cat.source}\n"
    tex = d / "textures.tsv"
    tex.write_text(
        header + "# name\twidth\theight\n"
        + "".join(f"{n}\t{w}\t{h}\n" for n, (w, h) in sorted(cat.textures.items())),
        encoding="utf-8", newline="\n",
    )
    flats = d / "flats.txt"
    flats.write_text(header + "".join(f"{n}\n" for n in sorted(cat.flats)), encoding="utf-8", newline="\n")
    return [tex, flats]


def load(root: Path) -> Catalog | None:
    """The committed catalog, or None if it hasn't been built yet."""
    d = root / CATALOG_DIR
    tex, flats = d / "textures.tsv", d / "flats.txt"
    if not (tex.exists() and flats.exists()):
        return None
    cat = Catalog()
    for line in tex.read_text(encoding="utf-8").splitlines():
        if line.startswith("# Built"):
            cat.source = line.split(" from ", 1)[-1]
        if not line or line.startswith("#"):
            continue
        name, w, h = line.split("\t")
        cat.textures[name] = (int(w), int(h))
    cat.flats = {l for l in flats.read_text(encoding="utf-8").splitlines() if l and not l.startswith("#")}
    return cat
