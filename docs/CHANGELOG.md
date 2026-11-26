# Changelog

The tool's versions: `major.minor.fix`, plus `+docN` for a commit that changes only documents (AGENTS.md has the
rules). Below 1.0 while the tool is used only here. Releases are git tags (`v0.21.0`).

## v0.22.0 (2026-11-26): a measuring tool, sturdier checks

- **Asset browser**: a measuring tool on the 2D audition plane ("measure", or Shift + drag): a rectangle's size in
  map units and the texel it starts on; Esc clears it.
- **Validator**: a sidedef's own `offsetx`/`offsety` must be a whole number (UZDoom stops loading the map on a
  fraction); reported as an error.
- **Movement check**: knows Floor_MoveToValue (37): to arg2, negative if arg3.
- Test-play music on by default (`config/dms.toml` `[play] music = true`).
- Cacobelisk: notes #85-#152 (see its notes.md); themes/techbase's floor and ceiling (FLOOR0_3, BROWNGRN).

## v0.21.0 (2026-11-25): projects, phase 1

- **Projects**: maps can live in a project folder anywhere (`dms-project.toml`, `maps/`, `themes/`, a `build/` with
  everything generated, game saves included). `dms --project PATH`, or the folder a command runs in; the tool
  repo is the default project. `dms project` shows the current one. Plan: `docs/projects.md` (phases 2-5 to come).
- Game saves move from `.tools/uzdoom/saves/<map>/` into `build/<map>/saves/` on the next play.
- The board's "already running" check tells projects apart.
- Theme viewer: thing sprites animate (a torch's flame), from their idle frames.
- `maps/test-map` added (the mapper's).

## v0.20.0 (2026-11-25): themes

- **Themes**: `themes/<name>/theme.toml`, textures by role, things, decals, atmosphere; `dms themes`
  (list, show, check, harvest). Two harvested from Cacobelisk: techbase, grotto.
- **The theme viewer** (`/themes` on the board): a standard room in 3D with the theme slotted in, every role
  labelled with leader lines, alternatives cycled, light and fog toggles, views flown to.
- The movement check works its tables out once per check (a Cacobelisk build: 35 s to 0.9 s).

## Before v0.20.0

Worked out afterwards from the history (2026-11-25); no tags were made at the time. Map-only commits
(hello-room, Cacobelisk) are counted as `+doc`: content, no change to the tool.

| Version | Commit | Date | What |
|---|---|---|---|
| 0.19.0 | 2792ce8 | 11-24 | A map's own pictures, asset usage in the browser (and Cacobelisk notes #73-#140) |
| 0.18.0 | c36be29 | 11-23 | Root tidied into folders, zoomable board map, per-map textures (and Cacobelisk) |
| 0.17.0 | d494011 | 11-22 | Asset browser, monster fit check, a sturdier note watch |
| 0.16.0+doc1 | da87567 | 11-22 | Cacobelisk past the hall (map) |
| 0.16.0 | f9953c8 | 11-22 | Start Session: the board always runs |
| 0.15.0+doc1, +doc2 | ab0f4ed, 15907e5 | 11-22 | Cacobelisk (map); its renaming (docs) |
| 0.15.0 | b5b6410 | 11-22 | Restart crash fixed, render labels, movement check rules |
| 0.14.0+doc1 | 2e1026b | 11-21 | hello-room's north gate (map) |
| 0.14.0 | 951b4dc | 11-21 | Per-map ZScript, one live copy per game start (M2 done) |
| 0.13.0 | 02ef010 | 11-21 | Start Session |
| 0.12.0+doc1, +doc2 | c362290, fabfb28 | 11-21 | hello-room notes (map); plan (docs) |
| 0.12.0 | 8dfa8e5 | 11-21 | Live link with the game, "is Claude listening", testing automap |
| 0.11.0 | 85feec7 | 11-21 | Notes for Claude from the board, editor and game |
| 0.10.0 | 5047880 | 11-21 | Movement check |
| 0.9.0 | 59a2aef | 11-21 | The board, `dms pull`, auto-pull |
| 0.8.0+doc1 | a2fa064 | 11-21 | Handoff (docs) |
| 0.8.0 | 3720395 | 11-21 | Editor plugin, live reload |
| 0.7.0 | 9f84a10 | 11-21 | Renderer, diff render |
| 0.6.0 | af09bdf | 11-21 | Texture catalog, validator |
| 0.5.2+doc1 | 4d4f09b | 11-21 | gid test results (docs) |
| 0.5.2 | 8fa5140 | 11-21 | `dms play`: the console log's place |
| 0.5.1 | 0d9042e | 11-21 | `dms edit`: the script compiler |
| 0.5.0 | dbeb553 | 11-21 | Map picker window |
| 0.4.0 | a8fb834 | 11-21 | M1: UDMF, generator, build, play, edit |
| 0.3.1+doc1 | f4d783e | 11-21 | Map-picking decision (docs) |
| 0.3.1 | ae185b8 | 11-21 | TEMP kept inside the repo |
| 0.3.0 | 1ba2a34 | 11-21 | UZDoom and the editor configured, launchers |
| 0.2.0 | ae53806 | 11-21 | `dms setup`, pinned tools |
| 0.1.0 | f760538 | 11-21 | Bootstrap, the `dms` command |
| 0.0.0+doc1 ... +doc5 | 6949053 ... cf276ce | 11-21 | .gitignore, design notes, plan, AGENTS.md |
| 0.0.0 | 069b2c2 | 11-21 | Initial commit |
