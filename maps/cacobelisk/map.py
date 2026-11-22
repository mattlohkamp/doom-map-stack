"""Cacobelisk (was test2): the generator for this map. `.\\dms.ps1 build cacobelisk` turns it into TEXTMAP."""

import hashlib

from dms.gen import MapBuilder

# In-game note #1, the follow-up in chat and note #2 (2026-11-22): the start is a broken elevator.
# A dark, low closet (128 x 256, 64 high; note #6) with the dead level-start door behind the player; at its far
# end a small square platform, the elevator, and straight ahead the switch, inset in a lit niche. The
# switch lowers only the platform (and the niche's floor with it), 256, once and for good, leaving the
# closet up the shaft behind, never to return. Going down, the shaft walls below the starting floor
# show the elevator track, and the niche opens out below the switch into a mouth and a big, tall room
# beyond (straight on). Looking up from the bottom, the switch is far above. When it lands, its light
# flickers and it sparks (zscript.zs).
CAR_TAG = 1
DROP = 256               # how far the platform goes down: the big room's floor is at -DROP
CAR_SPEED = 12           # 1.5 units a tic: the ride takes about 5 s
LOW = 64                 # the closet's and the shaft's ceiling: claustrophobic
# Note #6: the closet twice as wide and long (x -32 to 96, y -128 to 128), and darker; lit only by dim
# red emergency lights in channels in its long walls, as if no one has come through in a long time.
CLOSET = (-32, 96, -128, 128)
CLOSET_LIGHT = 80         # the closet and the platform (were 128)
CHANNEL_AT = (64, 128, 192)          # along each long wall
CHANNEL_TEXTURE = "LITERED"          # a red light tube, 16 wide
CHANNEL_LIGHT = 128
CHANNEL_TINT = 0xFF5A48
CHANNEL_GLOW = 9830                  # PointLightAttenuated: args red, green, blue, radius
CHANNEL_RGB = (96, 20, 12)
CHANNEL_RADIUS = 48
# Varied (mapper, 2026-11-22): some channels dimmer than the rest, not mirrored across the closet,
# as if some tubes are failing. Keyed by wall gid and channel number (1 = nearest the wall's start).
CHANNEL_DIM = {("closet.wall_w", 1), ("closet.wall_w", 3), ("closet.wall_e", 2)}
CHANNEL_DIM_LIGHT = 96
CHANNEL_DIM_RGB = (56, 12, 8)
# The closet breathes (mapper, 2026-11-22): its light fades slowly between these, 3 s each way
# (zscript.zs runs Light_Glow on CLOSET_TAG when the level loads).
CLOSET_TAG = 2
# Editor save 2026-11-22 01:47: a raised ceiling panel in the closet, x -24 to 88, y -128 (the south
# wall) to 120, its ceiling at 72, an 8-wide border at 64 along the west, east and north walls.
COFFER = (-24, 88, 120)
COFFER_CEILING = 72
TRACK = "SUPPORT3"       # the shaft's walls below the starting floor: the elevator track
# Notes #19, #20: the 16 lip between the platform and the niche (the sill under the switch, and the step
# out at the bottom) is a short safety step: STEPTOP (dark rusty brown, exactly 16 high, so it lines up)
# on both its faces (the platform's side, and the passage's side once down), the track metal (SUPPORT3)
# on top (the niche's floor). A-GRATE was tried first (grey in the game, black holes, misaligned), then a
# STEP1 tread plate on top (grey, didn't match the walls).
LIP_FACE = "STEPTOP"
LIP_TOP = TRACK            # note #22: the track metal itself, to match the shaft walls (STEP1 was grey)
SWITCH_TEXTURE = "SW1GRAY"
START_DOOR = "DOOR3"     # the classic level-start door, 64 x 72
# The switch niche: 48 wide, 8 deep, sill 16, top 48, a little brighter than the shaft (note #2).
NICHE_X0, NICHE_X1 = 8, 56
NICHE_FLOOR, NICHE_TOP = 16, 48
NICHE_LIGHT = 176
# Note #25: the bottom call switch's niche is dark, darker than the hall (104), so it doesn't draw attention.
CALL_NICHE_LIGHT = 72
# Note #7: a pulse at the switch, subtle but insistent (this is the only way on): a small pale light
# (PointLightPulseAttenuated, 9831) just in front of the plate, swelling and fading every second. Light
# things don't fall with the floor, so it stays up with the switch when the niche drops away.
SWITCH_PULSE_RGB = (150, 200, 170)
SWITCH_PULSE_RADIUS = (12, 24)   # the mapper's editor save 2026-11-22 01:42 (was 24 to 56)
SWITCH_PULSE_PERIOD = 35  # tics
# Note #7: the elevator track shows 16 up the platform's walls before it moves, a preview of the ride: the
# solid blocks lining the shaft are at 16, not 0, so the track (their lower texture) starts there.
TRACK_PREVIEW = 16
# The hall: the mouth and the big room, dim and quiet (mapper, 2026-11-22), in fog.
HALL_LIGHT = 104          # note #4: "drop the lighting just a bit" (was 120)
HALL_FOG = 0x50585C       # grey-green, like the stone
HALL_FOG_DENSITY = 360    # note #26: more intense (96 at first, then 200, then 280)
# Two rows of monoliths flanking the way downrange: green marble slabs 80 long, 32 deep, corners cut
# on the aisle side, the carved ring (MARBFAC2) wrapped round towards the aisle (note #3),
# on a base 16 wider all round and 16 up, a little brighter than the hall. The slab stands 128 above
# its base (one face texture), 48 below the ceiling.
# Note #4: all the ring (MARBFAC2), the mapper's favourite of the three; the skull (MARBFACE) and the
# alien (MARBFAC3) are kept for another use.
FACE = "MARBFAC2"
STONE = "MARBLE1"
# The slabs' west edges. Editor save 2026-11-22 01:23: both rows 64 further out (were -96 and 128), an
# aisle 320 wide, x -128 to 192.
MONOLITH_ROWS = (-160, 192)
# Note #5: spread at regular intervals down the room's whole length (y ~288 to ~2000 along the rows,
# under the apse): six a side, every 280, about half an interval from each end (were five, 160 apart).
MONOLITH_YS = (400, 680, 960, 1240, 1520, 1800)
# Note #5: a gutter of green water along the west and east walls, behind the rows, so the middle is
# the clear way on: 64 wide, 8 deep, NUKAGE1 (no damage), a lip of floor about 32 wide between it and
# the wall. The walls slant, so each gutter is a parallelogram following its wall, y 320 to 1760.
# Corners clockwise (the gutter on the right of each line): south-west, north-west, north-east, south-east.
GUTTERS = {
    "w": ((-336, 320), (-352, 1760), (-288, 1760), (-272, 320)),
    "e": ((320, 320), (352, 1760), (416, 1760), (384, 320)),
}
GUTTER_FLAT = "NUKAGE1"
MOUTH_W, MOUTH_E = (-64, 240), (144, 224)   # the mouth's far corners, onto the room
BASE_LIGHT = 120
BASE_STEP = 8             # note #8: was 16; 8 leaves the cacodemon (56 tall) room on top of the slab
# Note #8: the obelisks' reveal (zscript.zs, CacobeliskObelisks). Pair i (0 = nearest the mouth): sleeves
# tagged SLEEVE_TAG + i, slabs SLAB_TAG + i, glow lights thing id GLOW_TID + i.
SLEEVE_TAG, CACO_TAG, GLOW_TID = 100, 200, 100
# Note #9: the sleeves reach up into a slot in the ceiling (their top 48 above the hall's), so they sink
# further (104, was 56) before the carving starts to show, and the whole carving stays whole.
SLEEVE_TOP = -16
# Note #14: the slots severely darker than the hall: their ceilings and walls at light 120 - 88 = 32
# (relative to their sectors' 120: UDMF lightceiling on the ceilings, light on the walls' sides).
SLOT_DARK = -88
# Note #11: one obelisk is different, an object to interact with: the 5th pair's east one (monolith_e5).
# Only it brings a cacodemon (note #9 had one a pair, "6 is too many"); its slab is the only one tagged
# CACO_TAG + pair. Its glow is a touch different (greener and paler, a quicker pulse), and a low rumble
# (UZDoom's world/quake, looped, very quiet) comes from inside it from the start (zscript.zs).
SWITCH_OBELISK = (4, "e")            # (pair index, row)
SWITCH_GLOW_RGB = (170, 110, 220)   # note #26: more purple (note #17: 165,180,215; before that 120,220,150)
SWITCH_GLOW_PERIOD = 70              # 2 s (the others 3 s)
SWITCH_GLOW_TINT = 0xC8A8F0        # note #26: purple (note #17: 0xD0C8F0; before that 0xB8F0B0)
# Note #16: a low altar in front of each monolith (aisle side, 16 out from its base: 24 deep, 48 along,
# 16 high, green marble), with one or two small pickups, so the player is stocked up for the cacodemon.
# Pistol start, so only small things: clips (2007), health bonuses (2014), armour bonuses (2015); a
# stimpack (2011) on the pair before the switch obelisk. Varied, not mirrored. Keyed by monolith gid.
CLIP, HEALTH_BONUS, ARMOR_BONUS, STIMPACK = 2007, 2014, 2015, 2011
# Note #18: the switch obelisk's altar (the cacodemon's) carries a shotgun and two packs of 4 shells.
SHOTGUN, SHELLS = 2001, 2008
# The mapper, 2026-11-22: 15 armour bonuses (+15% armour) and 20 health bonuses (+20 health) across the
# hall, the stimpack kept, the ammo as it was (6 clips; the shotgun and 2 shell packs). Heavier altars
# are fine; the counts vary from altar to altar, not mirrored.
HB, AB = HEALTH_BONUS, ARMOR_BONUS
ALTAR_ITEMS = {
    "monolith_w1": (CLIP, HB, HB, AB), "monolith_e1": (HB, HB, AB, AB),
    "monolith_w2": (AB, AB, HB), "monolith_e2": (CLIP, HB, HB, AB),
    "monolith_w3": (HB, HB, AB, AB), "monolith_e3": (CLIP, HB, AB),
    "monolith_w4": (STIMPACK, AB, AB, HB), "monolith_e4": (AB, HB, HB),
    "monolith_w5": (CLIP, CLIP, HB, HB, AB), "monolith_e5": (SHELLS, SHOTGUN, SHELLS, HB),
    "monolith_w6": (AB, HB, HB), "monolith_e6": (CLIP, HB, HB, AB),
}
# Note #4: a sickly yellow-green glow round each monolith: the base and slab lit in that colour
# (UDMF lightcolor), and a slowly pulsing coloured light (UZDoom's PointLightPulseAttenuated, 9831:
# args red, green, blue, radius, second radius; angle = the pulse's period in tics) out in front of its
# face, 64 up. Dynamic lights need the game's lights on (the default).
GLOW_TINT = 0xC8F078
GLOW_LIGHT = 9831
GLOW_RGB = (150, 200, 40)
GLOW_RADIUS = (112, 80)
GLOW_PERIOD = 105         # 3 s


