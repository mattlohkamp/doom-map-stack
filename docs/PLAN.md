# DOOM Map Workshop — Plan

A workflow where Claude writes DOOM levels and the mapper views them in an editor,
test-plays them in the engine, and gives feedback for the next round.

Status: **M2 in progress** (see §9). Remaining unknowns are marked *to verify* inline.

---

## 1. The loop and the ground rules

How the loop works, the supported environment, the self-contained rules, licensing,
writing conventions and who each document is for are settled and live in **`AGENTS.md`**.
This section keeps only what M0 still has to verify:

- **Visual C++ runtime:** whether UZDoom or the editor need it. If so, try app-local DLLs before a system install.
- ~~uv locations / registry~~ **resolved in step 2:** `uv.toml` has `cache-dir` but no `python-install-dir`,
  and relative paths in it resolve against the current directory, so every location is an absolute
  `UV_*` variable in `scripts\dms-env.ps1`. per its docs, uv registers managed Pythons in HKCU by default;
  `--no-registry --no-bin` plus `UV_PYTHON_INSTALL_REGISTRY=0` / `UV_PYTHON_INSTALL_BIN=0` /
  `UV_PYTHON_NO_REGISTRY=1` prevent it (checked: no new registry key or shortcut after bootstrap).
- ~~UZDoom `-config`, saves, screenshots~~ **resolved in step 4:** UZDoom has a portable mode instead
  (`uzdoom_portable.ini` next to the exe), which keeps config, saves and screenshots in `.tools\uzdoom\`.
  Its graphics cache still goes to `%LOCALAPPDATA%\doom\` (see "Known exceptions" in `AGENTS.md`).
- **Visual C++ runtime, note:** UZDoom and the editor run on the dev machine, but it may already have the runtime
  installed, so this needs a clean machine (or VM) to settle.
- ~~Final check~~ **done at the end of M0** (see §9). Repeat it once `build`/`play`/`edit` exist in M1.

Planned reference (M2): `docs/udmf-cheatsheet.md`, covering the UDMF fields we use, line specials,
thing IDs and Doom's movement limits.

---

## 2. Decisions

| # | Decision | Leaning | Status |
|---|----------|---------|--------|
| D1 | Map format | **UDMF** (text TEXTMAP), which Claude can read and diff | ✅ |
| D2 | Target engine | **UZDoom** only, no vanilla/Boom compatibility | ✅ |
| D3 | IWAD | **Freedoom2**, pinned to 0.13.0 (stable). The texture catalog is built from this exact file | ✅ |
| D4 | Source of truth | **Hybrid**: generate the rough layout, then shared TEXTMAP editing (see §4) | ✅ |
| D2a | Movement | **Jump and crouch off** (MAPINFO `nojump` / `nocrouch` for all maps). Layouts are designed for classic movement | ✅ |
| D5 | Scripting | ACS (needs `acc`) and/or ZScript (no compile) | later |
| D6 | Packaging | `.wad` to start, `.pk3` once there are custom resources | later |

---

## 3. Project install (M0)

Everything installs into the repo (see "Self-contained" in `AGENTS.md`).

### Fresh-machine install

*Since 2026-11-23: clone, then double-click `Start Session.cmd`; it runs `scripts\bootstrap.ps1` by itself.*

```powershell
git clone https://github.com/mattlohkamp/doom-map-stack.git
cd doom-map-stack
.\bootstrap.ps1
```

`bootstrap.ps1` (plain PowerShell, no dependencies):
1. Downloads the pinned standalone `uv.exe` from its official GitHub release, checks its hash, and puts it in `.tools\uv\`.
2. `uv sync`: installs Python into `.tools\python\` and dependencies into `.venv\`.
3. `dms setup`: installs the engine, editor and IWAD into `.tools\`, and configures Ultimate Doom Builder (below).

Running it again only fills in what's missing. No manual steps should be needed.

### Python: uv (the npm equivalent)

| npm | uv |
|---|---|
| `package.json` | `pyproject.toml` (committed) |
| `package-lock.json` | `uv.lock` (committed) |
| `node_modules/` | `.venv/` (git-ignored) |
| `npm install` | `uv sync` |
| `npm run x` | `uv run dms x` (wrapped as `.\dms.ps1 x`) |

- uv also installs the pinned Python version itself, so it doesn't depend on whatever Python is on the machine.
- Expected dependencies: Pillow (renderer), PyYAML (overrides), pytest (dev). Keep the list short.

### Doom tools: `dms setup`

A committed `tools.toml` lists each tool with its official source, a pinned version, the exact download URL, and a SHA256 hash:

| Tool | Source | Notes |
|---|---|---|
| UZDoom | github: UZDoom/UZDoom releases | Portable Windows zip |
| Ultimate Doom Builder | github: UltimateDoomBuilder/UltimateDoomBuilder releases | `.7z`, extracted with Windows' own `tar.exe`. Bundles `acc` (`Compilers\Hexen\acc.exe`) and BCC |
| Freedoom | github: freedoom/freedoom releases, **0.13.0** | Only `freedoom2.wad` is used |
| SLADE | optional, off by default | Resource browser |
| ZDBSP | not needed (UZDoom builds nodes on load) | |

What `dms setup` does:
1. Downloads each tool from its official release.
2. Checks the SHA256 hash and stops if it doesn't match.
3. Extracts into `.tools/<name>/` (git-ignored).
4. Writes `tools.local.json` with the resolved paths. `tools.local.json` can also be
   hand-edited to point at an existing install instead.
5. Does nothing for tools already installed. `dms setup --upgrade <tool>` is used after bumping a version in `tools.toml`.

Updating a tool is a deliberate change to `tools.toml` that shows up in git.

### Ultimate Doom Builder: portable, configured by `dms setup`

Found in Ultimate Doom Builder's source (`Source/Core/General/General.cs`, `Config/ConfigurationInfo.cs`):
- Settings live in `UDBuilder.cfg`, by default in `%LOCALAPPDATA%\Doom Builder\`.
- **`-portable`** (a command-line flag, needed on every launch) stores settings in the
  program folder instead, i.e. `.tools\udb\`. There's no option for any other settings path.
- Game configuration settings are keys in that same file, e.g.
  `configurations.<gamekey>.engines.engine0.testprogram` and `configurations.<gamekey>.resources`,
  where `<gamekey>` is the lowercased config filename without its extension.
- Command-line options: `-cfg <game config file>`, `-resource wad|pk3|dir <path>`,
  `-map <name>`, `-nosettings`, plus a WAD path to open.

Plan:
- **`dms edit <map>`** always launches with `-portable -cfg <UZDoom Doom2 UDMF cfg>
  -resource wad .tools\freedoom\freedoom2.wad -map MAP01 <working wad>`.
- **`dms setup`** writes the test-engine path (`.tools\uzdoom\uzdoom.exe`) and the
  resources into `.tools\udb\UDBuilder.cfg`, so F9 test-play works with no clicking.
- Fallback if writing the file from scratch is fragile: launch the editor once
  with `-portable` to create it, then `dms setup` fills in the keys.
- The UZDoom game config is `Configurations\UZDoom_DoomUDMF.cfg`, so `<gamekey>` is `uzdoom_doomudmf` (checked in R4336).

No manual step remains, if this works out.

### Status on the dev machine (2026-11-21)

- System Python 3.14.5 is installed but not used: uv brings its own Python into `.tools\`. Don't install uv with winget; `bootstrap.ps1` fetches it.

---

## 4. How maps are authored (D4: hybrid)

Each map is in one of two **source modes**, recorded in its `map.toml`:

- **generated**: `map.py` (using the generator library) is the source of truth and is
  compiled to TEXTMAP. Big structural changes are cheap for Claude. The mapper's
  property tweaks from the editor come back through `pull` into `overrides.yaml`.
- **hand-edited**: TEXTMAP itself is the source of truth; Claude and the mapper both edit it
  directly, and it is never regenerated.

A new map normally starts **generated** while the layout is rough, and switches to
**hand-edited** once the layout settles or the mapper makes geometry changes in the editor.

---

## 5. Proposed repo layout

*Superseded 2026-11-23: the layout as it is now is in `AGENTS.md`, "Where things are".*

```
doom-map-stack/
├── AGENTS.md            instructions for Claude Code (read natively; source of truth)
├── .claude/settings.json  project Claude Code settings (permissions)
├── PLAN.md              this file
├── README.md            public-facing summary (never a source of truth)
├── bootstrap.ps1        one-time setup: fetches uv, then runs uv sync + dms setup
├── dms.ps1              entry point for every command (sets UV_* environment variables, runs uv run dms)
├── scripts/dms-env.ps1  shared by both scripts: the repo-local uv/Python environment
├── uv.toml              keeps uv's Python + cache inside .tools\ (if supported)
├── .python-version      pinned Python version
├── pyproject.toml       Python project + dependencies (uv)
├── uv.lock              pinned dependency versions
├── tools.toml           pinned versions + hashes of the Doom tools (`dms setup`)
├── tools.local.json     resolved tool paths (git-ignored)
├── .tools/              everything downloaded (git-ignored): uv, Python, uv cache,
│                        UZDoom (+ its ini, saves), Ultimate Doom Builder (+ portable settings), Freedoom
├── maps/                one self-contained folder per map, named by name (see `AGENTS.md`)
│   └── light-test2/
│       ├── map.toml     title, kind (map|test|example), status, source mode, sky, music
│       ├── map.py       generator source (while the map is generator-driven)
│       ├── TEXTMAP      generated or hand-edited
│       ├── overrides.yaml  the mapper's editor tweaks, pulled in, keyed by user_gid
│       ├── notes.md     design intent + feedback log for this map
│       └── resources/   anything only this map uses (ACS, extra MAPINFO, textures)
├── episodes/            (later) release groupings: map name → slot, e.g. MAP02 = "light-test2"
├── src/dms/             tooling (Python package `dms`)
│   ├── udmf/            TEXTMAP read/write, geometry helpers
│   ├── gen/             room/door/lift building blocks
│   ├── validate.py
│   ├── render.py        top-down PNG
│   └── pack.py          build WAD/PK3
├── resources/           ACS, ZScript, MAPINFO, custom textures
│   └── devtools/        ZScript dev mod: note key, screenshot tour (loaded only by play/tour)
├── catalog/             texture/flat/thing names pulled from the IWAD
├── docs/                design notes, references
│   └── map-design-notes.md   the mapper's map design guidelines (from play notes). AGENTS.md
│                           points to it as required reading before designing a map
├── feedback/<map>/      note screenshots, per map (git-ignored, temporary)
└── build/<map>/         per-map output (git-ignored): playable WAD, working edit WAD,
                         last generated TEXTMAP, fingerprints, render, tour/, log-play.txt
