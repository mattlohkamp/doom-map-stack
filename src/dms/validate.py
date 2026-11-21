"""Checks on a map's TEXTMAP that catch broken or unplayable maps before they reach the engine.

Errors make the map broken or unplayable; warnings are likely mistakes. Each issue names the
element (with its user_gid when it has one) and, where it makes sense, a position, so the
renderer can mark it. `dms build` runs this; `dms validate` runs it on its own (also on the
mapper's edit.wad).
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from dms.catalog import Catalog
from dms.udmf import Block, Textmap

PLAYER1_START = 1

# Line specials whose first argument is a sector tag (0 on a door means "the sector behind this line").
TAGGED_SPECIALS = {
    10, 11, 12, 13,  # Door_Close, Door_Open, Door_Raise, Door_LockedRaise
    20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 35, 36, 37, 38,  # floors
    40, 41, 42, 43, 44, 45, 69, 97, 104, 168, 169,  # ceilings
    60, 61, 62, 63, 64, 65, 172, 206, 207, 228,  # platforms / lifts
    94, 95, 96, 99, 245, 246,  # pillars, elevators, crushers
}
DOOR_SPECIALS_TAG0_OK = {10, 11, 12, 13}


@dataclass
class Issue:
    severity: str  # "error" | "warning"
    message: str
    where: str = ""
    pos: tuple[float, float] | None = None

    def __str__(self) -> str:
        at = f" at ({self.pos[0]:g}, {self.pos[1]:g})" if self.pos else ""
        return f"{self.severity}: {self.where}{': ' if self.where else ''}{self.message}{at}"


def _name(kind: str, i: int, b: Block) -> str:
    gid = b.get("user_gid")
    return f"{kind} {i}" + (f" ({gid})" if gid else "")


def _intersects(p1, p2, p3, p4) -> bool:
    """True if segments p1-p2 and p3-p4 cross at a point that isn't a shared endpoint."""
    def orient(a, b, c):
        v = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
        return (v > 1e-9) - (v < -1e-9)

    if {p1, p2} & {p3, p4}:
        return False
    o1, o2, o3, o4 = orient(p1, p2, p3), orient(p1, p2, p4), orient(p3, p4, p1), orient(p3, p4, p2)
    if o1 != o2 and o3 != o4 and 0 not in (o1, o2, o3, o4):
        return True

    def on_seg(a, b, c):  # c collinear with a-b and within its box
        return min(a[0], b[0]) <= c[0] <= max(a[0], b[0]) and min(a[1], b[1]) <= c[1] <= max(a[1], b[1])

    return (o1 == 0 and on_seg(p1, p2, p3)) or (o2 == 0 and on_seg(p1, p2, p4)) or \
           (o3 == 0 and on_seg(p3, p4, p1)) or (o4 == 0 and on_seg(p3, p4, p2))


def sector_edges(tm: Textmap) -> dict[int, list[tuple[int, int]]]:
    """For each sector, its boundary as directed vertex pairs with the sector on the right."""
    sides, lines = tm.sidedefs, tm.linedefs
    edges: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for ld in lines:
        v1, v2 = ld.get("v1"), ld.get("v2")
        for key, a, b in (("sidefront", v1, v2), ("sideback", v2, v1)):
            s = ld.get(key, -1)
            if isinstance(s, int) and 0 <= s < len(sides):
                sec = sides[s].get("sector")
                if isinstance(sec, int):
                    edges[sec].append((a, b))
    return edges


def sector_at(tm: Textmap, x: float, y: float, edges=None) -> int | None:
    """The sector containing (x, y) (even-odd test over each sector's boundary), smallest if nested."""
    verts = [(v["x"], v["y"]) for v in tm.vertices]
    edges = edges if edges is not None else sector_edges(tm)
    best, best_area = None, None
    for sec, es in edges.items():
        inside = False
        area = 0.0
        for a, b in es:
            if not (0 <= a < len(verts) and 0 <= b < len(verts)):
                continue
            (x1, y1), (x2, y2) = verts[a], verts[b]
            area += x1 * y2 - x2 * y1
            if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
                inside = not inside
        if inside and (best_area is None or abs(area) < best_area):
            best, best_area = sec, abs(area)
    return best