def build(m: MapBuilder) -> None:
    # Each sector is on the right (front) of its lines, going round it clockwise. North is "forward".
    # The car comes before the niche: both carry CAR_TAG.
    closet = m.sector("closet", floor=0, ceiling=LOW, light=CLOSET_LIGHT)
    m.sectors[closet.index]["id"] = CLOSET_TAG
    car = m.sector("car", floor=0, ceiling=LOW, light=CLOSET_LIGHT)
    m.sectors[car.index]["id"] = CAR_TAG
    # Note #24: the switch niche is all track metal (its floor, ceiling and side walls), the switch panel
    # itself kept.
    niche = m.sector("niche", floor=NICHE_FLOOR, ceiling=NICHE_TOP, light=NICHE_LIGHT, floor_tex=LIP_TOP,
                     ceiling_tex=TRACK)
    m.sectors[niche.index]["id"] = CAR_TAG
    # Ceilings from the mapper's editor save (2026-11-22 01:03): the mouth 192 high (was 256), the room
    # 192 high (was 384).
    mouth = m.sector("mouth", floor=-DROP, ceiling=-64, light=HALL_LIGHT)
    room = m.sector("room", floor=-DROP, ceiling=-64, light=HALL_LIGHT)
    # Fog (mapper, 2026-11-22): a grey-green haze (UDMF fadecolor) so the far end fades out; fogdensity
    # overrides the density UZDoom would work out from the light level (0-510, 0 = default). The mouth
    # has it too, so the fog doesn't start at a hard edge.
    for s in (mouth, room):
        fog(m, s)

    # The closet (note #6: twice as wide and long, was 64 x 128): 128 x 256, x -32 to 96, y -128 to
    # 128, the platform's opening (x 0-64) in the middle of its north wall, the start door in the
    # middle of its south wall behind the player, who faces north at the platform. Dark, lit only by
    # emergency light channels in its long walls.
    cx0, cx1, cy0, cy1 = CLOSET
    kx0, kx1, ky1 = COFFER
    coffer = m.sector("closet.coffer", floor=0, ceiling=COFFER_CEILING, light=CLOSET_LIGHT)
    m.sectors[coffer.index]["id"] = CLOSET_TAG      # breathes with the closet
    m.two_sided((kx0, ky1), (kx0, cy0), closet, coffer, "closet.coffer.edge_w")
    m.two_sided((kx1, ky1), (kx0, ky1), closet, coffer, "closet.coffer.edge_n")
    m.two_sided((kx1, cy0), (kx1, ky1), closet, coffer, "closet.coffer.edge_e")
    start_door(m, closet, coffer, (cx0, cy0), (cx1, cy0), (kx0, kx1))
    # Editor save 2026-11-22 01:42: the closet's far corners cut on the diagonal, (-32, 128) to
    # (-32, 104)-(-24, 120) and (96, 128) to (88, 120)-(96, 104).
    wall_with_channels(m, closet, (cx0, cy0), (cx0, cy1), "closet.wall_w", end=((-32, 104), (-24, 120)))
    m.wall((-24, 120), (-8, cy1), closet, "closet.wall_nw")
    back = m.two_sided((64, 128), (0, 128), car, closet, "car.back")
    m.sidedefs[m.linedefs[back]["sidefront"]]["texturebottom"] = TRACK
    m.wall((72, cy1), (88, 120), closet, "closet.wall_ne")
    wall_with_channels(m, closet, (cx1, cy1), (cx1, cy0), "closet.wall_e", start=((88, 120), (96, 104)))

    # The platform: 64 x 64 (y 128-192). Its side walls and the wall either side of the niche face
    # solid blocks (shaft_w, shaft_e: floor and ceiling at 0), so the shaft shows plain wall above
    # the starting floor and the track below it as the platform goes down.
    shaft_w = shaft_side(m, car, closet, "shaft_w", x_wall=0, x_out=-8, x_pillar=NICHE_X0)
    shaft_e = shaft_side(m, car, closet, "shaft_e", x_wall=64, x_out=72, x_pillar=NICHE_X1)
    m.player_start(32, cy0 + 24, angle=90)

    # The niche (x 8-56, y 192-200). The switch is its back wall: a two-sided line onto the mouth,
    # sealed while the niche's floor is up (the mouth's ceiling is at 0), the switch texture its
    # upper part, pegged to the niche's top so it stays up there. Floor_LowerByValue (20: tag, speed,
    # height), once, on CAR_TAG: the platform and the niche's floor go down together, and the niche
    # becomes the way through (48 wide, a 16 step up from the platform). The niche is the front side.
    lip = m.two_sided((NICHE_X0, 192), (NICHE_X1, 192), car, niche, "niche.mouth")
    m.sidedefs[m.linedefs[lip]["sidefront"]]["texturebottom"] = LIP_FACE   # the lip's face, from the platform
    for x, gid, other in ((NICHE_X0, "niche.side_w", shaft_w), (NICHE_X1, "niche.side_e", shaft_e)):
        a, b = ((x, 192), (x, 200)) if other is shaft_w else ((x, 200), (x, 192))
        side = m.two_sided(a, b, niche, other, gid, texture=TRACK)   # the niche's side walls (note #24)
        m.linedefs[side]["blocking"] = True
        m.sidedefs[m.linedefs[side]["sidefront"]]["texturebottom"] = TRACK
    switch = m.two_sided((NICHE_X0, 200), (NICHE_X1, 200), niche, mouth, "niche.switch")
    m.linedefs[switch].fields.update(special=20, arg0=CAR_TAG, arg1=CAR_SPEED, arg2=DROP, playeruse=True,
                                     dontpegtop=True)
    # The lip's other face: the passage's side of this line, below the niche's floor (16 once it's down).
    m.sidedefs[m.linedefs[switch]["sideback"]]["texturebottom"] = LIP_FACE
    front = m.sidedefs[m.linedefs[switch]["sidefront"]]
    front["texturetop"] = SWITCH_TEXTURE
    front["offsetx"] = 8     # the 64-wide texture's plate (x ~16-47) in the middle of the 48-wide niche
    front["offsety"] = 69    # its plate (rows ~70-102) fills the niche's 32 of height
    pulse = m.thing(9831, 32, 194, "niche.pulse", angle=SWITCH_PULSE_PERIOD)
    m.things[pulse].fields.update(height=16, arg0=SWITCH_PULSE_RGB[0], arg1=SWITCH_PULSE_RGB[1],
                                  arg2=SWITCH_PULSE_RGB[2], arg3=SWITCH_PULSE_RADIUS[0], arg4=SWITCH_PULSE_RADIUS[1])

    # The mouth: straight on from the platform, into the room, flaring out (editor save 2026-11-22 01:25:
    # its far corners from (0, 264) and (64, 264) out to MOUTH_W and MOUTH_E).
    m.two_sided((0, 200), (NICHE_X0, 200), shaft_w, mouth, "mouth.pillar_w")
    m.two_sided((NICHE_X1, 200), (64, 200), shaft_e, mouth, "mouth.pillar_e")
    # Note #10: a call switch at the bottom of the shaft, for completeness (in play you always arrive
    # from above): in a small niche in the mouth's west wall, beside the shaft, like the one up top.
    # The wall runs (0, 200) to (-64, 240), y = 200 - 5x/8: the niche's mouth (-16, 210)-(-48, 230) is on
    # it exactly, and (-5, -8) is exactly square to it, so every corner is a whole unit. Floor_MoveToValue
    # (37: tag, speed, height, 1 = negative) sends the platform (and the top niche's floor) to the
    # bottom, -256, once; already there, it does nothing.
    lower_switch_niche(m, mouth, (0, 200), MOUTH_W, ((-16, 210), (-48, 230)), (-5, -8))
    m.wall(MOUTH_E, (64, 200), mouth, "mouth.wall_e")
    m.two_sided(MOUTH_W, MOUTH_E, mouth, room, "mouth.edge")

    # The room, straight on from the mouth. Reshaped by the mapper in the editor: save 2026-11-22 01:03
    # (about 1000 deep, out of square; was 512 x 512), then 01:23 (wider and longer: about 750 x 1500).
    # 01:26: the east wall out to x 416-448, and the north wall a three-sided apse peaking at (192, 2080).
    sw, nw, ne, se = (-368, 288), (-384, 1792), (448, 1792), (416, 256)
    apse = ((-128, 2048), (192, 2080))

    m.wall(sw, nw, room, "room.wall_w")
    m.wall(nw, apse[0], room, "room.wall_n")
    m.wall(apse[0], apse[1], room, "room.wall_n2")
    m.wall(apse[1], ne, room, "room.wall_n3")
    m.wall(ne, se, room, "room.wall_e")
    m.wall(se, MOUTH_E, room, "room.wall_s2")
    m.wall(MOUTH_W, sw, room, "room.wall_s")

    for side, g in GUTTERS.items():
        gutter = m.sector(f"gutter_{side}", floor=-DROP - 8, ceiling=-64, light=HALL_LIGHT, floor_tex=GUTTER_FLAT)
        fog(m, gutter)
        for name, p, q in zip("wnes", g, g[1:] + g[:1]):
            m.two_sided(p, q, gutter, room, f"gutter_{side}.edge_{name}", texture=STONE)

    # The monoliths, in two rows (west row facing east, east row facing west).
    for r, x0 in enumerate(MONOLITH_ROWS):
        for i, y0 in enumerate(MONOLITH_YS):
            face = FACE
            monolith(m, room, f"monolith_{'we'[r]}{i + 1}", x0, y0, facing="e" if r == 0 else "w", face=face,
                     pair=i, switch=(i, "we"[r]) == SWITCH_OBELISK)


