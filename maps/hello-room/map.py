"""Hello room: the generator for this map. `.\\dms.ps1 build hello-room` turns it into TEXTMAP."""

import math

from dms.gen import MapBuilder

# The blood yards behind the hex room's windows: their floors start down in a pit, out of sight,
# and rise to the window sill when the player enters the hallway (notes #15, #16).
YARD_TAG = 1
YARD_PIT = -256
YARD_SILL = 32


def build(m: MapBuilder) -> None:
    # One 512 x 512 room, 128 high, with the player start near the south wall facing north.
    # Special 72 = glowing light: fades between the room's light (192, ~75%) and its darkest
    # neighbour's (platform_nw, 64 after the mapper's tweak, ~25%). Mapper's request, 2026-11-21.
    room = m.sector("room", floor=0, ceiling=128, light=192)  # the glow (special 72) removed: in-game note #11
    # The room's walls, clockwise. The mapper moved the south-east corner in from (512, 0) to (480, 32)
    # in the editor (pulled 2026-11-21), so it isn't a rectangle any more; same wall gids as m.room().
    sw, nw, ne, se = (0, 0), (0, 512), (512, 512), (480, 32)
    # In-game note #10: a hallway through the south wall (120 wide, between the two ledges, where the
    # mapper was looking) to a hexagonal room of the same size. The south wall slants (y = x / 15),
    # so the opening's ends are where that comes out whole: (180, 12) and (300, 20).
    mouth_w, mouth_e = (180, 12), (300, 20)
    for name, a, b in (("w", sw, nw), ("n", nw, ne), ("e", ne, se), ("s", se, mouth_e), ("s2", mouth_w, sw)):
        m.wall(a, b, room, f"room.wall_{name}")
    hallway_and_hex(m, room, mouth_w, mouth_e)
    m.player_start(256, 128, angle=90)
    # In-game note #17: start with a super shotgun, the chaingun and a backpack, picked up on the
    # first step (placed on the player start).
    for type_, name in ((82, "super_shotgun"), (2002, "chaingun"), (8, "backpack")):
        m.thing(type_, 256, 128, f"start.{name}")

    # Board test: a lower 128 x 128 platform in the north-west, 16 units up, dimmer than the room.
    low = m.sector("platform_nw", floor=16, ceiling=128, light=128)
    sw, nw, ne, se = (64, 320), (64, 448), (192, 448), (192, 320)
    for name, a, b in (("w", sw, nw), ("n", nw, ne), ("e", ne, se), ("s", se, sw)):
        m.two_sided(a, b, low, room, f"platform_nw.edge_{name}")
    m.thing(2011, 128, 400, "platform_nw.stimpack")  # a stimpack on top of the platform
    # A cacodemon on the platform, facing north-west. History of this spot (in-game notes): #4 a
    # zombieman, #5 facing away from the player, #6 three of them, #9 the three replaced by one caco.
    m.thing(3005, 128, 368, "platform_nw.cacodemon", angle=135)

    # Added by the mapper in the editor (pulled 2026-11-21) as a shotgun; the super shotgun since
    # in-game note #8; a rocket launcher since note #12 (same gid, so any overrides still apply).
    m.thing(2003, 416, 384, "room.super_shotgun")

    # Two ledges 40 up with partial invisibility (2024) on each (the movement-check demo; soulspheres
    # until note #3; the south-east copy from note #1). In-game note #7: a step up to each, on the
    # north side facing the room: 0 -> 20 -> 40, each rise within the player's 24.
    ledge_with_step(m, room, "ledge_sw", 48, 48)
    ledge_with_step(m, room, "ledge_se", 320, 48)


