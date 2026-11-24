"""The renders as SVG, for the board's pan/zoom map (render.svg, diff.svg, diff-before/-after.svg).

Same picture as render.py's PNGs, in map units (x right, y = -map y, so north is up), written beside
each PNG. Lines keep their width on screen at any zoom (non-scaling strokes). Things, issue rings and
labels carry their map position; the board (board.html) keeps them a constant size on screen and
hides labels that would overlap, so crowded spots spread out as the mapper zooms in. Opened on its
own, the file looks like the PNG (sizes are set for the PNG's scale), with every label drawn.
Sectors, things and lines with a special have a <title>: the board shows it under the cursor.
"""

from __future__ import annotations

import math
from pathlib import Path
from xml.sax.saxutils import escape

from dms import render as R
from dms.udmf import Textmap

_STYLE = """
.dms-map{background:#18181c;font-family:"Segoe UI",system-ui,sans-serif}
.dms-map *{vector-effect:non-scaling-stroke}
.dms-map .gf{stroke:#24242a;stroke-width:1px}
.dms-map .gm{stroke:#3a3a44;stroke-width:1px}
.dms-map .gl{fill:#6e6e7d;font-size:var(--fsg)}
.dms-map .sec{stroke:none}
.dms-map .sec:hover{filter:brightness(1.3)}
.dms-map line,.dms-map .ov,.dms-map .mf,.dms-map .ring,.dms-map .issue{pointer-events:none}
.dms-map .w{stroke:#ebebeb;stroke-width:2px;stroke-linecap:round}
.dms-map .t{stroke:#828291;stroke-width:1px}
.dms-map line.s{stroke:#ffa500;stroke-width:3px;stroke-linecap:round;pointer-events:stroke}
.dms-map .soft{fill:#ff9628;fill-opacity:.27;stroke:#ff9628;stroke-width:1px}
.dms-map .unreach{fill:url(#dms-hatch)}
.dms-map .thing circle,.dms-map .thing path{fill:none;stroke:#9682af;stroke-width:2px;pointer-events:all}
.dms-map .thing line{stroke:#9682af;stroke-width:2px}
.dms-map .thing.player circle,.dms-map .thing.player line{stroke:#46dc64}
.dms-map .thing.monster circle,.dms-map .thing.monster line{stroke:#ff553c}
.dms-map .thing.item path{stroke:#50c8ff}
.dms-map .thing:hover circle,.dms-map .thing:hover path{stroke-width:3.5px}
.dms-map .mf{stroke-width:2px}
.dms-map .ml{stroke-width:3px;stroke-linecap:round}
.dms-map .ring{fill:none;stroke-width:3px}
.dms-map .issue{fill:none;stroke:#ff3c3c;stroke-width:3px}
.dms-map .lbl{font-size:var(--fs);fill:#c8c8d2;text-anchor:middle;dominant-baseline:central;pointer-events:none;
  paint-order:stroke;stroke:#18181c;stroke-opacity:.8;stroke-width:3px;stroke-linejoin:round}
.dms-map .lbl.tl{fill:#9682af;text-anchor:start}
.dms-map .lbl.tl.monster{fill:#ff553c}
.dms-map .lbl.tl.item{fill:#50c8ff}
.dms-map .lbl.il{fill:#ff3c3c;text-anchor:start;font-weight:600}
"""


def _n(v: float) -> str:
    s = f"{v:.3f}".rstrip("0").rstrip(".")
    return "0" if s in ("", "-0") else s


def _hex(c) -> str:
    return "#%02x%02x%02x" % tuple(c[:3])


def _path(polys) -> str:
    return "".join("M" + "L".join(f"{_n(x)} {_n(-y)}" for x, y in poly) + "Z" for poly in polys if len(poly) >= 3)