def hall_ceiling(m: MapBuilder, sector) -> None:
    """Note #27: a sector lit brighter than the hall (an altar, a monolith's base) whose ceiling is the
    hall's: its ceiling at the hall's light, so it doesn't show as a bright patch overhead."""
    m.sectors[sector.index].fields.update(lightceiling=HALL_LIGHT, lightceilingabsolute=True)


def fog(m: MapBuilder, sector) -> None:
    m.sectors[sector.index].fields.update(fadecolor=HALL_FOG, fogdensity=HALL_FOG_DENSITY)


# A slab's outline in its own coordinates (u across it, 0-32; v along the row, 0-80), clockwise,
# starting with its back. Note #3: the aisle-side corners are cut (12 across, 16 along: 20 on the
# diagonal), so the carved face wraps round without a hard edge: side 20 + corner 20 + face 48 +
# corner 20 + side 20 = the face texture's 128, centred on the face. The back is plain stone.
SLAB_FACING_E = ((0, 0), (0, 80), (20, 80), (32, 64), (32, 16), (20, 0))
SLAB_FACING_W = ((32, 80), (32, 0), (12, 0), (0, 16), (0, 64), (12, 80))
SLAB_PARTS = ("back", "side_a", "corner_a", "face", "corner_b", "side_b")


