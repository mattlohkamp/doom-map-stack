"""Read and write WAD files (a header, the lump data, and a directory of name/offset/size)."""

from __future__ import annotations

import struct
from dataclasses import dataclass
from pathlib import Path

HEADER = struct.Struct("<4sii")  # "IWAD"/"PWAD", lump count, directory offset
ENTRY = struct.Struct("<ii8s")  # data offset, size, name (NUL-padded)


class WadError(Exception):
    pass


@dataclass
class Lump:
    name: str
    data: bytes = b""


def read(path: Path) -> tuple[str, list[Lump]]:
    """Return (kind, lumps), kind being "IWAD" or "PWAD"."""
    raw = path.read_bytes()
    if len(raw) < HEADER.size:
        raise WadError(f"{path}: too short to be a WAD")
    kind, count, diroffs = HEADER.unpack_from(raw, 0)
    kind = kind.decode("ascii", "replace")
    if kind not in ("IWAD", "PWAD") or count < 0 or diroffs + count * ENTRY.size > len(raw):
        raise WadError(f"{path}: not a valid WAD")
    lumps = []
    for i in range(count):
        offs, size, name = ENTRY.unpack_from(raw, diroffs + i * ENTRY.size)
        if offs < 0 or size < 0 or offs + size > len(raw):
            raise WadError(f"{path}: lump {i} points outside the file")
        lumps.append(Lump(name.rstrip(b"\0").decode("ascii", "replace"), raw[offs : offs + size]))
    return kind, lumps


def write(path: Path, lumps: list[Lump], kind: str = "PWAD") -> None:
    data = bytearray(HEADER.size)
    directory = bytearray()
    for lump in lumps:
        name = lump.name.upper().encode("ascii")
        if len(name) > 8:
            raise WadError(f"lump name too long: {lump.name}")
        directory += ENTRY.pack(len(data) if lump.data else 0, len(lump.data), name)
        data += lump.data
    HEADER.pack_into(data, 0, kind.encode("ascii"), len(lumps), len(data))
    path.parent.mkdir(parents=True, exist_ok=True)
    out = bytes(data + directory)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_bytes(out)
    try:
        tmp.replace(path)
    except PermissionError:
        # The editor keeps the WAD it has open (edit.wad) and won't let it be replaced or deleted,
        # but allows writing to it; so overwrite it in place. Its plugin reloads once it sees the change.
        tmp.unlink()
        with open(path, "r+b") as f:
            f.write(out)
            f.truncate()


def find(lumps: list[Lump], name: str, start: int = 0) -> int:
    """Index of the first lump called `name` at or after `start`, or -1."""
    name = name.upper()
    for i in range(start, len(lumps)):
        if lumps[i].name.upper() == name:
            return i
    return -1
