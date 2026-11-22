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