def monolith(m: MapBuilder, room, gid: str, x0: float, y0: float, *, facing: str, face: str, pair: int,
             switch: bool) -> None:
    """A carved slab in x0..x0+32, y0..y0+80 inside a plain sleeve 8 wider all round, on a base 16 wider
    all round. Note #8: at first the sleeve fills the space up to the ceiling: a featureless pillar. When
    the player passes this pair, zscript.zs (CacobeliskObelisks) lowers the sleeve to the altars' height, 8 above the base (note #23; it sinks
    slowly, grinding), uncovering the slab with its carving wrapped round its `facing` side ("e" or "w")
    and (the `switch` obelisk only, note #11) a cacodemon on top, and switches the glow on. The sleeve and the space above the slab
    reach up into a slot in the ceiling (SLEEVE_TOP), so the sleeve sinks a long way before the carving
    shows (note #9).

    Heights: the base is a step (8 up); the slab stands 128 above it (one face texture), its top 104
    under the slot's top, room for the cacodemon. Tags: the sleeve SLEEVE_TAG + pair; the slab CACO_TAG +
    pair if it gets a cacodemon (the script puts it there); the glow light's thing id GLOW_TID + pair.
    The slab's and sleeve's walls are lower textures, seen from the sleeve and the base. Each sector is
    on the right (front) of its lines, going round it clockwise."""
    floor = -DROP + BASE_STEP
    top = floor + 128
    base = m.sector(f"{gid}.base", floor=floor, ceiling=-64, light=BASE_LIGHT, floor_tex="FLOOR7_2")
    hall_ceiling(m, base)
    sleeve = m.sector(f"{gid}.sleeve", floor=SLEEVE_TOP, ceiling=SLEEVE_TOP, light=BASE_LIGHT, floor_tex="FLOOR7_2")
    slab = m.sector(gid, floor=top, ceiling=SLEEVE_TOP, light=BASE_LIGHT, floor_tex="FLOOR7_2")
    # No grinding while it sinks: the "Silence" sound sequence (note #13; the mapper, again: "still too
    # loud"). Not the UDMF `silent` flag, used here at first: that silences the things in the sector
    # (the script's own rumble, which sat in it), not the sector's movement.
    m.sectors[sleeve.index].fields.update(id=SLEEVE_TAG + pair, user_scenery=True, soundsequence="Silence")
    m.sectors[slab.index]["user_scenery"] = True
    if switch:
        m.sectors[slab.index]["id"] = CACO_TAG + pair
    for s in (base, sleeve, slab):
        fog(m, s)
        m.sectors[s.index]["lightcolor"] = SWITCH_GLOW_TINT if switch else GLOW_TINT
    # Note #14: the slot in the ceiling (above the sleeve and the slab) is marble all over, its ceiling
    # too, and dark: only its ceiling and walls are darkened (lightceiling here, light on the slot's
    # walls below), not the sectors themselves, whose light also falls on the carved face.
    for s in (sleeve, slab):
        m.sectors[s.index].fields.update(textureceiling=STONE, lightceiling=SLOT_DARK)
    altar(m, room, gid, x0, y0, facing)
    # The glow: a pulsing light 24 out from the middle of the face, 64 up; off until the reveal.
    gx = x0 + 32 + 24 if facing == "e" else x0 - 24
    rgb = SWITCH_GLOW_RGB if switch else GLOW_RGB
    t = m.thing(GLOW_LIGHT, gx, y0 + 40, f"{gid}.glow", angle=SWITCH_GLOW_PERIOD if switch else GLOW_PERIOD)
    m.things[t].fields.update(height=64, arg0=rgb[0], arg1=rgb[1], arg2=rgb[2],
                              arg3=GLOW_RADIUS[0], arg4=GLOW_RADIUS[1], id=GLOW_TID + pair, dormant=True)
    b = ((x0 - 16, y0 - 16), (x0 - 16, y0 + 96), (x0 + 48, y0 + 96), (x0 + 48, y0 - 16))
    for name, p, q in zip("wnes", b, b[1:] + b[:1]):
        m.two_sided(p, q, base, room, f"{gid}.base.edge_{name}", texture=STONE)
    c = ((x0 - 8, y0 - 8), (x0 - 8, y0 + 88), (x0 + 40, y0 + 88), (x0 + 40, y0 - 8))
    for name, p, q in zip("wnes", c, c[1:] + c[:1]):
        ln = m.two_sided(p, q, sleeve, base, f"{gid}.sleeve.edge_{name}", texture=STONE)
        # The sleeve's side of these lines only ever shows the slot's walls (its upper part).
        m.sidedefs[m.linedefs[ln]["sidefront"]]["light"] = SLOT_DARK
    pts = [(x0 + u, y0 + v) for u, v in (SLAB_FACING_E if facing == "e" else SLAB_FACING_W)]
    sides = []
    for k, part in enumerate(SLAB_PARTS):
        p, q = pts[k], pts[(k + 1) % len(pts)]
        ln = m.two_sided(p, q, slab, sleeve, f"{gid}.{part}", texture=STONE)
        sides.append((m.sidedefs[m.linedefs[ln]["sideback"]], p, q))
    # Seen from outside (the sleeve side), a line runs from its end (on the left) to its start, so the
    # texture is laid on the lines after the back in reverse order, each starting where the last ended.
    along = 0
    for side, p, q in reversed(sides[1:]):
        side["texturebottom"] = face
        if along:
            side["offsetx"] = along
        along += round(((q[0] - p[0]) ** 2 + (q[1] - p[1]) ** 2) ** 0.5)


