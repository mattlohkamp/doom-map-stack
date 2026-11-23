"""Cacobelisk (was test2): the generator for this map. `.\\dms.ps1 build cacobelisk` turns it into TEXTMAP."""

import hashlib

from dms.gen import WALL, MapBuilder

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
# Note #29: the entry secret. Turning round at the start, the player sees a small glowing panel inset
# above the start door (TARGET_*: a slot 16 wide, 8 high and 8 deep in a lintel beam that now stands 8
# out from the door's recess); shooting it (an impact line, Door_Open) opens a panel in the closet's east
# wall between its 2nd and 3rd channels, the player's left, hiding light amplification goggles that count
# as the map's secret when taken (UDMF countsecret).
SECRET_TAG = 3
# Note #31: the target is the flesh switch, SW1SKIN (the engine turns it to SW2SKIN when shot), shrunk to
# a quarter (UDMF scale 4: 64 x 128 becomes 16 x 32) so its fleshy plate (rows ~58-100) fits the slot,
# now 12 high: the top of the texture pegged to the slot's top, moved up 14 (56 rows) to the plate.
# (At first a blue light panel, LITEBLU4.)
# Note #32: the other way round: the eye open at first (SW2SKIN: a blue eye in the flesh), closed once
# shot (SW1SKIN; switch pairs swap either way), as if the player blinded it to open the secret; the eye
# centred in the slot. Scale 2 (the slot's 16 x 12 shows 32 x 24 of the texture), the window moved to
# columns 16-48 and rows 63-87, round the eye at about (32, 75). Note #33: the offsets are in texture
# pixels, not world units (8 / 31.5 showed rows 31-55, plain flesh above the eye).
# The mapper, 2026-11-22 (after note #34): the target is the red valve wheel of BROWNWEL instead (a
# bullseye), unscaled: the slot's 16 x 12 shows columns 166-182, rows 4-16, round the upper wheel
# (pixels 168-180 x 5-15). It glows (full bright, the red pulse in front) until it's shot; then
# zscript.zs (CacobeliskElevator) puts its wall back to the closet's light and turns the pulse off
# (thing id TARGET_TID). (Before: the flesh switch's eye, SW2SKIN closing to SW1SKIN.)
TARGET_TEXTURE = "BROWNWEL"
TARGET_TOP = 72                         # note #40: the coffer's height, 16 above the recess's 56 (was 68)
TARGET_OFFSET = (166.0, 5.0)            # texture pixels; note #40: the wheel sat low, cut off at the bottom
TARGET_TID = 301
TARGET_RGB = (200, 60, 50)              # a faint red pulse
TARGET_RADIUS = (10, 20)
TARGET_PERIOD = 35
SECRET_PANEL = ((96, -12), (96, -52))   # the panel in the east wall (40 wide; 4 of wall either side)
# The alcove behind it: x 104-144 (the panel is 8 thick). Note #31: was 24 deep, with the goggles 20
# behind the wall, close enough to pick up through the shut panel (pickups go by touching boxes); now
# 40 deep, the goggles 36 behind the wall, out of reach until it opens.
SECRET_ALCOVE_X = 144
LIGHT_AMP = 2024                        # note #74: partial invisibility (was 2045, light amplification)
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
# Note #46: the west gutter meanders like the east stream, nearer the obelisk row between the obelisks
# and further off beside them (its inner edge, south to north; it reaches the west wall, note #36).
# Note #47: both channels join in front of the elevator's landing: a channel (CROSSING, y 270-327)
# runs from the west gutter, which now reaches round the south-west corner along the south wall, across
# the aisle to the east stream. The player crosses it on a low bridge (BRIDGE: x -40 to 104; a step up,
# the obelisk bases' height), a 3D floor (Sector_Set3DFloor from a control sector outside the map), so
# the water runs on beneath it.
GUTTER_W_INNER = ((-180, 327), (-230, 380), (-196, 440), (-190, 505), (-150, 545), (-140, 600), (-190, 655),
                  (-236, 760), (-270, 860), (-250, 960), (-205, 1050), (-160, 1120), (-170, 1180),
                  (-215, 1240), (-280, 1330), (-300, 1420), (-240, 1500), (-200, 1560), (-190, 1630),
                  (-150, 1690), (-200, 1730), (-288, 1760))
GUTTER_W_TOP = 1760          # its north end
CROSSING = (270, 327)        # the crossing channel's south and north edges
CROSSING_SW = (-56, 270)     # where its south edge turns to meet the south wall (west of the mouth)
CROSSING_WALL_X = -72        # ... at this x on the south wall
BRIDGE = (-40, 104)
BRIDGE_TAG = 500
BRIDGE_SLAB = (-252, -248)   # the slab's underside and top (the bases' height, 8 above the floor)
BRIDGE_CONTROL = (720, -96)  # the control sector's corner (32 x 32, outside the map)
# Note #36: all round the hall the walls are lifted off the floor: a gap 16 high (DRAIN_TOP) at their
# foot shows a dark channel of water behind a grate (DRAIN_GRATE), out of view; the gutters now reach the
# walls (their lips gone), so their water runs under them into it. The channel runs behind every wall
# of the room (not the mouth), DRAIN_DEPTH deep, its floor 8 below the gutters'.
# Note #45: at the end of the hall, in the apse's middle wall, a great doorway (DOORWAY wide, its
# opening DOOR_HIGH high, a marble lintel above), its two leaves (BIGDOOR7, carved skulls) stuck ajar,
# half ruined: swung in by LEAF_ANGLES, a gap of about 15 between them to glimpse the dim vestibule
# beyond, too narrow to pass. A smaller door (WOODMET1, 64 x 128, Door_Raise) is set into the left
# leaf: the way on. The leaves are solid (floor = ceiling at the opening's top), LEAF_THICK thick.
# The vestibule: VESTIBULE deep behind the wall, wider than the doorway, dim, a red glow at its back.
DOORWAY = 192
DOOR_HIGH = 128
LEAF_ANGLES = (5, 8)            # degrees: the left leaf, the right one; note #48: a smaller gap (were 12, 20)
LEAF_SKULLS = 64                # BIGDOOR7's skull pile, centred on each leaf (note #49)
# Note #53: the left leaf (the one with the small door) plain, no skulls: BIGDOOR5 (wood and iron
# bands); the right one keeps BIGDOOR7. The small door a different thing altogether, so it reads as a
# door: DOOR1 (a brass-framed metal door, exactly 64 x 72; was WOODMET1, which looked like the leaf).
LEAF_TEXTURES = ("BIGDOOR5", "BIGDOOR7")
# Note #57: BIGDOOR6 (wood, iron bands, one skull) for the small door instead, its skull centred on the
# 64 x 72 panel (offsets in texture pixels on the lower part: columns 32-96, rows 26-98 of 128 x 112).
WICKET_TEXTURE = "BIGDOOR6"
WICKET_OFFSET = (32, 26)
# Note #58: the small door set into the leaf, in its own rusted metal frame: a recess FRAME[0] deep in
# the leaf's face, FRAME[1] wider than the door each side and FRAME[2] taller, lined with the elevator
# track's rusty metal (SUPPORT3); the door at its back. Posts of the frame stand either side of the door
# through the rest of the leaf.
FRAME = (4, 4, 4)
FRAME_TEXTURE = "SUPPORT3"
LEAF_THICK = 12
# Note #50: the small door is human-sized (64 x 72) and the leaf goes on above it: its panel (WOODMET1)
# sinks into the floor (Plat_DownWaitUpStay on WICKET_TAG) and comes back up; above it the leaf's
# texture, as a lintel. Centred in the left leaf.
WICKET = (15, 79)               # along the left leaf from its hinge
WICKET_HIGH = 72
WICKET_TAG = 501
# Note #72: a pinky couldn't follow into the vestibule (a 76 opening beside the right leaf's hinge, then
# a tight turn). Now twice as deep, rounded, its north-east side curving back down to a wide opening
# onto the passage (about 122, slanted). Its outline from the west jamb's back corner round to the
# east one's, (u, d) in the doorway's frame; the passage's first cross-section is the opening.
VESTIBULE_OUTLINE = ((-112, 16), (-128, 112), (-88, 184), (16, 208), (104, 184), (136, 136))
VESTIBULE = (224, 96)           # width, depth (from the wall); note #63: smaller (was 256 x 176), the
                                # passage leading on from its east side
