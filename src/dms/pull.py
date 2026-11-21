"""dms pull: bring the mapper's saved editor edits (build/<map>/edit.wad) back into the map's source.

The edits are what changed between the TEXTMAP edit.wad was packed from (builds are blocked while
edit.wad has saved edits, so TEXTMAP is still that base) and the editor's save. Elements are matched
by `user_gid`; the editor copies a gid on split, copy/paste and sector division (PLAN.md section 9),
so a gid seen more than once is a structural change, as is anything without a gid.

- Property tweaks (light, heights, textures, offsets, flags, a thing's position/angle/type) on
  elements whose gid appears once: written to maps/<map>/overrides.toml (generated maps).
- Structural changes (moved vertices, new/removed/split/copied lines, sectors, things): listed for
  Claude to port into map.py; nothing is written until `--ported`.
- Editor comments (the UDMF `comment` field): appended to the map's notes.md as requests, with the
  element's gid and position; the rebuild drops them from the map.

Then the map is rebuilt (edit.wad refreshed, so an open editor reloads) and the result is compared with
the save again. The save is kept in build/<map>/pulled/. Hand-edited maps: the save becomes TEXTMAP.
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from dms import build as b
from dms import overrides, udmf
from dms.maps import MapInfo

# UDMF defaults (zdoom namespace) for fields the editor leaves out when they hold the default.
# Any boolean flag defaults to false; args to 0.
DEFAULTS = {
    "thing": {"angle": 0, "height": 0, "special": 0, "id": 0},
    "linedef": {"special": 0, "id": -1, "sideback": -1},
    "sidedef": {"offsetx": 0, "offsety": 0, "texturetop": "-", "texturebottom": "-", "texturemiddle": "-"},
    "sector": {"heightfloor": 0, "heightceiling": 0, "lightlevel": 160, "special": 0, "id": 0},
}
ARGS = {f"arg{i}" for i in range(5)}
# Fields that tie an element to others (by index); compared through what they point at instead.
STRUCTURAL = {"linedef": {"v1", "v2", "sidefront", "sideback"}, "sidedef": {"sector"}}
IGNORED = {"user_gid", "comment"}
KINDS = ("thing", "linedef", "sidedef", "sector")


class PullError(Exception):
    pass


def default_for(kind: str, name: str, sample=None):
    if name in DEFAULTS.get(kind, {}):
        return DEFAULTS[kind][name]
    if name in ARGS:
        return 0
    if isinstance(sample, bool):
        return False
    return None


def props(block: udmf.Block) -> dict:
    """The element's own properties, without defaults, links, gid and comment."""
    skip = STRUCTURAL.get(block.kind, set()) | IGNORED
    return {k: v for k, v in block.fields.items()
            if k not in skip and v != default_for(block.kind, k, v)}


@dataclass
class Changes:
    tweaks: dict[tuple[str, str], dict] = field(default_factory=dict)   # (kind, gid) -> {field: new value}
    tweak_lines: list[str] = field(default_factory=list)
    structural: list[str] = field(default_factory=list)
    requests: list[str] = field(default_factory=list)                  # editor comments

    @property
    def empty(self) -> bool:
        return not (self.tweaks or self.structural or self.requests)


def _pt(p) -> str:
    return f"({p[0]:g}, {p[1]:g})"


class _Geo:
    """Positions of elements, for reports."""

    def __init__(self, tm: udmf.Textmap) -> None:
        from dms import render

        self.tm = tm
        self.verts = tm.vertices
        self.loops = render.sector_loops(tm)
        self.centroid = render.centroid
        self.area = render.polygon_area
        self.side_line = {}
        for i, ld in enumerate(tm.linedefs):
            for k in ("sidefront", "sideback"):
                s = ld.get(k, -1)
                if isinstance(s, int) and s >= 0:
                    self.side_line[s] = i

    def ends(self, ld: udmf.Block):
        try:
            a, c = self.verts[ld["v1"]], self.verts[ld["v2"]]
            return (a["x"], a["y"]), (c["x"], c["y"])
        except (KeyError, IndexError, TypeError):
            return None

    def where(self, kind: str, idx: int) -> str:
        if kind == "thing":
            t = self.tm.things[idx]
            return f"at {_pt((t.get('x', 0), t.get('y', 0)))}"
        if kind == "linedef":
            e = self.ends(self.tm.linedefs[idx])
            return f"{_pt(e[0])}-{_pt(e[1])}" if e else ""
        if kind == "sidedef":
            line = self.side_line.get(idx)
            return f"on line {self.where('linedef', line)}" if line is not None else ""
        if kind == "sector":
            polys = self.loops.get(idx, [])
            return f"around {_pt(self.centroid(max(polys, key=self.area)))}" if polys else ""
        return ""


