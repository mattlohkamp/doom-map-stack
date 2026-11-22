# Texture browser (spec, not built)

*Specced 2026-11-22 at the mapper's request; not implemented yet. Listed in `PLAN.md` §8.*

A page next to the board for looking up, comparing and auditioning the wall textures and flats of the
IWAD in use, and for handing a choice to Claude. It reads whatever IWAD is configured, so switching from
Freedoom to a bought `doom2.wad` changes what it shows with nothing else to do.

## Why

- The names only go so far (`MARBFAC3` is an alien face; nothing in the name says so). Today Claude
  renders contact sheets by hand to choose textures; the mapper has no way to browse at all outside the
  editor's texture picker, which only opens while editing a wall.
- Choosing is comparing: several candidates side by side, at the scale and in the light they'll be used.

## What it is

- **`/textures`** on the board's server (`dms board`, same port), opened in a second tab: a link in the
  board's sidebar, and `Open Board.cmd` can open both tabs (`[board] textures_tab`, default off).
  Same rules as the board: standard library only on the server, one HTML file read on every request
  (`src/dms/textures.html`), no build step, no front-end libraries.
- **Where the pictures come from:** a new module, `src/dms/texview.py` (Pillow, already a dependency),
  reads the IWAD named in `tools.local.json` (and later any per-map resource WADs): `PLAYPAL`, `PNAMES`,
  `TEXTURE1`/`TEXTURE2` (composite each texture from its patches), and the flats between `F_START` and
  `F_END` (raw 64 x 64). It renders each one to a PNG on first request and caches it in
  `build/textures/<hash of the IWAD>/` (git-ignored, so a commercial IWAD's art never reaches git;
  served on 127.0.0.1 only). A different IWAD gets a different cache folder; nothing to clear.
  The scratch script that made this session's contact sheets is the starting point.
- **API:** `GET /api/textures` -> `[{name, kind: wall|flat, width, height, tags, colour, animated,
  switch_pair, used: [{map, count}]}]`; `GET /tex/<kind>/<NAME>.png`; `POST /api/texture-tags` (the
  board's `X-DMS-Board` header rule applies) for the mapper's own tags.

## The grid

- A grid of every wall texture and flat, drawn at 2x with `image-rendering: pixelated`, its name and
  size under it. Hovering shows it at 4x. One page, no paging (Doom II has about 430 textures and 150
  flats; thumbnails are lazy-loaded).
- **Grouped by category**, a heading per group, collapsible; or a flat list.
- **Filter bar:** a search box (name, with `*` wildcards like the editor's filters), tag chips (click to
  filter, several = AND), wall / flat / both, a size filter (64 wide, 128 wide, 128 high...),
  "used in this map", "only my favourites".
- **Sort:** name, category, colour (hue, then brightness), size, how often it's used in the maps.

## Tags: where they come from

1. **Categories from Ultimate Doom Builder.** The editor ships `Configurations/Includes/Doom_texturesets.cfg`:
   16 sets (Rock, Brick, Liquids, Doors, Steps, Wood, Flesh, Switches, Marble, Lights, Metal, Silver,
   Base, Hell, Outdoors, Computer), each a list of name filters (`ROCK*`, `GSTONE1`...). It covers the
   Doom/Doom II names, which Freedoom shares. It's the editor's GPL file, so it's **read at run time
   from `.tools/udb/`, never copied into the repo**; a texture can be in several sets. (Heretic, Hexen
   and Strife have their own files, for later.)
2. **Derived tags**, worked out by `texview.py` from the WAD itself:
   - `colour`: the dominant hue bucket (grey, brown, green, red, blue, tan...) and brightness (dark,
     mid, light), from the pixels;
   - `animated` (with its frames) from UZDoom's built-in animation list (`ANIMDEFS` in `uzdoom.pk3`,
     read at run time) or an `ANIMATED` lump; `switch` with its on/off pair (`SW1*`/`SW2*`);
   - `sky` (`F_SKY1`, `SKY*`), `masked` (has see-through pixels: for mid-textures on two-sided lines,
     grates), `tall` (taller than 128), `door-sized` (64 or 128 wide, 72 or 128 high).
