"""The game's resources as the asset browser sees them (docs/asset-browser.md).

One view of every lump the engine would load for a map: the IWAD, then UZDoom's own `uzdoom.pk3`
(later, a map's resource WADs). Decodes what the browser needs: the palette, Doom pictures (patches,
sprites), flats, wall textures composited from their patches, DMX sounds (to WAV); and lists each
category: textures, flats, decals, things (items, monsters, decorations, specials), sounds, music.

Things come from Ultimate Doom Builder's thing configs (titles, categories, sprites, sizes), read at
run time from `.tools/udb/` (GPL; never copied into the repo). Nothing here is committed: converted
files are cached under `build/assets/<key>/` (git-ignored) and served on 127.0.0.1 only.
"""

from __future__ import annotations

import colorsys
import fnmatch
import hashlib
import io
import json
import re
import struct
import threading
import wave
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

from dms import wad

VERSION = 4  # bump when a converter's output changes, so old caches aren't used
CATEGORIES = ("textures", "flats", "decals", "items", "monsters", "decorations", "specials", "sounds", "music")

# The editor's thing categories -> the browser's tabs.
THING_GROUPS = {
    "monsters": "monsters",
    "weapons": "items", "ammunition": "items", "health": "items", "armor": "items", "armour": "items",
    "powerups": "items", "keys": "items",
    "obstacles": "decorations", "lights": "decorations", "decoration": "decorations",
}

# The order the editor loads them in for UZDoom/Doom UDMF (UZDoom_DoomUDMF.cfg): file, sections (None = all).
THING_CONFIGS = (
    ("Doom_things.cfg", None),
    ("Doom2_things.cfg", None),
    ("ZDoom_things.cfg", ("doom", "zdoom")),
    ("GZDoom_things.cfg", None),
)


@dataclass
class Picture:
    width: int
    height: int
    left: int  # offsets, as in the patch header
    top: int
    rgba: bytes


