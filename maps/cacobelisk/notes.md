# Cacobelisk

*Named 2026-11-22 (it was `test2`); kept as an example of what the workflow makes possible: built in one
evening entirely from in-game notes, editor saves and chat, every round played live with H. Ideas worth
reusing: a one-way broken elevator start with its switch in a lit niche and the track showing as you
descend; a hall of obelisks that reveal themselves in pairs as the player passes (sleeves that sink
into ceiling slots, scripted sounds, coloured glows, sprayed decals in a colour nothing bleeds); fog,
light and pickups tuned by ear and eye from the game.*


## Design intent

- **Start: a broken elevator.** A cramped closet (64 wide, 64 high, 128 long), the dead level-start
  door (DOOR3) behind the player. At its far end a small square platform (64 x 64, sector tag 1); straight
  ahead the switch, inset in a niche (48 wide, 8 deep, sill 16, top 48) lit a little brighter (176 vs 128).
  The switch lowers the platform and the niche's floor (both tag 1), 256, once: the closet stays up the
  shaft, never to return. Below the starting floor the shaft's walls are elevator track (SUPPORT3); above
  it, plain wall (the shaft is lined with solid blocks, floor = ceiling = 0, so its walls have an upper
  and a lower part). Going down, the niche opens out below the switch into a mouth and a big, tall room
  (about 550 wide, 1000 deep, 192 high; the mouth 192 high too) straight on, so the start opens up; the niche is the way through (a 16 step up
  from the platform). Looking up from the bottom, the switch is far above (pegged to the niche's top).
  On landing, the platform's light flickers and sparks fly off the shaft walls just above it, with the
  spark sound (`zscript.zs`, `CacobeliskElevator`). One-way on purpose: the elevator is broken, and
  nothing is left up there.
- **Second session (2026-11-22 evening, notes #29-#84 and two editor saves): the map grew past the hall.**
  An entry secret (shoot the glowing valve wheel over the start door: a panel opens on partial
  invisibility). The obelisks reveal as a show once the player is down; the purple switch obelisk only
  when its shotgun is taken, hinted by a stain trail, a dead marine, a violet-tinted east gutter and a
  violet leak from a slit in its back. Both gutters meander, meet in front of the landing under a low
  bridge (a 3D floor), and run out under the walls through vine grates into drains. At the far end a
  great door, stuck ajar, with a small door in its left leaf; behind it imps, then a mossy, torch-lit
  passage (wide enough for pinkies: 128) that climbs, turns back and goes down into a dark, flooded
  cistern east of the hall, its west wall a sheet of falling water, the hall glimpsed above through the
  vines; spectres lie in ambush there. Music D_ROMER2. **Open:** where the cistern leads (it's a dead
  end); what using the switch obelisk does; an exit.

## Feedback log

- 2026-11-22, note #1 (game): shrink the start room to a closet with the start door behind; hallway with a
  switch at its end that lowers the floor the player stands on to the entrance room, permanently; then
  flickering light and sparks. First built as a 512-long hallway that sank whole, the room off to its side.
- 2026-11-22, chat: closet 1/3 the length and 1/2 the height, claustrophobic; the elevator a small square
  platform (only it sinks); the way on revealed straight ahead below the switch, into a big room that
  feels like opening up.
- 2026-11-22, note #2 (game): the switch inset in a niche with a slight glow; the wall revealed below the
  starting floor as the elevator goes down should be another texture, a metal elevator track. Built as
  described above.
- 2026-11-22, editor save (01:03): the room stretched to about 1000 deep, its walls slightly out of square;
  the mouth's and the room's ceilings lowered to -64 (192 high). Ported into map.py (ceilings included, so
  no overrides).
- 2026-11-22, chat: fog in the big room (first at density 96), then "foggier" (200, the mouth too, so it
  doesn't start at a hard edge); the mouth and the room both dim (light 120), a big quiet hall; the ceiling
  stays at -64. Two rows of monoliths flanking the way downrange, to pull the eye: green marble slabs
  (MARBLE1, 64 x 32, 128 tall on a 16 step, 48 short of the ceiling), each with a carved face towards
  the aisle, all three faces alternating (MARBFACE skull, MARBFAC2 ring, MARBFAC3 alien); 5 a side,
  160 apart, an aisle 192 wide; their bases a little brighter (136).
- 2026-11-22, note #3 (game): the slabs were too narrow for the 128-wide carvings. Now 80 long with the
  aisle-side corners cut (12 across, 16 along, 20 on the diagonal), the carving wrapped round: side 20 +
  corner 20 + face 48 + corner 20 + side 20 = 128, centred on the face; plain marble at the back.
- 2026-11-22, note #4 (game): the ring (MARBFAC2) is the favourite: all ten monoliths carry it now; the
  skull (MARBFACE) and the alien (MARBFAC3) are kept for another use. Fog thicker (280), hall light 104,
  bases 120. A sickly yellow-green glow round each: base and slab tinted (lightcolor 0xC8F078) and a slowly
  pulsing coloured light (PointLightPulseAttenuated, 9831; 150,200,40; radius 112 to 80 every 3 s) 24 out
  in front of the face, 64 up. (Purple was the other colour offered.)
- 2026-11-22, editor saves 01:23-01:26: the room widened and lengthened (about 830 x 1800), its north
  wall a three-sided apse peaking at y 2080; both monolith rows 64 further out (aisle 320 wide, x -128 to
  192); the mouth flared out to (-64, 240) and (144, 224). Ported into map.py.
- 2026-11-22, note #5 (editor): monoliths spread at regular intervals down the whole length: six a side,
  every 280 (y 400-1800). A gutter of green water (NUKAGE1, 64 wide, 8 deep, harmless) along the west and
  east walls behind the rows, following the walls' slant, a lip of about 32 by the wall and a walkway of
  about 100 behind the stones, so the middle is the clear way on.
- 2026-11-22, note #6 (game): the closet twice as wide and long, darker, with dim vertical emergency
  lights in channels, as if no one has come this way in a long time. Now 128 x 256 (x -32 to 96, y -128
  to 128), still 64 high, the platform's opening in the middle of its north wall, the start door (64
  wide) in the middle of its south wall; light 80 (the platform too). Three channels in each long wall
  (16 wide, 8 deep, floor to ceiling): a red tube (LITERED) behind, DOORTRAK sides, light 128 tinted red,
  and a dim red light (PointLightAttenuated, 9830) in front spilling on the floor. The channels are
  marked `user_scenery` (too narrow to enter) for the movement check.
- 2026-11-22, chat: the red varied: three channels dimmer (west 1 and 3, east 2: light 96, a fainter red
  light), three as before, not mirrored. The closet breathes: Light_Glow between 92 and 60, 3 s each way,
  started by zscript.zs when the level loads (closet tag 2).
- 2026-11-22, note #7 (game): the switch's alcove should pulse, subtle but insistent: this is the only way
  forward. A small pale light (PointLightPulseAttenuated; 150,200,170; radius 24 to 56 every second) just
  in front of the plate; it stays up with the switch when the niche drops. And a glimpse of the elevator
  track before the ride: the solid blocks lining the shaft are at 16 (were 0), so the track shows 16 up the
  platform's walls.
- 2026-11-22, editor save 01:42: the closet's two far corners cut on the diagonal (either side of the
  platform opening); the switch pulse smaller (radius 12 to 24). Ported into map.py.
- 2026-11-22, note #8 (board): the obelisks reveal themselves. At first each is a plain pillar to the
  ceiling (a MARBLE1 sleeve, 8 round the slab). Crossing the line between a pair (the middle of the two
  slabs) sinks both sleeves into their bases (Floor_LowerToLowest, speed 6: ~7 s, with the floor's
  grinding sound), uncovering the carved slabs with a cacodemon on top of each (spawned by the script,
  hidden in the sleeve until it sinks) and switching their glow lights on (dormant until then). Pairs go
  one at a time as they're passed: zscript.zs CacobeliskObelisks, which finds everything by tag (sleeves
  100 + pair, slabs 200 + pair, lights thing id 100 + pair). The base step is 8 now (was 16), leaving
  the cacodemon its 56 between the slab's top and the ceiling. The note says "3 states": two are built;
  the third is to be asked.
