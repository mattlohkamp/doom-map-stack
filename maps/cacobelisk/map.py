"""Cacobelisk (was test2): the generator for this map. `.\\dms.ps1 build cacobelisk` turns it into TEXTMAP."""

import hashlib

from dms import gen
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
CAR_RECESS, CAR_FLOOR = 4, "AQF072"   # note #134
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
CHANNEL_DIM = {("closet.wall_w", 1), ("closet.wall_w", 3), ("closet.wall_e", 2),
               ("tech_hall.wall_n", 2), ("tech_hall.wall_n", 5), ("tech_hall.wall_s", 1), ("tech_hall.wall_s", 3)}   # note #77: the corridor past the tech door
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
TARGET_SLOT_TAG = 5                     # note #35: the slot, shut once the target is shot (zscript.zs SLOT_TAG)
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
JAMB_TRACK = "DOORTRAK"   # note #109: the jambs of the way out at the shaft's foot
TRACK_TURNED = "CACOTRKH"   # note #105: the track turned on its side (textures.txt)
LIP_TOP = TRACK            # note #22: the track metal itself, to match the shaft walls (STEP1 was grey)
SWITCH_TEXTURE = "SW1GRAY"
START_DOOR = "DOOR3"     # the classic level-start door, 64 x 72
# The switch niche: 48 wide, 8 deep, sill 16, top 48, a little brighter than the shaft (note #2).
NICHE_X0, NICHE_X1 = 8, 56
NICHE_FLOOR, NICHE_TOP = 16, 48
NICHE_LIGHT = 176
# Note #25: the bottom call switch's niche is dark, darker than the hall (104), so it doesn't draw attention.
CALL_NICHE_LIGHT = 72
HALL_SKY = 0                    # note #67: the walls 256 high under the sky (384 at first, note #59); the obelisks' pillars reach -16
SKY_FLAT = "F_SKY1"
HALL_WALL, HALL_WALL_SCALE = "STONE3", 0.5     # note #69 (scale 0.5 = twice the size)
# Note #71: STONE3's dark seams are at its rows 14, 46, 78, 110: hung from the sky's height (0) at twice the
# size, the lowest was at -221, 19 above the vine grates' top (-240). Moved down 16 (8 texture pixels) so it
# runs just above the vines. (Sign as worked out for the door's faces: a positive offset moves it up.)
HALL_WALL_SHIFT = -8
HALL_FLOOR = "FLAT10"           # note #58: brown dirt (a flat; on the banks it's used as a wall texture)
# Note #54: the map's own textures (textures.txt): the closet's wall with a strip of the track metal, turned
# on its side, along its foot; and the shaft's wall: that strip at its top, the upright track below.
CLOSET_WALL = "GRAY1"
CLOSET_SKIN = "METAL4"          # the mapper's pick (chat, 2026-11-23); PIPEWAL1 first (note #64), instead of cement
BASE_TEXTURE = "CACOBASE"
TECH_FLOOR, TECH_CEILING = "FLOOR0_3", "BROWNGRN"  # chat 2026-11-25: the techbase's floor and ceiling (were the defaults; SLIME14, FLAT5_4, AQF053, SLIME15, FCGRATE2 tried first; note #95: BROWNGRN, a wall texture)
TECHBASE_GIDS = ("closet", "car", "shaft_", "tech_door", "tech_hall")
CALL_NICHE_TAG = 4              # note #34: shut by a panel once a switch is used (zscript.zs CALL_TAG)
# Note #7: a pulse at the switch, subtle but insistent (this is the only way on): a small pale light
# (PointLightPulseAttenuated, 9831) just in front of the plate, swelling and fading every second. Light
# things don't fall with the floor, so it stays up with the switch when the niche drops away.
SWITCH_PULSE_RGB = (150, 200, 170)
SWITCH_PULSE_RADIUS = (12, 24)   # the mapper's editor save 2026-11-22 01:42 (was 24 to 56)
SWITCH_PULSE_PERIOD = 35  # tics
SWITCH_PULSE_TID = 302
SHUTTER_TAG = 6           # note #36 (zscript.zs SHUTTER_TAG)
SHUTTER_DEEP = 2
CALL_SHUTTER_TEXTURE = "AQF074"   # note #43: the bottom niche's panel (AQF049 "isn't quite a fit" there)
SHUTTER_TEXTURE = CALL_SHUTTER_TEXTURE   # note #44: the same panel on both (the top one was AQF049)
SWITCH_WINDOW = 32           # note #44: both niches' width: the panel's one 32 x 32 tile, and the switch's plate   # the mapper's pick (a flat; UZDoom draws flats on walls)
# Note #7: the elevator track shows 16 up the platform's walls before it moves, a preview of the ride: the
# solid blocks lining the shaft are at 16, not 0, so the track (their lower texture) starts there.
TRACK_PREVIEW = 16
# The hall: the mouth and the big room, dim and quiet (mapper, 2026-11-22), in fog.
HALL_LIGHT = 104          # note #4: "drop the lighting just a bit" (was 120)
HALL_FOG = 0x0A160E       # note #66 (2026-11-23): a near-black green, so the walls fade into the night like the sky above (was 0x50585C, grey mist: flat grey walls against the black sky)
HALL_FOG_DENSITY = 240    # note #66: thinner with the dark colour, or nothing would show (360 as grey: note #26; 96, 200, 280 before)
# Two rows of monoliths flanking the way downrange: green marble slabs 80 long, 32 deep, corners cut
# on the aisle side, the carved ring (MARBFAC2) wrapped round towards the aisle (note #3),
# on a base 16 wider all round and 16 up, a little brighter than the hall. The slab stands 128 above
# its base (one face texture), 48 below the ceiling.
# Note #4: all the ring (MARBFAC2), the mapper's favourite of the three; the skull (MARBFACE) and the
# alien (MARBFAC3) are kept for another use.
FACE = "MARBFAC2"
FACE_STAR = "CACOSTAR"       # textures/CACOSTAR.png: the mapper's artwork (art/), scaled to 128 x 128
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
BRIDGE = (-40, 104)             # since note #68 the landing's stone, not a bridge: its west and east edges
LANDING = {}                    # its sector (set in build(), used by west_water)
# Note #88 (2026-11-26): no stone slab any more: the landing (and the mouth under it) is the hall's dirt,
# level with it (it was FLOOR7_2, 8 up). Its sector stays, so the water east of it still meets it.
LANDING_UP, LANDING_LIP, LANDING_FLAT = 0, 18, HALL_FLOOR
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
WICKET_TEXTURE_HIGH = 112
WICKET_STEP, WICKET_SILL = 4, "FLAT5_2"     # note #55: a slight wooden step through the small door
# Note #58: the small door set into the leaf, in its own rusted metal frame: a recess FRAME[0] deep in
# the leaf's face, FRAME[1] wider than the door each side and FRAME[2] taller, lined with the elevator
# track's rusty metal (SUPPORT3); the door at its back. Posts of the frame stand either side of the door
# through the rest of the leaf.
FRAME = (4, 4, 4)
FRAME_TEXTURE = "SUPPORT3"
LEAF_THICK = 12
# Note #50: the small door is human-sized (64 x 72) and the leaf goes on above it, as a lintel. Centred in
# the left leaf. It slides up into the leaf and comes back down (Door_Raise on WICKET_TAG; it sank into
# the floor until note #1 of 2026-11-23).
WICKET = (15, 79)               # along the left leaf from its hinge
WICKET_HIGH = 72
WICKET_TAG = 501
# Note #72: a pinky couldn't follow into the vestibule (a 76 opening beside the right leaf's hinge, then
# a tight turn). Now twice as deep, rounded, its north-east side curving back down to a wide opening
# onto the passage (about 122, slanted). Its outline from the west jamb's back corner round to the
# east one's, (u, d) in the doorway's frame; the passage's first cross-section is the opening.
# Note #121 (2026-11-24): bloated out to the west and the back for a few wooden boxes (it was ((-112, 16),
# (-128, 112), (-88, 184), (16, 208), (104, 184), (136, 136))).
VESTIBULE_OUTLINE = ((-112, 16), (-190, 60), (-206, 176), (-140, 230), (0, 260), (104, 210), (136, 136))   # (its 3rd point from (-200, 150): a longer wall for the side passage's wider mouth)
# The boxes: strictly wooden (no tech crates): the map's own wood, as the shell niche and the cistern's
# platform. (u0, d0, u1, d1 in the doorway's frame, height): two along the back wall, a small one out in the room.
VESTIBULE_BOXES = ((-130, 160, -66, 224, 64), (-40, 196, 8, 244, 48), (-96, 120, -64, 152, 32))
VESTIBULE_BOX_SIDE, VESTIBULE_BOX_TOP = "WOOD1", "FLAT5_2"
VESTIBULE = (224, 96)           # width, depth (from the wall); note #63: smaller (was 256 x 176), the
                                # passage leading on from its east side
VESTIBULE_LIGHT = 72
# Note #118 (2026-11-26): the beam through the crack: (d from the doorway, half width) along it, and each band's floor light.
CRACK_BEAM = ((60, 6), (96, 12), (136, 20), (176, 28))   # starts clear of the swung leaves (their backs reach about 50 in)
CRACK_BEAM_LIGHT = (136, 112, 92)
CRACK_BEAM_COLOUR = 0x9CFFB0
VESTIBULE_GLOW = (180, 50, 24, 144)   # note #13: from the torch in the wall now (was mid-room, radius 112)
VESTIBULE_TORCH_WALL = 5              # the wall of the torch the red glow comes from (it was 1, vestibule.wall_2: now the side passage's entrance)
VESTIBULE_SIDE_WALL = 1               # between VESTIBULE_OUTLINE's points 1 and 2: the side passage's entrance
VESTIBULE_TORCH_WALLS = (5, 0)         # note #126: one in vestibule.wall_6, beside the way out to the passage. (The first
                                      # torch's wall, 1, is the side passage's entrance now: chat, 2026-11-24.)
                                      # Note #139: and one in vestibule.wall_1 (0), the wall left of the great door as you come in.
# Chat, 2026-11-24: a side passage, an alternative way round. Its entrance takes the place of the vestibule's
# first torch niche (the vestibule's west wall); it snakes west, then north up and round the outside of the
# main passage, hugging the map, curls east and south, and comes out where the torch niche of the main
# passage's 12th piece was (its outer wall). The same mossy stone, climbing a step at a time. Its middle
# line, in map units, between the two openings (each SIDE_MOUTH wide; the passage itself SIDE_WIDE):
SIDE_PATH = ((-300, 2150), (-360, 2240), (-370, 2400), (-340, 2560), (-260, 2720), (-140, 2850), (20, 2920),
             (200, 2945), (380, 2935), (500, 2895), (572, 2838))
SIDE_WIDE, SIDE_MOUTH, SIDE_HIGH = 128, 88, 112     # the mouths 88 (72 until note #130): 72 clear between the frame's posts
SIDE_EXIT_MOUTH = 144                 # note #137 (the way out into the main passage; the wall may allow less)
SIDE_EXIT = (11, "l")                 # the main passage's piece and wall it comes out in (PASSAGE_TORCHES had a niche there)
SIDE_TORCHES = ((1, "l"), (3, "l"), (4, "r"), (5, "l"), (7, "r"), (9, "l"), (10, "r"))   # in rough niches (note #132: the 4th piece's on its left wall, was right; note #98: one in the 5th piece's right wall, across from the storage door)
# Note #129 (2026-11-24): "even older, dirtier, more rundown" than the main passage: a greyer, duller mossy rock, mud
# underfoot, darker (56; the main passage is 80), a thin dark brown fog, and half its torches burnt out.
# Note #133: the two passages' textures swapped: "side can be more heavily green and stony, main can be more bare
# stone and dirt". The side passage has the green mossy rock the main one had (walls, floor and ceiling); the
# main passage (its pieces, niches and steps; not the vestibule, the stairs or the cistern, which keep
# PASSAGE_TEXTURE) the greyer rock and the mud floor first given to the side passage (note #129).
SIDE_WALL, SIDE_FLOOR = "A-MOSRK2", "A-MOSRK2"
MAIN_WALL, MAIN_FLOOR = "A-MOSROK", "A-MUD"
SIDE_LIGHT = 56
SIDE_LIGHT_AT = {3: 72, 4: 96, 5: 72}   # note #121 (2026-11-26): lighter by the storage door (the 5th piece), easing in and out
# Note #92 (2026-11-26): a big wooden door in the side passage's 5th piece (its left wall), and behind it a
# bulbous storage chamber full of wooden boxes, two pinkies and four imps waiting among them. All deaf
# (ambush): gunfire doesn't bring them out, only seeing the player. The shut door blocks sound as well.
# The door opens for monsters too (Door_Raise). Outline, boxes and monsters in the wall's frame: u along
# the wall from its middle, d into the rock.
SIDE_STORE = (4, "l")
# Notes #101, #102 (2026-11-26): wooden boxes against the side passage's walls, like the storage chamber's: (piece,
# side, where along the wall (0-1, its middle), length, depth out from the wall, height). 1 off the wall (so the
# wall needn't be cut), and no deeper than 40, so a pinky still passes.
SIDE_BOXES = ((2, "l", 0.32, 56, 40, 48), (2, "l", 0.62, 40, 32, 32),     # note #101: a couple against the 3rd piece's left wall
              (4, "r", 0.78, 40, 32, 40))                                   # note #102: beside the 5th piece's torch
STORE_TAG = 11
STORE_DOOR_WIDE, STORE_DOOR_THICK = 112, 16
STORE_FRAME = 8             # note #117: the door's frame on the room's side
# Note #127 (2026-11-26): the way round behind the box wall: a small chamber behind the middle box of the wall
# (STORE_BACK's 3rd), reached by a long back tunnel from a new box room off the station's north corridor; a switch
# in the chamber sinks that box (Floor_LowerToLowest), opening a shortcut into the storage room.
STORE_SHORTCUT, STORE_SHORTCUT_TAG = 2, 12     # which of STORE_BACK, and its tag
STORE_SHORTCUT_STEP = 8                        # note #142: the step it leaves when it sinks
STORE_SWITCH_WINDOW, STORE_SWITCH_SHUTTER_TAG = (423, 455), 15   # note #149: the switch's niche (d along the wall), its shutter's tag
STORE_SHORTCUT_PRIZE = ((2048, 1, 368), (2049, 29, 368), (2018, 15, 392))   # note #143: bullets, shells, green armour on top; note #150: kept 29 from the box's sides (a pickup's square, 20 each way, reaches 28 at a slant in this turned room), or the taller boxes beside it held them up when it sank
STORE_BACKWAY_D = 470                          # the chamber reaches this far back (d), behind the box at about 405
BACKWAY = {}                                   # the chamber's sector, far edge and floor, for the tunnel (station())
STORE_HIGH, STORE_LIGHT = 160, 72
STORE_OUTLINE = ((110, 40), (190, 110), (230, 220), (208, 300), (150, 345), (60, 355), (-30, 355), (-120, 350),
                 (-201, 330), (-250, 240), (-220, 120), (-130, 50))
# Note #112 (2026-11-26): the back of the room crowded with a wall of boxes, so there's no going back there: the room
# ends at their fronts (STORE_OUTLINE from (208, 300) to (-201, 330)), and the boxes fill the space to the old back
# walls, each its own height (none climbable). Each: its outline (front first, then round by the old wall), height.
STORE_BACK = ((((208, 300), (150, 345), (150, 361.8), (200, 330)), 80),
              (((150, 345), (60, 355), (60, 402), (90, 400), (150, 361.8)), 112),
              (((60, 355), (-30, 355), (-30, 408), (60, 402)), 56),
              (((-30, 355), (-120, 350), (-120, 382.3), (-60, 410), (-30, 408)), 128),
              (((-120, 350), (-201, 330), (-190, 350), (-120, 382.3)), 72))
# Note #97 (2026-11-26): fully navigable: the boxes in two clusters (boxes in a cluster touch, sharing a side),
# at least 59 from the walls and 70 apart, so nothing snags on the way round. Then pickups: 50 health
# (a medikit, two stimpacks, five bonuses), 50 armour (fifty bonuses, in short trails; gone in note #103), a box of shells.
STORE_BOXES = ((-160, 170, -96, 234, 96), (-96, 170, -48, 234, 48), (-160, 234, -96, 282, 64),
               (70, 150, 134, 214, 64), (70, 214, 134, 262, 48), (22, 150, 70, 214, 32))
STORE_DOOR_TORCHES = ((46, -84, 44), (46, 84, 44))   # note #113: tall red torches either side of the door, inside
STORE_MONSTERS = ((3002, -20, 300), (3002, 170, 290),                      # note #112: out of the new box wall
                  (3001, -200, 190), (3001, -60, 270), (3001, 100, 110), (3001, 40, 300))
# Note #103 (2026-11-26): no armour; the health and the shells up on the boxes, where the player bumps into them
# from the floor: only on boxes no higher than 48 (a pickup on a box is touched while it is lower than the
# player's 56), 10 in from a side the player can walk up to.
STORE_PICKUPS = ((2012, ((46, 160),)),                                     # the medikit: on the 32-high box
                 (2011, ((-72, 180), (102, 252))),                         # the stimpacks: on the two 48-high ones
                 (2014, ((32, 204), (60, 204), (-58, 224), (-58, 200), (124, 230))),
                 (2049, ((80, 240),)))
SIDE_FOG = (0x0E0C08, 180)
SIDE_CARVING = (8, "r")       # note #134: a carved alcove like the passage's in the 9th piece's right wall
SIDE_CARVING_ITEMS = (2015,) * 5     # armour bonuses (ARMOR_BONUS is defined further down)
# Note #136 (2026-11-24): two shadow imps lurking in it, deaf (ambush: they wake on seeing the player): (piece, the way
# it faces): in the 9th piece facing west, in the 12th facing south. "Shadow": drawn as a dark shape (UDMF
# renderstyle "shadow", as the switch obelisk's cacodemon is by its script); ordinary imps otherwise.
SIDE_IMPS = ((8, 180), (11, 270))
SIDE_TORCHES_OUT = set()      # note #131: none: "all the torches on the side passage should be lit" (three were out in note #129)
SIDE: dict = {}                       # filled as the map is built: its sectors, and its two openings' ends
# Note #59: two imps waiting behind the great doors, facing them. (u, d) in the doorway's frame. Note #62:
# not ambush (deaf) any more: shooting one through the gap left the other asleep; now gunfire wakes both.
IMP = 3001
VESTIBULE_IMPS = ((0, 76), (60, 72))     # note #138: the first straight behind the gap between the leaves, to be glimpsed through it (it stood at (-56, 64))
# Note #9 (2026-11-23): a third imp, deaf (ambush), in the vestibule's back corner behind the left leaf:
# gunfire draws the other two out, this one waits for whoever comes through the small door.
VESTIBULE_AMBUSH_IMP = (-120, 70)     # beside the side passage's entrance, out of its way (it stood in front of the torch that was there)
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
CISTERN_WALL = "A-MOSROK"        # note #123: STARG3 (sewer works); note #128: back to the mossy rock; note #133: the main passage's greyer rock (MAIN_WALL), carried on down the stairs, through the cistern and the shotgunner room
TORCH = 57
# Niches (piece, side "l"/"r"): 24 wide, NICHE_DEEP deep, NICHE_HIGH high, in the middle of that wall.
# Note #70: pinkies still stuck at a bend. The niches had a sill 24 up and were 48 high: a monster (56
# tall) brushing a niche's mouth was stopped (too little headroom), and the torch (radius 16) stuck out
# of the 12-deep niche, one right on a bend's inside corner. Now the niches start at the floor, 72 high,
# 24 deep, the torch 14 in (wholly inside), and torches are on the outside of the bends.
NICHE_DEEP, NICHE_HIGH, NICHE_TORCH_IN = 24, 72, 14
PASSAGE_TORCHES = ((1, "l"), (3, "r"), (5, "l"), (7, "l"), (9, "l"), (13, "r"), (14, "l"))   # ((11, "l") is the side passage's way out now)
# Chat, 2026-11-24: some torches are out: the map's own unlit torch (textures.txt, zscript.zs
# CacobeliskDeadTorch: the bowl with grey smoke, no light), swapped in for torches with this thing id;
# their niches are no brighter than the passage. A first pair as a sample: the mapper says which.
DEAD_TORCH_TID = 320
ALTAR_TORCH_TID = 321     # note #109: the altars' torches (zscript.zs)
PASSAGE_TORCHES_UNLIT = set()   # note #75: every torch in the vestibule and the passage is lit (a sample pair was out: 5 l, 11 l); the dark starts at the cistern stairs (STAIR_TORCHES)
# Note #65: a few pinkies in the wider stretch, imps behind them: (piece, type, along 0-1, across 0-1 from
# the left), all facing back up the passage.
PINKY = 3002
# Note #69: a cache of shotgun ammo on the right just into the passage: a box of shells (20). Note #73:
# on a shelf in a niche in the right wall, not on the floor; and 2049 (2048, used at first, is a box of
# bullets). Shelves (piece, side, thing): a niche 48 wide, 24 deep, its floor 32 up, 24 high, lit as the
# passage (note #76); the item 12 in, so the player can reach it from the passage.
SHELL_BOX = 2049
# Note #87 (2026-11-26): a secret wall in the main passage: the right wall of its 10th piece (48 long, where it
# turns towards the 11th) in a slightly different mossy rock (the side passage's), which opens on use onto
# an alcove with a chaingun; taking it counts as the map's second secret.
PASSAGE_SECRET = (9, "r")
PASSAGE_SECRET_TAG = 10
PASSAGE_SECRET_TEX = "A-MOSRK2"
PASSAGE_SECRET_ALCOVE = 56      # deep, behind the door (8 thick)
PASSAGE_SECRET_HIGH = 68        # note #90: the alcove's height: the door opens to 4 under it (64), not to the passage's ceiling
CHAINGUN = 2002
PASSAGE_ITEMS = ()
SHELF_FRAME = (6, 4)            # note #8: the wooden frame round a shelf's box: border, depth
PASSAGE_SHELVES = ((1, "r", SHELL_BOX),)   # the 2nd piece: the 1st's right wall is right against the hall's
# Note #4 (2026-11-23): a blank wall on the way down (piece, side) gets a big carving set into it: the
# hall's green marble skull (MARBFACE, 128 x 128; kept back from the obelisks, 2026-11-22 note #4) at the
# back of a marble alcove 128 wide, CARVING_DEEP deep, its sill CARVING_SILL up: the sill is a shelf with
# two stimpacks. Lit a little above the passage, so the face reads in the dark.
PASSAGE_CARVINGS = ((12, "l"),)
# Note #5 (2026-11-23): the skull read as significant; now a patterned marble panel (MARBLE3, no face), lit
# only a little above the passage (96, was 112), so it's plainly decoration.
# Note #125 (2026-11-24): the satyr's face swapped for the obelisks' eye: CACOFACE (textures/CACOFACE.png: GSTSATYR with
# MARBFAC2's carving scaled down and blended over the face; the stone round it is the satyr's own).
CARVING_TEXTURE, CARVING_SILL, CARVING_DEEP, CARVING_LIGHT = "CACOFACE", 32, 24, 96
# Note #10 (2026-11-23): the mapper's pick, GSTSATYR, once only: the texture is 64 wide (one face), so it
# takes the middle 64 of the alcove's 128-wide back, with plain gothic stone (GSTONE1, which the face is
# carved in) either side, its blocks carried on across the three stretches, and on the alcove's sides.
CARVING_WIDE, CARVING_STONE = 64, "GSTONE1"
# Note #67: spread out, one pinky a piece (two shared a piece, wedged side by side).
# Note #80: the 2nd pinky at the passage's peak (piece 9, where it starts down), away from the others.
PASSAGE_MONSTERS = ((11, PINKY, 0.5, 0.4), (9, PINKY, 0.5, 0.5), (13, PINKY, 0.3, 0.5),
                    (13, IMP, 0.85, 0.3), (14, IMP, 0.5, 0.7))
# Note #9 (2026-11-23): gunfire in the obelisk hall woke every pinky in the passage (sound carries through
# every open two-sided line, however far). Sound passes one sound-blocking line and stops at the second:
# the two steps after the first pinky's piece (passage_10) block sound, so that pinky still comes, and
# the pinkies and imps further on (passage_12 on) only hear shots fired past those steps. The other way
# round, through the drain, is closed the same way (the grates and the cistern's west wall).
PASSAGE_QUIET = (10, 11)        # the steps into passage_11 and passage_12
DRAIN_TOP = -DROP + 16
DRAIN_FLOOR = -DROP - 16
DRAIN_DEPTH = 96          # note #39: deep enough that its far wall is out of sight (was 16)
DRAIN_LIGHT = 32          # note #39: darker (was 64)
DRAIN_GRATE = "MIDVINE1"
# Note #96 (2026-11-24): the hall stands on the edge of a cliff. Where the west gutter meets the wall (the west
# side, and the south side west of the landing) there is no wall and no drain any more: the water runs to
# the edge and over it, a railing along the edge (so nobody falls: the line is impassable), and beyond it
# only sky, above and below. Built from the west drain's sector: its floor far down and sky, like its
# ceiling, and round its far side a strip with no height (floor = ceiling, sky), which the engine shows
# as open sky instead of a wall.
CLIFF_FLOOR = -DROP - 1024
CLIFF_RAIL = "MIDBARS3"         # 72 high: the bars already used in this map; its top 64 above the hall's floor
CLIFF_FALL = "SFALL1"           # down the cliff's face under the edge (out of sight from the hall)
CLIFF_HORIZON = 16
CLIFF_RAIL_SUNK = 48            # note #100: how much of the railing (72 high) is sunk; note #86: 44 under the dirt; note #111: 48, so its top rail sits just under the cap (CLIFF_CAP), not in the same place: the two fought (a flicker)
# Note #89 (2026-11-26): the railing has a top: a strip CLIFF_LEDGE wide just beyond it (the dirt runs on
# under it), carrying a 3D floor CLIFF_CAP thick whose top is the railing's top, in the bars' own texture
# (control sector at CLIFF_CAP_CONTROL, outside the map), so looking over it has depth.
CLIFF_LEDGE, CLIFF_CAP = 4, 4
CLIFF_CAP_TEX = "CACORAIL"      # note #108: the rail's brown bar only (textures.txt); MIDBARS3 as a flat streaked the cap
CLIFF_CAP_TAG, CLIFF_CAP_CONTROL = 403, (720, -96)   # (where the bridge's control sector was)
# Note #106 (2026-11-26): with the gutter gone the west side felt empty: the cliff's edge comes in now and then
# towards the obelisks (never nearer than about 100 to their bases, x -176), south to north between the pier's
# stretch and the north wall; and three dead trees stand on that side (CLIFF_TREES: type, x, y).
CLIFF_EDGE = ((-372, 420), (-290, 560), (-330, 700), (-376, 820), (-372, 980), (-280, 1110), (-300, 1240),
              (-360, 1360), (-378, 1520), (-300, 1640))
