"""Top-down PNG of a map (and a text version), plus a before/after diff between two builds.

render.png: sectors shaded by floor height (darker = lower), one-sided walls white, two-sided
lines grey, lines with a special orange, things as circles (player start green, with an arrow
for its angle), a coordinate grid, and validation issues as numbered red rings. render.txt says
the same in words. diff.png: the current map dimmed, with added lines green, removed red, and
changed lines/sectors/things yellow; diff.txt lists the changes.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from dms.udmf import Block, Textmap
from dms.validate import Issue, sector_edges

BG = (24, 24, 28)
GRID_FINE = (36, 36, 42)
GRID_MAJOR = (58, 58, 68)
GRID_LABEL = (110, 110, 125)
WALL = (235, 235, 235)
TWO_SIDED = (130, 130, 145)
SPECIAL = (255, 165, 0)
PLAYER = (70, 220, 100)
THING = (150, 130, 175)      # other things: lights, decoration, markers
MONSTER = (255, 85, 60)
ITEM = (80, 200, 255)
ISSUE = (255, 60, 60)
ADDED = (60, 230, 90)
REMOVED = (255, 70, 70)
CHANGED = (255, 220, 60)
LABEL = (200, 200, 210)

TARGET_PX = 1024
MARGIN = 64  # map units around the map


# Pickups not in movement's tables (ammo, small health and armour), for when the editor isn't installed.
_SMALL_PICKUPS = {2007: "clip", 2048: "box of bullets", 2008: "shells", 2049: "box of shells", 2010: "rocket",
                  2046: "box of rockets", 2047: "cell", 17: "cell pack", 2011: "stimpack", 2012: "medikit",
                  2014: "health bonus", 2015: "armor bonus"}
_KINDS: dict[int, tuple[str, str]] | None = None


def thing_kind(type_) -> tuple[str, str]:
    """(kind, name) of a thing type: kind "player", "monster", "item" (anything picked up) or "other"
    (lights, decoration, markers). From the editor's thing lists when it is installed (every type it
    knows), else from the tables dms has."""
    global _KINDS
    if _KINDS is None:
        from dms import movement

        kinds: dict[int, tuple[str, str]] = {}
        try:
            from dms import paths, resources
            from dms.launch import tool_path

            groups = {"monsters": "monster", "items": "item"}
            for num, t in resources.editor_things(tool_path(paths.repo_root(), "udb").parent).items():
                kinds[num] = (groups.get(resources.THING_GROUPS.get(t["category"], ""), "other"), t["title"])
        except (SystemExit, Exception):  # not installed, or its files aren't as expected: the tables below
            pass
        for table, kind in ((_SMALL_PICKUPS, "item"), (movement.ITEMS, "item"), (movement.WEAPONS, "item"),
                            (movement.KEYS, "item")):
            for num, name in table.items():
                kinds.setdefault(num, (kind, name))
        for num, spec in movement.MONSTERS.items():
            kinds.setdefault(num, ("monster", spec[0]))
        for num in (1, 2, 3, 4):
            kinds[num] = ("player", f"player {num} start")
        _KINDS = kinds
    return _KINDS.get(type_, ("other", ""))


THING_COLORS = {"player": PLAYER, "monster": MONSTER, "item": ITEM, "other": THING}


def _font(size: int):
    try:
        return ImageFont.load_default(size)
    except (TypeError, OSError):
        return ImageFont.load_default()


@dataclass
class View:
    minx: float
    miny: float
    maxx: float
    maxy: float
    scale: float
    width: int = field(init=False)
    height: int = field(init=False)

    def __post_init__(self) -> None:
        self.width = max(1, math.ceil((self.maxx - self.minx) * self.scale))
        self.height = max(1, math.ceil((self.maxy - self.miny) * self.scale))

    def px(self, x: float, y: float) -> tuple[float, float]:
        """Map coordinates -> image pixels (Doom's y axis points up, the image's down)."""
        return ((x - self.minx) * self.scale, (self.maxy - y) * self.scale)


def view_for(*maps: Textmap) -> View:
    xs, ys = [], []
    for tm in maps:
        xs += [v["x"] for v in tm.vertices] + [t["x"] for t in tm.things if "x" in t.fields]
        ys += [v["y"] for v in tm.vertices] + [t["y"] for t in tm.things if "y" in t.fields]
    if not xs:
        xs, ys = [0, 512], [0, 512]
    minx, maxx, miny, maxy = min(xs) - MARGIN, max(xs) + MARGIN, min(ys) - MARGIN, max(ys) + MARGIN
    span = max(maxx - minx, maxy - miny)
    scale = min(max(TARGET_PX / span, 0.05), 2.0)
    return View(minx, miny, maxx, maxy, scale)


def sector_loops(tm: Textmap) -> dict[int, list[list[tuple[float, float]]]]:
    """Each sector's boundary as closed polygons (lists of points)."""
    verts = [(v["x"], v["y"]) for v in tm.vertices]
    out: dict[int, list[list[tuple[float, float]]]] = {}
    for sec, edges in sector_edges(tm).items():
        edges = [(a, b) for a, b in edges if 0 <= a < len(verts) and 0 <= b < len(verts)]
        unused = list(range(len(edges)))
        by_start: dict[int, list[int]] = {}
        for k, (a, _b) in enumerate(edges):
            by_start.setdefault(a, []).append(k)
        loops = []
        used = set()
        for k in unused:
            if k in used:
                continue
            start, loop, cur = edges[k][0], [], k
            while cur is not None and cur not in used:
                used.add(cur)
                a, b = edges[cur]
                loop.append(verts[a])
                if b == start:
                    break
                cur = next((n for n in by_start.get(b, []) if n not in used), None)
            if len(loop) >= 3:
                loops.append(loop)
        out[sec] = loops
    return out


