# test map

## Design intent

A test room with a ritual look: a big red pentagon (~1460 across, ceiling 256) with a lava pentagram
(inverted, drawn as lines in a ring, glowing slowly via sector special 72), marble pillars in the corners
and a red torch mid-wall. A super shotgun in the middle is the bait for a trap; a secret room on the west
wall holds quad damage.

- **The trap:** the inner pentagon's five edges are walk-over lines (Door_Open, tag `PILLAR_TAG`): the
  only way to the shotgun. They open the five pillars (closed door sectors), each with a caco, and
  `zscript.zs` (`TestMapEvents.WorldLineActivated`) wakes the cacos (thing id `CACO_TID`) at once.
- **Quad damage:** Doom has none. `zscript.zs` defines `TestMapQuadDamage` (UZDoom's `PowerDamage`, x4,
  30 s, blue tint, an ice-tinted megasphere sprite) and `WorldLoaded` spawns it on the map spot
  (`QUAD_TID`) in the secret room.
- **The secret door:** 128 wide (cacos are 62 across), same texture as the wall (mapper: a mismatched
  texture gives it away). Use it to open; it stays open.

## Feedback log

### 2026-11-21 evening (first session)

- Editor save 21:07: the mapper dragged three corners of the starting 512 x 512 room (ported; since replaced
  by the pentagon at note #4).
- #1 (board): "this room should be red": REDWALL1 walls, BLOOD1 floor. (UZDoom's UDMF also has sector
  `lightcolor`, not used yet.)
- Chat: start with a chaingun (on the player start).
- #2 (game): a secret room with a caco behind the west wall.
- #3 (game): the secret door's texture didn't match; the caco couldn't leave (the door was ~60 wide, a caco
  is 62): door widened to 120, red.
- #4 (board): the room as a big pentagon, pillars, torches, subtle glow, a pentagram on the floor.
- #5 (game): "more satanic": inverted, drawn as lines in a ring.
- Chat: super shotgun in the middle; stepping onto it opens the pillars to a caco ambush; the secret
  room's caco became quad damage. Mapper on the pentagram: "that looks great".
- Open question from the design notes: five cacos, one per pillar, is a symmetrical placement; staggering
  the pillars (different speeds, or not all of them) would send them in waves.
