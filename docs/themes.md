# Themes (plan, building)

*Planned 2026-11-25 with the mapper. Status: milestone 1 built (theme files, `dms themes`, harvest);
milestone 3, the browser viewer, in a first form (`/themes`).*

A **theme** is a set of textures, things and atmosphere that belong together, like a colour palette:
the look of one kind of place. Picking from a theme keeps an area visually consistent, and makes the
seams between areas a choice. Cacobelisk has two already: the **techbase** (the start closet, the tech
hall: METAL4, the track metal, red light channels) and the **grotto** (the passages and the cistern:
mossy rock, mud, timber, torches, green water).

Themes are **shared across maps**: a tool of the repo, not of one map.

## A theme file

`themes/<name>/theme.toml` (a folder, so a theme can later carry textures of its own, see below):

```toml
title = "Techbase"
description = "The forgotten service levels: rusty track metal, red emergency light."

[textures]          # role = [names]: the first is the main one, the rest alternatives
wall = ["METAL4"]
trim = ["SUPPORT3"]
door = ["CACODOOR"]
floor = ["FLOOR4_8"]
ceiling = ["CEIL3_5"]
light = ["LITERED"]

[things]            # role = [thing types]
light_source = [9830]

decals = []

[atmosphere]
light = 80                  # the usual sector light
light_range = [60, 128]     # the darkest and brightest it goes
lightcolor = "FF8080"       # sector light tint (UDMF lightcolor), optional
fog = ""                    # fog colour (UDMF fadecolor), "" for none
fogdensity = 0
```

**Roles** (`themes.ROLES`; an unknown role is a warning):

| Role | What it's for |
|---|---|
| `wall`, `wall_alt` | the main wall surface; a second one for variety |
| `wall_base` | a strip along the foot of walls |
| `trim` | frames, beams, edges: what holds things together (metal, timber) |
| `door`, `door_frame` | door faces; the jambs and lintel round a door |
| `step` | the faces of steps and ledges |
| `floor`, `floor_alt`, `ceiling` | flats (a wall texture is fine as a flat, and the other way round) |
| `light` | a lit fixture: a light panel, a tube |
| `switch` | switch faces (SW1...; the game turns them to SW2...) |
| `liquid` | water, slime and the like |
| `sky` | the sky where the area is open |

Things: `light_source` (dynamic lights, torches: what lights the place) and `decoration`.
`decals`: decal names (`A_SprayDecal`) that belong to the look. Atmosphere is light, tint and fog
(and later an ambient sound).

**A map's own textures** (CACOBASE, CACODOOR) can be named in a theme; the theme then only works whole
in that map. Later: a theme folder carries its own `textures.txt` / `textures/*.png`, packed by every map
that uses the theme, so a look built for one map travels with the theme.

## Milestones

1. **Theme files, `dms themes`, harvest** (built). `dms themes` lists the themes, `dms themes show <name>`
   prints one, `dms themes check` checks every theme (roles, and names against the IWAD's catalog and the
   maps' own textures). `dms themes harvest <map> <name> --gid PATTERN...` drafts a theme from a part of a
   map: the sectors whose gid matches the patterns (`fnmatch`: `closet*`, `passage_*`), the textures on
   their walls, floors and ceilings sorted into roles by where they sit (one-sided middles are walls, step
   faces are steps, door lines are doors, SW1... are switches, animated liquids are liquids...), the things
   standing in them (lights, decoration), and the usual light and fog. The draft lists what it counted, for
   the mapper and Claude to trim.
2. ~~The standard scene as a map played in the game~~: the mapper chose the browser instead (2026-11-25):
   the scene is a model in the viewer, labelled. A playable copy may come later if the previews mislead.
3. **The browser viewer** (built; seen by the mapper, not yet by Claude, whose browser extension wasn't
   connected): `/themes` on the board's server (`src/dms/themes.html`, read per request; `/api/themes` is
   `themes.for_page`: every theme with each name's picture, wall roles looked up among the wall textures
   first, flat roles among the flats, then the maps' own). A small WebGL2 renderer of our own: the standard
   room as a cutaway diorama (512 x 384, ceiling 192; only the north and west walls, so it can be looked
   into): a door of the door texture's size in a `door_frame` (jambs and lintel), a light niche (`light`,
   full bright, lined with `trim`), a switch block, a `wall_alt` panel and pillar, a `wall_base` strip along
   the walls' foot, a dais (`step` faces, `floor_alt` top), a pool of `liquid` (animated, 8 tics a frame)
   with `trim` banks, a ceiling slab along two walls, the `sky` behind, the theme's thing sprites standing
   about. Doom's alignment (u along the line, pegging, flats on their own size), sector light with a
   distance fade and the fake contrast, the theme's tint and fog (density approximated). Labels in two
   columns with leader lines to each element, the texture's picture and name; "N of M" cycles a role's
   alternatives; a role the theme lacks falls back (shown as such) or is a magenta checkerboard. Views:
   model, low, inside (the default; F), flown to (eased, 0.7 s). Light and fog toggle (L, G; light off: every
   texture full bright). Leader lines are faint until their label, or one of their faces in the view, is
   under the mouse (a picking pass: each part drawn off screen in its label's colour). The ceiling is an
   L over the back and west side, past the pillar, drawn from below only. The page polls every 3 s, so an
   edited `theme.toml` shows. **Seen and liked by the mapper (2026-11-25).**
   Next: two themes side by side and a seam between them; a light-source glow.
4. **Choosing in the asset browser**: a Themes tab, the roles as slots; click a texture to put it in a slot,
   the scene updates; each slot's main colours as a swatch, the theme as a palette strip; "close in colour"
   to find candidates. Saves to `theme.toml`.
5. **Themes in the maps**: `t = b.theme("grotto")` in `map.py` (`t.wall`, `t.trim`...) in place of a map's
   texture constants; sectors carry `user_theme`, and the validator warns about a texture that isn't in its
   sector's theme (warnings only: accents are deliberate). The board can tint the map by theme. Cacobelisk
   moved over.
