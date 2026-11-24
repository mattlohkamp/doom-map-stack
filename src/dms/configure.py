"""Configure the installed tools so they keep everything inside the repo and work together.

- UZDoom: an empty `uzdoom_portable.ini` next to the exe turns on its portable mode, so its
  config, saves (`Save/`) and screenshots (`Screenshots/`) stay in .tools/uzdoom/.
- Ultimate Doom Builder (always run with -portable, so settings live in .tools/udb/UDBuilder.cfg):
  the UZDoom UDMF game config gets UZDoom as its test engine (F9) and freedoom2.wad as its resource,
  and is preselected in the New Map dialog. UDB discards a settings file without `currentversion`
  (it calls it "outdated"), so that is written too, from Builder.exe's own version.
  The editor rewrites the file on exit, so `dms editor` re-applies these settings before each launch.
"""

from __future__ import annotations

import re
import shutil
import struct
import tomllib
from pathlib import Path

from dms import paths, udbcfg

UDB_GAME_CONFIG = "UZDoom_DoomUDMF.cfg"
UDB_GAMEKEY = "uzdoom_doomudmf"  # lowercased config filename without extension
# The UDMF format's default ACS compiler config (Scripting/ZDoom_ACS.cfg; `defaultscriptcompiler` in
# the mapformat_udmf section of Configurations/Includes/ZDoom_common.cfg). The editor lowercases names.
UDB_SCRIPT_CONFIG = "zdoom_acs.cfg"
UZDOOM_PORTABLE_INI = "uzdoom_portable.ini"

DEFAULT_SETTINGS = {"play": {"music": False, "windowed": True, "test_automap": True},
                    "board": {"port": 8765, "auto_pull": True},
                    "session": {"board": True, "browser": True, "editor": True, "game": True, "agent": "claude"},
                    "agents": {"claude": {"name": "Claude Code", "launcher": "start-claude.bat"}}}


def project_settings(root: Path) -> dict:
    """config/dms.toml (committed project settings), over the defaults."""
    settings = {k: dict(v) for k, v in DEFAULT_SETTINGS.items()}
    path = paths.dms_toml(root)
    if path.exists():
        with path.open("rb") as f:
            for section, values in tomllib.load(f).items():
                settings.setdefault(section, {}).update(values)
    return settings


# The testing automap ([play] test_automap): every thing shown (the IDDT cheat, level 2), drawn as
# its own sprite (so a red skull looks like one), keys shown even without the cheat, and every
# trigger line in its own colour (2 = including doors). am_cheat isn't saved in UZDoom's ini; the
# others are, so they're set on every launch, on or off, and whatever the ini holds doesn't matter.
# Skull locks get their own colours in the devtools mod's LOCKDEFS (cards and skulls share one).
TEST_AUTOMAP = {"am_cheat": (2, 0), "am_showthingsprites": (1, 0), "am_showkeys_always": (1, 0),
                "am_showtriggerlines": (2, 0)}


def play_args(settings: dict) -> list[str]:
    """Extra UZDoom arguments for test-play, from the [play] settings. Per launch: -nomusic isn't
    saved, and the automap settings are set explicitly every time (see TEST_AUTOMAP)."""
    args = []
    if not settings["play"].get("music", False):
        args.append("-nomusic")
    # Windowed or full screen, set every launch (UZDoom saves it). Windowed, it remembers where its
    # window was, so it reopens on the same monitor.
    args += ["+vid_fullscreen", "0" if settings["play"].get("windowed", True) else "1"]
    on = settings["play"].get("test_automap", True)
    for cvar, (yes, no) in TEST_AUTOMAP.items():
        args += [f"+{cvar}", str(yes if on else no)]  # not "+set": an unknown name shows in the log
    return args


def configure_uzdoom(uzdoom_exe: Path) -> None:
    marker = uzdoom_exe.parent / UZDOOM_PORTABLE_INI
    if not marker.exists():
        marker.write_bytes(b"")
        print(f"    created {marker.name} (portable mode)")


def pe_file_version(exe: Path) -> tuple[int, int, int, int]:
    """The FileVersion (a.b.c.d) from a Windows executable's VS_FIXEDFILEINFO block."""
    data = exe.read_bytes()
    i = data.find(struct.pack("<I", 0xFEEF04BD))
    if i < 0:
        raise ValueError(f"no version info in {exe}")
    ms, ls = struct.unpack_from("<II", data, i + 8)
    return ms >> 16, ms & 0xFFFF, ls >> 16, ls & 0xFFFF