- 2026-11-22, editor save 01:47: a raised ceiling panel in the closet (x -24 to 88, from the south wall
  to y 120, ceiling 72; an 8-wide border at 64 on the west, east and north): ported as `closet.coffer`
  (tagged with the closet, so it breathes too). The save was made on the map from before note #8 (the
  editor hadn't reloaded: it had unsaved changes when note #8 was built), so it also "undid" note #8
  (no sleeves, lights not dormant, base step 16): those differences were not taken.
- 2026-11-22, note #9 (game): slower, and further down before the carving shows; a cacodemon on one
  obelisk a pair: left, right, left, left, right, left (going north). The sleeves (and the space over the
  slab) now reach up into a slot in the ceiling, top at -16 (48 above the hall's -64), so they sink 104
  before the carving shows (was 56) and the carving stays whole (MARBFAC2's ring fills rows ~5-118, no room
  to crop it). Speed 4: the 232 down takes about 13 s. The slot stays open in the ceiling afterwards.
  Only slabs with a cacodemon are tagged (200 + pair); pairs are found by their sleeves (100 + pair).
- 2026-11-22, note #10 (game): a switch to call the elevator from the bottom, for completeness (in play you
  always arrive from above). Not on the shaft wall itself (it's the way out, and SW1GRAY would repeat its
  plate on the 192-high wall): in a small lit niche in the mouth's west wall beside the shaft (38 wide, 9
  deep, sill 16, 32 high, like the top one). Floor_MoveToValue to -256 (not "by 256"), so it does nothing
  once the platform is down; the landing breaks it the same way (the script listens for either switch).
- 2026-11-22, note #11 (game): one obelisk, monolith_e5 (5th pair, east), is an object to interact with
  and should look, sound and glow slightly different. Built: it's the only one that brings a cacodemon
  ("6 is too many"); its glow greener and paler (120,220,150, tint 0xB8F0B0) with a quicker pulse (2 s);
  a very quiet low rumble (UZDoom's world/quake, looped, ATTN_STATIC) from inside it from the start.
  Open: what using it does, and its look: UZDoom's built-in decals are all damage marks (scorch, blood,
  bullet chips, plasma and BFG burns; the script can spray any of them by name), so a sign of "use me"
  probably wants our own decal (DECALDEF + a small graphic packed with the map) or a different texture.
- 2026-11-22, chat (answers to note #11): the switch obelisk's mark is a blood splatter in a colour nothing
  else bleeds: three of UZDoom's blood splats (A_SprayDecal "BloodSplat" with a colour, luminous violet
  0xA030FF) on its face, each sprayed as the sinking sleeve uncovers it. What using it does: not decided
  yet; it stays inert for now.
- 2026-11-22, note #12 (game): after calling the elevator from the bottom, the top switch could still be
  reached from the shaft and lowered it another 256. Now whichever switch is used first locks the other
  (zscript.zs LockSwitches: its special cleared, SW1GRAY turned to SW2GRAY), so both stay "on" for good.
- 2026-11-22, note #13 (game): the pillars should sink silently or with a quieter, more natural sound.
  The sleeves are `silent` (no standard grinding); the script plays UZDoom's quake rumble from each while
  it moves (volume 0.25, pitch 0.75), fading out over a second when it stops.
- 2026-11-22, note #14 (game): the marble of the ceiling slots (MARBLE1) carried onto their ceilings, and
  the slots severely darkened: lightceiling -88 on the sleeve and slab sectors, light -88 on the sleeve's
  side of its edges (the slot walls): 32 against the hall's 104-120. Only those surfaces: the sectors' own
  light, which also falls on the carved faces, is unchanged. (The validator now accepts a wall texture as
  a flat: UZDoom draws it.)
- 2026-11-22, note #15 (game): the reveal "still much too loud" (the grinding was already off; it was the
  rumble). Now volume 0.08 (was 0.25), pitch 0.5 (an octave down, half speed), ATTN_STATIC (heard only close
  by). Fully silent is the fallback if it's still too much.
- 2026-11-22, note #16 (game): a low altar in front of each monolith with one or two small pickups, to gear
  up for the cacodemon. Green marble (FLOOR7_2 top, MARBLE1 sides), 16 high, 24 deep, 48 along, 16 out from
  the base on the aisle side (the aisle is ~208 wide between them now). Pistol start, so small things:
  clips, health and armour bonuses, varied and not mirrored; a stimpack on w4, the pair before the switch
  obelisk (map.py ALTAR_ITEMS).
- 2026-11-22, chat: the reveal "*still* too loud, much much quieter". The cause: the grinding had never
  been off. UDMF `silent` (SECF_SILENT) means "things in this sector make no sound", not "this sector moves
  silently" (that's SECF_SILENTMOVE): it silenced the script's rumble (its source sat in the sleeve)
  and left the floor's grinding. Now the sleeves have `soundsequence = "Silence"` instead, and the rumble,
  no longer silenced, is very faint: 0.06, pitch 0.5, close by only.
  Also: the five ordinary pillars sink at half speed (0.25 units a tic, ~26 s); only the switch obelisk's at
  0.5 (~13 s). The script lowers each sleeve itself (level.CreateFloor) to give them their own speeds.
- 2026-11-22, note #17 (game): the switch obelisk's glow shifted towards purple (165,180,215, stone tint
  0xD0C8F0); its violet blood more pronounced: brighter (0xC020FF) and seven marks (BloodSplat1/2, the
  biggest splats, and BloodSmear, which runs down), overlapping across the face.
- 2026-11-22, note #18 (game): the switch obelisk's altar (the cacodemon's) carries a shotgun and two packs
  of 4 shells (Doom has no 2-shell pickup), in place of its health bonus. Altar items are now spread 14
  apart along the altar (two-item altars were 20 apart).
- 2026-11-22, chat: the reveal was now silent; the mapper wants a quiet, low sound. The rumble at 0.06 /
  ATTN_STATIC (turned down while the grinding was the real noise) was inaudible: now 0.2, pitch 0.5,
  ATTN_NORM, one from each sinking pillar, fading out when it stops.
- 2026-11-22, chat: the reveal rumble louder and further: 0.33, attenuation 0.5 (about twice the reach).
  Altar items scattered: each at its own spot and facing on its altar, from a hash of its gid (the same
  every build), 4 in from the edges, 12 apart.
- 2026-11-22, chat: the cacodemon is dark (STYLE_Shadow, set when the script spawns it). Altars heavier:
  15 armour bonuses (+15%) and 20 health bonuses (+20) across the hall; the stimpack, 6 clips, the shotgun
  and its 2 shell packs as before; 3 to 5 items an altar, varied, at least ~10 apart.
- 2026-11-22, note #19 (game): the 16 lip at the platform's edge (the sill under the switch; the step out at
  the bottom) as rusty metal grating, the track's tone, like a short safety step: A-GRATE (a rusty diamond
  mesh, see-through) on its face (the platform's side of niche.mouth) and its top (the niche's floor).
  Unchecked: how its holes render on a floor and a lower wall part; if wrong, the face goes to SUPPORT3.
- 2026-11-22, note #20 (game): A-GRATE failed (grey in the game, black holes, misaligned on a 16 step), and
  the lip's other face should match. Now STEPTOP (dark rusty brown, exactly 16 high) on both faces (the
  platform's side of niche.mouth; the passage's side of niche.switch, below the niche's floor) and STEP1
  (diagonal tread plate) on top.
- 2026-11-22, note #21 (game): as each pillar comes to rest, a loud thundering "whumph": the blazing door's
  slam (doors/dr2_clos, pitch 0.55, full volume) and the lift's stop clunk (plats/pt1_stop, pitch 0.5),
  from where it landed, as its rumble starts to fade.
