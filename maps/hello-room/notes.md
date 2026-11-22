# Hello room

## Design intent

## Feedback log

### 2026-11-21 13:12: editor comments (dms pull)

- [x] sector room around (256, 256): light cycle fade between 25%-75% linear tween
  - Done the built-in way (mapper's choice): room sector special 72, glowing light, between the room's 192
    and its darkest neighbour (platform_nw, 64). Fixed, fairly quick speed. For a set duration, use ACS
    `Light_Glow` instead (needs ACS compiling in builds).

### 2026-11-21 19:xx: the lost-soul yards (in-game notes #13-#19), parked

The hex room's windows open onto blood yards whose floors are lifts (pit 288 down); entering the hallway raises
them (line `hall.mouth_n`, special 23) and a second line (`hall.alarm`, NoiseAlert 173) is meant to wake the souls.
Both hallway mouths block sound so main-room gunfire doesn't wake them early. Mapper's findings:
- **The alarm doesn't wake them.** With partial invisibility the risen souls ignore the player; a monster that
  *heard* the player would chase regardless (only sight is fooled by invisibility). The map data is as intended
  (checked TEXTMAP), so the noise isn't reaching them or the line isn't firing: test in the game before relying on it.
- **Side souls stay in their yards** even once awake: Doom monsters don't find paths, they step straight at the
  target, so a soul whose straight line hits the yard wall stays put. Needs a different release (teleport closets
  with monster-crossed teleport lines, or wide openings), whatever wakes them.
- Note #19 (start the souls awake at level start) is parked: needs per-map scripts (ZScript, mapper's choice; in
  `PLAN.md` M2). The mapper also pointed out that, flying, they'd come up without the lift once awake.