def udb_version_number(udb_exe: Path) -> int:
    """What UDB writes as `currentversion`: Major * 1000000 + Revision."""
    major, _minor, _build, revision = pe_file_version(udb_exe)
    return major * 1000000 + revision


def udb_game_name(udb_dir: Path) -> str:
    """The display name of the UZDoom UDMF game config (its `game = "...";` line)."""
    text = (udb_dir / "Configurations" / UDB_GAME_CONFIG).read_text(encoding="utf-8", errors="replace")
    m = re.search(r'^game\s*=\s*"([^"]*)"\s*;', text, re.MULTILINE)
    if not m:
        raise ValueError(f"no game name in {UDB_GAME_CONFIG}")
    return m.group(1)


def udb_required_archives(udb_dir: Path) -> list[tuple[str, str, bool]]:
    """The archives the UZDoom game config requires as resources: (id, filename, exclude from testing).
    Read from Configurations/Includes/UZDoom_common.cfg; today that's ("gzdoom", "uzdoom.pk3", True)."""
    path = udb_dir / "Configurations" / "Includes" / "UZDoom_common.cfg"
    if not path.exists():
        return []
    block = udbcfg.parse(path.read_text(encoding="utf-8", errors="replace")).get("requiredarchives") or {}
    out = []
    for arc_id, spec in block.items():
        if isinstance(spec, dict) and isinstance(spec.get("filename"), str):
            out.append((arc_id, udbcfg.unquote(spec["filename"]), spec.get("need_exclude") == "true"))
    return out


def _resource(type_: int, location: Path, notfortesting: bool, requiredarchives: str | None = None) -> dict:
    res = {
        "type": udbcfg.integer(type_),
        "location": udbcfg.string(str(location)),
        "option1": udbcfg.integer(0),
        "option2": udbcfg.integer(0),
        "notfortesting": udbcfg.integer(int(notfortesting)),
    }
    if requiredarchives:
        res["requiredarchives"] = udbcfg.string(requiredarchives)
    return res


RESOURCE_WAD, RESOURCE_PK3 = 0, 2


def udb_settings(
    uzdoom_exe: Path,
    iwad: Path,
    version: int,
    game_name: str,
    required: list[tuple[str, str, bool]] = (),
    extra_args: str = "",
) -> dict[str, "str | dict"]:
    """The settings dms owns in UDBuilder.cfg, as dotted path -> raw value or structure."""
    base = f"configurations.{UDB_GAMEKEY}"
    # Same order UZDoom loads them in: the engine's own archive (e.g. uzdoom.pk3), then the IWAD.
    # The engine archive is excluded from F9 testing (UZDoom loads it by itself).
    resources = []
    for arc_id, filename, exclude in required:
        resources.append(_resource(RESOURCE_PK3, uzdoom_exe.parent / filename, exclude, arc_id))
    resources.append(_resource(RESOURCE_WAD, iwad, False))
    return {
        "currentversion": udbcfg.integer(version),
        "lastusedconfigname": udbcfg.string(game_name),
        f"{base}.enabled": udbcfg.boolean(True),
        f"{base}.currentengineindex": udbcfg.integer(0),
        f"{base}.engines": {
            "engine0": {
                "testprogramname": udbcfg.string("UZDoom"),
                "testprogram": udbcfg.string(str(uzdoom_exe)),
                "testparameters": udbcfg.string(""),
                "testshortpaths": udbcfg.boolean(False),
                "testlinuxpaths": udbcfg.boolean(False),
                "customparameters": udbcfg.boolean(False),
                "testskill": udbcfg.integer(3),
                "additionalparameters": udbcfg.string(extra_args),
            }
        },
        f"{base}.resources": {f"resource{i}": r for i, r in enumerate(resources)},
    }


