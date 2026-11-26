# Projects: maps outside the tool (plan, building)

*Planned 2026-11-25 with the mapper. Status: phase 1 built (project core, `--project`, build output and saves
in the project; tried on a scratch project from outside and from inside its folder), released in v0.21.0;
phase 2 next.*

Until now the tool (doom-map-stack) and the maps it builds (hello-room, Cacobelisk) share one repo, so
one history mixes tool releases with map work, and a map can't be kept, shared or versioned on its
own. This splits them: **the tool repo** holds the tool and everything it downloads; **a project
folder**, anywhere, holds one or more maps and everything that belongs to them, with its own git.

## Decided (with the mapper, 2026-11-25)

- **A project holds one or more maps** (`maps/<name>/`, as now); a new project starts with one.
- **Settings are layered**: the tool's defaults, then the mapper's own (a git-ignored `user\` folder in
  the tool repo: shared by every project, still nothing outside the repo), then the project's (committed
  with it). The later layer wins.
- **Claude runs in the project folder**, so its commits and notes go to the map's repo. Tool work is a
  session in the tool repo.
- **Cacobelisk is split out with its history** into a project repo of its own.
- The tool repo keeps **hello-room** as its example and test map: the tool repo is itself a project
  (the default one, and the only one without a `dms-project.toml`: nothing new goes in its root), so tests
  and the example work as they do now.

## Where things go

| What | Tool repo | `user\` (tool repo, git-ignored) | Project folder |
|---|---|---|---|
| Code, launchers, `.tools\` (UZDoom, the editor, Python), `catalog\` | yes | | |
| Tool config (`config\dms.toml`: board port, session defaults, agents, play) | defaults | `user\dms.toml` overrides | `dms-project.toml` overrides `[play]` |
| Maps (`maps\<name>\`) | hello-room (example) | | yes |
| Themes | | the mapper's library, `user\themes\` | `themes\` (travel with the project; win by name) |
| Asset favourites | | `user\favorites.json` (starring writes here) | `favorites.json` (read, merged; optional) |
| Recent projects | | `user\projects.json` | |
| Build output, history, notes inbox, shots, game saves, last map, watch heartbeat, agents | | | `build\` (git-ignored) |
| Converted assets cache, scratch | `build\assets\`, `build\scratch\` (the IWAD's, shared) | | |

A project folder:

```
my-episode\
  dms-project.toml      title; optional [play] overrides
  maps\<name>\          map.toml, map.py, TEXTMAP, notes.md, zscript.zs, textures.txt, textures\...
  themes\<name>\        theme.toml
  CLAUDE.md             written by dms: imports the tool's docs, says where the tool is (git-ignored)
  .claude\settings.json written by dms: hooks calling the tool's dms.ps1 (git-ignored)
  .gitignore            build/, CLAUDE.md, .claude/
  build\                everything generated
```

`CLAUDE.md` and the hooks name the tool repo by its absolute path, so they're machine-specific: dms
writes them (`dms project init`, and again on every session start) and the project's git ignores them.

## Which project a command acts on

Explicit, like map names: `--project PATH` on any command; else `DMS_PROJECT`; else the folder the
command runs in, or the nearest above it with a `dms-project.toml`; else the tool repo itself (the
example project). Every map command prints the project with the map (`dms build: cacobelisk in
D:\maps\cacobelisk-project`). `dms.ps1` keeps the caller's folder, so running the tool from a project
folder just works.

## Phases

1. **Project core.** `src/dms/project.py` (`Project`: its maps, build, themes, settings; how it's found);
   `--project` on every command; `MapInfo` knows its project, so `build_dir` is the project's; game saves,
   last map, the watch heartbeat and the agents registry move into the project's `build\`. The tool repo
   is the example project (no marker file in its root). Nothing moves for hello-room. Tests.
2. **Layered settings.** `user\` (git-ignored): `dms.toml`, `themes\`, `favorites.json`, `projects.json`;
   themes and favourites merged (project wins); config merged; the asset browser and theme viewer say where
   each favourite or theme comes from.
3. **Projects for the mapper and Claude.** `dms project init PATH [--map NAME]`: the folder, a first map,
   `.gitignore`, `git init`; `CLAUDE.md` + `.claude\settings.json` (re)written on every session start.
   AGENTS.md split: the mapping rules (commands, notes, order of work) into `docs/mapping.md`, which a
   project's `CLAUDE.md` imports; AGENTS.md keeps the tool-development rules and imports it too. Start
   Session: recent projects, "Open folder...", "New project...", then the map; `start-claude.bat` starts
   Claude in the project folder. The board serves one project (a board for another project takes the next
   free port; its banner names the project).
4. **Cacobelisk moves out.** A project repo made from its history (its `maps/cacobelisk` commits, carried
   over and moved under the new layout), its `build\cacobelisk\` (history, inbox, shots, pulled saves) and
   its themes (techbase, grotto: into the project; copies into `user\themes\` if wanted). The tool repo drops
   it. Where the new repo is hosted (a GitHub repo of its own?) is the mapper's call when it happens.
5. **Releases.** The tool's version scheme (`major.minor.fix`, `+docN` for docs-only) goes into AGENTS.md
   with a `CHANGELOG.md`; the project support is the next minor release.