def _marks(prev: Textmap, cur: Textmap, changes: dict, side: str, thing_r: float, u: float) -> tuple[list, list]:
    """The diff's marks, as render._mark_changes draws them: (fills under the lines, strokes over them)."""
    before, after = side in ("both", "before"), side in ("both", "after")
    matches = R.match_sectors(prev, cur)
    loops = {id(prev): R.sector_loops(prev), id(cur): R.sector_loops(cur)}
    fills, tops = [], []

    def sector(tm: Textmap, idx: int, color: tuple, alpha: int) -> None:
        d = _path(loops[id(tm)].get(idx, []))
        if d:
            fills.append(f'<path class="mf" d="{d}" fill-rule="evenodd" fill="{_hex(color)}" '
                         f'fill-opacity="{alpha / 255:.2f}" stroke="{_hex(color)}"/>')

    for _k, idx, fields in changes["changed_sectors"]:
        if fields == ["new sector"]:
            if after:
                sector(cur, idx, R.ADDED, 70)
        elif side == "before":
            if matches[idx] is not None:
                sector(prev, matches[idx], R.CHANGED, 40)
        else:
            sector(cur, idx, R.CHANGED, 40)
    if before:
        matched = set(m for m in matches if m is not None)
        for i in range(len(prev.sectors)):
            if i not in matched:
                sector(prev, i, R.REMOVED, 70 if side == "before" else 55)

    for key, color, shown in (("removed_lines", R.REMOVED, before), ("added_lines", R.ADDED, after),
                              ("changed_lines", R.CHANGED, True)):
        if not shown:
            continue
        for a, *rest in changes[key]:
            b = rest[0] if rest else a
            tops.append(f'<line class="ml" x1="{_n(a[0])}" y1="{_n(-a[1])}" x2="{_n(b[0])}" y2="{_n(-b[1])}" '
                        f'stroke="{_hex(color)}"/>')

    def ring(t, color: tuple) -> tuple[float, float]:
        x, y = t.get("x", 0), t.get("y", 0)
        tops.append(f'<circle class="ring" cx="{_n(x)}" cy="{_n(-y)}" r="{_n(thing_r + 3 * u)}" data-pad="3" '
                    f'stroke="{_hex(color)}"/>')
        return x, y

    if after:
        for _k, t in changes["added_things"]:
            ring(t, R.ADDED)
    if before:
        for _k, t in changes["removed_things"]:
            ring(t, R.REMOVED)
    for _k, old, new in changes["moved_things"]:
        if side == "before":
            ring(old, R.CHANGED)
        elif side == "after":
            ring(new, R.CHANGED)
        else:
            a, b = ring(old, R.REMOVED), ring(new, R.CHANGED)
            tops.append(f'<line class="ml" x1="{_n(a[0])}" y1="{_n(-a[1])}" x2="{_n(b[0])}" y2="{_n(-b[1])}" '
                        f'stroke="{_hex(R.CHANGED)}" style="stroke-width:2px"/>')
    return fills, tops