CLIFF_TREES = ((54, -310, 440), (43, -310, 1000), (54, -290, 1760))   # 54: a large brown tree; 43: a grey (burnt) one
CLIFF_PIER = 64                 # note #98: the south wall turns the corner this far up the west side, as a pier
# Note #77 and the mapper's editor save (22:36): the passage goes down, in CISTERN_STEPS steps, into a big
# dark room east of the hall (the cistern: CISTERN_EAST, its east and south walls as drawn), whose west
# wall is the far side of the drain behind the hall's east wall. That wall, facing the obelisk hall, is
# all water pouring down (SFALL: the gutter's NUKAGE falling), above and below the slot through the drain
# (32 high, 96 deep), and the floor is flooded (the player wades). From down here the player looks up
# through the slot and the vines into the obelisk hall. Very dark, very foggy.
CISTERN_FLOOR = -DROP - 64
CISTERN_TOP = 256             # note #16 (2026-11-23): out of sight in the dark (576 above the water; was -128, 192)
CISTERN_EAST = ((768, 1760), (832, 192))       # its north-east and south-east corners (editor save)
# Note #82: three spectres (shadow pinkies, 58) along the cistern, ambush, facing the way the player comes
# down (north).
SPECTRE = 58
# Note #11 (2026-11-23): asleep until touched or hurt (they don't hear or see the player): zscript.zs swaps
# the things with this id for CacobeliskSleeper when the level loads.
SLEEPER_TID = 310
# Note #7 (2026-11-23): spread further: the northmost where it was, the other two further down towards the
# cistern's south end (were at y 880 and 430).
# Editor save 2026-11-23 15:59: the northmost spectre (spectre_1, at (650, 1350)) removed by the mapper;
# the other two keep their numbers.
CISTERN_SPECTRES = {2: (690, 760), 3: (624, 436)}   # note #17: the 3rd in front of the platform (was y 270)
# Note #17 (2026-11-23): at the cistern's south end, a waterlogged wooden platform (an island just clear of
# the walls, its boards CISTERN_PLATFORM_UP above the water) with a dais on it carrying a switch: a wooden
# post at the back of the dais, the switch (SW1WOOD's ring, rows 64-112 of the texture) on its north face,
# towards the player coming down the cistern. The switch does nothing yet (the mapper to say what).
CISTERN_PLATFORM = (590, 216, 770, 376)        # x0, y0, x1, y1
CISTERN_PLATFORM_UP = 4         # (until note #20: the boards' height above the water)
# Note #20 (2026-11-23): the dais sits up on a grating, like the bridge over the hall's channel: the
# platform is a metal grate (a 3D floor: CISTERN_GRATE = its underside and top above the water, FCGRATE2,
# its control sector outside the map at CISTERN_GRATE_CONTROL) standing on bars (MIDBARS3 squeezed into the
# gap), the water running on beneath it. The dais (wood, 8 above the grate) and its post rise through it.
CISTERN_GRATE = (12, 16)
CISTERN_GRATE_TAG = 602
CISTERN_GRATE_CONTROL = (784, -96)
CISTERN_GRATE_FLAT, CISTERN_GRATE_SIDE = "FLAT5_2", "WOOD1"   # note #47: wooden boards (was a metal grate: FCGRATE2, SUPPORT3); the bars under it stay
# Note #19 (2026-11-23): dim candlelight on the dais: two candles (34: the smallest flame Doom has, and it
# doesn't block the way to the switch; UZDoom's lights.pk3 gives it its glow), either side of the post.
CANDLE = 34
GREEN_ARMOR = 2018
CISTERN_ARMOR = (680, 228)      # note #50: behind the post (y 248-264) and the dais, out of sight from the north
CISTERN_CANDLES = ((646, 288), (714, 288))   # note #24: forward of the post, lighting the switch face (were beside it, y 256)
CISTERN_DAIS = (632, 240, 728, 336)            # 12 above the boards
CISTERN_POST = (648, 248, 712, 264)            # 48 above the dais
CISTERN_WOOD, CISTERN_BOARDS, CISTERN_SWITCH = "WOOD1", "FLAT5_2", "SW1WOOD"
# Note #18 (2026-11-23): the water flows away from the obelisk hall, slow and lazy: the west gutter and its
# drain west, the east gutter and its drain east (they part under the bridge, out of sight), and the
# cistern's on east, out through a low drain along its east wall (CISTERN_OUT: high, deep). Using the
# switch on the dais turns the cistern's water south and speeds it up a little. zscript.zs
# (CacobeliskWater) moves the water's picture each tic, by sector tag; the player isn't carried.
# (The mapper wrote "west" for the east drain and the cistern too; "away from the obelisk room" is east
# on that side: Claude's reading.)
CISTERN_TAG = 600
# Note #41 (2026-11-23): the cistern's switch slowly opens a big wooden door in the west wall of the stairs
# down (their 2nd flight), the way forward: Door_Open on the switch itself (tag, speed 4: about 5 s), so
# the movement check follows it. Behind it a chamber (width along the wall, depth) with two shotgunners
# and a red glow that comes on as the door starts to open. Beyond the chamber: nothing yet.
CISTERN_DOOR_STAIR = 3          # note #53: the 3rd flight (was the 2nd)
CISTERN_DOOR_TAG = 7
CISTERN_DOOR_WIDE = 112
CISTERN_DOOR_TEXTURE = "BIGDOOR6"
# Note #53 (2026-11-23): the chamber about twice as big and less boxy: its outline (along the wall from the
# door's middle, away from the stairs), from the door's far side round to its near side; about 330 x 280.
# (It was a 192 x 192 box.)
# Note #77 (2026-11-24): a little bigger (about 350 x 340), with a straight far wall (its 5th: (40, 352) to
# (-56, 352)) for the tech door. It was ((96, 16), (150, 60), (168, 150), (120, 250), (30, 296), (-70, 280),
# (-150, 200), (-160, 90), (-110, 24)).
# Note #91: the south side out by about 40 ((176, 160) and (170, 270) before), so there is a way round behind
# the crates (56 wide) to the medikit.
# (Note #122 made the far wall 128 wide for a wider door frame; note #124 took that back.)
# Note #91 (2026-11-26): the far wall 32 wider (the door's posts carry a lamp each): (56, 352) to (-72, 352).
# Note #132 (2026-11-26): wider: the north side out 64 ((-160, 270), (-176, 100) before), the south-east corner 48
# ((214, 280) before; the cistern's outflow channel lies just south of the rest).
CISTERN_DOOR_OUTLINE = ((96, 16), (168, 56), (212, 150), (262, 280), (56, 352), (-72, 352), (-224, 270),
                        (-240, 100), (-110, 24))
# Note #77: the room is where the mossy rock ends and the rusty tech of the start comes back. Wooden crates
# in it (u0, d0, u1, d1 in the room's frame, height, side texture, top flat): cover from the shotgunners,
# clear of where they stand and of the way to the far door.
CISTERN_DOOR_CRATES = ((90, 130, 154, 194, 64, "CRATE1", "CRATOP2"), (90, 194, 154, 258, 96, "CRATE2", "CRATOP1"),
                       (-90, 240, -26, 304, 64, "CRATE2", "CRATOP1"),
                       # Note #132: more, a mix of the grotto's wooden boxes and the base's containers.
                       (-200, 150, -152, 198, 48, "WOOD1", "FLAT5_2"), (-200, 198, -152, 230, 32, "WOOD1", "FLAT5_2"),
                       (-40, 90, 8, 138, 48, "CRATE3", "CRATOP2"), (104, 272, 144, 304, 40, "WOOD1", "FLAT5_2"))
# The tech door in the far wall (DOOR1, 64 x 72, in a recess lined with the track's metal, the room's rock
# above it: note #81): Door_Raise from both sides, monsters too. Behind it a corridor like the start
# closet: 128 wide, LOW high, its walls CACOBASE (METAL4 over the track strip), red light channels in
# both long walls, dim. It ends at a wall for now.
TECH_DOOR_TAG = 8
# Note #87 (2026-11-24): the twin of the cistern's switch inside the room, so the big door opens from this side
# too: the same wooden post (16 x 64, 48 high) with the skull switch (SW1WOOD) on its face towards the room's
# middle, standing clear of the north wall (u0, d0, u1, d1 in the room's frame). One use only: zscript.zs
# snaps it into the floor (tag) when either switch is used; its top is the room's rock, so nothing is left.
# Note #93: by the wall segment next to the door (the slanted one north of it); it stood one segment further on,
# at (-150, 110, -134, 174). The deaf guard of that corner moved over a little to make room.
CISTERN_DOOR_SWITCH = (-118, 56, -102, 120)
MEDIKIT = 2012
CISTERN_DOOR_MEDIKIT = (184, 230)   # note #89: stashed behind the tall crate; note #91: in the middle of the way round behind it (it was out of reach in a gap 18 wide)
CISTERN_DOOR_SWITCH_TAG = 9
TECH_DOOR_TEXTURE = "CACODOOR"   # note #88: DOOR1 darkened (the map's own, textures.txt): DOOR1 itself was "oddly bright"
TECH_DOOR_FRAME = "SUPPORT3"     # note #88: the thin wall either side of the door and above it: the track's rusty metal, as round the small door
TECH_DOOR = (-40, 24, 352)      # u0, u1 along the far wall, the wall's d
TECH_DOOR_HIGH = 72
TECH_HALL_CEIL_PAN = 20        # note #114: the tech room's ceiling stripes over the door's middle; note #124: 20 (7 moved them 7 north, as meant, not enough: measured, its two bands now sit 64 either side of the room's middle)
TECH_DOOR_UNDER = "CEIL5_1"      # note #93: the door's underside, plain dark metal
TECH_DOOR_LAMP = "CACOBAR"       # note #108 (textures.txt)
# Note #91 (2026-11-26): no lamp over the door; an upright one in each post instead: a stripe of the track's
# metal, the red tube set into the wall (a channel TECH_POST_LAMP wide and deep, from TECH_POST_LAMP_Z up to
# the door's top, glowing), another stripe: so the posts are 32 wide.
TECH_POST_STRIPE, TECH_POST_LAMP, TECH_POST_LAMP_DEEP, TECH_POST_LAMP_Z = 8, 16, 8, 8
TECH_POST_LAMP_RADIUS = (32, 64)        # each lamp's pulsing red light, smaller than the one over the door was
TECH_DOOR_POST = 2 * TECH_POST_STRIPE + TECH_POST_LAMP   # was 16              # the frame's posts either side of the door (note #122 made them 32 for a bar right across; note #124: "looks worse", back)
TECH_DOOR_LAMP_GLOW = 80         # added to the room's light on the bar's three pieces of wall
TECH_DOOR_LAMP_RGB, TECH_DOOR_LAMP_RADIUS, TECH_DOOR_LAMP_PERIOD = (255, 40, 30), (40, 104), 50
# Note #82 (2026-11-24): three times the size (it was the closet's 128 x 256) and brighter (128; the closet's
# 80 at first): this is the part of the base that is in use, where the start was a forgotten way in.
TECH_HALL_WIDE, TECH_HALL_LONG = 256, 384
TECH_HALL_LIGHT = 128
TECH_HALL_HIGH = 128             # note #84: twice the closet's 64
TECH_HALL_CHANNELS = (64, 128, 192, 256, 320)   # the light channels along each long wall
CISTERN_DOOR_ROOM_HIGH = 128
CISTERN_DOOR_LIGHT, CISTERN_DOOR_TINT = 144, 0xFF7050
CISTERN_DOOR_GLOW = (255, 70, 30, 176)
CISTERN_DOOR_GLOW_TID = 303
SHOTGUNNER = 9
# Note #48 (2026-11-23): six shotgunners (along the wall from the door's middle, behind the door, kind):
# two that come for the player the moment the switch is used ("wake"), two ordinary ones ("idle": they
# wake on seeing or hearing the player), two deaf ones ("deaf": ambush, in the corners beside the door,
# out of sight from the doorway). Not mirrored.
CISTERN_DOOR_GUARDS = ((-34, 46, "wake"), (26, 74, "wake"), (-70, 160, "idle"), (60, 210, "idle"),
                       (-78, 24, "deaf"), (100, 54, "deaf"))    # note #93: the first was at (-100, 40), where the switch post is now
CISTERN_DOOR_WAKE_TID = 304
CISTERN_DOOR_ZOMBIES = {1, 3, 5}   # note #116: guards 2, 4, 6 (one roused, one ordinary, one deaf) are zombiemen
SWITCH_TAG = 601                # the platform, dais and post: the switch lights them a little (and tells the script)
FLOW_WEST_TAG, FLOW_EAST_TAG = 610, 611
CISTERN_OUT = (20, 96)
SWITCH_LIGHT = 96
# Note #7: dim lights along the east wall (PointLightAttenuated: every CISTERN_GLOW_GAP from the north,
# 20 out from the wall, 40 above the water), pale green like the water, so a spectre crossing in front of
# one shows as a shadow. (colour, radius), alternating a little so they don't read as a row of lamps.
CISTERN_TORCH_SILL = 8          # note #78: the torch shelves one step above the water (28 at first, over the slot: too high)
CISTERN_OUTCROP = (56, 32)      # note #78: each torch's outcrop: along the east wall, out into the cistern
CISTERN_GLOW_GAP = 250
# Note #85: 72 out (40 at first: level with the outcrops' faces, 28-42 out, which a light in their own plane
# can't light: the wall above each hollow stayed black).
CISTERN_GLOW_SIDE, CISTERN_GLOW_OUT = 48, 72   # note #83: a light either side of each torch's outcrop
CISTERN_GLOWS = (((70, 120, 90), 104), ((60, 105, 85), 88))
CISTERN_LIGHT = 40
# Note #79: grey, the hall's own fog (was a near-black 0x101810 at 420: from far off the black looked
# wrong), so through the grate it all fades uniformly to grey; the drains share it (note #78).
CISTERN_FOG = (HALL_FOG, HALL_FOG_DENSITY)       # the drains (seen from the hall through the vines)
# Note #84: down in the cistern itself (and the stairs to it), less fog and darker: a near-black fog,
# thinner, so the spectres don't stand out against grey mist. The drains keep the grey (note #79).
CISTERN_DARK_FOG = (0x080808, 200)
CISTERN_DARK_LIGHT = 48     # note #7 (2026-11-23): "a little too dark": slightly up (was 32)
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
LIP_VIOLET = 0x2E0555             # VIOLET x 35/104 (note #31)
VIOLET = 0x8A10FF                 # note #41: saturated (was 0xB060FF, which came out a lavender grey)
SLIT = (32, 48, 4, 32)            # along the back from the slab's y0: 32-48; 4 deep; 32 high above the base
SLIT_CONTROL, SLIT_CONTROL_TAG = (848, -96), 402   # note #107: the 3D floor above the slit's hollow (zscript.zs)
LIP_TAG = 401                     # note #101: the lip in front of the slit (zscript.zs LIP_TAG)
SLIT_TAG = 400                    # zscript.zs opens it upwards as the sleeve sinks
RIVULET = {}                      # the gutter piece the rivulet belongs to (set by violet_gutter)
GUTTER_E_WEST_EXTRA = {4: ((347, 1535), (240, 1552), (240, 1568), (348, 1580))}
GUTTER_E_SHARED = {((240, 1552), (240, 1568)),   # built by monolith(): the base's edge under the slit
                   ((138, 270), (129, 327))}     # built by west_water(): where the crossing channel joins
# Note #41: "lose the grey-out": the colours were pale (lots of green in them), so the desaturated water
# came out grey; now saturated violets (were 0xE8D8F0, 0xD8B8F0, 0xC890F0, 0xB060FF, 0xC080FF).
# Note #22 (2026-11-23): both gutters plain green again: no violet in the east one (the mapper's earlier
# idea, withdrawn). The pieces keep their cuts and names (gutter_e.violet_N), so nothing else moves; the
# rivulet from the switch obelisk, part of piece 4, is green with them. The obelisk's own violet leak (its
# slit and the spill on its base) is unchanged. Was: (0.25, 0xD8A0FF), (0.5, 0xC070FF), (0.75, 0xA040FF),
# (1.0, 0x8A10FF), (0.9, 0x9A30FF) for pieces 1-5.
# Note #25 (2026-11-23): violet after all, but only where the leak meets the gutter. The rivulet across the
# walkway is its own sector again, full violet, and where it runs into the gutter the violet spreads and
# fades in concentric rings, as if rippling out into the green: round islands in the gutter's water
# (VIOLET_RINGS: centre, then (radius, desaturation, colour) from the outside in; they must stay inside
# the gutter, which is about 95 wide there). The rest of the gutter is green.
# Note #30 (2026-11-23): the rings spread from the point of entry itself: half rings centred on the middle
# of the rivulet's mouth, on the gutter's west edge (they were whole circles out in the gutter in front of
# it). The innermost holds the whole mouth, so the little fall there is drawn by a desaturated sector and
# comes out violet (drawn by the green gutter it stayed blue). Radii must reach past half the mouth (23)
# and stay inside the gutter piece (66 south of the mouth's middle, about 95 across).
VIOLET_RINGS = ((66, 0.3, 0xD8A0FF), (52, 0.6, 0xB860FF), (38, 0.85, 0x9A30FF), (26, 1.0, 0x8A10FF))
VIOLET_RING_STEPS = 10          # lines in each half ring
GUTTER_E_VIOLET = ((0.0, None),) * 6   # (desaturation, floor colour) per piece, south to north; None = untinted
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
    # Note #134 (2026-11-26): the car's floor a little recessed (CAR_RECESS below the closet's), in AQF072.
    car = m.sector("car", floor=-CAR_RECESS, ceiling=LOW, light=CLOSET_LIGHT, floor_tex=CAR_FLOOR)
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
    # Note #100 (2026-11-26): the lowered strip round the coffer (the closet's own ceiling: the coffer covers the
    # rest) and the step's faces looking in from the coffer are the elevator's track metal.
    m.sectors[closet.index]["textureceiling"] = TRACK
    for ln in m.linedefs:
        if ln["user_gid"].startswith("closet.coffer.edge_"):
            m.sidedefs[ln["sideback"]]["texturetop"] = TRACK_TURNED   # note #105: the track on its side, lines along the edge
    start_door(m, closet, coffer, (cx0, cy0), (cx1, cy0), (kx0, kx1))
    # Editor save 2026-11-22 01:42: the closet's far corners cut on the diagonal, (-32, 128) to
    # (-32, 104)-(-24, 120) and (96, 128) to (88, 120)-(96, 104).
    wall_with_channels(m, closet, (cx0, cy0), (cx0, cy1), "closet.wall_w", end=((-32, 104), (-24, 120)))
    m.wall((-24, 120), (-16, cy1), closet, "closet.wall_nw")    # note #107: to the shaft block's outer edge, -16 (was -8)
    back = m.two_sided((64, 128), (0, 128), car, closet, "car.back")
    m.sidedefs[m.linedefs[back]["sidefront"]]["texturebottom"] = TRACK
    m.wall((80, cy1), (88, 120), closet, "closet.wall_ne")      # note #107: from 80 (was 72)
    wall_with_channels(m, closet, (cx1, cy1), (cx1, cy0), "closet.wall_e", start=((88, 120), (96, 104)),
                       panel=(3, secret_panel))

    # The platform: 64 x 64 (y 128-192). Its side walls and the wall either side of the niche face
    # solid blocks (shaft_w, shaft_e: floor and ceiling at 0), so the shaft shows plain wall above
    # the starting floor and the track below it as the platform goes down.
    shaft_w = shaft_side(m, car, closet, "shaft_w", x_wall=0, x_out=-16, x_pillar=NICHE_X0)   # note #107: 16 thick (was 8)
    shaft_e = shaft_side(m, car, closet, "shaft_e", x_wall=64, x_out=80, x_pillar=NICHE_X1)
    m.player_start(32, cy0 + 24, angle=90)

    # The niche (x 8-56, y 192-200). The switch is its back wall: a two-sided line onto the mouth,
    # sealed while the niche's floor is up (the mouth's ceiling is at 0), the switch texture its
    # upper part, pegged to the niche's top so it stays up there. Floor_LowerByValue (20: tag, speed,
    # height), once, on CAR_TAG: the platform and the niche's floor go down together, and the niche
    # becomes the way through (48 wide, a 16 step up from the platform). The niche is the front side.
    # Note #36 (2026-11-23): once the switch is used a panel comes down in front of it (the mapper: the
    # plate must not just vanish). The last SHUTTER_DEEP of the niche, right in front of the switch, is a
    # sector of its own, the shutter: its floor goes down with the niche's (CAR_TAG), and zscript.zs
    # lowers its ceiling (its second tag, SHUTTER_TAG) from the niche's top to its sill, so the panel
    # (SHUTTER_TEXTURE, the upper part of the line between the two, riding down with that ceiling)
    # covers the switch's window, while the way through below stays open.
    # Notes #44, #45: the window is SWITCH_WINDOW wide, the panel texture's one tile and the switch's
    # plate, like the bottom niche (its twin): the rest of the niche's width, either side, is a cheek of
    # track metal (a sector shut down to the sill: floor = ceiling there until the floor drops with the
    # platform, after which it is part of the way through, 48 wide below as before). No cement shows.
    ys = 200 - SHUTTER_DEEP
    wx0 = (NICHE_X0 + NICHE_X1 - SWITCH_WINDOW) / 2
    wx1 = wx0 + SWITCH_WINDOW
    metal = dict(light=NICHE_LIGHT, floor_tex=LIP_TOP, ceiling_tex=TRACK)
    shutter = m.sector("niche.shutter", floor=NICHE_FLOOR, ceiling=NICHE_TOP, **metal)
    m.sectors[shutter.index].fields.update(id=CAR_TAG, moreids=str(SHUTTER_TAG))
    cheeks = {}
    for name, x0, x1, shaft in (("w", NICHE_X0, wx0, shaft_w), ("e", wx1, NICHE_X1, shaft_e)):
        cheek = m.sector(f"niche.cheek_{name}", floor=NICHE_FLOOR, ceiling=NICHE_FLOOR, **metal)
        # user_scenery: the movement check takes each 8-wide cheek for a gap too narrow to pass and reports
        # it unreachable; in the game it's part of the 48-wide way through once its floor is down. (The
        # check therefore reads the way through as 32 wide, and says imps can't follow there: they can.)
        m.sectors[cheek.index].fields.update(id=CAR_TAG, user_scenery=True)
        cheeks[name] = cheek
        # Note #110 (2026-11-26): the switch's wall like the car's other walls: the tech wall (CLOSET_SKIN) either side of the
        # switch, and the track's strip along the foot (TRACK, the 16 below the niche, pegged as the side walls' are).
        ln = m.two_sided((x0, 192), (x1, 192), car, cheek, f"niche.cheek_{name}.face", texture=CLOSET_SKIN)
        m.sidedefs[m.linedefs[ln]["sidefront"]]["texturebottom"] = TRACK
        outer, a, b = (x0, (x0, 192), (x0, 200)) if name == "w" else (x1, (x1, 200), (x1, 192))
        # Note #109 (2026-11-26): the way out's two thin jambs (8 deep) in the door track (DOORTRAK), not the elevator's.
        ln = m.two_sided(a, b, cheek, shaft, f"niche.side_{name}", texture=JAMB_TRACK)   # against the shaft's solid block
        m.linedefs[ln]["blocking"] = True
        ln = m.two_sided((x0, 200), (x1, 200), cheek, mouth, f"niche.cheek_{name}.back", texture=TRACK)
        m.sidedefs[m.linedefs[ln]["sideback"]]["texturebottom"] = LIP_FACE
        # Its side of the window: the niche in front, the shutter behind.
        inner = x1 if name == "w" else x0
        for sec, y0, y1, part in ((niche, 192, ys, "niche"), (shutter, ys, 200, "shutter")):
            a, b = ((inner, y0), (inner, y1)) if name == "w" else ((inner, y1), (inner, y0))
            m.two_sided(a, b, sec, cheek, f"niche.cheek_{name}.{part}", texture=TRACK)
    lip = m.two_sided((wx0, 192), (wx1, 192), car, niche, "niche.mouth")
    m.sidedefs[m.linedefs[lip]["sidefront"]]["texturebottom"] = TRACK   # the lip's face, from the platform: note #110, the track's strip (was STEPTOP)
    panel = m.two_sided((wx0, ys), (wx1, ys), niche, shutter, "niche.shutter.panel", texture=TRACK)
    m.sidedefs[m.linedefs[panel]["sidefront"]]["texturetop"] = SHUTTER_TEXTURE
    switch = m.two_sided((wx0, 200), (wx1, 200), shutter, mouth, "niche.switch")
    # Note #120 (2026-11-26): Floor_MoveToValue (37) to -DROP, like the bottom call switch: Floor_LowerByValue took
    # everything down 256 from where it was, so the niche's floor (16 up) stopped 16 above the bottom, a step.
    m.linedefs[switch].fields.update(special=37, arg0=CAR_TAG, arg1=CAR_SPEED, arg2=DROP, arg3=1, playeruse=True)
    # The lip's other face: the passage's side of this line, below the niche's floor (16 once it's down).
    m.sidedefs[m.linedefs[switch]["sideback"]]["texturebottom"] = LIP_FACE
    front = m.sidedefs[m.linedefs[switch]["sidefront"]]
    front["texturetop"] = SWITCH_TEXTURE
    front["offsetx"] = 16    # the 64-wide texture's plate (x ~16-47) fills the 32-wide window
    # Note #42 (2026-11-23): the plate was hung from the ceiling in front of it, which is the shutter's now:
    # it came down with the panel. It hangs from the mouth's ceiling behind it instead (an upper part's
    # default: the texture's foot at the lower ceiling, which never moves), moved so the plate (rows
    # ~70-102) is still in the niche's window: row 69 at the niche's top.
    front["offsety"] = 69 - (128 - (NICHE_TOP - m.sectors[mouth.index]["heightceiling"]))
    pulse = m.thing(9831, 32, 194, "niche.pulse", angle=SWITCH_PULSE_PERIOD)
    m.things[pulse]["id"] = SWITCH_PULSE_TID       # note #36: goes out when the shutter comes down
    m.things[pulse].fields.update(height=16, arg0=SWITCH_PULSE_RGB[0], arg1=SWITCH_PULSE_RGB[1],
                                  arg2=SWITCH_PULSE_RGB[2], arg3=SWITCH_PULSE_RADIUS[0], arg4=SWITCH_PULSE_RADIUS[1])

    # The mouth: straight on from the platform, into the room, flaring out (editor save 2026-11-22 01:25:
    # its far corners from (0, 264) and (64, 264) out to MOUTH_W and MOUTH_E).
    # Note #99 (2026-11-26): the strips twice as wide (16, was 8), so the track shows whole: each runs on over the
    # shaft's block to its outer edge (x -8 and 72), the mouth's walls starting from there.
    m.two_sided((-16, 200), (NICHE_X0, 200), shaft_w, mouth, "mouth.pillar_w")   # note #107: 24 wide
    m.two_sided((NICHE_X1, 200), (80, 200), shaft_e, mouth, "mouth.pillar_e")
    # Note #96 (2026-11-26): the two thin pillars either side of the shaft, seen from the bottom: the track metal.
    for ln in m.linedefs:
        if ln["user_gid"] in ("mouth.pillar_w", "mouth.pillar_e"):
            m.sidedefs[ln["sideback"]].fields.update(texturetop=TRACK, texturebottom=TRACK)
    # Note #10: a call switch at the bottom of the shaft, for completeness (in play you always arrive
    # from above): in a small niche in the mouth's west wall, beside the shaft, like the one up top.
    # The wall runs (0, 200) to (-64, 240), y = 200 - 5x/8: the niche's mouth (-16, 210)-(-48, 230) is on
    # it exactly, and (-5, -8) is exactly square to it, so every corner is a whole unit. Floor_MoveToValue
    # (37: tag, speed, height, 1 = negative) sends the platform (and the top niche's floor) to the
    # bottom, -256, once; already there, it does nothing.
    # Note #44: SWITCH_WINDOW (32) wide, about the same middle (it was 37.7 wide: (-16, 210) to (-48, 230)).
    # Note #99: the wall now runs from (-8, 200), y = 200 - 5(x + 8)/7: the window's ends on it, 32 apart about
    # x -32, and (-5, -7) square to it.
    # Note #107: from (-16, 200) now, y = 200 - 5(x + 16)/6, the window about x -36, (-5, -6) square to it.
    lower_switch_niche(m, mouth, (-16, 200), MOUTH_W, ((-23.71, 206.43), (-48.29, 226.91)), (-5, -6))
    m.wall(MOUTH_E, (80, 200), mouth, "mouth.wall_e")
    # Note #68: the landing's stone starts under the mouth (its floor is the stone's) and goes on out into
    # the hall (west_water builds its edges).
    m.sectors[mouth.index].fields.update(heightfloor=-DROP + LANDING_UP, texturefloor=LANDING_FLAT)
    stone = m.sector("landing", floor=-DROP + LANDING_UP, ceiling=-64, light=HALL_LIGHT, floor_tex=LANDING_FLAT)
    fog(m, stone)
    LANDING["sector"] = stone
    m.two_sided(MOUTH_W, MOUTH_E, mouth, stone, "mouth.edge")

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
    west_water(m, room, wb, q)
    MOULD_JOINTS.clear()
    FRAMES.clear()
    great_door(m, room, apse[0], apse[1], before=nw, after=ne)
    drains = hall_walls(m, room, [
        (MOUTH_W, [(q, room, "room.wall_s"), (sw, room, "gutter_w.edge_s")]),
        (sw, [(pt, room, "gutter_w.edge_w" if k == 0 else f"gutter_w.edge_w{k + 1}")
              for k, pt in enumerate(list(CLIFF_EDGE) + [wb])] + [(nw, room, "room.wall_w2")]),
        (nw, [(apse[0], room, "room.wall_n")]),
        (apse[1], [(ne, room, "room.wall_n3")]),
        (ne, east[0]),
        (se, east[1] + [(MOUTH_E, room, "room.wall_s2")]),
    ], mould={"room.wall_n": dict(skip_start=32, after=apse[1], line=(nw, apse[0])),   # note #119: the north side
              "room.wall_n3": dict(before=apse[0], skip_end=72, line=(apse[1], ne))},
                       edges={"gutter_w.edge_s", "gutter_w.edge_w"} | {f"gutter_w.edge_w{k + 1}" for k in range(1, len(CLIFF_EDGE) + 1)})
    for k, (type_, x, y) in enumerate(CLIFF_TREES):                     # note #106
        m.thing(type_, x, y, f"cliff.tree_{k + 1}", angle=(k * 131) % 360)   # note #86: the cliff's run, dirt in front
    mould_joint(m, "room.wall_n", "room.wall_n2")
    mould_joint(m, "room.wall_n2b", "room.wall_n3")
    cistern(m, *drains["cistern"])  # needs the passage (great_door) and the drains
    # Note #123 (2026-11-26): the cistern's walls are massive stone sewer works (STARG3), not the passages' mossy
    # rock: every wall surface seen from the cistern itself, its outcrops, their torch hollows and its outflow
    # channel that was the mossy rock. Floors and ceilings keep theirs.
    # Note #133: the stairs down and the shotgunner room too (every sector named cistern...).
    sewer = {i for i, sct in enumerate(m.sectors) if sct["user_gid"].startswith("cistern")}
    for sd in m.sidedefs:
        if sd["sector"] in sewer:
            for key in ("texturetop", "texturemiddle", "texturebottom"):
                if sd.get(key) == PASSAGE_TEXTURE:
                    sd[key] = CISTERN_WALL
    # Notes #54, #57 (2026-11-23): the track metal as a strip along the foot of the closet's walls, as it
    # shows round the car (textures.txt: CACOBASE, the wall with the strip in its bottom rows; turned on
    # its side at first, then as it is). Every plain wall of the
    # closet and its coffer gets it, stood on the floor (dontpegbottom); the secret panel's face too, so
    # the strip doesn't give it away. The light channels and the start door's recess interrupt it.
    # Note #69 (2026-11-23): the hall's tall walls in huge, slightly ruined stone: STONE3 (grey blocks, cracked
    # and mossy) drawn at twice its size (UDMF scale 0.5), so a wall 256 high is two courses of great
    # blocks. Every surface of the hall, its gutters, the landing and the mouth that was the default grey.
    hall = {i for i, sct in enumerate(m.sectors)
            if sct["user_gid"].startswith(("room", "mouth", "landing", "gutter_"))}
    for sd in m.sidedefs:
        if sd["sector"] in hall:
            for key, part in (("texturetop", "top"), ("texturemiddle", "mid"), ("texturebottom", "bottom")):
                if sd.get(key) == CLOSET_WALL:
                    sd.fields.update({key: HALL_WALL, f"scalex_{part}": HALL_WALL_SCALE, f"scaley_{part}": HALL_WALL_SCALE,
                                      f"offsety_{part}": HALL_WALL_SHIFT})
    # Note #58 (2026-11-23): the hall's floor is dirt (HALL_FLOOR; it was the default hexagon tiles), the
    # landing in front of it too, and the dirt carries on down the shallow banks to the water: the bank
    # faces are the lower part of the water's side of each line between the floor and a gutter.
    ground = {i for i, sct in enumerate(m.sectors) if sct["user_gid"] == "room"}
    for i in ground:
        m.sectors[i]["texturefloor"] = HALL_FLOOR
    wet = {i for i, sct in enumerate(m.sectors) if sct["user_gid"].startswith(("gutter_w", "gutter_e"))}
    for ld in m.linedefs:
        if "sideback" not in ld.fields:
            continue
        f, b = m.sidedefs[ld["sidefront"]], m.sidedefs[ld["sideback"]]
        for dry, water in ((f, b), (b, f)):
            if dry["sector"] in ground and water["sector"] in wet:
                water["texturebottom"] = HALL_FLOOR
    inside = {i for i, sct in enumerate(m.sectors) if sct["user_gid"] in ("closet", "closet.coffer")}
    secret = {i for i, sct in enumerate(m.sectors) if sct.get("id") == SECRET_TAG}
    for ld in m.linedefs:
        front = m.sidedefs[ld["sidefront"]]
        if "sideback" not in ld.fields:
            if front["sector"] in inside and front.get("texturemiddle") == CLOSET_WALL:
                front["texturemiddle"] = BASE_TEXTURE
                ld["dontpegbottom"] = True
            continue
        back = m.sidedefs[ld["sideback"]]
        for near, far in ((front, back), (back, front)):
            if near["sector"] in inside and far["sector"] in secret and near.get("texturetop") == CLOSET_WALL:
                near["texturetop"] = BASE_TEXTURE
    # Note #64 (2026-11-23): no cement in the start: every other wall surface of the closet, the car and the
    # shaft's blocks that was the default grey is the green wall of pipes and conduits (CLOSET_SKIN), as is
    # the wall in CACOBASE above its strip (textures.txt).
    start = {i for i, sct in enumerate(m.sectors) if sct["user_gid"].startswith(("closet", "car", "shaft_"))}
    for sd in m.sidedefs:
        if sd["sector"] in start:
            for key in ("texturetop", "texturemiddle", "texturebottom"):
                if sd.get(key) == CLOSET_WALL:
                    sd[key] = CLOSET_SKIN
    # Note #114 (2026-11-24): the elevator's ride is given its sound by zscript.zs (it was silent); the engine's own
    # floor sound is off for its sectors, so the two can't play together.
    for sct in m.sectors:
        if sct.get("id") == CAR_TAG:
            sct["soundsequence"] = "Silence"
    for sct in m.sectors:                                # note #18: which way each water runs (zscript.zs)
        gid = sct["user_gid"]
        if gid in ("gutter_w", "drain"):
            sct["id"] = FLOW_WEST_TAG
        elif gid in ("gutter_e", "gutter_e.crown", "drain_2") or gid.startswith("gutter_e.violet_"):   # (the crown's strips: note #123)
            sct["id"] = FLOW_EAST_TAG
        elif gid == "cistern.out":                       # note #23: turns with the cistern's water at the switch
            sct["id"] = CISTERN_TAG
    for k, (x, y, type_) in enumerate(VIOLET_TRAIL):
        t = m.thing(type_, x, y, f"violet_trail_{k + 1}", angle=(k * 97) % 360)
        m.things[t].fields.update(renderstyle="stencil", fillcolor=TRAIL_COLOUR)
    m.thing(DEAD_MARINE, DEAD_MARINE_AT[0], DEAD_MARINE_AT[1], "dead_marine", angle=DEAD_MARINE_AT[2])

    # The monoliths, in two rows (west row facing east, east row facing west).
    for r, x0 in enumerate(MONOLITH_ROWS):
        for i, y0 in enumerate(MONOLITH_YS):
            # Note #120 (2026-11-24): the eye (MARBFAC2) only on the switch obelisk; the others carry the star
            # made from it (textures.txt CACOSTAR: no pupil, the gaps between its lobes drawn in to the middle).
            face = FACE if (i, "we"[r]) == SWITCH_OBELISK else FACE_STAR
            monolith(m, room, f"monolith_{'we'[r]}{i + 1}", x0, y0, facing="e" if r == 0 else "w", face=face,
                     pair=i, switch=(i, "we"[r]) == SWITCH_OBELISK)

    # Chat (2026-11-25): the techbase's floor and ceiling (the theme's, themes/techbase): every techbase
    # sector (the start closet, the car and shaft blocks, the tech door and tech room, their light
    # channels) that had the default floor or ceiling takes TECH_FLOOR / TECH_CEILING.
    for sct in m.sectors:
        if sct["user_gid"].startswith(TECHBASE_GIDS):
            if sct.get("texturefloor") == gen.FLOOR:
                sct["texturefloor"] = TECH_FLOOR
            if sct.get("textureceiling") == gen.CEILING:
                sct["textureceiling"] = TECH_CEILING

    # Last, once every sector exists (the obelisks are built just above):
    # Note #59 (2026-11-23): the hall is open to the sky (a dark, starry one: map.toml), its walls HALL_SKY
    # high. Everything in the hall that shared its ceiling (-64: the floor, the gutters, the obelisks'
    # bases and altars, the bridge) goes up with it and takes the sky; so do the obelisks' sleeves and
    # slabs, whose own ceiling was the slot above them (SLEEVE_TOP): a sleeve is now a free-standing
    # pillar, open above. The landing (mouth) keeps its ceiling: you come out from under it.
    for sct in m.sectors:
        gid, top = sct["user_gid"], sct["heightceiling"]
        in_hall = top == -64 and not gid.startswith("mouth")
        pillar = top == SLEEVE_TOP and gid.startswith("monolith_")
        if in_hall or pillar:
            sct.fields.update(heightceiling=HALL_SKY, textureceiling=SKY_FLAT)
            for k in ("lightceiling", "lightceilingabsolute"):
                sct.fields.pop(k, None)
            if False and gid.endswith(".lip"):               # (note #101's way, given up in note #107: see the slit)
                # Note #101 (2026-11-24): the strip of the sleeve's back above the slit is the upper part of the
                # line between the slit and this lip. With both ceilings sky (the slit's was, for when it has
                # risen) the engine draws no wall between two skies: a see-through slice up the obelisk's
                # back. So until the sleeve sinks the slit's ceiling is stone, and the lip's sky is at the
                # sleeve's top: the strip is exactly as tall as the sleeve. zscript.zs turns the slit's
                # ceiling to sky and lifts the lip's as the sleeve starts down (LIP_TAG).
                sct.fields.update(heightceiling=SLEEVE_TOP, id=LIP_TAG)


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
    # Note #25: the rivulet, a violet sector of its own between the obelisk's base and the gutter.
    # Note #27: flush with the walkway (a film of liquid across the floor, not a channel 8 deep): the
    # channel's marble banks were drawn by this sector, so its desaturation (which makes the green liquid
    # take the violet) turned them grey. Where it reaches the gutter it falls the 8 into it.
    rivulet = m.sector("gutter_e.violet_4.rivulet", floor=-DROP, ceiling=-64, light=HALL_LIGHT, floor_tex=GUTTER_FLAT)
    fog(m, rivulet)
    m.sectors[rivulet.index].fields.update(desaturation=1.0, color_floor=VIOLET)
    RIVULET["sector"] = rivulet
    RIVULET["piece0"] = pieces[0]
    names = ["gutter_e" if k == 0 else f"gutter_e.violet_{k}" for k in range(len(pieces))]
    for k, s in enumerate(pieces):
        side = ((s0,) + GUTTER_E_WEST) if k == 0 else (west[k],) + GUTTER_E_WEST_EXTRA.get(k, ()) + (west[k + 1],)
        extra = GUTTER_E_WEST_EXTRA.get(k, ())
        if extra:
            _leak_side(m, room, s, rivulet, names[k], west[k], extra, west[k + 1])
        else:
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


