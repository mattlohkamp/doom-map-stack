"""Hello room: the generator for this map. `.\\dms.ps1 build hello-room` turns it into TEXTMAP."""

from dms.gen import MapBuilder


def build(m: MapBuilder) -> None:
    # One 512 x 512 room, 128 high, with the player start near the south wall facing north.
    # Special 72 = glowing light: fades between the room's light (192, ~75%) and its darkest
    # neighbour's (platform_nw, 64 after the mapper's tweak, ~25%). Mapper's request, 2026-11-21.
    room = m.room("room", 0, 0, 512, 512, floor=0, ceiling=128, light=192, special=72)
    m.player_start(256, 128, angle=90)

    # Board test: a lower 128 x 128 platform in the north-west, 16 units up, dimmer than the room.
    low = m.sector("platform_nw", floor=16, ceiling=128, light=128)
    sw, nw, ne, se = (64, 320), (64, 448), (192, 448), (192, 320)
    for name, a, b in (("w", sw, nw), ("n", nw, ne), ("e", ne, se), ("s", se, sw)):
        m.two_sided(a, b, low, room, f"platform_nw.edge_{name}")
    m.thing(2011, 128, 400, "platform_nw.stimpack")  # a stimpack on top of the platform

    # Added by the mapper in the editor (pulled 2026-11-21): a shotgun in the north-east.
    m.thing(2001, 416, 384, "room.shotgun")