def lower_switch_niche(m: MapBuilder, mouth, a, b, mouth_pts, into) -> None:
    """The mouth's wall a -> b (the mouth on its right) with the bottom call switch (note #10) in a niche
    at mouth_pts (two points on the wall), `into` the wall by the vector `into`: sill 16 above the
    mouth's floor, 32 high, lit like the top niche, SW1GRAY's plate on its back wall. Lines run
    clockwise round each sector, so it's on their right."""
    p0, p1 = mouth_pts
    q0, q1 = (p0[0] + into[0], p0[1] + into[1]), (p1[0] + into[0], p1[1] + into[1])
    floor = -DROP + NICHE_FLOOR
    niche = m.sector("mouth.call_niche", floor=floor, ceiling=floor + NICHE_TOP - NICHE_FLOOR,
                     light=CALL_NICHE_LIGHT)
    m.sectors[niche.index]["user_scenery"] = True   # too small to enter: decoration (movement check)
    fog(m, niche)
    m.wall(a, p0, mouth, "mouth.wall_w")
    m.two_sided(p0, p1, mouth, niche, "mouth.call_niche.mouth")
    m.wall(p1, b, mouth, "mouth.wall_w2")
    m.wall(p0, q0, niche, "mouth.call_niche.side_a")
    back = m.wall(q0, q1, niche, "mouth.call_niche.switch", texture=SWITCH_TEXTURE)
    m.wall(q1, p1, niche, "mouth.call_niche.side_b")
    m.linedefs[back].fields.update(special=37, arg0=CAR_TAG, arg1=CAR_SPEED, arg2=DROP, arg3=1, playeruse=True)
    width = ((q1[0] - q0[0]) ** 2 + (q1[1] - q0[1]) ** 2) ** 0.5
    side = m.sidedefs[m.linedefs[back]["sidefront"]]
    side["offsetx"] = round(32 - width / 2)   # SW1GRAY's plate (x ~16-47) in the middle of the back wall
    side["offsety"] = 69                      # its plate (rows ~70-102) fills the niche's 32 of height