VESTIBULE_LIGHT = 72
VESTIBULE_GLOW = (180, 50, 24, 112)
# Note #59: two imps waiting behind the great doors, facing them. (u, d) in the doorway's frame. Note #62:
# not ambush (deaf) any more: shooting one through the gap left the other asleep; now gunfire wakes both.
IMP = 3001
# Note #61: a lost soul hidden high up behind the 2nd west obelisk (seen from the aisle at its south end,
# its pillar hides it), revealed when that pillar sinks; it waits until it sees the player (ambush).
LOST_SOUL = 3006
HIDDEN_SOUL = (-160, 810, 96)      # x, y, height above the floor
VESTIBULE_IMPS = ((-56, 64), (60, 72))
# Note #63: through the small door, a cramped, twisting passage of mossy stone (A-MOSRK2 on walls, floor
# and ceiling) leaves the vestibule on the right (east), bends north and gradually steps up, 8 at a
# time; dimly lit, with torches (short red, 57) in niches in its walls. PASSAGE: its cross-sections in the
# doorway's frame (u, d), each (left, right) going along it; the first is the opening in the vestibule's
# east wall. PASSAGE_STEP: from which piece the floor starts to rise. It ends, for now, at a wall.
PASSAGE = (((136, 136), (112, 16)), ((176, 96), (176, 32)), ((232, 120), (256, 56)), ((264, 176), (320, 136)),
           ((272, 248), (336, 232)), ((256, 320), (320, 320)), ((264, 392), (328, 384)),
           ((288, 456), (344, 432)), ((304, 520), (360, 504)),
           # Note #65: on, twisting back towards the first room (east, then south, along the hall's
           # north-east side), the pieces longer, wider and taller as it goes, so it opens out.
           ((352, 600), (416, 560)), ((440, 648), (480, 560)), ((560, 656), (560, 544)),
           ((680, 616), (624, 496)), ((728, 480), (600, 440)), ((736, 320), (592, 320)),
           ((728, 160), (568, 176)))      # editor save 22:36: from here, stairs down to the cistern
PASSAGE_STEP = 2
# Note #75: the hall's fog (which fills the vestibule) thins out gradually along the passage's first
# PASSAGE_FOG_PIECES pieces instead of stopping at its mouth.
PASSAGE_FOG_PIECES = 6
# Note #66: a pinky (radius 30) couldn't follow the player through the first, narrowest stretch (58-64):
# every cross-section is widened about its middle to at least PASSAGE_MIN_WIDE (the opening onto the
# vestibule stays as it is: 76).
PASSAGE_MIN_WIDE = 128       # note #68: still too tight at the bends for pinkies (was 88); monsters must path
                             # to the player (docs/map-design-notes.md), and Doom's move in 8 directions


def _widened(sections):
    import math
    out = [sections[0]]
    for l, r in sections[1:]:
        w = math.hypot(r[0] - l[0], r[1] - l[1])
        if w >= PASSAGE_MIN_WIDE:
            out.append((l, r))
            continue
        cx, cy = (l[0] + r[0]) / 2, (l[1] + r[1]) / 2
        k = PASSAGE_MIN_WIDE / w
        out.append(((round(cx + (l[0] - cx) * k, 1), round(cy + (l[1] - cy) * k, 1)),
                    (round(cx + (r[0] - cx) * k, 1), round(cy + (r[1] - cy) * k, 1))))
    return tuple(out)


PASSAGE_RISE_END = 9            # the floor rises 8 a piece up to here; note #77: then goes down 16 a piece
PASSAGE_HIGH = 88               # its height at first; from piece 8 on, 16 more each piece (note #65)
PASSAGE_LIGHT = 80
PASSAGE_TEXTURE = "A-MOSRK2"
TORCH = 57
# Niches (piece, side "l"/"r"): 24 wide, NICHE_DEEP deep, NICHE_HIGH high, in the middle of that wall.
# Note #70: pinkies still stuck at a bend. The niches had a sill 24 up and were 48 high: a monster (56
# tall) brushing a niche's mouth was stopped (too little headroom), and the torch (radius 16) stuck out
# of the 12-deep niche, one right on a bend's inside corner. Now the niches start at the floor, 72 high,
# 24 deep, the torch 14 in (wholly inside), and torches are on the outside of the bends.
NICHE_DEEP, NICHE_HIGH, NICHE_TORCH_IN = 24, 72, 14
PASSAGE_TORCHES = ((1, "l"), (3, "r"), (5, "l"), (7, "l"), (9, "l"), (11, "l"), (13, "r"), (14, "l"))
# Note #65: a few pinkies in the wider stretch, imps behind them: (piece, type, along 0-1, across 0-1 from
# the left), all facing back up the passage.
PINKY = 3002
# Note #69: a cache of shotgun ammo on the right just into the passage: a box of shells (20). Note #73:
# on a shelf in a niche in the right wall, not on the floor; and 2049 (2048, used at first, is a box of
# bullets). Shelves (piece, side, thing): a niche 48 wide, 24 deep, its floor 32 up, 24 high, lit as the
# passage (note #76); the item 12 in, so the player can reach it from the passage.
SHELL_BOX = 2049
PASSAGE_ITEMS = ()
PASSAGE_SHELVES = ((1, "r", SHELL_BOX),)   # the 2nd piece: the 1st's right wall is right against the hall's
# Note #67: spread out, one pinky a piece (two shared a piece, wedged side by side).
# Note #80: the 2nd pinky at the passage's peak (piece 9, where it starts down), away from the others.
PASSAGE_MONSTERS = ((11, PINKY, 0.5, 0.4), (9, PINKY, 0.5, 0.5), (13, PINKY, 0.3, 0.5),
                    (13, IMP, 0.85, 0.3), (14, IMP, 0.5, 0.7))
DRAIN_TOP = -DROP + 16
DRAIN_FLOOR = -DROP - 16
DRAIN_DEPTH = 96          # note #39: deep enough that its far wall is out of sight (was 16)
DRAIN_LIGHT = 32          # note #39: darker (was 64)
DRAIN_GRATE = "MIDVINE1"
# Note #77 and the mapper's editor save (22:36): the passage goes down, in CISTERN_STEPS steps, into a big
# dark room east of the hall (the cistern: CISTERN_EAST, its east and south walls as drawn), whose west
# wall is the far side of the drain behind the hall's east wall. That wall, facing the obelisk hall, is
# all water pouring down (SFALL: the gutter's NUKAGE falling), above and below the slot through the drain
# (32 high, 96 deep), and the floor is flooded (the player wades). From down here the player looks up
# through the slot and the vines into the obelisk hall. Very dark, very foggy.
CISTERN_FLOOR = -DROP - 64
CISTERN_TOP = -128
CISTERN_EAST = ((768, 1760), (832, 192))       # its north-east and south-east corners (editor save)
# Note #82: three spectres (shadow pinkies, 58) along the cistern, ambush, facing the way the player comes
# down (north).
SPECTRE = 58
CISTERN_SPECTRES = ((650, 1350), (690, 880), (660, 430))
CISTERN_LIGHT = 40
# Note #79: grey, the hall's own fog (was a near-black 0x101810 at 420: from far off the black looked
# wrong), so through the grate it all fades uniformly to grey; the drains share it (note #78).
CISTERN_FOG = (HALL_FOG, HALL_FOG_DENSITY)       # the drains (seen from the hall through the vines)
# Note #84: down in the cistern itself (and the stairs to it), less fog and darker: a near-black fog,
# thinner, so the spectres don't stand out against grey mist. The drains keep the grey (note #79).
CISTERN_DARK_FOG = (0x080808, 200)
CISTERN_DARK_LIGHT = 32
CISTERN_FALL = "SFALL1"
CISTERN_STEPS = 4
PASSAGE_END = {}   # note #37 (the mapper): hanging vines as the grate
# The mapper, 2026-11-22: hints that the switch obelisk is special. The east gutter turns violet towards
# it, as if something from it seeps into the water: the gutter cut across at these y (where its slanted
# edges fall on whole units: x moves 1 every 45), each piece desaturated and tinted (UDMF desaturation,
# color_floor: the green goes grey, then violet) more strongly as it nears the obelisk (y 1520-1600).
GUTTER_E_CUTS = (1085, 1220, 1355, 1490, 1670)
# Editor save 2026-11-22 21:37: the east gutter's south end reshaped by the mapper into a winding stream:
# from the room's south-east corner it runs west along the room's south wall to the mouth's corner,
# then north, swinging out round the first two obelisks (in front of e1, between e1 and e2) and back
# towards the wall up to its first cut, which now runs from (240, 1088); the second cut from (256, 1184).
# The west side, south to north, the gutter on its right (east).
# Note #36: the stream now starts at the south wall (DRAIN), its south edge along it from the room's
# south-east corner to x GUTTER_E_S0_X, then the mapper's line north from (144, 232).
GUTTER_E_S0_X = 152
GUTTER_E_WEST = ((144, 232), (138, 270), (129, 327), (120, 384), (248, 376), (256, 512), (192, 544), (168, 616),
                 (216, 648), (272, 656), (280, 768), (256, 856), (248, 936), (240, 1088))