def ledge_with_step(m: MapBuilder, room, gid: str, x: float, y: float) -> None:
    """A 128 x 128 ledge 40 up with its south-west corner at (x, y), a power-up on top, and a step
    (64 wide, 32 deep, 20 up) in the middle of its north side. Lines run clockwise round each
    sector, so that sector is on their front side."""
    ledge = m.sector(gid, floor=40, ceiling=128, light=192)
    step = m.sector(f"{gid}.step", floor=20, ceiling=128, light=192)
    sw, nw, ne, se = (x, y), (x, y + 128), (x + 128, y + 128), (x + 128, y)
    s0, s1 = (x + 32, y + 128), (x + 96, y + 128)          # where the step meets the ledge
    t0, t1 = (x + 32, y + 160), (x + 96, y + 160)          # the step's front edge
    m.two_sided(sw, nw, ledge, room, f"{gid}.edge_w")
    m.two_sided(nw, s0, ledge, room, f"{gid}.edge_n")
    m.two_sided(s0, s1, ledge, step, f"{gid}.edge_step")
    m.two_sided(s1, ne, ledge, room, f"{gid}.edge_n2")
    m.two_sided(ne, se, ledge, room, f"{gid}.edge_e")
    m.two_sided(se, sw, ledge, room, f"{gid}.edge_s")
    m.two_sided(s0, t0, step, room, f"{gid}.step.edge_w")
    m.two_sided(t0, t1, step, room, f"{gid}.step.edge_n")
    m.two_sided(t1, s1, step, room, f"{gid}.step.edge_e")
    m.thing(2024, x + 64, y + 64, f"{gid}.invisibility")


