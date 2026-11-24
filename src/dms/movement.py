"""Movement check: where can the player get to from the player 1 start? (PLAN.md section 6, item 5)

Works on sectors. Crossing a two-sided, non-blocking line from sector A to sector B needs:
- a step up of at most STEP (24) units; any drop is allowed (one-way drops are listed);
- at least HEIGHT (56) units between the higher floor and the lower ceiling;
- a gap at least WIDTH (32) units wide (collinear lines between the same two sectors, end to end,
  count as one gap).

Things that move: doors (specials 11-13, tag 0 = the sector behind the line) open to the lowest
neighbouring ceiling minus 4; locked doors (13) need their key. Lifts and floor movers can be at any
height between their own floor and their neighbours'; ceiling movers likewise. A special counts once
the player can reach its line (switches and shootables from the front side, walk-over lines from
either side). Repeats until nothing new opens up.

It is optimistic on purpose (movers are assumed to reach any height in their range): "unreachable" is
reliable, "reachable" means "probably". Not handled yet: teleporters, crushers, scripts,
jumping/crouching (off in this project anyway).

Monster fit (docs/map-design-notes.md: monsters need pathing): each monster is flooded the same way with
its own size (MONSTERS: a gap at least twice its radius, headroom its height), a step of 24 up and, unless
it flies, no drop of more than 24 (Doom monsters won't walk off a higher ledge). Movers that stay
where they're moved (floors, ceilings, Door_Open: once the player has used them) count as for the player;
doors and lifts that close or come back, only if a line that works them has a monster activation flag.
Wherever the player can go back and forth between a place the monster can reach and one it can't, the
monster can't follow there: a warning names the line and why. Not reported: a dead end too small for the
monster to stand in (an altar's top, a niche). Also optimistic: a corridor wide enough at every line can
still be too tight at a bend
(Doom's monsters move in 8 directions); give winding corridors about twice the monster's width.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from dms.udmf import Block, Textmap
from dms.validate import Issue, sector_at

STEP = 24
HEIGHT = 56
WIDTH = 32

DOORS = {11, 12, 13}                     # Door_Open, Door_Raise, Door_LockedRaise
LOCKED_DOOR = 13                          # its lock number is arg3
DOOR_OPEN = 11                            # opens and stays open
LIFTS = {60, 61, 62, 63, 64, 65, 206, 207}  # Plat_*
FLOORS = set(range(20, 39))              # Floor_* and stairs (raise/lower/move)
FLOOR_LOWER_BY_VALUE, FLOOR_RAISE_BY_VALUE = 20, 23   # move by arg2, not to a neighbour's height
CEILINGS = {40, 41, 42, 43, 44, 45, 69, 97, 104, 168, 169}
EXITS = {74: "exit (to a map)", 75: "exit (to a map)", 243: "exit", 244: "secret exit"}
BLOCKING_FLAGS = ("blocking", "blockplayers", "blockeverything")

KEYS = {5: "blue keycard", 6: "yellow keycard", 13: "red keycard",
        38: "red skull key", 39: "yellow skull key", 40: "blue skull key"}
# ZDoom lock numbers -> any one of these key types opens it.
LOCKS = {1: {13}, 2: {5}, 3: {6}, 4: {38}, 5: {40}, 6: {39},
         129: {13, 38}, 130: {5, 40}, 131: {6, 39}}
ALL_KEYS = {100, 101, 229}                # "all keys" locks: one of each colour
WEAPONS = {2001: "shotgun", 82: "super shotgun", 2002: "chaingun", 2003: "rocket launcher",
           2004: "plasma rifle", 2005: "chainsaw", 2006: "BFG9000"}
# Other pickups worth reporting when they can't be reached (not every health bonus or clip).
# Monster type -> (name, radius, height, flies): Doom's, as UZDoom defines them.
MONSTERS = {
    3004: ("zombieman", 20, 56, False), 9: ("shotgun guy", 20, 56, False), 65: ("chaingunner", 20, 56, False),
    84: ("wolfenstein SS", 20, 56, False), 3001: ("imp", 20, 56, False), 3002: ("pinky", 30, 56, False),
    58: ("spectre", 30, 56, False), 3006: ("lost soul", 16, 56, True), 3005: ("cacodemon", 31, 56, True),
    71: ("pain elemental", 31, 56, True), 66: ("revenant", 20, 56, False), 69: ("hell knight", 24, 64, False),
    3003: ("baron of hell", 24, 64, False), 67: ("mancubus", 48, 64, False), 68: ("arachnotron", 64, 64, False),
    64: ("arch-vile", 20, 56, False), 16: ("cyberdemon", 40, 110, False), 7: ("spider mastermind", 128, 100, False),
}
MONSTER_DROP = 24
MONSTER_FLAGS = ("monsteruse", "monstercross", "monsterpush", "monstershoot")
ITEMS = {2013: "soulsphere", 83: "megasphere", 2022: "invulnerability", 2023: "berserk",
         2024: "partial invisibility", 2025: "radiation suit", 2026: "computer map", 2045: "light amp goggles",
         2018: "green armor", 2019: "blue armor", 8: "backpack"}


@dataclass
class Range:
    lo: float
    hi: float

    def widen(self, lo: float, hi: float) -> bool:
        new = Range(min(self.lo, lo), max(self.hi, hi))
        changed = (new.lo, new.hi) != (self.lo, self.hi)
        self.lo, self.hi = new.lo, new.hi
        return changed


@dataclass
class Result:
    start: int | None
    reachable: set[int] = field(default_factory=set)
    unreachable: set[int] = field(default_factory=set)
    softlocks: set[int] = field(default_factory=set)
    issues: list[Issue] = field(default_factory=list)
    report: str = ""


def _length(tm: Textmap, ld: Block) -> float:
    v = tm.vertices
    try:
        a, b = v[ld["v1"]], v[ld["v2"]]
    except (KeyError, IndexError, TypeError):
        return 0.0
    return math.hypot(b["x"] - a["x"], b["y"] - a["y"])


def _mid(tm: Textmap, ld: Block) -> tuple[float, float] | None:
    v = tm.vertices
    try:
        a, b = v[ld["v1"]], v[ld["v2"]]
    except (KeyError, IndexError, TypeError):
        return None
    return ((a["x"] + b["x"]) / 2, (a["y"] + b["y"]) / 2)


def _side_sector(tm: Textmap, ld: Block, key: str) -> int | None:
    s = ld.get(key, -1)
    if isinstance(s, int) and 0 <= s < len(tm.sidedefs):
        sec = tm.sidedefs[s].get("sector")
        if isinstance(sec, int) and 0 <= sec < len(tm.sectors):
            return sec
    return None


def _tags(sector: Block) -> set[int]:
    out = set()
    if isinstance(sector.get("id"), int) and sector.get("id"):
        out.add(sector["id"])
    more = sector.get("moreids")
    if isinstance(more, str):
        out |= {int(t) for t in more.split() if t.lstrip("-").isdigit()}
    return out


def _gap_widths(tm: Textmap, lines: list[int]) -> dict[int, float]:
    """For each line between one pair of sectors: the width of the opening it belongs to (lines that
    are collinear and joined end to end count together)."""
    parent = {i: i for i in lines}

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    verts = tm.vertices
    by_vertex: dict[int, list[int]] = {}
    for i in lines:
        for k in ("v1", "v2"):
            by_vertex.setdefault(tm.linedefs[i].get(k), []).append(i)

    def direction(i):
        ld = tm.linedefs[i]
        a, b = verts[ld["v1"]], verts[ld["v2"]]
        return b["x"] - a["x"], b["y"] - a["y"]

    for shared in by_vertex.values():
        for x in range(len(shared)):
            for y in range(x + 1, len(shared)):
                (ax, ay), (bx, by) = direction(shared[x]), direction(shared[y])
                if abs(ax * by - ay * bx) <= 1e-6 * max(1.0, math.hypot(ax, ay) * math.hypot(bx, by)):
                    parent[find(shared[x])] = find(shared[y])
    total: dict[int, float] = {}
    for i in lines:
        total[find(i)] = total.get(find(i), 0.0) + _length(tm, tm.linedefs[i])
    return {i: total[find(i)] for i in lines}


def check(tm: Textmap) -> Result:
    sectors, lines = tm.sectors, tm.linedefs
    player = next((t for t in tm.things if t.get("type") == 1 and "x" in t.fields), None)
    start = sector_at(tm, player["x"], player["y"]) if player else None
    res = Result(start)
    if start is None:
        res.report = "movement: no player 1 start inside a sector; nothing checked\n"
        return res

    floor = [Range(s.get("heightfloor", 0), s.get("heightfloor", 0)) for s in sectors]
    ceil = [Range(s.get("heightceiling", 0), s.get("heightceiling", 0)) for s in sectors]

    # Two-sided lines: (line index, front sector, back sector), and openings' widths.
    portals = []
    pairs: dict[frozenset, list[int]] = {}
    neighbours: dict[int, set[int]] = {i: set() for i in range(len(sectors))}
    for i, ld in enumerate(lines):
        f, b = _side_sector(tm, ld, "sidefront"), _side_sector(tm, ld, "sideback")
        if f is None or b is None or f == b:
            continue
        neighbours[f].add(b)
        neighbours[b].add(f)
        if any(ld.get(flag) for flag in BLOCKING_FLAGS):
            continue
        portals.append((i, f, b))
        pairs.setdefault(frozenset((f, b)), []).append(i)
    width = {}
    for group in pairs.values():
        width.update(_gap_widths(tm, group))

    def can_move(a: int, b: int, line: int) -> bool:
        if width.get(line, 0) < WIDTH:
            return False
        for fa in {floor[a].lo, floor[a].hi}:
            if ceil[a].hi - fa < HEIGHT:
                continue  # can't stand in A at that height
            for fb in {floor[b].lo, floor[b].hi}:
                if fb - fa <= STEP and min(ceil[a].hi, ceil[b].hi) - max(fa, fb) >= HEIGHT \
                        and ceil[b].hi - fb >= HEIGHT:
                    return True
        return False

    def flood() -> set[int]:
        seen, todo = {start}, [start]
        while todo:
            a = todo.pop()
            for line, f, b in portals:
                for x, y in ((f, b), (b, f)):
                    if x == a and y not in seen and can_move(x, y, line):
                        seen.add(y)
                        todo.append(y)
        return seen

    def things_in(secs: set[int]) -> set[int]:
        return {t.get("type") for t in tm.things if "x" in t.fields and sector_at(tm, t["x"], t["y"]) in secs}

    def targets(ld: Block, front: int | None, back: int | None) -> list[int]:
        tag = ld.get("arg0", 0)
        if not tag:
            return [back] if back is not None else []
        return [i for i, s in enumerate(sectors) if tag in _tags(s)]

    def usable(ld: Block, front: int | None, back: int | None, reach: set[int]) -> bool:
        if ld.get("playercross") and not (ld.get("playeruse") or ld.get("impact") or ld.get("playerpush")):
            return (front in reach) or (back in reach)
        # A switch at the back of a niche the player can't step into (too low, too shallow) is used
        # from the sector in front of the niche: count it when the front sector, or a neighbour, is
        # reachable (optimistic: the neighbour may be out of use range).
        if front in reach or (front is not None and bool(neighbours[front] & reach)):
            return True
        # One more thin sector between (a shutter in front of the switch, itself at the back of a niche):
        # still within a use's reach, as long as both are thin (cacobelisk's top switch, 2026-11-23).
        return front is not None and thin(front) and any(
            thin(n) and neighbours[n] & reach for n in neighbours[front] if n not in reach)

    thin_cache: dict[int, bool] = {}

    def thin(sec: int) -> bool:
        """No more than half a use's reach (32) across one way: a niche, a slot, a shutter."""
        if sec not in thin_cache:
            xs, ys = [], []
            for ld in lines:
                if sec in (_side_sector(tm, ld, "sidefront"), _side_sector(tm, ld, "sideback")):
                    for k in ("v1", "v2"):
                        v = tm.vertices[ld[k]]
                        xs.append(v["x"])
                        ys.append(v["y"])
            thin_cache[sec] = bool(xs) and min(max(xs) - min(xs), max(ys) - min(ys)) <= 32
        return thin_cache[sec]

    def opens(lock: int, have: set[int]) -> bool:
        if lock in ALL_KEYS:
            return all(LOCKS[n] & have for n in (129, 130, 131))
        return not lock or bool(LOCKS.get(lock, set()) & have)

    used: set[int] = set()
    never_opened: dict[int, str] = {}
    reach = flood()
    while True:
        have = things_in(reach) & set(KEYS)
        changed = False
        for i, ld in enumerate(lines):
            sp = ld.get("special", 0)
            if i in used or not sp or not (sp in DOORS or sp in LIFTS or sp in FLOORS or sp in CEILINGS):
                continue
            f, b = _side_sector(tm, ld, "sidefront"), _side_sector(tm, ld, "sideback")
            if not usable(ld, f, b, reach):
                continue
            if sp == LOCKED_DOOR and not opens(ld.get("arg3", 0), have):
                never_opened[i] = f"locked door (lock {ld.get('arg3', 0)}) whose key isn't reachable"
                continue
            used.add(i)
            never_opened.pop(i, None)
            for s in targets(ld, f, b):
                nb = neighbours[s] or {s}
                if sp in DOORS:
                    top = min(ceil[n].hi for n in nb) - 4
                    changed |= ceil[s].widen(ceil[s].lo, max(top, ceil[s].hi))
                elif sp in LIFTS or sp in FLOORS:
                    lo, hi = min(floor[n].lo for n in nb), max(floor[n].hi for n in nb)
                    # Floor_LowerByValue / Floor_RaiseByValue move by their own amount (arg2), which
                    # may go past every neighbour (a platform down a shaft).
                    if sp == FLOOR_LOWER_BY_VALUE:
                        lo = min(lo, floor[s].lo - ld.get("arg2", 0))
                    elif sp == FLOOR_RAISE_BY_VALUE:
                        hi = max(hi, floor[s].hi + ld.get("arg2", 0))
                    changed |= floor[s].widen(lo, hi)
                elif sp in CEILINGS:
                    changed |= ceil[s].widen(min(ceil[n].lo for n in nb), max(ceil[n].hi for n in nb))
        if not changed:
            break
        reach = flood()
    res.reachable = reach
    # Scenery, never moved (untagged, not behind a special's line, unlike a closed door): solid blocks
    # (no height at all), and sectors too low to stand in raised above every neighbour by more than a
    # step (the top of a monolith). They are walls, not places to reach. A too-low corridor at its
    # neighbours' level is still reported.
    moved = {b for ld in lines if ld.get("special", 0) for b in (_side_sector(tm, ld, "sideback"),)}

    def scenery(i: int) -> bool:
        if sectors[i].get("user_scenery") is True:  # marked by the map: a recess, a light channel...
            return True
        if _tags(sectors[i]) or i in moved:
            return False
        if ceil[i].hi <= floor[i].lo:
            return True
        raised = all(floor[i].lo - floor[n].hi > STEP for n in neighbours[i]) and bool(neighbours[i])
        return ceil[i].hi - floor[i].lo < HEIGHT and raised

    solid = {i for i in range(len(sectors)) if scenery(i)}
    res.unreachable = set(range(len(sectors))) - reach - solid

    # Directed moves in the final state, for one-way drops and soft-locks.
    moves: dict[int, set[int]] = {i: set() for i in range(len(sectors))}
    for line, f, b in portals:
        if can_move(f, b, line):
            moves[f].add(b)
        if can_move(b, f, line):
            moves[b].add(f)
    one_way = sorted({(a, b) for a in reach for b in moves[a] if a not in moves[b]})

    exits = [(i, ld) for i, ld in enumerate(lines) if ld.get("special", 0) in EXITS]
    exit_secs = {s for _, ld in exits for s in (_side_sector(tm, ld, "sidefront"),) if s is not None}
    if exit_secs & reach:
        back: dict[int, set[int]] = {i: set() for i in range(len(sectors))}
        for a, bs in moves.items():
            for b in bs:
                back[b].add(a)
        escape, todo = set(exit_secs), list(exit_secs)
        while todo:
            x = todo.pop()
            for y in back[x]:
                if y not in escape:
                    escape.add(y)
                    todo.append(y)
        res.softlocks = reach - escape

    res.issues, res.report = _findings(tm, res, exits, exit_secs, one_way, never_opened, things_in)
    m_issues, m_report = _monster_fit(tm, res, portals, width, floor, ceil, moves, targets)
    res.issues += m_issues
    res.report += m_report
    return res


