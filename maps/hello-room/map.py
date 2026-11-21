"""Hello room: the generator for this map. `.\\dms.ps1 build hello-room` turns it into TEXTMAP."""

from dms.gen import MapBuilder


def build(m: MapBuilder) -> None:
    # One 512 x 512 room, 128 high, with the player start near the south wall facing north.
    # Special 72 = glowing light: fades between the room's light (192, ~75%) and its darkest
    # neighbour's (platform_nw, 64 after the mapper's tweak, ~25%). Mapper's request, 2026-11-21.
    room = m.sector("room", floor=0, ceiling=128, light=192, special=72)
    # The room's walls, clockwise. The mapper moved the south-east corner in from (512, 0) to (480, 32)
    # in the editor (pulled 2026-11-21), so it isn't a rectangle any more; same wall gids as m.room().
    sw, nw, ne, se = (0, 0), (0, 512), (512, 512), (480, 32)
    for name, a, b in (("w", sw, nw), ("n", nw, ne), ("e", ne, se), ("s", se, sw)):
        m.wall(a, b, room, f"room.wall_{name}")
    m.player_start(256, 128, angle=90)

    # Board test: a lower 128 x 128 platform in the north-west, 16 units up, dimmer than the room.
    low = m.sector("platform_nw", floor=16, ceiling=128, light=128)
    sw, nw, ne, se = (64, 320), (64, 448), (192, 448), (192, 320)
    for name, a, b in (("w", sw, nw), ("n", nw, ne), ("e", ne, se), ("s", se, sw)):
        m.two_sided(a, b, low, room, f"platform_nw.edge_{name}")
    m.thing(2011, 128, 400, "platform_nw.stimpack")  # a stimpack on top of the platform
    # Mapper's in-game note #4 ("drop a monster here", crosshair on this spot): a zombieman. Facing
    # north-west, away from the player (note #5).
    m.thing(3004, 136, 368, "platform_nw.zombieman", angle=135)
    # Two more, so three in all (in-game note #6), same facing.
    m.thing(3004, 88, 424, "platform_nw.zombieman_2", angle=135)
    m.thing(3004, 168, 424, "platform_nw.zombieman_3", angle=135)

    # Added by the mapper in the editor (pulled 2026-11-21): a shotgun in the north-east.
    m.thing(2001, 416, 384, "room.shotgun")

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