def _leak_side(m: MapBuilder, room, piece, rivulet, name: str, south, extra, north) -> None:
    """Notes #25, #30: a gutter piece's west side where the switch obelisk's rivulet runs into it (`extra`:
    the mouth's south end, the rivulet's two corners at the obelisk's base, the mouth's north end), from
    `south` to `north`: the rivulet's banks, its mouth, and the violet spreading from the mouth in half
    rings (VIOLET_RINGS, outermost first), each from a point on the edge south of the mouth round to one
    north of it."""
    import math
    m0, m1 = extra[0], extra[-1]
    cx, cy = (m0[0] + m1[0]) / 2, (m0[1] + m1[1]) / 2
    rings = []
    for n, (radius, desat, colour) in enumerate(VIOLET_RINGS):
        ring = m.sector(f"{name}.ring_{n + 1}", floor=-DROP - 8, ceiling=-64, light=HALL_LIGHT, floor_tex=GUTTER_FLAT)
        fog(m, ring)
        # Walkable, but the movement check reads a ring's short edges as gaps too narrow to pass and
        # reports it unreachable: marked as scenery to keep that out of the warnings.
        m.sectors[ring.index].fields.update(desaturation=desat, color_floor=colour, user_scenery=True)
        rings.append((ring, radius))
    r2 = lambda q: (round(q[0], 2), round(q[1], 2))
    # The edge, south to north: who owns each stretch (the gutter's side of it), then the mouth.
    below = [south] + [r2(on_line(south, m0, cy - radius)) for _, radius in rings] + [m0]
    above = [m1] + [r2(on_line(m1, north, cy + radius)) for _, radius in reversed(rings)] + [north]
    owners_below = [piece] + [ring for ring, _ in rings]
    owners_above = [ring for ring, _ in reversed(rings)] + [piece]
    for j, (a, b) in enumerate(zip(below, below[1:])):
        m.two_sided(a, b, owners_below[j], room, f"{name}.edge_w_s{j + 1}", texture=STONE)
    for j, (a, b) in enumerate(zip(above, above[1:])):
        m.two_sided(a, b, owners_above[j], room, f"{name}.edge_w_n{j + 1}", texture=STONE)
    for j, (a, b) in enumerate(zip(extra, extra[1:])):         # the rivulet's banks (its end is the base's edge)
        if (a, b) not in GUTTER_E_SHARED:
            m.two_sided(a, b, rivulet, room, f"{name}.rivulet.bank_{j + 1}", texture=STONE)
    inner = rings[-1][0]
    mouth = m.two_sided(m0, m1, inner, rivulet, f"{name}.rivulet_mouth", texture=STONE)
    m.sidedefs[m.linedefs[mouth]["sidefront"]].fields.update(
        texturebottom=VIOLET_FALL, useowncolors_bottom=True, uppercolor_bottom=VIOLET, lowercolor_bottom=VIOLET)
    # The half rings: from the edge south of the mouth, out east and round to the edge north of it.
    outer = piece
    for n, (ring, radius) in enumerate(rings):
        arc = [below[n + 1]] + [r2((cx + radius * math.cos(t), cy + radius * math.sin(t)))
                                for t in (math.pi * (i / VIOLET_RING_STEPS - 0.5) for i in range(1, VIOLET_RING_STEPS))]
        arc.append(above[len(rings) - n])
        for i, (a, b) in enumerate(zip(arc, arc[1:])):
            m.two_sided(a, b, outer, ring, f"{name}.ring_{n + 1}.arc_{i + 1}", texture=STONE)
        outer = ring


def rough_niche(gid: str, wide: float = 24, deep: float = NICHE_DEEP, undercut: bool = True):
    """Note #79 (2026-11-24): a torch niche hacked out of the rock, not a square box: its mouth and depth a
    little different each time, its back a few diagonals. Returns (mouth width, depth, back): back is the
    points between the mouth's two ends as (along the mouth from its first end, into the rock). The same
    for a gid on every build (drawn from the gid). undercut: the hollow may be a little wider inside
    than its mouth (not where rock is thin, as in the cistern's outcrops)."""
    import hashlib
    import random
    r = random.Random(int(hashlib.md5(gid.encode()).hexdigest()[:8], 16))
    w = wide + r.choice((-2, 0, 2, 4, 6))
    dp = deep + r.choice((-2, 0, 3, 6))
    lo, hi = (-0.10, 1.10) if undercut else (0.03, 0.97)
    back = [(w * r.uniform(lo, 0.12), dp * r.uniform(0.42, 0.66)),
            (w * r.uniform(0.24, 0.42), dp * r.uniform(0.88, 1.0)),
            (w * r.uniform(0.58, 0.78), dp * r.uniform(0.82, 1.0)),
            (w * r.uniform(0.90, hi), dp * r.uniform(0.38, 0.62))]
    return w, dp, back


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
    # Note #86 (2026-11-25): no west gutter any more: the hall's dirt runs to the west wall and the cliff's
    # railing, and the landing's west side meets the dirt. Only the stretch east of the landing is left,
    # coming out from under it into the east stream.
    # Note #28 (2026-11-23): the rule is "east of the landing flows east": the stretch of the channel east
    # of it is a sector of its own (it was part of the west gutter, and flowed west).
    stub = m.sector("gutter_w.east_of_bridge", **water)
    fog(m, stub)
    m.sectors[stub.index]["id"] = FLOW_EAST_TAG
    east = RIVULET["piece0"]
    m.two_sided((b1, s1), (129, s1), stub, room, "gutter_w.crossing_n2", texture=STONE)
    m.two_sided((129, s1), (138, s0), stub, east, "gutter_w.join", texture=STONE)
    m.two_sided((138, s0), (b1, s0), stub, room, "gutter_w.crossing_s2", texture=STONE)
    # Note #68 (2026-11-23): no bridge. The landing is one big sheet of stone (LANDING: built in build(),
    # which joins it to the mouth) from the foot of the elevator out over where the channel crossed, a
    # step above the dirt (LANDING_UP) and LANDING_LIP past the channel's north bank; the water comes out
    # from under it on either side (the west gutter's channel, and the stretch east of it), and the
    # player steps down off its lip into the row of obelisks.
    stone = LANDING["sector"]
    n1 = s1 + LANDING_LIP
    _edges(m, stone, [
        (MOUTH_W, MOUTH_E, "skip", ""),                       # onto the mouth (build())
        (MOUTH_E, (b1, s0), room, "landing.edge_se"),
        ((b1, s0), (b1, s1), stub, "landing.edge_e"),
        ((b1, s1), (b1, n1), room, "landing.edge_ne"),
        ((b1, n1), (b0, n1), room, "landing.edge_n"),
        ((b0, n1), (b0, s1), room, "landing.edge_nw"),
        ((b0, s1), (b0, s0), room, "landing.edge_w"),
        ((b0, s0), MOUTH_W, room, "landing.edge_sw"),
    ])
    for ld in m.linedefs:
        if ld["user_gid"].startswith("landing.edge_"):
            for side in ("sidefront", "sideback"):
                m.sidedefs[ld[side]]["texturebottom"] = HALL_FLOOR   # note #88: the dirt bank down to the water (was the stone's edge)


def passage(m: MapBuilder, vest, P, floor0) -> None:
    """Note #63: the mossy passage from the vestibule (PASSAGE: cross-sections in the doorway's frame,
    placed by P): one sector per piece between two cross-sections, rising PASSAGE_STEP on; one-sided
    walls along its sides, with torch niches (PASSAGE_TORCHES); a wall at its end."""
    PASSAGE = _widened(globals()["PASSAGE"])
    secs = []
    for k in range(len(PASSAGE) - 1):
        f = floor0 + 8 * max(0, min(k, PASSAGE_RISE_END) - PASSAGE_STEP + 1) - 16 * max(0, k - PASSAGE_RISE_END)
        s = m.sector(f"passage_{k + 1}", floor=f, ceiling=f + PASSAGE_HIGH + 16 * max(0, k - 7), light=PASSAGE_LIGHT,
                     floor_tex=MAIN_FLOOR, ceiling_tex=MAIN_WALL)
        if k < PASSAGE_FOG_PIECES:
            m.sectors[s.index].fields.update(
                fadecolor=HALL_FOG, fogdensity=round(HALL_FOG_DENSITY * (1 - (k + 1) / (PASSAGE_FOG_PIECES + 1))))
        secs.append(s)
    # The opening from the vestibule, and the steps between pieces (front: the piece before, on the right
    # of a line from the left wall to the right).
    (l0, r0) = PASSAGE[0]
    # Note #127: a wooden frame in the opening; the first piece starts FRAME_DEEP further in.
    import math
    (l1, r1) = PASSAGE[1]
    on = math.hypot(r0[0] - l0[0], r0[1] - l0[1])
    nx, ny = -(r0[1] - l0[1]) / on, (r0[0] - l0[0]) / on
    if nx * ((l1[0] + r1[0]) / 2 - (l0[0] + r0[0]) / 2) + ny * ((l1[1] + r1[1]) / 2 - (l0[1] + r0[1]) / 2) < 0:
        nx, ny = -nx, -ny                                  # towards the passage's next cross-section
    l0b, r0b = (l0[0] + nx * FRAME_DEEP, l0[1] + ny * FRAME_DEEP), (r0[0] + nx * FRAME_DEEP, r0[1] + ny * FRAME_DEEP)
    opening_frame = timber_frame(m, P(*l0), P(*r0), P(*l0b), P(*r0b), vest, secs[0], "passage.frame")
    PASSAGE = [(l0b, r0b)] + list(PASSAGE[1:])
    for k in range(1, len(PASSAGE) - 1):
        l, r = PASSAGE[k]
        step = m.two_sided(P(*l), P(*r), secs[k - 1], secs[k], f"passage_{k + 1}.step", texture=MAIN_WALL)
        if k in PASSAGE_QUIET:
            m.linedefs[step]["blocksound"] = True
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
            rough = None
            if (k, side) == SIDE_EXIT:                         # the side passage comes out here: an opening, SIDE_MOUTH wide
                dx, dy = b[0] - a[0], b[1] - a[1]
                n = math.hypot(dx, dy)
                # Note #137: monsters struggled through it at 88 (72 between the posts): as wide as the wall allows,
                # up to SIDE_EXIT_MOUTH.
                mouth = min(SIDE_EXIT_MOUTH, n - 16)
                print(f"    side passage: its way out is {mouth:.0f} wide ({mouth - 2 * FRAME_POST:.0f} between the posts) in a wall {n:.0f} long")
                o0 = (a[0] + dx / n * (n / 2 - mouth / 2), a[1] + dy / n * (n / 2 - mouth / 2))
                o1 = (a[0] + dx / n * (n / 2 + mouth / 2), a[1] + dy / n * (n / 2 + mouth / 2))
                m.wall(P(*a), P(*o0), s, f"{gid}_a", texture=MAIN_WALL)
                # Note #128: its wooden frame, out through the wall (the rock is on the left of a -> b).
                fx, fy = -dy / n * FRAME_DEEP, dx / n * FRAME_DEEP
                o0b, o1b = (o0[0] + fx, o0[1] + fy), (o1[0] + fx, o1[1] + fy)
                out_frame = timber_frame(m, P(*o0), P(*o1), P(*o0b), P(*o1b), s, SIDE["sectors"][-1], "side_passage.frame_out",
                                         rock=MAIN_WALL)
                m.wall(P(*o1), P(*b), s, f"{gid}_b", texture=MAIN_WALL)
                SIDE["exit"] = (P(*o0b), P(*o1b))
                continue
            if (k, side) == PASSAGE_SECRET:
                passage_secret(m, s, a, b, P, gid)
                continue
            if (k, side) in torches:
                # A torch niche: 24 wide, NICHE_DEEP deep, from the floor, the torch wholly inside.
                kind, wide, deep, sill, high, thing_in, thing = "niche", 24, NICHE_DEEP, 0, NICHE_HIGH, NICHE_TORCH_IN, TORCH
                wide, deep, rough = rough_niche(gid)             # note #79: a rough hollow, each a little different
            elif (k, side) in PASSAGE_CARVINGS:
                kind, wide, deep, sill, high, thing_in, thing = "carving", 128, CARVING_DEEP, CARVING_SILL, 128, 12, None
            elif (k, side) in shelves:
                # Note #76: wider, deeper and lower (was 32 wide, 16 deep, 40 high), lit as the passage.
                kind, wide, deep, sill, high, thing_in, thing = "shelf", 48, 24, 32, 24, 10, shelves[(k, side)]
            else:
                m.wall(P(*a), P(*b), s, gid, texture=MAIN_WALL)
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
                             floor_tex=MAIN_WALL, ceiling_tex=MAIN_WALL)
            m.sectors[niche.index]["user_scenery"] = True
            inside = MAIN_WALL
            if kind == "carving":
                inside = CARVING_STONE
                m.sectors[niche.index].fields.update(lightlevel=CARVING_LIGHT, texturefloor="FLOOR7_2",
                                                     textureceiling="FLOOR7_2")
            if kind == "shelf":                              # note #76: the passage's own light (and fog)
                piece = m.sectors[s.index].fields
                m.sectors[niche.index].fields.update(
                    lightlevel=piece["lightlevel"],
                    **{k2: piece[k2] for k2 in ("fadecolor", "fogdensity") if k2 in piece})
                # Note #6 (2026-11-23): a wooden box set into the stone: wood on its back, sides, shelf and top.
                inside = "WOOD1"
                m.sectors[niche.index].fields.update(texturefloor="FLAT5_2", textureceiling="FLAT5_2")
            if kind == "shelf":
                # Note #8 (2026-11-23): flush with the wall it looked "painted on stone". A wooden frame
                # gives it depth: a recess SHELF_FRAME[0] wider all round than the box and SHELF_FRAME[1]
                # deep, wood on its sides, sill and top; the box opens in its back, which shows as a
                # wooden border round the box. The box itself is a little darker than the frame.
                fb, fdp = SHELF_FRAME
                nx, ny = -ey, ex
                g0 = (p0[0] - ex * fb, p0[1] - ey * fb)
                g1 = (p1[0] + ex * fb, p1[1] + ey * fb)
                h0, h1 = (g0[0] + nx * fdp, g0[1] + ny * fdp), (g1[0] + nx * fdp, g1[1] + ny * fdp)
                shift = lambda pt: (pt[0] + nx * fdp, pt[1] + ny * fdp)
                p0, p1, q0, q1 = shift(p0), shift(p1), shift(q0), shift(q1)
                frame = m.sector(f"{gid}.shelf_frame", floor=f + sill - fb, ceiling=f + sill + high + fb,
                                 light=piece["lightlevel"], floor_tex="FLAT5_2", ceiling_tex="FLAT5_2")
                m.sectors[frame.index].fields.update(
                    user_scenery=True, **{k2: piece[k2] for k2 in ("fadecolor", "fogdensity") if k2 in piece})
                m.sectors[niche.index]["lightlevel"] = max(0, piece["lightlevel"] - 24)
                m.wall(P(*a), P(*g0), s, f"{gid}_a", texture=MAIN_WALL)
                m.two_sided(P(*g0), P(*g1), s, frame, f"{gid}.shelf_frame.mouth", texture=MAIN_WALL)
                m.wall(P(*g1), P(*b), s, f"{gid}_b", texture=MAIN_WALL)
                m.wall(P(*g0), P(*h0), frame, f"{gid}.shelf_frame.side_a", texture=inside)
                m.wall(P(*h0), P(*p0), frame, f"{gid}.shelf_frame.back_a", texture=inside)
                m.two_sided(P(*p0), P(*p1), frame, niche, f"{gid}.{kind}.mouth", texture=inside)
                m.wall(P(*p1), P(*h1), frame, f"{gid}.shelf_frame.back_b", texture=inside)
                m.wall(P(*h1), P(*g1), frame, f"{gid}.shelf_frame.side_b", texture=inside)
            else:
                m.wall(P(*a), P(*p0), s, f"{gid}_a", texture=MAIN_WALL)
                m.two_sided(P(*p0), P(*p1), s, niche, f"{gid}.{kind}.mouth", texture=MAIN_WALL)
                m.wall(P(*p1), P(*b), s, f"{gid}_b", texture=MAIN_WALL)
            if rough:
                pts = [p0] + [(p0[0] + ex * t2 + ox / deep * s2, p0[1] + ey * t2 + oy / deep * s2) for t2, s2 in rough] + [p1]
                for n2, (c0, c1) in enumerate(zip(pts, pts[1:])):
                    m.wall(P(*c0), P(*c1), niche, f"{gid}.{kind}.rock_{n2 + 1}", texture=inside)
            else:
                m.wall(P(*p0), P(*q0), niche, f"{gid}.{kind}.side_a", texture=inside)
            if kind == "carving":
                fl = (wide - CARVING_WIDE) / 2               # the plain stone either side of the face
                c0 = (q0[0] + ex * fl, q0[1] + ey * fl)
                c1 = (q1[0] - ex * fl, q1[1] - ey * fl)
                left = m.wall(P(*q0), P(*c0), niche, f"{gid}.{kind}.back_a", texture=inside)
                m.wall(P(*c0), P(*c1), niche, f"{gid}.{kind}.back", texture=CARVING_TEXTURE)
                right = m.wall(P(*c1), P(*q1), niche, f"{gid}.{kind}.back_b", texture=inside)
                m.sidedefs[m.linedefs[left]["sidefront"]]["offsetx"] = round(-fl) % 256
                m.sidedefs[m.linedefs[right]["sidefront"]]["offsetx"] = CARVING_WIDE
            elif not rough:
                m.wall(P(*q0), P(*q1), niche, f"{gid}.{kind}.back", texture=inside)
            if not rough:
                m.wall(P(*q1), P(*p1), niche, f"{gid}.{kind}.side_b", texture=inside)
            k_in = thing_in / deep
            cx, cy = (p0[0] + p1[0]) / 2 + ox * k_in, (p0[1] + p1[1]) / 2 + oy * k_in
            if kind == "carving":                            # two stimpacks on the sill, either side of the middle
                for j, along in enumerate((-22, 18)):
                    m.thing(STIMPACK, *P(cx + ex * along, cy + ey * along), f"{gid}.stimpack_{j + 1}", angle=90)
                continue
            ti = m.thing(thing, *P(cx, cy), f"{gid}.{'torch' if kind == 'niche' else 'item'}")
            if kind == "niche" and (k, side) in PASSAGE_TORCHES_UNLIT:
                m.things[ti].fields["id"] = DEAD_TORCH_TID
                m.sectors[niche.index]["lightlevel"] = m.sectors[s.index]["lightlevel"]


# Notes #127, #128 (2026-11-24): a wooden frame in each opening between a room and a passage (the vestibule's two,
# and the side passage's way out into the main passage). Note #130: not a wood-lined doorway (wood to the
# ceiling, flush with the wall): the opening is cut through the rock (a throat FRAME_DEEP deep, rock all round,
# its top 8 under the lower of the two ceilings), and a timber frame stands in front of it, out from the
# wall into the room, bracing it: two posts (FRAME_POST square) and a beam across their tops (FRAME_BEAM
# high), the rock wall showing above the beam. Posts and beam are 3D floors (their control sectors stand
# outside the map, FRAME_CONTROLS on), so the beam is a real beam with air over it.
FRAME_DEEP, FRAME_WOOD, FRAME_BOARDS = 12, "WOOD1", "FLAT5_2"
FRAME_POST, FRAME_BEAM = 8, 16
FRAME_TAG = 800                 # each frame takes two: its posts, its beam
FRAME_CONTROLS = (912, -96)     # the first control sector's corner; the rest follow, 48 apart
FRAMES: list = []


def timber_frame(m: MapBuilder, a, b, a2, b2, outer, inner, gid: str, rock: str = "A-MOSRK2"):
    """The opening a - b in a wall of `outer`, cut through to a2 - b2 (FRAME_DEEP further in, where `inner`
    begins), with its timber frame standing in the room in front of it. Builds everything: the throat, its
    line with `inner`, the posts and the beam and their lines with the room. The caller builds no line
    from a to b."""
    import math
    r2 = lambda pt: (round(pt[0], 2), round(pt[1], 2))
    src, dst = m.sectors[outer.index].fields, m.sectors[inner.index].fields
    floor, top = src["heightfloor"], min(src["heightceiling"], dst["heightceiling"]) - 8
    look = dict(light=src["lightlevel"], floor_tex=src["texturefloor"], ceiling_tex=src["textureceiling"])
    fogged = {k: src[k] for k in ("fadecolor", "fogdensity") if k in src}
    throat = m.sector(gid, floor=floor, ceiling=top, **look)
    m.sectors[throat.index].fields.update(fogged)
    made = _edges(m, throat, [(a, b, "skip", ""), (b, b2, None, f"{gid}.side_b"),
                              (b2, a2, inner, f"{gid}.inner"), (a2, a, None, f"{gid}.side_a")])
    # The timber: along the wall u, out into the room n.
    L = math.dist(a, b)
    ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
    D = math.dist(a, a2)
    nx, ny = (a[0] - a2[0]) / D, (a[1] - a2[1]) / D
    at = lambda along, out: r2((a[0] + ux * along + nx * out, a[1] + uy * along + ny * out))
    w, o = FRAME_POST, FRAME_POST
    a_in, b_in, qa, qa_in, qb_in, qb = at(w, 0), at(L - w, 0), at(0, o), at(w, o), at(L - w, o), at(L, o)
    k = len(FRAMES)
    FRAMES.append(gid)
    post_tag, beam_tag = FRAME_TAG + 2 * k, FRAME_TAG + 2 * k + 1
    parts = {}
    for name, tag in (("post_a", post_tag), ("beam", beam_tag), ("post_b", post_tag)):
        s = m.sector(f"{gid}.{name}", floor=floor, ceiling=src["heightceiling"], **look)
        m.sectors[s.index].fields.update(fogged, id=tag, user_scenery=name != "beam")
        parts[name] = s
    made += _edges(m, parts["post_a"], [(a, a_in, throat, f"{gid}.post_a.back"), (a_in, qa_in, parts["beam"], f"{gid}.post_a.in"),
                                        (qa_in, qa, outer, f"{gid}.post_a.front"), (qa, a, outer, f"{gid}.post_a.end")])
    made += _edges(m, parts["beam"], [(a_in, b_in, throat, f"{gid}.beam.back"), (b_in, qb_in, parts["post_b"], f"{gid}.beam.in"),
                                      (qb_in, qa_in, outer, f"{gid}.beam.front"), (qa_in, a_in, "skip", "")])
    made += _edges(m, parts["post_b"], [(b_in, b, throat, f"{gid}.post_b.back"), (b, qb, outer, f"{gid}.post_b.end"),
                                        (qb, qb_in, outer, f"{gid}.post_b.front"), (qb_in, b_in, "skip", "")])
    for ln in made:                                        # every face of the cut is the room's rock
        ld = m.linedefs[ln]
        if "sideback" in ld.fields:
            for sd in ("sidefront", "sideback"):
                m.sidedefs[ld[sd]].fields.update(texturetop=rock, texturebottom=rock)
        else:
            m.sidedefs[ld["sidefront"]]["texturemiddle"] = rock
    # The 3D floors: the posts from the floor to the beam's top, the beam its own height under that.
    for n, (name, tag, lo) in enumerate((("posts", post_tag, floor), ("beam", beam_tag, top - FRAME_BEAM))):
        cx, cy = FRAME_CONTROLS[0] + 48 * (2 * k + n), FRAME_CONTROLS[1]
        control = m.room(f"{gid}.{name}_control", cx, cy, 32, 32, floor=lo, ceiling=top,
                         floor_tex=FRAME_BOARDS, ceiling_tex=FRAME_BOARDS, light=src["lightlevel"])
        m.sectors[control.index]["user_scenery"] = True
        cl = next(i for i, l in enumerate(m.linedefs) if l["user_gid"] == f"{gid}.{name}_control.wall_s")
        m.linedefs[cl].fields.update(special=160, arg0=tag, arg1=1, arg2=1, arg3=255)
        m.sidedefs[m.linedefs[cl]["sidefront"]]["texturemiddle"] = FRAME_WOOD
    return throat

