# AGENTS.md

How to work in this repo. This file is the **source of truth** for conventions, commands and rules.
Claude Code reads it natively (there is deliberately no `CLAUDE.md`; if one is ever needed, it must `@AGENTS.md`).

## What this is

A workflow where Claude writes DOOM levels and the mapper views them in an editor (Ultimate Doom Builder),
test-plays them in the engine (UZDoom), and gives feedback for the next round:

```
Claude edits source ──► build ──► validate + render PNG ──► Claude checks the PNG
        ▲                                                       │
        │                                                       ▼
   feedback (notes, marks, screenshots, log) ◄── the mapper views in UDB / plays in UZDoom
```

One iteration should be: Claude runs `build`, then the mapper runs `play` (or presses F9 in the editor).

Settled choices: UDMF (text TEXTMAP) maps, UZDoom only (no vanilla/Boom compatibility),
Freedoom2 0.13.0 as the IWAD, jump and crouch off. `docs/PLAN.md` §2 has the full list.

## Start of every session

1. Read `docs/PLAN.md` §9 "Where we left off": what's done and what's next. `docs/PLAN.md` is the roadmap;
   settled rules live here, not there.
2. Before designing or changing a map, read `docs/map-design-notes.md`.
3. When work moves to a map, read its `maps/<map>/notes.md` first.

## Where things are

The repo root holds one script, **`Start Session.cmd`**, and the files that have to be there (`AGENTS.md`,
`README.md`, `LICENSE`, `.gitignore`, `.gitattributes`). Everything else is in folders; don't add files to the root.

