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
THING = (220, 90, 220)
ISSUE = (255, 60, 60)
ADDED = (60, 230, 90)
REMOVED = (255, 70, 70)
CHANGED = (255, 220, 60)
LABEL = (200, 200, 210)

TARGET_PX = 1024
MARGIN = 64  # map units around the map


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

    if labels and not dim:
        for sec, polys in loops.items():
            if polys and 0 <= sec < len(sectors):
                biggest = max(polys, key=polygon_area)
                cx, cy = view.px(*centroid(biggest))
                gid = sectors[sec].get("user_gid")
                draw.text((cx, cy), f"{sec}" + (f" {gid}" if gid else ""), fill=LABEL, font=font, anchor="mm")

    for t in tm.things:
        if "x" not in t.fields:
            continue
        cx, cy = view.px(t["x"], t["y"])
        r = max(4, 16 * view.scale)
        is_player = t.get("type") in (1, 2, 3, 4)
        color = PLAYER if is_player else THING
        if dim:
            color = tuple(int(c * 0.45) for c in color)
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color, width=2)
        ang = math.radians(t.get("angle", 0))
        draw.line([(cx, cy), (cx + math.cos(ang) * r * 1.8, cy - math.sin(ang) * r * 1.8)], fill=color, width=2)
        if not is_player and not dim:
            draw.text((cx + r + 2, cy), str(t.get("type")), fill=color, font=font, anchor="lm")


def render(tm: Textmap, out_png: Path, issues: list[Issue] = (), title: str = "") -> Path:
    view = view_for(tm)
    img = Image.new("RGB", (view.width, view.height), BG)
    _grid(ImageDraw.Draw(img), view, _font(11))
    _draw_map(img, view, tm)
    draw = ImageDraw.Draw(img)
    font = _font(13)
    for n, issue in enumerate([i for i in issues if i.pos], 1):
        cx, cy = view.px(*issue.pos)
        r = max(10, 28 * view.scale)
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=ISSUE, width=3)
        draw.text((cx + r + 2, cy - r), f"#{n}", fill=ISSUE, font=font)
    if title:
        draw.text((view.width - 6, view.height - 6), title, fill=GRID_LABEL, font=font, anchor="rd")
    out_png.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_png)
    out_png.with_suffix(".txt").write_text(describe(tm, issues, view, title), encoding="utf-8", newline="\n")
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
    lines.append(f"things ({len(tm.things)}): index, type, position, angle, gid")
    for i, t in enumerate(tm.things):
        lines.append(f"  {i} type {t.get('type')} at ({t.get('x', 0):g}, {t.get('y', 0):g}) angle {t.get('angle', 0)}"
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
    sides = tm.sidedefs
    def side(k):
        s = ld.get(k, -1)
        return tuple(sorted(sides[s].fields.items())) if isinstance(s, int) and 0 <= s < len(sides) else None
    own = tuple(sorted((k, v) for k, v in ld.fields.items() if k not in ("v1", "v2", "sidefront", "sideback")))
    return own, side("sidefront"), side("sideback")


def _key_by_gid_or_index(blocks: list[Block]) -> dict:
    gids = [b.get("user_gid") for b in blocks]
    return {(g if g and gids.count(g) == 1 else ("#", i)): b for i, (g, b) in enumerate(zip(gids, blocks))}


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
    # Sectors: the editor copies a gid when it splits a sector (see PLAN.md section 9), so match each
    # current sector to the previous one with the same gid (several may share it); without a gid,
    # fall back to the same index if that previous sector has no gid either.
    prev_by_gid: dict = {}
    for b in prev.sectors:
        prev_by_gid.setdefault(b.get("user_gid"), b)
    matched_prev = set()
    for idx, s in enumerate(cur.sectors):
        gid = s.get("user_gid")
        old = prev_by_gid.get(gid) if gid else (
            prev.sectors[idx] if idx < len(prev.sectors) and not prev.sectors[idx].get("user_gid") else None)
        if old is None:
            changes["changed_sectors"].append((gid or ("#", idx), idx, ["new sector"]))
            continue
        matched_prev.add(id(old))
        if s.fields != old.fields:
            diffs = sorted(f for f in set(s.fields) | set(old.fields) if s.get(f) != old.get(f))
            changes["changed_sectors"].append((gid or ("#", idx), idx, diffs))
    changes["removed_sectors"] = [b.get("user_gid") or f"#{i}" for i, b in enumerate(prev.sectors)
                                  if id(b) not in matched_prev]
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


def render_diff(prev: Textmap, cur: Textmap, out_png: Path, title: str = "") -> bool:
    """Write diff.png/diff.txt. Returns False (and removes old diff files) if nothing changed."""
    changes = diff(prev, cur)
    out_txt = out_png.with_suffix(".txt")
    if not any(changes.values()):
        out_png.unlink(missing_ok=True)
        out_txt.write_text(f"{title}: no changes since the previous build\n", encoding="utf-8", newline="\n")
        return False
    view = view_for(prev, cur)
    img = Image.new("RGB", (view.width, view.height), BG)
    _grid(ImageDraw.Draw(img), view, _font(11))
    _draw_map(img, view, cur, dim=True)
    draw = ImageDraw.Draw(img)
    w = max(2, round(view.scale * 3))
    loops = sector_loops(cur)
    for _k, idx, _f in changes["changed_sectors"]:
        for poly in loops.get(idx, []):
            draw.polygon([view.px(*p) for p in poly], outline=CHANGED, width=w)
    for key, color in (("removed_lines", REMOVED), ("added_lines", ADDED), ("changed_lines", CHANGED)):
        for a, *rest in changes[key]:
            b = rest[0] if rest else a
            draw.line([view.px(*a), view.px(*b)], fill=color, width=w)
    r = max(5, 16 * view.scale)
    for key, color in (("added_things", ADDED), ("removed_things", REMOVED)):
        for _k, t in changes[key]:
            cx, cy = view.px(t.get("x", 0), t.get("y", 0))
            draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color, width=3)
    for _k, old, new in changes["moved_things"]:
        a, b = view.px(old.get("x", 0), old.get("y", 0)), view.px(new.get("x", 0), new.get("y", 0))
        draw.line([a, b], fill=CHANGED, width=2)
        draw.ellipse([b[0] - r, b[1] - r, b[0] + r, b[1] + r], outline=CHANGED, width=3)
    if title:
        draw.text((view.width - 6, view.height - 6), title, fill=GRID_LABEL, font=_font(13), anchor="rd")
    img.save(out_png)

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
