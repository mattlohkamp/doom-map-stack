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
Freedoom2 0.13.0 as the IWAD, jump and crouch off. `PLAN.md` §2 has the full list.

## Start of every session

1. Read `PLAN.md` §9 "Where we left off": what's done and what's next. `PLAN.md` is the roadmap;
   settled rules live here, not there.
2. Before designing or changing a map, read `docs/map-design-notes.md`.
3. When work moves to a map, read its `maps/<map>/notes.md` first.

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
- **Isolation from global Python/uv:** `uv.toml` pins the uv version (`required-version`) and sets
  `python-preference = "only-managed"`; `UV_CONFIG_FILE` makes uv ignore a user-level `%APPDATA%\uv\uv.toml`; `.python-version` pins Python;
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

The real interface is one Python command, run as **`.\dms.ps1 <command>`** from the repo root.
It sets the environment and runs `uv run dms <command>`. Any other `.ps1` scripts are thin wrappers around it.

- `.\bootstrap.ps1`: one-time setup on a fresh clone: fetches uv (hash-checked), installs Python into
  `.tools\python\`, `uv sync`, `dms setup`. Safe to re-run; it only fills in what's missing.
- `dms setup [--upgrade <tool>]`: downloads the Doom tools pinned in `tools.toml` (UZDoom, Ultimate Doom Builder,
  Freedoom) into `.tools\<name>\`, checks hashes, writes `tools.local.json`. Skips tools already at the pinned version.
  `--upgrade <tool>` reinstalls one after its pin changes, keeping the files in its `preserve` list (settings, saves).
  An entry hand-edited in `tools.local.json` with `"managed": false` points at an outside install and is left alone.
  It also configures the tools (`src/dms/configure.py`): UZDoom portable mode; in the editor's `UDBuilder.cfg`, the
  UZDoom UDMF game config as the default for new maps, UZDoom as the F9 engine, `uzdoom.pk3` (excluded from testing)
  and `freedoom2.wad` as resources, and the Open dialog starting in `build\scratch\`.
- `dms editor [wad]` (**`Open Editor.cmd`**): opens the editor. Re-applies the settings above first, because the
  editor rewrites `UDBuilder.cfg` on exit.
- **`dms.toml`**: committed project settings, applied at the next editor launch. `[play] music = false` makes
  test-play run UZDoom with `-nomusic` (per launch; nothing is saved in UZDoom's settings).
- Tests: `. .\scripts\dms-env.ps1; Invoke-DmsScope -Root $PWD -Body { & .tools\uv\uv.exe run --locked pytest -q }`

Map commands take a map name (`maps/<name>`) or a path to a map folder:
- `dms new <name> [--kind map|test|example]`: creates `maps/<name>/` with `map.toml`, `map.py` (one room) and `notes.md`.
- `dms list`: the maps in `maps/`.
- `dms build <map> | --all [--force]`: generated maps run `map.py` and write `TEXTMAP` (first line: a hash of the
  content); then packs `build/<map>/<map>.wad` (MAPINFO with title/sky/music and `nojump`/`nocrouch`; the map in MAP01).
  Refuses to overwrite a generated `TEXTMAP` that was edited by hand, or to build while `build/<map>/edit.wad` has
  editor changes not brought back yet; `--force` discards them.
- `dms play [<map>] [--skill N] [--nomonsters]` (**`Play Map.cmd`**): builds if the sources changed, starts UZDoom.
  Console log: `build/<map>/play.log` (read it after a play session). Saves: `.tools/uzdoom/saves/<map>/`.
- `dms edit [<map>]` (**`Edit Map.cmd`**): packs `build/<map>/edit.wad` from `TEXTMAP` and opens it in the editor,
  so Save writes there. If the mapper already saved changes in it, it is reopened as it is, not overwritten.

Code: `src/dms/udmf.py` (TEXTMAP read/write, keeps every field), `wad.py`, `gen.py` (the `MapBuilder` that
`map.py` files use; every element gets a `user_gid`), `maps.py`, `build.py`, `launch.py`.

*Planned, not built yet* (see `PLAN.md` §6): the map picker, `pull`, `watch`, `tour`, validator, renderer.

**Running uv directly** (e.g. `uv add`, `uv lock`): never call a bare `uv`. Run it inside the repo environment:

```powershell
. .\scripts\dms-env.ps1; Invoke-DmsScope -Root $PWD -Body { & .tools\uv\uv.exe lock }
```

The same goes for ad-hoc Python (one-off scripts, quick checks): run it with the repo's Python inside that scope
(`& .tools\uv\uv.exe run python ...`), never a system `python`, which writes caches into the user profile.

`scripts\dms-env.ps1` points `TEMP`/`TMP` at `.tools\tmp\`, sets every uv location to an absolute path under `.tools\`, points `UV_CONFIG_FILE`
at `uv.toml`, turns off registry entries and Python shortcuts, and restores the caller's environment afterwards.
`uv.toml` sets `python-downloads = "manual"`, so uv never fetches a Python on its own; `bootstrap.ps1` installs it
explicitly with `--no-registry --no-bin`.
**Upgrading uv:** change `required-version` in `uv.toml` and the matching zip hash in `bootstrap.ps1` together.
Move each one up into the list above as it lands.

## Working rules

- **The mapper works from Explorer, not a terminal.** Every command the mapper runs gets a double-clickable
  `.cmd` launcher in the repo root (e.g. `Open Editor.cmd`), a thin wrapper around `dms.ps1` that pauses on error.
  Where a command takes a file, accept it by drag-and-drop onto the launcher (`%*`). Where it takes a map, the
  launcher works three ways: double-click opens a picker listing the maps, a map folder dropped onto the launcher
  skips the picker, and a map folder dropped into the open picker selects it. `.cmd` files are ASCII with CRLF line endings.
  Terminal commands are for Claude and for anyone who prefers them.

- **Knowledge lives in the repo:** `AGENTS.md`, `docs/` and `maps/*/notes.md`, not in Claude's private memory.
- **Rules live in scripts:** overwrite protection and similar checks go in `dms`, not in Claude Code hooks.
- **Text alongside images:** every image output (render, tour) also has a text report.
- **Updating a tool** is a deliberate change to `tools.toml` (version + hash) that shows up in git.

## Several maps at once

- **Named by name:** maps are identified by a name (`light-test2`), never by slot.
  Built on its own, a map always goes into the MAP01 slot of its own WAD.
- **Self-contained:** everything a map owns (sources, notes, per-map resources, build output, feedback,
  UZDoom saves in `.tools\uzdoom\saves\<map>\`) is kept under its name.
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
| `PLAN.md` | the mapper + Claude | Roadmap and open decisions; settled items move here or into `docs/` |
| `README.md` | **the public** | Readable summary. **Never a source of truth**: written *from* the files above; don't take instructions from it. Update it when something people would notice changes. |