- 2026-11-22, note #22 (game): the step's top didn't match the walls (the STEP1 tread plate is grey): now
  the track metal itself (SUPPORT3, as a floor), matching the shaft walls; STEPTOP stays on the faces.
- 2026-11-22, note #23 (game): the sheaths stop at the altars' height (-240), not the base's (-248): an 8 rim
  stays round each slab (script: floorLowerByValue to SLEEVE_REST). A sharp clack as each starts to sink
  (switches/normbutn pitch 0.8 over plats/pt1_strt pitch 0.7). The rumble at 0.5. (The splats spray once the
  sleeve is 12 below them, the lowest now 30 above the base.)
- 2026-11-22, note #24 (game): the switch niche all in the track metal (SUPPORT3) that its floor already
  had: its ceiling and its two side walls too; the switch panel (SW1GRAY) unchanged. (The bottom call
  switch's niche is unchanged.)
- 2026-11-22, chat: the obelisks' starting clack at 75% speed (pitch 0.75 on both layers; were 0.8 and 0.7).
- 2026-11-22, note #25 (game): the bottom call switch's niche kept dark, darker than the hall, so it doesn't
  draw attention: light 72 (was 176, like the top niche; the hall is 104).
- 2026-11-22, note #26 (game): the switch obelisk's glow more purple (170,110,220, stone tint 0xC8A8F0);
  the hall's fog more intense (density 360, was 280; the mouth too, it shares the hall's fog).
- 2026-11-22, notes #27, #28 (game): the altars' and the monolith bases' ceilings showed as bright patches
  (those sectors are lit 120, the hall 104). Their ceilings are now at the hall's light (lightceiling 104,
  lightceilingabsolute); floors and pickups keep 120. The bases' colour tint (lightcolor, the glow) still
  applies to their ceilings: if a tinted patch shows, that's next.
- 2026-11-22, chat: music D_ULTIMA (was D_RUNNIN; map.toml).
- 2026-11-22, chat: hints that the switch obelisk is special: a trail of violet blood on the floor (Doom's
  pools of blood and brains drawn as violet silhouettes, renderstyle addstencil, 0xC020FF), sparse from
  the aisle's middle at y ~1060, denser towards its altar, then on behind it across the walkway into the
  east gutter; the gutter cut into pieces that turn from green to violet towards it (desaturation +
  color_floor, strongest beside the obelisk). Not taken: a glow on its sleeve before the reveal, or purple
  tinges on the earlier obelisks.
- 2026-11-22, chat: the reveal is now a show watched from the elevator: 3 s after it lands and breaks,
  the obelisks reveal one at a time, nearest pair first, west then east, 2 s apart (zscript.zs
  SHOW_DELAY, SHOW_GAP); all but the switch obelisk, which reveals when the player takes the shotgun from
  its altar (thing id 300). After H (player in the hall, the elevator up again) the show starts from there.
- 2026-11-22, note #29 (game): an entry secret. Turning round at the start, a small glowing target inset
  above the start door: a lintel beam 8 out from the door's recess (ceiling 56) with a slot in its middle
  (16 wide, 8 high, 8 deep) whose back is one blue light panel (LITEBLU4, full bright, a faint pulsing
  blue light in front). Shooting it (impact line, Door_Open tag 3) opens a panel in the closet's east wall
  between its 2nd and 3rd channels (40 wide, looks like the wall, `secret` on the automap); behind it an
  alcove with light amplification goggles that count as the secret when taken (countsecret).
- 2026-11-22, note #30 (game): the blood trail "too stark": now a dark stain in the floor's grey with a
  faint violet cast (stencil 0x2A2232; was glowing violet addstencil); the pools behind the switch
  obelisk removed; a dead marine lies in front of its altar.
- 2026-11-22, chat: music D_ROMER2 (Doom II's MAP27; D_ULTIMA briefly). The obelisk show waits until the
  player is at the bottom (below z -200): riding down, 3 s after the landing; if they press the switch and
  step back (the platform goes without them), 3 s after they drop down the shaft.
- 2026-11-22, note #31 (game): the secret could be taken by walking into the shut panel (the goggles sat
  20 behind it, and pickups go by touching boxes): the alcove is 40 deep now, the goggles 36 behind the
  wall. The target is the flesh switch, SW1SKIN (SW2SKIN once shot, by the engine), scaled to a quarter to
  fit the slot (now 12 high), pegged to its top and moved to the fleshy plate; a faint red pulse (was blue).
- 2026-11-22, note #32 (game): the target the other way round: the flesh's blue eye open at first
  (SW2SKIN), closed once shot (SW1SKIN), as if the player blinded it to open the secret; the eye centred
  in the slot (scale 2, offsets 8 / 31.5 on the upper part: columns 16-48, rows 63-87 of the texture).
- 2026-11-22, note #33 (game): the eye still didn't show: UDMF per-part texture offsets are in texture
  pixels, not world units (8 / 31.5 showed rows 31-55, plain flesh). Now 16 / 63.
- 2026-11-22, note #34 (game): the eye sat low in the slot: offset y 72 (was 63).
- 2026-11-22, editor save 21:37: the east gutter's south end reshaped into a winding stream: from
  (400, 304) west along the south wall towards the mouth's corner, then north, swinging out round the
  first two east obelisks (in front of e1, between e1 and e2) and back to the wall; the first two cuts
  moved to (240, 1088) and (256, 1184) on its west side. Ported into map.py (GUTTER_E_SE, GUTTER_E_WEST).
- 2026-11-22, note #35 (game): the switch obelisk leaks violet from its back: a fall (WFALL, the blue
  waterfall, with red added: coloradd_bottom 0x500030) down the back of its sleeve, of its slab once the
  sleeve has sunk, and over its base's step; then a rivulet across the walkway into the gutter (part of
  the gutter's full-violet piece, 8 short of the base, 24 wide at its head, 45 at the gutter).
- 2026-11-22, notes #36, #37 (game): the hall's walls lifted off the floor all round (not the mouth): a gap
  16 high at their foot onto a dark channel of water (the drain: 16 deep behind every wall, floor -272,
  light 64), its grate hanging vines (MIDVINE1, the mapper's pick). The gutters now reach the walls (their
  lips gone: the west gutter's outer edge is the west wall, the east one's the east wall, the stream's
  south edge the south wall), so their water runs under the walls and out of sight.
- 2026-11-22, chat: the target is BROWNWEL's red valve wheel instead of the eye (a bullseye), unscaled in
  the 16 x 12 slot (offsets 166 / 4 round the upper wheel); it glows until shot (full bright, red pulse,
  thing id 301), then zscript.zs puts its wall back to the closet's light and turns the pulse off.
- 2026-11-22, note #38 (game): the waterfall over the whole back read as a blue wall; the violet now spills
  from a slit low on the switch obelisk's back (a sector cut 4 into the sleeve, 16 wide, 32 high from the
  base, liquid falling down its back wall), over the base's step (the 16 of its edge below the slit) into
  the rivulet, whose head now meets the base. The rest of the back is plain stone. The fall (WFALL) is in
  sectors desaturated and tinted violet (color_wall*), since coloradd on the base's walls didn't show.
  zscript.zs raises the slit's top with the sinking sleeve, so nothing of it is left standing.
- 2026-11-22, note #39 (game): the drain 96 deep behind the walls (was 16) and darker (32), so its far wall
  is out of sight past the vines.
- 2026-11-22, note #40 (game): the target's slot 16 high (ceiling 72, was 68) and the wheel moved up in it
  (offset y 5): it sat low, cut off at the bottom.
- 2026-11-22, note #41 (board): the violet water "greyed out": its colours were pale (lots of green), so
  desaturated it came out grey; now saturated violets (piece 5 and the slit 0x8A10FF).
- 2026-11-22, note #42 (game): once the switch obelisk's sleeve had sunk, the slit's walls showed as liquid
  up in the ceiling slot: now only its back wall's lower part is the fall; the rest is the slot's dark
  marble (light -88, ceiling dark too).