def polygon_area(pts) -> float:
    return abs(sum(x1 * y2 - x2 * y1 for (x1, y1), (x2, y2) in zip(pts, pts[1:] + pts[:1]))) / 2


def centroid(pts) -> tuple[float, float]:
    return (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))


def _grid(draw: ImageDraw.ImageDraw, view: View, font) -> None:
    fine = 64
    major = 512 if view.scale * 512 >= 60 else 1024
    if view.scale * fine >= 6:
        for x in range(math.floor(view.minx / fine) * fine, int(view.maxx) + 1, fine):
            draw.line([view.px(x, view.miny), view.px(x, view.maxy)], fill=GRID_FINE)
        for y in range(math.floor(view.miny / fine) * fine, int(view.maxy) + 1, fine):
            draw.line([view.px(view.minx, y), view.px(view.maxx, y)], fill=GRID_FINE)
    for x in range(math.floor(view.minx / major) * major, int(view.maxx) + 1, major):
        draw.line([view.px(x, view.miny), view.px(x, view.maxy)], fill=GRID_MAJOR)
        draw.text((view.px(x, 0)[0] + 2, 2), str(x), fill=GRID_LABEL, font=font)
    for y in range(math.floor(view.miny / major) * major, int(view.maxy) + 1, major):
        draw.line([view.px(view.minx, y), view.px(view.maxx, y)], fill=GRID_MAJOR)
        draw.text((2, view.px(0, y)[1] + 2), str(y), fill=GRID_LABEL, font=font)


def _floor_shade(h: float, lo: float, hi: float) -> tuple[int, int, int]:
    t = 0.5 if hi == lo else (h - lo) / (hi - lo)
    v = int(55 + 95 * t)
    return (v, v, v + 12)


def _line_points(tm: Textmap, ld: Block):
    verts = tm.vertices
    a, b = ld.get("v1"), ld.get("v2")
    if not (isinstance(a, int) and isinstance(b, int) and 0 <= a < len(verts) and 0 <= b < len(verts)):
        return None
    return (verts[a]["x"], verts[a]["y"]), (verts[b]["x"], verts[b]["y"])