def altar(m: MapBuilder, room, gid: str, x0: float, y0: float, facing: str) -> None:
    """Note #16: the low altar in front of monolith `gid` (slab at x0..x0+32, y0..y0+80, its face on the
    `facing` side), 16 out from the base towards the aisle, with its pickups (ALTAR_ITEMS) on top."""
    ax0 = x0 + 64 if facing == "e" else x0 - 56           # the base reaches x0 + 48 / x0 - 16
    ax1 = ax0 + 24
    ay0, ay1 = y0 + 16, y0 + 64
    top = m.sector(f"{gid}.altar", floor=-DROP + 16, ceiling=-64, light=BASE_LIGHT, floor_tex="FLOOR7_2")
    hall_ceiling(m, top)
    fog(m, top)
    a = ((ax0, ay0), (ax0, ay1), (ax1, ay1), (ax1, ay0))
    for name, p, q in zip("wnes", a, a[1:] + a[:1]):
        m.two_sided(p, q, top, room, f"{gid}.altar.edge_{name}", texture=STONE)
    # Scattered (the mapper, 2026-11-22: "each feels uniquely scattered"): each item at its own spot and
    # facing on the altar, picked from a hash of its gid, so it's the same on every build. Kept 4 in from
    # the edges and at least 10 from the altar's other items (up to five on an altar now).
    placed: list[tuple[float, float]] = []
    for k, type_ in enumerate(ALTAR_ITEMS.get(gid, ())):
        item = f"{gid}.altar.item_{k + 1}"
        h = hashlib.sha256(item.encode()).digest()
        for tries in range(32):
            b = h[2 * tries % 32: 2 * tries % 32 + 2]
            x = ax0 + 4 + b[0] % (ax1 - ax0 - 8)
            y = ay0 + 4 + b[1] % (ay1 - ay0 - 8)
            if all((x - px) ** 2 + (y - py) ** 2 >= 10 ** 2 for px, py in placed):
                break
        placed.append((x, y))
        m.thing(type_, x, y, item, angle=h[-1] * 360 // 256)


def shaft_side(m: MapBuilder, car, closet, gid: str, *, x_wall: float, x_out: float, x_pillar: float):
    """The solid block along one side of the shaft: a strip 8 thick behind the platform's side wall
    (x_wall, y 128-192) and the pillar beside the niche (y 192-200, out to x_pillar). Floor and ceiling
    at 0, so the platform's side shows its upper texture (wall) above 0 and its lower texture (the
    track) below. Its lines with the platform are blocking, front side the platform; its south end
    is part of the closet's north wall (blocking, the closet sees it as wall above 0)."""
    s = m.sector(gid, floor=TRACK_PREVIEW, ceiling=TRACK_PREVIEW, light=128)
    west = x_out < x_wall
    # The outline, clockwise (the block on the right of each line).
    if west:
        pts = [(x_out, 128), (x_out, 200), (x_wall, 200), (x_pillar, 200), (x_pillar, 192), (x_wall, 192),
               (x_wall, 128)]
    else:
        pts = [(x_wall, 128), (x_wall, 192), (x_pillar, 192), (x_pillar, 200), (x_wall, 200), (x_out, 200),
               (x_out, 128)]
    car_lines = {((x_wall, 192), (x_wall, 128)), ((x_wall, 128), (x_wall, 192)),
                 ((x_pillar, 192), (x_wall, 192)), ((x_wall, 192), (x_pillar, 192))}
    done = {((x_wall, 200), (x_pillar, 200)), ((x_pillar, 200), (x_wall, 200)),   # onto the mouth
            ((x_pillar, 200), (x_pillar, 192)), ((x_pillar, 192), (x_pillar, 200))}  # onto the niche
    for i, (a, b) in enumerate(zip(pts, pts[1:] + pts[:1])):
        if (a, b) in done:
            continue
        if (a, b) in car_lines:
            # The car's side of it, front: reverse the block's clockwise line.
            ln = m.two_sided(b, a, car, s, f"{gid}.car_{i}")
            m.linedefs[ln]["blocking"] = True
            m.sidedefs[m.linedefs[ln]["sidefront"]]["texturebottom"] = TRACK
        elif a[1] == b[1] == 128:
            ln = m.two_sided(a, b, s, closet, f"{gid}.closet")
            m.linedefs[ln]["blocking"] = True
        else:
            m.wall(a, b, s, f"{gid}.wall_{i}")
    return s


def wall_with_channels(m: MapBuilder, closet, a, b, gid: str, *, start=None, end=None) -> None:
    """A straight closet wall a -> b (the closet on its right) with emergency light channels in it
    (note #6): at CHANNEL_AT along the wall from a, each 16 wide, 8 deep, floor to ceiling, a red
    light tube (LITERED) at the back, DOORTRAK sides, a little brighter and tinted red, and a dim red
    light in front that spills onto the floor. start / end: (corner, point on the wall) when the wall's
    first or last stretch comes in from a cut corner instead of from a or to b. Each sector is on the
    right of its lines, clockwise."""
    (ax, ay), (bx, by) = a, b
    length = ((bx - ax) ** 2 + (by - ay) ** 2) ** 0.5
    dx, dy = (bx - ax) / length, (by - ay) / length
    nx, ny = -dy, dx                                  # left of a -> b: into the wall

    def at(along: float, out: float = 0) -> tuple[float, float]:
        return (round(ax + dx * along + nx * out), round(ay + dy * along + ny * out))

    if start:
        m.wall(start[0], start[1], closet, f"{gid}_0")
    start = start[1] if start else a
    for i, d in enumerate(CHANNEL_AT):
        p0, p1 = at(d - 8), at(d + 8)
        q0, q1 = at(d - 8, 8), at(d + 8, 8)
        name = f"{gid}.channel_{i + 1}"
        dim = (gid, i + 1) in CHANNEL_DIM
        ch = m.sector(name, floor=0, ceiling=LOW, light=CHANNEL_DIM_LIGHT if dim else CHANNEL_LIGHT)
        m.sectors[ch.index]["user_scenery"] = True   # too narrow to enter: decoration (movement check)
        m.sectors[ch.index]["lightcolor"] = CHANNEL_TINT
        m.wall(start, p0, closet, f"{gid}_{i + 1}")
        m.two_sided(p0, p1, closet, ch, f"{name}.mouth")
        m.wall(p0, q0, ch, f"{name}.side_a", texture="DOORTRAK")
        m.wall(q0, q1, ch, f"{name}.tube", texture=CHANNEL_TEXTURE)
        m.wall(q1, p1, ch, f"{name}.side_b", texture="DOORTRAK")
        x, y = at(d, -12)
        t = m.thing(CHANNEL_GLOW, x, y, f"{name}.glow")
        rgb = CHANNEL_DIM_RGB if dim else CHANNEL_RGB
        m.things[t].fields.update(height=32, arg0=rgb[0], arg1=rgb[1], arg2=rgb[2], arg3=CHANNEL_RADIUS)
        start = p1
    last = len(CHANNEL_AT) + 1
    if end:
        m.wall(start, end[0], closet, f"{gid}_{last}")
        m.wall(end[0], end[1], closet, f"{gid}_{last}b")
    else:
        m.wall(start, b, closet, f"{gid}_{last}")


def start_door(m: MapBuilder, closet, coffer, a, b, coffer_x) -> None:
    """The closet's south wall (a -> b along y = const, closet on its right; a west of b): the
    level-start door (64 wide) in its middle, in a recess 8 deep, DOORTRAK on its sides, a lintel
    above (the recess is 56 high, the door texture's bottom on the floor). It doesn't open."""
    (ax, ay), (bx, _) = a, b
    mid = (ax + bx) / 2
    p0, p1 = (mid - 32, ay), (mid + 32, ay)
    q0, q1 = (mid - 32, ay - 8), (mid + 32, ay - 8)
    recess = m.sector("closet.start_door", floor=0, ceiling=56, light=CLOSET_LIGHT)
    # The coffer (the raised ceiling panel) reaches this wall between coffer_x: it's the sector in front
    # of the door and the wall beside it there; the closet's border is beyond.
    k0, k1 = (coffer_x[0], ay), (coffer_x[1], ay)
    m.wall(b, k1, closet, "closet.wall_s2")
    m.wall(k1, p1, coffer, "closet.coffer.wall_s2")
    m.two_sided(p1, p0, coffer, recess, "closet.start_door.mouth")
    m.wall(p0, k0, coffer, "closet.coffer.wall_s")
    m.wall(k0, a, closet, "closet.wall_s")
    m.wall(q0, p0, recess, "closet.start_door.side_w", texture="DOORTRAK")
    door = m.wall(q1, q0, recess, "closet.start_door.door", texture=START_DOOR)
    m.linedefs[door]["dontpegbottom"] = True
    m.wall(p1, q1, recess, "closet.start_door.side_e", texture="DOORTRAK")