| Folder | What's in it |
|--------|--------------|
| `launchers\` | The other double-click launchers (`Edit Map.cmd`, `Play Map.cmd`, `Pull Map.cmd`, `Open Board.cmd`, `Open Editor.cmd`, `Bootstrap.cmd`) and the agent launchers (`start-claude.bat`) |
| `scripts\` | `dms.ps1` (the entry point for every command), `bootstrap.ps1`, `dms-env.ps1` |
| `config\` | `dms.toml` (project settings), `tools.toml` (the pinned Doom tools) |
| `src\` | The Python project: `pyproject.toml`, `uv.lock`, `uv.toml`, `.python-version`, the `dms` package (`src\dms\`), the editor plugin (`src\udb-plugin\`). uv is always run with `--project src` |
| `maps\`, `catalog\`, `resources\`, `docs\`, `tests\` | Maps, the IWAD's texture names, the devtools mod, documents (`docs\PLAN.md` is the roadmap), tests |
| `themes\` | Themes shared by every map: `themes\<name>\theme.toml` (`docs\themes.md`) |
| `.tools\`, `build\` | Git-ignored: downloads, the Python environment (`.tools\venv\`), `tools.local.json`; build output |

`src/dms/paths.py` has these locations for the code.

## Supported environment
- **Windows 11 only.** Scripts are PowerShell (`.ps1`); no bash/macOS/Linux support.
- **Claude Code only.** Other agents may work, but nothing is done to make sure of it.
  (Claude Code reads AGENTS.md natively from v2.1.277 when no CLAUDE.md exists.)
- The README says both plainly.

## Self-contained: everything lives in the repo folder

Everything needed to work here is installed into, configured in and run from the repo folder.
Nothing goes into Program Files, `%APPDATA%`, `%LOCALAPPDATA%`, Documents or the registry.
Deleting the repo folder removes everything.

- **System prerequisites only:** Windows 11 (PowerShell and .NET Framework 4.8 come with it), git, GPU drivers.
- **Exception:** Claude Code itself lives in the user profile (`~\.claude`).
  Settings for this project go in `.claude\settings.json` in the repo.
- **Downloads go in `.tools\`** (git-ignored): uv, Python, the uv cache, UZDoom (with its ini and saves),
  Ultimate Doom Builder (with its portable settings), Freedoom.
- **uv:** a standalone `uv.exe` in `.tools\uv\`, fetched by `bootstrap.ps1`. Never install uv with winget
  or use a `uv` from PATH. uv's Pythons and cache go in `.tools\python\` and `.tools\uv-cache\`.
  This isn't conventional Python practice (normally they're shared machine-wide); it's a deliberate choice for this project.
- **Isolation from global Python/uv:** `src\uv.toml` pins the uv version (`required-version`) and sets
  `python-preference = "only-managed"`; `UV_CONFIG_FILE` makes uv ignore a user-level `%APPDATA%\uv\uv.toml`; `src\.python-version` pins Python;
  `dms.ps1` clears `PYTHONPATH`, `PYTHONHOME`, `VIRTUAL_ENV`, `PIP_*` and outside `UV_*` variables.
- **UZDoom** runs in its portable mode (`uzdoom_portable.ini` next to the exe, created by `dms setup`), so its config,
  saves (`Save\`) and screenshots (`Screenshots\`) stay in `.tools\uzdoom\`.
- **Ultimate Doom Builder** is always launched with `-portable`, so its settings stay in `.tools\udb\`, and with
  `TEMP`/`TMP` pointed at `.tools\tmp\` (it builds the F9 test WAD there).
- **Known exceptions** (outside our control; caches only, safe to delete):
  - UZDoom writes its graphics cache to `%LOCALAPPDATA%\doom\uzdoom\` (`vulkanpipelinecache`, or the OpenGL shader cache)
    even in portable mode: it asks Windows for that folder directly, and neither renderer can turn the cache off.
  - Windows file dialogs remember the last-used folder per program in the registry.
- Never change PATH, global config or anything in the user profile.

## Commands

The real interface is one Python command, run as **`.\scripts\dms.ps1 <command>`** from the repo root.
It sets the environment and runs `uv run dms <command>`. Any other `.ps1` scripts are thin wrappers around it.

- `.\scripts\bootstrap.ps1` (**`launchers\Bootstrap.cmd`**): the install: fetches uv (hash-checked), installs Python into
  `.tools\python\`, `uv sync` (the environment goes in `.tools\venv\`), `dms setup`. Safe to re-run; it only fills in
  what's missing. **Nobody has to run it by hand:** `dms.ps1` runs it first whenever uv, the environment or
  `.tools\tools.local.json` is missing (`Test-DmsInstalled`), so on a fresh clone the first launcher or command
  installs everything, then carries on. The exception is `agent-hook` (Claude Code's hooks): it exits quietly
  and leaves the install to a real command.
- `dms setup [--upgrade <tool>]`: downloads the Doom tools pinned in `config\tools.toml` (UZDoom, Ultimate Doom Builder,
  Freedoom) into `.tools\<name>\`, checks hashes, writes `.tools\tools.local.json`. Skips tools already at the pinned version.
  `--upgrade <tool>` reinstalls one after its pin changes, keeping the files in its `preserve` list (settings, saves).
  An entry hand-edited in `.tools\tools.local.json` with `"managed": false` points at an outside install and is left alone.
  It also configures the tools (`src/dms/configure.py`): UZDoom portable mode; in the editor's `UDBuilder.cfg`, the
  UZDoom UDMF game config as the default for new maps, UZDoom as the F9 engine, `uzdoom.pk3` (excluded from testing)
  and `freedoom2.wad` as resources, and the Open dialog starting in `build\scratch\`.
- `dms editor [wad]` (**`launchers\Open Editor.cmd`**): opens the editor. Re-applies the settings above first, because the
  editor rewrites `UDBuilder.cfg` on exit.
- **`config\dms.toml`**: committed project settings, applied at the next editor launch. `[play] music = false` makes
  test-play run UZDoom with `-nomusic` (per launch; nothing is saved in UZDoom's settings).
  `[play] test_automap = true` (default) gives test-play (F9 and `dms play`) a testing automap: all things shown
  (`am_cheat 2`, not saved) as their sprites, keys always, every trigger line coloured; set explicitly on every
  launch, on or off, since UZDoom saves the other three in its ini (`configure.TEST_AUTOMAP`). The devtools mod's
  `LOCKDEFS` gives skull locks lighter map colours than card locks (`dms play` only).
- Tests: `. .\scripts\dms-env.ps1; Invoke-DmsScope -Root $PWD -Body { & .tools\uv\uv.exe run --locked --project src pytest -q -p no:cacheprovider }`

**Projects** (`src/dms/project.py`; plan and status: `docs/projects.md`): maps can live outside the tool, in a
project folder anywhere (`dms-project.toml`, `maps/<name>/`, `themes/`, a git-ignored `build/` with everything
generated, game saves included). The tool repo is itself the default project (its example maps; no marker file
in its root). Which project: `dms --project PATH <command>`, else `DMS_PROJECT`, else the folder the command
runs in (or the nearest above with a `dms-project.toml`), else the tool repo; `cli.main` decides once and sets
`DMS_PROJECT`, and library code reads only that (`project.path(root)`), never the current folder. A map knows its
project (`MapInfo.project`: the folder above its `maps/`), so `info.build_dir(root)` is in it. `dms project`
shows the current one. Still to come: layered user settings, `dms project init`, Start Session's project
picker, Claude in the project folder, Cacobelisk moved out.

Map commands take a map name (`maps/<name>` in the current project) or a path to a map folder:
- `dms new <name> [--kind map|test|example]`: creates `maps/<name>/` with `map.toml`, `map.py` (one room) and `notes.md`.
- `dms list`: the maps in `maps/`.
- `dms build <map> | --all [--force] [--note TEXT]`: generated maps run `map.py` and write `TEXTMAP` (first line: a hash of the
  content); then packs `build/<map>/<map>.wad` (MAPINFO with title/sky/music and `nojump`/`nocrouch`; the map in MAP01).
  Refuses to overwrite a generated `TEXTMAP` that was edited by hand, or to build while `build/<map>/edit.wad` has
  editor changes not brought back yet; `--force` discards them.
- `dms play [<map>] [--skill N] [--nomonsters]` (**`launchers\Play Map.cmd`**): builds if the sources changed, starts UZDoom.
  Console log: `build/<map>/log-play.txt` (read it after a play session; UZDoom 5 names logs `log-<name>.txt`
  in its working directory, so play runs UZDoom from `build/<map>/`). Saves: `build/<map>/saves/` in the map's project (moved there from `.tools/uzdoom/saves/<map>/` on the next play).
  **A quiet look round:** key **P** in the game (`dms_peaceful_key`, rebindable; the devtools mod's `DmsPeaceful`)
  turns peaceful monsters on and off: they don't notice the player, and any after the player anyway are sent
  back to idling; "Peaceful (P)" shows in the corner. It sticks through H and restarts: each change is logged
  (`[DMS-PEACEFUL] 0|1`) and the next `dms play` on the map starts the same way (`launch.last_peaceful`,
  `+set dms_peaceful`). `--nomonsters` starts with none at all (things a map's script spawns still appear);
  Start Session and the Play Map window have a "No monsters" tick for it (`[session] nomonsters`, `dms session <map> --nomonsters`).
- `dms edit [<map>]` (**`launchers\Edit Map.cmd`**): packs `build/<map>/edit.wad` from `TEXTMAP` and opens it in the editor,
  so Save writes there. If the mapper already saved changes in it, it is reopened as it is, not overwritten.
- **Live reload in the editor:** `dms setup` compiles `src/udb-plugin/DmsBridge.cs` (Windows' own C# compiler,
  .NET Framework 4.8, so C# 5) into `.tools/udb/Plugins/DmsBridge.dll`. For maps opened through `dms edit`, the
  plugin reloads `edit.wad` in place (view, zoom and mode kept) when it changes on disk, unless the mapper has
  unsaved changes (then it says so in the status bar), and writes `build/<map>/editor-state.json`
  (`open`, `unsaved_changes`). After a build, `dms` refreshes `edit.wad` from the new `TEXTMAP` whenever the
  mapper has no saved edits in it, so **an open editor shows Claude's change within a second or two**. A save that
  doesn't change the map data (only nodes) doesn't count as an edit. Details (live-tested 2026-11-21):
  - The editor keeps `edit.wad` open: it can't be replaced, only overwritten, so `wad.write` falls back to writing in place.
  - With unsaved changes the plugin warns (sound once per new version, the text again every 10 s). Undoing every
    edit counts as clean (the editor's own "changed" flag doesn't clear on undo), so the reload then happens.
  - `dms build --force` discards the mapper's saved edits in `edit.wad` too, and the open editor reloads.
  - `dms edit` (Edit Map) brings the editor to the front once the map opens (Windows would leave it behind):
    it writes `build/<map>/edit-front.request`, which the plugin uses up. Start Session doesn't (it opens
    several windows at once), not even for an editor that's already open.
  - Reload = the editor's internal `CloseMap()` then `OpenMapFileWithOptions()` (both by reflection). Without the
    close, the old map's handle on `edit.wad` leaked and the next save failed with "target file is locked by Builder".

- `dms pull [<map>] [--ported]` (**`launchers\Pull Map.cmd`**): brings the mapper's saved editor changes (`edit.wad`) back
  into the map's source (`src/dms/pull.py`). Compares the save with `TEXTMAP` (what `edit.wad` was packed from),
  matching elements by `user_gid`. Property tweaks (light, heights, textures, offsets, flags, a thing's
  position/angle/type) go to **`maps/<map>/overrides.toml`** (`src/dms/overrides.py`; keyed by kind and gid; every
  build applies it after `map.py`). Editor comments (UDMF `comment`) are appended to the map's `notes.md` as
  requests. Structural changes (moved vertices; new, removed, split or copied lines/sectors/things) are listed in
  `build/<map>/pull.txt` and nothing is written: **Claude ports them into `map.py`, then runs
  `dms pull <map> --ported`**. Then it rebuilds (the editor reloads), checks the result against the save and keeps
  the save in `build/<map>/pulled/`. A line whose ends differ by no more than 0.001 hasn't moved (the editor saves 3 decimals). Refuses while the editor has unsaved changes. Hand-edited maps: the save
  becomes `TEXTMAP`. It also draws `render-edit.png`/`diff-edit.png`: look at them, and read the requests.
  Claude looks at `overrides.toml` for patterns: if a whole room got the same tweak, fix `map.py` and drop those
  overrides.
- **Notes for Claude** (`src/dms/inbox.py`): one inbox per map, `build/<map>/inbox.jsonl` (append-only JSON lines,
  so the board, the editor plugin and the game can all write to it). Each note has its source, position, what it's
  about (sector/line/thing with its gid), the build it was made on, optional screenshot, and the mapper's text.
  - `dms notes [<map>] [--all]` lists open notes; `dms notes <map> --close ID --reply "what was done"` closes one
    (the reply shows on the board and in its console).
  - **Images cost tokens** (about width x height / 750 each, after scaling to ~1568 px max): a 1920x1080 game
    screenshot ~1,800, a 1024 render ~1,400, a note's text ~100. Read the note's text (position, facing, what
    it's about, with gids) first; open the image only when the words aren't enough, and then the note's
    `preview` (960-wide JPEG, ~700), not the full-size `screenshot`.
  - `dms watch [<map>]` prints open notes, then each new one as it arrives (`[DMS-NOTE] ...`), and an editor save
    with structural changes waiting to be ported (`[DMS-EDIT] ...`, once per save; builds refuse until it's ported). **While the mapper is
    working, Claude keeps it running with the Monitor tool** (re-arm it when it expires), acts on each note, and
    closes it with a reply. Notes from a play session can be batched until the mapper says "go".
  - **Game crashes come the same way** (`src/dms/gamelog.py`): `dms watch` reads `build/<map>/log-play.txt` each
    round and prints `[DMS-CRASH] <map>: ...` with the log's lines when UZDoom stops on an error (a script that
    doesn't compile, "VM execution aborted" while playing, a fatal error), each error once. **On a
    `[DMS-CRASH]` line Claude fixes the cause, rebuilds, and tells the mapper to start the game again**; the
    mapper doesn't have to paste the log. Only games started by `dms play` (or the board's restart) are
    covered: F9 from the editor writes no log dms reads.
  - **Order of work when requests come from several places** (editor saves, game notes, board notes, chat; agreed
    with the mapper 2026-11-21):
    1. **Editor saves first**, whenever they arrived: they're work the mapper already did, not requests, and
       everything else builds on them (builds refuse while a save waits anyway). Tweaks are pulled automatically;
       structural changes (`[DMS-EDIT]`) are ported into `map.py` before anything else is touched.
    2. **Then notes and chat messages in the order they arrived**, each merged on top of the last. One build per
       note by default (each shows on the board with its own `--note`, and gets its own reply); small related notes
       may share a build (say so in the build note and each reply). Notes from a play session can wait for "go".
       A chat message about the queue itself ("stop", "do X first", "skip that") overrides the order.
    3. **Conflicts:** a later request that refines an earlier one on the same element is the newer decision:
       apply it. Two requests that pull the same element different ways with no clear newer intent, or a request
       that would undo the mapper's own editor work: **ask, don't guess** (`dms status <map> "note #N needs a
       decision from you: see Claude's terminal"`), and leave the rest of the queue going. Notes name what
       they're about (kind, index, gid) and board notes the build they were made on: when the map has moved on,
       resolve a note by its element's gid, not its old coordinates.
  - **Is Claude listening?** `dms watch` rewrites `build/claude-watch.json` every second (`inbox.listening`: fresh
    within 10 s and covering the map). Without it, notes still land in the inbox, but the mapper is told: the board
    shows "Claude isn't watching notes" (and says so in its console when a note arrives), the game's "Got note #N"
    and status line say so, and the editor's "sent to Claude" becomes a warning. Two backstops on Claude's side:
    a `UserPromptSubmit` hook (`.claude/settings.json`, `dms agent-hook prompt`) shows Claude every open note no
    watch delivered with each message the mapper sends (silent when none are open), and `launchers\start-claude.bat` starts
    each session by asking Claude to arm the watch.
  - **Which Claude sessions are running** (`src/dms/agents.py`): the `SessionStart` and `UserPromptSubmit` hooks
    record the `claude.exe` process they run under (nearest ancestor) in `build/agents/<session id>.json`;
    `SessionEnd` removes it. A record counts while that process is alive with that name. Start Session uses it
    to hand the map to a running session (`build/session-request.json`, passed on once, as a `[DMS-SESSION]`
    line, by `dms watch` or the prompt hook) instead of starting a second Claude. **On a `[DMS-SESSION]`
    line, Claude arms the watch for that map, reads its notes and tells the mapper it's on it.**
  - Sources: the board (click a spot on a build's picture; each build records how its pictures map to the level,
    and the server works out the thing within 24 units or the sector there); the editor (**Send to Claude**,
    Ctrl+Shift+N, or Ctrl+right click for a "Message Claude about this..." menu, or Tools > Send to Claude; actions
    of the `DmsBridge` plugin declared in `src/udb-plugin/Actions.cfg`, rebindable in the editor: a note
    about the selected sectors/lines/things, or else the thing/line/sector under the mouse, with the main
    element's properties as the editor showed them; the plugin appends it to `inbox.jsonl` itself); and the game
    (key **N** while playing, rebindable under Customize Controls > doom-map-stack: the devtools mod in
    `resources/devtools/` (ZScript, loaded by `dms play`) takes a screenshot into `build/<map>/shots/`, logs where the
    player stands and what the crosshair is on, and opens a text box; `[DMS-NOTE-MARK]`/`[DMS-NOTE-TEXT]` lines in
    `log-play.txt` become notes via `inbox.ingest_game_log`, called by the board, `dms watch` and `dms notes`; sector
    and line numbers map straight to `TEXTMAP`, things by position).
  - The board's `POST /api/note` only accepts its own page's requests (JSON + an `X-DMS-Board` header, same origin):
    notes are instructions Claude acts on, so other web pages must not be able to add them.
- **The live link with the running game** (`src/dms/live.py`, the mod's `DmsLive`): `dms play` runs a live copy,
  `build/<map>/play-<n>.wad` (a new file for every start, named in `play-live.json`; older ones are deleted once
  no game has them open), whose lumps sit in fixed, space-padded slots so dms can rewrite them in place while the
  game runs (tried: UZDoom allows writing its open WADs and reads lumps from disk each time; it reads the
  directory only at startup, so the layout must never change, and a file must never be repacked under a game
  that still has it open: an old game once read the new copy's script where its map had been). Whether a game is
  running: the pid in `build/<map>/play.json`; `dms play` won't start a second game on a map (it brings the
  running one to the front).
  - **Every build** writes the new `TEXTMAP` into it. **Key H** in the game (`dms_reload`) reloads the map
    (`Level.ChangeLevel`) and puts the player back where they were, in about a second, with no restart.
    Monsters and pickups reset; inventory and health carry over. When the layout moved under the player
    (H puts them in a wall or outside the map), `map *` in the console restarts from the player start (a
    pistol start); the board's sidebar says so.
  - **Notes from the game are acknowledged in the game** as soon as dms picks them up ("Got note #N"), and a
    status line at the bottom shows "Claude: working on note #N" with moving dots. **While working on a note,
    update it with `dms status <map> "what you're doing"`** (e.g. "cutting the hallway"); closing the note
    moves it on to the next open note, or clears it.
  - **Closing a note** (`dms notes --close`) writes the reply into the `DMSLIVE` lump; the mod polls it every
    second and shows it in a box at the top of the screen for 12 s. Arriving in the map (H, a restart,
    `map *`) cuts whatever is still showing to 4 s, and the arrival messages themselves last 4 s. **So: build, then close the note with a reply
    saying what changed and "press H"**; the mapper sees it in the game and reloads.
  - If the map outgrows its slot (1 MB or 4x the map, whichever is bigger), `DMSLIVE` says "restart" and H instead
    logs `[DMS-RELOAD]`: the board's watcher closes the game (`launch.stop_game`) and starts it again with
    `+set dms_spawn` / `+set dms_message` (CVARINFO). That path needs the board running; it checks the script first, and keeps the
    running game if the script doesn't compile.
    `dms_spawn` and `dms_message` are plain local cvars (`nosave`): as `user` cvars they counted against
    UZDoom's userinfo size limit, and a long message stopped it at startup ("User info descriptor too
    big"). `launch.fit_message` still cuts the message to 400 characters (newest replies first, the rest
    "on the board"), so the box stays readable.
- `dms board [--port N] [--no-browser]` (**`launchers\Open Board.cmd`**): serves the board on 127.0.0.1 (port from `config\dms.toml`
  `[board]`, default 8765) and opens the browser (if the board is already running, it only opens the browser: the way back after
  closing the browser); the console window keeps it running and prints a timestamped
  line for each new build (with the note's first line), editor change (opened, unsaved, saved edits waiting,
  closed) and finished play session. **Auto-pull** (`config\dms.toml` `[board] auto_pull`, on by default): while the board
  runs, a save in the editor is pulled about a second after it settles (once per save). Tweak/comment-only saves
  rebuild straight away; a save with structural changes shows as "Editor save waiting for Claude" at the top of
  the board (pull's report and `diff-edit` pictures) until Claude ports it and runs `dms pull <map> --ported`. Per map, one build at a
  time (◀ ▶ or the arrow keys flip to older/newer, no animation, so steps can be compared; it follows the latest
  unless the mapper flipped back; "replay" or Space plays every build from the oldest, 4 a second): its picture
  (changes marked, or before/after), Claude's note, validation, the
  diff text; plus the editor's state and
  warning/error lines from the last play log. **The picture is a pan/zoom map** (the build's SVG, inline):
  the mouse wheel zooms about the cursor, dragging pans, F or "fit" shows the whole map; the view is kept
  while flipping builds and shared by the before/after pair. Labels, things and issue rings keep their size
  on screen, and a label is hidden while it would cover another (issues first, then sectors large to small,
  then things), so crowded spots spread out on zooming in; the line under the map says where the cursor is
  and what it's on. A click (not a drag) still opens the note box. It polls every 2 s, so new builds appear by themselves. The page is
  `src/dms/board.html`, read on every request: an open board reloads itself within 2 s when it changes. Changes to
  `src/dms/board.py` (the server, API, console log, auto-pull) need the board restarted. (`src/dms/board.py`,
  standard library only). Builds that changed the map, or carry a note, are kept in `build/<map>/history/<n>/`
  (`src/dms/history.py`, newest 100). **When building something for the mapper to look at, pass
  `dms build <map> --note "what changed; what to check"`**: the note is shown with that build on the board.

- **Per-map ZScript** (`src/dms/scripts.py`): an optional `maps/<map>/zscript.zs` (start it with `version "4.10"`;
  name classes after the map, never `Dms...`). Builds pack it as the map's `ZSCRIPT` lump and register every
  `EventHandler` class in it in the map's own MAPINFO block (`EventHandlers`), so it runs on that map only;
  `edit.wad` goes without. Every build with a script compile-checks it: UZDoom loads the WAD with the devtools mod
  in `-norun` mode, **hidden** (UZDoom shows script errors in a window and waits; the check stops it once the
  error is in its log), and errors become build errors with line numbers (`build/<map>/zscript.txt`; cached by
  content). A broken script isn't sent to the running game, and `dms play` refuses to start it. UZDoom compiles
  scripts only at startup, so a build that changes the script marks the running game for a restart (H restarts
  it, with the board running). Find things by thing id (UDMF `id` on things) and react to lines in
  `WorldLineActivated`; log with `Console.Printf("[DMS] ...")` so `log-play.txt` shows the script ran.
- **Per-map textures** (`src/dms/extras.py`): an optional `maps/<map>/textures.txt` is packed as the map's
  `TEXTURES` lump and `maps/<map>/animdefs.txt` as `ANIMDEFS` (UZDoom's text formats): new textures composed
  by the engine from the IWAD's own (turned, cut, layered, recoloured), so only text is committed, no
  graphics. Name them after the map (`CACOBASE`), 8 characters at most. They go into the game's WAD, the
  live copy and `edit.wad`; the validator learns the names from `textures.txt`; the hidden UZDoom load
  that checks the script re-runs when they change (a missing patch shows in `build/<map>/log-zscript-check.txt`).
  UZDoom reads them only at startup: a change marks the running game for a restart, like a script change.
  Where a wall needs two things one texture can't give (a strip along its foot, a turned texture), compose
  it here rather than cutting the map into more sectors.
  **Pictures of a map's own** (2026-11-24): `maps/<map>/textures/NAME.png` (8 characters at most) are packed between
  `TX_START` and `TX_END` and work on walls and as flats; the validator and the asset browser know them. Use one
  when composing can't do it (scaling, soft edges, the mapper's own artwork: sources go in `maps/<map>/art/`).
  These are graphics in the repo: one made from Freedoom's must have Freedoom's licence beside it
  (`maps/<map>/textures/NOTICE.txt`, see Licensing). Lessons for the text way: one change per `Patch` (the
  engine kept only the Blend of a Translation + Blend); a patch can't be scaled or feathered; a scratch load
  only proves the engine accepts a definition, not how it looks.
- **Asset browser** (`/assets` on the board's server, each page links to the other in a thin banner at the top, the place for further tools' pages too; dms opens only the board, the mapper clicks over; `src/dms/resources.py`,
  `src/dms/assets.html`; plan and status: `docs/asset-browser.md`): every texture, flat, decal, item, monster,
  decoration, sound and song the IWAD and `uzdoom.pk3` provide, as a list or grid with search, filter
  chips and sort; textures auditioned side by side on a 2D plane and on 3D boxes (offsets and scale as UDMF);
  sounds with the engine's controls; songs played by our own browser synth (`src/dms/assets-synth.js`) through UZDoom's soundfont.
  Favourites (starred by the mapper) are kept in `build/asset-favorites.json`: look there when asked to use
  "one of my favourites". Rule: the browser offers only settings the game itself can apply (no tempo or pitch for music: UZDoom plays songs as they are).
  The editor's thing and texture-set configs are read at run time from `.tools/udb/`. Everything converted is
  cached in `build/assets/<key>/` (the key changes with the resource files or `resources.VERSION`); the first
  load indexes for about 20 s, with a loading screen (a turning sigil drawn in the page, and a bar fed by
  `/api/assets/progress`: `resources.progress()`, the stage and its count, never waiting for the index). Changes to `resources.py` need the board restarted; `assets.html` is read per request.
  **The maps' own assets and what the maps use** (`src/dms/mapassets.py`; read from the maps' files when asked, not part
  of the cached index): each map's `textures.txt` textures and flats (put together here the way the engine does:
  patches placed, flipped, turned, blended, recoloured; a definition using something it doesn't know is shown with
  a `~`: the game is the judge) and the actors in its `zscript.zs` (with their Spawn picture) are listed in their
  tabs with a violet tag naming the map, and a `custom` chip. Use counts come from every map's `TEXTMAP`,
  `map.toml` (sky, music) and `zscript.zs` (sounds, decals, spawned classes): a green `xN` on each asset,
  an `in use` chip, and **in use first** (on by default): what the maps use comes first, most used first, under a
  divider, counted over every map or one (the `use:` menu; `/assets?map=<name>`, which the board's banner link passes for the map it shows). **For consistency, look there (or call `mapassets.usage`) before picking a new texture or sound.**
- **Themes** (`src/dms/themes.py`; plan and status: `docs/themes.md`): a theme is a set of textures, things and
  atmosphere that belong together, the look of one kind of place, shared by every map: `themes/<name>/theme.toml`,
  textures by **role** (`wall`, `wall_alt`, `wall_base`, `trim`, `door`, `door_frame`, `step`, `floor`, `floor_alt`,
  `ceiling`, `light`, `switch`, `liquid`, `sky`; the first name of a role is the main one), things (`light_source`,
  `decoration`), `decals`, and `[atmosphere]` (light, light_range, lightcolor, fog, fogdensity).
  `dms themes` lists them, `dms themes show <name>` prints one, `dms themes check` checks roles, names (the
  catalog and the maps' own textures) and values. `dms themes harvest <map> <name> --gid PATTERN...` drafts one
  from the sectors whose gids match (fnmatch; repeat `--gid`): roles guessed from where each texture sits, what
  it counted in the file's header; trim the draft by hand. **Before building a new area, pick its theme and
  take textures from it** (`techbase` and `grotto` come from Cacobelisk). **The theme viewer**: `/themes` on the
  board's server (a link in each page's banner; `src/dms/themes.html`, read per request; `/api/themes`), a
  standard room in 3D (our own WebGL2) with the chosen theme slotted into it, every role labelled with a
  leader line to its surfaces; it polls, so an edited `theme.toml` shows in a few seconds. Planned: choosing
  in the asset browser, `b.theme()` in `map.py` and a validator warning for off-theme textures.
- `dms catalog`: lists the IWAD's wall textures (with sizes) and flats into `catalog/` (committed; names only).
  Re-run after changing the Freedoom pin.
- `dms validate <map> [--edit]`: checks `TEXTMAP` (or the mapper's `edit.wad`) and writes `build/<map>/validate.txt`
  (`validate-edit.txt`). `dms build` runs the same checks and exits non-zero on errors, but still packs the WAD so the
  map can be opened to look at the problem. Checks: references, zero-length and crossing lines, missing front sides,
  one-sided walls without a middle texture, unclosed/orphan sectors, light 0-255, ceiling below floor, textures and
  flats against the catalog (a wall texture is accepted as a flat, and a flat as a wall texture: UZDoom draws both), player 1 start, things outside every sector or on no skill level, tagged specials.
- **Movement check** (`src/dms/movement.py`): every build (and `dms render`) works out which sectors the player can
  reach from the player 1 start and writes `build/<map>/movement.txt`. Rules: step up at most 24, any drop (one-way
  drops listed), 56 headroom, gaps at least 32 wide (collinear lines end to end count as one gap); blocking lines are
  walls. Doors (11-13; tag 0 = the sector behind) open to the lowest neighbouring ceiling - 4, locked doors (13,
  lock in arg3) need a reachable key, lifts/floor/ceiling movers span their neighbours' heights
  (Floor_LowerByValue/RaiseByValue, 20/23, also their own arg2, e.g. a platform down a shaft); a special counts
  once its line is reachable (front side for use/shoot, either side for walk-over; a switch at the back of a
  niche too small to enter counts from the sector in front of the niche, also through one more thin
  sector, e.g. a shutter in front of the switch). Scenery (no height at all, or
  under 56 high and raised more than a step above every neighbour, like a monolith's top; untagged, not
  behind a special's line; or marked `user_scenery = true` by the map, e.g. a recess too narrow to
  enter) is walls, never reported unreachable. Its problems are warnings:
  unreachable sectors, keys, weapons and notable items, exits, secrets; locked doors that never open; soft-locks
  (reachable, but no way on to an exit; only checked when the map has a reachable exit). Optimistic on purpose:
  "unreachable" is reliable, "reachable" means "probably". Not yet: teleporters, crushers, scripts.
  Door and lift use lines must have the player's side as their **front** side.
  **Monster fit** (same file, `_monster_fit`): every monster in the player's reach is flooded with its own
  size (`MONSTERS`: a gap of twice its radius, headroom its height), a step of 24 and, unless it flies, no
  drop over 24; movers that stay put once used (floors, ceilings, Door_Open) count, doors and lifts that
  close or return only with a monster activation flag (`monsteruse`...). Where the player goes back and
  forth between a place a monster reaches and one it can't (not a dead end too small for it), a warning
  names the line, the monsters and why. It can't see bends: give winding corridors about twice the
  monster's width (Doom's monsters move in 8 directions; Cacobelisk's passage, notes #66-#70).

- **Renders** (`src/dms/render.py`): every build writes `build/<map>/render.png` + `render.txt` (sectors shaded by
  floor height, walls, specials, things by kind (`render.thing_kind`, from the editor's thing lists: monsters
  red circles with a line for their facing, pickups blue diamonds, lights and decoration small grey circles,
  the player start green), grid, validation and movement issues ringed in red, unreachable sectors
  hatched red, soft-lock sectors tinted orange; labels kept clear of each other, a moved one joined to what
  it labels by a thin leader line: `render.place_labels`) and, when the map changed,
  `diff.png` + `diff.txt` against the previous build: the current map with the changes marked (green added,
  yellow changed, red see-through ghosts of what was removed), plus `diff-before.png` / `diff-after.png` (previous
  and current map, same view, each with its side of the changes) for the board's before/after view.
  `dms render <map> [--edit]` redraws; `--edit` draws the mapper's `edit.wad` (`render-edit.png`) and diffs it
  against `TEXTMAP` (`diff-edit.png`): that's how Claude sees the mapper's editor changes. **Look at the PNG
  (and read the .txt) after every build.**
  Beside every PNG the renderer writes the same picture as an **SVG** (`src/dms/svg.py`: `render.svg`,
  `diff.svg`, `diff-before.svg`, `diff-after.svg`, and the `-edit` ones), in map units with y turned over
  (north up), for the board's pan/zoom map; lines keep their width at any zoom, and sectors, things and
  special lines carry a `<title>` saying what they are. The PNGs stay Claude's view (and the fallback
  for builds from before the SVGs).

Code: `src/dms/udmf.py` (TEXTMAP read/write, keeps every field), `wad.py`, `catalog.py`, `validate.py`, `gen.py` (the `MapBuilder` that
`map.py` files use; every element gets a `user_gid`), `maps.py`, `build.py`, `launch.py`, `history.py`, `board.py`,
`pull.py`, `overrides.py`, `movement.py`, `inbox.py`.

- `dms session [<map>] [--no-browser|--no-editor|--no-game|--no-agent]` (**`Start Session.cmd`**, the
  mapper's usual way in; `src/dms/session.py`): `git pull`, then the session window (`picker.pick_session`): the map
  list (focused, last map selected), **New map...**, and toggles for the browser, editor, game and agent
  (defaults: `[session]` in `config\dms.toml`, not remembered). Choosing a map (Start, Enter, double-click) or creating one
  starts it: builds if needed, then opens what was ticked and isn't open: the browser on the map's page (`/#<map>`),
  the editor (`launch.edit`) and the game (`launch.play`), or brings them to the front. A dropped map skips the
  window and uses the defaults. **The board isn't a choice: a session always has one** (auto-pull and the game's
  restart need it). A board already running is used as it is; a port taken by something else stops the session
  before anything opens. Otherwise, from `Start Session.cmd` (`--board-here`), **the .cmd's own window becomes the
  board** once everything else is open (and opens the browser itself, once it's listening); from a terminal
  without `--board-here`, the board gets a console window of its own.
  It writes `build/session.txt` (`map=`; `launcher=`/`title=` when an agent is to start; `board=1`, `browser=1`
  when the .cmd is to run the board); the `.cmd` then runs the agent's launcher in its own window
  (`<launcher> --session <map>`), then the board. No agent is started if a Claude session
  is already running in the repo (`agents.running`; it's handed the map instead, and the window says so) or a
  `dms watch` covering the map already runs. Agents are listed under `[agents.<key>]` in `config\dms.toml` (`name`, `launcher`: a
  `.bat`/`.cmd` in `launchers\`, no spaces); only Claude Code is defined (scaffolding for others). The agent is
  started by the `.cmd`, not by Python, so it gets the mapper's environment rather than `dms.ps1`'s.
  Exit code 2 = the window was cancelled. `[play] windowed = true` (default) runs UZDoom with `+vid_fullscreen 0`
  on every launch; windowed, UZDoom remembers its position, so it reopens on the same monitor.
- **`launchers\start-claude.bat`**: Claude on its own: `git pull`, `claude update`, then starts Claude Code with a first
  message asking it to arm the note watch and say where things were left off. With `--session <map>` (from
  `Start Session.cmd`) it skips the pull and names the map in that message.

*Parked* (see `docs/PLAN.md` §8): the screenshot tour (`tour`), `dms shot`, the test map overlay.

**Running uv directly** (e.g. `uv add`, `uv lock`): never call a bare `uv`. Run it inside the repo environment:

```powershell
. .\scripts\dms-env.ps1; Invoke-DmsScope -Root $PWD -Body { & .tools\uv\uv.exe lock --project src }
```

The same goes for ad-hoc Python (one-off scripts, quick checks): run it with the repo's Python inside that scope
(`& .tools\uv\uv.exe run --project src python ...`), never a system `python`, which writes caches into the user profile.

`scripts\dms-env.ps1` points `TEMP`/`TMP` at `.tools\tmp\`, sets every uv location to an absolute path under `.tools\`, points `UV_CONFIG_FILE`
at `src\uv.toml`, turns off registry entries and Python shortcuts, and restores the caller's environment afterwards.
`src\uv.toml` sets `python-downloads = "manual"`, so uv never fetches a Python on its own; `bootstrap.ps1` installs it
explicitly with `--no-registry --no-bin`.
**Upgrading uv:** change `required-version` in `src\uv.toml` and the matching zip hash in `bootstrap.ps1` together.
Move each one up into the list above as it lands.

## Working rules

- **The mapper works from Explorer, not a terminal.** Every command the mapper runs gets a double-clickable
  `.cmd` launcher, a thin wrapper around `dms.ps1` that pauses on error: `Start Session.cmd` in the repo root (the
  only script there), the rest in `launchers\` (e.g. `launchers\Open Editor.cmd`).
  Where a command takes a file, accept it by drag-and-drop onto the launcher (`%*`). **Interactive menus are the
  default experience:** a launcher that takes a map opens a picker window on double-click (`src/dms/picker.py`,
  tkinter; the last map chosen is preselected); dropping a map folder onto the launcher skips the picker. `.cmd` files are ASCII with CRLF line endings.
  Terminal commands are for Claude and for anyone who prefers them.

- **Knowledge lives in the repo:** `AGENTS.md`, `docs/` and `maps/*/notes.md`, not in Claude's private memory.
- **Rules live in scripts:** overwrite protection and similar checks go in `dms`, not in Claude Code hooks.
- **Text alongside images:** every image output (render, tour) also has a text report.
- **Updating a tool** is a deliberate change to `config\tools.toml` (version + hash) that shows up in git.

## Versions and releases

The tool is versioned `major.minor.fix`, plus `+docN` (agreed with the mapper 2026-11-25):
- **minor**: new functionality, or a change in how something works (below 1.0, breaking changes are minor too);
- **fix**: only corrections;
- **`+docN`**: only documents changed (no code, no behaviour, no fix); numbered from 1 after each release
  (`0.21.0+doc1`, `+doc2`), reset by the next one. Map-only commits count as `+doc` while maps share this repo.
- **major** stays 0 until the tool is meant for people outside this repo.

A release: the version in `src/pyproject.toml` and `src/dms/__init__.py` (then `uv lock`, so `--locked` runs
still work), an entry in `docs/CHANGELOG.md`, a commit, and an annotated tag `vX.Y.Z` pushed with `main`.
`dms --version` prints it.

## Several maps at once

- **Named by name:** maps are identified by a name (`light-test2`), never by slot.
  Built on its own, a map always goes into the MAP01 slot of its own WAD.
- **Self-contained:** everything a map owns (sources, notes, per-map resources, build output, feedback,
  UZDoom saves in `build\<map>\saves\`) is kept under its name, in its project.
- **Map name always explicit:** every map command requires the name and prints which map it's acting on.
  No hidden "current map" setting.
- **Shared code stays safe:** `src/` and `resources/devtools/` are shared. TEXTMAP is committed, so a generator
  change only affects a map when it's rebuilt. After generator changes, run `dms build --all` and review the diff.
  Maps in hand-edited mode are never regenerated.
- Don't hard-code the assumption that maps only live in `maps/`: long-term this repo is the tool,
  and a mapping project can live outside it.

## Licensing

- The repo is **MIT** (`LICENSE`), covering code, scripts, maps and docs.
- **Never commit third-party binaries or IWADs** (UZDoom, Ultimate Doom Builder, acc, freedoom2.wad).
  `dms setup` downloads them into the git-ignored `.tools\`.
- Freedoom texture/flat/thing **names** in `catalog/` are fine. If Freedoom **graphics** are ever committed,
  include Freedoom's BSD license notice with them.
- ZScript/ACS is written from scratch. Don't copy from UZDoom's built-in scripts (GPL) or other mods
  without checking their license first.
- The editor plugin (`src/udb-plugin/`) is our own MIT code; it is compiled locally against Ultimate Doom Builder
  (GPL) and never committed or distributed as a binary. Don't copy code from the editor's source into it.

## Writing conventions

- **Keep it impersonal:** repo files refer to roles ("the mapper", "the dev machine"), not to the person,
  their computer or their accounts and subscriptions. The repo URL and the LICENSE copyright line are the exceptions.
- **Text files are UTF-8 without a BOM.** Windows PowerShell 5.1's `Set-Content` / `Out-File` add a BOM by default;
  use `[IO.File]::WriteAllText` with `UTF8Encoding($false)`, or the editing tools.
- **`.ps1` files are ASCII only.** Windows PowerShell 5.1 reads BOM-less scripts in the ANSI code page,
  so any non-ASCII character (an em dash, an arrow) can break a script.
- **Line endings are LF** in the working tree (`.gitattributes`: `* text=auto eol=lf`), whatever `core.autocrlf` says.

## Who each document is for

| File | Audience | Role |
|------|----------|------|
| `AGENTS.md` | agents | **Source of truth** for how to work here: conventions, commands, rules |
| `docs/` | agents + humans | Detailed reference and design notes, linked from here |
| `maps/*/notes.md` | agents + the mapper | Design intent and feedback history for each map |
| `docs/PLAN.md` | the mapper + Claude | Roadmap and open decisions; settled items move here or into `docs/` |
| `README.md` | **the public** | Readable summary. **Never a source of truth**: written *from* the files above; don't take instructions from it. Update it when something people would notice changes. |