class Resources:
    """The IWAD + uzdoom.pk3, lumps resolved by name the way the engine does (later files win)."""

    def __init__(self, iwad: Path, pk3: Path | None = None, udb: Path | None = None) -> None:
        self.iwad = Path(iwad)
        self.pk3 = Path(pk3) if pk3 and Path(pk3).is_file() else None
        self.udb = Path(udb) if udb and Path(udb).is_dir() else None
        _, self.lumps = wad.read(self.iwad)
        self.names = [lump.name.upper() for lump in self.lumps]
        self.zip = zipfile.ZipFile(self.pk3) if self.pk3 else None
        self.zip_names = self.zip.namelist() if self.zip else []
        self._lock = threading.Lock()
        pal = self.lump("PLAYPAL") or bytes(768)
        self.palette = [tuple(pal[i * 3 : i * 3 + 3]) for i in range(256)]
        self.flats = self._namespace(("F_START", "FF_START"), ("F_END", "FF_END"))
        self.sprites = self._namespace(("S_START", "SS_START"), ("S_END", "SS_END"))
        self.patch_names = self._pnames()
        self.texture_defs = self._texture_defs()

    # --- identity -------------------------------------------------------------------------------

    @property
    def key(self) -> str:
        """Changes when any resource file (or a converter) does: names the cache folder."""
        h = hashlib.sha256(f"v{VERSION}".encode())
        for p in (self.iwad, self.pk3):
            if p:
                st = p.stat()
                h.update(f"{p.name}:{st.st_size}:{st.st_mtime_ns};".encode())
        return h.hexdigest()[:16]

    # --- raw lumps ------------------------------------------------------------------------------

    def lump(self, name: str) -> bytes | None:
        """The last lump of that name in the IWAD (outside the flat/sprite namespaces it's the same)."""
        name = name.upper()
        for i in range(len(self.names) - 1, -1, -1):
            if self.names[i] == name:
                return self.lumps[i].data
        return None

    def _namespace(self, starts: tuple[str, ...], ends: tuple[str, ...]) -> dict[str, bytes]:
        out: dict[str, bytes] = {}
        inside = False
        for lump, name in zip(self.lumps, self.names):
            if name in starts:
                inside = True
            elif name in ends:
                inside = False
            elif inside and lump.data:
                out[name] = lump.data
        return out

    def pk3_file(self, path: str) -> bytes | None:
        if not self.zip:
            return None
        try:
            with self._lock:
                return self.zip.read(path)
        except KeyError:
            return None

    def pk3_by_lump(self, folder: str, name: str) -> tuple[str, bytes] | None:
        """A pk3 file in `folder/` whose name without extension is the lump name (case-insensitive)."""
        want = name.lower()
        for n in self.zip_names:
            if n.lower().startswith(folder + "/") and Path(n).stem.lower() == want and not n.endswith("/"):
                return n, self.pk3_file(n) or b""
        return None

    # --- pictures -------------------------------------------------------------------------------

    def picture(self, data: bytes) -> Picture:
        """A Doom picture (patch format) or a PNG, as RGBA."""
        if data[:8] == b"\x89PNG\r\n\x1a\n":
            from PIL import Image

            img = Image.open(io.BytesIO(data)).convert("RGBA")
            left, top = _png_grab(data)
            return Picture(img.width, img.height, left, top, img.tobytes())
        width, height, left, top = struct.unpack_from("<hhhh", data, 0)
        if not (0 < width <= 4096 and 0 < height <= 4096):
            raise ValueError("not a picture")
        out = bytearray(width * height * 4)
        cols = struct.unpack_from(f"<{width}I", data, 8)
        pal = self.palette
        for x, off in enumerate(cols):
            prev_top = -1
            while off < len(data) and data[off] != 0xFF:
                top_delta = data[off]
                length = data[off + 1]
                # Tall patches: a delta not above the previous one is relative to it (DeePsea).
                y0 = top_delta if top_delta > prev_top else prev_top + top_delta
                prev_top = y0
                for i in range(length):
                    y = y0 + i
                    if 0 <= y < height:
                        r, g, b = pal[data[off + 3 + i]]
                        p = (y * width + x) * 4
                        out[p : p + 4] = bytes((r, g, b, 255))
                off += length + 4
        return Picture(width, height, left, top, bytes(out))

    def flat(self, name: str) -> Picture | None:
        data = self.flats.get(name.upper())
        if data is None:
            return None
        if data[:8] == b"\x89PNG\r\n\x1a\n":
            return self.picture(data)
        size = 64 if len(data) < 4096 * 2 else int(len(data) ** 0.5)
        out = bytearray(size * size * 4)
        for i in range(min(len(data), size * size)):
            r, g, b = self.palette[data[i]]
            out[i * 4 : i * 4 + 4] = bytes((r, g, b, 255))
        return Picture(size, size, 0, 0, bytes(out))

    def patch(self, name: str) -> Picture | None:
        name = name.upper()
        data = self.lump(name) or self.sprites.get(name)
        if data is None:
            found = self.pk3_by_lump("patches", name) or self.pk3_by_lump("graphics", name)
            data = found[1] if found else None
        if not data:
            return None
        try:
            return self.picture(data)
        except (ValueError, struct.error):
            return None

    def sprite(self, name: str) -> Picture | None:
        data = self.sprites.get(name.upper())
        if data is None:
            found = self.pk3_by_lump("sprites", name)
            data = found[1] if found else None
        if not data:
            return None
        try:
            return self.picture(data)
        except (ValueError, struct.error):
            return None

    def graphic(self, name: str) -> Picture | None:
        """A decal's picture: pk3 graphics/ first, then the IWAD's sprites and lumps."""
        found = self.pk3_by_lump("graphics", name)
        if found:
            return self.picture(found[1])
        return self.sprite(name) or self.patch(name)

    # --- wall textures --------------------------------------------------------------------------

    def _pnames(self) -> list[str]:
        data = self.lump("PNAMES")
        if not data:
            return []
        (n,) = struct.unpack_from("<i", data, 0)
        return [data[4 + i * 8 : 12 + i * 8].rstrip(b"\0").decode("ascii", "replace").upper() for i in range(n)]

    def _texture_defs(self) -> dict[str, dict]:
        out: dict[str, dict] = {}
        for lump_name in ("TEXTURE1", "TEXTURE2"):
            data = self.lump(lump_name)
            if not data:
                continue
            (count,) = struct.unpack_from("<i", data, 0)
            for off in struct.unpack_from(f"<{count}i", data, 4):
                name = data[off : off + 8].rstrip(b"\0").decode("ascii", "replace").upper()
                width, height = struct.unpack_from("<hh", data, off + 12)
                (npatches,) = struct.unpack_from("<h", data, off + 20)
                patches = []
                for i in range(npatches):
                    ox, oy, idx = struct.unpack_from("<hhh", data, off + 22 + i * 10)
                    if 0 <= idx < len(self.patch_names):
                        patches.append((ox, oy, self.patch_names[idx]))
                out[name] = {"width": width, "height": height, "patches": patches}
        # The engine's own few (pk3 textures/): PNG files named after the texture.
        for n in self.zip_names:
            if n.lower().startswith("textures/") and n.lower().endswith(".png"):
                out.setdefault(Path(n).stem.upper(), {"file": n})
        return out

    def texture(self, name: str) -> Picture | None:
        d = self.texture_defs.get(name.upper())
        if d is None:
            return None
        if "file" in d:
            return self.picture(self.pk3_file(d["file"]) or b"")
        w, h = d["width"], d["height"]
        out = bytearray(w * h * 4)
        for ox, oy, pname in d["patches"]:
            p = self.patch(pname)
            if p is None:
                continue
            for y in range(p.height):
                ty = oy + y
                if not 0 <= ty < h:
                    continue
                for x in range(p.width):
                    tx = ox + x
                    if not 0 <= tx < w:
                        continue
                    s = (y * p.width + x) * 4
                    if p.rgba[s + 3]:
                        d_ = (ty * w + tx) * 4
                        out[d_ : d_ + 4] = p.rgba[s : s + 4]
        return Picture(w, h, 0, 0, bytes(out))

    # --- sounds and music -----------------------------------------------------------------------

    def sound_file(self, lump: str) -> tuple[bytes, str] | None:
        """(data, extension) for the browser: DMX -> WAV; OGG/FLAC/WAV as they are."""
        found = self.pk3_by_lump("sounds", lump)
        data = found[1] if found else self.lump(lump)
        if not data:
            return None
        return _browser_sound(data)

    def music_lump(self, name: str) -> bytes | None:
        found = self.pk3_by_lump("music", name)
        return found[1] if found else self.lump(name)


# --- helpers ------------------------------------------------------------------------------------


def _png_grab(data: bytes) -> tuple[int, int]:
    """ZDoom's grAb chunk (picture offsets) in a PNG, else (0, 0)."""
    i = 8
    while i + 8 <= len(data):
        (length,) = struct.unpack_from(">I", data, i)
        kind = data[i + 4 : i + 8]
        if kind == b"grAb" and length >= 8:
            return struct.unpack_from(">ii", data, i + 8)
        if kind == b"IDAT":
            break
        i += 12 + length
    return 0, 0