def validate(tm: Textmap, catalog: Catalog | None = None) -> list[Issue]:
    out: list[Issue] = []
    err = lambda msg, where="", pos=None: out.append(Issue("error", msg, where, pos))  # noqa: E731
    warn = lambda msg, where="", pos=None: out.append(Issue("warning", msg, where, pos))  # noqa: E731

    if str(tm.globals.get("namespace", "")).lower() != "zdoom":
        warn(f'namespace is {tm.globals.get("namespace")!r}; UZDoom maps use "zdoom"')

    verts, lines, sides, sectors, things = tm.vertices, tm.linedefs, tm.sidedefs, tm.sectors, tm.things
    vpos = [(v.get("x"), v.get("y")) for v in verts]
    for i, v in enumerate(verts):
        if not isinstance(v.get("x"), (int, float)) or not isinstance(v.get("y"), (int, float)):
            err("vertex without x/y", _name("vertex", i, v))
    used_verts, used_sides = set(), set()

    def mid(ld):
        a, b = ld.get("v1"), ld.get("v2")
        if isinstance(a, int) and isinstance(b, int) and a < len(vpos) and b < len(vpos):
            return ((vpos[a][0] + vpos[b][0]) / 2, (vpos[a][1] + vpos[b][1]) / 2)
        return None

    # -- linedefs ---------------------------------------------------------
    good_lines = []
    for i, ld in enumerate(lines):
        n = _name("linedef", i, ld)
        v1, v2 = ld.get("v1"), ld.get("v2")
        if not all(isinstance(v, int) and 0 <= v < len(verts) for v in (v1, v2)):
            err("refers to a vertex that doesn't exist", n)
            continue
        used_verts |= {v1, v2}
        if vpos[v1] == vpos[v2]:
            err("has zero length", n, vpos[v1])
            continue
        front, back = ld.get("sidefront"), ld.get("sideback", -1)
        if front is None or front == -1:
            err("has no front side (sidefront)", n, mid(ld))
        for key, s in (("sidefront", front), ("sideback", back)):
            if s is None or s == -1:
                continue
            if not (isinstance(s, int) and 0 <= s < len(sides)):
                err(f"{key} refers to a sidedef that doesn't exist", n, mid(ld))
            else:
                used_sides.add(s)
        if isinstance(front, int) and 0 <= front < len(sides) and back in (None, -1):
            if sides[front].get("texturemiddle", "-") == "-":
                err("one-sided wall has no middle texture (shows as a hall of mirrors)", n, mid(ld))
        special = ld.get("special", 0)
        if special in TAGGED_SPECIALS:
            tag = ld.get("arg0", 0)
            if tag == 0 and special not in DOOR_SPECIALS_TAG0_OK:
                err(f"special {special} needs a sector tag in arg0", n, mid(ld))
            elif tag and not any(_has_tag(s, tag) for s in sectors):
                err(f"special {special} targets tag {tag}, but no sector has that tag", n, mid(ld))
        good_lines.append(i)

    # Lines that cross each other (not at a shared vertex) break the map.
    segs = [(i, vpos[lines[i]["v1"]], vpos[lines[i]["v2"]]) for i in good_lines]
    boxes = [(min(a[0], b[0]), max(a[0], b[0]), min(a[1], b[1]), max(a[1], b[1])) for _, a, b in segs]
    for j in range(len(segs)):
        for k in range(j + 1, len(segs)):
            bj, bk = boxes[j], boxes[k]
            if bj[1] < bk[0] or bk[1] < bj[0] or bj[3] < bk[2] or bk[3] < bj[2]:
                continue
            (i1, a1, b1), (i2, a2, b2) = segs[j], segs[k]
            if _intersects(a1, b1, a2, b2):
                err(f"crosses {_name('linedef', i2, lines[i2])}", _name("linedef", i1, lines[i1]), mid(lines[i1]))

    # -- sidedefs ---------------------------------------------------------
    used_sectors = set()
    for i, sd in enumerate(sides):
        n = _name("sidedef", i, sd)
        sec = sd.get("sector")
        if not (isinstance(sec, int) and 0 <= sec < len(sectors)):
            err("refers to a sector that doesn't exist", n)
        else:
            used_sectors.add(sec)
        if i not in used_sides:
            warn("isn't used by any linedef", n)
        if catalog:
            for key in ("texturetop", "texturemiddle", "texturebottom"):
                tex = sd.get(key, "-")
                if tex != "-" and not catalog.has_texture(tex):
                    if catalog.has_flat(tex):
                        warn(f"{key} {tex!r} is a flat, not a wall texture", n)
                    else:
                        err(f"{key} {tex!r} isn't in the texture catalog", n)

    for i, _ in enumerate(verts):
        if i not in used_verts:
            warn("isn't used by any linedef", _name("vertex", i, verts[i]), vpos[i])
    seen_pos: dict = {}
    for i, p in enumerate(vpos):
        if p in seen_pos:
            warn(f"is at the same position as vertex {seen_pos[p]}", f"vertex {i}", p)
        else:
            seen_pos[p] = i

    # -- sectors ----------------------------------------------------------
    edges = sector_edges(tm)

    def sector_pos(i):
        pts = [vpos[v] for e in edges.get(i, []) for v in e if 0 <= v < len(vpos)]
        return (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)) if pts else None

    for i, s in enumerate(sectors):
        n = _name("sector", i, s)
        here = sector_pos(i)
        if i not in used_sectors:
            err("isn't used by any sidedef (orphan sector)", n)
            continue
        degree: dict[int, int] = defaultdict(int)
        for a, b in edges.get(i, []):
            degree[a] += 1
            degree[b] -= 1
        open_at = [v for v, d in degree.items() if d != 0]
        if open_at:
            err("isn't closed (its walls don't form complete loops)", n, vpos[open_at[0]])
        light = s.get("lightlevel", 160)
        if not (isinstance(light, int) and 0 <= light <= 255):
            err(f"light level {light} is outside 0-255", n, here)
        floor, ceil = s.get("heightfloor", 0), s.get("heightceiling", 0)
        if isinstance(floor, (int, float)) and isinstance(ceil, (int, float)) and ceil < floor:
            err(f"ceiling ({ceil}) is below the floor ({floor})", n, here)
        if catalog:
            for key in ("texturefloor", "textureceiling"):
                flat = s.get(key, "-")
                if not catalog.has_flat(flat):
                    if catalog.has_texture(flat):
                        warn(f"{key} {flat!r} is a wall texture, not a flat", n, here)
                    else:
                        err(f"{key} {flat!r} isn't in the flat catalog", n, here)

    # -- things -----------------------------------------------------------
    starts = [t for t in things if t.get("type") == PLAYER1_START]
    if not starts:
        err("no player 1 start (thing type 1)")
    elif len(starts) > 1:
        warn(f"{len(starts)} player 1 starts; the extra ones become voodoo dolls")
    for i, t in enumerate(things):
        x, y = t.get("x"), t.get("y")
        if not isinstance(x, (int, float)) or not isinstance(y, (int, float)):
            err("thing without x/y", _name("thing", i, t))
            continue
        if sector_at(tm, x, y, edges) is None:
            err("is outside every sector", _name("thing", i, t), (x, y))
        if not any(t.get(f"skill{k}") for k in range(1, 6)):
            warn("isn't on any skill level (skill1-5 all off), so it never appears", _name("thing", i, t), (x, y))

    return out


def _has_tag(sector: Block, tag: int) -> bool:
    if sector.get("id") == tag:
        return True
    more = sector.get("moreids", "")
    return isinstance(more, str) and str(tag) in more.split()


def report(issues: list[Issue], title: str) -> str:
    errors = sum(1 for i in issues if i.severity == "error")
    warnings = len(issues) - errors
    lines = [f"{title}: {errors} error(s), {warnings} warning(s)"]
    lines += [f"  {i}" for i in sorted(issues, key=lambda i: i.severity != "error")]
    return "\n".join(lines) + "\n"
