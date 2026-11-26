"""What the maps bring to the asset browser, and what they use (docs/asset-browser.md).

Two things the game's own resources (resources.py) can't say:

- **Custom assets**: what a map defines for itself. Textures and flats from `maps/<map>/textures.txt`
  (extras.py; put together here from the game's pictures the way the engine does: patches at their
  places, flipped, turned, blended, recoloured), and the actors in `maps/<map>/zscript.zs`, with the
  picture of their Spawn state. Every entry carries `custom` (the map's name), so the page can mark it.
  The compositor knows the common cases; a definition using something it doesn't (a translation by
  ranges, an unusual style) is still listed, with `approx` set: the game is the judge of its look.
- **Usage**: which textures, flats, things, sounds, decals and songs each map uses, and how often, read
  from every map's `TEXTMAP`, `map.toml` and `zscript.zs`. The page puts what is in use first.

Neither is part of the cached index (that follows the resource files): both are read from the maps'
files when asked, and kept in memory until one of those files changes.
"""

from __future__ import annotations

import re
import threading
from pathlib import Path

from dms import extras, maps, resources
from dms.resources import Picture

NAME_OK = re.compile(r"[A-Za-z0-9_\-\[\]\\^]+")
# The engine's named translations that keep brightness and replace the colour: name -> the colour at full brightness.
TINTS = {"red": (255, 0, 0), "green": (0, 255, 0), "blue": (0, 0, 255), "gold": (255, 204, 64), "ice": (160, 200, 255)}
COLOURS = {"black": (0, 0, 0), "white": (255, 255, 255), "red": (255, 0, 0), "green": (0, 255, 0), "blue": (0, 0, 255)}
PATCH_PROPS = {"flipx", "flipy", "rotate", "translation", "blend", "alpha", "style", "useoffsets"}
KIND_CATEGORY = {"walltexture": "textures", "texture": "textures", "flat": "flats"}

_HEADER = re.compile(r'\b(walltexture|texture|flat|sprite|graphic)\s+(?:optional\s+)?"?([A-Za-z0-9_\-\[\]\\^]+)"?\s*,\s*(\d+)\s*,\s*(\d+)\s*\{',
                     re.IGNORECASE)
_PATCH = re.compile(r'\b(?:patch|graphic|sprite)\s+"?([A-Za-z0-9_\-\[\]\\^]+)"?\s*,\s*(-?\d+)\s*,\s*(-?\d+)\s*(\{[^{}]*\})?', re.IGNORECASE)


def _strip_comments(text: str) -> str:
    text = re.sub(r"/\*.*?\*/", " ", text, flags=re.S)
    return re.sub(r"//[^\n]*", "", text)


def _block(text: str, start: int) -> tuple[str, int]:
    """The text between the brace at text[start - 1] and its partner, and where that partner is."""
    depth, i = 1, start
    while i < len(text) and depth:
        depth += {"{": 1, "}": -1}.get(text[i], 0)
        i += 1
    return text[start : i - 1], i


def parse_textures(text: str) -> list[dict]:
    """The definitions in a TEXTURES file, in order: {"kind", "name", "width", "height", "offset",
    "patches": [{"name", "x", "y", "props": {lower-case name: [arguments]}}]}."""
    text = _strip_comments(text)
    out, pos = [], 0
    while True:
        m = _HEADER.search(text, pos)
        if not m:
            return out
        body, pos = _block(text, m.end())
        patches = []
        for p in _PATCH.finditer(body):
            props: dict[str, list[str]] = {}
            current = None                       # several may share a line: a known name starts the next one
            for word in re.findall(r'"[^"]*"|[^\s,;]+', (p.group(4) or "")[1:-1]):
                if word.lower() in PATCH_PROPS:
                    current = props.setdefault(word.lower(), [])
                elif current is not None:
                    current.append(word.strip('"'))
            patches.append({"name": p.group(1).upper(), "x": int(p.group(2)), "y": int(p.group(3)), "props": props})
        off = re.search(r"\boffset\s+(-?\d+)\s*,\s*(-?\d+)", _PATCH.sub("", body), re.IGNORECASE)
        out.append({"kind": m.group(1).lower(), "name": m.group(2).upper(), "width": int(m.group(3)),
                    "height": int(m.group(4)), "offset": (int(off.group(1)), int(off.group(2))) if off else (0, 0),
                    "patches": patches})


