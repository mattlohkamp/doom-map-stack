"""Building blocks for generated maps (the `generated` source mode; see PLAN.md section 4).

A map's `map.py` defines `build(m: MapBuilder)` and adds geometry with it. Every element gets a
stable ID in the custom UDMF field `user_gid` (e.g. "room.wall_n"), so the mapper's editor tweaks
can later be matched back to what generated them. This is the M1 starting point: rooms and things.
Doors, lifts, stairs and the rest come as maps need them (M4).
"""

from __future__ import annotations

from dataclasses import dataclass

from dms.udmf import Block, Textmap

# Doom thing type numbers used so far.
PLAYER1_START = 1

# Greybox style (PLAN.md section 10): a small fixed set of plain Freedoom textures by purpose.
WALL = "GRAY1"
FLOOR = "FLOOR4_8"
CEILING = "CEIL3_5"


@dataclass
class Sector:
    index: int
    gid: str


class MapBuilder:
    def __init__(self) -> None:
        self.things: list[Block] = []
        self.vertices: list[Block] = []
        self.linedefs: list[Block] = []
        self.sidedefs: list[Block] = []
        self.sectors: list[Block] = []
        self._vertex_index: dict[tuple[float, float], int] = {}
        self._gids: set[str] = set()

    # -- low level -------------------------------------------------------

    def _gid(self, gid: str) -> str:
        if gid in self._gids:
            raise ValueError(f"duplicate gid {gid!r}")
        self._gids.add(gid)
        return gid

    def vertex(self, x: float, y: float) -> int:
        """Index of the vertex at (x, y); vertices are shared between lines that meet there."""
        key = (float(x), float(y))
        if key not in self._vertex_index:
            self._vertex_index[key] = len(self.vertices)
            self.vertices.append(Block("vertex", {"x": key[0], "y": key[1]}))
        return self._vertex_index[key]

    def sector(self, gid: str, *, floor: int = 0, ceiling: int = 128, light: int = 192,
               floor_tex: str = FLOOR, ceiling_tex: str = CEILING) -> Sector:
        self.sectors.append(Block("sector", {
            "heightfloor": int(floor),
            "heightceiling": int(ceiling),
            "texturefloor": floor_tex,
            "textureceiling": ceiling_tex,
            "lightlevel": int(light),
            "user_gid": self._gid(gid),
        }))
        return Sector(len(self.sectors) - 1, gid)

    def sidedef(self, sector: Sector, gid: str, *, middle: str = "-") -> int:
        self.sidedefs.append(Block("sidedef", {
            "sector": sector.index,
            "texturemiddle": middle,
            "user_gid": self._gid(gid),
        }))
        return len(self.sidedefs) - 1

    def wall(self, a: tuple[float, float], b: tuple[float, float], sector: Sector, gid: str,
             *, texture: str = WALL) -> int:
        """A one-sided, impassable line from a to b; `sector` is on its right (front) side."""
        front = self.sidedef(sector, f"{gid}.front", middle=texture)
        self.linedefs.append(Block("linedef", {
            "v1": self.vertex(*a),
            "v2": self.vertex(*b),
            "sidefront": front,
            "blocking": True,
            "user_gid": self._gid(gid),
        }))
        return len(self.linedefs) - 1

    def thing(self, type_: int, x: float, y: float, gid: str, *, angle: int = 0) -> int:
        """A thing on every skill level and in every game mode (PLAN.md section 10)."""
        fields: dict = {"x": float(x), "y": float(y), "angle": int(angle), "type": int(type_)}
        for flag in ("skill1", "skill2", "skill3", "skill4", "skill5", "single", "coop", "dm",
                     "class1", "class2", "class3"):
            fields[flag] = True
        fields["user_gid"] = self._gid(gid)
        self.things.append(Block("thing", fields))
        return len(self.things) - 1

    # -- building blocks -------------------------------------------------

    def room(self, gid: str, x: float, y: float, width: float, height: float, **sector_args) -> Sector:
        """A closed rectangular room with its lower-left corner at (x, y). Walls are named
        <gid>.wall_w/_n/_e/_s. Corners go clockwise so the room is on each wall's front side."""
        s = self.sector(gid, **sector_args)
        sw, nw, ne, se = (x, y), (x, y + height), (x + width, y + height), (x + width, y)
        self.wall(sw, nw, s, f"{gid}.wall_w")
        self.wall(nw, ne, s, f"{gid}.wall_n")
        self.wall(ne, se, s, f"{gid}.wall_e")
        self.wall(se, sw, s, f"{gid}.wall_s")
        return s

    def player_start(self, x: float, y: float, *, angle: int = 90, gid: str = "player1_start") -> int:
        return self.thing(PLAYER1_START, x, y, gid, angle=angle)

    # -- output ----------------------------------------------------------

    def textmap(self) -> Textmap:
        tm = Textmap()
        tm.blocks = [*self.things, *self.vertices, *self.linedefs, *self.sidedefs, *self.sectors]
        return tm