GUTTER_E_WEST_CUTS = {1085: (240, 1088), 1220: (256, 1184)}   # where a cut meets the west side, if moved
# Note #35: the switch obelisk leaks violet from its back. Note #38: not the whole back as a waterfall
# (that read as a blue wall): it spills from a slit low on the back of its sleeve (SLIT: 16 wide, 32 high
# from the base, 4 deep, liquid falling down its back wall), then over the base's step into a rivulet
# that spreads across the walkway into the gutter (part of the gutter's 5th piece, full violet; its
# head is the 16 of the base's edge below the slit). The fall is the blue waterfall (WFALL) in sectors
# desaturated and tinted violet, so it comes out violet (coloradd on the base's own walls didn't show).
VIOLET_FALL = "WFALL1"
VIOLET = 0x8A10FF                 # note #41: saturated (was 0xB060FF, which came out a lavender grey)
SLIT = (32, 48, 4, 32)            # along the back from the slab's y0: 32-48; 4 deep; 32 high above the base
SLIT_TAG = 400                    # zscript.zs opens it upwards as the sleeve sinks
RIVULET = {}                      # the gutter piece the rivulet belongs to (set by violet_gutter)
GUTTER_E_WEST_EXTRA = {4: ((347, 1535), (240, 1552), (240, 1568), (348, 1580))}
GUTTER_E_SHARED = {((240, 1552), (240, 1568)),   # built by monolith(): the base's edge under the slit
                   ((138, 270), (129, 327))}     # built by west_water(): where the crossing channel joins
# Note #41: "lose the grey-out": the colours were pale (lots of green in them), so the desaturated water
# came out grey; now saturated violets (were 0xE8D8F0, 0xD8B8F0, 0xC890F0, 0xB060FF, 0xC080FF).
GUTTER_E_VIOLET = ((0.0, None), (0.25, 0xD8A0FF), (0.5, 0xC070FF), (0.75, 0xA040FF), (1.0, 0x8A10FF),
                   (0.9, 0x9A30FF))   # (desaturation, floor colour) per piece, south to north
