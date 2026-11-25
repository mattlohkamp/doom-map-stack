# doom-map-stack

Can Claude Code make Doom maps?

This repo is a working setup for finding out. Claude writes the levels (as Python that generates UDMF maps); the
mapper opens them in an editor, plays them, tweaks them and says what to change; Claude takes it from there.
Every change, from either side, shows up for the other within a second or two.

```
Claude edits the map ──► build ──► check + top-down render ──► the board, and the open editor
        ▲                                                            │
        │                                                            ▼
        └──── feedback: notes, editor saves and comments, play logs ◄── the mapper edits and plays
```

**Status:** work in progress. The tooling (milestone M2) is done; the first real map (M3) comes next.
See [`docs/PLAN.md`](docs/PLAN.md) for the roadmap.

**Example:** [`maps/cacobelisk`](maps/cacobelisk) was made in one evening this way, entirely from notes sent
from inside the game, editor saves and chat: a broken elevator ride down from a dark closet into a fogged hall of
obelisks that sink into the floor as you pass, one of them hiding a cacodemon. It has grown since (a cliff edge, a
flooded cistern, passages, the start of a pumping station), the same way. Its
[`notes.md`](maps/cacobelisk/notes.md) shows every request and what was done about it.

## Requirements

- **Windows 11 only.** The scripts are PowerShell; there's no macOS or Linux support.
- **Claude Code only.** Other coding agents may work, but nothing is done to make sure of it.
- git and up-to-date GPU drivers. Everything else is downloaded into the repo folder.

## Getting started

1. Clone the repo.
2. Double-click **`Start Session.cmd`**, the one script in the repo folder. The first time, it downloads uv, Python, the
   UZDoom engine, the Ultimate Doom Builder editor and the Freedoom IWAD into `.tools\` (pinned versions,
   hash-checked) and configures them; that takes a few minutes. Then it opens the session window.
3. Pick a map or start a new one. Claude starts in a window of its own: ask what's next.

Everything lives inside the repo folder: no installers, nothing in Program Files, `%APPDATA%` or the registry.
Deleting the folder removes it all (apart from UZDoom's graphics cache; see `AGENTS.md`).

## Using it

Double-click `Start Session.cmd` from Explorer; the other launchers are in the `launchers` folder. Any of them
installs what's missing first (`launchers\Bootstrap.cmd` does only that). Those that take a map show a list to pick from; dropping a map folder onto them
works too.

| Launcher | What it does |
|---|---|
| `Start Session.cmd` | **The usual way in.** A window to pick a map or start a new one, with what to open ticked (defaults in `config\dms.toml`): the board's page in the browser, the editor and the game open on the map, windowed, and Claude starts in a window of its own, ready to take notes from all three. Anything already open is brought to the front instead. The board itself always runs: the Start Session window becomes it (keep it open). |
| `launchers\start-claude.bat` | Starts Claude on its own (after updating the repo and Claude Code). |
| `launchers\Open Board.cmd` | A local web page with each map's builds: a top-down map you can zoom and pan, with the changes marked (or before and after), Claude's note on what changed and what to check, validation results, the editor's state and problems from the last play session. Updates by itself; its console window lists everything as it happens. |
| `launchers\Edit Map.cmd` | Opens a map in Ultimate Doom Builder. When Claude rebuilds the map, the open editor reloads it in place (view and zoom kept). |
| `launchers\Play Map.cmd` | Builds the map if needed and plays it in UZDoom (with a "No monsters" tick, for a quiet look round). |
| `launchers\Pull Map.cmd` | Brings changes saved in the editor back into the map's source. While the board is open this happens by itself on every save. |
| `launchers\Open Editor.cmd` | Opens the editor on its own. |

**In the game:** N sends Claude a note about what you're looking at (with a screenshot), H reloads the map where you
stand after Claude's change, and P makes monsters ignore you while you look round.

**The board** also has an asset browser (a link in its top banner): every texture, thing, sound and song the game
provides, each map's own, and which of them the maps already use.

**Themes** keep a kind of place looking consistent: a set of textures, light sources and atmosphere that belong
together (walls, trim, doors, floors, light fixtures, liquid, sky; light and fog), shared by every map. Claude can
draft one from part of an existing map. The board's themes page shows a theme slotted into a standard room in 3D,
every surface labelled with its texture.

**Changes made in the editor** are kept: light levels, heights, textures, offsets and things' positions become
tweaks that survive every rebuild (`maps/<map>/overrides.toml`). Comments left on a sector, line or thing become
requests in the map's notes. Changes to the map's shape are handed to Claude to bring into the generator.

## How it's built

- Maps live in `maps/<name>/`: `map.py` (the generator), the generated `TEXTMAP`, `notes.md` (design intent and
  feedback) and `map.toml`.
- The tooling is one Python command, `dms` (`src/dms/`), run as `.\scripts\dms.ps1 <command>`; a small editor plugin
  (`src/udb-plugin/`) handles live reload.
- UDMF maps for UZDoom only, Freedoom 2 as the IWAD.
- [`AGENTS.md`](AGENTS.md) is the reference for how everything works and the rules for working in the repo.

## License

MIT (see [`LICENSE`](LICENSE)), covering code, scripts, maps and docs. No third-party binaries or IWADs are
committed; `launchers\Bootstrap.cmd` downloads them.