- 2026-11-22, note #43 (game): the leak vanished on the base's floor between the slit and the base's edge:
  now a strip of the same violet liquid (the spill, 8 x 16) runs across the base from the slit's mouth to
  the edge, where it falls into the rivulet.
- 2026-11-22, note #44 (game): the lifted wall, drain and vines only where the water runs out: behind the
  west gutter's stretch of the west wall, and the east gutter's stretches of the east and south walls
  (two drains, closed off at their ends); plain walls everywhere else.
- 2026-11-22, note #45 (game): the great door at the end of the hall, in the apse's middle wall: a
  192-wide doorway, 128 high under a marble lintel, its two carved leaves (BIGDOOR7, solid, 12 thick)
  stuck ajar, half ruined (swung in 12 and 20 degrees), a gap of about 15 between them to glimpse the
  vestibule beyond (256 x 176, dim, a red glow at its back), too narrow to pass. A small door (WOODMET1,
  64 x 128, Door_Raise, usable from both sides) set into the left leaf is the way on. Beyond the
  vestibule: nothing yet.
- 2026-11-22, note #46 (board): the west gutter meanders like the east stream: its inner edge swings in
  towards the row between the obelisks and out beside them (GUTTER_W_INNER).
- 2026-11-22, note #47 (game): both channels join in front of the elevator's landing: the west gutter runs
  round the south-west corner along the south wall (to x -72, west of the mouth) and a channel (y 270-327)
  crosses the aisle to the east stream. A low marble bridge over it (x -40 to 104), a step up (the
  bases' height), a 3D floor (Sector_Set3DFloor from a control sector outside the map, tag 500), so the
  water runs on beneath it.
- 2026-11-22, notes #48-50 (game): the great door's leaves closer (swung 5 and 8 degrees, were 12 and 20:
  a gap of about 7); BIGDOOR7's skull pile centred on each leaf (offsets worked out per stretch); the
  small door human-sized (64 x 72), the leaf going on above it as a lintel: its panel (WOODMET1) sinks
  into the floor when used and comes back up after 3 s (Plat_DownWaitUpStay, tag 501), from either side.
- 2026-11-22, note #51 (game): the switch obelisk's back had lost its alignment with the others once split
  round the slit: each piece now carries the marble on from the last (x offsets), and the stretch above
  the slit (an upper part, pegged to the top) is moved to match the lower parts beside it.
- 2026-11-22, note #52 (game): bars under the bridge deck's open sides (MIDBARS3 squeezed to the 12 from
  the water to the slab, pegged to the water), so it doesn't seem to hover; the water shows through.
- 2026-11-22, note #53 (game): the left leaf plain (BIGDOOR5, wood and iron bands, no skulls), the right
  keeps BIGDOOR7's skulls; the small door a brass-framed metal door (DOOR1, exactly 64 x 72) so it reads
  as a door, not part of the leaf.
- 2026-11-22, note #54 (game): the strip of the switch obelisk's back above the slit came out grey: it's
  drawn by the sector in front of the slit, and the spill is desaturated for its liquid. A lip 1 wide
  (marble floor, lit and tinted like the base) now stands between the slit and the spill and draws it.
- 2026-11-22, note #55 (game): bars all round the bridge: on its ends over the bank too (filling the 4
  between the bank's floor and the slab; MIDBARS3 squeezed, pegged to the higher floor).
- 2026-11-22, note #56 (game): the wall above the drain's grate stood out from the plain wall beside it:
  it was pegged from the gap's top (now dontpegtop: from the ceiling, like the plain walls) and tinted
  violet by the gutter pieces' wall colours (dropped: only their floors are tinted; GRAY1 is grey, so
  their desaturation doesn't show). The fall over the switch obelisk's step keeps its violet with its own
  sidedef colours (useowncolors_bottom).
- 2026-11-22, note #57 (game): the small door BIGDOOR6 (wood and iron, one skull; was DOOR1), the skull
  centred on its 64 x 72 panel (per-part offsets on the lower part, which add to the side's own offset).
- 2026-11-22, note #58 (game): the small door set back into the left leaf in its own rusted metal frame:
  a recess 4 deep, 4 wider each side and 4 taller than the door, lined with SUPPORT3; the door at its
  back, posts of the frame either side of it through the rest of the leaf. (The leaf's pieces are built
  from one table of edges in the leaf's own coordinates, so neighbours share their lines.)
- 2026-11-22, note #59 (game): two imps waiting behind the great doors, facing them (ambush).
- 2026-11-22, note #60 (game): build #84 had the small door in plain SUPPORT3 and without its special (a
  bug in the build script); since build #85 the door is BIGDOOR6 (skull centred) in its SUPPORT3 frame,
  and opens.
- 2026-11-22, note #61 (game): a lost soul hidden high up (96 above the floor) behind the 2nd west obelisk
  (x -160, y 810), out of sight from the aisle's south end until that pillar sinks; ambush.
- 2026-11-22, note #62 (game): shooting one imp through the gap left the other asleep (they were ambush:
  deaf); ambush off, so gunfire wakes both.
- 2026-11-22, note #63 (game): through the small door, a cramped passage of mossy stone (A-MOSRK2 on
  walls, floor and ceiling; 64 wide, 88 high, light 80) leaves the vestibule (now 224 x 96, the imps in
  it) on the right, bends north and twists, stepping up 8 at a time from its 3rd piece; short red torches
  (57) in niches in its walls (24 wide, 12 deep, sill 24). It ends at a wall for now (PASSAGE in map.py).
- 2026-11-22, note #64 (game): the imps couldn't open the small door once woken: its faces are monsteruse
  now, so monsters open it too.
- 2026-11-22, note #65 (game): the passage goes on, twisting east and then back south along the hall's
  north-east side (towards the first room), its pieces longer, wider (to about 160) and taller (16 more
  each from piece 9) so it opens out; the floor rises to piece 12, then levels; more torch niches; three
  pinkies in the wide stretch, two imps behind them, facing back up the passage. Ends at a wall for now.
- 2026-11-22, note #66 (game): a pinky couldn't get through the passage's first stretch (58-64 wide; it
  needs 60): every cross-section widened about its middle to at least 88 (the opening onto the vestibule
  76).
- 2026-11-22, note #67 (game): two pinkies were wedged side by side in one piece: now one pinky a piece
  (pieces 12, 13, 14), the imps behind them.
- 2026-11-22, note #68 (game): still too tight for pinkies at the bends (88): every cross-section at least
  128 now. Monsters must be able to path to the player (docs/map-design-notes.md); Doom's move in 8
  directions and catch on tight bends, so a 60-wide pinky wants about twice its width.
- 2026-11-22, note #69 (game): a box of shotgun shells (20) by the right-hand wall just into the passage
  (PASSAGE_ITEMS).
- 2026-11-22, note #70 (game): pinkies still stopped at a bend. Likely the torch niches: a sill 24 up and
  only 48 high (a monster brushing the mouth found too little headroom), the torch sticking out of the
  12-deep niche, one on a bend's inside corner. Now the niches start at the floor, 72 high, 24 deep, the
  torch 14 in (wholly inside), and the torches are on the outsides of the bends. Unverified: if they
  still stick, the next suspect is the hairpin's sharp inside corner (r12).
- 2026-11-22, note #71 (game): 20 more shells across the obelisk altars: a pack of 4 on e1, w2, e3, e4 and
  w6 (those with the fewest items).
- 2026-11-22, note #72 (game): a pinky couldn't follow into the vestibule (a 76 opening beside the right
  leaf's hinge, then a tight turn): the vestibule ballooned out, twice as deep (to about 208), rounded,
  its north-east side curving back down to a wide, slanted opening onto the passage (about 122).
- 2026-11-22, note #73 (editor): the shell cache was the wrong thing (2048 is a box of bullets; a box of
  20 shells is 2049) and on the floor: now 2049 on a shelf in a niche in the passage's right wall (its
  2nd piece: the 1st's right wall runs right against the hall's), 32 wide, 16 deep, 32 up, 40 high, the
  box 8 in so it can be taken from the passage (PASSAGE_SHELVES).
