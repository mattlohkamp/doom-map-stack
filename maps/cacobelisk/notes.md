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
