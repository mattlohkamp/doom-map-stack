# Hello room

## Design intent

## Feedback log

### 2026-11-21 13:12: editor comments (dms pull)

- [x] sector room around (256, 256): light cycle fade between 25%-75% linear tween
  - Done the built-in way (mapper's choice): room sector special 72, glowing light, between the room's 192
    and its darkest neighbour (platform_nw, 64). Fixed, fairly quick speed. For a set duration, use ACS
    `Light_Glow` instead (needs ACS compiling in builds).