def dmx_to_wav(data: bytes) -> bytes:
    """Doom's sound format (u16 3, u16 rate, u32 count incl. 16+16 pad bytes, 8-bit unsigned) -> WAV."""
    fmt, rate, count = struct.unpack_from("<HHI", data, 0)
    if fmt != 3:
        raise ValueError("not a DMX sound")
    samples = data[8 : 8 + count]
    if len(samples) > 32:
        samples = samples[16:-16]  # DMX pads each end with 16 bytes
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(1)
        w.setframerate(rate or 11025)
        w.writeframes(samples)
    return buf.getvalue()


def _browser_sound(data: bytes) -> tuple[bytes, str] | None:
    if data[:4] == b"OggS":
        return data, "ogg"
    if data[:4] == b"fLaC":
        return data, "flac"
    if data[:4] == b"RIFF":
        return data, "wav"
    if len(data) > 8 and struct.unpack_from("<H", data, 0)[0] == 3:
        try:
            return dmx_to_wav(data), "wav"
        except (ValueError, struct.error, wave.Error):
            return None
    return None


def sound_length(data: bytes, ext: str) -> float | None:
    """Seconds, for WAV (exact) and OGG (from the last granule position); None if unknown."""
    try:
        if ext == "wav":
            with wave.open(io.BytesIO(data)) as w:
                return round(w.getnframes() / w.getframerate(), 2)
        if ext == "ogg":
            last = data.rfind(b"OggS")
            first = data.find(b"\x01vorbis")
            if last >= 0 and first >= 0:
                (granule,) = struct.unpack_from("<q", data, last + 6)
                (rate,) = struct.unpack_from("<I", data, first + 12)
                return round(granule / rate, 2) if rate else None
    except (wave.Error, struct.error, EOFError):
        return None
    return None


def midi_length(data: bytes) -> float | None:
    """A standard MIDI file's length in seconds (tempo changes followed), None if it isn't one."""
    if data[:4] != b"MThd":
        return None
    try:
        _, ntrk, division = struct.unpack_from(">HHH", data, 8)
        if division & 0x8000:
            return None
        pos = 8 + struct.unpack_from(">I", data, 4)[0]
        tempo_events: list[tuple[int, int]] = []
        end_tick = 0
        for _ in range(ntrk):
            if data[pos : pos + 4] != b"MTrk":
                break
            (length,) = struct.unpack_from(">I", data, pos + 4)
            i, end, tick, status = pos + 8, pos + 8 + length, 0, 0
            while i < end:
                delta, i = _varlen(data, i)
                tick += delta
                b = data[i]
                if b & 0x80:
                    status = b
                    i += 1
                if status == 0xFF:
                    kind = data[i]
                    n, i = _varlen(data, i + 1)
                    if kind == 0x51 and n == 3:
                        tempo_events.append((tick, int.from_bytes(data[i : i + 3], "big")))
                    i += n
                elif status in (0xF0, 0xF7):
                    n, i = _varlen(data, i)
                    i += n
                else:
                    i += 1 if (status & 0xF0) in (0xC0, 0xD0) else 2
            end_tick = max(end_tick, tick)
            pos = end
        tempo_events.sort()
        seconds, last_tick, tempo = 0.0, 0, 500000
        for t, new in tempo_events:
            if t > end_tick:
                break
            seconds += (t - last_tick) * tempo / division / 1e6
            last_tick, tempo = t, new
        seconds += (end_tick - last_tick) * tempo / division / 1e6
        return round(seconds, 1)
    except (struct.error, IndexError):
        return None


def _varlen(data: bytes, i: int) -> tuple[int, int]:
    value = 0
    while True:
        b = data[i]
        i += 1
        value = (value << 7) | (b & 0x7F)
        if not b & 0x80:
            return value, i


def png_bytes(p: Picture) -> bytes:
    from PIL import Image

    img = Image.frombytes("RGBA", (p.width, p.height), p.rgba)
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return buf.getvalue()