def _monster_fit(tm, res, portals, width, floor, ceil, moves, targets):
    """The monster fit check (see the module's docstring): warnings and report lines."""
    sectors, lines = tm.sectors, tm.linedefs
    # Sectors as the player can move them, for a monster: movers that stay put once used, and doors and
    # lifts worked by a line with a monster activation flag.
    movable = set()
    for ld in lines:
        sp = ld.get("special", 0)
        if not sp or not (sp in DOORS or sp in LIFTS or sp in FLOORS or sp in CEILINGS):
            continue
        stays = sp in FLOORS or sp in CEILINGS or sp == DOOR_OPEN     # Door_Open doesn't close again
        if stays or any(ld.get(f) for f in MONSTER_FLAGS):
            movable.update(targets(ld, _side_sector(tm, ld, "sidefront"), _side_sector(tm, ld, "sideback")))
    # Each sector's size (its lines' bounding box), for the dead ends too small to matter.
    box: dict[int, list[float]] = {}
    for ld in lines:
        for key in ("sidefront", "sideback"):
            s = _side_sector(tm, ld, key)
            if s is None:
                continue
            for v in (tm.vertices[ld["v1"]], tm.vertices[ld["v2"]]):
                b = box.setdefault(s, [v["x"], v["y"], v["x"], v["y"]])
                b[0], b[1] = min(b[0], v["x"]), min(b[1], v["y"])
                b[2], b[3] = max(b[2], v["x"]), max(b[3], v["y"])

    def too_small_dead_end(y, reach, radius):
        b = box.get(y)
        small = b is not None and min(b[2] - b[0], b[3] - b[1]) < 2 * radius
        return small and all(n in reach for n in moves[y])
    flo = [Range(f.lo, f.hi) if i in movable else Range(s.get("heightfloor", 0), s.get("heightfloor", 0))
           for i, (f, s) in enumerate(zip(floor, sectors))]
    cei = [Range(c.lo, c.hi) if i in movable else Range(s.get("heightceiling", 0), s.get("heightceiling", 0))
           for i, (c, s) in enumerate(zip(ceil, sectors))]

    def why_not(a, b, line, radius, height, flies):
        """None if a monster this size can move from sector a to b over `line`, else the reason."""
        if width.get(line, 0) < 2 * radius:
            return f"gap {width.get(line, 0):g} wide, it needs {2 * radius}"
        reason = "headroom"
        for fa in {flo[a].lo, flo[a].hi}:
            if cei[a].hi - fa < height:
                continue
            for fb in {flo[b].lo, flo[b].hi}:
                room = min(cei[a].hi, cei[b].hi) - max(fa, fb) >= height and cei[b].hi - fb >= height
                if not room:
                    continue
                if flies or (fb - fa <= STEP and fa - fb <= MONSTER_DROP):
                    return None
                reason = f"a step of {fb - fa:g}" if fb > fa else f"a drop of {fa - fb:g} (more than {MONSTER_DROP})"
        return reason if reason != "headroom" else f"less than {height} of headroom"

    def flood(start, size):
        seen, todo = {start}, [start]
        while todo:
            a = todo.pop()
            for line, f, b in portals:
                for x, y in ((f, b), (b, f)):
                    if x == a and y not in seen and why_not(x, y, line, *size) is None:
                        seen.add(y)
                        todo.append(y)
        return seen

    blocked: dict[tuple[int, str], list[str]] = {}
    checked = 0
    for t in tm.things:
        kind = MONSTERS.get(t.get("type"))
        if not kind or "x" not in t.fields:
            continue
        s = sector_at(tm, t["x"], t["y"])
        if s is None or s not in res.reachable:
            continue                                   # where the player never goes: nothing to chase
        checked += 1
        name, *size = kind
        reach = flood(s, tuple(size))
        for line, f, b in portals:
            for a, y in ((f, b), (b, f)):
                # The player goes both ways between a (the monster's) and y (not): it can't follow there.
                if a in reach and y not in reach and y in res.reachable and a in moves[y] and y in moves[a] \
                        and not too_small_dead_end(y, reach, size[0]):
                    reason = why_not(a, y, line, *size)
                    if reason:
                        blocked.setdefault((line, reason), []).append(f"{name} ({t.get('user_gid') or s})")
    issues = []
    for (line, reason), who in sorted(blocked.items()):
        ld = lines[line]
        issues.append(Issue("warning", f"{', '.join(sorted(set(who)))} can't follow the player here: {reason}",
                            f"line {ld.get('user_gid') or line}", _mid(tm, ld)))
    report = f"monsters: {checked} checked for fit (their size, steps, drops)"
    if issues:
        report += f"; {len(issues)} place(s) one can't follow the player:\n" + "".join(f"  {i}\n" for i in issues)
    else:
        report += "; all can follow the player\n"
    return issues, report