- 2026-11-22, note #74 (game): the entry secret holds partial invisibility (2024) instead of the light
  amplification goggles (still counts as the secret).
- 2026-11-22, note #75 (game): the fog stopped abruptly at the passage: the hall's fog now thins out over the
  passage's first six pieces (density 309 down to 51), then none.
- 2026-11-22, note #76 (game): the shell shelf wider (48), deeper (24) and lower (24 high), lit (and fogged)
  as the passage piece it opens off.
- 2026-11-22, note #77 (editor) and editor save 22:36: the passage leads down instead of on up: it rises
  to its 10th piece, then goes down 16 a piece, and from its 15th section four steps go on down south to
  a cistern, the big room the mapper drew east of the hall (x about 510-832, y 170-1760): floor -320
  (flooded, NUKAGE), ceiling -128, light 40, very foggy (0x101810, 420). Its west wall is the far side of
  the drain behind the hall's east wall: water pouring down it (SFALL) above and below the slot through
  the drain (32 high), and through the slot and the vines the player looks up into the obelisk hall.
  (A first version made the drain itself the cistern; replaced by the mapper's shape.) Two property
  tweaks from the save went to overrides.toml under drain_2.back_3/back_6, lines that no longer exist
  (now cistern.wall_w_*): they do nothing; the file can go.
- 2026-11-22, note #78 (game): looking down through the vines, the drain (the hall's grey fog) showed a seam
  against the cistern's dark fog beyond: both drains now have the cistern's light (40) and dark fog, so the
  water fades uniformly into darkness.
- 2026-11-22, note #79 (game): the mapper prefers the grey: the drains, the cistern and the stairs down now use
  the hall's grey fog (0x50585C, 360; the near-black one looked wrong from afar), the drains and the cistern
  at the same light (40), so through the grate it fades uniformly to grey. To check from below next.
- 2026-11-22, note #80 (game): the 2nd pinky moved up to the passage's peak (piece 9, passage_10, where it
  starts down), away from the third pinky and the imps.
- 2026-11-22, note #81 (game): from the cistern the hall showed through some gaps clear and others through
  vines: the vines were only on the gutter side of the grate lines (a middle texture is drawn per side);
  now on both sides, so it's always seen through vines.
- 2026-11-22, note #82 (game): three spectres (shadow pinkies, 58), ambush, along the cistern (y 1350, 880,
  430), facing north, the way the player comes down.
- 2026-11-22, note #83 (game): the grate lines block monster sight (blocksight), so the cistern's ambush
  spectres can't see the player in the hall through the vines.