def _draw_map(img: Image.Image, view: View, tm: Textmap, *, dim: bool = False, labels: bool = True) -> None:
    draw = ImageDraw.Draw(img)
    font = _font(12)
    sectors = tm.sectors
    loops = sector_loops(tm)
    heights = [s.get("heightfloor", 0) for s in sectors] or [0]
    lo, hi = min(heights), max(heights)
    # Larger sectors first, so sectors inside other sectors are drawn on top.
    order = sorted(loops, key=lambda s: -max((polygon_area(p) for p in loops[s]), default=0))
    for sec in order:
        if not (0 <= sec < len(sectors)):
            continue
        shade = _floor_shade(sectors[sec].get("heightfloor", 0), lo, hi)
        if dim:
            shade = tuple(int(c * 0.5) for c in shade)
        for poly in loops[sec]:
            draw.polygon([view.px(*p) for p in poly], fill=shade)

    w = max(1, round(view.scale * 2))
    for ld in tm.linedefs:
        pts = _line_points(tm, ld)
        if not pts:
            continue
        two = ld.get("sideback", -1) not in (-1, None)
        color, width = (TWO_SIDED, 1) if two else (WALL, w)
        if ld.get("special", 0):
            color, width = SPECIAL, w + 1
        if dim:
            color = tuple(int(c * 0.45) for c in color)
        draw.line([view.px(*pts[0]), view.px(*pts[1])], fill=color, width=width)

    pending: list[Label] = []
    if labels and not dim:
        for sec, polys in loops.items():
            if polys and 0 <= sec < len(sectors):
                biggest = max(polys, key=polygon_area)
                cx, cy = view.px(*centroid(biggest))
                gid = sectors[sec].get("user_gid")
                pending.append(Label(f"{sec}" + (f" {gid}" if gid else ""), (cx, cy), LABEL,
                                     priority=polygon_area(biggest)))

    markers: list[tuple[float, float, float, float]] = []
    for t in tm.things:
        if "x" not in t.fields:
            continue
        cx, cy = view.px(t["x"], t["y"])
        r = max(4, 16 * view.scale)
        kind = thing_kind(t.get("type"))[0]
        is_player = kind == "player"
        color = THING_COLORS[kind]
        if dim:
            color = tuple(int(c * 0.45) for c in color)
        # Monsters and player starts: a circle with an arrow for the way they face. Items: a diamond.
        # Everything else (lights, decoration): a smaller circle.
        if kind == "item":
            draw.polygon([(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)], outline=color, width=2)
        elif kind == "other":
            draw.ellipse([cx - r * 0.6, cy - r * 0.6, cx + r * 0.6, cy + r * 0.6], outline=color, width=2)
        else:
            draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color, width=2)
            ang = math.radians(t.get("angle", 0))
            draw.line([(cx, cy), (cx + math.cos(ang) * r * 1.8, cy - math.sin(ang) * r * 1.8)], fill=color, width=2)
        markers.append((cx - r, cy - r, cx + r, cy + r))
        if not is_player and not dim:
            pending.append(Label(str(t.get("type")), (cx, cy), color, priority=-1, gap=r + 2))
    place_labels(draw, pending, font, (img.width, img.height), obstacles=markers)


@dataclass
class Label:
    text: str
    anchor: tuple[float, float]   # the point it labels, in pixels
    color: tuple
    priority: float = 0           # placed in increasing order: things (-1), then sectors small to large
    gap: float = 0                # > 0: its natural spot is beside the anchor (things), not on it


# Where a label may go, tried in order: rings of growing radius round its natural spot, 16 directions
# each, starting to the right and alternating above and below. Pixels.
_RINGS = (0, 10, 18, 28, 40, 54, 70, 90, 115, 145, 180)
_DIRS = sorted(range(16), key=lambda k: (min(k, 16 - k), k))


def place_labels(draw: ImageDraw.ImageDraw, labels: list[Label], font, size: tuple[int, int],
                 obstacles=()) -> None:
    """Draw labels so they don't cover each other (or the obstacles: things' markers). Each goes at
    its natural spot if it's free, else at the nearest free spot on rings around it, joined to what it
    labels by a 1px leader line and a dot. If nowhere is free it goes at its natural spot anyway."""
    taken = [tuple(o) for o in obstacles]
    w_img, h_img = size

    def free(box) -> bool:
        x0, y0, x1, y1 = box
        if x0 < 0 or y0 < 0 or x1 > w_img or y1 > h_img:
            return False
        return not any(x0 < b[2] and b[0] < x1 and y0 < b[3] and b[1] < y1 for b in taken)

    for lab in sorted(labels, key=lambda l: l.priority):
        bx0, by0, bx1, by1 = font.getbbox(lab.text)
        w, h = bx1 - bx0 + 4, by1 - by0 + 4
        ax, ay = lab.anchor
        home = (ax + lab.gap + w / 2, ay) if lab.gap else (ax, ay)   # the label's centre, undisturbed
        best = None
        for radius in _RINGS:
            for k in (_DIRS if radius else (0,)):
                a = 2 * math.pi * k / 16
                cx, cy = home[0] + radius * math.cos(a), home[1] - radius * math.sin(a)
                box = (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)
                if free(box):
                    best = box
                    break
            if best:
                break
        moved = best is not None and ((best[0] + best[2]) / 2, (best[1] + best[3]) / 2) != home
        if best is None:
            best = (home[0] - w / 2, home[1] - h / 2, home[0] + w / 2, home[1] + h / 2)
        taken.append(best)
        if moved:
            # The leader: from the anchor to the nearest point of the label's box.
            nx = min(max(ax, best[0]), best[2])
            ny = min(max(ay, best[1]), best[3])
            lead = tuple(int(c * 0.7) for c in lab.color[:3])
            draw.line([(ax, ay), (nx, ny)], fill=lead, width=1)
            draw.ellipse([ax - 1.5, ay - 1.5, ax + 1.5, ay + 1.5], fill=lead)
        draw.text(((best[0] + best[2]) / 2, (best[1] + best[3]) / 2), lab.text, fill=lab.color, font=font, anchor="mm")