def hallway_and_hex(m: MapBuilder, room, mouth_w, mouth_e) -> None:
    """A hallway south from the room's opening (mouth_w-mouth_e on its south wall) into a hexagonal
    room as wide as the main room (512 across, flat side to the north where the hallway joins,
    points to the east and west). Lines run clockwise round each sector, so it's on their front."""
    hall = m.sector("hall", floor=0, ceiling=104, light=160)
    hex_ = m.sector("hex", floor=0, ceiling=128, light=160)
    (x0, _), (x1, _) = mouth_w, mouth_e
    y = -128                                     # where the hallway meets the hexagon
    # In-game notes #15, #16, #18: entering the hallway brings the lost souls up out of the blood
    # yards, already after the player. Two lines, crossed one after the other (each once):
    # - its north mouth raises every yard's floor (tag YARD_TAG) from the pit to the window sill
    #   (Floor_RaiseByValue, 23: tag, speed 32 = 4 units a tic, ~2 s, height);
    # - a line 28 further in makes a noise where the player is (NoiseAlert, 173), which wakes the
    #   souls and sets them on the player, seen or not.
    # Both mouths block sound: a sound gets through one such line but not two, so gunfire in the main
    # room doesn't wake them early, while the noise from the hallway reaches the hexagon and yards.
    split = -16
    entry = m.sector("hall.entry", floor=0, ceiling=104, light=160)
    n = m.two_sided(mouth_w, mouth_e, entry, room, "hall.mouth_n")
    m.linedefs[n].fields.update(special=23, arg0=YARD_TAG, arg1=32, arg2=YARD_SILL - YARD_PIT,
                                playercross=True, blocksound=True)
    m.wall(mouth_e, (x1, split), entry, "hall.entry.wall_e")
    k = m.two_sided((x1, split), (x0, split), entry, hall, "hall.alarm")
    m.linedefs[k].fields.update(special=173, playercross=True)
    m.wall((x0, split), mouth_w, entry, "hall.entry.wall_w")
    m.wall((x1, split), (x1, y), hall, "hall.wall_e")
    s = m.two_sided((x1, y), (x0, y), hall, hex_, "hall.mouth_s")
    m.linedefs[s]["blocksound"] = True
    m.wall((x0, y), (x0, split), hall, "hall.wall_w")
    # A regular hexagon, radius 256, centred 222 (256 * sqrt(3) / 2) below its north side.
    cx, r, h = 240, 256, 222
    top_w, top_e = (cx - r // 2, y), (cx + r // 2, y)
    east, west = (cx + r, y - h), (cx - r, y - h)
    bot_e, bot_w = (cx + r // 2, y - 2 * h), (cx - r // 2, y - 2 * h)
    m.wall(top_w, (x0, y), hex_, "hex.wall_n")
    m.wall((x1, y), top_e, hex_, "hex.wall_n2")
    # In-game note #13 ("seems empty"): a lit niche in the middle of each full wall; note #14: windows
    # instead, bleeding into a blood pool on the floor.
    for name, a, b in (("ne", top_e, east), ("se", east, bot_e), ("s", bot_e, bot_w),
                       ("sw", bot_w, west), ("nw", west, top_w)):
        wall_with_bleeding_window(m, hex_, a, b, f"hex.wall_{name}")


def wall_with_bleeding_window(m: MapBuilder, room, a, b, gid: str) -> None:
    """The wall a->b (room on its front) with a window in its middle, 64 wide, sill 32, top 96, onto
    a small open-air yard behind (sky, floor of blood level with the sill). The blood runs over the
    sill and down the wall below it (BFALL1, animated) into a pool sunk 8 into the floor in front.
    The sill is above the player's 24 step, so the window can't be climbed through. Each sector is
    on the right (front) of its lines, going round it clockwise."""
    (ax, ay), (bx, by) = a, b
    length = ((bx - ax) ** 2 + (by - ay) ** 2) ** 0.5
    dx, dy = (bx - ax) / length, (by - ay) / length
    nx, ny = -dy, dx                                   # left of a->b: away from the room
    c = length / 2

    def at(along: float, out: float = 0) -> tuple[float, float]:
        """`along` the wall from a, `out` beyond it (negative: into the room)."""
        return (round(ax + dx * (c + along) + nx * out), round(ay + dy * (c + along) + ny * out))

    window = m.sector(f"{gid}.window", floor=YARD_SILL, ceiling=96, light=192, floor_tex="BLOOD1")
    # The yard's floor is a lift (note #16): down in the pit until the hallway raises it to the sill.
    yard = m.sector(f"{gid}.yard", floor=YARD_PIT, ceiling=224, light=224, floor_tex="BLOOD1", ceiling_tex="F_SKY1")
    m.sectors[yard.index]["id"] = YARD_TAG
    pool = m.sector(f"{gid}.pool", floor=-8, ceiling=128, light=160, floor_tex="BLOOD1")
    p0, p1 = at(-32), at(32)                           # the window, in the wall
    q0, q1 = at(-32, 16), at(32, 16)                   # where it opens onto the yard
    w0, w1, x0, x1 = at(-64, 16), at(64, 16), at(-64, 80), at(64, 80)  # the yard
    r0, r1, s0, s1 = at(-48), at(48), at(-48, -48), at(48, -48)        # the pool
    # The wall, with the pool against it.
    m.wall(a, r0, room, gid)
    m.wall(r0, p0, pool, f"{gid}.pool_a")
    mouth = m.two_sided(p1, p0, window, pool, f"{gid}.window.sill")
    m.sidedefs[m.linedefs[mouth]["sideback"]]["texturebottom"] = "BFALL1"  # the bloodfall
    m.wall(p1, r1, pool, f"{gid}.pool_b")
    m.wall(r1, b, room, f"{gid}.b")
    # The window's sides, and the yard behind it.
    m.wall(p0, q0, window, f"{gid}.window.side_a")
    m.two_sided(q0, q1, window, yard, f"{gid}.window.out")
    m.wall(q1, p1, window, f"{gid}.window.side_b")
    for name, u, v in (("a", q0, w0), ("left", w0, x0), ("back", x0, x1), ("right", x1, w1), ("b", w1, q1)):
        m.wall(u, v, yard, f"{gid}.yard.wall_{name}")
    # The pool's edges in the room.
    for name, u, v in (("b", r1, s1), ("front", s1, s0), ("a", s0, r0)):
        m.two_sided(u, v, pool, room, f"{gid}.pool.edge_{name}")
    # Note #15: a lost soul in the yard, facing the window; #16: it waits down in the pit, out of
    # sight, until the lift brings it up; #18: the hallway's alarm wakes it as the lift starts (not
    # deaf, so it hears that). The window (64 x 64) is big enough for it (radius 16, 56 high).
    x, y = at(0, 48)
    m.thing(3006, x, y, f"{gid}.yard.lost_soul", angle=round(math.degrees(math.atan2(-ny, -nx))) % 360)