- 2026-11-22, note #84 (game): the cistern (and the stairs down) darker and less foggy: near-black fog
  (0x080808, 200), light 32, so the spectres don't stand out against grey mist. The drains keep the hall's
  grey (note #79); to watch for a seam where the two meet, seen from the hall.
- 2026-11-23, editor save 13:35: the hidden lost soul behind the 2nd west obelisk (note #61) removed. Ported
  into map.py. (The 26 "moved" lines pull listed with it were the editor rounding coordinates to 3
  decimals; pull now ignores differences that small.)
- 2026-11-23, note #1 (game; note numbers start again from 1 today): the small door slides up instead of
  sinking into the floor: a real door sector (Door_Raise, tag 501, both sides, monsters too), 4 thick,
  between the frame in front and a recess of the same height behind it (great_door.wicket_back), so only
  the door's own height shows from either side and the leaf above stays put. Its face is now an upper
  texture hung from the door's underside (BIGDOOR6, offsets 32 / -14).
- 2026-11-23, note #2 (game): the wall above the great door didn't match the walls round it (a marble
  lintel): now the hall's GRAY1, hung from the ceiling and carried on from the wall on its left.
- 2026-11-23, note #3 (game): the vestibule in the passage's style: A-MOSRK2 on its walls, floor and
  ceiling. The jambs (in the hall wall's thickness) stay grey; its light (72) and fog are unchanged.
- 2026-11-23, note #4 (game): the blank wall on the way down (passage_13, left) has a big carving set into
  it: the green marble skull (MARBFACE, 128 x 128) at the back of a marble alcove (128 wide, 24 deep, sill
  32 up, light 112), the sill a shelf with two stimpacks (PASSAGE_CARVINGS). Unchecked in the game: the
  face's light, and whether the stimpacks can be taken from the passage (the shell shelf works the same way).
- 2026-11-23, note #5 (game): the skull carving looked "too significant": now a patterned marble panel with
  no face (MARBLE3) and dimmer (light 96, was 112), plainly decorative. Unchecked: how Freedoom's MARBLE3
  reads in the game; the mapper can pick another in the asset browser.
- 2026-11-23, note #6 (game): the shell shelf in the passage as a wooden box set into the stone: WOOD1 on its
  back and sides, FLAT5_2 on its shelf and top; the stone face above and below its mouth is unchanged.
- 2026-11-23, note #7 (game): the cistern a little brighter (light 48, was 32; fog unchanged); six dim
  pale-green lights along its east wall (PointLightAttenuated, every 250 from y 1650 to 400, 20 out from the
  wall, 40 above the water, radius 104/88 alternating) so a spectre crossing in front shows as a shadow;
  the two southern spectres further south (y 760 and 270, were 880 and 430), the northern one as it was.
  The lights have no fixture (they read as a glow off the water); to check: whether they want one, and
  whether the spectres still hide well enough at 48.
- 2026-11-23, note #8 (game): the wooden niche looked "painted on stone": it now sits in a wooden frame, a
  wood-lined recess 6 wider all round than the box and 4 deep (passage_2.wall_r.shelf_frame, SHELF_FRAME),
  the box opening in its back and 24 darker inside; the shells 10 into the box. A ridge standing out from
  the wall wasn't possible (it would have to run floor to ceiling). Unchecked: that the shells can still
  be taken from the passage (they are 14 behind the wall now, were 12).
- 2026-11-23, note #9 (game): gunfire in the hall woke every pinky in the passage (sound carries through all
  open two-sided lines, so "further back" wouldn't help). Now the two steps after the first pinky's piece
  block sound (passage_11.step, passage_12.step: sound passes one such line and stops at the second), so
  that pinky still comes and the pinkies and imps from passage_12 on only hear shots fired past them; the
  way round through the drain is closed the same way (the vine grates and the cistern's west wall are
  blocksound). A third imp, deaf (ambush), in the vestibule's back corner behind the left leaf
  (vestibule.imp_ambush). Unchecked in the game.
- 2026-11-23, note #10 (game): the mapper's pick for the alcove: GSTSATYR, one face only. The texture is 64
  wide, so it takes the middle 64 of the 128-wide back wall, with plain GSTONE1 either side (its blocks
  carried on across the three stretches by x offsets 224 / 0 / 64) and on the alcove's sides; sill and
  top stay FLOOR7_2, light 96. Unchecked: whether the stone's courses line up across the face's edges
  in Freedoom's versions of these textures, and whether the marble sill still suits it.
- 2026-11-23, note #11 (board): the cistern's spectres "hard of seeing" too: asleep until touched or hurt,
  so a careful player can skirt round them. Doom has no such flag (dormant monsters can't be hurt), so
  zscript.zs has CacobeliskSleeper, a spectre whose idle state never looks or listens; damage wakes it
  as it does any monster, and its Tick wakes it when a player comes within 8 of touching it. The
  handler CacobeliskSleepers swaps the map's spectres (thing id 310, SLEEPER_TID) for it when the level
  loads (the log says "[DMS] CacobeliskSleepers: 3 spectre(s) asleep"). Compiles; unchecked in the game:
  that they stay asleep when shot past, wake on a touch, and that the kill count still reads right.
- 2026-11-23, note #12 (game): the switch obelisk's cacodemon asleep too, a shadow up there until the
  player alerts it. zscript.zs spawns CacobeliskDozer instead: it never looks (walking up to it doesn't
  wake it); it wakes when hurt, or when it hears the player make noise after it appeared (gunfire in the
  hall; shots fired before the obelisk's reveal don't count). Claude's reading of "alerts": noise or
  damage, not sight. Compiles; unchecked in the game.
- 2026-11-23, note #13 (game): a torch (short red, like the passage's) in a niche in the vestibule's wall
  (vestibule.wall_2, the back-left one: 24 wide, 24 deep, 72 high), to explain the room's red glow: the
  glow light moved from mid-room to just in front of the torch (radius 144, was 112). The deaf imp
  (note #9) stands about 36 in front of it. Unchecked in the game.
- 2026-11-23, note #15 (game): the waterfall on the cistern's west wall showed above the drain's slot as
  well as below: now only below (it runs out of the drain and down); above it, the mossy stone. **Open:**
  the same note says "gutter violet 5 can be removed I believe" (gutter_e.violet_5, the east gutter's
  north end, y 1670-1760, past the switch obelisk): untouched; asked whether to remove that stretch of
  gutter (and its drain, which the cistern's west wall follows) or only its violet tint.
- 2026-11-23, note #16 (game): the cistern's roof raised out of sight: ceiling 256 (576 above the water;
  was -128, 192). Unchecked: that it really fades into the dark at light 48, and how the tall stone
  above the slot reads.
- 2026-11-23, note #17 (game): at the cistern's south end, a waterlogged wooden platform: an island
  (x 590-770, y 216-376) just clear of the walls, its boards (FLAT5_2, WOOD1 edges) 4 above the water; on
  it a dais (96 x 96, 12 up) and at the dais's back a wooden post (64 x 16, 48 high) with the switch
  (SW1WOOD, rows 64-112) on its north face. **The switch does nothing yet: what it does is the mapper's
  to say** (it would also answer "where the cistern leads"). "Can we choose water flow direction?": yes:
  Scroll_Floor on cistern.wall_s (tag 600; CISTERN_FLOW = (0, -8): the picture drifts south, about 9 units
  a second, the player isn't carried). Unchecked in the game: the drift's direction and speed, and that
  the switch's ring shows whole on the post. The 3rd spectre moved from the platform's spot to (624, 436).
- 2026-11-23, note #18 (game): the water flows away from the obelisk hall, slow and lazy (0.12 units a tic):
  the west gutter and its drain west (tag 610), the east gutter, its violet pieces, its drain and the
  cistern east (611; the cistern 600), parting under the bridge (the bridge's own water is still). The
  cistern's water leaves through a new low slot along its east wall (cistern.out: 20 high, a dark channel
  96 deep behind). The dais switch (Light_ChangeToValue 96 on the platform, dais and post, tag 601, so
  using it shows) turns the cistern's water south at 0.2. Done by zscript.zs CacobeliskWater, which
  shifts the floors' texture offsets each tic (the player isn't carried); note #17's Scroll_Floor line is
  gone. The mapper wrote "west" for the east drain and the cistern as well; Claude read "away from the
  obelisk room" as east on that side. Two builds of this had a script that didn't compile (a constant
  TURNED beside a variable turned: names ignore case, again; and AddXOffset takes two arguments).
  Unchecked in the game: each direction (a sign error would show as water running towards the hall).
- 2026-11-23, note #19 (game): dim candlelight on the dais ("small torches, if possible"): two candles (34)
  either side of the switch post; they don't block, and UZDoom's lights.pk3 gives them their glow. The
  short torches (55-57) are the alternative if candles are too faint.
- 2026-11-23, note #20 (game): the dais sits up on a grating, like the bridge over the hall's channel: the
  platform is now a metal grate (FCGRATE2, a 3D floor 12-16 above the water, tag 602, control sector
  cistern_grate_control outside the map) on bars (MIDBARS3), the water beneath it; the wooden dais (8
  above the grate) and the post rise through it. The wooden boards of note #17 are gone (only the dais
  and post are wood). The switch's light change now covers the dais and post only.
- 2026-11-23, note #22 (board): the answer to note #15's open question: both gutters plain green; no
  violet in the east gutter any more (all six pieces untinted; they keep their gids gutter_e.violet_N).
  The rivulet from the switch obelisk across the walkway is part of the gutter's piece 4, so it is green
  too; the obelisk's own leak (the violet fall from its slit and the spill on its base) is unchanged.
  **Open:** whether that leak should stay violet, now that it runs into green water, or go as well.
- 2026-11-23, note #23 (board): the cistern's east drain (cistern.out) has the hall drains' vine grating
  (MIDVINE1 on both sides of its slot), and its water carries the cistern's tag (600), so it turns south
  with the cistern's at the switch.
- 2026-11-23, note #24 (game): the candles forward of the post (y 288, 24 in front of the switch face, at its
  two edges; were beside the post at y 256), so their light falls on the switch.
- 2026-11-23, note #25 (board): violet after all (the answer to note #22's open question), but only where
  the leak meets the gutter: the rivulet across the walkway is a sector of its own again, full violet
  (gutter_e.violet_4.rivulet), and in the gutter in front of its mouth the violet spreads and fades in
  four concentric rings (round islands, radii 44, 31, 18, 8 round (394, 1557), from a faint tint to full
  violet: VIOLET_RINGS). The rest of the gutter is green. The rings are still (they flow east with the
  gutter's water); making them pulse outwards would be a script. Unchecked in the game.
- 2026-11-23, note #26 (game): "can the current actually move you?": yes, and it does once the switch is
  used: zscript.zs CacobeliskWater pushes a player standing in the cistern's water south (0.18 a tic,
  settling at about 2 units a tic, a quarter of walking speed; not on the grate or the dais, and not
  monsters). Before the switch the water only looks as if it moves. Unchecked: the strength.
- 2026-11-23, note #27 (game): "fix up the leak: bits missing the water texture, bits wrongly tinted". No
  screenshot reached Claude (see below), so two faults found by reading the map: the rivulet's sunken
  channel had marble banks drawn by the rivulet's own (desaturated) sector, so they came out grey: the
  rivulet is now flush with the walkway (a film across the floor) and falls the 8 into the gutter at its
  mouth (WFALL, violet); and the 1-wide lip between the slit and the spill was marble: now liquid
  (FWATER1 tinted violet; it can't be desaturated). **To check with the mapper: whether these were the
  bits meant.** Tooling: note screenshots had not been saved since the map was renamed: the game was
  given build\cacobelisk\shots, and in a console command "\c" plus a letter is a colour code
  ("buildcobelisk/shots"): launch.py passes the folder with forward slashes now (needs the board
  restarted, since the board starts the game on H).
- 2026-11-23, note #28 (game): the bit of channel east of the bridge flowed west (it was part of the west
  gutter's sector). The mapper's rule: east of the bridge flows east. It is its own sector now
  (gutter_w.east_of_bridge, tag 611), and the water under the bridge is two halves parting at its middle
  (x 32): gutter_w.bridge (tag 500 + moreids 610, west) and gutter_w.bridge_e (500 + moreids 611, east).
  Unchecked: that the script's tag search finds the second tags (moreids), i.e. that the water under
  the bridge moves at all.
- 2026-11-23, note #29 (game): "a sliver of blue water" at the leak: the lip of note #27, blue water tinted
  violet, stayed blue (a tint only takes colour away). Its floor is a plain grey flat (FLAT19) tinted violet
  now; 1 wide, so its not moving does not show.
- 2026-11-23, note #30 (game): the rings spread from the point of entry: four half rings centred on the
  middle of the rivulet's mouth on the gutter's west edge (radii 66, 52, 38, 26; they were whole circles
  out in the gutter). The innermost holds the mouth, so the fall there is drawn by a desaturated sector
  and is violet (it was blue: "blue water at delta"). map.py _leak_side.
- 2026-11-23, note #31 (game): the lip's strip "far too bright; the whole leak the same colour": its violet
  scaled to the liquid's brightness (0x2E0555: FLAT19 is three times as light as desaturated NUKAGE1).
  Measured from the textures, not seen: to check in the game.
- 2026-11-23, note #32 (game): the shadow cacodemon deaf to gunshots too, like the cistern's spectres: it
  wakes only when hurt or touched (it no longer wakes on hearing the player; note #12's reading of
  "alerts" was noise or damage). It sits on top of the obelisk, so in practice: when shot.
- 2026-11-23, note #33 (game): "still a bright violet stripe": darkening the tint (note #31) did not help,
  probably because the light flat (FLAT19) still caught the obelisk's pulsing light. The lip is now CEIL5_1, a
  neutral flat as dark as the desaturated liquid (38 against 35), with the full VIOLET tint like the spill.
  LIP_VIOLET is unused. Still not seen by Claude (no screenshots until the board is restarted).
- 2026-11-23, note #34 (game): the elevator's switches are shut away once used, so it's plain they are a
  one-time thing. A second after either is used: the bottom call niche's sill rises to its top (tag 4,
  Floor_RaiseByValue 32), its face (SUPPORT3, the track's metal; it shows as a metal sill before use)
  being the panel; the top switch's niche is the way down and can't shut, so its plate is replaced by
  the niche's own metal (looking up from the bottom, no switch is left). zscript.zs ShutSwitches.
  Compiles; unchecked in the game.
- 2026-11-23, note #35 (game): once the secret's target (the valve wheel over the start door) is shot, a
  block drops over it: the slot's ceiling comes down 16 to the beam's height (Ceiling_LowerByValue on the
  slot's second tag, 5), leaving the lintel one plain beam. Compiles; unchecked in the game (the face
  that covers the slot is the line's default wall texture, as on the beams beside it).
- 2026-11-23, note #36 (game): the top switch must not just vanish (note #34 swapped its plate for metal):
  a panel comes down in front of it and its pulsing light goes out. The last 2 of the niche in front of
  the switch is its own sector (niche.shutter, tags 1 and 6): a second after a switch is used its ceiling
  comes down from the niche's top to its sill, the panel (AQF049, the mapper's pick, a flat used on a
  wall) riding down with it over the switch's window; the way through below stays open. The validator
  may not know a flat as a wall texture: see the build's warnings. Compiles; unchecked in the game.
- 2026-11-23, note #37 (game): the bottom niche's panel ran all the way down the wall (the rising sill's
  face): now a shutter like the top one: the last 2 of the niche in front of the switch is its own sector
  (mouth.call_niche.shutter, tag 4) whose ceiling comes down, the panel (AQF049) inside the niche only.
- 2026-11-23, note #38 (game): "why does my hand turn black and white in the purple water?": the violet is
  made by desaturating the sector and tinting its floor, and desaturation takes everything drawn in that
  sector, the weapon in the player's hand included. **Open (offered):** the cure is violet flats of our
  own (the green liquid recoloured in a TEXTURES lump packed with the map, with ANIMDEFS for its
  animation), which needs `dms build` to pack those lumps; then no sector is desaturated.
- 2026-11-23, note #39 (game): a little cloud of dust when the secret panel opens: ten pale, see-through
  puffs (the bullet puff's smoke, bigger: zscript.zs CacobeliskDust) thrown out of the panel towards the
  closet's middle, slowing and fading over about two seconds. Compiles; unchecked in the game.
- 2026-11-23, note #40 (game): the panels snap shut at once (no delay, 8 units a tic; was a second later).
- 2026-11-23, note #41 (game): the cistern's switch slowly opens a big wooden door (BIGDOOR6, 112 wide, 84
  high, about 5 s) in the west wall of the stairs down (their 2nd flight), the way forward. Behind it a
  chamber (144 x 160, mossy stone, lit red) with two shotgunners facing the door and a red light that
  comes on as the door starts to open (dormant before: thing id 303). The door is the switch's own
  special (Door_Open, tag 7), so the movement check follows it; zscript.zs does the dais light, the
  water's turn and the glow. **Open:** what lies beyond the chamber (it's a dead end), i.e. the exit.
  The current after the switch pushes the player south, away from the door: to check that it reads right.