def side_sectors(m: MapBuilder, floor: int) -> None:
    """The side passage's pieces (sectors only: the vestibule and the main passage, built first, each open
    onto one). One piece between each pair of cross-sections: the entrance, SIDE_PATH's points, the way
    out. It climbs 8 every third piece, and a last 8 into the main passage."""
    pieces = len(SIDE_PATH) + 1
    SIDE["sectors"] = []
    for i in range(pieces):
        f = floor + 8 * min(i // 3, 3)
        s = m.sector(f"side_passage_{i + 1}", floor=f, ceiling=f + SIDE_HIGH, light=SIDE_LIGHT_AT.get(i, SIDE_LIGHT),
                     floor_tex=SIDE_FLOOR, ceiling_tex=SIDE_WALL)
        m.sectors[s.index].fields.update(fadecolor=SIDE_FOG[0], fogdensity=SIDE_FOG[1])
        SIDE["sectors"].append(s)


def side_passage(m: MapBuilder) -> None:
    """The side passage's lines: its cross-sections between the two openings (SIDE["entrance"], SIDE["exit"],
    built by the vestibule and the main passage), its walls, and its torches (SIDE_TORCHES: lit, in rough
    niches)."""
    import math
    secs = SIDE["sectors"]
    mid = lambda pair: ((pair[0][0] + pair[1][0]) / 2, (pair[0][1] + pair[1][1]) / 2)
    line = [mid(SIDE["entrance"])] + list(SIDE_PATH) + [mid(SIDE["exit"])]

    def left_right(pair, d):
        """The opening's two ends as (left, right) of someone going along d."""
        c = mid(pair)
        first_is_left = d[0] * (pair[0][1] - c[1]) - d[1] * (pair[0][0] - c[0]) > 0
        return (pair[0], pair[1]) if first_is_left else (pair[1], pair[0])

    def unit(p, q):
        n = math.hypot(q[0] - p[0], q[1] - p[1])
        return ((q[0] - p[0]) / n, (q[1] - p[1]) / n)

    cuts = [left_right(SIDE["entrance"], unit(line[0], line[1]))]
    for i in range(1, len(line) - 1):
        d1, d2 = unit(line[i - 1], line[i]), unit(line[i], line[i + 1])
        bx, by = d1[0] + d2[0], d1[1] + d2[1]
        bn = math.hypot(bx, by)
        nx, ny = -by / bn, bx / bn                        # across the passage, to the left
        half = SIDE_WIDE / 2 / max(0.75, d1[0] * bx / bn + d1[1] * by / bn)     # a little wider at a bend
        c = line[i]
        cuts.append(((round(c[0] + nx * half, 2), round(c[1] + ny * half, 2)),
                     (round(c[0] - nx * half, 2), round(c[1] - ny * half, 2))))
    cuts.append(left_right(SIDE["exit"], unit(line[-2], line[-1])))
    for k, (i, facing) in enumerate(SIDE_IMPS):
        imp = m.thing(3001, round((line[i][0] + line[i + 1][0]) / 2), round((line[i][1] + line[i + 1][1]) / 2),
                      f"side_passage_{i + 1}.imp", angle=facing)
        m.things[imp]["ambush"] = True                     # note #137: plain deaf imps (shadow ones in note #136)
    torches = set(SIDE_TORCHES)
    for i, s in enumerate(secs):
        (la, ra), (lb, rb) = cuts[i], cuts[i + 1]
        if i:                                              # (the entrance's own line is the vestibule's)
            m.two_sided(la, ra, secs[i - 1], s, f"side_passage_{i + 1}.step", texture=SIDE_WALL)
        for k, (bi, bside, at, blen, bdeep, bhigh) in enumerate(SIDE_BOXES):
            if bi == i:
                a, b = (la, lb) if bside == "l" else (rb, ra)        # the wall, the passage on its right
                wall_box(m, s, a, b, at, blen, bdeep, bhigh, f"side_passage_{i + 1}.box_{k + 1}")
        if (i, "l") == SIDE_STORE:                         # note #92: the storage chamber's door
            storage_chamber(m, s, la, lb)
        else:
            _stair_wall(m, s, la, lb, f"side_passage_{i + 1}.wall_l", (i, "l") in torches,
                        lit=(i, "l") not in SIDE_TORCHES_OUT, texture=SIDE_WALL)
        if (i, "r") == SIDE_CARVING:                       # note #134: a carved alcove, five armour bonuses on its shelf
            _stair_carving(m, s, rb, ra, f"side_passage_{i + 1}.wall_r", items=SIDE_CARVING_ITEMS, texture=SIDE_WALL)
        else:
            _stair_wall(m, s, rb, ra, f"side_passage_{i + 1}.wall_r", (i, "r") in torches,
                        lit=(i, "r") not in SIDE_TORCHES_OUT, texture=SIDE_WALL)


def wall_box(m: MapBuilder, s, a, b, at, length, deep, high, gid: str) -> None:
    """Notes #101, #102: a wooden box (WOOD1 sides, FLAT5_2 top) standing against the wall a -> b (the sector s on
    its right), its middle `at` of the way along, 1 off the wall."""
    import math
    dx, dy = b[0] - a[0], b[1] - a[1]
    n = math.hypot(dx, dy)
    ex, ey = dx / n, dy / n
    rx, ry = ey, -ex                                           # right of a -> b: into the passage
    c = n * at
    pt = lambda t, o: (round(a[0] + ex * t + rx * o, 2), round(a[1] + ey * t + ry * o, 2))
    corners = [pt(c - length / 2, 1), pt(c + length / 2, 1), pt(c + length / 2, 1 + deep), pt(c - length / 2, 1 + deep)]
    piece = m.sectors[s.index].fields
    box = m.sector(gid, floor=piece["heightfloor"] + high, ceiling=piece["heightceiling"], light=piece["lightlevel"],
                   floor_tex=VESTIBULE_BOX_TOP, ceiling_tex=piece["textureceiling"])
    m.sectors[box.index].fields.update(user_scenery=True, **{k: piece[k] for k in ("fadecolor", "fogdensity") if k in piece})
    for ln in _edges(m, box, [(c0, c1, s, f"{gid}.side_{j + 1}") for j, (c0, c1) in enumerate(zip(corners, corners[1:] + corners[:1]))]):
        for sd in ("sidefront", "sideback"):
            m.sidedefs[m.linedefs[ln][sd]]["texturebottom"] = VESTIBULE_BOX_SIDE


def storage_chamber(m: MapBuilder, s, a, b) -> None:
    """Note #92: the big wooden door in the side passage's wall a -> b (the passage on its right), in its
    middle, like the cistern's (BIGDOOR6 on a wooden sill, DOORTRAK jambs) but a Door_Raise (12) anyone opens,
    monsters too; behind it the storage chamber (STORE_OUTLINE), its wooden boxes and its waiting monsters."""
    import math
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
    mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
    P = lambda u, d: (round(mx + u * ux - d * uy, 2), round(my + u * uy + d * ux, 2))
    half, thick = STORE_DOOR_WIDE / 2, STORE_DOOR_THICK
    piece = m.sectors[s.index].fields
    floor = piece["heightfloor"]
    gid = "store"
    door = m.sector(f"{gid}.door", floor=floor + WICKET_STEP, ceiling=floor + WICKET_STEP, light=SIDE_LIGHT,
                    floor_tex=WICKET_SILL, ceiling_tex=CISTERN_BOARDS)
    m.sectors[door.index]["id"] = STORE_TAG
    room = m.sector(gid, floor=floor, ceiling=floor + STORE_HIGH, light=STORE_LIGHT, floor_tex=SIDE_FLOOR,
                    ceiling_tex=SIDE_WALL)
    m.sectors[room.index].fields.update(fadecolor=SIDE_FOG[0], fogdensity=SIDE_FOG[1])
    m.wall(a, P(-half, 0), s, f"{gid}.wall_a", texture=SIDE_WALL)
    m.wall(P(half, 0), b, s, f"{gid}.wall_b", texture=SIDE_WALL)
    use = dict(special=12, arg0=STORE_TAG, arg1=16, arg2=150, playeruse=True, monsteruse=True, repeatspecial=True)
    # Note #117 (2026-11-26): from the room the door's face ran up the whole room's height (160) and BIGDOOR6 repeated
    # above it: a frame on the room's side now, STORE_FRAME deep, its top as high as the passage's ceiling, so the
    # door shows the same height from both sides, one count of the texture; DOORTRAK on its sides, the room's rock
    # above it.
    # Note #152 (2026-11-26): set back on the corridor's side too, as it is on the room's: a recess STORE_FRAME deep in
    # front of the door (DOORTRAK sides, the wooden step), the door behind it.
    ins = STORE_FRAME
    recess = m.sector(f"{gid}.door.recess", floor=floor + WICKET_STEP, ceiling=piece["heightceiling"], light=piece["lightlevel"],
                      floor_tex=WICKET_SILL, ceiling_tex=CISTERN_BOARDS)
    m.sectors[recess.index].fields.update(fadecolor=SIDE_FOG[0], fogdensity=SIDE_FOG[1])
    for name, p, q in (("side_a", P(-half, 0), P(-half, ins)), ("side_b", P(half, ins), P(half, 0))):
        m.wall(p, q, recess, f"{gid}.door.recess.{name}", texture="DOORTRAK")
    ln = m.two_sided(P(-half, 0), P(half, 0), s, recess, f"{gid}.door.recess.mouth", texture=SIDE_WALL)
    m.sidedefs[m.linedefs[ln]["sidefront"]]["texturebottom"] = CISTERN_WOOD
    fr = ins + thick + STORE_FRAME
    # Note #122: the frame's floor is the door's wooden step too (it was level with the room's floor), its riser wood.
    frame = m.sector(f"{gid}.door.frame", floor=floor + WICKET_STEP, ceiling=piece["heightceiling"], light=STORE_LIGHT,
                     floor_tex=WICKET_SILL, ceiling_tex=CISTERN_BOARDS)
    m.sectors[frame.index].fields.update(fadecolor=SIDE_FOG[0], fogdensity=SIDE_FOG[1])
    for name, p, q in (("side_a", P(-half, ins + thick), P(-half, fr)), ("side_b", P(half, fr), P(half, ins + thick))):
        m.wall(p, q, frame, f"{gid}.door.frame.{name}", texture="DOORTRAK")
    ln = m.two_sided(P(half, fr), P(-half, fr), room, frame, f"{gid}.door.frame.mouth", texture=SIDE_WALL)
    m.sidedefs[m.linedefs[ln]["sidefront"]]["texturebottom"] = CISTERN_WOOD
    for name, p, q, front in (("face", P(-half, ins), P(half, ins), recess), ("back", P(half, ins + thick), P(-half, ins + thick), frame)):
        ln = m.two_sided(p, q, front, door, f"{gid}.door.{name}", texture=CISTERN_DOOR_TEXTURE)
        m.linedefs[ln].fields.update(use)
        m.sidedefs[m.linedefs[ln]["sidefront"]]["offsetx"] = round((128 - STORE_DOOR_WIDE) / 2)
        m.sidedefs[m.linedefs[ln]["sidefront"]]["texturebottom"] = CISTERN_WOOD   # the sill's riser
    for name, p, q in (("jamb_a", P(-half, ins), P(-half, ins + thick)), ("jamb_b", P(half, ins + thick), P(half, ins))):
        ln = m.wall(p, q, door, f"{gid}.door.{name}", texture="DOORTRAK")
        m.linedefs[ln]["dontpegbottom"] = True
    ring = [P(half, fr)] + [P(u, d) for u, d in STORE_OUTLINE] + [P(-half, fr)]
    fronts = {frozenset((P(*pts[0]), P(*pts[1]))) for pts, _ in STORE_BACK}      # note #112: built by the boxes
    for ln in _edges(m, room, [(P(-half, fr), P(half, fr), "skip", "")]
                     + [(p, q, "skip" if frozenset((p, q)) in fronts else None, f"{gid}.wall_{i + 1}")
                        for i, (p, q) in enumerate(zip(ring, ring[1:]))]):
        m.sidedefs[m.linedefs[ln]["sidefront"]]["texturemiddle"] = SIDE_WALL
    # Note #112: the wall of boxes at the back: each box's front onto the room, a side it shares with the next
    # box built once (by the later one), the rest one-sided (the old back wall, and nothing behind).
    # Note #127: the chamber behind the shortcut box: its back edge the box's, its far edge onto the tunnel.
    sc_pts = STORE_BACK[STORE_SHORTCUT][0]
    sb0, sb1 = P(*sc_pts[2]), P(*sc_pts[3])                 # the box's back edge
    ua, ub = sc_pts[2][0], sc_pts[3][0]
    far0, far1 = P(ua, STORE_BACKWAY_D), P(ub, STORE_BACKWAY_D)
    # Note #139 (2026-11-26): glimpsed over the box from the storage room, the chamber is plainly somewhere else: the
    # base's (its walls METAL4, the techbase floor and ceiling, a grey switch), while the wall over the box, on the
    # storage room's side, stays the grotto's rock.
    chamber = m.sector(f"{gid}.backway", floor=floor, ceiling=floor + 96, light=96, floor_tex=TECH_FLOOR,
                       ceiling_tex=TECH_CEILING)
    # Note #149 (2026-11-26): the switch set into a niche in the side wall, like the elevator's: a window of the plate
    # (32 x 32, 24 above the floor), track metal round it, and in front of the switch a shutter whose ceiling
    # zscript.zs brings down once it's used (one use), the panel (CALL_SHUTTER_TEXTURE) riding down over it.
    wu, (wd0, wd1), z0 = sc_pts[2][0], STORE_SWITCH_WINDOW, floor + 24
    N0, N1 = P(wu, wd1), P(wu, wd0)                         # the niche's mouth, in the order the wall runs
    M0, M1 = P(wu - 6, wd1), P(wu - 6, wd0)                 # the panel's line
    B0, B1 = P(wu - 8, wd1), P(wu - 8, wd0)                 # the switch
    niche = m.sector(f"{gid}.backway.niche", floor=z0, ceiling=z0 + 32, light=112, floor_tex=TRACK, ceiling_tex=TRACK)
    shutter = m.sector(f"{gid}.backway.shutter", floor=z0, ceiling=z0 + 32, light=112, floor_tex=TRACK, ceiling_tex=TRACK)
    m.sectors[niche.index]["user_scenery"] = True
    m.sectors[shutter.index].fields.update(user_scenery=True, id=STORE_SWITCH_SHUTTER_TAG)
    for ln in _edges(m, chamber, [(sb0, sb1, "skip", ""), (sb1, far1, None, f"{gid}.backway.side_b"),
                                  (far1, far0, "skip", ""), (far0, N0, None, f"{gid}.backway.side_a"),
                                  (N0, N1, niche, f"{gid}.backway.niche.mouth"), (N1, sb0, None, f"{gid}.backway.side_a2")]):
        ld = m.linedefs[ln]
        if "sideback" in ld.fields:
            for sd in ("sidefront", "sideback"):
                m.sidedefs[ld[sd]].fields.update(texturetop=CLOSET_SKIN, texturebottom=CLOSET_SKIN)
        else:
            m.sidedefs[ld["sidefront"]]["texturemiddle"] = CLOSET_SKIN
    for ln in _edges(m, niche, [(N0, N1, "skip", ""), (N1, M1, None, f"{gid}.backway.niche.side_b"),
                                (M1, M0, shutter, f"{gid}.backway.niche.panel"), (M0, N0, None, f"{gid}.backway.niche.side_a")]):
        ld = m.linedefs[ln]
        if "sideback" in ld.fields:                          # the panel, on the niche's side, hung from the shutter's ceiling
            side = next(sd for sd in ("sidefront", "sideback") if m.sidedefs[ld[sd]]["sector"] == niche.index)
            m.sidedefs[ld[side]]["texturetop"] = CALL_SHUTTER_TEXTURE
        else:
            m.sidedefs[ld["sidefront"]]["texturemiddle"] = TRACK
    for ln in _edges(m, shutter, [(M0, M1, "skip", ""), (M1, B1, None, f"{gid}.backway.shutter.side_b"),
                                  (B1, B0, None, f"{gid}.backway.switch"), (B0, M0, None, f"{gid}.backway.shutter.side_a")]):
        ld = m.linedefs[ln]
        m.sidedefs[ld["sidefront"]]["texturemiddle"] = TRACK
        if ld["user_gid"].endswith(".switch"):                # the switch that sinks the box
            # SW1GRAY's plate (columns 16-47, rows 70-101) in the 32 x 32 window: hung from the window's top.
            m.sidedefs[ld["sidefront"]].fields.update(texturemiddle="SW1GRAY", offsetx=16, offsety=70)
            # Note #142 (2026-11-26): it sinks to a step (STORE_SHORTCUT_STEP) above the floor, not flush, so the box's wood
            # still has a face: Floor_LowerByValue, not Floor_LowerToLowest.
            ld.fields.update(special=20, arg0=STORE_SHORTCUT_TAG, arg1=16,
                             arg2=STORE_BACK[STORE_SHORTCUT][1] - STORE_SHORTCUT_STEP, playeruse=True)
    BACKWAY.update(sector=chamber, edge=(far0, far1), floor=floor)
    walls, shared = [], {}
    for k, (pts, bh) in enumerate(STORE_BACK):
        box = m.sector(f"{gid}.back_{k + 1}", floor=floor + bh, ceiling=floor + STORE_HIGH, light=STORE_LIGHT,
                       floor_tex=VESTIBULE_BOX_TOP, ceiling_tex=SIDE_WALL)
        m.sectors[box.index].fields.update(fadecolor=SIDE_FOG[0], fogdensity=SIDE_FOG[1], user_scenery=k != STORE_SHORTCUT)
        if k == STORE_SHORTCUT:                                  # note #127: it sinks from behind
            m.sectors[box.index]["id"] = STORE_SHORTCUT_TAG
        corners = [P(*q) for q in pts]
        walls.append((box, list(zip(corners, corners[1:] + corners[:1]))))
        for c0, c1 in walls[-1][1]:
            shared.setdefault(frozenset((c0, c1)), []).append(k)
    for k, (box, edges) in enumerate(walls):
        outline = []
        for j, (c0, c1) in enumerate(edges):
            other = [i for i in shared[frozenset((c0, c1))] if i != k]
            kind = (room if j == 0 else "skip" if other and other[0] > k else walls[other[0]][0] if other
                    else chamber if k == STORE_SHORTCUT and frozenset((c0, c1)) == frozenset((sb0, sb1)) else None)
            outline.append((c0, c1, kind, f"{gid}.back_{k + 1}.side_{j + 1}"))
        for ln in _edges(m, box, outline):
            ld = m.linedefs[ln]
            if "sideback" in ld.fields:
                for sd in ("sidefront", "sideback"):
                    m.sidedefs[ld[sd]]["texturebottom"] = VESTIBULE_BOX_SIDE
                    # Note #139: over the shortcut box, the wall down to the chamber's lower ceiling, seen from the
                    # storage room: the grotto's rock; seen from the chamber: the base's metal.
                    m.sidedefs[ld[sd]]["texturetop"] = CLOSET_SKIN if m.sidedefs[ld[sd]]["sector"] == chamber.index else SIDE_WALL
            else:
                m.sidedefs[ld["sidefront"]]["texturemiddle"] = VESTIBULE_BOX_SIDE
    boxes, sides = [], {}
    for k, (bu0, bd0, bu1, bd1, bh) in enumerate(STORE_BOXES):
        box = m.sector(f"{gid}.box_{k + 1}", floor=floor + bh, ceiling=floor + STORE_HIGH, light=STORE_LIGHT,
                       floor_tex=VESTIBULE_BOX_TOP, ceiling_tex=SIDE_WALL)
        m.sectors[box.index].fields.update(fadecolor=SIDE_FOG[0], fogdensity=SIDE_FOG[1], user_scenery=True)
        corners = [P(bu0, bd0), P(bu1, bd0), P(bu1, bd1), P(bu0, bd1)]
        boxes.append((box, list(zip(corners, corners[1:] + corners[:1]))))
        for c0, c1 in boxes[-1][1]:
            sides.setdefault(frozenset((c0, c1)), []).append(k)
    for k, (box, edges) in enumerate(boxes):
        # Note #97: a side two boxes share is one line between them, built by the later box.
        outline = []
        for j, (c0, c1) in enumerate(edges):
            other = [i for i in sides[frozenset((c0, c1))] if i != k]
            outline.append((c0, c1, "skip" if other and other[0] > k else boxes[other[0]][0] if other else room,
                            f"{gid}.box_{k + 1}.side_{j + 1}"))
        for ln in _edges(m, box, outline):
            for sd in ("sidefront", "sideback"):
                m.sidedefs[m.linedefs[ln][sd]]["texturebottom"] = VESTIBULE_BOX_SIDE
    to_door = round(math.degrees(math.atan2(-ux, uy))) % 360          # facing the door
    for k, (type_, u, d) in enumerate(STORE_MONSTERS):
        t = m.thing(type_, *P(u, d), f"{gid}.monster_{k + 1}", angle=to_door)
        m.things[t]["ambush"] = True
    for k, (type_, u, d) in enumerate(STORE_SHORTCUT_PRIZE):             # note #143: on the shortcut box, out of reach until it sinks
        m.thing(type_, *P(u, d), f"{gid}.back_3.prize_{k + 1}", angle=(k * 97) % 360)
    for k, (type_, u, d) in enumerate(STORE_DOOR_TORCHES):               # note #113
        m.thing(type_, *P(u, d), f"{gid}.torch_{k + 1}")
    n = 0
    for type_, spots in STORE_PICKUPS:                                    # note #97
        for u, d in spots:
            n += 1
            m.thing(type_, *P(u, d), f"{gid}.item_{n}", angle=(n * 53) % 360)


def great_door(m: MapBuilder, room, a, b, before=None, after=None) -> None:
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
    # Note #119: the wall either side of the doorway has the hall's mouldings (before / after: the far ends of
    # the walls it meets, for the mitres); they stop 16 short of the doorway.
    moulded_wall(m, room, a, P(-half, 0), "room.wall_n2", before=before, skip_end=16, line=(a, b))
    moulded_wall(m, room, P(half, 0), b, "room.wall_n2b", skip_start=16, after=after, line=(a, b))
    vest = m.sector("vestibule", floor=floor, ceiling=top, light=VESTIBULE_LIGHT)
    fog(m, vest)
    # Note #2 (2026-11-23): the wall above the doorway is the hall's own wall (it was a marble lintel,
    # which didn't match the walls round it): the same texture, hung from the ceiling like them, and
    # carried on from the wall on its left.
    from dms.gen import WALL
    opening = m.two_sided(P(-half, 0), P(half, 0), room, vest, "vestibule.opening", texture=WALL)
    m.linedefs[opening]["dontpegtop"] = True
    m.sidedefs[m.linedefs[opening]["sidefront"]]["offsetx"] = round(L / 2 - half)
    # The vestibule: the jambs (16 deep), then wider behind the wall.
    j = 16
    # Note #13 (2026-11-23): a torch set in the vestibule's wall VESTIBULE_TORCH_WALL (a niche like the
    # passage's: 24 wide, from the floor), to explain the room's red glow; the glow now comes from it.
    # Note #126 (2026-11-24): a second lit torch, in the wall beside the way out to the passage
    # (VESTIBULE_TORCH_WALLS), and both niches are rough hollows now, like the passage's (note #79).
    niches = {}
    for i in VESTIBULE_TORCH_WALLS:
        ta, tb = VESTIBULE_OUTLINE[i], VESTIBULE_OUTLINE[i + 1]
        tn = math.hypot(tb[0] - ta[0], tb[1] - ta[1])
        te = ((tb[0] - ta[0]) / tn, (tb[1] - ta[1]) / tn)
        to = (-te[1], te[0])                             # out of the room: away from its middle
        tmid = ((ta[0] + tb[0]) / 2, (ta[1] + tb[1]) / 2)
        if to[0] * (0 - tmid[0]) + to[1] * (100 - tmid[1]) > 0:
            to = (-to[0], -to[1])
        name = "vestibule.torch_niche" if i == VESTIBULE_TORCH_WALL else f"vestibule.torch_niche_{i + 1}"
        wide, deep, rough = rough_niche(name)
        t0 = (tmid[0] - te[0] * wide / 2, tmid[1] - te[1] * wide / 2)
        t1 = (tmid[0] + te[0] * wide / 2, tmid[1] + te[1] * wide / 2)
        back = [(t0[0] + te[0] * t2 + to[0] * s2, t0[1] + te[1] * t2 + to[1] * s2) for t2, s2 in rough]
        sec = m.sector(name, floor=floor, ceiling=floor + NICHE_HIGH, light=VESTIBULE_LIGHT + 72,
                       floor_tex=PASSAGE_TEXTURE, ceiling_tex=PASSAGE_TEXTURE)
        m.sectors[sec.index]["user_scenery"] = True
        fog(m, sec)
        niches[i] = (t0, t1, back, sec, tmid, to, name)

    # The side passage's entrance: SIDE_MOUTH wide, in the middle of the wall the first torch niche was in.
    side_sectors(m, floor)
    sa, sb = VESTIBULE_OUTLINE[VESTIBULE_SIDE_WALL], VESTIBULE_OUTLINE[VESTIBULE_SIDE_WALL + 1]
    sn = math.hypot(sb[0] - sa[0], sb[1] - sa[1])
    se = ((sb[0] - sa[0]) / sn, (sb[1] - sa[1]) / sn)
    smid = ((sa[0] + sb[0]) / 2, (sa[1] + sb[1]) / 2)
    side_in = (P(smid[0] - se[0] * SIDE_MOUTH / 2, smid[1] - se[1] * SIDE_MOUTH / 2),
               P(smid[0] + se[0] * SIDE_MOUTH / 2, smid[1] + se[1] * SIDE_MOUTH / 2))
    # Note #127: its wooden frame, out through the wall (away from the room's middle); the passage starts behind it.
    so = (-se[1], se[0])
    if so[0] * (0 - smid[0]) + so[1] * (100 - smid[1]) > 0:
        so = (-so[0], -so[1])
    side_in2 = (P(smid[0] - se[0] * SIDE_MOUTH / 2 + so[0] * FRAME_DEEP, smid[1] - se[1] * SIDE_MOUTH / 2 + so[1] * FRAME_DEEP),
                P(smid[0] + se[0] * SIDE_MOUTH / 2 + so[0] * FRAME_DEEP, smid[1] + se[1] * SIDE_MOUTH / 2 + so[1] * FRAME_DEEP))
    side_frame = timber_frame(m, side_in[0], side_in[1], side_in2[0], side_in2[1], vest, SIDE["sectors"][0],
                              "side_passage.frame_in")
    SIDE["entrance"] = side_in2

    def outline_edge(i):
        a2, b2 = P(*VESTIBULE_OUTLINE[i]), P(*VESTIBULE_OUTLINE[i + 1])
        if i == VESTIBULE_SIDE_WALL:
            return [(a2, side_in[0], None, f"vestibule.wall_{i + 1}_a"),
                    (side_in[0], side_in[1], "skip", ""),      # (timber_frame builds the opening: note #130)
                    (side_in[1], b2, None, f"vestibule.wall_{i + 1}_b")]
        if i not in niches:
            return [(a2, b2, None, f"vestibule.wall_{i + 1}")]
        t0, t1, _, sec, _, _, name = niches[i]
        return [(a2, P(*t0), None, f"vestibule.wall_{i + 1}_a"),
                (P(*t0), P(*t1), sec, f"{name}.mouth"),
                (P(*t1), b2, None, f"vestibule.wall_{i + 1}_b")]
    _edges(m, vest, [
        (P(half, 0), P(-half, 0), "skip", ""),
        (P(-half, 0), P(-half, j), None, "vestibule.jamb_w"),
        (P(-half, j), P(*VESTIBULE_OUTLINE[0]), None, "vestibule.wall_sw"),
    ] + [e for i in range(len(VESTIBULE_OUTLINE) - 1) for e in outline_edge(i)] + [
        (P(*PASSAGE[0][0]), P(*PASSAGE[0][1]), "skip", ""),     # the passage's opening (passage())
        (P(*PASSAGE[0][1]), P(half, j), None, "vestibule.wall_se"),
        (P(half, j), P(half, 0), None, "vestibule.jamb_e"),
    ])
    # Note #3 (2026-11-23): the vestibule in the passage's style: mossy stone on its walls, floor and
    # ceiling (the jambs, in the thickness of the hall's wall, stay the hall's).
    m.sectors[vest.index].fields.update(texturefloor=PASSAGE_TEXTURE, textureceiling=PASSAGE_TEXTURE)
    for i, (t0, t1, back, sec, tmid, to, name) in niches.items():
        ring = [t1] + back[::-1] + [t0]
        _edges(m, sec, [(P(*t0), P(*t1), "skip", "")]
               + [(P(*c0), P(*c1), None, f"vestibule.wall_torch_{i + 1}.rock_{n + 1}") for n, (c0, c1) in enumerate(zip(ring, ring[1:]))])
        m.thing(TORCH, *P(tmid[0] + to[0] * NICHE_TORCH_IN, tmid[1] + to[1] * NICHE_TORCH_IN),
                "vestibule.torch" if i == VESTIBULE_TORCH_WALL else f"vestibule.torch_{i + 1}")
    for ld in m.linedefs:
        if ld["user_gid"].startswith("vestibule.wall_"):
            m.sidedefs[ld["sidefront"]]["texturemiddle"] = PASSAGE_TEXTURE
        elif ld["user_gid"].startswith("vestibule.torch_niche") and ld["user_gid"].endswith(".mouth"):
            for side in ("sidefront", "sideback"):
                m.sidedefs[ld[side]].fields.update(texturetop=PASSAGE_TEXTURE, texturebottom=PASSAGE_TEXTURE)
        elif ld["user_gid"] == "side_passage.entrance":
            for side in ("sidefront", "sideback"):
                m.sidedefs[ld[side]].fields.update(texturetop=FRAME_WOOD, texturebottom=FRAME_WOOD)
    tmid, to = niches[VESTIBULE_TORCH_WALL][4], niches[VESTIBULE_TORCH_WALL][5]      # the first torch: the red glow's
    passage(m, vest, P, floor)
    side_passage(m)                                            # needs both its openings (the vestibule's, the passage's)
    for k, (bu0, bd0, bu1, bd1, bh) in enumerate(VESTIBULE_BOXES):                 # note #121
        box = m.sector(f"vestibule.box_{k + 1}", floor=floor + bh, ceiling=top, light=VESTIBULE_LIGHT,
                       floor_tex=VESTIBULE_BOX_TOP, ceiling_tex=PASSAGE_TEXTURE)
        fog(m, box)
        m.sectors[box.index]["user_scenery"] = True
        corners = [P(bu0, bd0), P(bu1, bd0), P(bu1, bd1), P(bu0, bd1)]
        for ln in _edges(m, box, [(c0, c1, vest, f"vestibule.box_{k + 1}.side_{j + 1}")
                                  for j, (c0, c1) in enumerate(zip(corners, corners[1:] + corners[:1]))]):
            for sd in ("sidefront", "sideback"):
                m.sidedefs[m.linedefs[ln][sd]]["texturebottom"] = VESTIBULE_BOX_SIDE
    # Note #118 (2026-11-26): a beam of the hall's green light falling through the crack between the leaves onto the
    # vestibule's floor: a wedge on the floor, narrow at the crack and widening into the room, in bands that fade
    # (each its own light, tinted green; only the floor). Not a dynamic light: a slice of the floor.
    bands = [(d, w) for d, w in CRACK_BEAM]
    beam = []
    for k, ((d0, w0), (d1, w1), lit) in enumerate(zip(bands, bands[1:], CRACK_BEAM_LIGHT)):
        sec = m.sector(f"vestibule.beam_{k + 1}", floor=floor, ceiling=top, light=VESTIBULE_LIGHT,
                       floor_tex=PASSAGE_TEXTURE, ceiling_tex=PASSAGE_TEXTURE)
        m.sectors[sec.index].fields.update(lightfloor=lit, lightfloorabsolute=True, color_floor=CRACK_BEAM_COLOUR,
                                           user_scenery=True)   # only light on the floor: the movement check took its bands for narrow gaps
        fog(m, sec)
        beam.append((sec, [P(-w0, d0), P(w0, d0), P(w1, d1), P(-w1, d1)]))
    for k, (sec, (a, b, c, d)) in enumerate(beam):
        _edges(m, sec, [(a, b, vest if k == 0 else "skip", f"vestibule.beam_{k + 1}.near"),
                        (b, c, vest, f"vestibule.beam_{k + 1}.side_b"),
                        (c, d, beam[k + 1][0] if k + 1 < len(beam) else vest, f"vestibule.beam_{k + 1}.far"),
                        (d, a, vest, f"vestibule.beam_{k + 1}.side_a")])
    for k, (iu, idd) in enumerate(VESTIBULE_IMPS):
        # Facing the doors; note #140: the one behind the gap (the first) has his back to them, so he doesn't
        # spot the player through the crack at once (he still hears: not deaf).
        imp = m.thing(IMP, *P(iu, idd), f"vestibule.imp_{k + 1}",
                      angle=(round(math.degrees(math.atan2(-ux, uy))) + (180 if k == 0 else 0)) % 360)
    imp = m.thing(IMP, *P(*VESTIBULE_AMBUSH_IMP), "vestibule.imp_ambush",
                  angle=round(math.degrees(math.atan2(-ux, uy))) % 360)
    m.things[imp]["ambush"] = True
    glow = m.thing(9830, *P(tmid[0] - to[0] * 20, tmid[1] - to[1] * 20), "vestibule.glow")   # in front of the torch
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
        # Note #61 (2026-11-23): no skulls on the inside: a leaf's back, seen from the vestibule, is the
        # plain wood and iron of the other leaf (LEAF_TEXTURES[0]).
        vest_side(by_gid(f"{gid}.back"))["texturebottom"] = LEAF_TEXTURES[0]
        return s
    w0, w1 = WICKET
    leaf(1, 0, length, "great_door.leaf_e", (vest, vest))
    # The left leaf, with the small door (notes #50, #57, #58): pieces in the leaf's own (s, t), built
    # through one table of edges so pieces that meet share their lines; edges nobody else has face the
    # vestibule. Note #1 (2026-11-23): the door slides up (it sank into the floor): a real door sector,
    # shut (ceiling on the floor), between the frame in front and a recess of the same height behind
    # (wicket_back), so from both sides only the door's own height shows and the leaf above stays put.
    # Door_Raise (12: tag, speed, delay) opens it to 4 under those two ceilings (WICKET_HIGH), from either side.
    fd, fw, fh = FRAME
    td = (fd + T) / 2               # the door's back face: the door is the front half of what's left of the leaf
    a0, a1 = w0 - fw, w1 + fw
    solid = dict(floor=top, ceiling=top, light=VESTIBULE_LIGHT)
    # Note #55 (2026-11-23): the way through the small door is a slight wooden step (it was the default
    # grey floor): its frame, the door's own floor and the recess behind it are WICKET_STEP up, in boards.
    sill = floor + WICKET_STEP
    pieces = {
        "great_door.leaf_w": (m.sector("great_door.leaf_w", **solid), [(0, 0), (a0, 0), (a0, fd), (a0, T), (0, T)]),
        "great_door.frame": (m.sector("great_door.frame", floor=sill, ceiling=sill + WICKET_HIGH + fh,
                                      light=VESTIBULE_LIGHT, ceiling_tex=WICKET_SILL, floor_tex=WICKET_SILL),
                             [(a0, 0), (a1, 0), (a1, fd), (w1, fd), (w0, fd), (a0, fd)]),
        "great_door.post_w": (m.sector("great_door.post_w", **solid), [(a0, fd), (w0, fd), (w0, td), (w0, T), (a0, T)]),
        "great_door.wicket": (m.sector("great_door.wicket", floor=sill, ceiling=sill, light=VESTIBULE_LIGHT,
                                       ceiling_tex=WICKET_SILL, floor_tex=WICKET_SILL),
                              [(w0, fd), (w1, fd), (w1, td), (w0, td)]),
        "great_door.wicket_back": (m.sector("great_door.wicket_back", floor=sill, ceiling=sill + WICKET_HIGH + fh,
                                            light=VESTIBULE_LIGHT, ceiling_tex=WICKET_SILL, floor_tex=WICKET_SILL),
                                   [(w0, td), (w1, td), (w1, T), (w0, T)]),
        "great_door.post_e": (m.sector("great_door.post_e", **solid), [(w1, fd), (a1, fd), (a1, T), (w1, T), (w1, td)]),
        "great_door.leaf_w2": (m.sector("great_door.leaf_w2", **solid), [(a1, 0), (length, 0), (length, T), (a1, T), (a1, fd)]),
    }
    fog(m, pieces["great_door.frame"][0])
    # Note #72 (2026-11-23): the step's boards ran askew to the door (flats lie along the map's axes, the
    # leaf is swung): turned to run with the leaf, in all three sectors of the way through.
    leaf_dir = (leaf_point(0, 1, 0)[0] - leaf_point(0, 0, 0)[0], leaf_point(0, 1, 0)[1] - leaf_point(0, 0, 0)[1])
    for name in ("great_door.frame", "great_door.wicket", "great_door.wicket_back"):
        turn = round(math.degrees(math.atan2(leaf_dir[1], leaf_dir[0])), 2)
        m.sectors[pieces[name][0].index].fields.update(rotationfloor=turn, rotationceiling=turn)   # note #94: the wooden ceiling too
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
            L.fields.update(special=12, arg0=WICKET_TAG, arg1=16, arg2=105, playeruse=True, monsteruse=True,
                            repeatspecial=True)
            # The door's face is the upper part of the side looking at it, hung from the door's underside
            # (so it rides up with it): WICKET_OFFSET's row at WICKET_HIGH above the floor.
            fs.fields.update(texturetop=WICKET_TEXTURE, offsetx_top=WICKET_OFFSET[0],
                             offsety_top=WICKET_OFFSET[1] + WICKET_HIGH - WICKET_TEXTURE_HIGH)
        elif is_wicket:                                 # the door's sides
            fs["texturebottom"] = bs["texturebottom"] = "DOORTRAK"
        elif other is vest:                                             # the leaf's face and back
            vs = fs
            side = "face" if t0 == 0 else "back"
            vs.fields.update(texturetop=LEAF_TEXTURES[0], texturebottom=LEAF_TEXTURES[0],
                             offsetx=skull_offset(0, side, lo, hi))
            L.fields.update(dontpegtop=True, blocking=name not in ("great_door.frame", "great_door.wicket_back"))
            if name in ("great_door.frame", "great_door.wicket_back"):
                vs["texturebottom"] = CISTERN_WOOD                      # the step's riser (note #55)
    return None


def cistern_door(m: MapBuilder, stair, a, b) -> None:
    """Note #41: the big wooden door in the stairs' west wall a -> b (the stair on its right), in the
    middle of it, shut until the cistern's switch is used; behind it a chamber with two shotgunners and
    a red glow. Built in the wall's own frame (u along it from its middle, d away from the stairs)."""
    import math
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
    mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
    P = lambda u, d: (round(mx + u * ux - d * uy, 2), round(my + u * uy + d * ux, 2))
    half, thick = CISTERN_DOOR_WIDE / 2, 16
    floor = m.sectors[stair.index]["heightfloor"]
    gid = "cistern_door"
    # Note #63: its floor is a slight wooden step, like the small door's (note #55): WICKET_STEP up, boards.
    door = m.sector(gid, floor=floor + WICKET_STEP, ceiling=floor + WICKET_STEP, light=PASSAGE_LIGHT,
                    floor_tex=WICKET_SILL, ceiling_tex=CISTERN_BOARDS)
    m.sectors[door.index]["id"] = CISTERN_DOOR_TAG
    room = m.sector(f"{gid}.room", floor=floor, ceiling=floor + CISTERN_DOOR_ROOM_HIGH, light=CISTERN_DOOR_LIGHT,
                    floor_tex=PASSAGE_TEXTURE, ceiling_tex=PASSAGE_TEXTURE)
    m.sectors[room.index]["lightcolor"] = CISTERN_DOOR_TINT
    # The stairs' wall either side, and the door's two faces: each the upper part of the side looking at
    # it, hung from the door's underside so it rides up with it.
    m.wall(a, P(-half, 0), stair, f"{gid}.wall_s", texture=PASSAGE_TEXTURE)
    m.wall(P(half, 0), b, stair, f"{gid}.wall_n", texture=PASSAGE_TEXTURE)
    for name, p, q, front in (("face", P(-half, 0), P(half, 0), stair), ("back", P(half, thick), P(-half, thick), room)):
        ln = m.two_sided(p, q, front, door, f"{gid}.{name}", texture=CISTERN_DOOR_TEXTURE)
        m.sidedefs[m.linedefs[ln]["sidefront"]]["offsetx"] = round((128 - CISTERN_DOOR_WIDE) / 2)
        m.sidedefs[m.linedefs[ln]["sidefront"]]["texturebottom"] = CISTERN_WOOD   # the step's riser
    for name, p, q in (("jamb_s", P(-half, 0), P(-half, thick)), ("jamb_n", P(half, thick), P(half, 0))):
        ln = m.wall(p, q, door, f"{gid}.{name}", texture="DOORTRAK")
        m.linedefs[ln]["dontpegbottom"] = True                 # the track stays put as the door rises
    # The chamber behind it.
    # Note #53: an irregular outline (CISTERN_DOOR_OUTLINE), from one side of the door round to the other.
    ring = [P(half, thick)] + [P(u, d) for u, d in CISTERN_DOOR_OUTLINE] + [P(-half, thick)]
    tu0, tu1, td = TECH_DOOR
    far = (P(tu1 + TECH_DOOR_POST, td), P(tu0 - TECH_DOOR_POST, td))                # the far wall, as the ring runs: the tech door is in it
    assert far[0] in ring and ring[ring.index(far[0]) + 1] == far[1], "TECH_DOOR must sit in the outline's far wall"
    _edges(m, room, [(P(-half, thick), P(half, thick), "skip", "")]
           + [(a2, b2, "skip" if (a2, b2) == far else None, f"{gid}.room.wall_{i + 1}")
              for i, (a2, b2) in enumerate(zip(ring, ring[1:]))])
    for ld in m.linedefs:                                  # the room's own walls: the passage's mossy rock
        if ld["user_gid"].startswith(f"{gid}.room.wall_"):
            m.sidedefs[ld["sidefront"]]["texturemiddle"] = PASSAGE_TEXTURE
    tech_door(m, room, P, floor)
    crates, edges = [], {}
    for i, (u0, d0, u1, d1, high, side, top) in enumerate(CISTERN_DOOR_CRATES):
        crate = m.sector(f"{gid}.crate_{i + 1}", floor=floor + high, ceiling=floor + CISTERN_DOOR_ROOM_HIGH,
                         light=CISTERN_DOOR_LIGHT, floor_tex=top, ceiling_tex=PASSAGE_TEXTURE)
        m.sectors[crate.index].fields.update(lightcolor=CISTERN_DOOR_TINT, user_scenery=True)
        corners = [P(u0, d0), P(u1, d0), P(u1, d1), P(u0, d1)]
        crates.append((crate, list(zip(corners, corners[1:] + corners[:1])), side))
        for c0, c1 in crates[-1][1]:
            edges.setdefault(frozenset((c0, c1)), []).append(i)
    for i, (crate, sides, side) in enumerate(crates):
        outline = []
        for j, (c0, c1) in enumerate(sides):
            # A side two crates share (one stacked against the other) is one line between them, built by the later one.
            sharing = [k for k in edges[frozenset((c0, c1))] if k != i]
            other = "skip" if sharing and sharing[0] > i else crates[sharing[0]][0] if sharing else room
            outline.append((c0, c1, other, f"{gid}.crate_{i + 1}.side_{j + 1}"))
        for ln in _edges(m, crate, outline):
            for sd in ("sidefront", "sideback"):               # seen from whichever side is lower
                m.sidedefs[m.linedefs[ln][sd]]["texturebottom"] = side
    m.thing(MEDIKIT, *P(*CISTERN_DOOR_MEDIKIT), f"{gid}.medikit")          # note #89
    # Note #87: the switch post, the room on the right of each of its lines (the front: where it's used from).
    su0, sd0, su1, sd1 = CISTERN_DOOR_SWITCH
    post = m.sector(f"{gid}.switch", floor=floor + 48, ceiling=floor + CISTERN_DOOR_ROOM_HIGH, light=CISTERN_DOOR_LIGHT,
                    floor_tex=PASSAGE_TEXTURE, ceiling_tex=PASSAGE_TEXTURE)
    m.sectors[post.index].fields.update(lightcolor=CISTERN_DOOR_TINT, id=CISTERN_DOOR_SWITCH_TAG, user_scenery=True)
    pts = [P(su0, sd0), P(su1, sd0), P(su1, sd1), P(su0, sd1)]
    if sum(p[0] * q[1] - q[0] * p[1] for p, q in zip(pts, pts[1:] + pts[:1])) < 0:      # clockwise: turn it round
        pts.reverse()
    face = {P(su1, sd0), P(su1, sd1)}
    for j, (p, q) in enumerate(zip(pts, pts[1:] + pts[:1])):
        ln = m.two_sided(p, q, room, post, f"{gid}.switch.side_{j + 1}", texture=CISTERN_WOOD)
        if {p, q} == face:
            m.sidedefs[m.linedefs[ln]["sidefront"]].fields.update(texturebottom=CISTERN_SWITCH, offsety_bottom=64)
            m.linedefs[ln].fields.update(special=11, arg0=CISTERN_DOOR_TAG, arg1=4, playeruse=True)
    out = round(math.degrees(math.atan2(-ux, uy))) % 360       # facing the door (towards the stairs)
    for i, (u, d, kind) in enumerate(CISTERN_DOOR_GUARDS):
        # Note #116 (2026-11-26): half of them zombiemen, one of each kind (roused, ordinary, deaf), like the shotgunners.
        t = m.thing(3004 if i in CISTERN_DOOR_ZOMBIES else SHOTGUNNER, *P(u, thick + d), f"{gid}.guard_{i + 1}", angle=out)
        if kind == "wake":                                     # zscript.zs sets these on the player at the switch
            m.things[t]["id"] = CISTERN_DOOR_WAKE_TID
        elif kind == "deaf":
            m.things[t]["ambush"] = True
    # The red glow: dormant (a dynamic light shines through a shut door) until zscript.zs wakes it as the
    # door starts to open.
    r, g, bl, rad = CISTERN_DOOR_GLOW
    glow = m.thing(9830, *P(0, thick + 40), f"{gid}.glow")
    m.things[glow].fields.update(height=56, arg0=r, arg1=g, arg2=bl, arg3=rad, id=CISTERN_DOOR_GLOW_TID, dormant=True)


def post_lamp(m: MapBuilder, room, P, floor, ua, ub, d, gid: str, back: bool = False) -> None:
    """Note #91: one of the tech door's posts, from u `ua` to `ub` along the far wall (the room on the right
    as u rises): a stripe of the track's metal, a channel set into the wall with the red tube at its back
    (full bright, a pulsing red light in front), another stripe. Note #138: back=True for the tech room's side,
    where the room is beyond the wall (larger d): the lines run the other way and the channel goes in to smaller d."""
    c0, c1 = ua + TECH_POST_STRIPE, ub - TECH_POST_STRIPE
    sgn = -1 if back else 1
    wall = (lambda a, b, sec, g, **kw: m.wall(b, a, sec, g, **kw)) if back else (lambda a, b, sec, g, **kw: m.wall(a, b, sec, g, **kw))
    wall(P(ua, d), P(c0, d), room, f"{gid}_a", texture=TECH_DOOR_FRAME)
    chan = m.sector(f"{gid}.lamp", floor=floor + TECH_POST_LAMP_Z, ceiling=floor + TECH_DOOR_HIGH, light=CHANNEL_LIGHT,
                    floor_tex=TRACK, ceiling_tex=TRACK)
    m.sectors[chan.index].fields.update(lightcolor=CHANNEL_TINT, user_scenery=True)
    k = TECH_POST_LAMP_DEEP * sgn
    made = _edges(m, chan, [(P(c0, d), P(c1, d), room, f"{gid}.lamp.mouth"), (P(c1, d), P(c1, d + k), None, f"{gid}.lamp.side_b"),
                            (P(c1, d + k), P(c0, d + k), None, f"{gid}.lamp.back"), (P(c0, d + k), P(c0, d), None, f"{gid}.lamp.side_a")])
    for ln in made:
        ld = m.linedefs[ln]
        if "sideback" in ld.fields:                            # the post's metal above and below the channel
            for sd in ("sidefront", "sideback"):
                m.sidedefs[ld[sd]].fields.update(texturetop=TECH_DOOR_FRAME, texturebottom=TECH_DOOR_FRAME)
        elif ld["user_gid"].endswith(".back"):                 # the tube, glowing
            m.sidedefs[ld["sidefront"]].fields.update(texturemiddle=CHANNEL_TEXTURE, light=255, lightabsolute=True)
        else:
            m.sidedefs[ld["sidefront"]]["texturemiddle"] = TECH_DOOR_FRAME
    wall(P(c1, d), P(ub, d), room, f"{gid}_b", texture=TECH_DOOR_FRAME)
    r, g, bl = TECH_DOOR_LAMP_RGB
    lamp = m.thing(9831, *P((c0 + c1) / 2, d - 12 * sgn), f"{gid}.lamp.light", angle=TECH_DOOR_LAMP_PERIOD)
    m.things[lamp].fields.update(height=(TECH_POST_LAMP_Z + TECH_DOOR_HIGH) // 2, arg0=r, arg1=g, arg2=bl,
                                 arg3=TECH_POST_LAMP_RADIUS[0], arg4=TECH_POST_LAMP_RADIUS[1])


def tech_door(m: MapBuilder, room, P, floor) -> None:
    """Note #77: the tech door in the shotgunner room's far wall, and the corridor behind it, in the room's
    frame P(u along the stairs' wall, d away from the stairs). Along d: the far wall, a recess 8 deep
    (TECH_DOOR_HIGH high: the door's own height shows, under a metal lintel), the door 16 thick, then the
    corridor, 128 wide about the door's middle and TECH_HALL_LONG long, like the start closet."""
    u0, u1, d = TECH_DOOR
    I = lambda u, dd: tuple(round(v) for v in P(u, dd))        # whole numbers: the channel walls round theirs
    A, B = P(u0 - TECH_DOOR_POST, d), P(u1 + TECH_DOOR_POST, d)    # the far wall's ends
    R0, R1, S0, S1 = P(u0, d), P(u1, d), P(u0, d + 8), P(u1, d + 8)
    T0, T1 = I(u0, d + 24), I(u1, d + 24)
    mid = (u0 + u1) / 2
    half = TECH_HALL_WIDE / 2
    # Note #84: with the room twice as high, the door needs a recess on this side too (TECH_DOOR_HIGH high,
    # 8 deep), or its face would run up the whole wall.
    U0, U1 = I(u0, d + 32), I(u1, d + 32)
    C0, C1 = I(mid - half, d + 32), I(mid + half, d + 32)
    C2, C3 = I(mid + half, d + 32 + TECH_HALL_LONG), I(mid - half, d + 32 + TECH_HALL_LONG)
    light = m.sectors[room.index]["lightlevel"]
    recess = m.sector("tech_door.recess", floor=floor, ceiling=floor + TECH_DOOR_HIGH, light=light,
                      floor_tex=PASSAGE_TEXTURE, ceiling_tex=TRACK)
    m.sectors[recess.index]["lightcolor"] = CISTERN_DOOR_TINT
    # Note #93 (2026-11-26): its underside dark metal (it took the techbase ceiling, a grate, by default).
    door = m.sector("tech_door", floor=floor, ceiling=floor, light=CLOSET_LIGHT, ceiling_tex=TECH_DOOR_UNDER)
    m.sectors[door.index]["id"] = TECH_DOOR_TAG
    hall = m.sector("tech_hall", floor=floor, ceiling=floor + TECH_HALL_HIGH, light=TECH_HALL_LIGHT)
    # Note #114 (2026-11-26): the ceiling's two stripes centred on the door (they sat about 7 south of its middle,
    # measured from the mapper's screenshot; a ceiling's y panning moves its picture north).
    m.sectors[hall.index]["ypanningceiling"] = TECH_HALL_CEIL_PAN
    recess2 = m.sector("tech_door.recess_e", floor=floor, ceiling=floor + TECH_DOOR_HIGH, light=TECH_HALL_LIGHT,
                       ceiling_tex=TRACK)
    use = dict(special=12, arg0=TECH_DOOR_TAG, arg1=16, arg2=105, playeruse=True, monsteruse=True, repeatspecial=True)
    # The room's far wall, the room on the right (u rising), with the recess's mouth in it.
    # Note #88: a metal frame round the door: the 16 of wall either side of it and the wall above it (the
    # room's rock in note #81, a METAL4 lintel alone before that), announcing the base beyond.
    # Note #122: the red bar runs across the whole frame, post to post, 128 long: the red tube from end to end,
    # nothing cut off (over the door alone, 64 wide, only its middle fitted). Each post's texture carries its
    # end of the bar at the same height (textures.txt CACOBARL, CACOBARR); all three a little brighter than
    # the room, alike (the panel alone was full bright).
    # Note #124: "there should just be one small red lit element above the door. leave the sides alone": the posts
    # are plain frame metal again, and the light is a small lamp in the middle of the panel over the door
    # (CACOBAR: a 32 x 12 piece of the tube), the panel full bright as in note #108.
    # Note #91 (2026-11-26): the lamp over the door (notes #108, #124: CACOBAR, full bright, a pulsing red light)
    # is gone; each post has an upright lamp set into it instead (post_lamp).
    post_lamp(m, room, P, floor, u0 - TECH_DOOR_POST, u0, d, "tech_door.wall_n")
    mouth = m.two_sided(R0, R1, room, recess, "tech_door.mouth", texture=TECH_DOOR_FRAME)
    post_lamp(m, room, P, floor, u1, u1 + TECH_DOOR_POST, d, "tech_door.wall_s")
    made = _edges(m, recess, [(R0, R1, "skip", ""), (R1, S1, None, "tech_door.recess.side_s"),
                              (S1, S0, door, "tech_door.face"), (S0, R0, None, "tech_door.recess.side_n")])
    for ln in made:
        ld = m.linedefs[ln]
        if "sideback" in ld.fields:                            # the door's face, hung from its underside
            m.sidedefs[ld["sidefront"]]["texturetop"] = TECH_DOOR_TEXTURE
            ld.fields.update(use)
        else:
            m.sidedefs[ld["sidefront"]]["texturemiddle"] = TRACK
    for ln in _edges(m, door, [(S0, S1, "skip", ""), (S1, T1, None, "tech_door.jamb_s"), (T1, T0, "skip", ""),
                               (T0, S0, None, "tech_door.jamb_n")]):
        m.sidedefs[m.linedefs[ln]["sidefront"]]["texturemiddle"] = "DOORTRAK"
        m.linedefs[ln]["dontpegbottom"] = True                 # the track stays put as the door rises
    # The corridor, on the right of each line: the door's wall (u falling), the north wall out, the end
    # wall, the south wall back.
    for ln in _edges(m, recess2, [(T0, T1, door, "tech_door.back"), (T1, U1, None, "tech_door.recess_e.side_s"),
                                  (U1, U0, "skip", ""), (U0, T0, None, "tech_door.recess_e.side_n")]):
        ld = m.linedefs[ln]
        if "sideback" in ld.fields:
            m.sidedefs[ld["sidefront"]]["texturetop"] = TECH_DOOR_TEXTURE
            ld.fields.update(use)
        else:
            m.sidedefs[ld["sidefront"]]["texturemiddle"] = TRACK
    before = len(m.linedefs)
    # Note #138 (2026-11-26): the door the same on this side as on the other: posts of the track's metal, each with
    # an upright red lamp set into it (post_lamp, mirrored), and the frame's metal over the door.
    pw = TECH_DOOR_POST
    m.wall(C1, I(u1 + pw, d + 32), hall, "tech_hall.wall_door_s")
    post_lamp(m, hall, I, floor, u1, u1 + pw, d + 32, "tech_hall.door_post_s", back=True)
    m.two_sided(U1, U0, hall, recess2, "tech_door.mouth_e", texture=TECH_DOOR_FRAME)
    post_lamp(m, hall, I, floor, u0 - pw, u0, d + 32, "tech_hall.door_post_n", back=True)
    m.wall(I(u0 - pw, d + 32), C0, hall, "tech_hall.wall_door_n")
    wall_with_channels(m, hall, C0, C3, "tech_hall.wall_n", floor=floor, channels=TECH_HALL_CHANNELS, high=TECH_HALL_HIGH)
    station(m, hall, C3, C2, floor)                            # note #92: the way on, through the end wall
    wall_with_channels(m, hall, C2, C1, "tech_hall.wall_s", floor=floor, channels=TECH_HALL_CHANNELS, high=TECH_HALL_HIGH)
    for ld in m.linedefs[before:]:                             # the closet's wall: METAL4 over the track strip
        sd = m.sidedefs[ld["sidefront"]]
        if "sideback" not in ld.fields and sd["sector"] == hall.index and sd.get("texturemiddle") == CLOSET_WALL:
            sd["texturemiddle"] = BASE_TEXTURE
            ld["dontpegbottom"] = True


# ---- Note #92 (2026-11-24): the pumping station ---------------------------------------------------
# Past the tech room: "a small complex of a hydro power pumping station - pipes, big computer and machinery
# rigs, lots of little nooks and crannies for items and enemy ambushes, access doors to back stairways up
# to catwalks... a big cavernous main room with pump machinery ringed / crossed by catwalks - and the
# ancillary rooms and hallways that surround and interconnect it. no monster or items yet, just plotting out
# the layout", kept fairly light so it can be seen (mood lighting later).
#
# Drawn on a grid (station_zones: rectangles, x east and y north from STATION's origin, heights from the
# tech room's floor) and turned into sectors and lines by raster(). Textures are first picks, to be
# chosen properly in the asset browser.
STATION_CATWALK_TAG = 700       # every sector with catwalk over it (one 3D floor)
STATION_CATWALK = (136, 144)    # its underside and top, above the ground floor; note #126 (2026-11-26): above the
                                # doors' frames (128; it was 88-96, lower than their tops)
STATION_STAIR_STEPS, STATION_STAIR_RISE, STATION_STAIR_DEEP = 8, 18, 24   # note #126: up to the catwalk's 144
STATION_DOOR_TAG = 710          # the doors' tags count up from here
STATION_DOOR, STATION_FRAME, STATION_TRACK = "BIGDOOR2", "SUPPORT3", "DOORTRAK"
STATION_LIGHT = 176
# Note #127: the box room's crates (x0, y0, x1, y1, height, side texture) and the back tunnel's mouth in its north
# wall (x0, x1 at y 752), the tunnel's line (y of its long stretch, x of its last), width.
STATION_BOXES = ((-480, 384, -416, 448, 64, "CRATE1"), (-480, 448, -416, 512, 96, "CRATE2"),
                 (-416, 384, -352, 448, 48, "CRATE3"), (-240, 384, -176, 448, 64, "CRATE1"),
                 (-224, 656, -160, 720, 48, "CRATE2"), (-480, 656, -416, 736, 64, "CRATE3"))
STATION_BACK_TUNNEL = (-336, -272)
STATION_BOX_GUARDS = ((3004, -300, 600), (3004, -220, 540), (9, -380, 560))   # note #145: two zombiemen and a shotgunner, facing the door (east)
BACK_TUNNEL_Y, BACK_TUNNEL_WIDE, BACK_TUNNEL_X = 3120, 64, -770
# Note #136 (2026-11-26): a narrow access tunnel: lower (72), rusty brown underfoot and overhead, and now and then a
# candle in a small niche in its north wall (every BACK_TUNNEL_CANDLES along the long stretch), its feeble glow
# the engine's own.
BACK_TUNNEL_HIGH, BACK_TUNNEL_FLOOR, BACK_TUNNEL_CEIL = 72, "SLIME16", "SLIME15"
BACK_TUNNEL_CANDLES, BACK_TUNNEL_NICHE = 320, (16, 8)   # every, and the niche's width and depth
BACK_TUNNEL_STEPS, BACK_TUNNEL_STEP_LONG = 4, 64          # note #141: the rise to the storage room's level, gently


def station_zones() -> list[dict]:
    """The station's plan, in order (a later zone covers an earlier one)."""
    Z: list[dict] = []
    doors = [0]

    def base(key, x0, y0, x1, y1, **a):
        a = {"floor": 0, "ceil": 128, "light": STATION_LIGHT, "wall": "STARG3", "floor_tex": "FLAT5_4",
             "ceil_tex": "CEIL3_5", **a}
        a["ceil"] = a["ceil"] + (a["floor"] if a.pop("above", False) else 0)
        Z.append({"box": (x0, y0, x1, y1), "base": {"key": key, **a}})

    def void(x0, y0, x1, y1):
        Z.append({"box": (x0, y0, x1, y1), "void": True})

    def catwalk(x0, y0, x1, y1):
        Z.append({"box": (x0, y0, x1, y1), "over": {"tag": STATION_CATWALK_TAG}, "suffix": "_cw"})

    def door(key, x0, y0, x1, y1, floor=0, high=128, tex=STATION_DOOR, **a):
        """A door across a wall 48 thick: a recess, the door (16), a recess. The wall is thin along x
        when x1 - x0 == 48, else along y."""
        tag = STATION_DOOR_TAG + doors[0]
        doors[0] += 1
        frame = {"floor": floor, "ceil": floor + high, "wall": STATION_FRAME, "side": STATION_FRAME, **a}
        leaf = {"floor": floor, "ceil": floor, "wall": STATION_TRACK, "side": tex, "door": tag, **a}
        if x1 - x0 == 48:
            base(f"{key}_a", x0, y0, x0 + 16, y1, **frame)
            base(key, x0 + 16, y0, x0 + 32, y1, **leaf)
            base(f"{key}_b", x0 + 32, y0, x1, y1, **frame)
        else:
            base(f"{key}_a", x0, y0, x1, y0 + 16, **frame)
            base(key, x0, y0 + 16, x1, y0 + 32, **leaf)
            base(f"{key}_b", x0, y0 + 32, x1, y1, **frame)

    hall = {"ceil": 320, "light": 192, "wall": "ICKWALL3", "floor_tex": "FLOOR0_3", "ceil_tex": "CEIL5_1"}
    pit = {**hall, "wall": "PIPEWAL1", "side": "PIPEWAL1", "floor_tex": "FLAT1"}
    machine = {**hall, "side": "PIPE2", "floor_tex": "CEIL5_1", "scenery": True}
    pipes = {"ceil": 96, "wall": "PIPEWAL1", "floor_tex": "FLAT1", "ceil_tex": "CEIL5_1"}
    comp = {"ceil": 144, "wall": "SILVER1", "floor_tex": "FLAT14", "ceil_tex": "CEIL3_5", "light": 192}
    gen = {"ceil": 224, "wall": "TEKGREN2", "floor_tex": "FLOOR0_3", "ceil_tex": "CEIL5_1", "light": 192}
    store = {"wall": "BROWN96", "floor_tex": "FLAT5_4"}

    # The way in from the tech room, and the service passages north and south off it (one space).
    base("service", 0, -64, 112, 64)
    base("service", 16, 64, 112, 496)
    base("service", 16, -432, 112, -64)
    # Note #140: the guard posts' back ways open into the service passages through cells of their own (8 deep).
    base("service_guard_n", 8, ENTRY_GUARD_BACKDOOR[0], 16, ENTRY_GUARD_BACKDOOR[1], ceil=76)
    base("service_guard_s", 8, -ENTRY_GUARD_BACKDOOR[1], 16, -ENTRY_GUARD_BACKDOOR[0], ceil=76)
    door("door_hall_w", 112, -64, 160, 64)

    # The main pump hall: 1024 x 896, 320 high. A sunken pit in its middle (steps down on the west and
    # the east), four pumps in the pit, pipe columns at the pit's corners.
    base("hall", 160, -448, 1184, 448, **hall)
    base("pit_step_w1", 352, -256, 376, 256, **{**pit, "floor": -16})
    base("pit_step_w2", 376, -256, 400, 256, **{**pit, "floor": -32})
    base("pit", 400, -256, 944, 256, **{**pit, "floor": -48})
    base("pit_step_e2", 944, -256, 968, 256, **{**pit, "floor": -32})
    base("pit_step_e1", 968, -256, 992, 256, **{**pit, "floor": -16})
    base("pump_1", 448, 96, 576, 208, **{**machine, "floor": 144})
    base("pump_2", 768, 96, 896, 208, **{**machine, "floor": 144})
    base("pump_3", 448, -208, 576, -96, **{**machine, "floor": 144})
    base("pump_4", 752, -224, 912, -96, **{**machine, "floor": 176, "side": "PIPE4"})
    for x, y in ((304, 272), (1008, 272), (304, -304), (1008, -304)):
        void(x, y, x + 32, y + 32)
    # Catwalks (144 up since note #126): a ring round the walls (96 wide) and a cross over the pit.
    catwalk(160, 352, 1184, 448)
    catwalk(160, -448, 1184, -352)
    catwalk(160, -448, 256, 448)
    catwalk(1088, -448, 1184, 448)
    catwalk(624, -448, 720, 448)
    catwalk(160, -48, 1184, 48)

    # Note #127 (2026-11-26): west off the north corridor's end, a short hall and a door into a box room; a back
    # tunnel leaves the box room's north wall (station(): STATION_BACK_TUNNEL) for the storage room's box wall.
    # Note #137: an ordinary door (72 high, the tech door's CACODOOR) and a hall of ordinary height (96) to it, not
    # the station's big 128.
    base("back_hall", -64, 528, 16, 592, ceil=76)   # note #144: down to the door's height (72, plus the 4 a door stops short): a side route
    door("door_boxes", -112, 528, -64, 592, high=72, tex=TECH_DOOR_TEXTURE)
    base("boxes", -496, 368, -112, 752, **{**store, "light": 144})
    base("boxes_exit", STATION_BACK_TUNNEL[0], 752, STATION_BACK_TUNNEL[1], 760, **{**store, "light": 144})   # the tunnel's mouth: its own cell, so the wall is cut there
    for k, (x0, y0, x1, y1, hgt, tex) in enumerate(STATION_BOXES):
        base(f"boxes_crate_{k + 1}", x0, y0, x1, y1, **{**store, "light": 144, "floor": hgt, "side": tex,
                                                        "floor_tex": "CRATOP1" if hgt > 64 else "CRATOP2", "scenery": True})

    # North: a corridor behind the hall's north wall, a door into the hall, the control room off it, and
    # at its east end a back stairway up to the catwalk's north-east corner.
    base("corridor_n", 16, 496, 896, 624)
    door("door_hall_n", 400, 448, 528, 496)
    n, rise, deep = STATION_STAIR_STEPS, STATION_STAIR_RISE, STATION_STAIR_DEEP
    top = STATION_CATWALK[1]
    for k in range(n):
        base(f"stair_n_{k + 1}", 896 + deep * k, 496, 896 + deep * (k + 1), 624, floor=rise * (k + 1), above=True)
    base("landing_n", 1088, 496, 1184, 624, floor=top, above=True)
    base("landing_n_door", 1104, 448, 1168, 496, floor=top, ceil=112, above=True, wall=STATION_FRAME, side=STATION_FRAME)
    base("nook_n1", 608, 624, 672, 672, ceil=96)
    base("nook_n2", 752, 624, 848, 656, ceil=96)
    base("control", 160, 672, 544, 928, **comp)
    door("door_control", 288, 624, 416, 672)
    base("control_console", 224, 832, 480, 880, **{**comp, "floor": 48, "side": "COMPSTA1", "floor_tex": "FLAT23", "scenery": True})
    void(496, 704, 528, 800)                                   # a bank of machines standing in the room

    # South: a low pipe gallery behind the hall's south wall with nooks off it, a door into the hall, and
    # at its west end the other back stairway, up to the catwalk's south-west corner.
    base("tunnel", 448, -624, 1360, -496, **pipes)
    door("door_hall_s", 800, -496, 928, -448)
    for k in range(n):
        base(f"stair_s_{k + 1}", 448 - deep * (k + 1), -624, 448 - deep * k, -496, **{**pipes, "floor": rise * (k + 1), "ceil": 128, "above": True})
    base("landing_s", 160, -624, 256, -496, **{**pipes, "floor": top, "ceil": 128, "above": True})
    base("landing_s_door", 176, -496, 240, -448, floor=top, ceil=112, above=True, wall=STATION_FRAME, side=STATION_FRAME)
    base("nook_s1", 560, -672, 624, -624, **{**pipes, "ceil": 72})
    base("nook_s2", 704, -688, 800, -624, **{**pipes, "ceil": 72})
    base("nook_s3", 1040, -672, 1104, -624, **{**pipes, "ceil": 72})

    # East: the generator room (two turbines, a nook), a door from the hall, and a link down to the gallery.
    base("generator", 1232, -320, 1616, 320, **gen)
    door("door_hall_e", 1184, -64, 1232, 64)
    base("turbine_1", 1328, 96, 1520, 224, **{**gen, "floor": 112, "side": "COMPSTA2", "floor_tex": "CEIL5_1", "scenery": True})
    base("turbine_2", 1328, -224, 1456, -64, **{**gen, "floor": 112, "side": "COMPSTA2", "floor_tex": "CEIL5_1", "scenery": True})
    base("gen_link", 1264, -496, 1360, -320)
    base("nook_g1", 1616, -32, 1664, 64, **{**gen, "ceil": 96})

    # South-west: a storage room at the end of the south service passage, crates in it.
    base("storage", -176, -656, 112, -432, **store)
    base("storage_crate_1", -144, -624, -80, -560, **{**store, "floor": 64, "side": "CRATE1", "floor_tex": "CRATOP2", "scenery": True})
    base("storage_crate_2", -80, -624, -16, -560, **{**store, "floor": 96, "side": "CRATE2", "floor_tex": "CRATOP1", "scenery": True})
    base("storage_crate_3", -48, -496, 16, -432, **{**store, "floor": 64, "side": "CRATE3", "floor_tex": "CRATOP2", "scenery": True})
    # Note #131 (2026-11-26): a frame where the service passage opens into the storage room, so the walls don't change
    # texture in a bare corner: the track's metal (STATION_FRAME), 16 deep, posts 8 wide, a lintel at 112.
    base("storage_frame", 16, -448, 112, -432, ceil=112, wall=STATION_FRAME, side=STATION_FRAME)
    void(16, -448, 24, -432)
    void(104, -448, 112, -432)
    return Z


def raster(m: MapBuilder, prefix: str, origin, z0: int, zones: list[dict], links=()) -> dict:
    """Sectors and lines from a plan of rectangles (zones, in order: "base" sets a cell, "over" changes the
    cell under it and adds "suffix" to its key, "void" empties it; coordinates from `origin`, heights from
    z0). Cells with the same key that touch are one sector. Between two sectors: a passable line, each
    side showing the other's "side" texture where it stands higher or hangs lower; against nothing: a
    wall in the cell's "wall" texture. A "door" cell's faces get Door_Raise (its tag), the other sector in
    front. links: ((x0, y0, x1, y1), sector): a stretch of the outline that opens onto a sector built
    elsewhere. Returns the sectors by name."""
    ox, oy = origin
    xs = sorted({v for z in zones for v in (z["box"][0], z["box"][2])})
    ys = sorted({v for z in zones for v in (z["box"][1], z["box"][3])})
    nx, ny = len(xs) - 1, len(ys) - 1
    cell = [[None] * ny for _ in range(nx)]
    for z in zones:
        x0, y0, x1, y1 = z["box"]
        for i in range(xs.index(x0), xs.index(x1)):
            for j in range(ys.index(y0), ys.index(y1)):
                if z.get("void"):
                    cell[i][j] = None
                elif "base" in z:
                    cell[i][j] = dict(z["base"])
                elif cell[i][j] is not None:
                    key = cell[i][j]["key"]                    # (two overlapping "over" zones add the suffix once)
                    cell[i][j] = {**cell[i][j], **z["over"], "key": key if key.endswith(z["suffix"]) else key + z["suffix"]}
    # Sectors: touching cells with the same key.
    owner = [[None] * ny for _ in range(nx)]
    sectors, attrs, count = {}, {}, {}
    for i in range(nx):
        for j in range(ny):
            if cell[i][j] is None or owner[i][j] is not None:
                continue
            a = cell[i][j]
            count[a["key"]] = count.get(a["key"], 0) + 1
            name = f"{prefix}.{a['key']}" + (f"_{count[a['key']]}" if count[a["key"]] > 1 else "")
            s = m.sector(name, floor=z0 + a["floor"], ceiling=z0 + a["ceil"], light=a["light"],
                         floor_tex=a["floor_tex"], ceiling_tex=a["ceil_tex"])
            if a.get("tag") or a.get("door"):
                m.sectors[s.index]["id"] = a.get("door") or a["tag"]
            if a.get("scenery"):
                m.sectors[s.index]["user_scenery"] = True
            sectors[name], attrs[s.index] = s, a
            todo = [(i, j)]
            owner[i][j] = s
            while todo:
                ci, cj = todo.pop()
                for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ni, nj = ci + di, cj + dj
                    if 0 <= ni < nx and 0 <= nj < ny and owner[ni][nj] is None and cell[ni][nj] is not None \
                            and cell[ni][nj]["key"] == a["key"]:
                        owner[ni][nj] = s
                        todo.append((ni, nj))
    at = lambda i, j: owner[i][j] if 0 <= i < nx and 0 <= j < ny else None
    pair = lambda a, b: None if a is b else (a.index if a else None, b.index if b else None)
    # The elementary edges that are lines: vert[i][j] at xs[i] from ys[j] up (west, east), horiz[i][j] at
    # ys[j] from xs[i] east (south, north).
    vert = {(i, j): (at(i - 1, j), at(i, j)) for i in range(nx + 1) for j in range(ny) if pair(at(i - 1, j), at(i, j))}
    horiz = {(i, j): (at(i, j - 1), at(i, j)) for i in range(nx) for j in range(ny + 1) if pair(at(i, j - 1), at(i, j))}
    world = lambda x, y: (ox + x, oy + y)

    def link_for(x0, y0, x1, y1):
        for (lx0, ly0, lx1, ly1), sec in links:
            if lx0 <= min(x0, x1) and max(x0, x1) <= lx1 and ly0 <= min(y0, y1) and max(y0, y1) <= ly1:
                return sec
        return None

    def line(p, q, first, second, tagname):
        """The line between `first` (west or south of it) and `second`, along p -> q (north or east)."""
        gid = f"{prefix}.{tagname}.{p[0]}_{p[1]}"
        if first is None or second is None:
            sec = first or second
            a, b = (q, p) if first is not None else (p, q)     # the sector on the right
            if p[0] != q[0]:                                   # horizontal lines turn the other way
                a, b = b, a
            other = link_for(*p, *q)
            if other is not None:
                m.two_sided(world(*a), world(*b), sec, other, gid, texture=attrs[sec.index].get("side", attrs[sec.index]["wall"]))
                return
            ln = m.wall(world(*a), world(*b), sec, gid, texture=attrs[sec.index]["wall"])
            if attrs[sec.index].get("door"):
                m.linedefs[ln]["dontpegbottom"] = True         # the track stays put as the door rises
            return
        fa, sa = attrs[first.index], attrs[second.index]
        front, back = (second, first) if fa.get("door") else (first, second)
        a, b = (q, p) if front is first else (p, q)
        if p[0] != q[0]:
            a, b = b, a
        ln = m.two_sided(world(*a), world(*b), front, back, gid)
        fa, ba = attrs[front.index], attrs[back.index]
        f, k = m.sidedefs[m.linedefs[ln]["sidefront"]], m.sidedefs[m.linedefs[ln]["sideback"]]
        f.fields.update(texturetop=ba.get("side", ba["wall"]), texturebottom=ba.get("side", ba["wall"]))
        k.fields.update(texturetop=fa.get("side", fa["wall"]), texturebottom=fa.get("side", fa["wall"]))
        door = ba.get("door")
        if door:
            m.linedefs[ln].fields.update(special=12, arg0=door, arg1=16, arg2=150, playeruse=True, monsteruse=True,
                                         repeatspecial=True)

    # Runs of edges between the same two sectors are one line, broken wherever a crossing line ends.
    for i in range(nx + 1):
        j = 0
        while j < ny:
            if (i, j) not in vert:
                j += 1
                continue
            start, who = j, pair(*vert[(i, j)])
            j += 1
            while j < ny and (i, j) in vert and pair(*vert[(i, j)]) == who \
                    and (i - 1, j) not in horiz and (i, j) not in horiz:
                j += 1
            line((xs[i], ys[start]), (xs[i], ys[j]), *vert[(i, start)], "v")
    for j in range(ny + 1):
        i = 0
        while i < nx:
            if (i, j) not in horiz:
                i += 1
                continue
            start, who = i, pair(*horiz[(i, j)])
            i += 1
            while i < nx and (i, j) in horiz and pair(*horiz[(i, j)]) == who \
                    and (i, j - 1) not in vert and (i, j) not in vert:
                i += 1
            line((xs[start], ys[j]), (xs[i], ys[j]), *horiz[(start, j)], "h")
    return sectors


# Note #115 (2026-11-26): the way from the tech room into the station, in the end wall's frame (u along it from its
# middle, C3 to C2; d into the link): an arch (columns between ENTRY_ARCH's u, each ENTRY_ARCH_TOPS high, 8 deep),
# a window slit either side (u ENTRY_SLIT, ENTRY_SLIT_Z above the floor: a zombie fires through at about 36), and
# behind each slit a guard post (u ENTRY_GUARD_U) with a zombie.
STATION_ENTRY_DEEPER = 64
# Note #125: wider (128, the link's full width; it was 64) and taller, and the slits horizontal: 40 wide, 16 high
# at eye height (the guards' shots, at about 36, pass), the guard posts moved out beside the wider passage.
ENTRY_ARCH = (-64, -56, -48, 48, 56, 64)
ENTRY_ARCH_TOPS = (88, 104, 112, 104, 88)
ENTRY_SLIT, ENTRY_SLIT_Z = (84, 124), (28, 44)
ENTRY_GUARD_U, ENTRY_GUARD_LIGHT = (72, 136), 112
ENTRY_GUARD_DOOR_TAG = 13      # note #129: the guard posts' doors, tags 13 and 14
ENTRY_GUARD_BACKDOOR = (80, 128)   # note #140: the door in each post's back wall, |u| (48 wide, 72 high)
ZOMBIE = 3004


def station(m: MapBuilder, hall, C3, C2, floor: int) -> None:
    """Note #92: the pumping station past the tech room, through the middle of its end wall C3 -> C2 (the
    room on that wall's right). The station's grid is square to the map; the tech room is turned a few
    degrees, so a short link joins the two: from an opening 128 wide in the end wall to the grid's edge."""
    import math
    length = math.hypot(C2[0] - C3[0], C2[1] - C3[1])
    ux, uy = (C2[0] - C3[0]) / length, (C2[1] - C3[1]) / length
    mid = ((C3[0] + C2[0]) / 2, (C3[1] + C2[1]) / 2)
    # Note #115 (2026-11-26): the way through is an arch now, 64 wide with a stepped top, and either side of it a
    # window slit in the end wall onto a guard post behind, a zombie in each. The link is 64 longer for them (the
    # station moves east with it).
    ox = (max(C3[0], C2[0]) + 48 + STATION_ENTRY_DEEPER + 15) // 16 * 16
    origin = (ox, round(mid[1]))
    ne, se = (origin[0], origin[1] + 64), (origin[0], origin[1] - 64)
    nx, ny = -uy, ux                                          # out of the room, into the link
    P = lambda u, d: (round(mid[0] + ux * u + nx * d, 2), round(mid[1] + uy * u + ny * d, 2))
    dfar = min((q[0] - mid[0]) * nx + (q[1] - mid[1]) * ny for q in (ne, se))
    dw = math.floor(dfar) - 16                                # where the passage widens to meet the station
    # Note #130 (2026-11-26): the light eases from the tech room's (128) to the station's (176): the arch a third of the
    # way, the passage behind it two thirds.
    ease = lambda k: TECH_HALL_LIGHT + (STATION_LIGHT - TECH_HALL_LIGHT) * k // 3
    link = m.sector("station.entry_link", floor=floor, ceiling=floor + 128, light=ease(2),
                    floor_tex="FLAT5_4", ceiling_tex="CEIL3_5")
    metal = lambda ln: [m.sidedefs[m.linedefs[ln][sd]].fields.update(texturetop=CLOSET_SKIN, texturebottom=CLOSET_SKIN)
                        for sd in ("sidefront", "sideback")]
    # The end wall, the room on its right, with the two slits and the arch in it.
    (s0, s1), arch_u = ENTRY_SLIT, ENTRY_ARCH
    m.wall(C3, P(-s1, 0), hall, "tech_hall.wall_end_n")
    m.wall(P(-s0, 0), P(arch_u[0], 0), hall, "tech_hall.wall_end_n2")
    m.wall(P(arch_u[-1], 0), P(s0, 0), hall, "tech_hall.wall_end_s2")
    m.wall(P(s1, 0), C2, hall, "tech_hall.wall_end_s")
    g0, g1 = ENTRY_GUARD_U
    # Note #129 (2026-11-26): a door into each guard post, which monsters open too, so the zombies can come after the
    # player. Note #140: an ordinary door (72 high) at the post's back, from the station's service passage behind it
    # by a short connector (not from the passage under the arch, as #129 had it): ENTRY_GUARD_BACKDOOR (|u|).
    doors = {}
    ba, bb = ENTRY_GUARD_BACKDOOR
    for k, (name, sign) in enumerate((("n", -1), ("s", 1))):
        Ga, Gb = P(sign * bb, dw - 8), P(sign * ba, dw - 8)              # on the post's back wall
        Da, Db = P(sign * bb, dw + 8), P(sign * ba, dw + 8)              # the door's other face
        Qa, Qb = (origin[0] + 8, origin[1] - sign * bb), (origin[0] + 8, origin[1] - sign * ba)   # the raster's cell
        gate = m.sector(f"station.guard_{name}.door", floor=floor, ceiling=floor, light=ENTRY_GUARD_LIGHT,
                        floor_tex="FLAT5_4", ceiling_tex="CEIL5_1")
        m.sectors[gate.index]["id"] = ENTRY_GUARD_DOOR_TAG + k
        conn = m.sector(f"station.guard_{name}.way", floor=floor, ceiling=floor + 76, light=ENTRY_GUARD_LIGHT,
                        floor_tex="FLAT5_4", ceiling_tex="CEIL5_1")
        doors[name] = (gate, conn, Ga, Gb, Da, Db, Qa, Qb, ENTRY_GUARD_DOOR_TAG + k)
    def door_line(ln, tag):
        ld = m.linedefs[ln]
        ld.fields.update(special=12, arg0=tag, arg1=16, arg2=150, playeruse=True, monsteruse=True, repeatspecial=True)
        for sd in ("sidefront", "sideback"):
            m.sidedefs[ld[sd]].fields.update(texturetop=TECH_DOOR_TEXTURE, texturebottom=TECH_DOOR_TEXTURE)
    for name, (gate, conn, Ga, Gb, Da, Db, Qa, Qb, tag) in doors.items():
        for ln in _edges(m, gate, [(Ga, Gb, "skip", ""), (Gb, Db, None, f"station.guard_{name}.door.end_b"),
                                   (Db, Da, conn, f"station.guard_{name}.door.back"), (Da, Ga, None, f"station.guard_{name}.door.end_a")]):
            ld = m.linedefs[ln]
            if "sideback" in ld.fields:
                door_line(ln, tag)
            else:
                m.sidedefs[ld["sidefront"]]["texturemiddle"] = "DOORTRAK"
                ld["dontpegbottom"] = True
        for ln in _edges(m, conn, [(Da, Db, "skip", ""), (Db, Qb, None, f"station.guard_{name}.way.side_b"),
                                   (Qb, Qa, "skip", ""), (Qa, Da, None, f"station.guard_{name}.way.side_a")]):
            m.sidedefs[m.linedefs[ln]["sidefront"]]["texturemiddle"] = "STARG3"
    for name, sign in (("n", -1), ("s", 1)):
        guard = m.sector(f"station.guard_{name}", floor=floor, ceiling=floor + 96, light=ENTRY_GUARD_LIGHT,
                         floor_tex="FLAT5_4", ceiling_tex="CEIL5_1")
        # (Note #129: no longer scenery: a door opens into it.)
        slit = m.sector(f"station.slit_{name}", floor=floor + ENTRY_SLIT_Z[0], ceiling=floor + ENTRY_SLIT_Z[1],
                        light=ENTRY_GUARD_LIGHT, floor_tex="CEIL5_1", ceiling_tex="CEIL5_1")
        m.sectors[slit.index]["user_scenery"] = True
        a, b = sorted((sign * s0, sign * s1))
        for ln in _edges(m, slit, [(P(a, 0), P(b, 0), hall, f"station.slit_{name}.front"), (P(b, 0), P(b, 8), None, f"station.slit_{name}.side_b"),
                                   (P(b, 8), P(a, 8), guard, f"station.slit_{name}.back"), (P(a, 8), P(a, 0), None, f"station.slit_{name}.side_a")]):
            ld = m.linedefs[ln]
            if "sideback" in ld.fields:
                metal(ln)
            else:
                m.sidedefs[ld["sidefront"]]["texturemiddle"] = CLOSET_SKIN
        lo, hi = sorted((sign * g0, sign * g1))
        sa, sb = sorted((sign * s0, sign * s1))
        gate, conn, Ga, Gb, Da, Db, Qa, Qb, tag = doors[name]
        # The back wall runs from P(hi, dw - 8) to P(lo, dw - 8): the door's two ends in it, in that order.
        back_pts = sorted((Ga, Gb), key=lambda q: math.dist(q, P(hi, dw - 8)))
        ring = [P(lo, 8), P(sa, 8), P(sb, 8), P(hi, 8), P(hi, dw - 8)] + back_pts + [P(lo, dw - 8)]
        outline = []
        for i, (q0, q1) in enumerate(zip(ring, ring[1:] + ring[:1])):
            kind = "skip" if (q0, q1) == (P(sa, 8), P(sb, 8)) else gate if {q0, q1} == {Ga, Gb} else None
            outline.append((q0, q1, kind, f"station.guard_{name}.wall_{i + 1}"))
        for ln in _edges(m, guard, outline):
            ld = m.linedefs[ln]
            if "sideback" in ld.fields:
                door_line(ln, tag)
            else:
                m.sidedefs[ld["sidefront"]]["texturemiddle"] = "STARG3"
        out = round(math.degrees(math.atan2(-ny, -nx))) % 360           # facing the room, through the slit
        m.thing(ZOMBIE, *P(sign * (s0 + s1) / 2, 40), f"station.guard_{name}.zombie", angle=out)
    # The arch: columns 8 deep across the way through, each its own ceiling, so the top steps up to the middle.
    cols = []
    for k, (u0, u1, top) in enumerate(zip(arch_u, arch_u[1:], ENTRY_ARCH_TOPS)):
        col = m.sector(f"station.arch_{k + 1}", floor=floor, ceiling=floor + top, light=ease(1),
                       floor_tex="FLAT5_4", ceiling_tex="CEIL5_1")
        if top < ENTRY_ARCH_TOPS[len(ENTRY_ARCH_TOPS) // 2]:
            # The shoulders, 8 wide each: the movement check takes them for gaps too narrow to pass (it reads the
            # arch as 32 wide; it is 64 under 72 or more), like the top switch's cheeks.
            m.sectors[col.index]["user_scenery"] = True
        cols.append((col, u0, u1))
    for k, (col, u0, u1) in enumerate(cols):
        right = cols[k + 1][0] if k + 1 < len(cols) else None
        made = _edges(m, col, [(P(u0, 0), P(u1, 0), hall, f"station.arch_{k + 1}.front"),
                               (P(u1, 0), P(u1, 8), right, f"station.arch_{k + 1}.side_b"),
                               (P(u1, 8), P(u0, 8), link, f"station.arch_{k + 1}.back"),
                               (P(u0, 8), P(u0, 0), "skip" if k else None, f"station.arch_{k + 1}.side_a")])
        for ln in made:
            ld = m.linedefs[ln]
            if "sideback" in ld.fields:
                metal(ln)
            else:
                m.sidedefs[ld["sidefront"]]["texturemiddle"] = CLOSET_SKIN
    # The passage behind the arch, the station's 128 wide all the way (note #125).
    a0, a1 = arch_u[0], arch_u[-1]
    for ln in _edges(m, link, [(P(a0, 8), P(a1, 8), "skip", ""), (P(a1, 8), se, None, "station.entry_link.wall_s"),
                               (se, ne, "skip", ""), (ne, P(a0, 8), None, "station.entry_link.wall_n")]):
        m.sidedefs[m.linedefs[ln]["sidefront"]]["texturemiddle"] = "STARG3"
    # Note #127: the back tunnel, built before the raster so the box room's north wall opens onto it: north from
    # the box room, three steps up to the storage room's level, then west above everything, then down to the
    # chamber behind the box wall (BACKWAY, built by storage_chamber).
    tx0, tx1 = STATION_BACK_TUNNEL
    S1, S2 = (origin[0] + tx0, origin[1] + 760), (origin[0] + tx1, origin[1] + 760)
    hw = BACK_TUNNEL_WIDE // 2
    yl, yh = BACK_TUNNEL_Y - hw, BACK_TUNNEL_Y + hw
    top_floor = BACKWAY["floor"]
    rise = top_floor - floor
    # Note #141 (2026-11-26): the steps were 24 deep under a 72 ceiling: the player, 32 across, stood on two at once
    # and the lower one's ceiling was too low over the higher's floor. The way north and the corner stay level now;
    # the rise comes in the long stretch, in BACK_TUNNEL_STEPS steps each BACK_TUNNEL_STEP_LONG long.
    pieces = [("back_tunnel", floor, [S1, S2, (S2[0], yl), (S1[0], yl)])]
    pieces.append(("back_tunnel.corner", floor, [(S1[0], yl), (S2[0], yl), (S2[0], yh), (S1[0], yh)]))
    # Note #146: long steps instead, one between each pair of candles: a candle, halfway to the next a step up,
    # the next candle, and so on, evenly up the long stretch until the storage room's level, past the last candle.
    e0, e1 = BACKWAY["edge"]
    west = (BACK_TUNNEL_X - hw, BACK_TUNNEL_X + hw)
    nw, nd = BACK_TUNNEL_NICHE
    niches = list(range(round(west[0]) + 200, round(S1[0]) - 120, BACK_TUNNEL_CANDLES))
    notch = lambda lo, hi: [q for c in niches if lo < c < hi
                            for q in ((c - nw // 2, yh), (c - nw // 2, yh + nd), (c + nw // 2, yh + nd), (c + nw // 2, yh))]
    mids = sorted(((a + b) // 2 for a, b in zip(niches, niches[1:])), reverse=True)    # the steps, east to west
    xs = [S1[0]] + mids
    for k, (xe, xw) in enumerate(zip(xs, xs[1:])):
        pieces.append((f"back_tunnel.step_{k + 1}", floor + round(rise * k / len(mids)),
                       [(xe, yh), (xe, yl), (xw, yl), (xw, yh)] + notch(xw, xe)))
    pieces.append(("back_tunnel.long", top_floor, [(xs[-1], yh), (xs[-1], yl), (west[1], yl), e1, e0, (west[0], yh)]
                   + notch(west[0], xs[-1])))
    secs, sides = [], {}
    for k, (name, f, pts) in enumerate(pieces):
        sec = m.sector(f"station.{name}", floor=f, ceiling=f + BACK_TUNNEL_HIGH, light=96, floor_tex=BACK_TUNNEL_FLOOR,
                       ceiling_tex=BACK_TUNNEL_CEIL)
        secs.append((sec, list(zip(pts, pts[1:] + pts[:1]))))
        for a, b in secs[-1][1]:
            sides.setdefault(frozenset((a, b)), []).append(k)
    tunnel = secs[0][0]
    for k, (sec, edges) in enumerate(secs):
        outline = []
        for j, (a, b) in enumerate(edges):
            other = [i for i in sides[frozenset((a, b))] if i != k]
            if frozenset((a, b)) == frozenset((S1, S2)):
                kind = "skip"                                       # the box room's (the raster's link)
            elif frozenset((a, b)) == frozenset((e0, e1)):
                kind = BACKWAY["sector"]
            else:
                kind = "skip" if other and other[0] > k else secs[other[0]][0] if other else None
            outline.append((a, b, kind, f"station.{pieces[k][0]}.side_{j + 1}"))
        for ln in _edges(m, sec, outline):
            ld = m.linedefs[ln]
            for sd in ("sidefront", "sideback"):
                if sd in ld.fields:
                    side = m.sidedefs[ld[sd]]
                    for key in ("texturetop", "texturemiddle", "texturebottom"):
                        if side.get(key, "-") != "-":
                            side[key] = "BROWN96"
            if "sideback" not in ld.fields:
                m.sidedefs[ld["sidefront"]]["texturemiddle"] = "BROWN96"
    for k, (type_, gx, gy) in enumerate(STATION_BOX_GUARDS):           # note #145
        m.thing(type_, origin[0] + gx, origin[1] + gy, f"station.boxes.guard_{k + 1}", angle=0)
    for k, c in enumerate(niches):                                  # note #136: a candle in each niche
        m.thing(34, c, yh + nd // 2, f"station.back_tunnel.candle_{k + 1}")
    raster(m, "station", origin, floor, station_zones(),
           links=(((0, -64, 0, 64), link), ((tx0, 760, tx1, 760), tunnel))
           + tuple(((8, min(doors[n][6][1], doors[n][7][1]) - origin[1], 8, max(doors[n][6][1], doors[n][7][1]) - origin[1]), doors[n][1])
                   for n in ("n", "s")))
    # The catwalks: one 3D floor over every sector tagged for it; its control sector stands outside the map.
    lo, hi = STATION_CATWALK
    cx, cy = origin[0] + 700, origin[1] - 900
    control = m.room("station_catwalk_control", cx, cy, 32, 32, floor=floor + lo, ceiling=floor + hi,
                     floor_tex="FLAT23", ceiling_tex="FLAT23", light=192)
    m.sectors[control.index]["user_scenery"] = True
    ln = next(i for i, l in enumerate(m.linedefs) if l["user_gid"] == "station_catwalk_control.wall_s")
    m.linedefs[ln].fields.update(special=160, arg0=STATION_CATWALK_TAG, arg1=1, arg2=0, arg3=255)
    m.sidedefs[m.linedefs[ln]["sidefront"]]["texturemiddle"] = "SUPPORT2"

# Note #74 (2026-11-24): the stairs down to the cistern have the passage's torch niches, but their torches
# are out (the unlit torch, DEAD_TORCH_TID), which is why it is dark down here: (stair, side), sides as
# the walls are named (l = east, r = west), alternating like the passage's; the 3rd's east wall is the door.
STAIR_TORCHES = {(1, "l"), (2, "r"), (3, "r"), (4, "l")}


# Note #97 (2026-11-24): a carved alcove like the passage's (the satyr's face in plain stone, a marble shelf)
# in the west wall of the stairs' first flight, two packs of shells on its shelf. A little narrower than
# the passage's (112, not 128: the wall is 134 long).
STAIR_CARVING = (1, "r")
STAIR_CARVING_WIDE = 112
STAIR_CARVING_ITEMS = (SHELLS, SHELLS)


def _stair_carving(m: MapBuilder, s, a, b, gid: str, items=None, texture: str = PASSAGE_TEXTURE) -> None:
    """A wall of the stairs a -> b (the stair on its right) with the carved alcove in its middle
    (PASSAGE_CARVINGS' design: CARVING_SILL up, CARVING_DEEP deep, 128 high, the face in the middle of
    its back wall), the items along its shelf."""
    import math
    dx, dy = b[0] - a[0], b[1] - a[1]
    n = math.hypot(dx, dy)
    ex, ey = dx / n, dy / n
    wide, deep = STAIR_CARVING_WIDE, CARVING_DEEP
    at = lambda along, into=0.0: (round(a[0] + ex * along - ey * into, 2), round(a[1] + ey * along + ex * into, 2))
    lo, hi = n / 2 - wide / 2, n / 2 + wide / 2
    p0, p1, q0, q1 = at(lo), at(hi), at(lo, deep), at(hi, deep)
    fl = (wide - CARVING_WIDE) / 2                         # the plain stone either side of the face
    c0, c1 = at(lo + fl, deep), at(hi - fl, deep)
    piece = m.sectors[s.index].fields
    f = piece["heightfloor"] + CARVING_SILL
    # Note #135: no higher than the passage it is in (the side passage is 112 high: the alcove ran up past its
    # ceiling). The carving hangs from the alcove's top, so it comes down with it, whole.
    alcove = m.sector(f"{gid}.carving", floor=f, ceiling=min(f + 128, piece["heightceiling"]), light=CARVING_LIGHT,
                      floor_tex="FLOOR7_2", ceiling_tex="FLOOR7_2")
    m.sectors[alcove.index].fields.update(user_scenery=True, **{k: piece[k] for k in ("fadecolor", "fogdensity") if k in piece})
    m.wall(a, p0, s, f"{gid}_a", texture=texture)
    m.two_sided(p0, p1, s, alcove, f"{gid}.carving.mouth", texture=texture)
    m.wall(p1, b, s, f"{gid}_b", texture=texture)
    m.wall(p0, q0, alcove, f"{gid}.carving.side_a", texture=CARVING_STONE)
    left = m.wall(q0, c0, alcove, f"{gid}.carving.back_a", texture=CARVING_STONE)
    m.wall(c0, c1, alcove, f"{gid}.carving.back", texture=CARVING_TEXTURE)
    right = m.wall(c1, q1, alcove, f"{gid}.carving.back_b", texture=CARVING_STONE)
    m.wall(q1, p1, alcove, f"{gid}.carving.side_b", texture=CARVING_STONE)
    m.sidedefs[m.linedefs[left]["sidefront"]]["offsetx"] = round(-fl) % 256
    m.sidedefs[m.linedefs[right]["sidefront"]]["offsetx"] = CARVING_WIDE
    things = STAIR_CARVING_ITEMS if items is None else items
    # Along the shelf: two as the passage's (a little off-centre); more, spread evenly across it.
    spots = (-22, 18) if len(things) == 2 else [round(-wide / 2 + 16 + k * (wide - 32) / max(1, len(things) - 1)) for k in range(len(things))]
    for j, (thing, along) in enumerate(zip(things, spots)):
        m.thing(thing, *at(n / 2 + along, 12), f"{gid}.item_{j + 1}", angle=90)


def _stair_wall(m: MapBuilder, s, a, b, gid: str, torch: bool, lit: bool = False, texture: str = PASSAGE_TEXTURE) -> None:
    """A wall of the stairs a -> b (the stair on its right); with `torch`, a niche like the passage's in
    its middle (24 wide, NICHE_DEEP deep, from the floor, NICHE_HIGH high) holding an unlit torch, as dark
    and as foggy as the stair."""
    if not torch:
        m.wall(a, b, s, gid, texture=texture)
        return
    import math
    dx, dy = b[0] - a[0], b[1] - a[1]
    n = math.hypot(dx, dy)
    ex, ey = dx / n, dy / n
    wide, deep, rough = rough_niche(gid)                  # note #79: a rough hollow, each a little different
    ox, oy = -ey * deep, ex * deep                        # left of a -> b: into the rock
    p0 = (round(a[0] + ex * (n / 2 - wide / 2), 2), round(a[1] + ey * (n / 2 - wide / 2), 2))
    p1 = (round(a[0] + ex * (n / 2 + wide / 2), 2), round(a[1] + ey * (n / 2 + wide / 2), 2))
    pts = [p0] + [(round(p0[0] + ex * t2 - ey * s2, 2), round(p0[1] + ey * t2 + ex * s2, 2)) for t2, s2 in rough] + [p1]
    piece = m.sectors[s.index].fields
    f = piece["heightfloor"]
    niche = m.sector(f"{gid}.niche", floor=f, ceiling=f + NICHE_HIGH, light=piece["lightlevel"],
                     floor_tex=texture, ceiling_tex=texture)
    m.sectors[niche.index].fields.update(user_scenery=True, **{k: piece[k] for k in ("fadecolor", "fogdensity") if k in piece})
    m.wall(a, p0, s, f"{gid}_a", texture=texture)
    m.two_sided(p0, p1, s, niche, f"{gid}.niche.mouth", texture=texture)
    m.wall(p1, b, s, f"{gid}_b", texture=texture)
    for n2, (c0, c1) in enumerate(zip(pts, pts[1:])):
        m.wall(c0, c1, niche, f"{gid}.niche.rock_{n2 + 1}", texture=texture)
    k_in = NICHE_TORCH_IN / deep
    ti = m.thing(TORCH, round((p0[0] + p1[0]) / 2 + ox * k_in, 2), round((p0[1] + p1[1]) / 2 + oy * k_in, 2), f"{gid}.torch")
    if lit:                                                # (the side passage's: burning, the niche brighter for it)
        m.sectors[niche.index]["lightlevel"] = piece["lightlevel"] + 64
    else:
        m.things[ti].fields["id"] = DEAD_TORCH_TID


def cistern(m: MapBuilder, drain, west) -> None:
    """Note #77, editor save 22:36: the stairs down from the passage's end (PASSAGE_END) to the cistern, and
    the cistern: `west` is the drain's far side, north to south (the cistern's west wall, shared with
    the drain: water pouring down it); CISTERN_EAST its east side."""
    end = PASSAGE_END
    ne, se = CISTERN_EAST
    nw = west[0]
    top = m.sectors[end["sector"].index]["heightfloor"]
    # Note #73 (2026-11-24): the stairs keep the headroom of the passage's last piece (they had the
    # passage's first, low one: PASSAGE_HIGH), their ceiling stepping down with them.
    high = m.sectors[end["sector"].index]["heightceiling"] - top
    secs = []
    for k in range(CISTERN_STEPS):
        f = top - (top - CISTERN_FLOOR) * (k + 1) // (CISTERN_STEPS + 1)
        s = m.sector(f"cistern_stair_{k + 1}", floor=f, ceiling=f + high, light=PASSAGE_LIGHT - 8 * (k + 1),
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
        # Note #48: the big door is in the east (left) wall now; it was in the west one.
        if k + 1 == CISTERN_DOOR_STAIR:
            cistern_door(m, s, la, lb)
        else:
            _stair_wall(m, s, la, lb, f"cistern_stair_{k + 1}.wall_l", (k + 1, "l") in STAIR_TORCHES)
        if (k + 1, "r") == STAIR_CARVING:
            _stair_carving(m, s, rb, ra, f"cistern_stair_{k + 1}.wall_r")
        else:
            _stair_wall(m, s, rb, ra, f"cistern_stair_{k + 1}.wall_r", (k + 1, "r") in STAIR_TORCHES)
    for k, (x, y) in CISTERN_SPECTRES.items():
        sp = m.thing(SPECTRE, x, y, f"cistern.spectre_{k}", angle=90)
        m.things[sp].fields.update(ambush=True, id=SLEEPER_TID)
    y, n = ne[1] - 110, 0
    glows = []                                             # where each meets the east wall (note #76: a torch niche there)
    while y > se[1] + 60:                                  # note #7: the lights along the east wall
        wx = ne[0] + (se[0] - ne[0]) * (ne[1] - y) / (ne[1] - se[1])
        glows.append((wx, y))
        (r, g, bl), rad = CISTERN_GLOWS[n % len(CISTERN_GLOWS)]
        # Note #83 (2026-11-24): one light straight in front of an outcrop (note #78) left the outcrop's flanks
        # black: they face along the wall, away from it. Two smaller lights now, one either side of the
        # outcrop (CISTERN_GLOW_SIDE along the wall, CISTERN_GLOW_OUT from it), each on its own flank,
        # both on the face and the hollow; a little dimmer each, so the pair is about as bright as the one.
        for name, side in (("", 1), ("b", -1)):
            t = m.thing(9830, round(wx - CISTERN_GLOW_OUT), round(y + side * CISTERN_GLOW_SIDE), f"cistern.glow_{n + 1}{name}")
            m.things[t].fields.update(height=40, arg0=round(r * 0.75), arg1=round(g * 0.75), arg2=round(bl * 0.75),
                                      arg3=rad - 16)
        y, n = y - CISTERN_GLOW_GAP, n + 1
    # The cistern: east and south walls as drawn, the west wall the drain's far side.
    # Note #18: the east wall stands on a low slot (CISTERN_OUT) the water runs out through, into a dark
    # channel behind it.
    oh, od = CISTERN_OUT
    out = m.sector("cistern.out", floor=CISTERN_FLOOR, ceiling=CISTERN_FLOOR + oh, light=24, floor_tex=GUTTER_FLAT,
                   ceiling_tex=PASSAGE_TEXTURE)
    m.sectors[out.index].fields.update(fadecolor=CISTERN_DARK_FOG[0], fogdensity=CISTERN_DARK_FOG[1], user_scenery=True)
    # Note #76 (2026-11-24): an unlit torch at each of the east wall's glows. Note #78: not set into the wall
    # above the slot (that broke the vine grate with a pier under each), but in an outcrop: the wall pulled
    # forward into the cistern as a buttress (CISTERN_OUTCROP wide and deep, solid, floor to ceiling, down
    # into the water), a hollow in its face for the torch (24 wide, NICHE_DEEP deep, NICHE_HIGH high, its
    # shelf CISTERN_TORCH_SILL above the water: one step). The slot and its vines run on behind, level with
    # the back wall. So the wall is built in pieces, ne -> se, their textures carried on by x offsets.
    import math
    length = math.hypot(se[0] - ne[0], se[1] - ne[1])
    ex, ey = (se[0] - ne[0]) / length, (se[1] - ne[1]) / length
    ix, iy = -ey, ex                                       # left of ne -> se: east, into the wall
    along = lambda d, into=0.0: (round(ne[0] + ex * d + ix * into, 2), round(ne[1] + ey * d + iy * into, 2))
    ow, od2 = CISTERN_OUTCROP

    def east_piece(a, b, d, gid):
        line = m.two_sided(a, b, cis, out, gid, texture=PASSAGE_TEXTURE)
        m.linedefs[line].fields.update(blocking=True, dontpegtop=True)
        m.sidedefs[m.linedefs[line]["sidefront"]]["offsetx"] = round(d)
        # Note #23 (2026-11-23): the same hanging vines as the hall's drains (DRAIN_GRATE), on both sides.
        for sd in ("sidefront", "sideback"):
            m.sidedefs[m.linedefs[line][sd]]["texturemiddle"] = DRAIN_GRATE

    prev, prev_d = ne, 0.0
    for k, (gx, gy) in enumerate(glows):
        d = math.hypot(gx - ne[0], gy - ne[1])
        gid = f"cistern.torch_{k + 1}"
        # Note #79: no two alike, and no square corners: the hollow a rough one (rough_niche), the outcrop
        # as deep as its hollow needs plus a little, its two flanks each a different width, out from the
        # wall on a slant with a knee in it.
        import hashlib
        import random
        rnd = random.Random(int(hashlib.md5((gid + ".outcrop").encode()).hexdigest()[:8], 16))
        wide, deep, rough = rough_niche(gid, undercut=False)
        od3 = deep + rnd.choice((6, 8, 10, 12))
        hn, hs = wide / 2 + rnd.uniform(14, 24), wide / 2 + rnd.uniform(14, 24)      # half widths at the wall
        a0, a1 = along(d - hn), along(d + hs)
        kn = along(d - hn + rnd.uniform(3, 8), -od3 * rnd.uniform(0.45, 0.7))        # the flanks' knees
        ks = along(d + hs - rnd.uniform(3, 8), -od3 * rnd.uniform(0.45, 0.7))
        n0, n1 = along(d - wide / 2, -od3), along(d + wide / 2, -od3)
        east_piece(prev, a0, prev_d, "cistern.wall_e" if k == 0 else f"cistern.wall_e_{k + 1}")
        # Note #85 (2026-11-25): seen through the vines, the outcrop was a flat wall on the channel's side.
        # Its back bulges into the channel too (not as far: the water must get past), rough like the front:
        # flanks slanting out with a knee, a back of its own width. Drawn after the front's numbers, so the
        # cistern side keeps its shape.
        bd = od3 * rnd.uniform(0.5, 0.75)
        bw = wide / 2 + rnd.uniform(-4, 6)
        back = [a1, along(d + hs - rnd.uniform(4, 10), bd * rnd.uniform(0.45, 0.65)),
                along(d + bw, bd), along(d + rnd.uniform(-6, 6), bd + rnd.uniform(2, 6)), along(d - bw, bd),
                along(d - hn + rnd.uniform(4, 10), bd * rnd.uniform(0.45, 0.65)), a0]
        for n2, (c0, c1) in enumerate(zip(back, back[1:])):                 # the channel's wall round the outcrop
            m.wall(c0, c1, out, f"{gid}.behind_{n2 + 1}", texture=PASSAGE_TEXTURE)
        sill = CISTERN_FLOOR + CISTERN_TORCH_SILL
        niche = m.sector(gid, floor=sill, ceiling=sill + NICHE_HIGH, light=CISTERN_DARK_LIGHT,
                         floor_tex=PASSAGE_TEXTURE, ceiling_tex=PASSAGE_TEXTURE)
        m.sectors[niche.index].fields.update(fadecolor=CISTERN_DARK_FOG[0], fogdensity=CISTERN_DARK_FOG[1], user_scenery=True)
        # The outcrop, the cistern on the right of each line: out from the wall, to the hollow's mouth, and
        # back to the wall.
        for a, b, name in ((a0, kn, "side_n"), (kn, n0, "face_n"), (n1, ks, "face_s"), (ks, a1, "side_s")):
            m.wall(a, b, cis, f"{gid}.{name}", texture=PASSAGE_TEXTURE)
        mouth = m.two_sided(n0, n1, cis, niche, f"{gid}.mouth", texture=PASSAGE_TEXTURE)
        m.linedefs[mouth].fields.update(blocking=True, dontpegtop=True)
        pts = [n0] + [along(d - wide / 2 + t2, -od3 + s2) for t2, s2 in rough] + [n1]
        for n2, (c0, c1) in enumerate(zip(pts, pts[1:])):
            m.wall(c0, c1, niche, f"{gid}.rock_{n2 + 1}", texture=PASSAGE_TEXTURE)
        ti = m.thing(TORCH, *along(d, -od3 + NICHE_TORCH_IN), f"{gid}.torch")
        m.things[ti].fields["id"] = DEAD_TORCH_TID
        prev, prev_d = a1, d + hs
    east_piece(prev, se, prev_d, f"cistern.wall_e_{len(glows) + 1}")
    _edges(m, out, [(ne, se, "skip", ""), (se, (se[0] + od, se[1]), None, "cistern.out.end_s"),
                    ((se[0] + od, se[1]), (ne[0] + od, ne[1]), None, "cistern.out.back"),
                    ((ne[0] + od, ne[1]), ne, None, "cistern.out.end_n")])
    for ld in m.linedefs:
        if ld["user_gid"].startswith("cistern.out."):
            m.sidedefs[ld["sidefront"]]["texturemiddle"] = PASSAGE_TEXTURE
    south = m.wall(se, west[-1], cis, "cistern.wall_s", texture=PASSAGE_TEXTURE)
    # Note #17: the platform, dais and switch post at the south end. Note #18: the switch
    # (Light_ChangeToValue on the platform, dais and post: a little brighter, so using it shows) turns the
    # cistern's water south (zscript.zs listens for it).
    m.sectors[cis.index]["id"] = CISTERN_TAG
    dark = dict(light=CISTERN_DARK_LIGHT + 16, floor_tex=CISTERN_BOARDS, ceiling_tex=PASSAGE_TEXTURE)
    water = CISTERN_FLOOR
    g0, g1 = CISTERN_GRATE
    levels = (("cistern.platform", CISTERN_PLATFORM, water, cis),
              ("cistern.dais", CISTERN_DAIS, water + g1 + 8, None),
              ("cistern.post", CISTERN_POST, water + g1 + 8 + 48, None))
    outer = cis
    for name, (x0, y0, x1, y1), f, _ in levels:
        grate = name == "cistern.platform"
        sec = m.sector(name, floor=f, ceiling=CISTERN_TOP, **dict(dark, floor_tex=GUTTER_FLAT if grate else CISTERN_BOARDS))
        m.sectors[sec.index].fields.update(fadecolor=CISTERN_DARK_FOG[0], fogdensity=CISTERN_DARK_FOG[1],
                                           id=CISTERN_GRATE_TAG if grate else SWITCH_TAG)
        pts = [(x0, y1), (x1, y1), (x1, y0), (x0, y0)]         # clockwise from the north-west corner
        for i, side in enumerate(("n", "e", "s", "w")):
            # The front is the outer (lower) side: where the player stands to look at it, or to use the switch.
            ln = m.two_sided(pts[(i + 1) % 4], pts[i], outer, sec, f"{name}.edge_{side}", texture=CISTERN_WOOD)
            if grate:                                          # bars from the water up to the grate
                m.linedefs[ln]["dontpegbottom"] = True
                for sd in ("sidefront", "sideback"):
                    m.sidedefs[m.linedefs[ln][sd]].fields.update(texturemiddle="MIDBARS3", scaley_mid=72 / g0)
            if name == "cistern.post" and side == "n":
                m.sidedefs[m.linedefs[ln]["sidefront"]].fields.update(texturebottom=CISTERN_SWITCH, offsety_bottom=64)
                # Note #41: the switch's own special is the big door (Door_Open, slow); zscript.zs does the
                # rest when it's used (the dais's light, the water turning, the glow behind the door).
                m.linedefs[ln].fields.update(special=11, arg0=CISTERN_DOOR_TAG, arg1=4, playeruse=True)
        outer = sec
    m.sectors[outer.index]["user_scenery"] = True              # the post's top: nowhere to stand
    # The grate's control sector (as the bridge's): floor and ceiling = the grate's underside and top.
    gx, gy = CISTERN_GRATE_CONTROL
    control = m.room("cistern_grate_control", gx, gy, 32, 32, floor=water + g0, ceiling=water + g1,
                     floor_tex=CISTERN_GRATE_FLAT, ceiling_tex=CISTERN_GRATE_FLAT, light=CISTERN_DARK_LIGHT + 16)
    m.sectors[control.index]["user_scenery"] = True
    ln = next(i for i, l in enumerate(m.linedefs) if l["user_gid"] == "cistern_grate_control.wall_s")
    m.linedefs[ln].fields.update(special=160, arg0=CISTERN_GRATE_TAG, arg1=1, arg2=0, arg3=255)
    m.sidedefs[m.linedefs[ln]["sidefront"]]["texturemiddle"] = CISTERN_GRATE_SIDE
    for i, (x, y) in enumerate(CISTERN_CANDLES):               # note #19
        m.thing(CANDLE, x, y, f"cistern.candle_{i + 1}")
    # Note #50 (2026-11-23): a green armour tucked behind the switch post, on the boards behind the dais.
    # Note #51: it spawned on the water's floor under the boards (a 3D floor), sunk into them: lifted
    # by the boards' height above the water.
    armor = m.thing(GREEN_ARMOR, *CISTERN_ARMOR, "cistern.armor")
    m.things[armor]["height"] = g1
    for i, (a, b) in enumerate(zip(west, west[1:])):
        if a == b:
            continue
        ln = m.two_sided(a, b, drain, cis, f"cistern.wall_w_{i + 1}", texture=CISTERN_FALL)
        # blocksound (note #9): with the grates', the second sound-blocking line on the way round from the
        # hall through the drain, so gunfire in the hall isn't heard in the cistern or up its stairs.
        m.linedefs[ln].fields.update(blocking=True, blocksound=True)
        # Note #15 (2026-11-23): water only below the slot (it runs out of the drain and down the wall);
        # above it, the cistern's stone.
        m.sidedefs[m.linedefs[ln]["sideback"]]["texturetop"] = PASSAGE_TEXTURE


# Note #119 (2026-11-24): the hall's plain outer walls (its north side: the apse and the great door's wall) have a
# crown along the top, where the wall meets the sky, and along the foot a baseboard with a shoe moulding in
# front of it: big plain courses of the wall's own stone, standing out from it.
MOULD_OUT, MOULD_SHOE_OUT = 12, 6       # how far the crown and baseboard stand out; the shoe, in front of them
MOULD_BASE, MOULD_SHOE, MOULD_CROWN = 32, 12, 32     # their heights


def moulded_wall(m: MapBuilder, room, a, b, gid: str, *, before=None, after=None, skip_start=0, skip_end=0,
                 line=None) -> int:
    """The wall a -> b (the room on its right) with its mouldings. before / after: the far end of the wall
    that meets this one at a / at b, when that wall has mouldings too: the two then meet in a mitre.
    Without one, the mouldings end square, skip_start / skip_end short of the wall's end (plain wall
    there). Two strips of sector along the wall: the trim (MOULD_OUT deep: its floor is the baseboard's
    top, its ceiling the crown's underside) and in front of it the shoe (MOULD_SHOE_OUT deep). Returns
    the wall's line (the middle one). line: the whole straight wall (its two ends) when a -> b is only a
    piece of it, so that the mitres are worked out from the same points as the neighbouring walls' are."""
    length = ((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2) ** 0.5
    ux, uy = (b[0] - a[0]) / length, (b[1] - a[1]) / length
    start = a if before is not None or not skip_start else (round(a[0] + ux * skip_start, 2), round(a[1] + uy * skip_start, 2))
    end = b if after is not None or not skip_end else (round(b[0] - ux * skip_end, 2), round(b[1] - uy * skip_end, 2))
    if start != a:
        m.wall(a, start, room, f"{gid}_a")
    if end != b:
        m.wall(end, b, room, f"{gid}_b")

    def inner(dist):                                       # the wall's line moved `dist` into the room
        whole = line or (start, end)
        chain = ([before] if before is not None else []) + list(whole) + ([after] if after is not None else [])
        moved = _shifted_polyline(chain, -dist)            # (it shifts to the left: the room is on the right)
        i = 1 if before is not None else 0
        square = lambda pt: (round(pt[0] + uy * dist, 2), round(pt[1] - ux * dist, 2))
        s = tuple(round(v, 2) for v in moved[i]) if before is not None else square(start)
        e = tuple(round(v, 2) for v in moved[i + 1]) if after is not None else square(end)
        return s, e

    s1, e1 = inner(MOULD_OUT)
    s2, e2 = inner(MOULD_OUT + MOULD_SHOE_OUT)
    floor = -DROP
    trim = m.sector(f"{gid}.trim", floor=floor + MOULD_BASE, ceiling=HALL_SKY - MOULD_CROWN, light=HALL_LIGHT,
                    floor_tex=HALL_WALL, ceiling_tex=HALL_WALL)
    shoe = m.sector(f"{gid}.shoe", floor=floor + MOULD_SHOE, ceiling=-64, light=HALL_LIGHT, floor_tex=HALL_WALL)
    for sec in (trim, shoe):
        fog(m, sec)
        m.sectors[sec.index]["user_scenery"] = True
    line = m.wall(start, end, trim, gid)
    m.two_sided(s1, e1, shoe, trim, f"{gid}.trim.face")
    # The mouldings are walls to walk along, not steps to stand on (the shoe is only MOULD_SHOE high): their
    # outer lines block, like the wall did.
    blocks = [m.two_sided(s2, e2, room, shoe, f"{gid}.shoe.face")]
    # The ends: where the next wall's mouldings carry on, a line between the two walls' strips is built by
    # neither (they are different sectors with the same heights: one line each, built here for the start
    # only when nothing comes before); otherwise an end face towards the room.
    if before is None:
        blocks.append(m.two_sided(s1, start, trim, room, f"{gid}.trim.end_a"))   # (each strip on the right of its end lines)
        blocks.append(m.two_sided(s2, s1, shoe, room, f"{gid}.shoe.end_a"))
    else:
        MOULD_JOINTS[(gid, "a")] = (start, s1, s2, trim, shoe)
    if after is None:
        blocks.append(m.two_sided(end, e1, trim, room, f"{gid}.trim.end_b"))
        blocks.append(m.two_sided(e1, e2, shoe, room, f"{gid}.shoe.end_b"))
    else:
        MOULD_JOINTS[(gid, "b")] = (end, e1, e2, trim, shoe)
    for ln in blocks:
        m.linedefs[ln]["blocking"] = True
    return line


MOULD_JOINTS: dict = {}


def mould_joint(m: MapBuilder, first: str, second: str) -> None:
    """The mitre where wall `first` ends and wall `second` starts: one line between their trims and one
    between their shoes (call once both are built)."""
    corner, p1, p2, trim_a, shoe_a = MOULD_JOINTS[(first, "b")]
    corner2, q1, q2, trim_b, shoe_b = MOULD_JOINTS[(second, "a")]
    assert corner == corner2 and p1 == q1 and p2 == q2, f"mouldings of {first} and {second} don't meet"
    m.two_sided(corner, p1, trim_a, trim_b, f"{first}.trim.joint")    # (the first wall's strips on the right)
    m.two_sided(p1, p2, shoe_a, shoe_b, f"{first}.shoe.joint")


def _crowned_run(m: MapBuilder, run, drain) -> list:
    """Note #123 (2026-11-24): the crown of the north walls (note #119) carried along the east wall, which stands on
    its vine grate over the gutter: no baseboard there, but the crown can run above the water. For each
    gutter sector along the run, a strip MOULD_OUT deep along the wall: the gutter's own water and light,
    its ceiling the crown's underside. Where two gutter pieces meet at the wall, the line between them is
    cut MOULD_OUT from the wall and its first part becomes the line between their two strips. The crown
    stops 16 short of the run's two ends. Returns the stretches for hall_walls to build the wall's own
    lines from: the same, with the strips in front in place of the gutters."""
    import math
    unit = lambda p, q: ((q[0] - p[0]) / math.dist(p, q), (q[1] - p[1]) / math.dist(p, q))
    pts = [run[0][0]] + [s[1] for s in run]
    mitre = [tuple(round(v, 2) for v in q) for q in _shifted_polyline(pts, -MOULD_OUT)]
    strips: dict = {}

    def strip_of(sector, gid):
        if sector.index not in strips:
            src = m.sectors[sector.index].fields
            s = m.sector(f"{src['user_gid']}.crown", floor=src["heightfloor"], ceiling=HALL_SKY - MOULD_CROWN,
                         light=src["lightlevel"], floor_tex=src["texturefloor"], ceiling_tex=HALL_WALL)
            m.sectors[s.index].fields.update({k: src[k] for k in ("fadecolor", "fogdensity", "desaturation", "color_floor",
                                                                  "lightcolor") if k in src})
            strips[sector.index] = s
        return strips[sector.index]

    out, last = [], len(run) - 1
    inner_prev = None
    for k, (a, b, sector, gid, along) in enumerate(run):
        ux, uy = unit(a, b)
        square = lambda pt: (round(pt[0] + uy * MOULD_OUT, 2), round(pt[1] - ux * MOULD_OUT, 2))
        strip = strip_of(sector, gid)
        s, e = a, b
        if k == 0:                                         # the crown starts 16 into the run
            s = (round(a[0] + ux * 16, 2), round(a[1] + uy * 16, 2))
            out.append((a, s, sector, f"{gid}_a", along))
            i_s = square(s)
            m.two_sided(i_s, s, strip, sector, f"{gid}.crown.end_a")
        else:
            i_s = inner_prev
        if k == last:
            e = (round(b[0] - ux * 16, 2), round(b[1] - uy * 16, 2))
            i_e = square(e)
            m.two_sided(e, i_e, strip, sector, f"{gid}.crown.end_b")
        elif run[k + 1][2] is sector:                      # the same gutter goes on round a bend: the strip does too
            i_e = mitre[k + 1]
        else:
            # The line between this gutter piece and the next starts at b: cut it MOULD_OUT from the wall.
            nxt = run[k + 1][2]
            vb = m.vertex(*b)
            cut = next(ld for ld in m.linedefs if "sideback" in ld.fields and vb in (ld["v1"], ld["v2"])
                       and {m.sidedefs[ld["sidefront"]]["sector"], m.sidedefs[ld["sideback"]]["sector"]} == {sector.index, nxt.index})
            far = cut["v2"] if cut["v1"] == vb else cut["v1"]
            q = (m.vertices[far]["x"], m.vertices[far]["y"])
            wx, wy = unit(b, q)
            reach = MOULD_OUT / abs(wx * uy - wy * ux)     # along that line, to be MOULD_OUT from the wall
            i_e = (round(b[0] + wx * reach, 2), round(b[1] + wy * reach, 2))
            cut["v1" if cut["v1"] == vb else "v2"] = m.vertex(*i_e)
            m.two_sided(b, i_e, strip, strip_of(nxt, run[k + 1][3]), f"{gid}.crown.joint")
        m.two_sided(i_s, i_e, sector, strip, f"{gid}.crown")
        out.append((s, e, strip, gid, along + (16 if k == 0 else 0)))
        if k == last:
            out.append((e, b, sector, f"{gid}_b", along + round(math.dist(a, e))))
        inner_prev = i_e
    return out


def hall_walls(m: MapBuilder, room, walls, mould=None, edges=()) -> dict:
    """Note #36: the hall's outer walls. `walls`: the walls in order, clockwise from the mouth's west
    corner round to its east corner, each (start, stretches), a stretch being (end, the sector in front,
    gid). Note #44: only where a gutter meets the wall is it lifted off the floor over a drain (a
    two-sided line, blocking, the grate in the gap); elsewhere it's a plain wall. Each run of gutter
    stretches gets its own drain, DRAIN_DEPTH deep behind it, closed off at both ends. A wall's texture
    runs on along its whole length."""
    # Note #86: `edges`: stretches with the room in front that still make a run (the cliff's, once its
    # gutter was gone).
    runs, run = [], []
    for start, stretches in walls:
        a = start
        for end, sector, gid in stretches:
            along = round(((a[0] - start[0]) ** 2 + (a[1] - start[1]) ** 2) ** 0.5)
            if sector is room and gid not in edges:
                if mould and gid in mould:                 # note #119: crown, baseboard and shoe
                    ln = moulded_wall(m, room, a, end, gid, **mould[gid])
                else:
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
        cliff = k == 0                                       # the west run: the cliff's edge (note #96)
        drain = m.sector(name, floor=DRAIN_FLOOR, ceiling=DRAIN_TOP, light=CISTERN_LIGHT, floor_tex=GUTTER_FLAT)
        if cliff:
            # Note #99: the hall's fog too, so the walls at the cliff's ends are the colour of the hall's walls
            # (without it they stood out; the sky takes no fog).
            m.sectors[drain.index].fields.update(heightfloor=CLIFF_FLOOR, heightceiling=HALL_SKY, texturefloor=SKY_FLAT,
                                                 textureceiling=SKY_FLAT, lightlevel=HALL_LIGHT,
                                                 fadecolor=HALL_FOG, fogdensity=HALL_FOG_DENSITY)
        if cistern:                                          # note #94: seen from the cistern, looking up into the slot: its mossy stone
            m.sectors[drain.index]["textureceiling"] = PASSAGE_TEXTURE
        # Note #78: seen from the hall through the vines, the water should fade uniformly into darkness:
        # the drains get the cistern's light and its dark fog (they had the hall's grey fog, then the
        # cistern's dark one showed beyond: a seam).
        if cliff:
            # Note #98 (2026-11-24): the cliff is the west side only. The run's south stretch (along the
            # south wall, west of the landing) is the stone wall again, and it turns the corner: the first
            # CLIFF_PIER of the west side is wall too, a pier that ends the wall; its flank (the cliff
            # sector's end wall, DRAIN_DEPTH long) stands out past the railing at the cliff's edge.
            kept = []
            for a, b, sector, gid, along in run:
                if abs(b[0] - a[0]) >= abs(b[1] - a[1]):       # along the south wall
                    ln = m.wall(a, b, sector, gid)
                elif not kept:                                 # the first stretch up the west side: the pier, then the edge
                    n = ((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2) ** 0.5
                    c = (round(a[0] + (b[0] - a[0]) * CLIFF_PIER / n, 2), round(a[1] + (b[1] - a[1]) * CLIFF_PIER / n, 2))
                    ln = m.wall(a, c, sector, f"{gid}_pier")
                    kept.append((c, b, sector, gid, along + CLIFF_PIER))
                else:
                    kept.append((a, b, sector, gid, along))
                    continue
                if along:
                    m.sidedefs[m.linedefs[ln]["sidefront"]]["offsetx"] = along
            run = kept
        else:
            m.sectors[drain.index].fields.update(fadecolor=CISTERN_FOG[0], fogdensity=CISTERN_FOG[1])
        m.sectors[drain.index]["user_scenery"] = True
        if cistern:                                          # note #123: a crown along the top of the wall over the drain
            run_lines = _crowned_run(m, run, drain)
        else:
            run_lines = [(a, b, sector, gid, along) for a, b, sector, gid, along in run]
        if cliff:                                            # note #89: the strip under the railing's top
            hall_floor = m.sectors[room.index]["heightfloor"]
            strip = m.sector("cliff_ledge", floor=hall_floor, ceiling=HALL_SKY, light=HALL_LIGHT, floor_tex=HALL_FLOOR,
                             ceiling_tex=SKY_FLAT)
            m.sectors[strip.index].fields.update(fadecolor=HALL_FOG, fogdensity=HALL_FOG_DENSITY, id=CLIFF_CAP_TAG,
                                                 user_scenery=True)
            rail_top = hall_floor + 72 - CLIFF_RAIL_SUNK + CLIFF_CAP   # note #111: the cap sits on the bars' top rail, not over it
            control = m.room("cliff_cap_control", *CLIFF_CAP_CONTROL, 32, 32, floor=rail_top - CLIFF_CAP, ceiling=rail_top,
                             floor_tex=CLIFF_CAP_TEX, ceiling_tex=CLIFF_CAP_TEX, light=HALL_LIGHT)
            m.sectors[control.index]["user_scenery"] = True
            cl = next(i for i, l in enumerate(m.linedefs) if l["user_gid"] == "cliff_cap_control.wall_s")
            m.linedefs[cl].fields.update(special=160, arg0=CLIFF_CAP_TAG, arg1=1, arg2=0, arg3=255)
            m.sidedefs[m.linedefs[cl]["sidefront"]]["texturemiddle"] = CLIFF_CAP_TEX
        for a, b, sector, gid, along in run_lines:
            ln = m.two_sided(a, b, sector, strip if cliff else drain, gid, texture=WALL)
            if cliff:                                        # the edge: a railing standing in the water, nothing above it
                m.linedefs[ln].fields.update(blocking=True, dontpegbottom=True)
                for sd in ("sidefront", "sideback"):
                    # Note #100: sunk CLIFF_RAIL_SUNK into the water, so half of it shows: its top rail 28 above
                    # the hall's floor (it was 64: too high).
                    m.sidedefs[m.linedefs[ln][sd]].fields.update(texturemiddle=CLIFF_RAIL, offsety_mid=-CLIFF_RAIL_SUNK)
                m.sidedefs[m.linedefs[ln]["sidefront"]]["offsetx"] = round(along) % 64   # note #108: the bars carry on round the bends
                continue
            # Note #56: the wall above the gap pegged to the ceiling, as the plain walls beside it are.
            # Note #83: blocksight: monsters (the cistern's spectres) can't see through the vines.
            m.linedefs[ln].fields.update(blocking=True, dontpegtop=True, blocksight=True, blocksound=True)
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
        horizon = far = None
        if cliff:
            ledge = _shifted_polyline(inner, CLIFF_LEDGE)
            for i, (a, b) in enumerate(zip(ledge, ledge[1:])):  # note #89: the strip's far edge, the cliff's lip
                ln = m.two_sided(a, b, strip, drain, f"cliff_ledge.edge_{i + 1}", texture=WALL)
                m.sidedefs[m.linedefs[ln]["sideback"]]["texturebottom"] = CLIFF_FALL
            horizon = m.sector("cliff_horizon", floor=CLIFF_FLOOR, ceiling=CLIFF_FLOOR, light=HALL_LIGHT,
                               floor_tex=SKY_FLAT, ceiling_tex=SKY_FLAT)
            far = _shifted_polyline(inner, DRAIN_DEPTH + CLIFF_HORIZON)
        for i, (a, b) in enumerate(zip(outer, outer[1:])):
            if a != b and i >= shared:
                if cliff:
                    m.two_sided(a, b, drain, horizon, f"{name}.back_{i + 1}")
                    m.wall(far[i], far[i + 1], horizon, f"cliff_horizon.back_{i + 1}")
                else:
                    m.wall(a, b, drain, f"{name}.back_{i + 1}")
        if cliff:
            m.wall(outer[0], far[0], horizon, "cliff_horizon.end_a")
            m.wall(far[-1], outer[-1], horizon, "cliff_horizon.end_b")
        if cistern:
            out["cistern"] = (drain, outer[:shared + 1])
        if cliff:                                            # note #89: the ends cross the strip, then the drain
            ends = (m.wall(inner[0], ledge[0], strip, "cliff_ledge.end_a"), m.wall(ledge[0], outer[0], drain, f"{name}.end_a"),
                    m.wall(outer[-1], ledge[-1], drain, f"{name}.end_b"), m.wall(ledge[-1], inner[-1], strip, "cliff_ledge.end_b"))
        else:
            ends = (m.wall(inner[0], outer[0], drain, f"{name}.end_a"), m.wall(outer[-1], inner[-1], drain, f"{name}.end_b"))
        if cliff:                                            # the hall's walls carried out to the cliff's face: its great stone
            for ln in ends:
                m.sidedefs[m.linedefs[ln]["sidefront"]].fields.update(
                    texturemiddle=HALL_WALL, scalex_mid=HALL_WALL_SCALE, scaley_mid=HALL_WALL_SCALE)
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
    # Note #27: the lip's floor showed as a strip of marble across the liquid: now liquid too (blue water
    # tinted violet: the lip can't be desaturated like the spill, that's what it is for).
    # Note #29: blue water stayed blue (a tint can only take colour away): a plain grey flat takes the violet.
    lip = m.sector(f"{gid}.lip", floor=floor, ceiling=-64, light=BASE_LIGHT, floor_tex="CEIL5_1")   # note #33: a dark neutral flat, as dark as the desaturated liquid
    fog(m, lip)
    hall_ceiling(m, lip)
    # Note #31: the strip was far brighter than the liquid round it: FLAT19 is three times as light as the
    # green liquid once that is desaturated (104 against 35 of 255), so its violet is scaled down to match.
    m.sectors[lip.index].fields.update(lightcolor=SWITCH_GLOW_TINT, user_scenery=True, color_floor=VIOLET)
    # Note #103 (2026-11-24): the lip's sky sits at the sleeve's top, 16 under the hall's (note #101), and the
    # lines round it showed that 16 as a scrap of marble above the obelisk's top: no upper texture on their
    # outer sides, so nothing is drawn there.
    for name, p0, p1, other in (("edge_e", (lx, yn), (lx, ys), spill), ("side_n", (sx, yn), (lx, yn), base),
                                ("side_s", (lx, ys), (sx, ys), base)):
        ln = m.two_sided(p0, p1, lip, other, f"{gid}.lip.{name}", texture=STONE)
        m.sidedefs[m.linedefs[ln]["sideback"]]["texturetop"] = "-"
    m.two_sided((lx, yn), (bx, yn), spill, base, f"{gid}.spill.side_n", texture=STONE)
    m.two_sided((bx, ys), (lx, ys), spill, base, f"{gid}.spill.side_s", texture=STONE)
    # Note #107 (2026-11-24): the slit built again, without ceiling tricks (under an open sky they left a
    # see-through slice, then scraps on the obelisk's top: notes #101, #103, #106). The slit is open to the
    # sky like everything round it, and the piece of sleeve above the hollow is a 3D floor in it: a solid
    # block from the hollow's top (floor + high) to the sleeve's top, the sleeve's marble on its sides
    # (its control sector stands outside the map, SLIT_CONTROL). zscript.zs lowers the block's top with the
    # sinking sleeve until nothing of it is left (SLIT_CONTROL_TAG).
    slit = m.sector(f"{gid}.slit", floor=floor, ceiling=-64, light=BASE_LIGHT, floor_tex=GUTTER_FLAT)
    # (Note #111: not named "monolith_...": the pass that opens the hall to the sky takes every monolith_ sector
    # whose ceiling is at the sleeve's top for a pillar and lifts it to the sky: the block stood 16 too tall.)
    cx, cy = SLIT_CONTROL
    control = m.room("slit_control", cx, cy, 32, 32, floor=floor + high, ceiling=SLEEVE_TOP,
                     floor_tex=STONE, ceiling_tex=STONE, light=BASE_LIGHT)
    m.sectors[control.index].fields.update(id=SLIT_CONTROL_TAG, soundsequence="Silence", user_scenery=True)
    cl = next(i for i, l in enumerate(m.linedefs) if l["user_gid"] == "slit_control.wall_s")
    # arg2 = 1 (note #117): the block doesn't light what is under it. Without it the hollow's liquid took the
    # control sector's plain light: bright, not the slit's own deep violet.
    m.linedefs[cl].fields.update(special=160, arg0=SLIT_TAG, arg1=1, arg2=1, arg3=255)
    m.sidedefs[m.linedefs[cl]["sidefront"]]["texturemiddle"] = STONE
    fog(m, slit)
    # Note #42: once the sleeve has sunk, the slit is part of the ceiling's slot above the slab: its
    # ceiling, and its walls' upper parts, are the slot's (marble, as dark), not liquid.
    m.sectors[slit.index].fields.update(id=SLIT_TAG, soundsequence="Silence", user_scenery=True,
                                        desaturation=1.0, color_floor=VIOLET, color_wallbottom=VIOLET)
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
    # Note #101: the lip's ceiling is at the sleeve's top now, so the texture needs no moving down.
    m.sidedefs[m.linedefs[mouth]["sideback"]].fields.update(offsetx=ys - (y0 - 8))
    back = m.two_sided((sx - depth, ys), (sx - depth, yn), slit, sleeve, f"{gid}.slit.back", texture=STONE)
    m.sidedefs[m.linedefs[back]["sidefront"]].fields.update(texturebottom=VIOLET_FALL, light=SLOT_DARK)
    # Note #106 (2026-11-24): with the slit's ceiling stone again (note #101), the sleeve's side of the slit's
    # three inner lines drew the 16 between the sleeve's top and the sky as wall: a small block standing on
    # the obelisk. No upper texture there: nothing is drawn.
    m.sidedefs[m.linedefs[back]["sideback"]]["texturetop"] = "-"
    for name, p, q in (("side_n", (sx - depth, yn), (sx, yn)), ("side_s", (sx, ys), (sx - depth, ys))):
        ln = m.two_sided(p, q, slit, sleeve, f"{gid}.slit.{name}", texture=STONE)
        m.sidedefs[m.linedefs[ln]["sidefront"]]["light"] = SLOT_DARK
        m.sidedefs[m.linedefs[ln]["sideback"]]["texturetop"] = "-"          # note #106


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
                     light=CALL_NICHE_LIGHT, floor_tex=LIP_TOP, ceiling_tex=TRACK)    # note #45: track metal, as the top one
    m.sectors[niche.index]["user_scenery"] = True   # too small to enter: decoration (movement check)
    fog(m, niche)
    m.wall(a, p0, mouth, "mouth.wall_w")
    # Notes #34, #37 (2026-11-23): once an elevator switch has been used, this niche is shut by a panel, so
    # it's plainly a one-time thing. As at the top switch (note #36): the last SHUTTER_DEEP of the niche,
    # in front of the switch, is a sector of its own whose ceiling zscript.zs brings down (tag
    # CALL_NICHE_TAG), the panel riding down inside the niche. (First the sill rose instead, and its
    # metal face ran all the way down the wall under the niche.)
    # Note #135 (2026-11-26): the wall above and below the niche carries on from the wall beside it: offset by its
    # distance along (as hall_walls does), and pegged like a plain wall (to the ceiling: upper and lower parts).
    import math
    ln = m.two_sided(p0, p1, mouth, niche, "mouth.call_niche.mouth")
    m.linedefs[ln].fields.update(dontpegtop=True, dontpegbottom=True)
    m.sidedefs[m.linedefs[ln]["sidefront"]]["offsetx"] = round(math.dist(a, p0))   # a whole number: UZDoom refuses a fraction (a crash)
    ln = m.wall(p1, b, mouth, "mouth.wall_w2")
    m.sidedefs[m.linedefs[ln]["sidefront"]]["offsetx"] = round(math.dist(a, p1))
    depth = (into[0] ** 2 + into[1] ** 2) ** 0.5
    k = (depth - SHUTTER_DEEP) / depth
    r0, r1 = (p0[0] + into[0] * k, p0[1] + into[1] * k), (p1[0] + into[0] * k, p1[1] + into[1] * k)
    shutter = m.sector("mouth.call_niche.shutter", floor=floor, ceiling=floor + NICHE_TOP - NICHE_FLOOR,
                       light=CALL_NICHE_LIGHT, floor_tex=LIP_TOP, ceiling_tex=TRACK)
    m.sectors[shutter.index].fields.update(user_scenery=True, id=CALL_NICHE_TAG)
    fog(m, shutter)
    m.wall(p0, r0, niche, "mouth.call_niche.side_a", texture=TRACK)
    panel = m.two_sided(r0, r1, niche, shutter, "mouth.call_niche.shutter.panel")
    m.sidedefs[m.linedefs[panel]["sidefront"]]["texturetop"] = CALL_SHUTTER_TEXTURE
    m.wall(r1, p1, niche, "mouth.call_niche.side_b", texture=TRACK)
    m.wall(r0, q0, shutter, "mouth.call_niche.shutter.side_a", texture=TRACK)
    back = m.wall(q0, q1, shutter, "mouth.call_niche.switch", texture=SWITCH_TEXTURE)
    m.wall(q1, r1, shutter, "mouth.call_niche.shutter.side_b", texture=TRACK)
    m.linedefs[back].fields.update(special=37, arg0=CAR_TAG, arg1=CAR_SPEED, arg2=DROP, arg3=1, playeruse=True)
    width = ((q1[0] - q0[0]) ** 2 + (q1[1] - q0[1]) ** 2) ** 0.5
    side = m.sidedefs[m.linedefs[back]["sidefront"]]
    side["offsetx"] = round(32 - width / 2)   # SW1GRAY's plate (x ~16-47) in the middle of the back wall
    # Note #42: stood on the floor (dontpegbottom), not hung from the shutter's ceiling, so the plate
    # stays put as the panel comes down: row 69 at the niche's top, 32 above the floor.
    m.linedefs[back]["dontpegbottom"] = True
    side["offsety"] = 69 - (128 - (NICHE_TOP - NICHE_FLOOR))


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
    # Note #109 (2026-11-24): a snuffed torch for every altar. zscript.zs
    # swaps it for the unlit torch (thing id ALTAR_TORCH_TID; not solid, so the pickups stay in reach) and
    # lights it as its obelisk is revealed: a green torch, the switch obelisk's a violet one.
    # Note #115: not on the altar: on the floor just behind it, in the 16 between the altar and the obelisk's base.
    torch = m.thing(TORCH, ax0 - 8 if facing == "e" else ax1 + 8, (ay0 + ay1) / 2, f"{gid}.altar.torch")
    m.things[torch]["id"] = ALTAR_TORCH_TID
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
            ((x_out, 200), (x_wall, 200)), ((x_wall, 200), (x_out, 200)),      # note #99: onto the mouth too
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
            m.sidedefs[m.linedefs[ln]["sideback"]]["texturebottom"] = TRACK    # its foot: the strip (note #54)
        else:
            m.wall(a, b, s, f"{gid}.wall_{i}")
    return s


def wall_with_channels(m: MapBuilder, closet, a, b, gid: str, *, start=None, end=None, panel=None, floor=0,
                       channels=CHANNEL_AT, high=LOW) -> None:
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
    for i, d in enumerate(channels):
        p0, p1 = at(d - 8), at(d + 8)
        q0, q1 = at(d - 8, 8), at(d + 8, 8)
        name = f"{gid}.channel_{i + 1}"
        dim = (gid, i + 1) in CHANNEL_DIM
        ch = m.sector(name, floor=floor, ceiling=floor + high, light=CHANNEL_DIM_LIGHT if dim else CHANNEL_LIGHT)
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
    last = len(channels) + 1
    if end:
        m.wall(start, end[0], closet, f"{gid}_{last}")
        m.wall(end[0], end[1], closet, f"{gid}_{last}b")
    else:
        m.wall(start, b, closet, f"{gid}_{last}")


def passage_secret(m: MapBuilder, s, a, b, P, gid: str) -> None:
    """Note #87: the passage wall a -> b (passage coordinates, rock on its left) as a secret door: the
    whole stretch is a door 8 thick (PASSAGE_SECRET_TAG, shut: floor = ceiling), its face the
    side passage's mossy rock (PASSAGE_SECRET_TEX, a shade off the passage's), opened by using it
    (Door_Open, stays open); behind it an alcove as wide as the wall with a chaingun that counts as the
    secret when taken. Note #90: it lifts only to a doorway's height (a door opens to the lowest ceiling
    beside it, less 4: the alcove's, PASSAGE_SECRET_HIGH), with a puff of dust (zscript.zs)."""
    import math
    dx, dy = b[0] - a[0], b[1] - a[1]
    n = math.hypot(dx, dy)
    ix, iy = -dy / n, dx / n                                   # left of a -> b: into the rock
    at = lambda pt, d: P(pt[0] + ix * d, pt[1] + iy * d)
    piece = m.sectors[s.index].fields
    f, c = piece["heightfloor"], piece["heightceiling"]
    door = m.sector(f"{gid}.secret_door", floor=f, ceiling=f, light=piece["lightlevel"],
                    floor_tex=MAIN_WALL, ceiling_tex=MAIN_WALL)
    m.sectors[door.index]["id"] = PASSAGE_SECRET_TAG
    deep = 8 + PASSAGE_SECRET_ALCOVE
    alcove = m.sector(f"{gid}.secret", floor=f, ceiling=f + PASSAGE_SECRET_HIGH, light=max(0, piece["lightlevel"] - 16),
                      floor_tex=MAIN_FLOOR, ceiling_tex=MAIN_WALL)
    face = m.two_sided(P(*a), P(*b), s, door, f"{gid}.secret_door.face", texture=PASSAGE_SECRET_TEX)
    # Door_Open (11: tag, speed): opened by the player's use from the passage, stays open; a plain wall on the automap.
    m.linedefs[face].fields.update(special=11, arg0=PASSAGE_SECRET_TAG, arg1=16, playeruse=True, secret=True)
    m.sidedefs[m.linedefs[face]["sidefront"]]["texturetop"] = PASSAGE_SECRET_TEX
    # _edges turns each outline round so its sector is on the right (P may mirror the passage's frame).
    made = _edges(m, door, [(P(*a), P(*b), "skip", ""), (P(*b), at(b, 8), None, f"{gid}.secret_door.side_b"),
                            (at(b, 8), at(a, 8), alcove, f"{gid}.secret_door.back"),
                            (at(a, 8), P(*a), None, f"{gid}.secret_door.side_a")])
    made += _edges(m, alcove, [(at(a, 8), at(b, 8), "skip", ""), (at(b, 8), at(b, deep), None, f"{gid}.secret.side_b"),
                               (at(b, deep), at(a, deep), None, f"{gid}.secret.back"),
                               (at(a, deep), at(a, 8), None, f"{gid}.secret.side_a")])
    for ln in made:
        for sd in ("sidefront", "sideback"):
            if sd in m.linedefs[ln].fields:
                side = m.sidedefs[m.linedefs[ln][sd]]
                for key in ("texturetop", "texturemiddle", "texturebottom"):
                    if side.get(key, "-") != "-":
                        side[key] = MAIN_WALL
    mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
    gx, gy = at(mid, deep - 24)
    ox, oy = P(*mid)
    t = m.thing(CHAINGUN, gx, gy, f"{gid}.secret.chaingun",
                angle=round(math.degrees(math.atan2(oy - gy, ox - gx))) % 360)
    m.things[t]["countsecret"] = True


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
    # Note #35 (2026-11-23): once the target is shot, a block drops over it: the slot's ceiling comes down
    # to the beam's (zscript.zs, by the slot's second tag), which leaves the lintel one plain beam.
    m.sectors[slot.index]["moreids"] = str(TARGET_SLOT_TAG)
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
