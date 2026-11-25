"""Themes: sets of textures, things and atmosphere that belong together (docs/themes.md).

A theme is `themes/<name>/theme.toml`, shared by every map. `harvest` drafts one from a part of a
map (the sectors whose gids match some patterns); `check` looks every theme over.
"""

from __future__ import annotations

import fnmatch
import re
import tomllib
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from dms.udmf import Textmap

# role -> what it's for. The order is the order `show` and the draft list them in.
ROLES = {
    "wall": "the main wall surface",
    "wall_alt": "a second wall surface, for variety",
    "wall_base": "a strip along the foot of walls",
    "trim": "frames, beams, edges: what holds things together",
    "door": "door faces",
    "door_frame": "the jambs and lintel round a door",
    "step": "the faces of steps and ledges",
    "floor": "the main floor",
    "floor_alt": "other floors",
    "ceiling": "ceilings",
    "light": "a lit fixture: a light panel, a tube",
    "switch": "switch faces",
    "liquid": "water, slime and the like",
    "sky": "the sky where the area is open",
}
THING_ROLES = {
    "light_source": "what lights the place: dynamic lights, torches, lamps",
    "decoration": "scenery that belongs to the look",
}
ATMOSPHERE = {
    "light": "the usual sector light",
    "light_range": "the darkest and brightest it goes",
    "lightcolor": "sector light tint, RRGGBB ('' for none)",
    "fog": "fog colour, RRGGBB ('' for none)",
    "fogdensity": "fog density (0 for the engine's default)",
}

NAME_OK = re.compile(r"[a-z0-9][a-z0-9-]*")
HEX = re.compile(r"[0-9A-Fa-f]{6}")
DOOR_SPECIALS = {10, 11, 12, 13, 14, 202, 249}
LIQUIDS = ("NUKAGE", "FWATER", "SWATER", "BLOOD", "LAVA", "SLIME", "WFALL", "SFALL", "BFALL", "RROCK05", "RROCK08")
LIGHTS = ("LITE", "TLITE", "GRNLITE", "CEIL1_2", "CEIL1_3", "FLOOR1_7")
LIGHT_THINGS = {34, 35, 44, 45, 46, 55, 56, 57, 70, 85, 86, 2028}   # candles, torches, lamps, burning barrel
SKY_FLAT = "F_SKY1"
STEP = 24          # a lower part this high or less is a step's face
TRIM = 24          # a wall this short or less is a frame, a post, a jamb
SHARE = 0.03       # what's used less than this (of its kind) is left out of the draft's roles


def themes_dir(root: Path) -> Path:
    """The current project's themes/ (the mapper's own library comes in docs/projects.md phase 2)."""
    from dms import project

    return project.path(root) / "themes"


@dataclass
class Theme:
    name: str
    title: str = ""
    description: str = ""
    textures: dict[str, list[str]] = field(default_factory=dict)
    things: dict[str, list[int]] = field(default_factory=dict)
    decals: list[str] = field(default_factory=list)
    atmosphere: dict = field(default_factory=dict)
    folder: Path | None = None

    def texture(self, role: str) -> str | None:
        """The main texture for a role, or None."""
        names = self.textures.get(role) or []
        return names[0] if names else None

    def names(self) -> set[str]:
        """Every texture name in the theme."""
        return {n for names in self.textures.values() for n in names}


class ThemeError(Exception):
    pass


