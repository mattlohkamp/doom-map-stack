"""Hello room: the generator for this map. `.\\dms.ps1 build hello-room` turns it into TEXTMAP."""

from dms.gen import MapBuilder


def build(m: MapBuilder) -> None:
    # One 512 x 512 room, 128 high, with the player start in the middle facing north.
    m.room("room", 0, 0, 512, 512, floor=0, ceiling=128, light=192)
    m.player_start(256, 256, angle=90)
