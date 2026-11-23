# Asset browser (plan, building)

*Status (2026-11-22): milestones 1-5 built in a first form and served at `/assets` (not yet tried by the
mapper); milestone 6 open: Send to Claude, "used in", `dms assets`. Music first went through UZDoom's `writewave`
(works as `+writewave <song> +quit` on a hidden normal start; `-norun` quits before console commands run; it
writes `<song>` as a 32-bit float WAV into its working directory, ~4 s a song), but every song as WAV came to
~1.1 GB, so the mapper chose a browser synth instead: a close preview at no disk cost.*

*Planned 2026-11-22 at the mapper's request; replaces the texture browser and sound tester specs
(`docs/texture-browser.md`, `docs/sound-tester.md`, folded in here). Written to be built in one go,
milestone by milestone, each one usable on its own.*

A page on the board's server for browsing, auditioning and picking everything the game makes available
to a map: **textures** (walls and flats), **decals**, **items** (weapons, ammo, health, armour,
powerups, keys), **monsters**, **decorations** (obstacles, lights, corpses, scenery), **sound effects**
and **music**. It reads the resources actually in use (the configured IWAD plus UZDoom's own
`uzdoom.pk3`), so a different IWAD changes what it shows with nothing else to do.

## Why

- Names only go so far (`MARBFAC3` is an alien face; `world/quake` is a rumble). Today Claude renders
  contact sheets by hand, and sounds were tuned by ear in a dozen rebuild-and-replay rounds (Cacobelisk).
- Choosing is comparing: several candidates side by side, at the scale and offsets they'll be used with.

## Ground rules (same as the board)

- **`/assets`** on the board's server (`dms board`, same port), a link in the board's sidebar, opened
  in its own tab. `/assets#textures`, `#sounds`... pick the category (deep-linkable).
- **Server: standard library + Pillow** (already a dependency). No new Python packages.
- **Page: plain HTML/CSS/JS, no front-end libraries, no build step.** It may be split into a few
  files (`src/dms/assets.html`, `assets.js`, `assets.css`) served by the board and read on every request
  (edit, refresh). 3D is CSS 3D transforms, not WebGL (enough for boxes; pixel-exact with
  `image-rendering: pixelated`).
- **Nothing third-party is committed.** Pictures and sounds are converted on request and cached in
  `build/assets/<key>/` (git-ignored), served on 127.0.0.1 only. `<key>` is a hash of the resource
  files' sizes and mtimes plus a converter version, so a new IWAD or engine gets a fresh cache.
  The editor's config files (GPL) are **read at run time** from `.tools/udb/`, never copied.
- **The page works without the editor's files** (an outside install, another game): categories then come
  from our own rules, and nothing goes missing (an "Other" group catches the rest).
- **Text alongside images** (`AGENTS.md`): `dms assets [category] [--search TEXT]` prints the same
  lists in the terminal, so Claude can use the index without the browser.

## Where each category comes from