3. **Uncategorised:** whatever no set and no rule claims gets an "Other" group, so nothing goes missing.
4. **The mapper's own tags and favourites**, saved in `catalog/texture-tags.toml` (committed; names
   and words only, no art): e.g. `MARBFACE = ["hall", "carved", "favourite"]`. Added from the detail
   panel. This is also where a map's palette can live (`palette:cacobelisk`), the "small fixed set by
   purpose" from `PLAN.md` §10.

If the editor's file isn't there (an outside install, another game), the page still works with 2-4.

## The detail panel

Click a texture: a panel with it large, its name (click to copy), size, tags (editable), where it's used
(map, element gids, as in the board's notes), and for a switch its other state, for an animation its
frames playing. Then the **audition** views:

- **Wall:** a stretch of wall filled with the texture repeated, at 1 texel = 1 map unit on screen, with
  a 56-unit player silhouette and a 64 x 128 doorway outline for scale. A **light slider** (0-255,
  like a sector's light) and a **fog** switch (colour and density, like `fadecolor`/`fogdensity`):
  an approximation in CSS (brightness, and a tint that grows with distance on the receding views),
  not the engine's exact lighting; say so on the page.
- **Cube:** a cube with the texture on all six faces, slowly turning, drag to turn it by hand. Pure
  CSS 3D transforms (six `div`s with the image as background), no WebGL. Good for blocks, pillars,
  crates, monoliths.
- **Floor / ceiling:** a plane tilted away into the distance (CSS perspective), tiled, for flats; or a
  wall texture seen at an angle down a corridor (two walls, floor and ceiling picked from the shortlist).
- **Room:** a box corridor in CSS 3D: walls, floor and ceiling each set from the shortlist, to see
  combinations together.

## Comparing and picking

- **Shortlist:** pin textures (a pin on each tile, or `P`); the shortlist sits along the bottom and
  survives reloads (`localStorage`, per IWAD). Any audition view can show the whole shortlist side by
  side, same light and fog, so candidates are compared like for like.
- **Hand it to Claude:** "Send to Claude" on the shortlist makes a note in the map's inbox (the board's
  existing `POST /api/note`, source `board`), e.g. *"textures for the hall pillars: MARBFACE, MARBFAC2,
  MARBFAC3; plain sides MARBLE1"*, with a text box for what they're for. Claude acts on it like any note.
- **Copy:** names to the clipboard, one per line, for the editor.

## Switching IWADs (related, separate)

The browser follows the configured IWAD on its own, but switching from Freedoom to `doom2.wad` touches
more than the browser: `tools.toml`/`tools.local.json` (a bought IWAD is pointed at, not downloaded:
`"managed": false`), `dms catalog` (the validator checks names against `catalog/`), the editor's
resources and the game's `-iwad`. That deserves its own small change (`dms setup --iwad <path>`); the
names are the same in both, so maps keep working.

## Build order (when it's picked up)

1. `texview.py` (composite, flats, cache) + `/api/textures` + the grid with search, categories from the
   editor's file, sort by name/category. Tests: compositing against a tiny hand-made WAD.
2. The detail panel with the wall view, light slider and fog; derived tags (colour, animated, switch).
3. Cube, floor and room views; the shortlist and side-by-side comparing.
4. The mapper's tags and favourites (`catalog/texture-tags.toml`); "Send to Claude"; "used in this map".

Later: per-map resource WADs and `TEXTURES` lumps (custom textures, `PLAN.md` "Later"), sprites as a
third kind (decorations: their real height next to the player silhouette), and an in-engine audition
(a generated test room with the shortlist on its walls, opened with `dms play`).

## Open questions for the mapper

- Open the textures tab automatically with the board, or only from the link?
- Should favourites and tags be shared (committed in `catalog/`) or kept per machine?
- Is the editor's 16-way split good enough as the main grouping, or do you want your own groups from the
  start (the tags file can carry them)?