- 2026-11-23, note #42 (game): the top switch was "shoved down" with the panel: its plate hung from the
  ceiling in front of it, now the shutter's. Both switches are anchored to something that doesn't move
  (the top one to the mouth's ceiling behind it, the bottom one to its floor), offsets worked out so the
  plate sits in the niche's window as before (53 and -27). Unchecked: that the plates are where they were.
- 2026-11-23, note #43 (game): the bottom niche's panel is AQF074 (the mapper's pick; AQF049 "isn't quite a
  fit" there). The top switch's panel stays AQF049 until the mapper says otherwise.
- 2026-11-23, notes #44, #45 (game): the two switches are twins. Both windows are 32 wide (the panel
  texture's one 32 x 32 tile, and SW1GRAY's plate): the bottom niche narrowed from 37.7; the top niche,
  which must stay 48 wide below as the way through, has a cheek of track metal either side of a 32-wide
  window (niche.cheek_w/e: sectors shut down to the sill until their floors drop with the platform).
  Both panels are AQF074. No cement: the top switch's grey margins are behind the cheeks, and the bottom
  niche's sides, floor and ceiling are the track's metal like the top one's. Unchecked in the game.
- 2026-11-23, note #46 (game): the hall's bridge is wooden (boards FLAT5_2 top and underneath, WOOD1 edges;
  it was marble), "similar to the waterlogged platform down in the cistern": that platform has been a
  metal grate since note #20, with only its dais and post in wood. **Open:** whether the cistern's
  platform should be wooden boards too (one visual language), or stay a grate.
  The cheeks of the top switch's niche (note #44) are user_scenery: the movement check took them for
  gaps too narrow to pass; it now reads the way through at the shaft's foot as 32 wide and warns that
  imps and shotgunners can't follow there (they can: it is 48).
- 2026-11-23, note #47 (game): the answer to note #46: the cistern's platform is wooden boards too (FLAT5_2,
  WOOD1 edges; it was a metal grate), with the metal bars (MIDBARS3) only underneath, where it meets the water.
- 2026-11-23, note #48 (game): the big door is in the opposite (east) wall of the stairs' 2nd flight, its
  chamber east of the stairs (192 x 192). Six shotgunners: two set on the player the moment the switch is
  used (thing id 304, zscript.zs), two ordinary, two deaf (ambush) in the corners beside the door. The
  roused two wait behind the door for the 5 s it takes to open. Compiles; unchecked in the game.
- 2026-11-23, note #49 (game): riding down, the wall under the top switch showed cement where the track
  should be: that wall is the switch's own texture (SW1GRAY: the plate, cement round it) all the way
  down. Once the panel has covered the plate (8 tics after the switch is used), zscript.zs turns that
  wall to the track's metal (SUPPORT3). Compiles; unchecked in the game.
- 2026-11-23, note #50 (game): a green armour (2018) behind the switch, on the platform's boards behind the
  dais at (680, 228), hidden by the post from the north. Unchecked: that it stands on the boards (a 3D
  floor) rather than in the water under them.
- 2026-11-23, note #51 (game): the armour was sunk into the boards: a thing on a 3D floor spawns on the
  sector's real floor (the water's) unless given a height. It has height 16 (the boards' top) now. A
  lesson for anything else put on the bridge or this platform.
- 2026-11-23, note #52 (game): trying the big door by hand, before the switch has been used, shows "This
  door is opened elsewhere." with the "can't use that" grunt: zscript.zs TryBigDoor watches for a use
  press within 100 of the door's middle, facing it (the door's own lines carry no special). Compiles;
  unchecked in the game.
- 2026-11-23, note #53 (board): the big door moved down to the stairs' 3rd flight (east wall), and its
  chamber about twice as big and less boxy: an irregular nine-sided room about 330 x 280
  (CISTERN_DOOR_OUTLINE), the six shotgunners spread through it (the deaf two still in the corners
  beside the door).