def _colour(text: str) -> tuple[int, int, int] | None:
    t = text.strip().lstrip("#").lower()
    if re.fullmatch(r"[0-9a-f]{6}", t):
        return int(t[0:2], 16), int(t[2:4], 16), int(t[4:6], 16)
    return COLOURS.get(t)


def _apply(img, props: dict) -> tuple[object, bool]:
    """A patch's own changes, in the engine's order. Returns (image, approximate?)."""
    from PIL import Image

    approx = False
    if "flipx" in props:
        img = img.transpose(Image.FLIP_LEFT_RIGHT)
    if "flipy" in props:
        img = img.transpose(Image.FLIP_TOP_BOTTOM)
    if "rotate" in props:
        turn = {90: Image.ROTATE_270, 180: Image.ROTATE_180, 270: Image.ROTATE_90}.get(int(float(props["rotate"][0] or 0)) % 360)
        if turn is not None:
            img = img.transpose(turn)
    px = img.load()
    w, h = img.size

    def each(fn) -> None:
        for y in range(h):
            for x in range(w):
                r, g, b, a = px[x, y]
                if a:
                    px[x, y] = (*fn(r, g, b), a)

    lum = lambda r, g, b: (r * 77 + g * 143 + b * 37) >> 8
    if "translation" in props:
        args = [a.lower() for a in props["translation"]]
        kind = args[0] if args else ""
        if kind == "desaturate":
            k = min(31, max(0, int(float(args[1])) if len(args) > 1 else 31)) / 31
            each(lambda r, g, b: tuple(round(c + (lum(r, g, b) - c) * k) for c in (r, g, b)))
        elif kind == "inverse":
            each(lambda r, g, b: (255 - lum(r, g, b),) * 3)
        elif kind in TINTS:
            tr, tg, tb = TINTS[kind]
            each(lambda r, g, b: (lum(r, g, b) * tr // 255, lum(r, g, b) * tg // 255, lum(r, g, b) * tb // 255))
        else:
            approx = True
    if "blend" in props:
        args = props["blend"]
        rgb = _colour(args[0]) if args else None
        if rgb is None:
            approx = True
        elif len(args) > 1:                      # a mix towards the colour
            k = min(1.0, max(0.0, float(args[1])))
            each(lambda r, g, b: tuple(round(c + (t - c) * k) for c, t in zip((r, g, b), rgb)))
        else:                                    # a tint: the colour multiplied in
            each(lambda r, g, b: tuple(c * t // 255 for c, t in zip((r, g, b), rgb)))
    alpha = float(props["alpha"][0]) if props.get("alpha") else 1.0
    style = (props.get("style") or ["copy"])[0].lower()
    if style not in ("copy", "translucent", "copyalpha", "overlay"):
        approx = True
    if alpha < 1.0 and style != "copy":
        each_a = img.getchannel("A").point(lambda a: round(a * alpha))
        img.putalpha(each_a)
    return img, approx


def compose(defn: dict, source) -> tuple[Picture, bool]:
    """A definition's picture. source(name) -> Picture | None finds a patch (another definition of the
    map, or the game's). Returns (picture, approximate?): approximate when a patch is missing or uses
    something this doesn't know."""
    from PIL import Image

    canvas = Image.new("RGBA", (defn["width"], defn["height"]), (0, 0, 0, 0))
    approx = False
    for patch in defn["patches"]:
        p = source(patch["name"])
        if p is None:
            approx = True
            continue
        img, rough = _apply(Image.frombytes("RGBA", (p.width, p.height), p.rgba), patch["props"])
        approx = approx or rough
        layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        layer.paste(img, (patch["x"], patch["y"]))
        canvas = Image.alpha_composite(canvas, layer)
    ox, oy = defn["offset"]
    return Picture(defn["width"], defn["height"], ox, oy, canvas.tobytes()), approx


# ---- a map's custom assets ---------------------------------------------------------------------

_CLASS = re.compile(r"^\s*class\s+(\w+)\s*:\s*(\w+)", re.M)
_NOT_ACTORS = {"eventhandler", "staticeventhandler", "thinker", "object", "genericmenu", "inventory"}


def parse_actors(text: str) -> list[dict]:
    """The actor classes in a map's script: {"class", "parent", "frames": [[sprite + letter, tics]],
    "radius", "height", "monster"} (frames: its Spawn state, empty when it has none of its own; monster: True when
    its Default says `Monster;` or `+ISMONSTER`, None when it doesn't say, so the parent's counts)."""
    text = _strip_comments(text)
    found = list(_CLASS.finditer(text))
    out = []
    for i, m in enumerate(found):
        if m.group(2).lower() in _NOT_ACTORS:
            continue
        body = text[m.end() : found[i + 1].start() if i + 1 < len(found) else len(text)]
        frames = []
        sp = re.search(r"(?<![:\w])Spawn\s*:(?!:)", body, re.I)
        for line in re.split(r"[;\n]", body[sp.end():]) if sp else []:
            s = line.strip()
            if not s:
                continue
            fm = resources._FRAME_LINE.match(s)
            if not fm:
                break
            frames += [[fm.group(1).upper() + letter, int(fm.group(3))] for letter in fm.group(2).upper()]
        size = {k: int(v.group(1)) if (v := re.search(rf"(?<![\w.]){k}\s+(\d+)", body, re.I)) else None
                for k in ("radius", "height")}
        monster = True if re.search(r"(?<![\w.])Monster\s*;|\+\s*ISMONSTER\b", body, re.I) else None
        out.append({"class": m.group(1), "parent": m.group(2), "frames": frames, **size, "monster": monster})
    return out


def _stamp(root: Path) -> tuple:
    """Changes when any file this module reads does."""
    out = []
    for info in maps.all_maps(root):
        own = [f for _, f in extras.pictures(info) + extras.sprites(info)]
        for f in [info.folder / name for name in ("TEXTMAP", "map.toml", "zscript.zs", "textures.txt", "animdefs.txt")] + own:
            if f.is_file():
                st = f.stat()
                out.append((str(f), st.st_mtime_ns, st.st_size))
    return tuple(out)


_LOCK = threading.Lock()
_CACHE: dict[tuple, dict] = {}


def _cached(root: Path, what: str, make) -> dict:
    with _LOCK:
        key = (str(root), what)
        stamp = _stamp(root)
        got = _CACHE.get(key)
        if not got or got["stamp"] != stamp:
            got = _CACHE[key] = {"stamp": stamp, "value": make()}
        return got["value"]


def _version(info: maps.MapInfo) -> int:
    f = info.folder / "textures.txt"
    return f.stat().st_mtime_ns if f.is_file() else 0


def _definitions(info: maps.MapInfo) -> list[dict]:
    f = info.folder / "textures.txt"
    return parse_textures(f.read_text(encoding="utf-8", errors="replace")) if f.is_file() else []


def _source(res, defs: list[dict], upto: int):
    """Finds a patch for definition number `upto`: an earlier definition of the map, then the game's
    patches and sprites, textures and flats."""
    def find(name: str) -> Picture | None:
        for d in reversed(defs[:upto]):
            if d["name"] == name:
                return compose(d, _source(res, defs, defs.index(d)))[0]
        return res.patch(name) or res.sprite(name) or res.texture(name) or res.flat(name)
    return find


def picture(root: Path, map_name: str, name: str) -> Picture | None:
    """One of a map's own textures, flats or sprites, put together."""
    info = next((i for i in maps.all_maps(root) if i.name == map_name), None)
    if info is None:
        return None
    res, _, _ = resources.load(root)
    defs = _definitions(info)
    for i in range(len(defs) - 1, -1, -1):
        if defs[i]["name"] == name.upper():
            return compose(defs[i], _source(res, defs, i))[0]
    return None


def picture_file(root: Path, map_name: str, name: str) -> tuple[bytes, str] | None:
    """(PNG, content type) for /asset-custom/<map>/<NAME>.png."""
    stem, _, ext = name.rpartition(".")
    if ext != "png" or not NAME_OK.fullmatch(stem or ""):
        return None
    info = next((i for i in maps.all_maps(root) if i.name == map_name), None)
    for own, f in (extras.pictures(info) + extras.sprites(info)) if info else ():   # the map's own: the file itself
        if own == stem.upper():
            return f.read_bytes(), "image/png"
    p = picture(root, map_name, stem)
    return (resources.png_bytes(p), "image/png") if p else None


def custom(root: Path) -> dict[str, list[dict]]:
    """Every map's own assets, by the browser's category, shaped like the index's entries plus
    `custom` (the map) and, where the picture is a guess, `approx`."""
    return _cached(root, "custom", lambda: _custom(root))


def _custom(root: Path) -> dict[str, list[dict]]:
    res, idx, _ = resources.load(root)
    by_class = {}
    for group in ("items", "monsters", "decorations", "specials"):
        for t in idx.categories.get(group, []):
            if t.get("class"):
                by_class.setdefault(t["class"].lower(), (group, t))
    out: dict[str, list[dict]] = {}
    for info in maps.all_maps(root):
        defs = _definitions(info)
        v = _version(info)
        url = lambda name: f"/asset-custom/{info.name}/{name}.png?v={v}"
        sprites = {}
        for i, d in enumerate(defs):
            if d["kind"] == "sprite":
                sprites[d["name"]] = d
            category = KIND_CATEGORY.get(d["kind"])
            if not category:
                continue
            p, approx = compose(d, _source(res, defs, i))
            out.setdefault(category, []).append({
                "name": d["name"], "width": d["width"], "height": d["height"], "sets": ["Custom"],
                "colour": resources.colour_of(p), "masked": category == "textures" and resources.masked(p),
                "anim": None, "switch": None, "sky": False, "url": url(d["name"]),
                "custom": info.name, "approx": approx, "made_of": sorted({x["name"] for x in d["patches"]})})
        for name, f in extras.pictures(info):                # its own pictures (textures/NAME.png): walls and flats
            p = res.picture(f.read_bytes())
            for category in ("textures", "flats"):
                out.setdefault(category, []).append({
                    "name": name, "width": p.width, "height": p.height, "sets": ["Custom"],
                    "colour": resources.colour_of(p), "masked": category == "textures" and resources.masked(p),
                    "anim": None, "switch": None, "sky": False,
                    "url": f"/asset-custom/{info.name}/{name}.png?v={f.stat().st_mtime_ns}",
                    "custom": info.name, "approx": False, "made_of": [], "picture": True})
        script = info.folder / "zscript.zs"
        actors = parse_actors(script.read_text(encoding="utf-8", errors="replace")) if script.is_file() else []
        own = {a["class"].lower(): a for a in actors}
        own_sprites = {n: f"/asset-custom/{info.name}/{n}.png?v={f.stat().st_mtime_ns}" for n, f in extras.sprites(info)}
        for a in actors:
            # Its looks and size: its own, else the nearest parent's that has them (the map's, then the game's).
            frames, radius, height, parent, base = a["frames"], a["radius"], a["height"], a["parent"].lower(), None
            monster = a["monster"]
            for _ in range(8):
                if parent in own:
                    up = own[parent]
                    frames, radius, height = frames or up["frames"], radius or up["radius"], height or up["height"]
                    monster = monster or up["monster"]
                    parent = up["parent"].lower()
                else:
                    base = by_class.get(parent)
                    break
            group = "monsters" if monster else base[0] if base and base[0] != "specials" else "decorations"
            lump, picture_url, anim = None, None, []
            for frame, tics in frames:
                mine = next((n for n in sprites if n[:5] == frame), None) \
                    or next((n for n, _ in extras.sprites(info) if n[:5] == frame), None)   # sprites/NAME.png
                theirs = None if mine else resources.frame_lump(res, frame)
                if mine or theirs:
                    anim.append([(own_sprites[mine] if mine in own_sprites else url(mine)) if mine else f"sprite/{theirs}.png", tics])
                    if lump is None:
                        lump, picture_url = mine or theirs, anim[-1][0]
            if lump is None and base:
                lump, picture_url = base[1].get("sprite_lump"), base[1].get("url")
            if not lump:
                continue  # nothing to show (e.g. a class that only holds code)
            entry = {"num": None, "title": a["class"], "name": a["class"], "class": a["class"],
                     "category": "custom", "category_title": f"Custom ({info.name})",
                     "radius": radius if radius is not None else (base[1].get("radius") if base else None),
                     "height": height if height is not None else (base[1].get("height") if base else None),
                     "sprite": lump, "sprite_lump": lump, "frames": [], "url": picture_url,
                     "spawn": anim if len({x[0] for x in anim}) > 1 else [],
                     "custom": info.name, "parent": a["parent"]}
            out.setdefault(group, []).append(entry)
    return out


# ---- what the maps use -------------------------------------------------------------------------

_TEXTMAP_FIELD = re.compile(r'\b(texturetop|texturemiddle|texturebottom|texturefloor|textureceiling)\s*=\s*"([^"]*)"\s*;', re.I)
_THING_TYPE = re.compile(r"^thing\b[^{]*\{([^}]*)\}", re.M | re.I)
_SOUND = re.compile(r'(?:StartSound|A_PlaySound|S_Sound)\s*\(\s*"([^"]+)"', re.I)
_DECAL = re.compile(r'A_SprayDecal\s*\(\s*"([^"]+)"', re.I)
_SPAWN = re.compile(r'(?:Spawn|A_SpawnItemEx)\s*\(\s*"(\w+)"', re.I)


def usage(root: Path) -> dict:
    """{"maps": [name], "tex": {NAME: {map: count}}, "things": {editor number: {map: count}},
    "classes", "sounds", "decals" (lower-case names), "music" (lump)}: what each map uses. Textures and
    flats are counted together by name (the engine draws either as the other)."""
    return _cached(root, "usage", lambda: _usage(root))


def _usage(root: Path) -> dict:
    out: dict = {"maps": [], "tex": {}, "things": {}, "classes": {}, "sounds": {}, "decals": {}, "music": {}}

    def add(kind: str, name: str, map_name: str, n: int = 1) -> None:
        if name and name != "-":
            per = out[kind].setdefault(name, {})
            per[map_name] = per.get(map_name, 0) + n

    for info in maps.all_maps(root):
        out["maps"].append(info.name)
        if info.textmap.is_file():
            text = info.textmap.read_text(encoding="utf-8", errors="replace")
            for _, name in _TEXTMAP_FIELD.findall(text):
                add("tex", name.upper(), info.name)
            for body in _THING_TYPE.findall(text):
                t = re.search(r"\btype\s*=\s*(\d+)", body)
                if t:
                    add("things", t.group(1), info.name)
        add("tex", info.sky.upper(), info.name)
        add("music", info.music.upper(), info.name)
        defs = _definitions(info)
        used = {n for n, per in out["tex"].items() if info.name in per}
        for d in defs:                        # what the map's own textures are made of counts too
            if d["name"] in used or d["kind"] == "sprite":
                for p in d["patches"]:
                    add("tex", p["name"], info.name)
        script = info.folder / "zscript.zs"
        if script.is_file():
            code = _strip_comments(script.read_text(encoding="utf-8", errors="replace"))
            for name in _SOUND.findall(code):
                add("sounds", name.lower(), info.name)
            for name in _DECAL.findall(code):
                add("decals", name.lower(), info.name)
            for name in _SPAWN.findall(code):
                add("classes", name.lower(), info.name)
    return out
