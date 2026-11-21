# DOOM Map Workshop — Plan

A workflow where Claude writes DOOM levels and the mapper views them in an editor,
test-plays them in the engine, and gives feedback for the next round.

Status: **planning complete; M0 not started.** Remaining unknowns are marked *to verify* inline.

---

## 1. The loop

```
Claude edits source ──► build ──► validate + render PNG ──► Claude checks the PNG
        ▲                                                       │
        │                                                       ▼
   feedback (notes, marks, screenshots, log) ◄── the mapper views in UDB / plays in UZDoom
```

One iteration should be: Claude runs `build`, then the mapper runs `play` (or presses F9 in UDB).

### Supported environment

- **OS:** Windows 11 only. Scripts are PowerShell (`.ps1`), with no bash/macOS/Linux support.
- **Agent:** Claude Code only. Other agents may work, but nothing is done to make sure of it.
- The README says both plainly.

### Self-contained: everything lives in the repo root

**Goal:** everything needed to work in this environment is installed into, configured in, and run from
the repo folder. Nothing goes into Program Files, `%APPDATA%`, `%LOCALAPPDATA%`,
Documents or the registry. Deleting the repo folder removes everything.

- **System prerequisites:** Windows 11 (PowerShell and .NET Framework 4.8 come with it), git, GPU drivers.
  Possibly the Visual C++ runtime (to verify; if needed, try app-local DLLs before a system install).
- **Claude Code itself** is the one exception: it lives in the user profile and keeps its
  own settings in `~\.claude`. Settings for this project go in `.claude\settings.json` in the repo.
- **uv:** a standalone `uv.exe` fetched by `bootstrap.ps1` into `.tools\uv\`, not installed with winget.
- **uv's Python and cache:** redirected to `.tools\python\` and `.tools\uv-cache\`.
  Preferred: a committed `uv.toml` with `cache-dir` / `python-install-dir` (to verify those
  keys exist), so even running bare `uv` stays inside the repo. Fallback: the `UV_*`
  environment variables set in `dms.ps1`.
  - This isn't conventional Python practice (normally uv, its Pythons and its cache are
    shared machine-wide). It's a deliberate choice for this project, and AGENTS.md and the
    README should say so.
  - Side benefit: with the repo on D:, a cache inside the repo is on the same drive as `.venv`,
    so uv can hard-link packages instead of copying them.
- **UZDoom:** always launched with `-config .tools\uzdoom\uzdoom.ini`, with the save and
  screenshot folders pointed inside the repo. This works whether or not UZDoom has a portable mode.
- **Isolation from any global Python/uv** (we never touch PATH or global config, so
  nothing leaks out; these settings stop global things leaking in):
  - `uv.toml`: `required-version` pins uv (a different global uv refuses to run);
    `python-preference = "only-managed"`; every setting that matters is set explicitly,
    since a user-level `%APPDATA%\uv\uv.toml` would otherwise apply too.
  - `.python-version` pins the Python version.
  - `dms.ps1` calls `.tools\uv\uv.exe` directly, never a `uv` on PATH, and clears `PYTHONPATH`,
    `PYTHONHOME`, `VIRTUAL_ENV`, `PIP_*` and outside `UV_*` variables before running.
  - **To verify in M0:** whether uv registers its Pythons in the Windows registry (HKCU) or puts
    `python3.x.exe` shortcuts in a user folder. If so, turn that off (uv's no-registry /
    no-shortcut options or environment variables).
- **Ultimate Doom Builder:** always launched with `-portable`.
- **Entry point:** `.\dms.ps1 <command>` in the repo root sets the environment variables and runs
  `uv run dms <command>`, so nothing falls back to the default locations in the user profile.
- **Check:** after a fresh bootstrap plus a build/play/edit cycle, look in the user profile and confirm nothing new appeared.

### Habits we keep anyway (cheap, and they help Claude too)

- **Commands:** the real interface is one Python command, run as `.\dms.ps1 <command>`.
  Any other `.ps1` scripts are thin wrappers around it.
- **Knowledge lives in the repo:** `AGENTS.md`, `docs/` and `maps/*/notes.md`, not
  in Claude's private memory.
- **Rules live in scripts:** overwrite protection and similar checks go in `dms`,
  not in Claude Code hooks.
- **Text alongside images:** every image output (render, tour) also has a text report.
- **Doom reference:** `docs/udmf-cheatsheet.md` covers the fields we use, line
  specials, thing IDs and Doom's movement limits.

### Licensing rules (to go into AGENTS.md)

- The repo is **MIT** (`LICENSE`), covering our code, scripts, maps and docs.
- **Never commit third-party binaries or IWADs** (UZDoom, Ultimate Doom Builder,
  acc, freedoom2.wad). `dms setup` downloads them into the git-ignored `.tools/`.
- Freedoom texture/flat/thing **names** in `catalog/` are fine. If Freedoom
  **graphics** are ever committed, include Freedoom's BSD license notice with them.
- ZScript/ACS is written from scratch. Don't copy from UZDoom's built-in scripts
  (GPL) or other mods without checking their license first.

### Writing conventions (to go into AGENTS.md)

- **Keep it impersonal:** repo files refer to roles ("the mapper", "the dev machine"),
  not to the person, their computer or their accounts and subscriptions. Anyone could be
  doing this work. The repo URL and the LICENSE copyright line are the exceptions.
- **Text files are UTF-8 without a BOM.** Windows PowerShell 5.1's `Set-Content` /
  `Out-File` add a BOM by default, so use `[IO.File]::WriteAllText` with
  `UTF8Encoding($false)`, or the editing tools.

### Who each document is for

| File | Audience | Role |
|------|----------|------|
| `AGENTS.md` | agents | **Source of truth** for how to work in this repo: conventions, commands, rules |
| *(no CLAUDE.md)* | Claude Code | Not needed: Claude Code ≥ v2.1.277 reads AGENTS.md natively when no CLAUDE.md exists (default "Project instructions" mode; dev machine is on 2.1.330). Adding a CLAUDE.md would take priority, so if one is ever needed it must `@AGENTS.md`. |
| `docs/` | agents + humans | Detailed reference and design notes, linked from AGENTS.md |
| `maps/*/notes.md` | agents + mapper | Design intent and feedback history for each map |
| `PLAN.md` | mapper + Claude | Roadmap and open decisions; settled items move into AGENTS.md/docs |
| `README.md` | **the public** | A readable summary of the project. **Never a source of truth**: it is written *from* the files above, and agents don't use it for instructions. It's updated when something people would notice changes. |

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

Everything installs into the repo (see "Self-contained" in §1).

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

A committed `tools.toml` lists each tool with its official source, a pinned version, a filename pattern for the download, and a SHA256 hash:

| Tool | Source | Notes |
|---|---|---|
| UZDoom | github: UZDoom/UZDoom releases | Portable Windows zip |
| Ultimate Doom Builder | github: UltimateDoomBuilder/UltimateDoomBuilder releases | Includes `acc` in `Compilers\` (to verify) |
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
- To verify in M0: the exact UZDoom game config filename in `.tools\udb\Configurations\`.

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
├── uv.toml              keeps uv's Python + cache inside .tools\ (if supported)
├── .python-version      pinned Python version
├── pyproject.toml       Python project + dependencies (uv)
├── uv.lock              pinned dependency versions
├── tools.toml           pinned versions + hashes of the Doom tools (`dms setup`)
├── tools.local.json     resolved tool paths (git-ignored)
├── .tools/              everything downloaded (git-ignored): uv, Python, uv cache,
│                        UZDoom (+ its ini, saves), Ultimate Doom Builder (+ portable settings), Freedoom
├── maps/                one self-contained folder per map, named by name (see §5a)
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
                         last generated TEXTMAP, fingerprints, render, tour/, play.log
```