def colour_of(p: Picture) -> dict:
    """The picture's average colour, a hue bucket and a brightness bucket (opaque pixels only)."""
    rgba = p.rgba
    n = r = g = b = 0
    step = max(1, (p.width * p.height) // 4096) * 4
    for i in range(0, len(rgba), step):
        if rgba[i + 3]:
            r += rgba[i]
            g += rgba[i + 1]
            b += rgba[i + 2]
            n += 1
    if not n:
        return {"rgb": "#000000", "hue": "none", "light": "dark", "h": 0.0, "v": 0.0}
    r, g, b = r / n, g / n, b / n
    h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
    if s < 0.18 or v < 0.12:
        hue = "grey"
    else:
        deg = h * 360
        hue = ("red" if deg < 15 or deg >= 340 else "brown" if deg < 45 and v < 0.6 else "orange" if deg < 45
               else "yellow" if deg < 70 else "green" if deg < 160 else "cyan" if deg < 200
               else "blue" if deg < 260 else "purple")
        if hue in ("orange", "yellow") and s < 0.45:
            hue = "tan"
    light = "dark" if v < 0.3 else "mid" if v < 0.6 else "light"
    return {"rgb": "#%02x%02x%02x" % (int(r), int(g), int(b)), "hue": hue, "light": light,
            "h": round(h if hue != "grey" else 2 + v, 3), "v": round(v, 3)}


def masked(p: Picture) -> bool:
    return any(p.rgba[i] == 0 for i in range(3, len(p.rgba), 4))


# --- the editor's config files (Ultimate Doom Builder) ------------------------------------------

_CFG_TOKEN = re.compile(r'"(?:\\.|[^"\\])*"|[A-Za-z0-9_.:$+\-\\/*#\[\]]+|[{}=;(),]')


def parse_cfg(text: str) -> dict:
    """The editor's config syntax, tolerantly: `key = value;`, `key { ... }`; `include(...)` skipped."""
    text = re.sub(r"/\*.*?\*/", " ", text, flags=re.S)
    text = re.sub(r"//[^\n]*", " ", text)
    toks = _CFG_TOKEN.findall(text)
    pos = 0

    def block() -> dict:
        nonlocal pos
        out: dict = {}
        while pos < len(toks):
            t = toks[pos]
            if t == "}":
                pos += 1
                return out
            if t == "include" and pos + 1 < len(toks) and toks[pos + 1] == "(":
                while pos < len(toks) and toks[pos] != ")":
                    pos += 1
                pos += 1
                if pos < len(toks) and toks[pos] == ";":
                    pos += 1
                continue
            nxt = toks[pos + 1] if pos + 1 < len(toks) else ""
            if nxt == "{":
                pos += 2
                out[t] = block()
            elif nxt == "=":
                pos += 2
                parts = []
                while pos < len(toks) and toks[pos] != ";":
                    parts.append(toks[pos])
                    pos += 1
                pos += 1
                v = " ".join(parts)
                out[t] = v[1:-1].replace('\\"', '"') if v.startswith('"') and v.endswith('"') else v
            else:
                pos += 1
        return out

    return block()


def texture_sets(udb: Path | None) -> list[tuple[str, list[str]]]:
    """[(set name, [filters])] from the editor's Doom_texturesets.cfg; [] without it."""
    if not udb:
        return []
    f = udb / "Configurations" / "Includes" / "Doom_texturesets.cfg"
    if not f.is_file():
        return []
    data = parse_cfg(f.read_text(encoding="latin-1"))
    sets = []
    for v in data.values():
        if isinstance(v, dict) and "name" in v:
            sets.append((v["name"], [x.upper() for k, x in v.items() if k.startswith("filter")]))
    return sets


def editor_things(udb: Path | None) -> dict[int, dict]:
    """Editor number -> {title, category, category_title, sprite, radius, height, class} from the editor's
    thing configs, later files overriding earlier ones (as the editor loads them for UZDoom)."""
    out: dict[int, dict] = {}
    if not udb:
        return out
    inc = udb / "Configurations" / "Includes"
    for fname, sections in THING_CONFIGS:
        f = inc / fname
        if not f.is_file():
            continue
        data = parse_cfg(f.read_text(encoding="latin-1"))
        roots = [data[s] for s in sections if isinstance(data.get(s), dict)] if sections else [data]
        for r in roots:
            for key, cat in r.items():
                if isinstance(cat, dict):
                    _walk_things(key, cat, {}, out)
    return out


def _walk_things(key: str, cat: dict, inherited: dict, out: dict[int, dict]) -> None:
    props = {**inherited, **{k: v for k, v in cat.items() if not isinstance(v, dict)}}
    props.setdefault("category", key.lower())
    if "title" in cat and "category_title" not in inherited:
        props["category_title"] = cat["title"]
    for k, v in cat.items():
        if not isinstance(v, dict):
            continue
        if k.isdigit():
            t = {**props, **{kk: vv for kk, vv in v.items() if not isinstance(vv, dict)}}
            out[int(k)] = {
                "num": int(k), "title": t.get("title", f"thing {k}"), "category": props["category"],
                "category_title": props.get("category_title", key), "sprite": t.get("sprite", ""),
                "radius": _num(t.get("width")), "height": _num(t.get("height")),
                "class": t.get("class", ""), "hangs": t.get("hangs") == "1",
            }
        else:
            _walk_things(k, v, {**props, "category_title": props.get("category_title", key)}, out)


def _num(v) -> int | None:
    try:
        return int(float(str(v).rstrip("f")))
    except (TypeError, ValueError):
        return None


# --- SNDINFO and DECALDEF -----------------------------------------------------------------------


def parse_sndinfo(text: str) -> dict[str, dict]:
    """Logical sound name -> {lump} or {random: [names]} or {alias: name}; other commands skipped."""
    text = re.sub(r"/\*.*?\*/", " ", text, flags=re.S)
    text = re.sub(r"//[^\n]*", " ", text)
    out: dict[str, dict] = {}
    toks = re.findall(r'"[^"]*"|[{}]|[^\s{}]+', text)
    i = 0
    while i < len(toks):
        t = toks[i]
        if t.startswith("$"):
            cmd = t.lower()
            if cmd == "$random" and i + 2 < len(toks) and toks[i + 2] == "{":
                name = toks[i + 1].strip('"').lower()
                j = i + 3
                members = []
                while j < len(toks) and toks[j] != "}":
                    members.append(toks[j].strip('"').lower())
                    j += 1
                out[name] = {"random": members}
                i = j + 1
                continue
            if cmd == "$alias" and i + 2 < len(toks):
                out[toks[i + 1].strip('"').lower()] = {"alias": toks[i + 2].strip('"').lower()}
                i += 3
                continue
            # Other commands: skip to the next line's start (approximate: commands take 1-4 args).
            nargs = {"$playersound": 3, "$playersounddup": 3, "$playeralias": 3, "$limit": 2, "$pitchshift": 2,
                     "$pitchshiftrange": 1, "$singular": 1, "$volume": 2, "$rolloff": 3, "$attenuation": 2,
                     "$musicvolume": 2, "$ambient": 0, "$map": 2, "$registered": 0, "$archivepath": 1,
                     "$edfoverride": 0, "$mididevice": 2, "$musicalias": 2}.get(cmd, 1)
            if cmd == "$ambient":
                # $ambient index logicalname [point [atten] | surround | world] continuous|random min max|periodic n volume
                j = i + 1
                while j < len(toks) and not toks[j].startswith("$") and not re.match(r"^[a-z0-9_]+/", toks[j], re.I):
                    j += 1
                i = j + 1
                continue
            i += 1 + nargs
            continue
        if i + 1 < len(toks):
            out[t.strip('"').lower()] = {"lump": toks[i + 1].strip('"').upper()}
            i += 2
        else:
            i += 1
    return out


def parse_decaldef(text: str) -> tuple[dict[str, dict], dict[str, list[str]]]:
    """(decals: name -> {pic, shade, xscale, yscale, add, translucent, fullbright, id}, groups: name -> [members])."""
    text = re.sub(r"/\*.*?\*/", " ", text, flags=re.S)
    text = re.sub(r"//[^\n]*", " ", text)
    toks = re.findall(r'"[^"]*"|[{}]|[^\s{}]+', text)
    decals: dict[str, dict] = {}
    groups: dict[str, list[str]] = {}
    i = 0
    while i < len(toks):
        kw = toks[i].lower()
        if kw in ("decal", "decalgroup", "fader", "stretcher", "slider", "colorchanger", "combiner"):
            name = toks[i + 1].strip('"')
            j = i + 2
            dec_id = None
            if j < len(toks) and toks[j] != "{":
                dec_id = toks[j]
                j += 1
            if j >= len(toks) or toks[j] != "{":
                i = j
                continue
            j += 1
            body = []
            while j < len(toks) and toks[j] != "}":
                body.append(toks[j])
                j += 1
            i = j + 1
            if kw == "decal":
                d = {"name": name, "id": dec_id, "pic": "", "shade": None, "xscale": 1.0, "yscale": 1.0,
                     "add": None, "translucent": None, "fullbright": False, "flipx": False}
                k = 0
                while k < len(body):
                    p = body[k].lower()
                    arg = body[k + 1].strip('"') if k + 1 < len(body) else ""
                    if p == "pic":
                        d["pic"] = arg.upper(); k += 2
                    elif p == "shade":
                        d["shade"] = arg; k += 2
                    elif p == "x-scale":
                        d["xscale"] = _float(arg); k += 2
                    elif p == "y-scale":
                        d["yscale"] = _float(arg); k += 2
                    elif p == "add":
                        d["add"] = _float(arg); k += 2
                    elif p == "translucent":
                        d["translucent"] = _float(arg); k += 2
                    elif p == "fullbright":
                        d["fullbright"] = True; k += 1
                    elif p == "randomflipx":
                        d["flipx"] = True; k += 1
                    else:
                        k += 1
                decals[name.lower()] = d
            elif kw == "decalgroup":
                groups[name.lower()] = [body[k].strip('"') for k in range(0, len(body), 2)]
        else:
            i += 1
    return decals, groups


def _float(s: str) -> float:
    try:
        return float(s)
    except ValueError:
        return 1.0


def shade_rgb(shade: str | None) -> tuple[int, int, int] | None:
    if not shade:
        return None
    if shade.lower() == "blooddefault":
        return (0x88, 0x00, 0x00)  # the bleeding actor's colour; Doom's red by default
    parts = shade.split()
    try:
        if len(parts) == 3:
            return tuple(int(p, 16) for p in parts)  # type: ignore[return-value]
        if shade.startswith("#") and len(shade) == 7:
            return tuple(int(shade[i : i + 2], 16) for i in (1, 3, 5))  # type: ignore[return-value]
    except ValueError:
        return None
    return None


def stencil(p: Picture, rgb: tuple[int, int, int]) -> Picture:
    """A shaded decal as the engine draws it: one colour, the picture's brightness as its opacity."""
    out = bytearray(len(p.rgba))
    for i in range(0, len(p.rgba), 4):
        a = p.rgba[i + 3]
        if a:
            lum = max(p.rgba[i], p.rgba[i + 1], p.rgba[i + 2])
            out[i : i + 4] = bytes((rgb[0], rgb[1], rgb[2], lum * a // 255))
    return Picture(p.width, p.height, p.left, p.top, bytes(out))


# --- the index ----------------------------------------------------------------------------------


@dataclass
class Index:
    key: str
    categories: dict[str, list[dict]] = field(default_factory=dict)

    def counts(self) -> dict[str, int]:
        return {k: len(v) for k, v in self.categories.items()}


def sprite_frames(res: Resources, prefix: str) -> list[str]:
    """All sprite lumps for a 4-letter sprite name, sorted."""
    prefix = prefix.upper()[:4]
    names = [n for n in res.sprites if n.startswith(prefix)]
    names += [Path(n).stem.upper() for n in res.zip_names
              if n.lower().startswith("sprites/") and Path(n).stem.upper().startswith(prefix)]
    return sorted(set(names))


def resolve_sprite(res: Resources, sprite: str) -> str | None:
    """The editor's sprite field (e.g. POSSA2A8, CANDA0, or a prefix) -> a sprite lump that exists."""
    s = sprite.upper()
    if not s or s.startswith("INTERNAL:"):
        return None
    if s in res.sprites or res.pk3_by_lump("sprites", s):
        return s
    frames = sprite_frames(res, s[:4])
    if not frames:
        return None
    if len(s) >= 5:
        for f in frames:
            if f[4] == s[4] and f[5:6] in ("0", "1", "2"):
                return f
        for f in frames:
            if f[4] == s[4]:
                return f
    for f in frames:
        if f[5:6] in ("0", "1"):
            return f
    return frames[0]


_FRAME_LINE = re.compile(r"^\s*([A-Z0-9_#]{4})\s+([A-Z\[\]\\\^]+)\s+(-?\d+)", re.I)


def spawn_states(res: Resources) -> dict[str, dict]:
    """Class (lower case) -> {"frames": [[frame, tics]], "loops": bool} from each actor's Spawn state in
    UZDoom's ZScript (zscript/actors/**.zs). `frame` is sprite + letter, e.g. "BAR1A". A state that ends
    in Goto (another state) is left out: its frames aren't known here."""
    out: dict[str, dict] = {}
    for n in res.zip_names:
        if not (n.startswith("zscript/actors/") and n.endswith(".zs")):
            continue
        text = (res.pk3_file(n) or b"").decode("latin-1")
        text = re.sub(r"/\*.*?\*/", " ", text, flags=re.S)
        text = re.sub(r"//[^\n]*", "", text)
        for m in re.finditer(r"^\s*class\s+(\w+)", text, re.M):
            start = m.end()
            nxt = re.search(r"^\s*class\s+\w+", text[start:], re.M)
            body = text[start : start + nxt.start()] if nxt else text[start:]
            sp = re.search(r"(?<![:\w])Spawn\s*:(?!:)", body, re.I)  # the label, not "Goto Super::Spawn"
            if not sp:
                continue
            frames, loops, ended = [], False, False
            for line in re.split(r"[;\n]", body[sp.end():]):
                s = line.strip()
                if not s:
                    continue
                if s.startswith("}"):
                    break
                if re.match(r"^(loop)\b", s, re.I):
                    loops, ended = True, True
                    break
                if re.match(r"^(stop|wait|fail)\b", s, re.I):
                    ended = True
                    break
                if re.match(r"^goto\b", s, re.I) or re.match(r"^\w+\s*:", s):
                    break
                fm = _FRAME_LINE.match(s)
                if fm:
                    sprite, letters, tics = fm.group(1).upper(), fm.group(2).upper(), int(fm.group(3))
                    for letter in letters:
                        frames.append([sprite + letter, tics])
            if ended and frames:
                out[m.group(1).lower()] = {"frames": frames, "loops": loops}
    return out


def frame_lump(res: Resources, frame: str, lumps: list[str] | None = None) -> str | None:
    """The front-view sprite lump for a frame like "BAR1A": rotation 0 or 1 (or a pair starting with it)."""
    names = lumps if lumps is not None else sprite_frames(res, frame[:4])
    for rot in "01":
        for n in names:
            if n[:5] == frame and n[5:6] == rot:
                return n
    for n in names:
        if len(n) >= 8 and n[6:7] == frame[4] and n[7:8] in "01":  # the frame as the mirrored half of a pair
            return n
    return None


# How far the first indexing has got, for the asset browser's loading bar (/api/assets/progress). Plain
# values written by the indexing thread and read by others without a lock: a stale read only shows an
# older number.
STAGES = ("textures", "flats", "decals", "things", "sounds", "music")
_PROGRESS = {"active": False, "stage": "", "step": 0, "steps": len(STAGES), "done": 0, "total": 0}


def progress() -> dict:
    """What load() is doing: {"active", "stage", "step" (1-based), "steps", "done", "total"} (done/total
    within the stage; total 0 = not counted). Never waits for load()."""
    return dict(_PROGRESS)


def _stage(name: str, total: int = 0) -> None:
    _PROGRESS.update(active=True, stage=name, step=STAGES.index(name) + 1, done=0, total=total)


def build_index(res: Resources, cache: Path) -> Index:
    """Every category's list. Composites and caches every texture and flat (for colour and masking)."""
    try:
        return _build_index(res, cache)
    finally:
        _PROGRESS.update(active=False)


def _build_index(res: Resources, cache: Path) -> Index:
    idx = Index(res.key)
    sets = texture_sets(res.udb)

    def sets_of(name: str) -> list[str]:
        return [s for s, filters in sets if any(fnmatch.fnmatchcase(name, f) for f in filters)]

    anims = _animations(res)
    textures = []
    _stage("textures", len(res.texture_defs))
    for name in sorted(res.texture_defs):
        _PROGRESS["done"] += 1
        p = res.texture(name)
        if p is None:
            continue
        _cache_png(cache, "tex", name, p)
        textures.append({"name": name, "width": p.width, "height": p.height, "sets": sets_of(name) or ["Other"],
                         "colour": colour_of(p), "masked": masked(p), "anim": anims.get(name),
                         "switch": _switch_pair(name, res.texture_defs), "sky": name.startswith("SKY"),
                         "url": f"tex/{name}.png"})
    idx.categories["textures"] = textures

    flats = []
    _stage("flats", len(res.flats))
    for name in sorted(res.flats):
        _PROGRESS["done"] += 1
        p = res.flat(name)
        if p is None:
            continue
        _cache_png(cache, "flat", name, p)
        flats.append({"name": name, "width": p.width, "height": p.height, "sets": sets_of(name) or ["Other"],
                      "colour": colour_of(p), "masked": False, "anim": anims.get(name),
                      "sky": name == "F_SKY1", "url": f"flat/{name}.png"})
    idx.categories["flats"] = flats

    _stage("decals")
    idx.categories["decals"] = _decal_list(res)

    _stage("things")
    things = editor_things(res.udb)
    spawns = spawn_states(res)
    for group in ("items", "monsters", "decorations", "specials"):
        idx.categories[group] = []
    _PROGRESS["total"] = len(things)
    for num in sorted(things):
        _PROGRESS["done"] += 1
        t = things[num]
        lump = resolve_sprite(res, t["sprite"])
        group = THING_GROUPS.get(t["category"], "specials")
        if group != "specials" and not lump:
            group = "specials"  # nothing to show in this game (e.g. Heretic-only)
        frames = sprite_frames(res, lump[:4]) if lump else []
        # Its idle animation: the Spawn state's frames as front-view lumps with their tics (a looping
        # state with more than one picture is "animated").
        spawn = spawns.get(t["class"].lower()) if t["class"] else None
        anim = []
        if spawn and lump:
            for frame, tics in spawn["frames"]:
                fl = frame_lump(res, frame, frames if frame[:4] == lump[:4] else None)
                if fl:
                    anim.append([fl, tics])
        animated = bool(spawn and spawn["loops"] and len({a[0] for a in anim}) > 1)
        entry = {**t, "name": t["title"], "sprite_lump": lump, "frames": frames,
                 "spawn": anim if animated else [], "url": f"sprite/{lump}.png" if lump else None}
        idx.categories[group].append(entry)

    _stage("sounds")
    idx.categories["sounds"] = _sound_list(res)
    _stage("music")
    idx.categories["music"] = _music_list(res)
    return idx


def _cache_png(cache: Path, kind: str, name: str, p: Picture) -> None:
    f = cache / kind / f"{name}.png"
    if not f.is_file():
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_bytes(png_bytes(p))


def _switch_pair(name: str, defs: dict) -> str | None:
    if name.startswith("SW1") and "SW2" + name[3:] in defs:
        return "SW2" + name[3:]
    if name.startswith("SW2") and "SW1" + name[3:] in defs:
        return "SW1" + name[3:]
    return None


def _animations(res: Resources) -> dict[str, list[str]]:
    """Texture/flat name -> its animation's frames, from the pk3's ANIMDEFS (range form) and ANIMATED."""
    out: dict[str, list[str]] = {}
    tex_order = list(res.texture_defs)
    flat_order = list(res.flats)
    # The IWAD's own ANIMATED, else UZDoom's built-in one for the Doom games (Freedoom has none of its own).
    data = res.lump("ANIMATED") or res.pk3_file("filter/game-doomchex/animated.lmp")
    if data:
        for i in range(0, len(data) - 22, 23):
            kind = data[i]
            if kind == 0xFF:
                break
            last = data[i + 1 : i + 10].split(b"\0")[0].decode("ascii", "replace").upper()
            first = data[i + 10 : i + 19].split(b"\0")[0].decode("ascii", "replace").upper()
            order = tex_order if kind & 1 else flat_order
            _range(order, first, last, out)
    text = (res.pk3_file("animdefs.txt") or b"").decode("latin-1")
    for m in re.finditer(r"^\s*(texture|flat)\s+(\S+)\s+range\s+(\S+)", text, re.M | re.I):
        order = tex_order if m.group(1).lower() == "texture" else flat_order
        _range(order, m.group(2).upper(), m.group(3).upper(), out)
    return out


def _range(order: list[str], first: str, last: str, out: dict) -> None:
    if first in order and last in order:
        a, b = order.index(first), order.index(last)
        if a < b:
            frames = order[a : b + 1]
            for f in frames:
                out[f] = frames


def _decal_list(res: Resources) -> list[dict]:
    text = (res.pk3_file("decaldef.txt") or b"").decode("latin-1")
    decals, groups = parse_decaldef(text)
    member_of: dict[str, list[str]] = {}
    for g, members in groups.items():
        for m in members:
            member_of.setdefault(m.lower(), []).append(g)
    out = []
    for key, d in sorted(decals.items()):
        p = res.graphic(d["pic"]) if d["pic"] else None
        rgb = shade_rgb(d["shade"])
        out.append({**d, "width": p.width if p else 0, "height": p.height if p else 0,
                    "groups": [groups_name(groups, g) for g in member_of.get(key, [])],
                    "kind": _decal_kind(d["name"]), "shade_rgb": "#%02x%02x%02x" % rgb if rgb else None,
                    "url": f"decal/{d['name']}.png" if p else None})
    return out


def groups_name(groups: dict, key: str) -> str:
    return key


def _decal_kind(name: str) -> str:
    n = name.lower()
    for word, kind in (("blood", "blood"), ("scorch", "scorch"), ("chip", "chips"), ("plasma", "plasma"),
                       ("bfg", "bfg"), ("rail", "rail"), ("bullet", "chips"), ("crossbow", "heretic/hexen"),
                       ("blaster", "heretic/hexen"), ("arach", "plasma"), ("baron", "scorch"), ("cacoscorch", "scorch"),
                       ("doomimp", "scorch"), ("rocket", "scorch")):
        if word in n:
            return kind
    return "other"


def _sound_list(res: Resources) -> list[dict]:
    text = ""
    for path in ("sndinfo.txt", "filter/game-doomchex/sndinfo.txt"):
        text += (res.pk3_file(path) or b"").decode("latin-1") + "\n"
    defs = parse_sndinfo(text)
    out = []
    named_lumps = set()
    for name in sorted(defs):
        d = defs[name]
        entry = {"name": name, "group": name.split("/")[0] if "/" in name else "other"}
        if "lump" in d:
            entry["lump"] = d["lump"]
            named_lumps.add(d["lump"])
            got = res.sound_file(d["lump"])
            if got is None:
                continue
            entry["length"] = sound_length(*got)
            entry["url"] = f"sound/{d['lump']}.{got[1]}"
        elif "random" in d:
            entry["random"] = d["random"]
        elif "alias" in d:
            entry["alias"] = d["alias"]
        out.append(entry)
    # Resolve random/alias to something playable (their first member).
    by_name = {e["name"]: e for e in out}
    for e in out:
        target, seen = e, set()
        while "url" not in target and target["name"] not in seen:
            seen.add(target["name"])
            nxt = (target.get("random") or [target.get("alias")])[0] if (target.get("random") or target.get("alias")) else None
            target = by_name.get(nxt) if nxt else None
            if target is None:
                break
        if target is not None and "url" in target and target is not e:
            e["url"], e["length"], e["lump"] = target["url"], target.get("length"), target.get("lump")
    out = [e for e in out if "url" in e]
    # Sound lumps nothing names (by lump name).
    for name in res.names:
        if name.startswith("DS") and name not in named_lumps:
            got = res.sound_file(name)
            if got:
                named_lumps.add(name)
                out.append({"name": name.lower(), "lump": name, "group": "(unnamed)", "length": sound_length(*got),
                            "url": f"sound/{name}.{got[1]}"})
    return out


def _music_list(res: Resources) -> list[dict]:
    used: dict[str, list[str]] = {}
    text = (res.pk3_file("mapinfo/doom2.txt") or b"").decode("latin-1")
    for m in re.finditer(r'map\s+(\S+)\s+(?:lookup\s+)?"?([^"\n{]*)"?\s*\{(.*?)\}', text, re.S | re.I):
        mm = re.search(r'music\s*=\s*"?\$?([A-Z0-9_]+)', m.group(3), re.I)
        if mm:
            mus = mm.group(1).upper()
            mus = mus if mus.startswith("D_") else "D_" + mus.replace("MUSIC_", "")
            used.setdefault(mus, []).append(m.group(1).upper())
    out = []
    for name in res.names:
        if name.startswith("D_"):
            data = res.music_lump(name) or b""
            fmt = "midi" if data[:4] == b"MThd" else "mus" if data[:4] == b"MUS\x1a" else "ogg" if data[:4] == b"OggS" else "?"
            out.append({"name": name, "format": fmt, "length": midi_length(data) if fmt == "midi" else None,
                        "maps": used.get(name, []), "url": f"music/{name}.mid"})
    return out


_INDEX_LOCK = threading.Lock()
_LOADED: dict[str, tuple[Resources, Index]] = {}


def load(root: Path) -> tuple[Resources, Index, Path]:
    """The resources and their index for this repo's configured tools (cached on disk and in memory)."""
    from dms.launch import tool_path

    iwad = tool_path(root, "freedoom")
    uz = tool_path(root, "uzdoom").parent
    udb = tool_path(root, "udb").parent
    with _INDEX_LOCK:
        res = Resources(iwad, uz / "uzdoom.pk3", udb)
        key = res.key
        cache = root / "build" / "assets" / key
        if key in _LOADED:
            return _LOADED[key][0], _LOADED[key][1], cache
        f = cache / "index.json"
        if f.is_file():
            idx = Index(key, json.loads(f.read_text(encoding="utf-8")))
        else:
            idx = build_index(res, cache)
            cache.mkdir(parents=True, exist_ok=True)
            f.write_text(json.dumps(idx.categories), encoding="utf-8")
        _LOADED[key] = (res, idx)
        return res, idx, cache


def asset_file(root: Path, kind: str, name: str) -> tuple[bytes, str] | None:
    """(data, content type) for /asset/<kind>/<name>; converted on first request and cached."""
    res, idx, cache = load(root)
    stem, _, ext = name.rpartition(".")
    if not re.fullmatch(r"[A-Za-z0-9_\-\[\]\\^~!@$%&]+", stem or ""):
        return None
    types = {"png": "image/png", "wav": "audio/wav", "ogg": "audio/ogg", "flac": "audio/flac", "mid": "audio/midi"}
    if kind == "soundfont" and name == "uzdoom.sf2":
        # The game's own soundfont, for the page's MIDI synth (assets-synth.js); served from .tools, not copied.
        from dms.launch import tool_path

        sf = tool_path(root, "uzdoom").parent / "soundfonts" / "uzdoom.sf2"
        return (sf.read_bytes(), "application/octet-stream") if sf.is_file() else None
    f = cache / kind / name
    if f.is_file():
        return f.read_bytes(), types.get(ext, "application/octet-stream")
    data: bytes | None = None
    if kind in ("tex", "flat", "sprite", "decal") and ext == "png":
        if kind == "tex":
            p = res.texture(stem)
        elif kind == "flat":
            p = res.flat(stem)
        elif kind == "sprite":
            p = res.sprite(stem)
        else:
            d = next((x for x in idx.categories.get("decals", []) if x["name"].lower() == stem.lower()), None)
            p = res.graphic(d["pic"]) if d and d["pic"] else None
            rgb = shade_rgb(d["shade"]) if d else None
            if p is not None and rgb:
                p = stencil(p, rgb)
        data = png_bytes(p) if p else None
    elif kind == "sound":
        got = res.sound_file(stem)
        data = got[0] if got and got[1] == ext else None
    elif kind == "music" and ext == "mid":
        data = res.music_lump(stem)
    if not data:
        return None
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_bytes(data)
    return data, types.get(ext, "application/octet-stream")


# ---- favourites -------------------------------------------------------------------------------
# The mapper's favourite assets, starred in the asset browser: {category: [name, ...]}, kept by the
# board in build/asset-favorites.json (not per browser, and readable by Claude: "my favourite
# textures"). Names, not resource keys: a favourite stays one when the IWAD or the pk3 changes.
FAVORITES_FILE = "asset-favorites.json"
_fav_lock = __import__("threading").Lock()


def favorites(root: Path) -> dict[str, list[str]]:
    try:
        data = json.loads((root / "build" / FAVORITES_FILE).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return {str(k): [str(n) for n in v] for k, v in data.items() if isinstance(v, list)} if isinstance(data, dict) else {}


def set_favorite(root: Path, category: str, name: str, on: bool) -> dict[str, list[str]]:
    """Stars or unstars `name` in `category`; returns all the favourites."""
    with _fav_lock:
        favs = favorites(root)
        names = [n for n in favs.get(category, []) if n != name]
        if on:
            names.append(name)
        if names:
            favs[category] = sorted(names)
        else:
            favs.pop(category, None)
        f = root / "build" / FAVORITES_FILE
        f.parent.mkdir(parents=True, exist_ok=True)
        tmp = f.with_suffix(".tmp")
        tmp.write_bytes(json.dumps(favs, indent=1, sort_keys=True).encode("utf-8") + b"\n")
        tmp.replace(f)
        return favs
