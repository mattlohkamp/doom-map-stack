"""maps/<map>/overrides.toml: property tweaks pulled from the editor (`dms pull`), keyed by gid.

Every build of a generated map applies them after map.py, so the mapper's tweaks survive rebuilds:

    [sector."room"]
    lightlevel = 200

    [sidedef."room.wall_n.front"]
    offsetx = 16

Tables are element kinds (thing, linedef, sidedef, sector), then gids, then UDMF fields. An override
applies to every element carrying that gid. Written by dms; hand edits are fine (it's plain TOML), but
comments in it are not kept when `pull` rewrites it.
"""

from __future__ import annotations

import json
import tomllib
from pathlib import Path

from dms import udmf
from dms.maps import MapInfo

FILENAME = "overrides.toml"
KINDS = ("thing", "linedef", "sidedef", "sector")
HEADER = (
    "# Property tweaks pulled from the editor (dms pull). Every build applies them after map.py,\n"
    "# keyed by gid: [<kind>.\"<gid>\"] then UDMF fields. Rewritten by `dms pull`.\n"
)


def path(info: MapInfo) -> Path:
    return info.folder / FILENAME


def load(info: MapInfo) -> dict[str, dict[str, dict]]:
    p = path(info)
    if not p.exists():
        return {}
    with p.open("rb") as f:
        data = tomllib.load(f)
    bad = set(data) - set(KINDS)
    if bad:
        raise ValueError(f"{p}: unknown element kind(s) {sorted(bad)}; use {', '.join(KINDS)}")
    return data


def _value(v) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, int):
        return str(v)
    if isinstance(v, float):
        return repr(v)
    if isinstance(v, str):
        return json.dumps(v)  # a TOML basic string
    raise TypeError(f"can't write {v!r} to {FILENAME}")


def dumps(data: dict[str, dict[str, dict]]) -> str:
    out = [HEADER]
    for kind in KINDS:
        for gid in sorted(data.get(kind, {})):
            fields = data[kind][gid]
            if not fields:
                continue
            out.append(f"\n[{kind}.{json.dumps(gid)}]\n")
            out += [f"{name} = {_value(fields[name])}\n" for name in sorted(fields)]
    return "".join(out)


def save(info: MapInfo, data: dict[str, dict[str, dict]]) -> None:
    path(info).write_text(dumps(data), encoding="utf-8", newline="\n")


def merge(data: dict, tweaks: dict[tuple[str, str], dict]) -> dict:
    """`tweaks` {(kind, gid): {field: value}} on top of `data`."""
    out = {k: {g: dict(f) for g, f in v.items()} for k, v in data.items()}
    for (kind, gid), fields in tweaks.items():
        out.setdefault(kind, {}).setdefault(gid, {}).update(fields)
    return out


def apply(tm: udmf.Textmap, data: dict) -> list[str]:
    """Apply overrides to a generated textmap in place. Returns warnings (gids that don't exist)."""
    warnings = []
    for kind, table in data.items():
        by_gid: dict[str, list[udmf.Block]] = {}
        for b in tm.of(kind):
            by_gid.setdefault(b.get("user_gid"), []).append(b)
        for gid, fields in table.items():
            blocks = by_gid.get(gid)
            if not blocks:
                warnings.append(f"{FILENAME}: no {kind} with gid {gid!r} (map.py no longer makes it); override ignored")
                continue
            for b in blocks:
                for name, value in fields.items():
                    b[name] = value
    return warnings