def configure_udb(
    udb_exe: Path,
    uzdoom_exe: Path,
    iwad: Path,
    *,
    extra_args: list[str] = (),
    repo: Path | None = None,
) -> None:
    """extra_args: appended to UZDoom's command line on F9.
    repo: if given, the Open dialog starts in <repo>/build/scratch unless it's already somewhere in the repo."""
    udb_dir = udb_exe.parent
    cfg_path = udb_dir / "UDBuilder.cfg"
    if not cfg_path.exists():
        # What UDB itself does on first run: start from the shipped defaults.
        shutil.copyfile(udb_dir / "UDBuilder.default.cfg", cfg_path)
        print(f"    created {cfg_path.name} from defaults")

    before = cfg_path.read_text(encoding="utf-8")
    data = udbcfg.parse(before)
    required = udb_required_archives(udb_dir)
    for _id, filename, _ex in required:
        if not (uzdoom_exe.parent / filename).exists():
            print(f"    warning: the editor wants {filename}, not found next to {uzdoom_exe.name}")
    settings = udb_settings(
        uzdoom_exe, iwad, udb_version_number(udb_exe), udb_game_name(udb_dir), required, " ".join(extra_args)
    )
    if repo is not None:
        current = data.get("lastusedmapfolder")
        current_path = Path(udbcfg.unquote(current)) if isinstance(current, str) else None
        if current_path is None or not current_path.resolve().is_relative_to(repo.resolve()):
            scratch = repo / "build" / "scratch"
            scratch.mkdir(parents=True, exist_ok=True)
            settings["lastusedmapfolder"] = udbcfg.string(str(scratch))
    for path, value in settings.items():
        udbcfg.set_path(data, path, value)
    after = udbcfg.dump(data)
    if udbcfg.parse(after) != udbcfg.parse(before):
        cfg_path.write_text(after, encoding="utf-8", newline="")
        names = ", ".join([f for _i, f, _e in required] + [iwad.name])
        f9 = " ".join(["UZDoom", *extra_args])
        print(f"    configured {cfg_path.name}: F9 runs {f9}; resources {names}")


PLUGIN_SOURCE = Path("src") / "udb-plugin" / "DmsBridge.cs"
PLUGIN_DLL = "DmsBridge.dll"


def csc_path() -> Path:
    """The C# compiler that ships with Windows (.NET Framework 4.8)."""
    import os

    return Path(os.environ.get("WINDIR", r"C:\Windows")) / "Microsoft.NET" / "Framework64" / "v4.0.30319" / "csc.exe"


def build_udb_plugin(root: Path, udb_exe: Path) -> bool:
    """Compile src/udb-plugin/DmsBridge.cs into the editor's Plugins folder (live reload, status).
    Skipped when the DLL is up to date with the source. Returns False if it couldn't be built."""
    import hashlib
    import subprocess

    src = root / PLUGIN_SOURCE
    plugins = udb_exe.parent / "Plugins"
    dll = plugins / PLUGIN_DLL
    stamp = plugins / (PLUGIN_DLL + ".sha256")
    actions = src.with_name("Actions.cfg")  # the plugin's editor actions (Send to Claude), embedded
    # Rebuild when the source, its actions or the editor version changes.
    digest = hashlib.sha256(src.read_bytes() + actions.read_bytes()
                            + str(udb_version_number(udb_exe)).encode()).hexdigest()
    if dll.exists() and stamp.exists() and stamp.read_text(encoding="utf-8").strip() == digest:
        return True
    csc = csc_path()
    if not csc.exists():
        print(f"    warning: {csc} not found; the editor plugin (live reload) wasn't built")
        return False
    result = subprocess.run(
        [str(csc), "/nologo", "/target:library", "/optimize+", f"/out:{dll}",
         f"/reference:{udb_exe}", "/reference:System.Windows.Forms.dll", "/reference:System.Drawing.dll",
         f"/resource:{actions},Dms.UdbBridge.Resources.Actions.cfg", str(src)],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print("    warning: the editor plugin didn't compile:")
        print(result.stdout + result.stderr)
        return False
    stamp.write_text(digest + "\n", encoding="utf-8")
    print(f"    built {dll.name} (editor plugin: live reload, status, Send to Claude)")
    return True


def configure_all(root: Path, paths: dict[str, Path], managed: set[str]) -> None:
    """paths: tool name -> main file. Only tools in `managed` (installed in .tools/) are modified;
    an outside install listed in tools.local.json is only referenced."""
    if "uzdoom" in managed:
        configure_uzdoom(paths["uzdoom"])
    if "udb" in managed and all(k in paths for k in ("uzdoom", "freedoom")):
        extra = play_args(project_settings(root))
        configure_udb(paths["udb"], paths["uzdoom"], paths["freedoom"], extra_args=extra, repo=root)
        build_udb_plugin(root, paths["udb"])