New module **`src/dms/resources.py`**: one view of every lump in load order (IWAD, then `uzdoom.pk3`'s
files; later, a map's own resource WADs), later ones overriding earlier ones by name, the way the engine
resolves them. It decodes:

- `PLAYPAL` (palette 0), Doom **pictures** (patch format: width, height, offsets, columns of posts) to
  RGBA, PNG files as they are (pk3), **flats** (raw 64 x 64, `F_START`..`F_END`).
- `PNAMES` + `TEXTURE1`/`TEXTURE2`: composite each wall texture from its patches (`catalog.py` already
  reads the sizes). A texture with see-through pixels is `masked`.
- Sounds: Doom's DMX format (`DS*`: format 3, rate, sample count, 8-bit unsigned) to WAV; OGG/FLAC/WAV
  served as they are.
- Music: `D_*` lumps (Freedoom's are standard MIDI, `MThd`; MUS is converted to MIDI if met).

| Category | List from | Picture / sound from |
|---|---|---|
| **Textures** (walls) | `TEXTURE1/2` + pk3 `textures/` | composited patches |
| **Flats** | `F_START`..`F_END` | raw flats |
| **Decals** | `uzdoom.pk3` `decaldef.txt`: 80 decals, 29 groups (`decal NAME [id] { pic X; shade "rr gg bb"; x-scale; y-scale; add; translucent; randomflipx; fullbright; ... }`, `decalgroup NAME { a weight ... }`) | `pic` from pk3 `graphics/` (PNG) or the IWAD's sprites; `shade` makes it a one-colour stencil of that colour, as the engine draws it |
| **Things** (items, monsters, decorations) | the editor's thing configs, read like `UZDoom_DoomUDMF.cfg` includes them: `Doom_things.cfg`, `Doom2_things.cfg`, `ZDoom_things.cfg` (`doom`, `zdoom` sections), `GZDoom_things.cfg` (`gzdoom`): categories (`monsters`, `weapons`, `ammunition`, `health`, `powerups`, `keys`, `obstacles`, `lights`, `decoration`, ...) each with editor number, `title`, `sprite`, `width` (radius), `height`, `class`. Parsed with `udbcfg.py`. Without them: `mapinfo/doomitems.txt` (DoomEdNums -> class) and the class's spawn sprite from `zscript/actors/doom/*.zs`. | sprites between `S_START`/`S_END` (1350 in Freedoom2); `NAMEA1` or `NAMEA0`, rotations `A2A8` mirrored as the engine does |
| **Sound effects** | `uzdoom.pk3` `sndinfo.txt` (logical names -> lumps, `$random`, `$alias`, `$limit`, `$pitchshift`) plus any lump not named there (by lump name) | `DS*` in the IWAD, `sounds/*.ogg` in the pk3 |
| **Music** | `D_*` lumps (35 in Freedoom2), titles from `mapinfo/doom2.txt` (which map uses which) | played in the page by our own synth through the game's soundfont (see Music) |

The four "item" kinds the mapper named map onto the editor's thing categories:
**items** = weapons, ammunition, health, armour, powerups, keys; **monsters** = monsters;
**decorations** = obstacles, lights, decoration (and corpses). **Everything else** (player starts,
teleport destinations, dynamic lights, ambient sounds, sector actions...) is indexed as `specials` but has
no tab (mapper, 2026-11-22): they're editor markers with nothing to look at, so a gallery of them isn't
worth it unless their effect can be previewed (see Later).

## Common to every category: the list

- **List / grid toggle** (remembered per category, `localStorage`). Grid: thumbnails at 2x,
  `image-rendering: pixelated`, name under; hover shows 4x. List: one row each with a small thumbnail
  (or a play button) and columns.
- **Search box**: type to filter as you go; matches name, title, class, category and tags; `*` wildcards
  like the editor's filters. `/` focuses it.
- **Filters** per category (chips; several = AND) and **sort** (click a column in list view, or a sort
  menu in grid view):

| Category | Columns / sort | Filters |
|---|---|---|
| Textures | name, set, size, colour (hue, then brightness), used in maps | wall / flat, the editor's texture sets (`Doom_texturesets.cfg`: 16 sets, read at run time), colour, size (64 / 128 wide, tall), masked, animated, switch, sky |
| Decals | name, group, pic size, colour | blood / scorch / chips / plasma... (from the name's group), shaded / plain |
| Items, monsters, decorations | editor number, title, class, size (radius x height), category | the editor's category; for monsters: health and size if the class says (later) |
| Sounds | logical name, lump, length, group (prefix before `/`: `plats/`, `doors/`, `world/`...) | group; looping-friendly (later) |
| Music | lump, length, used by (map) | |

- **Favourites** (the mapper, 2026-11-22): a star on every tile (top left, shown on hover until set) and
  list row; a "favourites" chip shows only the starred ones. Kept by the board in
  `build/asset-favorites.json` (`{category: [name, ...]}`), not in the browser, so they survive it and
  Claude can read them ("use one of my favourite textures").
- **Counts** in each tab label and above the list ("412 textures, 31 shown").
- **Copy**: click a name to copy it (what goes in `map.py` or the editor).
- **"Used in"**: where a texture / thing is used in our maps (scan of each map's `TEXTMAP`), shown in the
  detail panel; a filter "used in this map" when the page was opened from a map (`/assets?map=x`).
- Lazy-loaded thumbnails; one page per category, no paging.

## Textures: audition and compare

Click a texture (or several, with the **shortlist**: a pin on each tile, or `P`; kept along the bottom,
survives reloads per resource key). The audition area has two views, each showing **one or several
textures side by side**, so seams and how they mesh can be judged:

- **Wall / plan view (2D):** a flat plane tiled with the texture, at 1 texel = 1 map unit x zoom.
  Several textures sit side by side in **adjacent strips** (each its own column, touching, so the seams
  show; or a 2 x 2 / n x 1 arrangement for flats). **Zoom** with the wheel or +/-, from 0.25x to 16x,
  pixel-sharp; **drag to pan**. A 56-high player silhouette and a 64 x 128 doorway outline for scale
  (toggle). Strip size defaults to two repeats of the largest texture each way; editable.
- **Cube view (3D):** a box per texture, all six faces textured (CSS 3D, six `div`s with the image as a
  repeating background), slowly turning, drag to turn, wheel to zoom. **Sized to show the whole texture
  once per face by default** (width x height x width of the texture, e.g. 128 x 128 x 128 for a 128-square,
  64 x 128 x 64 for SUPPORT3); cube size editable (width, height, depth, with a "fit texture" reset).
  Several textures: the boxes stand side by side, touching, on a common floor line, turning together,
  so the joins are visible. Option: one box with a different texture per face.
- **Per-texture settings** (each strip / box has its own, in a small panel; "link all" applies one to every
  one): **x offset, y offset** (texels, like UDMF `offsetx`/`offsety`), **x scale, y scale** (the
  engine's sense, UDMF `scalex_*`/`scaley_*`: 2 = the texture drawn half size, repeating twice as often).
  The panel shows the matching UDMF fields as text to copy, e.g. `offsetx = 16; scaley_mid = 2.0;`.
- **Light** slider (0-255, like a sector's light, as a CSS brightness, an approximation of the engine's
  banding; say so on the page) applied to all, and a background colour toggle (black / grey / checker
  for masked textures).
- Detail panel: large picture, name, size, set(s), tags, animated frames playing (from `ANIMDEFS` in the
  pk3 or `ANIMATED`), a switch's other state (`SW1*`/`SW2*`), where it's used.

## Decals

Grid of every decal on a neutral wall (a mid-grey texture behind, switchable to any texture from the
shortlist), drawn as the engine would: its `pic`, `shade` colour applied as a stencil, `x-scale`/`y-scale`,
`add`/`translucent` as opacity / blend. Groups expand to their members. The detail panel shows the
`A_SprayDecal("NAME")` / DECALDEF name to copy, and a colour picker that previews the decal re-tinted
(the way Cacobelisk sprays `BloodSplat` in violet).

## Things: items, monsters, decorations

Sprite thumbnails (frame A, front rotation), title and editor number. Detail panel: the sprite large,
**all 8 rotations** (or the one rotation-less frame), **the frames animating** (the spawn sprite's
letters in order, e.g. `CANDA0..CANDB0`, at ~4 fps; the true state timings come later from ZScript),
size drawn to scale next to the 56-high player silhouette and a 64-unit grid, radius as a circle,
class name and editor number to copy.

## Sounds

- Each row: a **play** button (click again to stop), name, lump, length; space plays the selected one,
  arrow keys move.
- The **player panel** offers exactly what the engine can do (from the sound tester spec), so what's
  heard can be put into a map script as is:

| Control | In the browser | In the game |
|---|---|---|
| Volume | gain | `A_StartSound(..., volume)`, `A_SoundVolume` |
| Pitch (speed tied, as in the engine) | `playbackRate`, pitch follows | `A_StartSound(..., pitch)`, `A_SoundPitch` |
| Loop | `loop` | `CHANF_LOOPING` |
| Fade in / out | gain ramps | the script steps `A_SoundVolume` |
| Start point | `start(0, offset)` | `startTime` |
| Distance | gain from the engine's attenuation curve at a chosen distance | `ATTN_NORM` / `ATTN_IDLE` / `ATTN_STATIC` / `ATTN_NONE` or a number |
| Now and then | random gaps between plays | the script, or SNDINFO `$ambient random` |

- **Layering**: several sounds playing at once, each with its own settings (a hum + a tink + a growl).
- **Copy as script**: the settings as a ZScript line (`A_StartSound("world/quake", CHAN_AUTO,
  CHANF_LOOPING, 0.3, ATTN_STATIC, 0.8);`).

## Music

Browsers can't play MIDI, so the page has its own small synth (`src/dms/assets-synth.js`, our code, no
libraries): it parses the song's MIDI and the game's soundfont (`.tools/uzdoom/soundfonts/uzdoom.sf2`, the
one UZDoom's FluidSynth uses: `snd_mididevice = -5`) and plays it with Web Audio (sample zones and their
generators, volume envelopes, low-pass filter, pan, pitch bend, sustain, exclusive classes, programs and
banks, drums on channel 10). **A close preview, not exact**: FluidSynth's modulators, chorus and reverb
are approximated or left out. Nothing is rendered or stored; the soundfont (3 MB) loads once per page.

- **Only what the game can do is offered** (a rule for the whole browser): UZDoom plays a song as it is,
  looping or not, so there are no speed or pitch controls. The synth still supports both
  (`setSpeed`, `transpose`), unused, in case a "save as MIDI" ever writes a changed song for a map.
- Tried first and dropped: UZDoom's `writewave` (exact, but ~20 MB per song as WAV; see Status above).
- The list shows each track's length and which maps (Doom II's MAPINFO) use it; play / stop / seek; loop.
- Copy: the MAPINFO line (`music = "D_RUNNIN"`) for `map.toml`.

## Picking: handing a choice to Claude

- "Send to Claude" on the shortlist (any category, any mix) makes a note in a map's inbox (the board's
  `POST /api/note`, same `X-DMS-Board` rule), with a text box for what it's for, and the settings when
  there are any: *"hall pillars: MARBFAC2 (offsetx 16, scaley 2), sides MARBLE1"*,
  *"ambience: world/quake, loop, volume 0.3, pitch 0.8, ATTN_STATIC"*. Claude acts on it like any note.
- "Copy" gives the same text.

## API (board server)

- `GET /assets` (+ `/assets.js`, `/assets.css`): the page.
- `GET /api/assets/index`: counts per category and the resource key.
- `GET /api/assets/<category>`: the full list for one category (`textures`, `flats`, `decals`, `items`,
  `monsters`, `decorations`, `specials`, `sounds`, `music`), each entry with its fields and its file URLs.
- `GET /asset/<key>/<kind>/<NAME>.png` (`tex`, `flat`, `decal`, `sprite`), `.../sound/<NAME>.wav|.ogg`,
  `.../music/<NAME>.mid`, `.../soundfont/uzdoom.sf2` (served from `.tools`, not copied); `/assets-synth.js`. Long cache headers (the key changes when the
  resources do).
- `GET /api/assets/favorites`: the favourites; `POST /api/assets/favorites` `{category, name, on}` stars
  or unstars one (same checks as notes: JSON, the `X-DMS-Board` header, this server's origin).
- Indexing is done once per resource key and kept in `build/assets/<key>/index.json`; conversions happen
  on first request (threaded server, a lock per file).

## Milestones (each one usable; tests with each)

1. **Resources + textures.** `resources.py` (WAD + pk3 lumps in load order, palette, pictures, flats,
   texture compositing), the index, `/assets` with the textures and flats tabs: list/grid, search, sort,
   filters (sets from the editor's file, size, colour, masked), copy name. `dms assets`. Tests: a tiny
   hand-made WAD (palette, two patches, a texture composited from them with an offset, a flat);
   picture decoding with posts; DMX -> WAV header.
2. **Texture audition.** The 2D plan view and the 3D cube view, several textures side by side, per-texture
   offsets and scale (engine sense) with the UDMF text, zoom/pan, cube fit and size, light, background,
   shortlist. Animated textures and switch pairs in the detail panel.
3. **Things.** Items, monsters, decorations, specials from the editor's configs (fallback: doomitems +
   ZScript), sprites with rotations and frame animation, size against the player silhouette.
4. **Decals.** DECALDEF parsing, stencil/tint drawing, groups, re-tint preview.
5. **Sounds and music.** SNDINFO, DMX -> WAV, the player panel (volume, pitch, loop, fades, start,
   distance, now-and-then), layering, copy as script. Music: the browser SF2 synth.
6. **Picking.** Send to Claude (shortlist + settings as a note), "used in" scan and filter, board sidebar
   link, `AGENTS.md` / `README.md` / `PLAN.md` updated, `dms build --all` not affected (nothing here touches
   maps).

Each milestone: run the tests; start the board and **check the page in the browser** (Claude in Chrome
when available, else the mapper), at least: counts match the WAD (Freedoom2: 1350 sprite lumps, 109
`DS*` sounds, 35 `D_*` songs, about 430 textures and 150 flats), a composited texture looks right
(compare a few with the editor), the cube fits a 64 x 128 texture, offsets and scale move the texture in
the right direction (positive `offsetx` moves the texture left on the wall, as in the engine).

## Decided without the mapper (defaults; change if wrong)

- One page, tabs per category, rather than separate pages.
- "Several textures side by side" = adjacent strips in 2D and adjacent boxes in 3D (plus a box with a
  texture per face).
- Scale follows the engine's convention (bigger number = smaller texture), so values copy straight into maps.
- Tags/favourites of the mapper's own (`catalog/texture-tags.toml` in the old spec) are left for later;
  the shortlist covers picking for now.

## Later

- A Specials tab only if it can preview the effects (mapper, 2026-11-22): dynamic lights (colour, radius,
  pulse / flicker cycles, from their args) as a glow on a wall; particle fountains; slopes. Without previews,
  a gallery of editor markers isn't useful.
- Per-map resource WADs / `TEXTURES` lumps (custom art), our own sounds (CC0).
- An in-engine audition: a generated test room with the shortlist on its walls (`dms play`), and playing
  sound settings in the running game through the live link (`DMSLIVE`).
- A room view (corridor with walls, floor, ceiling from the shortlist) and fog in the texture audition.
- Switching IWAD (`dms setup --iwad <path>`): the browser already follows it; the catalog, the editor's
  resources and `-iwad` need the change too.