SOFTLOCK = (255, 150, 40)


def _mark_sectors(img: Image.Image, view: View, tm: Textmap, unreachable, softlocks) -> Image.Image:
    """Hatch unreachable sectors in red; tint soft-lock sectors orange (movement check)."""
    if not unreachable and not softlocks:
        return img
    loops = sector_loops(tm)
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    for sec in softlocks:
        d = ImageDraw.Draw(layer)
        for poly in loops.get(sec, []):
            d.polygon([view.px(*p) for p in poly], fill=SOFTLOCK + (70,), outline=SOFTLOCK + (255,))
    if unreachable:
        mask = Image.new("L", img.size, 0)
        dm = ImageDraw.Draw(mask)
        for sec in unreachable:
            for poly in loops.get(sec, []):
                dm.polygon([view.px(*p) for p in poly], fill=255)
        hatch = Image.new("RGBA", img.size, (0, 0, 0, 0))
        dh = ImageDraw.Draw(hatch)
        w, h = img.size
        for x in range(-h, w, 14):
            dh.line([(x, h), (x + h, 0)], fill=ISSUE + (150,), width=2)
        layer.paste(hatch, (0, 0), mask)
    return Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB")


def render(tm: Textmap, out_png: Path, issues: list[Issue] = (), title: str = "",
           unreachable=(), softlocks=()) -> Path:
    view = view_for(tm)
    img = Image.new("RGB", (view.width, view.height), BG)
    _grid(ImageDraw.Draw(img), view, _font(11))
    _draw_map(img, view, tm)
    img = _mark_sectors(img, view, tm, set(unreachable), set(softlocks))
    draw = ImageDraw.Draw(img)
    font = _font(13)
    at_same_spot: dict[tuple, int] = {}
    for n, issue in enumerate([i for i in issues if i.pos], 1):
        cx, cy = view.px(*issue.pos)
        k = at_same_spot.get(issue.pos, 0)  # several issues at one spot: bigger rings, labels stacked
        at_same_spot[issue.pos] = k + 1
        r0 = max(10, 28 * view.scale)
        r = r0 + 7 * k
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=ISSUE, width=3)
        draw.text((cx + r0 + 24, cy - r0 + 17 * k), f"#{n}", fill=ISSUE, font=font)
    if title:
        draw.text((view.width - 6, view.height - 6), title, fill=GRID_LABEL, font=font, anchor="rd")
    out_png.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_png)
    from dms import svg  # the same picture for the board's pan/zoom map

    svg.write(out_png.with_suffix(".svg"), svg.scene(view, tm, issues=issues, unreachable=set(unreachable),
                                                     softlocks=set(softlocks)))
    text = describe(tm, issues, view, title)
    if unreachable:
        text += f"hatched red: unreachable from the player start: sectors {', '.join(map(str, sorted(unreachable)))}\n"
    if softlocks:
        text += f"tinted orange: soft-locks (no way to an exit): sectors {', '.join(map(str, sorted(softlocks)))}\n"
    out_png.with_suffix(".txt").write_text(text, encoding="utf-8", newline="\n")
    return out_png