def _same_place(ga: "_Geo", a: udmf.Block, gb: "_Geo", b: udmf.Block) -> bool:
    if a.kind == "thing":
        return (a.get("x"), a.get("y"), a.get("type")) == (b.get("x"), b.get("y"), b.get("type"))
    if a.kind == "linedef":
        ea = ga.ends(a)
        return ea is not None and ea == gb.ends(b)
    return False


def _gid_of(tm: udmf.Textmap, kind: str, idx) -> str | None:
    blocks = tm.of(kind)
    if isinstance(idx, int) and 0 <= idx < len(blocks):
        return blocks[idx].get("user_gid") or f"#{idx} (no gid)"
    return None


def compare(base: udmf.Textmap, edited: udmf.Textmap) -> Changes:
    """What the mapper changed between `base` (what edit.wad was packed from) and `edited`."""
    ch = Changes()
    gb, ge = _Geo(base), _Geo(edited)
    alias: dict[tuple[str, int], str] = {}  # edited elements without a gid, matched by position -> base gid

    def ed_gid(kind: str, idx) -> str | None:
        return alias.get((kind, idx)) or _gid_of(edited, kind, idx)

    for kind in KINDS:
        base_blocks, ed_blocks = base.of(kind), edited.of(kind)
        by_gid: dict[str, list[int]] = {}
        for i, blk in enumerate(ed_blocks):
            by_gid.setdefault(blk.get("user_gid"), []).append(i)
        base_gids = set()
        for bi, old in enumerate(base_blocks):
            gid = old.get("user_gid")
            if not gid:
                continue  # dms gives every element a gid; nothing to match by
            base_gids.add(gid)
            found = by_gid.get(gid, [])
            if not found:
                # Fall back to position: an element without a gid exactly where this one was is the
                # same element (e.g. a thing the mapper added, since ported into map.py with a gid).
                # A line matched that way brings its sides along.
                same = next((i for (k, i), g in alias.items() if k == kind and g == gid), None)
                if same is None:
                    same = next((i for i in by_gid.get(None, []) if _same_place(gb, old, ge, ed_blocks[i])), None)
                if same is None:
                    ch.structural.append(f"removed {kind} {gid} {gb.where(kind, bi)}".rstrip())
                    continue
                if same in by_gid.get(None, []):
                    by_gid[None].remove(same)
                alias[(kind, same)] = gid
                if kind == "linedef":
                    for side in ("sidefront", "sideback"):
                        bs, es = old.get(side, -1), ed_blocks[same].get(side, -1)
                        if (isinstance(bs, int) and 0 <= bs < len(base.sidedefs) and isinstance(es, int)
                                and 0 <= es < len(edited.sidedefs) and not edited.sidedefs[es].get("user_gid")
                                and base.sidedefs[bs].get("user_gid")):
                            alias[("sidedef", es)] = base.sidedefs[bs]["user_gid"]
                found = [same]
            if len(found) > 1:
                ch.structural.append(f"{kind} {gid} is now {len(found)} {kind}s (split or copied in the editor): "
                                     + "; ".join(ge.where(kind, i) for i in found))
                continue
            ei = found[0]
            new = ed_blocks[ei]
            # Links: a line's ends and sides, a side's sector.
            if kind == "linedef":
                oe, ne = gb.ends(old), ge.ends(new)
                if oe != ne:
                    ch.structural.append(f"line {gid} moved: {_pt(oe[0])}-{_pt(oe[1])} -> {_pt(ne[0])}-{_pt(ne[1])}"
                                         if oe and ne else f"line {gid}: ends changed")
                for side in ("sidefront", "sideback"):
                    was, now = _gid_of(base, "sidedef", old.get(side, -1)), ed_gid("sidedef", new.get(side, -1))
                    if was != now:
                        ch.structural.append(f"line {gid}: {side} {was or 'none'} -> {now or 'none'}")
            if kind == "sidedef":
                was, now = _gid_of(base, "sector", old.get("sector")), ed_gid("sector", new.get("sector"))
                if was != now:
                    ch.structural.append(f"side {gid}: sector {was} -> {now}")
            # Properties.
            po, pn = props(old), props(new)
            diff = {}
            for name in sorted(set(po) | set(pn)):
                if po.get(name) == pn.get(name):
                    continue
                value = pn[name] if name in pn else default_for(kind, name, po[name])
                if value is None:
                    ch.structural.append(f"{kind} {gid}: field {name} removed (no known default)")
                    continue
                diff[name] = value
                ch.tweak_lines.append(f"{kind} {gid}: {name} {_fmt(po.get(name, default_for(kind, name, value)))}"
                                      f" -> {_fmt(value)}")
            if diff:
                ch.tweaks[(kind, gid)] = diff
        for gid, idxs in by_gid.items():
            if gid and gid not in base_gids:
                ch.structural.append(f"{kind} with gid {gid} that the generated map doesn't have: "
                                     + "; ".join(ge.where(kind, i) for i in idxs))
        for i in by_gid.get(None, []):
            if kind == "sidedef":
                continue  # belongs to a new line, reported with it
            blk = ed_blocks[i]
            what = f"type {blk.get('type')} " if kind == "thing" else ""
            ch.structural.append(f"new {kind} {what}{ge.where(kind, i)}".rstrip())
    for kind in KINDS:
        for i, blk in enumerate(edited.of(kind)):
            text = blk.get("comment")
            if isinstance(text, str) and text.strip():
                gid = blk.get("user_gid") or f"new {kind} #{i}"
                ch.requests.append(f"{kind} {gid} {ge.where(kind, i)}: {text.strip()}".replace("  ", " "))
    return ch