def scene(view: R.View, tm: Textmap, *, issues=(), unreachable=(), softlocks=(), marks=None) -> str:
    """The map as an SVG document. `marks`: (prev, cur, changes, side) to mark a diff on it, where `tm`
    is the map drawn (prev for side "before", else cur)."""
    u = 1 / view.scale                       # map units per pixel at the PNG's scale
    w, h = view.maxx - view.minx, view.maxy - view.miny
    thing_r = max(16.0, 4 * u)
    o: list[str] = []
    o.append(f'<svg xmlns="http://www.w3.org/2000/svg" class="dms-map" viewBox="{_n(view.minx)} {_n(-view.maxy)} '
             f'{_n(w)} {_n(h)}" data-u="{_n(u)}" style="--fs:{_n(12 * u)}px;--fsg:{_n(11 * u)}px">')
    o.append(f"<style>{_STYLE}</style>")
    o.append(f'<defs><pattern id="dms-hatch" width="{_n(14 * u)}" height="{_n(14 * u)}" patternUnits="userSpaceOnUse" '
             f'patternTransform="rotate(-45)"><line x1="0" y1="0" x2="{_n(14 * u)}" y2="0" stroke="#ff3c3c" '
             f'stroke-opacity=".6" stroke-width="2"/></pattern></defs>')

    # Grid: lines well past the map, so there's grid wherever the mapper pans.
    pad = max(w, h)
    gx0, gx1, gy0, gy1 = view.minx - pad, view.maxx + pad, view.miny - pad, view.maxy + pad
    fine = 64
    major = 512 if view.scale * 512 >= 60 else 1024
    o.append('<g class="grid">')
    if (gx1 - gx0 + gy1 - gy0) / fine <= 800:
        for x in range(math.floor(gx0 / fine) * fine, int(gx1) + 1, fine):
            if x % major:
                o.append(f'<line class="gf" x1="{x}" y1="{_n(-gy0)}" x2="{x}" y2="{_n(-gy1)}"/>')
        for y in range(math.floor(gy0 / fine) * fine, int(gy1) + 1, fine):
            if y % major:
                o.append(f'<line class="gf" x1="{_n(gx0)}" y1="{-y}" x2="{_n(gx1)}" y2="{-y}"/>')
    for x in range(math.floor(gx0 / major) * major, int(gx1) + 1, major):
        o.append(f'<line class="gm" x1="{x}" y1="{_n(-gy0)}" x2="{x}" y2="{_n(-gy1)}"/>')
        o.append(f'<text class="gl" data-gx="{x}" x="{_n(x + 2 * u)}" y="{_n(-view.maxy + 12 * u)}">{x}</text>')
    for y in range(math.floor(gy0 / major) * major, int(gy1) + 1, major):
        o.append(f'<line class="gm" x1="{_n(gx0)}" y1="{-y}" x2="{_n(gx1)}" y2="{-y}"/>')
        o.append(f'<text class="gl" data-gy="{y}" x="{_n(view.minx + 2 * u)}" y="{_n(-y - 3 * u)}">{y}</text>')
    o.append("</g>")

    sectors = tm.sectors
    loops = R.sector_loops(tm)
    heights = [s.get("heightfloor", 0) for s in sectors] or [0]
    lo, hi = min(heights), max(heights)
    labels: list[str] = []
    o.append('<g class="sectors">')
    # Larger sectors first, so sectors inside other sectors are drawn (and hovered) on top.
    for sec in sorted(loops, key=lambda s: -max((R.polygon_area(p) for p in loops[s]), default=0)):
        if not (0 <= sec < len(sectors)) or not loops[sec]:
            continue
        s = sectors[sec]
        gid = s.get("user_gid")
        d = _path(loops[sec])
        if not d:
            continue
        tip = (f"sector {sec}" + (f" {gid}" if gid else "") + f": floor {s.get('heightfloor', 0)}, ceiling "
               f"{s.get('heightceiling', 0)}, light {s.get('lightlevel', 160)}, {s.get('texturefloor')} / "
               f"{s.get('textureceiling')}" + (f", tag {s.get('id')}" if s.get("id") else ""))
        o.append(f'<path class="sec" d="{d}" fill-rule="evenodd" '
                 f'fill="{_hex(R._floor_shade(s.get("heightfloor", 0), lo, hi))}"><title>{escape(tip)}</title></path>')
        biggest = max(loops[sec], key=R.polygon_area)
        cx, cy = R.centroid(biggest)
        labels.append(f'<text class="lbl" x="{_n(cx)}" y="{_n(-cy)}" data-p="{_n(R.polygon_area(biggest))}">'
                      f'{escape(f"{sec}" + (f" {gid}" if gid else ""))}</text>')
    o.append("</g>")

    o.append('<g class="ov">')
    for sec in softlocks:
        d = _path(loops.get(sec, []))
        if d:
            o.append(f'<path class="soft" fill-rule="evenodd" d="{d}"/>')
    for sec in unreachable:
        d = _path(loops.get(sec, []))
        if d:
            o.append(f'<path class="unreach" fill-rule="evenodd" d="{d}"/>')
    o.append("</g>")

    fills, tops = _marks(*marks, thing_r, u) if marks else ([], [])
    o.append('<g class="marks-fill">' + "".join(fills) + "</g>")

    o.append('<g class="lines">')
    special: list[str] = []
    for i, ld in enumerate(tm.linedefs):
        pts = R._line_points(tm, ld)
        if not pts:
            continue
        (x1, y1), (x2, y2) = pts
        xy = f'x1="{_n(x1)}" y1="{_n(-y1)}" x2="{_n(x2)}" y2="{_n(-y2)}"'
        if ld.get("special", 0):
            args = ", ".join(str(ld.get(f"arg{k}", 0)) for k in range(5))
            gid = ld.get("user_gid")
            tip = f"line {i}" + (f" {gid}" if gid else "") + f": special {ld['special']}({args})"
            special.append(f'<line class="s" {xy}><title>{escape(tip)}</title></line>')
        else:
            o.append(f'<line class="{"t" if ld.get("sideback", -1) not in (-1, None) else "w"}" {xy}/>')
    o.extend(special)   # on top, so they can be pointed at
    o.append("</g>")
    o.append('<g class="marks">' + "".join(tops) + "</g>")

    o.append('<g class="things">')
    k = thing_r / 16
    for i, t in enumerate(tm.things):
        if "x" not in t.fields:
            continue
        x, y = t["x"], t.get("y", 0)
        kind, name = R.thing_kind(t.get("type"))
        is_player = kind == "player"
        ang = math.radians(t.get("angle", 0))
        gid = t.get("user_gid")
        tip = (f"thing {i}" + (f" {gid}" if gid else "") + f": {name or kind} (type {t.get('type')}) at ({x:g}, {y:g}), "
               f"angle {t.get('angle', 0)}")
        # As in the PNG: monsters and player starts a circle with an arrow, items a diamond, the rest a
        # smaller circle.
        if kind == "item":
            shape = '<path d="M0 -16L16 0L0 16L-16 0Z"/>'
        elif kind == "other":
            shape = '<circle r="9.6"/>'
        else:
            shape = f'<circle r="16"/><line x2="{_n(math.cos(ang) * 28.8)}" y2="{_n(-math.sin(ang) * 28.8)}"/>'
        o.append(f'<g class="thing {kind}" transform="translate({_n(x)} {_n(-y)})">'
                 f'<g class="k" transform="scale({_n(k)})">{shape}</g>'
                 f"<title>{escape(tip)}</title></g>")
        if not is_player:
            labels.append(f'<text class="lbl tl {kind}" data-x="{_n(x)}" x="{_n(x + thing_r + 3 * u)}" y="{_n(-y)}">'
                          f'{escape(str(t.get("type")))}</text>')
    o.append("</g>")

    o.append('<g class="issues">')
    at_same_spot: dict[tuple, int] = {}
    for n, issue in enumerate([i for i in issues if i.pos], 1):
        x, y = issue.pos
        j = at_same_spot.get(issue.pos, 0)   # several issues at one spot: bigger rings, labels stacked
        at_same_spot[issue.pos] = j + 1
        r0 = max(28.0, 10 * u)
        o.append(f'<circle class="issue" cx="{_n(x)}" cy="{_n(-y)}" r="{_n(r0 + 7 * j * u)}" data-k="{j}">'
                 f"<title>{escape(str(issue))}</title></circle>")
        labels.append(f'<text class="lbl il" data-x="{_n(x)}" data-y="{_n(-y)}" data-k="{j}" x="{_n(x + r0 + 8 * u)}" '
                      f'y="{_n(-y - r0 + 17 * j * u)}">#{n}</text>')
    o.append("</g>")
    o.append('<g class="labels">' + "".join(labels) + "</g>")
    o.append("</svg>")
    return "\n".join(o) + "\n"


def write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
    return path
