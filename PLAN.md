# DOOM Map Workshop — Plan

A workflow where Claude writes DOOM levels and the mapper views them in an editor,
test-plays them in the engine, and gives feedback for the next round.

Status: **M0 done; M1 next** (see §9). Remaining unknowns are marked *to verify* inline.

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

---

## 8. Milestones

- **M0, Setup:** `bootstrap.ps1` + `dms.ps1`; `pyproject.toml` and `tools.toml`; `dms setup` working,
  including configuring Ultimate Doom Builder in portable mode; check that nothing was written outside the repo; `.gitignore` updated; AGENTS.md written (confirm with `/memory` that Claude Code loaded it).
- **M1, Hello room:** one square room with a player start, packed and playable. Proves the whole loop.
  Also check that Ultimate Doom Builder keeps `user_gid` fields when saving, including on lines it splits or copies.
- **M2, Tooling:** catalog, validator, renderer, movement check, screenshot tour,
  in-game notes, editor notes (comment field), `dms watch` live delivery.
- **M3, First real map:** a small layout (3–5 rooms, a key door, a lift, a secret), iterated on the mapper's feedback.
  Claude reads `docs/map-design-notes.md` first, and turns any guidelines that can be checked into validator rules where practical.
- **M4, Generator library grows** from whatever M3 needed repeatedly.
- **Later:** ACS scripting, custom textures, multi-map episode, MAPINFO, music.

---

## 9. Where we left off

*Updated at the end of M0 (2026-11-21). A new session starts here.*

**M0 is done** (step-by-step history is in git). What exists now:
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

**Next: M1, Hello room** (§8): one square room with a player start, packed and playable; proves the loop.
Roughly: UDMF TEXTMAP writer (+ reader), packer (`build/<map>/<map>.wad`), `dms new`, `dms build`, `dms play`,
`dms edit` (packs `build/<map>/edit.wad`, opens it; Save then writes inside the repo with no dialog), and `.cmd`
launchers for the mapper-facing ones. Then check that the editor keeps `user_gid` when saving (also on split or copied lines).

**Decided (M1): picking a map from Explorer.** Interactive menus are the default: double-clicking a map
launcher (`Play Map.cmd`, `Edit Map.cmd`, later `Pull Map.cmd`) opens a picker window listing the maps.
Dropping a map folder onto the launcher still works and skips the picker. A drop zone inside the picker
window was considered and left out (dragging between Explorer panes is the awkward part; it would also need
an extra package); easy to add later if wanted.

**Model choice:** Opus for most milestones; Sonnet is fine for the routine scripting in M1.
**Use Fable for M3** (first real map): spatial layout and design judgment are where it should pay off.

**Still to verify:** whether the Visual C++ runtime is needed (needs a clean machine or VM);
the ZScript note text box and crosshair trace (M2); whether the editor keeps `user_gid` (M1).

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