def _fmt(v) -> str:
    return "unset" if v is None else repr(v) if isinstance(v, str) else str(v)


def strip_comments(tm: udmf.Textmap) -> None:
    for blk in tm.blocks:
        blk.fields.pop("comment", None)


def report_text(info: MapInfo, ch: Changes, title: str) -> str:
    lines = [title, ""]
    lines.append(f"property tweaks ({len(ch.tweak_lines)}) -> maps/{info.name}/{overrides.FILENAME}")
    lines += [f"  {t}" for t in ch.tweak_lines] or ["  none"]
    lines.append(f"structural changes ({len(ch.structural)}) -> to port into map.py")
    lines += [f"  {s}" for s in ch.structural] or ["  none"]
    lines.append(f"editor comments ({len(ch.requests)}) -> maps/{info.name}/notes.md")
    lines += [f"  {r}" for r in ch.requests] or ["  none"]
    return "\n".join(lines) + "\n"


def _append_requests(info: MapInfo, requests: list[str]) -> None:
    notes = info.folder / "notes.md"
    text = notes.read_text(encoding="utf-8") if notes.exists() else f"# {info.title}\n\n## Feedback log\n"
    if not text.endswith("\n"):
        text += "\n"
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    text += f"\n### {stamp}: editor comments (dms pull)\n\n" + "".join(f"- [ ] {r}\n" for r in requests)
    notes.write_text(text, encoding="utf-8", newline="\n")


@dataclass
class Outcome:
    status: str                      # "nothing" | "waiting" (structural changes to port) | "pulled"
    changes: Changes | None = None
    matches: bool = True             # after "pulled": the rebuilt map matches the save
    errors: int = 0                  # after "pulled": validation errors in the rebuild

    @property
    def code(self) -> int:
        return 1 if self.status == "waiting" or self.errors else 0