```

### 5a. Several maps at once

The rules (named by name, self-contained, map name always explicit, shared code stays safe) are in `AGENTS.md`.
Still to build later:

- **Releases:** `episodes/<name>.toml` assigns maps to slots;
  `dms build --episode <name>` produces one WAD with combined MAPINFO and an idgames-style `.txt`.

---

## 6. Tooling to build

1. **UDMF I/O**: parse and write TEXTMAP, round-trip safe (keeps fields we don't model).
2. **Packer**: TEXTMAP(s) → `build/<map>/<map>.wad` (MAP01 marker, TEXTMAP, ENDMAP) + MAPINFO.
3. **Texture catalog**: read TEXTURE1/2, PNAMES and flats from the IWAD → `catalog/*.txt`.
4. **Validator**:
   - player 1 start exists
   - sectors are closed and linedefs reference valid sidedefs
   - textures and flats exist in the catalog
   - tags match their specials (doors, lifts)
   - no orphan sectors
   - every one-sided line has a middle texture
5. **Movement check** (Python, no engine): works out which sectors a player can
   reach from the player start, using Doom's movement rules:
   - step-up of 24 units at most; any drop is allowed, but one-way drops are flagged
   - 56 units of floor-to-ceiling headroom needed (the player's height)
   - passages narrower than 32 units (the player's width) are blocked
   - doors and lifts count as passable once activated; locked doors need their key to have been reached first
   - blocking lines are treated as walls
   - **Reports:** unreachable sectors, unreachable keys/exit/weapons,
     soft-locks (areas you can get into but not out of without an exit),
     and secrets that can't be reached.
   - Results are drawn onto the render PNG (reachable shaded, problems in red).
6. **Renderer**: top-down PNG (sectors shaded by floor height, things as glyphs,
   linedef specials highlighted, coordinate grid). Claude looks at it after every build.
   Also a **diff render** (`build/<map>/diff.png`): before/after against the previous build,
   with added geometry in green, removed in red and changed in yellow.
7. **Screenshot tour** (devtools ZScript mod + script):
   - `tour <map>` runs UZDoom with the devtools mod, which visits a list of
     viewpoints, saves screenshots from several angles at each, then quits.
   - Viewpoints come from: each sector or room centroid at eye height,
     the mapper's feedback marks, and named points in the map's `notes.md`.
   - Screenshots land in `build/<map>/tour/`, named by viewpoint, for Claude to review.
   - Lets Claude see the actual engine output (lighting, textures, height
     changes, sky, misalignments) without steering a player.
8. **Generator library**: rooms, corridors, doors, lifts, stairs,
   windows, key doors, secrets. Every generated element gets a stable ID in a
   custom field, `user_gid` (e.g. `"courtyard.wall_n.2.front"`).
9. **Pulling in the mapper's editor tweaks** (`pull`):
   - Ultimate Doom Builder edits WADs, not bare TEXTMAP files. So `edit` packs
     `maps/<map>/TEXTMAP` into a working copy, `build/<map>/edit.wad`, and opens that.
     `pull` unpacks the TEXTMAP from it. TEXTMAP stays plain text in git; the WAD is temporary.
   - Reads the edited TEXTMAP and the last generated one (`build/<map>/generated.textmap`)
     as map data, so differences in field order or number formatting don't show as changes.
   - Matches elements by `user_gid`, falling back to position (e.g. a line by its endpoints).
     The editor copies gids on split, copy/paste and sector division (see §9), so a gid can appear on
     several elements: disambiguate by position, and report duplicated or missing gids as geometry changes.
   - **Property tweaks** (offsets, textures, light, heights, thing angles and flags)
     → written to `maps/<map>/overrides.yaml`, keyed by gid. The generator applies
     overrides last, so tweaks survive every rebuild.
   - **Geometry changes** (vertices moved, lines added or removed, new sectors)
     → listed in a report; Claude ports them into the generator by hand, or the map
     moves to TEXTMAP being the source of truth.
   - Claude looks at overrides for patterns: if a whole room shares the same
     correction, the generator is fixed instead and those overrides are dropped.
   - **Overwrite protection:** `build` records a hash of each TEXTMAP it generates
     and of each working WAD it packs. It refuses to regenerate a map whose TEXTMAP or
     working WAD has been edited since, and tells you to run `pull` first.
10. **Scripts**:
   - `build <map> | --all | --episode <name>`: generate (+ overrides) → validate → movement check → render + diff render → pack
   - `new <map> [--kind map|test|example]`: create a new map folder from a template
   - `watch <map>`: stream new in-game and editor notes for Claude (see §7)
   - `pull <map>`: pull the mapper's editor tweaks into overrides (see item 9)
   - `tour <map>`: screenshot tour (on demand; slower than `build`)
   - `play <map> [--skill N] [--nomonsters] [--god]`: start the engine with `+logfile`
   - `edit <map>`: pack the working WAD and open it in Ultimate Doom Builder (portable mode)

---

## 7. Feedback channel

- **Free-form**: The mapper describes it, Claude appends to `maps/<map>/notes.md`.
- **In-game notes** (devtools mod, a key such as `N`):
  1. Takes a screenshot (key bound to an alias: `screenshot` + open the note box).
  2. Opens a text box (ZScript, like the save-name box); the mapper types the note.
  3. Writes a tagged line to the log: note number, map, x/y/z, angle/pitch, sector
     **standing in** and the sector/line/thing **looking at** (crosshair trace),
     with their `user_gid` read from the map data, plus the screenshot path and the text.
     ```
     [DMS-NOTE] #7 map=light-test2 pos=(1024,-512,0) angle=90 pitch=-5
       standing_in=sector 12 (gid "closet_east") looking_at=sector 14 (gid "closet_east.pit") line 88
       shot=feedback/light-test2/note-007.png
       text="there should be twice as many zombies in here"
     ```
  - To verify: ZScript text box, crosshair trace, reading `user_gid` from the map data.
  - Fallback: the key only logs a numbered mark + screenshot; the mapper types "#7: …" in chat.
  - Notes can also be drawn onto the render PNG.
- **Editor notes** (Ultimate Doom Builder): put the request in the standard UDMF `comment`
  field of the selected sector/line/thing (properties dialog; the editor has a comments view),
  then save. `pull` collects every comment as a request tied to that element's gid,
  then clears them. Later: a JavaScript hotkey script in the editor (select, press key, type).
- **"Send to Claude" from the editor** (mapper's idea, 2026-11-21; builds on the `DmsBridge` plugin): a hotkey on the
  focused/selected sector, line or thing sends a reference (map, element kind and index, `user_gid`, position, key
  properties, optional typed comment) either to the clipboard or straight into the live channel below.
- **"Send to Claude" from the board** (mapper's idea): on the browser board that shows each build's render and diff,
  click a change (or a spot on the render) to send a reference to it with a comment ("make this taller", "why?").
  Same channel and format as the editor version.
- **The board** (`Open Board.cmd`, a small local web server in `dms`): a per-map timeline of builds, newest first:
  render + diff side by side, diff text, Claude's note on what changed and what to check, validation issues,
  play-log warnings, and the editor state from `editor-state.json`. Updates by itself; history in `build/<map>/history/`.
- **Live delivery** (`dms watch <map>`): a background process follows UZDoom's log and
  the saved working WAD, and prints each new note. Claude Code watches it, so notes
  arrive in the conversation within seconds, with reference and screenshot.
  - Default: Claude queues notes during a play session and acts on "go", so play isn't interrupted.
  - Only works while a Claude Code session is open. Otherwise notes stay in the log or
    map and are picked up by `pull` or when asked. Nothing is lost.
- **Screenshots**: UZDoom saves to a per-map folder, which Claude can view.
- **Engine log**: `log-play.txt` shows script errors and warnings, which Claude reads after a play session.
- **Load check without a window** (idea for M2 `dms build`): `uzdoom -iwad ... -file <map>.wad -norun +logfile check`
  loads everything and parses MAPINFO/definitions, then quits (exit code 1337) before opening a window; scan its log for errors.
- Later: playtest stats (kills, secrets, time) dumped at the end of a level.
- **Idea, later (mapper, 2026-11-21): our own editor context menu** (e.g. Shift+right click) with agentic
  iteration actions, beyond "Message Claude about this..." (which is on Ctrl+right click now). The editor has no
  right-click menu of its own to add to: plain right click is its "Edit" action (properties, right-drag draws).
- **Idea, tabled (mapper, 2026-11-21): one background "manager" for a dev session.** Today the board needs its
  console window kept open, and closing it doesn't close the browser tab. A single manager process (tray icon or
  small window) could own the board server, `dms watch`, and launching play/edit, and stop everything together.
  Risk to design around: a forgotten or orphaned background process. Revisit when `watch` lands, since that is a
  second long-running process.

---

## 8. Milestones

- **M0, Setup:** `bootstrap.ps1` + `dms.ps1`; `pyproject.toml` and `tools.toml`; `dms setup` working,
  including configuring Ultimate Doom Builder in portable mode; check that nothing was written outside the repo; `.gitignore` updated; AGENTS.md written (confirm with `/memory` that Claude Code loaded it).
- **M1, Hello room:** one square room with a player start, packed and playable. Proves the whole loop.
  Also check that Ultimate Doom Builder keeps `user_gid` fields when saving, including on lines it splits or copies.
- **M2, Tooling:** catalog, validator, renderer, movement check, in-game notes, editor notes (comment field),
  `dms watch` live delivery, **per-map ZScript** (mapper chose ZScript over ACS; built 2026-11-21).
- **Parked (mapper, 2026-11-21: not worth it while the mapper plays live and sends screenshot notes):**
  - **Screenshot tour** (§6 item 7): Claude would see its own work in the engine before the mapper plays.
    Worth it if Claude works on maps unattended. A smaller first step: `dms shot <map> <x> <y> <angle>`, one
    screenshot on demand, if "I haven't seen it in the game" caveats keep costing round trips.
  - **Test map overlay:** a map drawn by the devtools mod on a key, beyond what the engine's automap can do (it
    colours lines only): interactive sectors shaded by kind (doors, lifts, crushers, secrets, damaging floors),
    locked doors in key colours with a card or skull icon, monsters and items; ideally the board render's colours.
    The engine-settings part is done (`[play] test_automap`).
- **Planned, being built (mapper, 2026-11-22): the asset browser** (`docs/asset-browser.md`; replaces the
  texture browser and sound tester specs): `/assets` on the board's server, browsing everything the IWAD and
  UZDoom provide (textures and flats, decals, items, monsters, decorations, sound effects, music) as a list or a
  grid with search, filters and sort; textures auditioned side by side on a zoomable 2D plane and on 3D boxes
  with per-texture offsets and scale; sounds with the engine's own controls; music rendered by UZDoom; picks
  sent to Claude as a note.
- **Built 2026-11-23 (see `AGENTS.md`, "Renders" and `dms board`); earmarked by the mapper 2026-11-22: a
  pan/zoom map on the board, drawn as SVG.** The renderer writes an SVG
  besides the PNG (it already draws polygons, lines, circles and text); the board shows it with mouse-wheel
  zoom and drag to pan (the viewBox), sharp at any zoom, labels a constant size on screen so crowded spots
  spread out as you zoom in, and a click still maps to map coordinates for notes. Chosen over zooming the PNG
  (blurs) and real tiles (overkill for maps this size).
- **M3, First real map:** a small layout (3–5 rooms, a key door, a lift, a secret), iterated on the mapper's feedback.
  Claude reads `docs/map-design-notes.md` first, and turns any guidelines that can be checked into validator rules where practical.
- **M4, Generator library grows** from whatever M3 needed repeatedly.
- **Later:** ACS scripting, custom textures, multi-map episode, MAPINFO, music.

---

## 9. Where we left off

*Updated 2026-11-26. A new session starts here.*

**2026-11-26, later: released v0.23.0, enemy edits.** The mapper asked for a lost soul variant that is
human/robot rather than bio/alien and stares, then shoots instead of charging. Built in Cacobelisk as **the
station drones** (zscript.zs `CacobeliskDrone`, `CacobeliskRedDrone`; `maps/cacobelisk/notes.md`): a floating
metal sphere with a visor slit, its look after Freedoom's chaingunner and revenant (the mapper's pointer). The
cyan drone has 25 health and fires a fan of three small fast bolts; the red one has 90 (two shotgun blasts) and
fires two slower, harder bolts. Three cyan and one red in the pump hall. Mapper: "they're perfect".
*Tools:* a map's own sprites (`maps/<map>/sprites/`, AGENTS.md); custom monsters placed as stock things with a
thing id and swapped at load; the asset browser files script monsters under Monsters. *Lessons:* Freedoom's
palette has no cyan: keep glowing colours out of palette quantization (true colour shows in the hardware
renderer). Sprites drawn by a script (`art/drone_sprites.py`, a small ray tracer) redraw in a minute, so colour
variants are cheap. **Next:** the mapper said "a few things" for enemies: ask what else; the open items below
still stand.

**2026-11-26: released v0.22.0**, after a long session on Cacobelisk (in-game notes #85-#152 of 11-25/26, and chat;
`maps/cacobelisk/notes.md` has every one). The map gained: the west gutter gone and the cliff edge wandering in, with
dead trees and a railing with a real top; a secret wall with a chaingun in the main passage; a storage room off the
side passage (a wall of boxes at its back, deaf monsters, pickups on boxes) and a long back tunnel to it from a new box
room in the station, ending in a switch that sinks a box as a shortcut; the station's entrance as an arch with window
slits onto zombie guard posts; catwalks above the doors; techbase floors and ceilings tried in turn (now FLOOR0_3,
BROWNGRN); many texture and alignment fixes. **Open:** the switch obelisk's steps 2 and 3, an exit, the station's
machines and monsters (as before).
*Tools:* the asset browser's measuring tool; the validator catches fractional sidedef offsets (one crashed the game);
the movement check knows Floor_MoveToValue. *Lessons:* a thing rests on the highest floor under its square (radius
each way, square to the map): pickups on a moving box near a taller one stay up in the air; keep a radius and a half
clear. Several builds reached the game's copy broken for a minute (unclosed sectors from lines drawn the wrong way
round, a polygon cutting through a door leaf): use `_edges` for every new outline, it turns them round. Writing
`map.py` failed with "Invalid argument" about ten times (fine on retry): **dms should retry its own file writes**.
**Worth building next:** that retry; the movement check treating sectors level with their neighbours as open floor
(the crack's light beam and the arch's shoulders read as narrow gaps); `dms validate` (alone) doesn't know a map's
own textures, though `dms build`'s validation does.

**2026-11-25, end of session: released v0.21.0** (`main`, tag `v0.21.0`; `docs/CHANGELOG.md`, with the whole history
mapped onto versions). The version scheme is in AGENTS.md ("Versions and releases").
**Next, in order:** `docs/projects.md` phase 2 (layered settings: `user\` in the tool repo, project settings on top),
phase 3 (`dms project init`, Start Session choosing a project, Claude started in the project folder with a generated
`CLAUDE.md` and hooks, AGENTS.md split into tool rules and `docs/mapping.md`), phase 4 (Cacobelisk split out with
its history: ask the mapper where its repo lives), then the themes viewer's next steps (two themes side by side
with a seam, a light-source glow). Cacobelisk's open questions are unchanged (its notes.md, and below).

**2026-11-25: themes** (the mapper's idea: a palette of textures that belong together, to keep areas
consistent; `docs/themes.md` has the plan, five milestones). Milestone 1 built: `themes/<name>/theme.toml`
(textures by role, things, decals, atmosphere; shared by every map), `dms themes` / `show` / `check` /
`harvest` (`src/dms/themes.py`). Two themes harvested from Cacobelisk and trimmed by hand: `techbase` (the
start closet, the tech hall) and `grotto` (the passages, vestibule, cistern). 160 tests. Settled with the
mapper: atmosphere is part of a theme; off-theme textures warn; the sky, decals and decoration are roles too.
Then the mapper chose to see the standard scene in the browser, not as a map: **the theme viewer** at
`/themes` (`src/dms/themes.html`, our own WebGL2: the room as a cutaway, every role labelled with leader lines,
alternatives cycled per role). Tuned with the mapper from screenshots: inside view by default, views flown
to, light and fog toggles, faint leader lines lit by hovering a label or a face, labels kept on screen.
Lesson: Claude had no browser, so a geometry bug (floors with no height, NaN) was found by running the page's
build code in Node against `/api/themes`: worth doing before handing over any WebGL change.
**Next:** two themes side by side with a seam, a light-source glow, then choosing in the asset browser.

**2026-11-24, a long session on Cacobelisk (in-game and board notes #73-#140 and chat) and the tools round it.**
155 tests. `maps/cacobelisk/notes.md` has every note; the short of it:

*Cacobelisk now, in play order:* the start as before (the elevator's ride has a sound of its own now); the hall
on the edge of a cliff (no west wall: a low railing, sky beyond), a darker sky that turns red-violet later,
mouldings on its north walls and a crown along the east one; the ordinary obelisks carry a star (the mapper's
artwork), each with a torch behind its altar that flares up green as it is revealed; the **switch obelisk goes
in three steps** (shotgun: revealed; a switch: its violet torch and paint, a niche; an item placed: the sky
turns, and what follows): only step 1 is built, steps 2 and 3 wait in the script for a switch, a niche and an
item that don't exist yet. Behind the great door a bigger vestibule (wooden boxes, torches), the main passage
(bare rock and mud now) and a **side passage** round it (green rock, six torches, an alcove with armour, two
deaf imps), timber frames in the openings; the cistern stairs and the cistern with unlit torches in outcrops,
which flare up one by one when the big door opens; the shotgunner room (crates, a medikit, a twin switch that
sinks) with a tech door under a small red lamp; a tech room; and **the pumping station**, a first layout only
(main pump hall with a pit, pumps and catwalks, corridors, control room, pipe gallery, generator room, storage;
no monsters or items; plain blocks for machines).
**Open:** the switch obelisk's steps 2 and 3 (where the switch and the niche are, what the item is, what
happens after); the station (railings, real machines, water, textures, an exit); an exit for the map; whether
the cistern's green glows should stay under torches that now light; the violet water still greys the weapon.
Much of today is unchecked in the game by Claude: each note says what.

*Tools built today* (all in `AGENTS.md`):
- **A map's own pictures:** `maps/<map>/textures/NAME.png`, packed between TX_START and TX_END (`extras.py`); a
  picture made from Freedoom's needs its licence beside it (`textures/NOTICE.txt`). Used for the star and for
  the eye in the alcoves, where composing in TEXTURES couldn't scale or soften an edge.
- **The asset browser** lists each map's own assets (a violet tag) and what the maps use (a count, "in use
  first"): `src/dms/mapassets.py`. The board opens alone now; the browser is a click away in its banner.
- **Peaceful monsters** (key P in the game, sticks through restarts) and a **No monsters** tick in Start
  Session and Play Map.
- `map.py` helpers worth knowing: `raster()` (rooms from a plan of rectangles: the station), `rough_niche()`,
  `moulded_wall()`, `timber_frame()`, `_stair_wall()` / `_stair_carving()`.

*Lessons:* **read a build's errors before closing its note**: four times a broken build (unclosed sectors, a
dropped drain) reached the game's copy because the note was closed first. TEXTURES: one change per `Patch`
(Translation + Blend kept only the Blend: a red sky); a turned patch lands where its x, y say; a scratch load
proves the engine takes a definition, not how it looks: **measure the mapper's screenshot** rather than guess
(the sky took four rounds until it was measured). Under an open sky, no wall is drawn between two sky ceilings:
don't cut holes with ceilings there (the slit ended as a 3D floor). A sector a later pass matches by name gets
changed by it (`monolith_...`). The game's sector numbers in a note are from the build it runs: go by where the
mapper stood. The 30-minute watch lapses: re-arm at once, a note can land in the gap.
**Builds were slow** (evening): the movement check took 35 s of a Cacobelisk build (303 sectors), because
`Textmap.sidedefs`/`.sectors`/`.vertices` scan every block on each call and it called them per line. It now
works them out once per check (0.9 s, same report). Watch for the same pattern in new code over big maps.
**Worth building next:** the watch re-arming itself or a longer one; a way for Claude to see the game (a
screenshot on request) so less is "unchecked"; `dms rename`; a decal lump for maps (a scaled picture on a wall
without a new texture).

**2026-11-23, a long session on Cacobelisk (72 in-game and board notes, two editor saves) and the tools
round it.** Not committed until the end of the day; 147 tests.

*Cacobelisk now* (`maps/cacobelisk/notes.md` has every note): the start closet in METAL4 with a strip of
track metal along its walls' foot (the map's own texture), both elevator switches twins in 32-wide
niches that a panel shuts once either is used, a block over the secret's target once shot and a puff of
dust from the panel; the hall open to a green cloud sky, walls of big ruined stone (STONE3 at twice its
size), a dirt floor, a stone landing in place of the bridge; water that flows away from the hall
(script), a violet leak from the switch obelisk spreading in half rings where it meets the gutter; the
cacodemon and the cistern's two spectres asleep until hurt or touched; sound blocked so only one pinky
comes at gunfire; a carved satyr with a stimpack shelf, a wooden shell niche; the cistern roofless-dark
with a wooden platform, dais, candles, an armour, and a switch that turns the current south (it then
carries the player, monsters and bodies) and slowly opens a big wooden door on the stairs: a chamber of
six shotgunners (two roused at once, two ordinary, two deaf), a dead end.
**Open:** where that chamber leads and an exit; what the switch obelisk does (still inert); the violet
water turns the weapon grey (sector desaturation: the cure is violet flats of the map's own in
`textures.txt`, with `animdefs.txt`); the sky may want darkening; unverified signs and directions listed
in the notes (water flow, wall seam, step rotation). The movement check warns, wrongly, that imps and
shotgunners can't pass the shaft's foot (it reads 32, it is 48).

*Tools built today* (all in `AGENTS.md`):
- **The board's map pans and zooms**: an SVG beside every PNG (`src/dms/svg.py`), shown inline; labels
  decluttered by zoom (stacked where sectors share a middle), a readout under the cursor, corner buttons
  instead of captions. Seen working by the mapper (notes came from it). Things are drawn by kind
  (monsters red, pickups blue diamonds, the rest grey) in PNG and SVG.
- **Per-map textures** (`src/dms/extras.py`, `maps/<map>/textures.txt`, `animdefs.txt`): composed by the
  engine, text only. Lessons: a Blend colour of digits only is read as a number (write "#808080"); a
  thing on a 3D floor needs a `height`; an upper texture is hung from the lower ceiling unless
  `dontpegtop`, which matters when that ceiling moves.
- **Crashes reach Claude** (`src/dms/gamelog.py`, `[DMS-CRASH]` from `dms watch`); the board won't restart
  the game onto a script that doesn't compile; `dms play` waits for a script check already running.
- **Note screenshots work again** (the folder was passed with backslashes: "\c" + a letter is a colour
  code in a console command; no screenshot had been saved since the map was renamed to *c*acobelisk).
- `dms pull` ignores the editor's 3-decimal rounding; the movement check knows a switch behind a shutter
  at the back of a niche; the validator accepts a flat on a wall; the asset browser's first load shows a
  spinner and real progress.

*Lessons about working this way:* changes to `board.py`, `launch.py`, `live.py` reach the mapper only
when the board is restarted (it starts the game): say so in the note's reply and the game's status line,
since the mapper reads those, not the terminal. Don't try texture or script variants on the map being
played: three builds today had a script that didn't compile (a constant and a method or variable with
the same name, twice more: ZScript ignores case), and a sky definition the engine rejected stopped the
mapper's `dms play`. The "hidden" script check's error window is not hidden: the mapper sees it.
**Worth building next:** a scratch check (compile a script or load a textures file without touching the
map's build), `dms rename`, layer toggles and a gid search on the board's map.

**2026-11-23: the repo root was tidied, and launchers install by themselves** (mapper's request, after Start
Session failed on a fresh clone with `uv is not installed`). The root now holds one script, `Start Session.cmd`;
the other launchers are in `launchers\`, `dms.ps1` and `bootstrap.ps1` in `scripts\`, `dms.toml` and `tools.toml` in
`config\`, the Python project files (`pyproject.toml`, `uv.lock`, `uv.toml`, `.python-version`) in `src\`, this file
in `docs\`; the environment moved to `.tools\venv\` and `tools.local.json` into `.tools\` (`AGENTS.md` "Where things
are"). `dms.ps1` runs `bootstrap.ps1` whenever something is missing. 144 tests. **Entries below this one, and
§3 and §5, use the old paths** (`.\dms.ps1`, `Bootstrap.cmd` in the root, and so on). To try on a clean clone by
the mapper: double-click `Start Session.cmd` and let it install.

**Latest, 2026-11-22: Cacobelisk (`maps/cacobelisk`, kind `example`; was `test2`), 129 tests.** One evening's
map built entirely from 28 in-game notes, five editor saves and chat, every round played live with H. A broken
one-way elevator start (dark closet with emergency light channels, switch in a pulsing niche, track revealed
on the ride, a call switch at the bottom, both switches locking each other), then a fogged hall of six pairs
of obelisks that sink into the floor as the player passes, uncovering carvings, with altars of small pickups;
one, the switch obelisk (violet blood, purple glow, a rumble from inside), brings a dark cacodemon. Its
`notes.md` has the whole history. **Open:** what using the switch obelisk does (it's inert; maybe the
obelisks' "third state", note #8); whether the call switch's niche should get the track metal too.

Tooling done along the way (all in `AGENTS.md`):
- Editor focus: only Edit Map brings the editor forward (Start Session opens several windows).
- Restart crash "User info descriptor too big": `dms_spawn`/`dms_message` are plain local cvars now
  (`nosave`), checked with a 1,657-character message (the old `user` cvars crash). Arrival messages last 4 s
  and old ones are cut short on arrival (a countdown, since `map *` resets `level.totaltime`).
- Board: the sidebar's "In the game" box (H, and `map *` when H leaves you out of bounds); Open Board opens
  the last-picked map and the page remembers a map it was opened on.
- Renders: labels kept apart, with leader lines (`render.place_labels`).
- Movement check: niche switches, Floor_Lower/RaiseByValue past neighbours, scenery (solid blocks,
  monolith tops, `user_scenery`) not reported. Validator: wall textures accepted as flats.
- Script check: re-runs when the devtools mod changes; reads UZDoom's one-line error form too.
- Planned: the asset browser (`docs/asset-browser.md`, six milestones; replaces the texture browser and
  sound tester specs); earmarked: the SVG pan/zoom map (§8).

**Cacobelisk, second session (2026-11-22 evening):** notes #29-#84 and two editor saves, all closed. The map
now runs past the hall: entry secret, the obelisk reveal as a show, purple-obelisk hints, meandering gutters
joined under a 3D-floor bridge and draining under the walls, a great door with a small door, a mossy passage,
and a flooded cistern below the hall. `maps/cacobelisk/notes.md` has the details. **Open:** where the cistern
leads, what the switch obelisk does, an exit.
Lessons: monsters need about twice their width in winding corridors (Doom's 8-direction movement), and
niches with less headroom than a monster block it: now checked on every build (`movement.py` monster fit;
AGENTS.md). Thing numbers: 2048 is a box of bullets, 2049 a box of shells. Texture offsets on a line's parts
(`offsetx_top` ...) are in texture pixels and add to the side's own offset. A middle texture on a two-sided
line is drawn per side. `ambush` monsters are deaf.
Tooling along the way: asset browser favourites (`build/asset-favorites.json`, needs the board restarted),
the banner between the board and the asset browser, both opened as tabs; `dms watch` no longer dies on a
file another program has open for a moment (`edit.wad` mid-save, `inbox.lock`). Offered, not built: a
"read, retrying if locked" helper used wherever dms reads files other programs write.

**The board is no longer optional in a session** (2026-11-22, mapper's call): auto-pull and the game's restart
only work while it runs, so Start Session's window offers just the browser, editor, game and agent, and its own
console window becomes the board once everything is open (`--board-here`, `board=1` in `build/session.txt`).
Tried by the mapper: works.

**The asset browser is up (2026-11-22; seen by the mapper, first fixes done):**
`/assets` on the board (a banner links the two pages; dms opens both, each in its own tab). Rule: it offers only what the game can do (so no music tempo/pitch). Milestones 1-5 of `docs/asset-browser.md` are in a first form (textures and
flats with the 2D/3D audition, things, decals, sounds, music through our own browser synth and the game's soundfont); milestone 6 (Send to Claude,
"used in", `dms assets` in the terminal) is open. Next: M6, then M3.

**No `dms rename` yet** (worth adding): renaming test2 to cacobelisk was by hand: move `maps/<old>` (rename
the script's classes after the map), then copy `build/<old>/history/` (renumbering the new map's builds after
it), `inbox.jsonl`, `shots/` and `pulled/` into `build/<new>/`, so the board keeps the whole run and the notes;
point `build/last-map.txt` at the new name. `build/test2/` is left as it was (git-ignored).

**Lessons from Cacobelisk** (worth keeping in mind for M3):
- UDMF `silent` on a sector silences the *things in it*, not its movement: use `soundsequence = "Silence"`.
  hello-room's yard lifts use `silent` and probably still sound (ask the mapper before changing).
- Check textures in the game: A-GRATE rendered grey with solid black holes, unlike its composited preview.
- ZScript names are case-insensitive (a method `Rumbles` clashed with an array `rumbles`); dynamic arrays
  can't hold `Vector2`.
- Sounds were tuned by ear in steps; the asset browser's sound panel (`docs/asset-browser.md`) should shorten that loop.

**Earlier (late M2, 2026-11-21, 91 tests):**
- **Notes for Claude** from the board, the editor (Ctrl+Shift+N) and the game (key N), `dms watch`/`dms notes`.
- **The live link with the running game** (`src/dms/live.py`): every build rewrites `play.wad` in place; key H
  reloads the map where the player stands; notes are acknowledged in the game, Claude's status shows there
  (`dms status`), and replies pop up. Used all evening for in-game notes #12-#19 on hello-room.
- **"Is Claude listening?"** (mapper's catch: a note sat unseen because no `dms watch` ran): `dms watch` writes a
  heartbeat (`build/claude-watch.json`); the board, the game and the editor say when nobody is watching; a
  `UserPromptSubmit` hook (`.claude/settings.json`, `dms agent-hook prompt`) shows Claude unseen open notes with each
  message (confirmed working); `start-claude.bat` opens each session by asking Claude to arm the watch.
- **Testing automap** (`[play] test_automap`): things as sprites, keys, trigger lines, lighter skull-lock colours.
  **Mapper confirmed it in the game: "worked perfectly".**
- **Parked:** hello-room's lost-soul yards (alarm doesn't wake them; side souls can't find their way out; see
  `maps/hello-room/notes.md`), waiting on per-map ZScript (M2 list, §8).

- **Start Session** (`Start Session.cmd`, `dms session`; mapper's request): one window to pick or create a map and
  tick what to open (board, browser, editor, game windowed, agent); a Claude already running in the repo is handed
  the map instead of a second one starting (hooks record sessions, `src/dms/agents.py`). Mapper, first run:
  "this is so perfect".

- **Per-map ZScript** (`maps/<map>/zscript.zs`, `src/dms/scripts.py`): packed into the map's WAD, its event
  handlers registered for that map only, compile-checked on every build by a hidden UZDoom load (errors with line
  numbers; a broken script never reaches the game). First use: hello-room's `HelloRoomYards` wakes the yard souls
  when the lift trigger fires (replacing the NoiseAlert line that never worked). **Works in the game** (mapper:
  "seems good"; log: `[DMS] HelloRoomYards: the yards rise; woke 5 lost soul(s)`).
  Also: the mapper's 20:12 editor save (room, hallway, hex corners, ledges) ported into `map.py`; `dms watch` now
  reports saves waiting to be ported (`[DMS-EDIT]`), which is how that one went unnoticed.
- **One live copy per game start** (`play-<n>.wad`): an old game that outlived a restart read the new copy's
  script where its map had been ("Map does not define a namespace"); `dms play` won't start a second game.
- **Request order** across editor, game, board and chat agreed with the mapper and written into `AGENTS.md`.
- **Parked by the mapper:** the screenshot tour and the test map overlay (§8).

**M2 is done (2026-11-21).** **Next: M3**, the first real map: read `docs/map-design-notes.md` first; Fable is
suggested for the layout work.

**Earlier in M2** (69 tests at the time): `dms catalog` (`catalog/`), the validator (runs in every build;
`dms validate [--edit]`), the renderer (`render.png/.txt` and `diff.png/.txt` per build; `dms render --edit`), and the
`DmsBridge` editor plugin (live reload of `edit.wad`, `editor-state.json`), with `dms build` refreshing `edit.wad`.

**Editor plugin live-tested with the mapper (2026-11-21): works.** Claude's rebuilds show up in the open editor in
place (view, zoom and mode kept); with unsaved changes the reload waits and the status bar warns; undoing every edit
lets it reload. Fixed along the way: the editor holds `edit.wad` open (overwrite in place instead of replace); undo
doesn't clear the editor's "changed" flag (no undo levels left = clean); the warning only fired once and faded (now
per version, repeated every 10 s); `build --force` didn't discard saved edits in `edit.wad`; the editor opened behind
other windows (the plugin brings it to the front once). `MapBuilder.two_sided` added for the test platform.
One unexplained hiccup: a build once failed writing `maps/hello-room/TEXTMAP` ("Invalid argument"), fine on retry;
probably antivirus or a file watcher. If it recurs, add a short retry to file writes.

**The board is built** (`Open Board.cmd` / `dms board`, `dms build --note`; build history in
`build/<map>/history/`). "Send to Claude" from the board comes later, with `dms watch`.

**`dms pull` is built** (`Pull Map.cmd`; overrides in `maps/<map>/overrides.toml`, TOML rather than the YAML
planned in §6, matching the other config files). Tried on a real save with the mapper (tweaks, a comment, an added
shotgun ported by Claude). The board auto-pulls saves while it runs (mapper's idea); structural saves wait there.

**The edit loop works end to end (mapper, 2026-11-21: "working REALLY WELL").** Claude builds -> the open editor
reloads in place and the board shows the build; the mapper saves in the editor -> auto-pull keeps the tweaks, rebuilds,
and the board shows it within a second or two. Fixed on the way: the plugin's reload leaked a handle on `edit.wad`
(saves failed "locked by Builder"; it now closes the map before reopening), and `Edit Map` no longer starts a second
editor on a map that's already open (it brings that one to the front). 63 tests.

**The movement check is built** (`src/dms/movement.py`, runs in every build; see `AGENTS.md`). Hello room has a
demo ledge 40 up with a soulsphere, which it flags. Not handled yet: teleporters, crushers, scripts.

**M1 is done.** `maps/hello-room` (a 512 x 512 greybox room) is generated by `map.py`, built, played and edited
through `Play Map.cmd` / `Edit Map.cmd` (with the map picker); the mapper confirmed play, edit and F9 from the editor.
`AGENTS.md` lists the commands. 28 tests. Findings along the way:
- `dms edit` must pass `-scriptconfig zdoom_acs.cfg` (opening with `-map` skips the editor's default compiler).
- UZDoom 5 writes `+logfile NAME` to `log-NAME.txt` in its working directory; `dms play` runs it from `build/<map>/`.
- `-norun` loads everything without a window (exit code 1337): a possible automatic load check for M2.

**`user_gid` test (mapper split, copied and divided lines in the editor, then saved; 2026-11-21):**
- Untouched elements keep their `user_gid` and all other fields; the editor drops TEXTMAP comments (our hash header)
  and adds a `ZNODES` lump. Vertices have no gid (we don't give them one).
- **Splitting a line copies its gid to both halves** (`room.wall_n` on two lines, with their sidedefs).
- **Copy/paste copies the gid too** (a third `room.wall_n`; a lone pasted line had no sidedefs at all).
- **Dividing a sector gives both halves the original sector's gid** (`room` twice). The new dividing line and its
  two sidedefs have **no** gid.
- So a gid is a **lineage** ("came from"), not a unique key. `pull` (M2) must expect duplicates and missing gids:
  match by gid, then by position among same-gid elements; anything with a duplicated or missing gid is a geometry
  change for the report, not a property tweak.
- Values the editor lets through that Doom can't use (a sector light of 99999 was entered): validator rules (M2)
  should check ranges like light 0-255.

**M0** (step-by-step history is in git). What exists from it:
- `AGENTS.md`: the rules and commands. Read it first.
- `Bootstrap.cmd` / `bootstrap.ps1`: uv 0.13.9 and Python 3.14 into `.tools\`, then `uv sync` and `dms setup`.
- `dms setup`: UZDoom 5.0.3, Ultimate Doom Builder R4336, Freedoom 0.13.0 (pinned in `tools.toml`, hash-checked),
  then configures both tools so they stay in the repo and F9 in the editor runs UZDoom.
- `Open Editor.cmd` / `dms editor`. `dms.toml` for project settings (music off in test-play).
- 15 tests (`tests/`).
- **The mapper confirmed** the editor setup and F9 test-play end to end.
- **Nothing-outside-the-repo check** done against a snapshot taken before bootstrap: no new registry keys, Python
  shortcuts or tool folders in the user profile. A uv lock file in the system TEMP was found and fixed (TEMP now
  points into `.tools\tmp\`). The one remaining write is UZDoom's graphics cache in `%LOCALAPPDATA%\doom\`,
  which can't be redirected (a known exception in `AGENTS.md`).
- `docs/map-design-notes.md`: **not yet read by Claude.** Read before M3.

**Next: M2, Tooling** (§8, §6): catalog, validator, renderer, movement check, `pull` (with the gid findings above),
screenshot tour, in-game and editor notes, `dms watch`. Suggested order: catalog -> validator -> renderer (Claude needs
it to see maps) -> `pull` -> movement check -> notes/watch -> tour.

**Decided (M1): picking a map from Explorer.** Interactive menus are the default: double-clicking a map
launcher (`Play Map.cmd`, `Edit Map.cmd`, later `Pull Map.cmd`) opens a picker window listing the maps.
Dropping a map folder onto the launcher still works and skips the picker. A drop zone inside the picker
window was considered and left out (dragging between Explorer panes is the awkward part; it would also need
an extra package); easy to add later if wanted.

**Model choice:** Opus for most milestones (M2 included: geometry and matching logic).
**Use Fable for M3** (first real map): spatial layout and design judgment are where it should pay off.

**Still to verify:** whether the Visual C++ runtime is needed (needs a clean machine or VM);
the ZScript note text box and crosshair trace (M2).

---

## 10. Other decisions

- **Diff render:** each `build` of a map also writes `build/<map>/diff.png`, a before/after
  top-down image against the previous build (added green, removed red, changed yellow),
  so the mapper sees at a glance what changed.
- **Feedback screenshots** are not committed (temporary). Takeaways go into map sources or `src/`.
- **Style: greybox.** A small fixed set of plain Freedoom textures, colour-coded by
  purpose (wall, door, lift, switch, secret, exit). No art direction yet.
- **Difficulty:** every thing on every skill level; play at the default (Hurt Me Plenty).
  A difficulty pass comes much later.
- **Maps in this repo are MIT**, like everything else. Long-term, this repo is the tool, and a
  mapping project can live anywhere outside it. So don't hard-code the assumption that maps only live in `maps/`.
