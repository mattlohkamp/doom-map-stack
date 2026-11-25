"""test map: the generator for this map. `.\\dms.ps1 build test-map` turns it into TEXTMAP."""

import math

from dms.gen import MapBuilder

SECRET_TAG = 1  # the secret room's sector tag; the door opens it (Door_Open, special 11)
PILLAR_TAG = 2  # the pillars' sector tag: they open when the player steps up to the super shotgun
CACO_TID = 10   # the pillar cacos' thing id; the map's script (zscript.zs) wakes them as they open
QUAD_TID = 11   # a map spot in the secret room; the map's script puts its quad damage there

# Test-map note #4 (build #7): the room is a big regular pentagon, one corner pointing north, with a
# pillar in each corner, a torch in the middle of each wall and a glowing pentagram on the floor.
R = 768              # the pentagon's corners are this far from its centre (0, 0); ~1460 across
CEILING = 256        # taller than before, for a room this size
ROOM_LIGHT = 176
WALL_TEX = "REDWALL1"          # the room is red (note #1)
PILLAR_TEX = "MARBLE1"
PILLAR_R = 64                  # each pillar is a small pentagon, room enough inside for a caco (62)
PILLAR_IN = 144                # its centre, in from the room's corner towards the middle
TORCH = 46                     # tall red torch
TORCH_IN = 40                  # in from the wall
# The pentagram (note #5: "more satanic"): drawn as lines, inverted (one point south, towards the
# player start, so it reads the right way up looking north), inside a ring.
STAR_R = 360                   # where the lines' centres meet at the points
LINE_HALF = 12                 # the lines are 24 wide
RING_GAP = 12                  # between the points (mitred, so they reach past STAR_R) and the ring
RING_W = 24
RING_SEGMENTS = 40             # a multiple of 5 (and 8 x 5 puts a ring vertex in front of each point)
STAR_LIGHT = 224               # it glows between this and the room's light (sector special 72)
STAR_FLAT = "LAVA1"


def polar(r: float, deg: float) -> tuple[int, int]:
    a = math.radians(deg)
    return (round(r * math.cos(a)), round(r * math.sin(a)))


def along(a, b, t: float) -> tuple[int, int]:
    return (round(a[0] + (b[0] - a[0]) * t), round(a[1] + (b[1] - a[1]) * t))


def build(m: MapBuilder) -> None:
    room = m.sector("room", floor=0, ceiling=CEILING, light=ROOM_LIGHT, floor_tex="BLOOD1")
    # The corners clockwise from north, so the room is on the right (front) of each wall.
    n, ene, se, sw, wnw = (polar(R, a) for a in (90, 18, -54, -126, 162))

    # The secret room (notes #2, #3) is behind the west wall (sw -> wnw), between its middle and its
    # north end: a 128-wide secret door that looks like the wall (use it to open), and a closed room
    # 160 deep behind it with a caco. Wider than a caco (62), so it can walk out.
    door_a, door_b = along(sw, wnw, 0.68), along(sw, wnw, 0.82)
    for name, a, b in (("ne", n, ene), ("e", ene, se), ("s", se, sw), ("w", sw, door_a)):
        m.wall(a, b, room, f"room.wall_{name}", texture=WALL_TEX)
    secret = m.sector("secret_room", floor=0, ceiling=0, light=128)
    m.sectors[secret.index]["id"] = SECRET_TAG
    door = m.two_sided(door_a, door_b, room, secret, "room.secret_door", texture=WALL_TEX)
    m.linedefs[door].fields.update(special=11, arg0=SECRET_TAG, arg1=16, playeruse=True)
    for name, a, b in (("w2", door_b, wnw), ("nw", wnw, n)):
        m.wall(a, b, room, f"room.wall_{name}", texture=WALL_TEX)
    # Out from the wall (its outward normal is to the left going sw -> wnw).
    dx, dy = wnw[0] - sw[0], wnw[1] - sw[1]
    length = math.hypot(dx, dy)
    ox, oy = -dy / length * 160, dx / length * 160
    far_a = (round(door_a[0] + ox), round(door_a[1] + oy))
    far_b = (round(door_b[0] + ox), round(door_b[1] + oy))
    # Clockwise round the secret room: door_a -> far_a -> far_b -> door_b (then the door back).
    for name, a, b in (("s", door_a, far_a), ("w", far_a, far_b), ("n", far_b, door_b)):
        m.wall(a, b, secret, f"secret_room.wall_{name}", texture=WALL_TEX)
    # In the secret room: quad damage (it was a caco until the mapper's chat request, build #9). Doom
    # has no quad damage, so the map's script defines one (UZDoom's PowerDamage, x4 for 30 s) and puts
    # it on this map spot.
    mid = along(along(door_a, door_b, 0.5), along(far_a, far_b, 0.5), 0.5)
    t = m.thing(9001, mid[0], mid[1], "secret_room.quad_spot")
    m.things[t]["id"] = QUAD_TID

    # Pillars: a pentagon in each corner, pointing into the corner, each a closed door sector (tag
    # PILLAR_TAG) with a caco inside, facing the middle. They open when the player steps up to the
    # super shotgun (see pentagram()). Their sides go round them anticlockwise, so the room (outside)
    # is on the front.
    for name, deg in (("n", 90), ("ene", 18), ("se", -54), ("sw", -126), ("wnw", 162)):
        cx, cy = polar(R - PILLAR_IN, deg)
        pts = [polar(PILLAR_R, deg + 72 * k) for k in range(5)]
        pts = [(cx + x, cy + y) for x, y in pts]
        pillar = m.sector(f"pillar_{name}", floor=0, ceiling=0, light=ROOM_LIGHT)
        m.sectors[pillar.index]["id"] = PILLAR_TAG
        for k in range(5):
            m.two_sided(pts[k], pts[(k + 1) % 5], room, pillar, f"pillar_{name}.side_{k}",
                        texture=PILLAR_TEX)
        t = m.thing(3005, cx, cy, f"pillar_{name}.cacodemon", angle=(deg + 180) % 360)
        m.things[t]["id"] = CACO_TID

    # A tall red torch in the middle of each wall, just in from it.
    apothem = R * math.cos(math.radians(36))
    for name, deg in (("ne", 54), ("e", -18), ("s", -90), ("w", -162), ("nw", 126)):
        x, y = polar(apothem - TORCH_IN, deg)
        m.thing(TORCH, x, y, f"room.torch_{name}")

    pentagram(m, room)

    # The player starts near the south wall, facing north across the pentagram, with a chaingun
    # (picked up on the first step).
    m.player_start(0, -480, angle=90)
    m.thing(2002, 0, -480, "start.chaingun")