def pull(info: MapInfo, root: Path, ported: bool = False) -> int:
    return run(info, root, ported).code


def run(info: MapInfo, root: Path, ported: bool = False) -> Outcome:
    """`dms pull`, returning what happened. Raises PullError when it can't start."""
    print(f"dms pull: {info.name} ({info.source})")
    ew = info.edit_wad(root)
    if not ew.exists():
        raise PullError(f"{ew} doesn't exist; there's nothing to pull (open the map with Edit Map first)")
    state = b.editor_state(info, root)
    if state.get("open") and state.get("unsaved_changes"):
        raise PullError("the editor has unsaved changes. Save them first (only saved edits are pulled), "
                        "or undo them, then pull again.")
    if not b.edit_wad_changed(info, root):
        print("    nothing to pull: edit.wad has no saved changes")
        return Outcome("nothing")
    if info.source == "generated" and b.hand_edited_since_generated(info.textmap.read_text(encoding="utf-8")):
        raise PullError(f"{info.textmap} was edited by hand since it was generated; sort that out first "
                        "(see `dms build`)")

    base = udmf.parse(info.textmap.read_text(encoding="utf-8"))
    edited = b.read_edit_wad_textmap(info, root)
    ch = compare(base, edited)
    out_dir = info.build_dir(root)
    title = f"{info.name}: editor changes in edit.wad (saved {datetime.fromtimestamp(ew.stat().st_mtime):%Y-%m-%d %H:%M})"
    report = report_text(info, ch, title)
    (out_dir / "pull.txt").write_text(report, encoding="utf-8", newline="\n")
    print("    " + report.rstrip().replace("\n", "\n    "))
    # Picture of the save against TEXTMAP, for Claude (render-edit.png, diff-edit.png).
    b.draw(info, root, edited, [], base, suffix="-edit", diff_title=f"{info.name}: editor changes")

    if info.source == "generated" and ch.structural and not ported:
        print(f"\n    Nothing written yet. These structural changes have to go into map.py first: ask Claude.\n"
              f"    (Claude: port them, then run `dms pull {info.name} --ported`.)")
        return Outcome("waiting", ch)

    # Keep the save, whatever happens next.
    keep = out_dir / "pulled"
    keep.mkdir(parents=True, exist_ok=True)
    saved = keep / f"edit-{datetime.now():%Y%m%d-%H%M%S}.wad"
    shutil.copy2(ew, saved)
    print(f"    kept the save as {saved}")

    if ch.requests:
        _append_requests(info, ch.requests)
        print(f"    added {len(ch.requests)} editor comment(s) to {info.folder / 'notes.md'}")

    if info.source == "generated":
        if ch.tweaks:
            overrides.save(info, overrides.merge(overrides.load(info), ch.tweaks))
            print(f"    wrote {overrides.path(info)}")
    else:
        strip_comments(edited)
        info.textmap.write_text(udmf.dump(edited), encoding="utf-8", newline="\n")
        print(f"    wrote {info.textmap} from the save")

    parts = [f"{len(ch.tweaks)} tweaked element(s)" if ch.tweaks else "",
             f"{len(ch.structural)} structural change(s) ported" if ch.structural else "",
             f"{len(ch.requests)} comment(s) to notes.md" if ch.requests else ""]
    note = "Pulled the mapper's editor changes: " + (", ".join(p for p in parts if p) or "nothing to keep") + "."
    print()
    result = b.build(info, root, force=True, note=note)

    # Check: the rebuilt map against the save (comments aside).
    strip_comments(edited)
    rebuilt = udmf.parse(info.textmap.read_text(encoding="utf-8"))
    left = compare(rebuilt, edited)
    if left.empty:
        print("    check: the rebuilt map matches the editor save")
    else:
        print("    check: the rebuilt map still differs from the editor save in:")
        for line in left.tweak_lines + left.structural:
            print(f"      {line}")
        if ported:
            print("    (expected only where map.py now differs from the save on purpose)")
    return Outcome("pulled", ch, matches=left.empty, errors=result.errors)