def describe(tm: Textmap, issues: list[Issue], view: View, title: str) -> str:
    """render.txt: what the picture shows, in words."""
    lines = [f"{title or 'map'}: top-down render",
             f"bounds x {view.minx + MARGIN:g}..{view.maxx - MARGIN:g}, y {view.miny + MARGIN:g}..{view.maxy - MARGIN:g}"
             f" (map units); {view.scale:.3g} px per unit; north is up", ""]
    loops = sector_loops(tm)
    lines.append(f"sectors ({len(tm.sectors)}): index, gid, floor/ceiling, light, floor/ceiling flats, box")
    for i, s in enumerate(tm.sectors):
        pts = [p for poly in loops.get(i, []) for p in poly]
        box = (f"x {min(p[0] for p in pts):g}..{max(p[0] for p in pts):g}, y {min(p[1] for p in pts):g}..{max(p[1] for p in pts):g}"
               if pts else "no closed outline")
        lines.append(f"  {i} {s.get('user_gid', '-')}: {s.get('heightfloor', 0)}/{s.get('heightceiling', 0)}, "
                     f"light {s.get('lightlevel', 160)}, {s.get('texturefloor')}/{s.get('textureceiling')}, {box}")
    lines.append(f"things ({len(tm.things)}): index, type (kind: name), position, angle, gid; drawn as red circles"
                 " (monsters), blue diamonds (items), small grey circles (lights, decoration), green (player start)")
    for i, t in enumerate(tm.things):
        kind, name = thing_kind(t.get("type"))
        what = f" ({kind}: {name})" if name else f" ({kind})"
        lines.append(f"  {i} type {t.get('type')}{what} at ({t.get('x', 0):g}, {t.get('y', 0):g}) angle {t.get('angle', 0)}"
                     f" {t.get('user_gid', '')}".rstrip())
    specials = [(i, ld) for i, ld in enumerate(tm.linedefs) if ld.get("special", 0)]
    lines.append(f"lines: {len(tm.linedefs)}, of which {len(specials)} with a special")
    for i, ld in specials:
        args = ", ".join(str(ld.get(f"arg{k}", 0)) for k in range(5))
        lines.append(f"  {i} {ld.get('user_gid', '-')}: special {ld['special']}({args})")
    marked = [i for i in issues if i.pos]
    if issues:
        lines.append(f"issues ({len(issues)}; numbered ones are ringed in red):")
        for n, i in enumerate(marked, 1):
            lines.append(f"  #{n} {i}")
        for i in issues:
            if not i.pos:
                lines.append(f"  -  {i}")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------- diff

def _line_key(tm: Textmap, ld: Block):
    pts = _line_points(tm, ld)
    return frozenset(pts) if pts else None


def _line_signature(tm: Textmap, ld: Block) -> tuple:
    sides, sectors = tm.sidedefs, tm.sectors

    def side(k):
        s = ld.get(k, -1)
        if not (isinstance(s, int) and 0 <= s < len(sides)):
            return None
        fields = dict(sides[s].fields)
        sec = fields.get("sector")
        # Which sector, not its number: removing another sector renumbers the rest.
        if isinstance(sec, int) and 0 <= sec < len(sectors) and sectors[sec].get("user_gid"):
            fields["sector"] = sectors[sec].get("user_gid")
        return tuple(sorted(fields.items(), key=lambda kv: kv[0]))
    own = tuple(sorted((k, v) for k, v in ld.fields.items() if k not in ("v1", "v2", "sidefront", "sideback")))
    return own, side("sidefront"), side("sideback")


def _key_by_gid_or_index(blocks: list[Block]) -> dict:
    gids = [b.get("user_gid") for b in blocks]
    return {(g if g and gids.count(g) == 1 else ("#", i)): b for i, (g, b) in enumerate(zip(gids, blocks))}


def match_sectors(prev: Textmap, cur: Textmap) -> list[int | None]:
    """For each current sector, the index of the previous sector it is, or None (new).
    The editor copies a gid when it splits a sector (see PLAN.md section 9), so match each current
    sector to a previous one with the same gid (several may share it): the one at the same index if
    it has that gid, else the first one not matched yet, else the first one (a copy made by a split).
    Without a gid, fall back to the same index if that previous sector has no gid either."""
    by_gid: dict = {}
    for i, b in enumerate(prev.sectors):
        by_gid.setdefault(b.get("user_gid"), []).append(i)
    used: set[int] = set()
    out: list[int | None] = []
    for idx, s in enumerate(cur.sectors):
        gid = s.get("user_gid")
        if gid:
            cands = by_gid.get(gid, [])
            pick = (idx if idx in cands and idx not in used
                    else next((c for c in cands if c not in used), cands[0] if cands else None))
            if pick is not None:
                used.add(pick)
            out.append(pick)
        else:
            same = idx < len(prev.sectors) and not prev.sectors[idx].get("user_gid")
            out.append(idx if same else None)
    return out