# And a trail of blood on the floor (Doom's pools of blood and brains drawn as silhouettes), sparse at
# first and denser towards the obelisk's altar, where a dead marine lies. Note #30: first a glowing
# violet (renderstyle addstencil, 0xC020FF), "too stark": now the floor's own dark grey (FLOOR4_8,
# about 0x333333), a little darker and with a faint violet cast, a stain more than a glow; the pools
# behind the obelisk gone.
POOL_BLOOD, POOL_BLOOD2, POOL_BRAINS = 79, 80, 81
TRAIL_COLOUR = 0x2A2232
DEAD_MARINE = 15
DEAD_MARINE_AT = (100, 1572, 200)   # x, y, angle: on the aisle side of the switch obelisk's altar
VIOLET_TRAIL = (
    (20, 1060, POOL_BRAINS), (44, 1190, POOL_BLOOD2), (60, 1300, POOL_BLOOD), (82, 1390, POOL_BRAINS),
    (96, 1450, POOL_BLOOD2), (112, 1490, POOL_BLOOD), (120, 1530, POOL_BRAINS), (108, 1562, POOL_BLOOD),
    (124, 1600, POOL_BLOOD2),
)
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
# The mapper, 2026-11-22: the switch obelisk is revealed only when the player takes that shotgun
# (zscript.zs watches the thing with this id).
SHOTGUN_TID = 300
# The mapper, 2026-11-22: 15 armour bonuses (+15% armour) and 20 health bonuses (+20 health) across the
# hall, the stimpack kept, the ammo as it was (6 clips; the shotgun and 2 shell packs). Heavier altars
# are fine; the counts vary from altar to altar, not mirrored.
HB, AB = HEALTH_BONUS, ARMOR_BONUS
# Note #71: 20 more shells across the altars: a pack of 4 on five of them (those with the fewest items).
ALTAR_ITEMS = {
    "monolith_w1": (CLIP, HB, HB, AB), "monolith_e1": (HB, HB, AB, AB, SHELLS),
    "monolith_w2": (AB, SHELLS, AB, HB), "monolith_e2": (CLIP, HB, HB, AB),
    "monolith_w3": (HB, HB, AB, AB), "monolith_e3": (CLIP, SHELLS, HB, AB),
    "monolith_w4": (STIMPACK, AB, AB, HB), "monolith_e4": (AB, HB, SHELLS, HB),
    "monolith_w5": (CLIP, CLIP, HB, HB, AB), "monolith_e5": (SHELLS, SHOTGUN, SHELLS, HB),
    "monolith_w6": (AB, HB, HB, SHELLS), "monolith_e6": (CLIP, HB, HB, AB),
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
    wall_with_channels(m, closet, (cx1, cy1), (cx1, cy0), "closet.wall_e", start=((88, 120), (96, 104)),
                       panel=(3, secret_panel))

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

    # Note #36: the gutters reach the walls; each wall is a list of stretches, each with the sector in
    # front of it (the room, or a gutter), and the drain behind them all (hall_walls).
    east = violet_gutter(m, room, GUTTERS["e"], ne, se, MOUTH_E)
    wb = on_line(sw, nw, GUTTER_W_TOP)
    q = (CROSSING_WALL_X, MOUTH_W[1] + (sw[1] - MOUTH_W[1]) * (CROSSING_WALL_X - MOUTH_W[0]) / (sw[0] - MOUTH_W[0]))
    gutter_w = west_water(m, room, wb, q)
    great_door(m, room, apse[0], apse[1])
    drains = hall_walls(m, room, [
        (MOUTH_W, [(q, room, "room.wall_s"), (sw, gutter_w, "gutter_w.edge_s")]),
        (sw, [(wb, gutter_w, "gutter_w.edge_w"), (nw, room, "room.wall_w2")]),
        (nw, [(apse[0], room, "room.wall_n")]),
        (apse[1], [(ne, room, "room.wall_n3")]),
        (ne, east[0]),
        (se, east[1] + [(MOUTH_E, room, "room.wall_s2")]),
    ])
    cistern(m, *drains["cistern"])  # needs the passage (great_door) and the drains
    for k, (x, y, type_) in enumerate(VIOLET_TRAIL):
        t = m.thing(type_, x, y, f"violet_trail_{k + 1}", angle=(k * 97) % 360)
        m.things[t].fields.update(renderstyle="stencil", fillcolor=TRAIL_COLOUR)
    m.thing(DEAD_MARINE, DEAD_MARINE_AT[0], DEAD_MARINE_AT[1], "dead_marine", angle=DEAD_MARINE_AT[2])
    soul = m.thing(LOST_SOUL, HIDDEN_SOUL[0], HIDDEN_SOUL[1], "hidden_soul", angle=270)
    m.things[soul].fields.update(height=HIDDEN_SOUL[2], ambush=True)

    # The monoliths, in two rows (west row facing east, east row facing west).
    for r, x0 in enumerate(MONOLITH_ROWS):
        for i, y0 in enumerate(MONOLITH_YS):
            face = FACE
            monolith(m, room, f"monolith_{'we'[r]}{i + 1}", x0, y0, facing="e" if r == 0 else "w", face=face,
                     pair=i, switch=(i, "we"[r]) == SWITCH_OBELISK)


def on_line(a, b, y):
    """The point at y on the line through a and b."""
    return (a[0] + (b[0] - a[0]) * (y - a[1]) / (b[1] - a[1]), y)


def violet_gutter(m: MapBuilder, room, g, ne, se, mouth_e):
    """The east gutter (`g`: its inner corners, south-west, north-west; the outer two are on the room's
    east wall, ne -> se, since note #36), cut across at GUTTER_E_CUTS into pieces that turn from green to
    violet towards the switch obelisk. Its south end is the mapper's stream, starting at the south wall
    (se -> mouth_e). Builds everything but its stretches of wall, which it returns for hall_walls: those
    of the east wall (north to south) and of the south wall."""
    sw, nw = g[0], g[1]
    s0 = (GUTTER_E_S0_X, se[1] + (mouth_e[1] - se[1]) * (GUTTER_E_S0_X - se[0]) / (mouth_e[0] - se[0]))
    east = [se] + [on_line(se, ne, y) for y in GUTTER_E_CUTS] + [on_line(se, ne, nw[1])]
    west = [s0] + [GUTTER_E_WEST_CUTS.get(y, on_line(sw, nw, y)) for y in GUTTER_E_CUTS] + [nw]
    pieces = []
    for k in range(len(east) - 1):
        s = m.sector("gutter_e" if k == 0 else f"gutter_e.violet_{k}", floor=-DROP - 8, ceiling=-64,
                     light=HALL_LIGHT, floor_tex=GUTTER_FLAT)
        fog(m, s)
        desat, colour = GUTTER_E_VIOLET[k]
        if colour is not None:
            # Note #56: the floor only; tinted walls made the wall above the drain's grate stand out
            # from the plain wall beside it (the wall's GRAY1 is grey, so the desaturation alone is fine).
            m.sectors[s.index].fields.update(desaturation=desat, color_floor=colour)
        pieces.append(s)
    RIVULET["sector"] = pieces[4]
    RIVULET["piece0"] = pieces[0]
    names = ["gutter_e" if k == 0 else f"gutter_e.violet_{k}" for k in range(len(pieces))]
    for k, s in enumerate(pieces):
        side = ((s0,) + GUTTER_E_WEST) if k == 0 else (west[k],) + GUTTER_E_WEST_EXTRA.get(k, ()) + (west[k + 1],)
        for j, (a, b) in enumerate(zip(side, side[1:])):
            if (a, b) in GUTTER_E_SHARED:
                continue
            m.two_sided(a, b, s, room, f"{names[k]}.edge_w" + (f"_{j + 1}" if j else ""), texture=STONE)
        if k == len(pieces) - 1:
            m.two_sided(west[k + 1], east[k + 1], s, room, f"{names[k]}.edge_n", texture=STONE)
        else:
            m.two_sided(west[k + 1], east[k + 1], s, pieces[k + 1], f"{names[k]}.edge_n", texture=STONE)
    east_wall = [(east[-1], room, "room.wall_e")]
    east_wall += [(east[k], pieces[k], f"{names[k]}.edge_e") for k in range(len(pieces) - 1, -1, -1)]
    return east_wall, [(s0, pieces[0], "gutter_e.edge_s")]


def _edges(m: MapBuilder, sector, edges) -> None:
    """A sector's outline: edges (a, b, other, gid), the sector on either side of a -> b as given; turned
    round if needed so it's on the right (clockwise). other: a sector (two-sided), None (a wall), or
    "skip" (built elsewhere)."""
    area = sum(a[0] * b[1] - b[0] * a[1] for a, b, _, _ in edges)
    if area > 0:                                                  # anticlockwise: turn round
        edges = [(b, a, o, g) for a, b, o, g in reversed(edges)]
    out = []
    for a, b, other, gid in edges:
        if other == "skip":
            continue
        out.append(m.wall(a, b, sector, gid) if other is None else m.two_sided(a, b, sector, other, gid))
    return out


def west_water(m: MapBuilder, room, wb, q):
    """Notes #46, #47: the west gutter (from the west wall's point `wb` at its north end, down the wall
    and along the south wall to `q`: those stretches are hall_walls'), meandering, with the crossing
    channel to the east stream, and the bridge over it. Returns the gutter's sector."""
    s0, s1 = CROSSING
    b0, b1 = BRIDGE
    water = dict(floor=-DROP - 8, ceiling=-64, light=HALL_LIGHT, floor_tex=GUTTER_FLAT)
    g = m.sector("gutter_w", **water)
    fog(m, g)
    bridge = m.sector("gutter_w.bridge", **water)
    fog(m, bridge)
    m.sectors[bridge.index]["id"] = BRIDGE_TAG
    east = RIVULET["piece0"]
    inner = GUTTER_W_INNER
    m.two_sided(wb, inner[-1], g, room, "gutter_w.edge_n", texture=STONE)
    for k in range(len(inner) - 1, 0, -1):          # the inner edge, north to south
        m.two_sided(inner[k], inner[k - 1], g, room, f"gutter_w.edge_e_{len(inner) - k}", texture=STONE)
    m.two_sided(inner[0], (b0, s1), g, room, "gutter_w.crossing_n", texture=STONE)
    m.two_sided((b1, s1), (129, s1), g, room, "gutter_w.crossing_n2", texture=STONE)
    m.two_sided((129, s1), (138, s0), g, east, "gutter_w.join", texture=STONE)
    m.two_sided((138, s0), (b1, s0), g, room, "gutter_w.crossing_s2", texture=STONE)
    m.two_sided((b0, s0), CROSSING_SW, g, room, "gutter_w.crossing_s", texture=STONE)
    m.two_sided(CROSSING_SW, q, g, room, "gutter_w.crossing_sw", texture=STONE)
    # The bridge's stretch of the channel: water under a 3D floor.
    # Note #52: bars under the deck's open sides, from the water up to the slab (MIDBARS3, squeezed to
    # that height and pegged to the water), so it doesn't seem to hover; the water still shows through.
    for name, a, b in (("edge_w", (b0, s0), (b0, s1)), ("edge_e", (b1, s1), (b1, s0))):
        ln = m.two_sided(a, b, bridge, g, f"gutter_w.bridge.{name}", texture=STONE)
        m.linedefs[ln]["dontpegbottom"] = True
        for side in ("sidefront", "sideback"):
            m.sidedefs[m.linedefs[ln][side]].fields.update(texturemiddle="MIDBARS3",
                                                           scaley_mid=72 / (BRIDGE_SLAB[0] - (-DROP - 8)))
    # Note #55: bars all round, its ends on the bank too: there they fill the 4 between the bank's floor
    # and the slab (a two-sided line's middle texture, pegged to the higher floor).
    for name, a, b in (("edge_n", (b0, s1), (b1, s1)), ("edge_s", (b1, s0), (b0, s0))):
        ln = m.two_sided(a, b, bridge, room, f"gutter_w.bridge.{name}", texture=STONE)
        m.linedefs[ln]["dontpegbottom"] = True
        for side in ("sidefront", "sideback"):
            m.sidedefs[m.linedefs[ln][side]].fields.update(texturemiddle="MIDBARS3",
                                                           scaley_mid=72 / (BRIDGE_SLAB[0] - (-DROP)))
    # The control sector: its floor and ceiling are the slab's underside and top; its line carries
    # Sector_Set3DFloor (160: tag, type 1 = solid, flags, alpha), its middle texture the slab's sides.
    cx, cy = BRIDGE_CONTROL
    control = m.room("bridge_control", cx, cy, 32, 32, floor=BRIDGE_SLAB[0], ceiling=BRIDGE_SLAB[1],
                     floor_tex="FLOOR7_2", ceiling_tex="FLOOR7_2", light=BASE_LIGHT)
    m.sectors[control.index]["user_scenery"] = True
    ln = next(i for i, l in enumerate(m.linedefs) if l["user_gid"] == "bridge_control.wall_s")
    m.linedefs[ln].fields.update(special=160, arg0=BRIDGE_TAG, arg1=1, arg2=0, arg3=255)
    m.sidedefs[m.linedefs[ln]["sidefront"]]["texturemiddle"] = STONE
    return g


def passage(m: MapBuilder, vest, P, floor0) -> None:
    """Note #63: the mossy passage from the vestibule (PASSAGE: cross-sections in the doorway's frame,
    placed by P): one sector per piece between two cross-sections, rising PASSAGE_STEP on; one-sided
    walls along its sides, with torch niches (PASSAGE_TORCHES); a wall at its end."""
    PASSAGE = _widened(globals()["PASSAGE"])
    secs = []
    for k in range(len(PASSAGE) - 1):
        f = floor0 + 8 * max(0, min(k, PASSAGE_RISE_END) - PASSAGE_STEP + 1) - 16 * max(0, k - PASSAGE_RISE_END)
        s = m.sector(f"passage_{k + 1}", floor=f, ceiling=f + PASSAGE_HIGH + 16 * max(0, k - 7), light=PASSAGE_LIGHT,
                     floor_tex=PASSAGE_TEXTURE, ceiling_tex=PASSAGE_TEXTURE)
        if k < PASSAGE_FOG_PIECES:
            m.sectors[s.index].fields.update(
                fadecolor=HALL_FOG, fogdensity=round(HALL_FOG_DENSITY * (1 - (k + 1) / (PASSAGE_FOG_PIECES + 1))))
        secs.append(s)
    # The opening from the vestibule, and the steps between pieces (front: the piece before, on the right
    # of a line from the left wall to the right).
    (l0, r0) = PASSAGE[0]
    m.two_sided(P(*l0), P(*r0), vest, secs[0], "passage.opening", texture=PASSAGE_TEXTURE)
    for k in range(1, len(PASSAGE) - 1):
        l, r = PASSAGE[k]
        m.two_sided(P(*l), P(*r), secs[k - 1], secs[k], f"passage_{k + 1}.step", texture=PASSAGE_TEXTURE)
    le, re_ = PASSAGE[-1]
    # Note #77: no end wall: it goes on down into the cistern (cistern(), once the hall's drains exist).
    PASSAGE_END.update(sector=secs[-1], l=P(*le), r=P(*re_))
    import math
    for n, (k, type_, along, across) in enumerate(PASSAGE_ITEMS):
        (la, ra), (lb, rb) = PASSAGE[k], PASSAGE[k + 1]
        a = (la[0] + (ra[0] - la[0]) * across, la[1] + (ra[1] - la[1]) * across)
        b = (lb[0] + (rb[0] - lb[0]) * across, lb[1] + (rb[1] - lb[1]) * across)
        m.thing(type_, *P(a[0] + (b[0] - a[0]) * along, a[1] + (b[1] - a[1]) * along),
                f"passage_{k + 1}.item_{n + 1}", angle=90)
    for n, (k, type_, along, across) in enumerate(PASSAGE_MONSTERS):
        (la, ra), (lb, rb) = PASSAGE[k], PASSAGE[k + 1]
        a = (la[0] + (ra[0] - la[0]) * across, la[1] + (ra[1] - la[1]) * across)
        b = (lb[0] + (rb[0] - lb[0]) * across, lb[1] + (rb[1] - lb[1]) * across)
        x, y = P(a[0] + (b[0] - a[0]) * along, a[1] + (b[1] - a[1]) * along)
        bx, by = P(*a)                                     # facing back the way the player comes
        m.thing(type_, x, y, f"passage_{k + 1}.monster_{n + 1}",
                angle=round(math.degrees(math.atan2(by - y, bx - x))) % 360)
    torches = set(PASSAGE_TORCHES)
    shelves = {(k, side): thing for k, side, thing in PASSAGE_SHELVES}
    import math
    for k, s in enumerate(secs):
        (la, ra), (lb, rb) = PASSAGE[k], PASSAGE[k + 1]
        # Going along, the left wall runs la -> lb with the passage on its right; the right wall rb -> ra.
        for side, a, b in (("l", la, lb), ("r", rb, ra)):
            gid = f"passage_{k + 1}.wall_{side}"
            if (k, side) in torches:
                # A torch niche: 24 wide, NICHE_DEEP deep, from the floor, the torch wholly inside.
                kind, wide, deep, sill, high, thing_in, thing = "niche", 24, NICHE_DEEP, 0, NICHE_HIGH, NICHE_TORCH_IN, TORCH
            elif (k, side) in shelves:
                # Note #76: wider, deeper and lower (was 32 wide, 16 deep, 40 high), lit as the passage.
                kind, wide, deep, sill, high, thing_in, thing = "shelf", 48, 24, 32, 24, 12, shelves[(k, side)]
            else:
                m.wall(P(*a), P(*b), s, gid, texture=PASSAGE_TEXTURE)
                continue
            dx, dy = b[0] - a[0], b[1] - a[1]
            n = math.hypot(dx, dy)
            ex, ey = dx / n, dy / n
            ox, oy = -ey * deep, ex * deep                   # left of a -> b: into the rock
            mid = n / 2
            p0 = (a[0] + ex * (mid - wide / 2), a[1] + ey * (mid - wide / 2))
            p1 = (a[0] + ex * (mid + wide / 2), a[1] + ey * (mid + wide / 2))
            q0, q1 = (p0[0] + ox, p0[1] + oy), (p1[0] + ox, p1[1] + oy)
            f = m.sectors[s.index]["heightfloor"]
            niche = m.sector(f"{gid}.{kind}", floor=f + sill, ceiling=f + sill + high, light=PASSAGE_LIGHT + 64,
                             floor_tex=PASSAGE_TEXTURE, ceiling_tex=PASSAGE_TEXTURE)
            m.sectors[niche.index]["user_scenery"] = True
            if kind == "shelf":                              # note #76: the passage's own light (and fog)
                piece = m.sectors[s.index].fields
                m.sectors[niche.index].fields.update(
                    lightlevel=piece["lightlevel"],
                    **{k2: piece[k2] for k2 in ("fadecolor", "fogdensity") if k2 in piece})
            m.wall(P(*a), P(*p0), s, f"{gid}_a", texture=PASSAGE_TEXTURE)
            m.two_sided(P(*p0), P(*p1), s, niche, f"{gid}.{kind}.mouth", texture=PASSAGE_TEXTURE)
            m.wall(P(*p1), P(*b), s, f"{gid}_b", texture=PASSAGE_TEXTURE)
            m.wall(P(*p0), P(*q0), niche, f"{gid}.{kind}.side_a", texture=PASSAGE_TEXTURE)
            m.wall(P(*q0), P(*q1), niche, f"{gid}.{kind}.back", texture=PASSAGE_TEXTURE)
            m.wall(P(*q1), P(*p1), niche, f"{gid}.{kind}.side_b", texture=PASSAGE_TEXTURE)
            k_in = thing_in / deep
            cx, cy = (p0[0] + p1[0]) / 2 + ox * k_in, (p0[1] + p1[1]) / 2 + oy * k_in
            m.thing(thing, *P(cx, cy), f"{gid}.{'torch' if kind == 'niche' else 'item'}")


def great_door(m: MapBuilder, room, a, b) -> None:
    """Note #45: the great doorway in the wall a -> b (the room on its right), in the middle of it; its
    stuck leaves, the small door in the left one, and the vestibule beyond. Built in the wall's own
    frame (u along it from its middle, d away from the room), then placed."""
    import math
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
    mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
    P = lambda u, d: (round(mx + u * ux - d * uy, 2), round(my + u * uy + d * ux, 2))
    half, top, floor = DOORWAY / 2, -DROP + DOOR_HIGH, -DROP
    vw, vd = VESTIBULE[0] / 2, VESTIBULE[1]

    # The wall either side of the opening, and the opening with its lintel.
    m.wall(a, P(-half, 0), room, "room.wall_n2")
    m.wall(P(half, 0), b, room, "room.wall_n2b")
    vest = m.sector("vestibule", floor=floor, ceiling=top, light=VESTIBULE_LIGHT)
    fog(m, vest)
    opening = m.two_sided(P(-half, 0), P(half, 0), room, vest, "vestibule.opening", texture=STONE)
    # The vestibule: the jambs (16 deep), then wider behind the wall.
    j = 16
    _edges(m, vest, [
        (P(half, 0), P(-half, 0), "skip", ""),
        (P(-half, 0), P(-half, j), None, "vestibule.jamb_w"),
        (P(-half, j), P(*VESTIBULE_OUTLINE[0]), None, "vestibule.wall_sw"),
    ] + [(P(*VESTIBULE_OUTLINE[i]), P(*VESTIBULE_OUTLINE[i + 1]), None, f"vestibule.wall_{i + 1}")
         for i in range(len(VESTIBULE_OUTLINE) - 1)] + [
        (P(*PASSAGE[0][0]), P(*PASSAGE[0][1]), "skip", ""),     # the passage's opening (passage())
        (P(*PASSAGE[0][1]), P(half, j), None, "vestibule.wall_se"),
        (P(half, j), P(half, 0), None, "vestibule.jamb_e"),
    ])
    passage(m, vest, P, floor)
    for k, (iu, idd) in enumerate(VESTIBULE_IMPS):
        imp = m.thing(IMP, *P(iu, idd), f"vestibule.imp_{k + 1}",
                      angle=round(math.degrees(math.atan2(-ux, uy))) % 360)      # facing the doors
    glow = m.thing(9830, *P(0, 168), "vestibule.glow")
    r, g, bl, rad = VESTIBULE_GLOW
    m.things[glow].fields.update(height=48, arg0=r, arg1=g, arg2=bl, arg3=rad)

    # The leaves: solid, hinged at the jambs' back corners, swung in. Leaf k's point s along it, t
    # through it (towards the vestibule).
    def leaf_point(k, s, tt):
        ang = math.radians(LEAF_ANGLES[k])
        hu = -half if k == 0 else half
        du = (math.cos(ang), math.sin(ang)) if k == 0 else (-math.cos(ang), math.sin(ang))
        nu = (-math.sin(ang), math.cos(ang)) if k == 0 else (math.sin(ang), math.cos(ang))
        return P(hu + s * du[0] + tt * nu[0], j + s * du[1] + tt * nu[1])
    length, T = half - 2, LEAF_THICK
    mid = length / 2

    def skull_offset(k, side, s0, s1):
        """Note #49: the x offset that centres the texture's skulls on the leaf, for the stretch s0-s1 of
        its face (seen from the hall) or back: a texture starts at the end on the viewer's left."""
        left_is_s0 = (k == 0) == (side == "face")
        return round(LEAF_SKULLS - (mid - s0) if left_is_s0 else LEAF_SKULLS - (s1 - mid)) % 128

    def vest_side(ln):
        for side in ("sidefront", "sideback"):
            sd = m.sidedefs[m.linedefs[ln][side]]
            if sd["sector"] == vest.index:
                return sd

    def by_gid(gid):
        return next(i for i, l in enumerate(m.linedefs) if l["user_gid"] == gid)

    def leaf(k, s0, s1, gid, ends):
        s = m.sector(gid, floor=top, ceiling=top, light=VESTIBULE_LIGHT)
        lines = _edges(m, s, [
            (leaf_point(k, s0, 0), leaf_point(k, s1, 0), vest, f"{gid}.face"),
            (leaf_point(k, s1, 0), leaf_point(k, s1, T), ends[1], f"{gid}.end_b"),
            (leaf_point(k, s1, T), leaf_point(k, s0, T), vest, f"{gid}.back"),
            (leaf_point(k, s0, T), leaf_point(k, s0, 0), ends[0], f"{gid}.end_a"),
        ])
        for ln in lines:
            m.linedefs[ln]["blocking"] = True
            for side in ("sidefront", "sideback"):
                if side in m.linedefs[ln].fields:
                    m.sidedefs[m.linedefs[ln][side]]["texturebottom"] = LEAF_TEXTURES[k]
        for side in ("face", "back"):
            vest_side(by_gid(f"{gid}.{side}"))["offsetx"] = skull_offset(k, side, s0, s1)
        return s
    w0, w1 = WICKET
    leaf(1, 0, length, "great_door.leaf_e", (vest, vest))
    # The left leaf, with the small door (notes #50, #57, #58): pieces in the leaf's own (s, t), built
    # through one table of edges so pieces that meet share their lines; edges nobody else has face the
    # vestibule. The door's floor is the panel's top, its ceiling the lintel's underside: Plat_DownWaitUpStay
    # (62: tag, speed, delay) sinks the panel and brings it back up, from either side.
    fd, fw, fh = FRAME
    a0, a1 = w0 - fw, w1 + fw
    solid = dict(floor=top, ceiling=top, light=VESTIBULE_LIGHT)
    pieces = {
        "great_door.leaf_w": (m.sector("great_door.leaf_w", **solid), [(0, 0), (a0, 0), (a0, fd), (a0, T), (0, T)]),
        "great_door.frame": (m.sector("great_door.frame", floor=floor, ceiling=floor + WICKET_HIGH + fh,
                                      light=VESTIBULE_LIGHT, ceiling_tex="FLOOR4_8"),
                             [(a0, 0), (a1, 0), (a1, fd), (w1, fd), (w0, fd), (a0, fd)]),
        "great_door.post_w": (m.sector("great_door.post_w", **solid), [(a0, fd), (w0, fd), (w0, T), (a0, T)]),
        "great_door.wicket": (m.sector("great_door.wicket", floor=floor + WICKET_HIGH, ceiling=floor + WICKET_HIGH,
                                       light=VESTIBULE_LIGHT), [(w0, fd), (w1, fd), (w1, T), (w0, T)]),
        "great_door.post_e": (m.sector("great_door.post_e", **solid), [(w1, fd), (a1, fd), (a1, T), (w1, T)]),
        "great_door.leaf_w2": (m.sector("great_door.leaf_w2", **solid), [(a1, 0), (length, 0), (length, T), (a1, T), (a1, fd)]),
    }
    fog(m, pieces["great_door.frame"][0])
    door = pieces["great_door.wicket"][0]
    m.sectors[door.index]["id"] = WICKET_TAG
    edges = {}
    for name, (sec, pts) in pieces.items():
        w = [leaf_point(0, s, tt) for s, tt in pts]
        area = sum(w[i][0] * w[(i + 1) % len(w)][1] - w[(i + 1) % len(w)][0] * w[i][1] for i in range(len(w)))
        order = list(range(len(w))) if area < 0 else list(range(len(w)))[::-1]   # clockwise
        for i, k in enumerate(order):
            k2 = order[(i + 1) % len(order)]
            edges.setdefault(frozenset((pts[k], pts[k2])), []).append((name, sec, pts[k], pts[k2]))
    for key, owners in edges.items():
        name, sec, pa, pb = owners[0]
        other = owners[1][1] if len(owners) > 1 else vest
        oname = owners[1][0] if len(owners) > 1 else "vestibule"
        (s0, t0), (s1, t1) = pa, pb
        where = "face" if t0 == t1 == 0 else "back" if t0 == t1 == T else f"{min(s0, s1):g}_{min(t0, t1):g}"
        gid = f"{name}.{oname.split('.')[-1]}.{where}"
        # The front is the player's side (the vestibule or the frame) on the door's faces.
        front, back, a, b = sec, other, leaf_point(0, *pa), leaf_point(0, *pb)
        if other is vest or name == "great_door.wicket":
            front, back, a, b = other, sec, b, a
        ln = m.two_sided(a, b, front, back, gid, texture=FRAME_TEXTURE)
        L = m.linedefs[ln]
        fs, bs = m.sidedefs[L["sidefront"]], m.sidedefs[L["sideback"]]
        lo, hi = sorted((s0, s1))
        is_wicket = "great_door.wicket" in (name, oname)
        if is_wicket and t0 == t1:                      # the door's two faces
            # Note #64: monsters can open it too (monsteruse), so the imps come through once woken.
            L.fields.update(special=62, arg0=WICKET_TAG, arg1=16, arg2=105, playeruse=True, monsteruse=True,
                            repeatspecial=True)
            side = "face" if t0 == fd else "back"
            fs.fields.update(texturebottom=WICKET_TEXTURE, offsetx_bottom=WICKET_OFFSET[0],
                             offsety_bottom=WICKET_OFFSET[1])
            if side == "back":                                          # the leaf above it, from behind
                L["dontpegtop"] = True
                fs.fields.update(texturetop=LEAF_TEXTURES[0], offsetx=skull_offset(0, "back", lo, hi),
                                 offsetx_bottom=WICKET_OFFSET[0] - skull_offset(0, "back", lo, hi))
        elif is_wicket:                                 # the door's sides
            fs["texturebottom"] = bs["texturebottom"] = "DOORTRAK"
        elif other is vest:                                             # the leaf's face and back
            vs = fs
            side = "face" if t0 == 0 else "back"
            vs.fields.update(texturetop=LEAF_TEXTURES[0], texturebottom=LEAF_TEXTURES[0],
                             offsetx=skull_offset(0, side, lo, hi))
            L.fields.update(dontpegtop=True, blocking=name != "great_door.frame")
    return None


def cistern(m: MapBuilder, drain, west) -> None:
    """Note #77, editor save 22:36: the stairs down from the passage's end (PASSAGE_END) to the cistern, and
    the cistern: `west` is the drain's far side, north to south (the cistern's west wall, shared with
    the drain: water pouring down it); CISTERN_EAST its east side."""
    end = PASSAGE_END
    ne, se = CISTERN_EAST
    nw = west[0]
    top = m.sectors[end["sector"].index]["heightfloor"]
    secs = []
    for k in range(CISTERN_STEPS):
        f = top - (top - CISTERN_FLOOR) * (k + 1) // (CISTERN_STEPS + 1)
        s = m.sector(f"cistern_stair_{k + 1}", floor=f, ceiling=f + PASSAGE_HIGH, light=PASSAGE_LIGHT - 8 * (k + 1),
                     floor_tex=PASSAGE_TEXTURE, ceiling_tex=PASSAGE_TEXTURE)
        m.sectors[s.index].fields.update(fadecolor=CISTERN_DARK_FOG[0],
                                         fogdensity=CISTERN_DARK_FOG[1] * (k + 1) // (CISTERN_STEPS + 1))
        secs.append(s)
    cis = m.sector("cistern", floor=CISTERN_FLOOR, ceiling=CISTERN_TOP, light=CISTERN_DARK_LIGHT,
                   floor_tex=GUTTER_FLAT, ceiling_tex=PASSAGE_TEXTURE)
    m.sectors[cis.index].fields.update(fadecolor=CISTERN_DARK_FOG[0], fogdensity=CISTERN_DARK_FOG[1])
    # Cross-sections (left, right) going down (south: left is east): the passage's end, then on to the
    # cistern's north edge.
    def lerp(a, b, f):
        return (round(a[0] + (b[0] - a[0]) * f, 2), round(a[1] + (b[1] - a[1]) * f, 2))
    cuts = [(lerp(end["l"], ne, k / CISTERN_STEPS), lerp(end["r"], nw, k / CISTERN_STEPS))
            for k in range(CISTERN_STEPS + 1)]
    chain = [end["sector"]] + secs + [cis]
    for k, (l, r) in enumerate(cuts):
        name = "passage.down" if k == 0 else "cistern.mouth" if k == CISTERN_STEPS else f"cistern_stair_{k + 1}.step"
        m.two_sided(l, r, chain[k], chain[k + 1], name, texture=PASSAGE_TEXTURE)
    for k, s in enumerate(secs):
        (la, ra), (lb, rb) = cuts[k], cuts[k + 1]
        m.wall(la, lb, s, f"cistern_stair_{k + 1}.wall_l", texture=PASSAGE_TEXTURE)
        m.wall(rb, ra, s, f"cistern_stair_{k + 1}.wall_r", texture=PASSAGE_TEXTURE)
    for k, (x, y) in enumerate(CISTERN_SPECTRES):
        sp = m.thing(SPECTRE, x, y, f"cistern.spectre_{k + 1}", angle=90)
        m.things[sp]["ambush"] = True
    # The cistern: east and south walls as drawn, the west wall the drain's far side.
    m.wall(ne, se, cis, "cistern.wall_e", texture=PASSAGE_TEXTURE)
    m.wall(se, west[-1], cis, "cistern.wall_s", texture=PASSAGE_TEXTURE)
    for i, (a, b) in enumerate(zip(west, west[1:])):
        if a == b:
            continue
        ln = m.two_sided(a, b, drain, cis, f"cistern.wall_w_{i + 1}", texture=CISTERN_FALL)
        m.linedefs[ln]["blocking"] = True


def hall_walls(m: MapBuilder, room, walls) -> dict:
    """Note #36: the hall's outer walls. `walls`: the walls in order, clockwise from the mouth's west
    corner round to its east corner, each (start, stretches), a stretch being (end, the sector in front,
    gid). Note #44: only where a gutter meets the wall is it lifted off the floor over a drain (a
    two-sided line, blocking, the grate in the gap); elsewhere it's a plain wall. Each run of gutter
    stretches gets its own drain, DRAIN_DEPTH deep behind it, closed off at both ends. A wall's texture
    runs on along its whole length."""
    runs, run = [], []
    for start, stretches in walls:
        a = start
        for end, sector, gid in stretches:
            along = round(((a[0] - start[0]) ** 2 + (a[1] - start[1]) ** 2) ** 0.5)
            if sector is room:
                ln = m.wall(a, end, room, gid)
                if along:
                    m.sidedefs[m.linedefs[ln]["sidefront"]]["offsetx"] = along
                if run:
                    runs.append(run)
                    run = []
            else:
                run.append((a, end, sector, gid, along))
            a = end
    if run:
        runs.append(run)
    out = {}
    for k, run in enumerate(runs):
        name = "drain" if k == 0 else f"drain_{k + 1}"
        cistern = k == 1                                     # the east run: the cistern behind it (note #77)
        drain = m.sector(name, floor=DRAIN_FLOOR, ceiling=DRAIN_TOP, light=CISTERN_LIGHT, floor_tex=GUTTER_FLAT)
        # Note #78: seen from the hall through the vines, the water should fade uniformly into darkness:
        # the drains get the cistern's light and its dark fog (they had the hall's grey fog, then the
        # cistern's dark one showed beyond: a seam).
        m.sectors[drain.index].fields.update(fadecolor=CISTERN_FOG[0], fogdensity=CISTERN_FOG[1])
        m.sectors[drain.index]["user_scenery"] = True
        for a, b, sector, gid, along in run:
            ln = m.two_sided(a, b, sector, drain, gid, texture=WALL)
            # Note #56: the wall above the gap pegged to the ceiling, as the plain walls beside it are.
            # Note #83: blocksight: monsters (the cistern's spectres) can't see through the vines.
            m.linedefs[ln].fields.update(blocking=True, dontpegtop=True, blocksight=True)
            front = m.sidedefs[m.linedefs[ln]["sidefront"]]
            front["texturemiddle"] = DRAIN_GRATE
            # Note #81: the vines on the drain's side too (a two-sided line's middle texture is drawn per
            # side), so from below, in the cistern, it's always seen through them.
            m.sidedefs[m.linedefs[ln]["sideback"]]["texturemiddle"] = DRAIN_GRATE
            if along:
                front["offsetx"] = along
            if cistern:                                      # the water pouring over into the drain
                m.sidedefs[m.linedefs[ln]["sideback"]]["texturebottom"] = CISTERN_FALL
        inner = [run[0][0]] + [s[1] for s in run]
        outer = _shifted_polyline(inner, DRAIN_DEPTH)
        # The cistern's run: its far side from the north end to the south-east corner (the hall's corner
        # se, the 7th point of the run) is the cistern's west wall (built by cistern()).
        shared = len(inner) - 2 if cistern else 0
        for i, (a, b) in enumerate(zip(outer, outer[1:])):
            if a != b and i >= shared:
                m.wall(a, b, drain, f"{name}.back_{i + 1}")
        if cistern:
            out["cistern"] = (drain, outer[:shared + 1])
        m.wall(inner[0], outer[0], drain, f"{name}.end_a")
        m.wall(outer[-1], inner[-1], drain, f"{name}.end_b")
    return out


def _shifted_polyline(pts, d):
    """`pts` moved `d` to the left of the direction they run in; corners where the moved lines meet
    (straight on, where they don't turn)."""
    def shifted(a, b):
        dx, dy = b[0] - a[0], b[1] - a[1]
        n = (dx * dx + dy * dy) ** 0.5
        ox, oy = -dy / n * d, dx / n * d
        return (a[0] + ox, a[1] + oy), (b[0] + ox, b[1] + oy)
    lines = [shifted(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]
    def meet(l1, l2):
        (x1, y1), (x2, y2) = l1
        (x3, y3), (x4, y4) = l2
        den = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
        if abs(den) < 1e-6 * max(1.0, abs(x1 - x2) + abs(y1 - y2)) * max(1.0, abs(x3 - x4) + abs(y3 - y4)):
            return l1[1]                                  # straight on
        u = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / den
        return (x1 + u * (x2 - x1), y1 + u * (y2 - y1))
    r = lambda q: (round(q[0], 2), round(q[1], 2))
    out = [r(lines[0][0])] + [r(meet(lines[i], lines[i + 1])) for i in range(len(lines) - 1)] + [r(lines[-1][1])]
    return out


def slit_edges(m: MapBuilder, room, base, sleeve, gid: str, x0: float, y0: float) -> None:
    """Notes #35, #38: the switch obelisk's leak (it faces west; its back is east). The base's east edge
    and the sleeve's east edge, each split round the slit: the slit itself (a sector cut into the sleeve's
    back, from the base's floor up SLIT[3], tagged SLIT_TAG), liquid falling down its back wall; the
    base's edge below it onto the rivulet, the fall going on over the step."""
    a0, a1, depth, high = SLIT
    ys, yn = y0 + a0, y0 + a1
    bx, sx = x0 + 48, x0 + 40
    rivulet = RIVULET["sector"]
    floor = -DROP + BASE_STEP
    # Note #43: the liquid ran down the slit, vanished on the base's floor and showed again on its edge:
    # now it runs on across the base in a strip of the same liquid (the spill, the slit's width) from the
    # slit's mouth to the base's edge, and down that into the rivulet.
    spill = m.sector(f"{gid}.spill", floor=floor, ceiling=-64, light=BASE_LIGHT, floor_tex=GUTTER_FLAT)
    fog(m, spill)
    hall_ceiling(m, spill)
    m.sectors[spill.index].fields.update(desaturation=1.0, color_floor=VIOLET, color_wallbottom=VIOLET,
                                         user_scenery=True)   # 8 wide: too narrow to enter
    # Note #51: the pieces of a split edge carry the texture on from where the last left off (seen from
    # outside, a back side's texture starts at the line's end), as the unsplit edges of the others do.
    ln = m.two_sided((bx, y0 + 96), (bx, yn), base, room, f"{gid}.base.edge_e", texture=STONE)
    m.sidedefs[m.linedefs[ln]["sideback"]]["offsetx"] = yn - (y0 - 16)
    step = m.two_sided((bx, yn), (bx, ys), spill, rivulet, f"{gid}.base.edge_e_fall", texture=STONE)
    # The fall over the step, tinted violet on its own (its sector, the rivulet, no longer tints walls).
    m.sidedefs[m.linedefs[step]["sideback"]].fields.update(texturebottom=VIOLET_FALL, useowncolors_bottom=True,
                                                           uppercolor_bottom=VIOLET, lowercolor_bottom=VIOLET)
    m.two_sided((bx, ys), (bx, y0 - 16), base, room, f"{gid}.base.edge_e_2", texture=STONE)
    # Note #54: the strip of the sleeve's back above the slit is drawn by the sector in front of the slit;
    # the spill is desaturated (for its liquid), which greyed it. So a lip 1 wide, lit and tinted like the
    # base, stands between them and draws it.
    lx = sx + 1
    lip = m.sector(f"{gid}.lip", floor=floor, ceiling=-64, light=BASE_LIGHT, floor_tex="FLOOR7_2")
    fog(m, lip)
    hall_ceiling(m, lip)
    m.sectors[lip.index].fields.update(lightcolor=SWITCH_GLOW_TINT, user_scenery=True)
    m.two_sided((lx, yn), (lx, ys), lip, spill, f"{gid}.lip.edge_e", texture=STONE)
    m.two_sided((sx, yn), (lx, yn), lip, base, f"{gid}.lip.side_n", texture=STONE)
    m.two_sided((lx, ys), (sx, ys), lip, base, f"{gid}.lip.side_s", texture=STONE)
    m.two_sided((lx, yn), (bx, yn), spill, base, f"{gid}.spill.side_n", texture=STONE)
    m.two_sided((bx, ys), (lx, ys), spill, base, f"{gid}.spill.side_s", texture=STONE)
    slit = m.sector(f"{gid}.slit", floor=floor, ceiling=floor + high, light=BASE_LIGHT, floor_tex=GUTTER_FLAT)
    fog(m, slit)
    # Note #42: once the sleeve has sunk, the slit is part of the ceiling's slot above the slab: its
    # ceiling, and its walls' upper parts, are the slot's (marble, as dark), not liquid.
    m.sectors[slit.index].fields.update(id=SLIT_TAG, soundsequence="Silence", user_scenery=True,
                                        desaturation=1.0, color_floor=VIOLET, color_wallbottom=VIOLET,
                                        textureceiling=STONE, lightceiling=SLOT_DARK)
    for name, p, q in (("edge_e", (sx, y0 + 88), (sx, yn)), ("edge_e_2", (sx, ys), (sx, y0 - 8))):
        ln = m.two_sided(p, q, sleeve, base, f"{gid}.sleeve.{name}", texture=STONE)
        m.sidedefs[m.linedefs[ln]["sidefront"]]["light"] = SLOT_DARK
        if q[1] - (y0 - 8):
            m.sidedefs[m.linedefs[ln]["sideback"]]["offsetx"] = q[1] - (y0 - 8)
    mouth = m.two_sided((sx, yn), (sx, ys), slit, lip, f"{gid}.slit.mouth", texture=STONE)
    m.sidedefs[m.linedefs[mouth]["sidefront"]]["light"] = SLOT_DARK
    # Above the slit, the sleeve's back is this line's upper part: pegged to the top and moved to match
    # the sleeve's lower parts beside it (their texture's top is at the sleeve's top, SLEEVE_TOP; this
    # one's at the spill's ceiling).
    m.linedefs[mouth]["dontpegtop"] = True
    m.sidedefs[m.linedefs[mouth]["sideback"]].fields.update(offsetx=ys - (y0 - 8), offsety=SLEEVE_TOP - (-64))
    back = m.two_sided((sx - depth, ys), (sx - depth, yn), slit, sleeve, f"{gid}.slit.back", texture=STONE)
    m.sidedefs[m.linedefs[back]["sidefront"]].fields.update(texturebottom=VIOLET_FALL, light=SLOT_DARK)
    for name, p, q in (("side_n", (sx - depth, yn), (sx, yn)), ("side_s", (sx, ys), (sx - depth, ys))):
        ln = m.two_sided(p, q, slit, sleeve, f"{gid}.slit.{name}", texture=STONE)
        m.sidedefs[m.linedefs[ln]["sidefront"]]["light"] = SLOT_DARK


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
    its turn comes (a show after the elevator lands; the switch obelisk when its shotgun is taken), zscript.zs (CacobeliskObelisks) lowers the sleeve to the altars' height, 8 above the base (note #23; it sinks
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
        if switch and name == "e":
            continue                                 # slit_edges
        m.two_sided(p, q, base, room, f"{gid}.base.edge_{name}", texture=STONE)
    c = ((x0 - 8, y0 - 8), (x0 - 8, y0 + 88), (x0 + 40, y0 + 88), (x0 + 40, y0 - 8))
    if switch:
        slit_edges(m, room, base, sleeve, gid, x0, y0)
    for name, p, q in zip("wnes", c, c[1:] + c[:1]):
        if switch and name == "e":
            continue
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
        t = m.thing(type_, x, y, item, angle=h[-1] * 360 // 256)
        if type_ == SHOTGUN:
            m.things[t]["id"] = SHOTGUN_TID


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


def wall_with_channels(m: MapBuilder, closet, a, b, gid: str, *, start=None, end=None, panel=None) -> None:
    """A straight closet wall a -> b (the closet on its right) with emergency light channels in it
    (note #6): at CHANNEL_AT along the wall from a, each 16 wide, 8 deep, floor to ceiling, a red
    light tube (LITERED) at the back, DOORTRAK sides, a little brighter and tinted red, and a dim red
    light in front that spills onto the floor. start / end: (corner, point on the wall) when the wall's
    first or last stretch comes in from a cut corner instead of from a or to b. panel: (n, build) builds
    the wall's n-th stretch (from the previous channel to the n-th) with build(m, closet, p, q, gid)
    instead of a plain wall. Each sector is on the right of its lines, clockwise."""
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
        if panel and panel[0] == i + 1:
            panel[1](m, closet, start, p0, f"{gid}_{i + 1}")
        else:
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


def secret_panel(m: MapBuilder, closet, a, b, gid: str) -> None:
    """Note #29: the stretch of the closet's east wall a -> b (going south) with the secret panel in it:
    a door 8 thick (SECRET_TAG, shut: floor = ceiling = 0) that looks like the wall, and behind it an
    alcove with the light amplification goggles, which count as the secret when taken. The alcove's
    ceiling (72) is above the closet's, so the opened panel (lowest ceiling - 4 = 60) lets the player in."""
    (pa, pb), x1 = SECRET_PANEL, SECRET_ALCOVE_X
    x0 = pa[0] + 8
    door = m.sector("closet.secret_door", floor=0, ceiling=0, light=CLOSET_LIGHT)
    m.sectors[door.index]["id"] = SECRET_TAG
    alcove = m.sector("closet.secret", floor=0, ceiling=72, light=72)
    m.wall(a, pa, closet, f"{gid}a")
    ln = m.two_sided(pa, pb, closet, door, "closet.secret_door.face")
    m.linedefs[ln]["secret"] = True                         # a plain wall on the automap
    m.sidedefs[m.linedefs[ln]["sidefront"]]["offsetx"] = abs(pa[1] - a[1])   # the wall's texture runs on
    m.wall(pb, b, closet, f"{gid}b")
    m.wall(pa, (x0, pa[1]), door, "closet.secret_door.side_n", texture="DOORTRAK")
    m.wall((x0, pb[1]), pb, door, "closet.secret_door.side_s", texture="DOORTRAK")
    m.two_sided((x0, pa[1]), (x0, pb[1]), door, alcove, "closet.secret_door.back")
    m.wall((x0, pa[1]), (x1, pa[1]), alcove, "closet.secret.wall_n")
    m.wall((x1, pa[1]), (x1, pb[1]), alcove, "closet.secret.wall_e")
    m.wall((x1, pb[1]), (x0, pb[1]), alcove, "closet.secret.wall_s")
    t = m.thing(LIGHT_AMP, x1 - 12, (pa[1] + pb[1]) / 2, "closet.secret.goggles", angle=180)
    m.things[t]["countsecret"] = True


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
    # Note #29: a lintel beam 8 deep in front of the recess (ceiling 56, like the recess), with a slot in
    # its middle (16 wide, ceiling 64) whose back, the recess's lintel, is the target: one small blue
    # light panel (TARGET_TEXTURE), full bright, with a faint pulsing blue light in front. Shooting it
    # opens the secret panel (Door_Open on SECRET_TAG). The beam and slot breathe with the closet.
    (x0, y0), (x1, _) = p0, p1
    t0, t1, yb = mid - 8, mid + 8, y0 + 8
    beam_w = m.sector("closet.lintel_w", floor=0, ceiling=56, light=CLOSET_LIGHT)
    slot = m.sector("closet.target", floor=0, ceiling=TARGET_TOP, light=CLOSET_LIGHT)
    beam_e = m.sector("closet.lintel_e", floor=0, ceiling=56, light=CLOSET_LIGHT)
    for s in (beam_w, slot, beam_e):
        m.sectors[s.index].fields.update(id=CLOSET_TAG, user_scenery=True)   # too narrow to walk into
    m.sectors[recess.index]["user_scenery"] = True   # behind the beam now: too narrow to reach
    m.two_sided((x1, y0), (x1, yb), coffer, beam_e, "closet.lintel_e.edge_e")
    m.two_sided((x1, yb), (t1, yb), coffer, beam_e, "closet.lintel_e.edge_n")
    m.two_sided((t1, yb), (t0, yb), coffer, slot, "closet.target.edge_n")
    m.two_sided((t0, yb), (x0, yb), coffer, beam_w, "closet.lintel_w.edge_n")
    m.two_sided((x0, yb), (x0, y0), coffer, beam_w, "closet.lintel_w.edge_w")
    m.two_sided((t1, yb), (t1, y0), slot, beam_e, "closet.target.side_e")
    m.two_sided((t0, y0), (t0, yb), slot, beam_w, "closet.target.side_w")
    m.two_sided((x1, y0), (t1, y0), beam_e, recess, "closet.start_door.mouth_e")
    target = m.two_sided((t1, y0), (t0, y0), slot, recess, "closet.start_door.mouth")
    m.two_sided((t0, y0), (x0, y0), beam_w, recess, "closet.start_door.mouth_w")
    m.linedefs[target].fields.update(special=11, arg0=SECRET_TAG, arg1=16, impact=True)
    m.linedefs[target]["dontpegtop"] = True
    m.sidedefs[m.linedefs[target]["sidefront"]].fields.update(texturetop=TARGET_TEXTURE,
                                                              offsetx_top=TARGET_OFFSET[0],
                                                              offsety_top=TARGET_OFFSET[1],
                                                              light=255,
                                                              lightabsolute=True)
    glow = m.thing(GLOW_LIGHT, mid, y0 + 6, "closet.target.glow", angle=TARGET_PERIOD)
    m.things[glow].fields.update(height=60, arg0=TARGET_RGB[0], arg1=TARGET_RGB[1], arg2=TARGET_RGB[2],
                                 arg3=TARGET_RADIUS[0], arg4=TARGET_RADIUS[1], id=TARGET_TID)
    m.wall(p0, k0, coffer, "closet.coffer.wall_s")
    m.wall(k0, a, closet, "closet.wall_s")
    m.wall(q0, p0, recess, "closet.start_door.side_w", texture="DOORTRAK")
    door = m.wall(q1, q0, recess, "closet.start_door.door", texture=START_DOOR)
    m.linedefs[door]["dontpegbottom"] = True
    m.wall(p1, q1, recess, "closet.start_door.side_e", texture="DOORTRAK")
