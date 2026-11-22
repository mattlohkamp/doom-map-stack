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
See [`PLAN.md`](PLAN.md) for the roadmap.

**Example:** [`maps/cacobelisk`](maps/cacobelisk) was made in one evening this way, entirely from notes sent
from inside the game, editor saves and chat: a broken elevator ride down from a dark closet into a fogged hall of
obelisks that sink into the floor as you pass, one of them hiding a cacodemon. Its
[`notes.md`](maps/cacobelisk/notes.md) shows every request and what was done about it.

## Requirements

- **Windows 11 only.** The scripts are PowerShell; there's no macOS or Linux support.
- **Claude Code only.** Other coding agents may work, but nothing is done to make sure of it.
- git and up-to-date GPU drivers. Everything else is downloaded into the repo folder.

## Getting started

1. Clone the repo.
2. Double-click **`Bootstrap.cmd`**. It downloads uv, Python, the UZDoom engine, the Ultimate Doom Builder editor and
   the Freedoom IWAD into `.tools\` (pinned versions, hash-checked) and configures them.
3. Start Claude Code in the repo folder and ask what's next.

Everything lives inside the repo folder: no installers, nothing in Program Files, `%APPDATA%` or the registry.
Deleting the folder removes it all (apart from UZDoom's graphics cache; see `AGENTS.md`).

## Using it

Double-click these from Explorer. Those that take a map show a list to pick from; dropping a map folder onto them
works too.

| Launcher | What it does |
|---|---|
| `Start Session.cmd` | **The usual way in.** A window to pick a map or start a new one, with what to open ticked (defaults in `dms.toml`): the board (in the browser), the editor and the game open on the map, windowed, and Claude starts in a window of its own, ready to take notes from all three. Anything already open is brought to the front instead. |
| `start-claude.bat` | Starts Claude on its own (after updating the repo and Claude Code). |
| `Open Board.cmd` | A local web page with each map's builds: the top-down render with the changes marked (or before and after), Claude's note on what changed and what to check, validation results, the editor's state and problems from the last play session. Updates by itself; its console window lists everything as it happens. |
| `Edit Map.cmd` | Opens a map in Ultimate Doom Builder. When Claude rebuilds the map, the open editor reloads it in place (view and zoom kept). |
| `Play Map.cmd` | Builds the map if needed and plays it in UZDoom. |
| `Pull Map.cmd` | Brings changes saved in the editor back into the map's source. While the board is open this happens by itself on every save. |
| `Open Editor.cmd` | Opens the editor on its own. |

**Changes made in the editor** are kept: light levels, heights, textures, offsets and things' positions become
tweaks that survive every rebuild (`maps/<map>/overrides.toml`). Comments left on a sector, line or thing become
requests in the map's notes. Changes to the map's shape are handed to Claude to bring into the generator.

## How it's built

- Maps live in `maps/<name>/`: `map.py` (the generator), the generated `TEXTMAP`, `notes.md` (design intent and
  feedback) and `map.toml`.
- The tooling is one Python command, `dms` (`src/dms/`), run as `.\dms.ps1 <command>`; a small editor plugin
  (`src/udb-plugin/`) handles live reload.
- UDMF maps for UZDoom only, Freedoom 2 as the IWAD.
- [`AGENTS.md`](AGENTS.md) is the reference for how everything works and the rules for working in the repo.

## License

MIT (see [`LICENSE`](LICENSE)), covering code, scripts, maps and docs. No third-party binaries or IWADs are
committed; `Bootstrap.cmd` downloads them.