def diff(prev: Textmap, cur: Textmap) -> dict[str, list]:
    """Geometry and property changes between two textmaps."""
    pl = {k: ld for ld in prev.linedefs if (k := _line_key(prev, ld))}
    cl = {k: ld for ld in cur.linedefs if (k := _line_key(cur, ld))}
    changes: dict[str, list] = {"added_lines": [], "removed_lines": [], "changed_lines": [],
                                "changed_sectors": [], "added_things": [], "removed_things": [], "moved_things": []}
    for k in cl.keys() - pl.keys():
        changes["added_lines"].append(tuple(k))
    for k in pl.keys() - cl.keys():
        changes["removed_lines"].append(tuple(k))
    for k in cl.keys() & pl.keys():
        if _line_signature(cur, cl[k]) != _line_signature(prev, pl[k]):
            changes["changed_lines"].append(tuple(k))
    matches = match_sectors(prev, cur)
    for idx, (s, old_idx) in enumerate(zip(cur.sectors, matches)):
        gid = s.get("user_gid")
        if old_idx is None:
            changes["changed_sectors"].append((gid or ("#", idx), idx, ["new sector"]))
            continue
        old = prev.sectors[old_idx]
        if s.fields != old.fields:
            diffs = sorted(f for f in set(s.fields) | set(old.fields) if s.get(f) != old.get(f))
            changes["changed_sectors"].append((gid or ("#", idx), idx, diffs))
    matched_prev = set(m for m in matches if m is not None)
    changes["removed_sectors"] = [b.get("user_gid") or f"#{i}" for i, b in enumerate(prev.sectors)
                                  if i not in matched_prev]
    pt, ct = _key_by_gid_or_index(prev.things), _key_by_gid_or_index(cur.things)
    for k in ct.keys() - pt.keys():
        changes["added_things"].append((k, ct[k]))
    for k in pt.keys() - ct.keys():
        changes["removed_things"].append((k, pt[k]))
    for k in ct.keys() & pt.keys():
        if ct[k].fields != pt[k].fields:
            changes["moved_things"].append((k, pt[k], ct[k]))
    return changes


def _fmt(v) -> str:
    return "unset" if v is None else repr(v) if isinstance(v, str) else str(v)


def _old_value(prev: Textmap, cur: Textmap, idx: int, field_name: str):
    gid = cur.sectors[idx].get("user_gid")
    for b in prev.sectors:
        if b.get("user_gid") == gid:
            return b.get(field_name)
    return prev.sectors[idx].get(field_name) if idx < len(prev.sectors) else None


def _mark_changes(img: Image.Image, view: View, prev: Textmap, cur: Textmap, changes: dict, side: str) -> Image.Image:
    """Mark the changes on a full render. side "both": on the current map, with removed things as
    red ghosts; "before": on the previous map (removed red, changed yellow); "after": on the current
    map (added green, changed yellow)."""
    before, after = side in ("both", "before"), side in ("both", "after")
    on = prev if side == "before" else cur
    matches = match_sectors(prev, cur)
    w = max(2, round(view.scale * 3))
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    fill, draw = ImageDraw.Draw(layer), ImageDraw.Draw(img)
    outlines: list[tuple[list, tuple]] = []

    def sector(tm: Textmap, idx: int, color: tuple, alpha: int) -> None:
        for poly in sector_loops(tm).get(idx, []):
            pts = [view.px(*p) for p in poly]
            fill.polygon(pts, fill=color + (alpha,))
            outlines.append((pts, color))

    for _k, idx, fields in changes["changed_sectors"]:
        if fields == ["new sector"]:
            if after:
                sector(cur, idx, ADDED, 70)
        elif side == "before":
            if matches[idx] is not None:
                sector(prev, matches[idx], CHANGED, 40)
        else:
            sector(cur, idx, CHANGED, 40)
    if before:
        matched = set(m for m in matches if m is not None)
        for i in range(len(prev.sectors)):
            if i not in matched:
                sector(prev, i, REMOVED, 70 if side == "before" else 55)

    img = Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB")
    draw = ImageDraw.Draw(img)
    for pts, color in outlines:
        draw.polygon(pts, outline=color, width=max(1, w - 1))
    for key, color, shown in (("removed_lines", REMOVED, before), ("added_lines", ADDED, after),
                              ("changed_lines", CHANGED, True)):
        if not shown:
            continue
        for a, *rest in changes[key]:
            b = rest[0] if rest else a
            draw.line([view.px(*a), view.px(*b)], fill=color, width=w)
    r = max(5, 16 * view.scale)

    def ring(t: Block, color: tuple, width: int = 3) -> tuple[float, float]:
        cx, cy = view.px(t.get("x", 0), t.get("y", 0))
        draw.ellipse([cx - r - 3, cy - r - 3, cx + r + 3, cy + r + 3], outline=color, width=width)
        return cx, cy

    if after:
        for _k, t in changes["added_things"]:
            ring(t, ADDED)
    if before:
        for _k, t in changes["removed_things"]:
            ring(t, REMOVED)
    for _k, old, new in changes["moved_things"]:
        if side == "before":
            ring(old, CHANGED)
        elif side == "after":
            ring(new, CHANGED)
        else:
            a = ring(old, REMOVED, 2)  # where it was: a ghost
            b = ring(new, CHANGED)
            draw.line([a, b], fill=CHANGED, width=2)
    return img