def load(folder: Path) -> Theme:
    f = folder / "theme.toml"
    try:
        data = tomllib.loads(f.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ThemeError(f"no theme at {folder} (no theme.toml)") from None
    except tomllib.TOMLDecodeError as e:
        raise ThemeError(f"{f}: {e}") from None
    return Theme(
        name=folder.name, title=str(data.get("title", folder.name)), description=str(data.get("description", "")),
        textures={k: [str(n).upper() for n in _list(v)] for k, v in (data.get("textures") or {}).items()},
        things={k: [int(n) for n in _list(v)] for k, v in (data.get("things") or {}).items()},
        decals=[str(n) for n in _list(data.get("decals"))], atmosphere=dict(data.get("atmosphere") or {}),
        folder=folder)


def _list(v) -> list:
    return [] if v is None else list(v) if isinstance(v, (list, tuple)) else [v]


def all_themes(root: Path) -> list[Theme]:
    d = themes_dir(root)
    return [load(p) for p in sorted(d.iterdir()) if (p / "theme.toml").is_file()] if d.is_dir() else []


def find(root: Path, name: str) -> Theme:
    folder = themes_dir(root) / name
    if not (folder / "theme.toml").is_file():
        known = ", ".join(t.name for t in all_themes(root)) or "none yet"
        raise ThemeError(f"no theme {name!r} (themes: {known})")
    return load(folder)


# ---------------------------------------------------------------- writing and showing

def _toml_str(s: str) -> str:
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _toml_value(v) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return repr(v)
    if isinstance(v, (list, tuple)):
        return "[" + ", ".join(_toml_value(x) for x in v) + "]"
    return _toml_str(str(v))


def dump(theme: Theme, header: str = "", footer: str = "") -> str:
    """theme.toml text: known roles in their order, then any others."""
    out = [header.rstrip() + "\n"] if header else []
    out += [f"title = {_toml_str(theme.title or theme.name)}", f"description = {_toml_str(theme.description)}",
            f"decals = {_toml_value(theme.decals)}", ""]      # top-level keys come before the first table

    def table(name: str, values: dict, order) -> None:
        out.append(f"[{name}]")
        for k in [*[r for r in order if r in values], *sorted(k for k in values if k not in order)]:
            out.append(f"{k} = {_toml_value(values[k])}")
        out.append("")

    table("textures", theme.textures, ROLES)
    table("things", theme.things, THING_ROLES)
    table("atmosphere", theme.atmosphere, ATMOSPHERE)
    text = "\n".join(out).rstrip() + "\n"
    return text + ("\n" + footer.rstrip() + "\n" if footer else "")


def show(theme: Theme) -> str:
    """A theme as text, for the terminal."""
    lines = [f"{theme.name}: {theme.title}"]
    if theme.description:
        lines.append(f"  {theme.description}")
    lines.append("  textures:")
    for role in [*[r for r in ROLES if r in theme.textures], *sorted(set(theme.textures) - set(ROLES))]:
        lines.append(f"    {role:11} {' '.join(theme.textures[role]) or '-'}")
    if theme.things:
        lines.append("  things:")
        for role, types in theme.things.items():
            lines.append(f"    {role:13} {' '.join(map(str, types)) or '-'}")
    if theme.decals:
        lines.append(f"  decals: {' '.join(theme.decals)}")
    if theme.atmosphere:
        lines.append("  atmosphere: " + ", ".join(f"{k} {v}" for k, v in theme.atmosphere.items()))
    return "\n".join(lines)


# ---------------------------------------------------------------- checking

def check(theme: Theme, known_walls: set[str], known_flats: set[str]) -> list[str]:
    """What's wrong with a theme: unknown roles, names neither the game nor any map knows, bad values."""
    problems = []
    for role, names in theme.textures.items():
        if role not in ROLES:
            problems.append(f"textures.{role}: not a role ({', '.join(ROLES)})")
        for n in names:
            if n not in known_walls and n not in known_flats:
                problems.append(f"textures.{role}: {n} isn't a texture or flat of the game or of any map")
    for role in theme.things:
        if role not in THING_ROLES:
            problems.append(f"things.{role}: not a role ({', '.join(THING_ROLES)})")
    for k, v in theme.atmosphere.items():
        if k not in ATMOSPHERE:
            problems.append(f"atmosphere.{k}: not known ({', '.join(ATMOSPHERE)})")
        elif k in ("lightcolor", "fog") and v and not HEX.fullmatch(str(v)):
            problems.append(f"atmosphere.{k}: {v!r} isn't RRGGBB")
        elif k == "light" and not (isinstance(v, int) and 0 <= v <= 255):
            problems.append(f"atmosphere.light: {v!r} isn't 0-255")
        elif k == "light_range" and not (isinstance(v, list) and len(v) == 2 and all(isinstance(x, int) for x in v)):
            problems.append(f"atmosphere.light_range: {v!r} isn't [darkest, brightest]")
    return problems


def known_names(root: Path) -> tuple[set[str], set[str]]:
    """(wall textures, flats) the game and every map's own textures know."""
    from dms import catalog, extras, maps

    walls: set[str] = set()
    flats: set[str] = set()
    cat = catalog.load(root)
    if cat:
        walls |= set(cat.textures)
        flats |= set(cat.flats)
    for info in maps.all_maps(root):
        w, f = extras.textures(info)
        walls |= set(w)
        flats |= f
    return walls, flats


# ---------------------------------------------------------------- for the viewer (themes.html)

FLAT_ROLES = {"floor", "floor_alt", "ceiling", "liquid"}


def for_page(root: Path) -> dict:
    """Every theme for the viewer, each name with its picture: {"themes": [...], "problems": {name: [...]}}.
    A wall role looks among the wall textures first, a flat role among the flats; then the maps' own
    (with the map named in `custom`). A thing type comes with its title and sprite."""
    from dms import mapassets, resources

    _, idx, _ = resources.load(root)
    own = mapassets.custom(root)
    pools = {"textures": {t["name"]: t for t in idx.categories.get("textures", [])},
             "flats": {t["name"]: t for t in idx.categories.get("flats", [])}}
    for cat in ("textures", "flats"):
        for t in own.get(cat, []):
            pools[cat].setdefault(t["name"], t)
    things = {t["num"]: t for g in ("items", "monsters", "decorations", "specials")
              for t in idx.categories.get(g, []) if "num" in t}

    def url(u: str | None) -> str | None:
        return None if not u else u if u.startswith("/") else f"/asset/{idx.key}/{u}"

    def picture(role: str, name: str) -> dict:
        order = ("flats", "textures") if role in FLAT_ROLES else ("textures", "flats")
        t = next((pools[c][name] for c in order if name in pools[c]), None)
        if t is None:
            return {"name": name, "missing": True}
        anim = [url(pools["flats" if "flat/" in (t.get("url") or "") else "textures"].get(f, {}).get("url"))
                for f in (t.get("anim") or [])]
        return {"name": name, "url": url(t.get("url")), "width": t["width"], "height": t["height"],
                "masked": bool(t.get("masked")), "custom": t.get("custom"),
                "anim": [a for a in anim if a] if anim and all(anim) else None}

    out = []
    walls, flats = set(pools["textures"]), set(pools["flats"])
    problems = {}
    for theme in all_themes(root):
        problems[theme.name] = check(theme, walls, flats)
        out.append({
            "name": theme.name, "title": theme.title, "description": theme.description,
            "textures": {role: [picture(role, n) for n in names] for role, names in theme.textures.items()},
            "things": {role: [{"type": ty, "title": things.get(ty, {}).get("title", f"thing {ty}"),
                               "url": url(things.get(ty, {}).get("url"))} for ty in types]
                       for role, types in theme.things.items()},
            "decals": theme.decals, "atmosphere": theme.atmosphere})
    return {"themes": out, "problems": problems, "roles": ROLES, "thing_roles": THING_ROLES}


# ---------------------------------------------------------------- harvest

def matches(gid: str | None, patterns: list[str]) -> bool:
    return bool(gid) and any(fnmatch.fnmatchcase(str(gid), p) for p in patterns)


def _area(tm: Textmap, edges: list[tuple[int, int]]) -> float:
    verts = tm.vertices
    total = 0.0
    for a, b in edges:
        (x1, y1), (x2, y2) = (verts[a]["x"], verts[a]["y"]), (verts[b]["x"], verts[b]["y"])
        total += x1 * y2 - x2 * y1
    return abs(total) / 2


def _hex(v) -> str:
    return f"{int(v) & 0xFFFFFF:06X}"


def _weighted_median(pairs: list[tuple[float, float]]) -> float:
    pairs = sorted(pairs)
    half, run = sum(w for _, w in pairs) / 2, 0.0
    for v, w in pairs:
        run += w
        if run >= half:
            return v
    return pairs[-1][0] if pairs else 0


@dataclass
class Harvest:
    theme: Theme
    counts: dict[str, Counter]        # role -> name -> weight (map units of wall, or of floor area)
    sectors: int
    things: Counter                   # thing type -> how many


def harvest(tm: Textmap, patterns: list[str], name: str, sky: str = "", thing_kind=None) -> Harvest:
    """A draft theme from the sectors whose gid matches `patterns`. Walls are weighed by length, flats
    by area. `thing_kind(type) -> (kind, title)` sorts things (render.thing_kind); without it only
    lights are recognised."""
    from dms.validate import sector_at, sector_edges

    sectors, sides, lines, verts = tm.sectors, tm.sidedefs, tm.linedefs, tm.vertices
    picked = {i for i, s in enumerate(sectors) if matches(s.get("user_gid"), patterns)}
    if not picked:
        raise ThemeError(f"no sector's gid matches {' '.join(patterns)}")
    edges = sector_edges(tm)
    area = {i: _area(tm, edges.get(i, [])) for i in picked}
    counts: dict[str, Counter] = {r: Counter() for r in ROLES}

    def put(role: str, tex, weight: float) -> None:
        tex = str(tex or "-").upper()
        if tex == "-" or weight <= 0:
            return
        if tex.startswith(("SW1", "SW2")):
            role = "switch"
        elif tex.startswith(LIQUIDS):
            role = "liquid"
        elif tex.startswith(LIGHTS):
            role = "light"
        counts[role][tex] += weight

    for i in picked:
        s = sectors[i]
        put("floor", s.get("texturefloor"), area[i])
        ceiling = str(s.get("textureceiling") or "-").upper()
        if ceiling == SKY_FLAT:
            if sky:
                counts["sky"][sky.upper()] += area[i]
        else:
            put("ceiling", ceiling, area[i])

    for ld in lines:
        a, b = verts[ld["v1"]], verts[ld["v2"]]
        length = ((a["x"] - b["x"]) ** 2 + (a["y"] - b["y"]) ** 2) ** 0.5
        front, back = ld.get("sidefront"), ld.get("sideback")
        door = ld.get("special") in DOOR_SPECIALS
        for mine, other in ((front, back), (back, front)):
            if mine is None or mine < 0 or mine >= len(sides):
                continue
            side = sides[mine]
            if side.get("sector") not in picked:
                continue
            if other is None or other < 0:                       # a one-sided wall
                put("door" if door else "trim" if length <= TRIM else "wall", side.get("texturemiddle"), length)
                continue
            here, there = sectors[side["sector"]], sectors[sides[other]["sector"]]
            rise = there["heightfloor"] - here["heightfloor"]
            drop = here["heightceiling"] - there["heightceiling"]
            if door:
                put("door", side.get("texturetop"), length)
            elif drop > 0:
                put("trim" if length <= TRIM else "wall", side.get("texturetop"), length)
            if rise > 0:
                put("step" if rise <= STEP else "trim" if length <= TRIM else "wall", side.get("texturebottom"), length)

    things: Counter = Counter()
    light_things, decoration = Counter(), Counter()
    for t in tm.things:
        sec = sector_at(tm, t["x"], t["y"], edges)
        if sec not in picked:
            continue
        ty = int(t["type"])
        things[ty] += 1
        kind = thing_kind(ty)[0] if thing_kind else "other"
        if 9800 <= ty <= 9899 or ty in LIGHT_THINGS:
            light_things[ty] += 1
        elif kind == "other" and ty not in (1, 2, 3, 4):
            decoration[ty] += 1

    textures: dict[str, list[str]] = {}

    def keep(counter: Counter) -> list[str]:
        total = sum(counter.values())
        return [n for n, w in counter.most_common() if total and w / total >= SHARE]

    for role in ROLES:
        names = keep(counts[role])
        if role in ("wall", "floor") and len(names) > 1:          # the most used is the main one
            textures[role], textures[f"{role}_alt"] = names[:1], names[1:]
        elif names:
            textures[role] = names

    lit = [(sectors[i]["lightlevel"], max(area[i], 1.0)) for i in picked]
    atmosphere: dict = {"light": int(_weighted_median(lit)),
                        "light_range": [min(v for v, _ in lit), max(v for v, _ in lit)]}
    tints: Counter = Counter()
    fogs: Counter = Counter()
    for i in picked:
        tints[_hex(sectors[i]["lightcolor"]) if "lightcolor" in sectors[i].fields else ""] += area[i]
        fogs[_hex(sectors[i]["fadecolor"]) if "fadecolor" in sectors[i].fields else ""] += area[i]
    atmosphere["lightcolor"] = tints.most_common(1)[0][0]
    atmosphere["fog"] = fogs.most_common(1)[0][0]
    dens = [(sectors[i].get("fogdensity", 0), max(area[i], 1.0)) for i in picked
            if atmosphere["fog"] and "fadecolor" in sectors[i].fields and _hex(sectors[i]["fadecolor"]) == atmosphere["fog"]]
    atmosphere["fogdensity"] = int(_weighted_median(dens)) if dens else 0

    theme = Theme(name=name, title=name.replace("-", " ").title(), textures=textures,
                  things={k: [ty for ty, _ in c.most_common()] for k, c in
                          (("light_source", light_things), ("decoration", decoration)) if c},
                  atmosphere=atmosphere)
    return Harvest(theme, {r: c for r, c in counts.items() if c}, len(picked), things)


def harvest_report(h: Harvest, source: str, patterns: list[str], thing_kind=None) -> str:
    """What harvest counted, as TOML comments: the draft's evidence, for trimming it."""
    lines = [f"# Drafted by `dms themes harvest` from {source}, sectors with gids {' '.join(patterns)}",
             f"# ({h.sectors} sectors). Roles are guessed from where each texture sits: trim it by hand.",
             "#", "# Counted (walls in map units of length, flats in square units of area):"]
    for role in ROLES:
        if role in h.counts:
            total = sum(h.counts[role].values())
            lines.append(f"#   {role:10} " + ", ".join(f"{n} {w / total:.0%}" for n, w in h.counts[role].most_common(8)))
    if h.things:
        named = [f"{ty}" + (f" {thing_kind(ty)[1]}" if thing_kind else "") + f" x{n}" for ty, n in h.things.most_common(12)]
        lines.append("#   things     " + ", ".join(named))
    return "\n".join(lines)