def _name(tm: Textmap, s: int) -> str:
    gid = tm.sectors[s].get("user_gid")
    return f"sector {s}" + (f" ({gid})" if gid else "")


def _centre(tm: Textmap, s: int):
    from dms import render

    polys = render.sector_loops(tm).get(s, [])
    return render.centroid(max(polys, key=render.polygon_area)) if polys else None


def _findings(tm, res, exits, exit_secs, one_way, never_opened, things_in):
    issues: list[Issue] = []
    warn = lambda msg, where="", pos=None: issues.append(Issue("warning", msg, where, pos))  # noqa: E731
    n = len(tm.sectors)
    lines = [f"movement: {len(res.reachable)} of {n} sector(s) reachable from the player start "
             f"({_name(tm, res.start)}); step {STEP}, headroom {HEIGHT}, gap {WIDTH}"]

    for s in sorted(res.unreachable):
        warn("unreachable from the player start", _name(tm, s), _centre(tm, s))
    for t in tm.things:
        typ = t.get("type")
        what = KEYS.get(typ) or WEAPONS.get(typ) or ITEMS.get(typ)
        if what and "x" in t.fields:
            s = sector_at(tm, t["x"], t["y"])
            if s is None or s not in res.reachable:
                warn(f"{what} can't be reached", f"thing {t.get('user_gid') or typ}", (t["x"], t["y"]))
    for i, ld in exits:
        f = _side_sector(tm, ld, "sidefront")
        if f is None or f not in res.reachable:
            warn(f"{EXITS[ld['special']]} can't be reached", f"line {ld.get('user_gid') or i}", _mid(tm, ld))
    for s, sec in enumerate(tm.sectors):
        if (sec.get("secret") or (sec.get("special", 0) & 1024)) and s not in res.reachable:
            warn("secret can't be reached", _name(tm, s), _centre(tm, s))
    for i, why in sorted(never_opened.items()):
        ld = tm.linedefs[i]
        warn(f"{why}; never opens", f"line {ld.get('user_gid') or i}", _mid(tm, ld))
    for s in sorted(res.softlocks):
        warn("soft-lock: you can get here but not to an exit", _name(tm, s), _centre(tm, s))

    if not exits:
        lines.append("no exit in the map: soft-locks not checked")
    elif not exit_secs & res.reachable:
        lines.append("no exit is reachable: soft-locks not checked")
    else:
        lines.append(f"soft-locks: {len(res.softlocks)}")
    if one_way:
        lines.append(f"one-way drops ({len(one_way)}): you can go down but not back up")
        lines += [f"  {_name(tm, a)} -> {_name(tm, b)}" for a, b in one_way]
    if issues:
        lines.append(f"problems ({len(issues)}):")
        lines += [f"  {i}" for i in issues]
    else:
        lines.append("no problems")
    return issues, "\n".join(lines) + "\n"