### 5a. Several maps at once

- **Named by name:** maps are identified by a name (`light-test2`), never by slot. Built
  on its own, a map always goes into the **MAP01** slot of its own WAD.
- **Self-contained:** everything a map owns (sources, notes, per-map resources, build
  output, feedback, UZDoom saves in `.tools\uzdoom\saves\<map>\`) is kept under its name.
- **Map name always explicit:** every map command requires the name (`dms build light-test2`)
  and prints which map it's acting on. No hidden "current map" setting. Tab-completion in `dms.ps1` is optional.
- **Switching:** when work moves to a map, Claude reads its `notes.md` first.
- **Shared code stays safe:** `src/` and `resources/devtools/` are shared. TEXTMAP is
  committed, so a generator change only affects a map when it's rebuilt, and the change
  shows up in git. Maps edited by hand in TEXTMAP are never regenerated.
  `dms build --all` + review the diff after generator changes.
- **Releases (later):** `episodes/<name>.toml` assigns maps to slots;
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
- **Engine log**: `play.log` shows script errors and warnings, which Claude reads after a play session.
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

*Handoff from the planning session (2026-11-21). A new session starts here.*

**Done:**
- Planning: everything in this file was discussed and agreed with the mapper. Decisions in §2 and §10 are final.
- Repo cloned; the working folder is renamed to match it (`doom-map-stack`).
- `docs/map-design-notes.md` added: the mapper's design guidelines. **Not yet read by Claude.** Read before M3.
- `.gitignore`: Python template + `.tools/`, `tools.local.json`, `feedback/`.

**Nothing built yet.** No AGENTS.md, no `src/`, no scripts.

**Next: M0** (§8), roughly in this order:
1. Write `AGENTS.md`. Move the settled rules from §1 (self-contained, licensing, writing
   conventions, who each document is for) and §5a into it. Confirm with `/memory` that it loaded.
2. `bootstrap.ps1`, `dms.ps1`, `uv.toml`, `.python-version`, `pyproject.toml` with a stub `dms` command.
3. `tools.toml` + `dms setup`: UZDoom, Ultimate Doom Builder, Freedoom 0.13.0 into `.tools\`, hashes checked.
4. Configure Ultimate Doom Builder in portable mode; check that F9 launches UZDoom.
5. Check that nothing was written outside the repo.

**Still to verify** (marked inline): uv `cache-dir` / `python-install-dir` / registry behavior;
UZDoom `-config` and save/screenshot folders; whether the Visual C++ runtime is needed;
the Ultimate Doom Builder UZDoom game config filename and whether `acc` is bundled;
the ZScript note text box and crosshair trace; whether the editor keeps `user_gid`.

**Also decide in M0:** a `.gitattributes` for line endings. Git currently warns that it
will convert LF to CRLF; TEXTMAP and scripts should probably stay LF.

Once AGENTS.md takes over the rules, this section can be trimmed. PLAN.md then stays the roadmap.

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