DIFF_SUFFIXES = ("", "-before", "-after")


def render_diff(prev: Textmap, cur: Textmap, out_png: Path, title: str = "") -> bool:
    """Write diff.png (the current map with the changes marked: green added, yellow changed, red
    ghosts of what was removed), diff-before.png / diff-after.png (the previous and current map with
    their side of the changes marked, same view) and diff.txt. Returns False (and removes old diff
    images) if nothing changed."""
    changes = diff(prev, cur)
    out_txt = out_png.with_suffix(".txt")
    if not any(changes.values()):
        stem = out_png.with_suffix("")
        for s in DIFF_SUFFIXES:
            stem.with_name(stem.name + s + ".png").unlink(missing_ok=True)
            stem.with_name(stem.name + s + ".svg").unlink(missing_ok=True)
        out_txt.write_text(f"{title}: no changes since the previous build\n", encoding="utf-8", newline="\n")
        return False
    from dms import svg

    # One view for all three images, so before and after line up.
    view = view_for(prev, cur)
    stem = out_png.with_suffix("")
    for side, path, base in (("both", out_png, cur),
                             ("before", stem.with_name(stem.name + "-before.png"), prev),
                             ("after", stem.with_name(stem.name + "-after.png"), cur)):
        img = Image.new("RGB", (view.width, view.height), BG)
        _grid(ImageDraw.Draw(img), view, _font(11))
        _draw_map(img, view, base)
        img = _mark_changes(img, view, prev, cur, changes, side)
        label = {"both": title, "before": f"{title} (before)", "after": f"{title} (after)"}[side]
        if label:
            ImageDraw.Draw(img).text((view.width - 6, view.height - 6), label, fill=GRID_LABEL, font=_font(13), anchor="rd")
        img.save(path)
        svg.write(path.with_suffix(".svg"), svg.scene(view, base, marks=(prev, cur, changes, side)))

    def pt(p):
        return f"({p[0]:g}, {p[1]:g})"

    lines = [f"{title}: changes since the previous build (green added, red removed, yellow changed)"]
    for key, label in (("added_lines", "added line"), ("removed_lines", "removed line"), ("changed_lines", "changed line")):
        for a, *rest in changes[key]:
            lines.append(f"  {label} {pt(a)}-{pt(rest[0] if rest else a)}")
    for k, idx, fields in changes["changed_sectors"]:
        detail = ", ".join(
            f if f == "new sector" else f"{f} {_fmt(_old_value(prev, cur, idx, f))} -> {_fmt(cur.sectors[idx].get(f))}"
            for f in fields)
        lines.append(f"  changed sector {idx} ({k}): {detail}")
    for k in changes.get("removed_sectors", []):
        lines.append(f"  removed sector ({k})")
    for key, label in (("added_things", "added thing"), ("removed_things", "removed thing")):
        for k, t in changes[key]:
            lines.append(f"  {label} type {t.get('type')} at {pt((t.get('x', 0), t.get('y', 0)))} ({k})")
    for k, old, new in changes["moved_things"]:
        lines.append(f"  changed thing ({k}): {pt((old.get('x', 0), old.get('y', 0)))} -> {pt((new.get('x', 0), new.get('y', 0)))}")
    out_txt.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return True