def pentagram(m: MapBuilder, room) -> None:
    """An inverted pentagram drawn in lava lines inside a lava ring, one sector ("pentagram", same
    floor height as the room) glowing slowly: special 72 fades its light down to the room's and back.

    The five lines are the extended sides of a regular pentagon: line k runs from point k to point
    k + 2, as the set {x : n_k . x = d} (n_k pointing away from the centre). A line 2h wide covers
    d - h <= n_k . x <= d + h. Their union is a thick star outline with six holes (the inner pentagon
    and the five point triangles), all room floor. Every corner is where two of the offset lines
    cross (mitred at the points)."""
    points = [polar(STAR_R, -90 + 72 * k) for k in range(5)]        # point 0 is south
    lines = []
    for k in range(5):
        (x0, y0), (x1, y1) = points[k], points[(k + 2) % 5]
        nx, ny = y1 - y0, x0 - x1
        length = math.hypot(nx, ny)
        nx, ny = nx / length, ny / length
        d = nx * x0 + ny * y0
        if d < 0:
            nx, ny, d = -nx, -ny, -d
        lines.append((nx, ny, d))

    def cross(j: int, oj: int, k: int, ok: int) -> tuple[int, int]:
        """Where line j offset by oj * h meets line k offset by ok * h."""
        (a1, b1, d1), (a2, b2, d2) = lines[j % 5], lines[k % 5]
        c1, c2 = d1 + oj * LINE_HALF, d2 + ok * LINE_HALF
        det = a1 * b2 - a2 * b1
        return (round((c1 * b2 - c2 * b1) / det), round((a1 * c2 - a2 * c1) / det))

    def by_angle(pts, clockwise: bool):
        cx = sum(p[0] for p in pts) / len(pts)
        cy = sum(p[1] for p in pts) / len(pts)
        return sorted(pts, key=lambda p: math.atan2(p[1] - cy, p[0] - cx), reverse=clockwise)

    star = m.sector("pentagram", floor=0, ceiling=CEILING, light=STAR_LIGHT, floor_tex=STAR_FLAT,
                    special=72)

    def loop(pts, gid: str) -> list[int]:
        return [m.two_sided(pts[i], pts[(i + 1) % len(pts)], star, room, f"{gid}_{i}", texture=WALL_TEX)
                for i in range(len(pts))]

    # The outline's outside: mitred points (lines k and k + 2 meet there) and the notches between
    # them (lines k and k + 1), all offset outwards; clockwise, so the pentagram is on the right.
    # It's star-shaped around the centre, so sorting by angle orders it.
    outer = [cross(k, 1, k + 2, 1) for k in range(5)] + [cross(k, 1, k + 1, 1) for k in range(5)]
    loop(by_angle(outer, clockwise=True), "pentagram.outline")
    # The holes go anticlockwise, so the pentagram (round them) is on the right.
    inner = loop(by_angle([cross(k, -1, k + 1, -1) for k in range(5)], clockwise=False),
                 "pentagram.inner")
    # A super shotgun in the middle (mapper's chat request, build #9). The inner pentagon's edges are
    # the trap: walking over any of them (the only way to the shotgun) opens the pillars, and the
    # map's script wakes the cacos in them at the same moment.
    m.thing(82, 0, 0, "pentagram.super_shotgun")
    for i in inner:
        m.linedefs[i].fields.update(special=11, arg0=PILLAR_TAG, arg1=16, playercross=True)
    # Point triangle at point p: inside lines p and p - 2 (which meet there), beyond line p - 1.
    for p in range(5):
        tri = [cross(p, -1, p - 2, -1), cross(p, -1, p - 1, 1), cross(p - 2, -1, p - 1, 1)]
        loop(by_angle(tri, clockwise=False), f"pentagram.point{p}")

    # The ring, just beyond the points.
    tip = STAR_R + LINE_HALF / math.cos(math.radians(72))
    r_in = tip + RING_GAP
    r_out = r_in + RING_W
    step = 360 / RING_SEGMENTS
    angles = [-90 + step * i for i in range(RING_SEGMENTS)]
    loop([polar(r_out, -a) for a in angles], "ring.outer")            # clockwise
    loop([polar(r_in, a) for a in angles], "ring.inner")              # anticlockwise