- 2026-11-23, note #54 (game): the track metal turned 90 degrees, as one strip 16 high all round the foot of
  the start closet's walls and the elevator car's; below the starting floor the shaft's walls are the
  upright track as before. The game has no turned texture, so the map has its own now
  (maps/cacobelisk/textures.txt, packed as TEXTURES: a new dms feature, src/dms/extras.py): CACOBASE
  (GRAY1 with the strip in its bottom rows; on every plain wall of the closet and its coffer, stood on
  the floor, and on the secret panel's face) and CACOSHFT (the strip, then 256 of upright track; the
  car's side walls and the blocks' foot on the closet's north wall). The light channels and the start
  door's recess interrupt the strip. Needs the board restarted (it starts the game, and the game's
  copy of the map must carry the new lump). Unchecked in the game: everything about how it looks.
- 2026-11-23, note #55 (game): the floor through the small door (its frame, the door's own floor, the
  recess behind) is a slight wooden step: 4 up, boards (FLAT5_2), wood risers; it was the default grey
  floor. The door is still 72 high above the step.
- 2026-11-23, note #56 (game): "something is fucked about this texturing": the closet's walls showed as
  missing textures: the board, still running its code from before today's changes, restarted the game
  with a copy of the map that lacked the new TEXTURES lump (the log: "Unknown middle texture
  'CACOBASE'"). Nothing wrong in the map; the board has to be restarted.
- 2026-11-23, note #57 (game): no turning: the track as it is, a strip along the foot of the walls all round,
  consistent with what shows round the car. CACOBASE is now GRAY1 with SUPPORT3's top 16 rows at its foot
  (the rows the car's walls show); CACOSHFT is gone (the shaft's walls are plain SUPPORT3 again). It is
  still the map's own texture: the closet's walls are single surfaces, and a strip on them without one
  would mean lining every wall with a block as the shaft's are, which the light channels get in the way
  of. So the board restart is still needed.
- 2026-11-23, note #58 (game): no more hexagon tiles in the hall: its floor, and the landing's, is dirt
  (FLAT10), carried on down the shallow banks to the water (the 8-high faces along both gutters, the
  crossing channel and the rivulet's mouth were marble). The obelisks' bases and altars stay marble; the
  rivulet, flush with the floor, is unchanged. Rocky alternatives if dirt isn't it: RROCK01-19.
- 2026-11-23, note #59 (game): the hall is open to the sky: SKY4 (Freedoom's dark starfield with a green
  nebula; map.toml), its walls 384 high (ceiling 128, was -64). Every sector in the hall takes the sky
  (the gutters, bases, altars, bridge), and the obelisks' sleeves and slabs too: there is no slot in a
  ceiling any more, a sleeve is a free-standing pillar until it sinks. The landing (mouth) keeps its
  low ceiling. Unchecked in the game: the fog against the sky, the tall walls' look, and the reveal
  (the cacodemon is still hidden inside its sleeve, but now open from above).
- 2026-11-23, note #61 (game): no skulls on the inside of the great door: the right leaf's back, seen from
  the vestibule, is plain wood and iron (BIGDOOR5) like the left leaf; its face towards the hall keeps
  the skulls (BIGDOOR7).
- 2026-11-23, note #62 (game): the current (after the switch) carries enemies too: every monster that is
  awake and every body standing or lying in the cistern's water is pushed south like the player. Not a
  monster still asleep (a sleeping spectre drifting into the player would spoil skirting round it), nor
  flyers. Compiles; unchecked in the game.
- 2026-11-23, note #63 (game): the big door's floor is a slight wooden step too (4 up, boards, wood risers),
  like the small door's. A pattern now: doors stand on a wooden sill.
- 2026-11-23, note #64 (game): the start's cement "feeling odd": the closet's, car's and shaft blocks' grey
  walls are PIPEWAL1 (Freedoom's green wall of rusty pipes and conduits), in CACOBASE above the track
  strip too. Not changed: the light channels, the start door, the switch's niche, the wall below the
  starting floor (track). The secret panel takes it with the walls round it.
- 2026-11-23, editor save 15:59: the northmost cistern spectre (cistern.spectre_1) removed. Ported into
  map.py: two sleeping spectres are left (y 760 and 436).
- 2026-11-23, chat: the start closet's walls are METAL4 (the mapper's pick, in place of PIPEWAL1 from note #64):
  CLOSET_SKIN in map.py and the wall in CACOBASE (textures.txt).
- 2026-11-23, note #65 (game): the sky "like 50% greener": the map's own sky texture CACOSKY (textures.txt):
  SKY4 with its red and blue halved (Blend "80FF80"), so the stars and nebula go green and black stays
  black. map.toml sky = "CACOSKY". The tint is one number to change if it wants more or less.
- 2026-11-23, note #66 (game, with a screenshot): the grey fog made flat grey walls against the black sky.
  The hall's fog is now a near-black green (0x0A160E) and thinner (240, was 360 grey): the walls fade
  into darkness, as the sky does, instead of into mist. The drains and the passage's first pieces, which
  share the hall's fog, go dark with it. Not done (offered): brightness stepping up the walls towards
  the sky, or tinting the sky to the old grey. To check: that the hall isn't simply too dark now.
- 2026-11-23, note #67 (game): the walls stuck up too high into the sky: the hall's walls are 256 high now
  (sky at 0; they were 384). No lower: the obelisks' pillars reach 240 (to -16) before they sink.
- 2026-11-23, note #68 (game, screenshot): stepping out of the elevator: no bridge. One big sheet of stone
  (sector "landing", green marble FLOOR7_2, 8 above the dirt) from the foot of the elevator (the mouth's
  floor is part of it) out over where the channel crossed, x -40 to 104, to 18 past the channel's north
  bank; the water comes out from under it on either side (west: the west gutter's channel; east: the
  stretch to the east stream), and the player steps down off its lip into the row of obelisks. The
  wooden bridge, its bars and its control sector are gone (notes #47, #52, #55, #28, #46). The dirt of
  note #58 no longer covers the mouth.
- 2026-11-23, note #69 (game, screenshot): "huge powerful slightly ruined stone" for the tall walls: STONE3
  (grey blocks, cracked and mossy) at twice its size on every grey surface of the hall, its gutters,
  the landing and the mouth. Looked at and passed over: BIGBRIK2 (huge dark blocks, not ruined), STONEW5,
  A-MOSBRI, A-BROCK2. Unchecked: seams where wall stretches meet (their offsets were set for the
  unscaled grey), and how the mouth's low walls take the big blocks.
- 2026-11-23, note #70 (game): the sky from SKY3 (the mapper's "p-sky3": red clouds on black), darkened and
  tinted all green: CACOSKY is now those clouds through the engine's Green translation at 60% over black.
  Unchecked in the game (the engine loads it); the darkness is the Alpha value in textures.txt.
- 2026-11-23, note #70 (game): settled as P-SKY3 (the mapper's "p-sky3", 512 x 128) through the engine's
  Green translation, not darkened further. Getting there broke the map for a few minutes: sky variants
  the engine rejected were tried on the live map, and the mapper's `dms play` met one (and a race with
  Claude's own script check, a traceback). Lessons: a Blend colour made only of digits ("808080") is
  read as a number: write "#808080"; try texture variants on a scratch map, not the one being played;
  the "hidden" script check's error window is not hidden (the mapper sees it).
- 2026-11-23, note #71 (game, screenshot): the big walls "decent"; the dark seam to run just above the vines:
  all the hall's wall parts moved down 16 (offsety -8), so the lowest seam is at about -237, above the
  grates' top at -240. Unchecked: the direction (if the seam went up instead, the sign is wrong).
- 2026-11-23, note #72 (game, screenshot): the wooden step under the small door was askew to the door: its
  boards are turned to the leaf's angle (rotationfloor, about 11 degrees) in the frame, the door's floor
  and the recess behind. Unchecked: the direction of the turn.
