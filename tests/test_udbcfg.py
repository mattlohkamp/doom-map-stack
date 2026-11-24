import struct
from pathlib import Path

from dms import configure, udbcfg

SAMPLE = r"""
// comment
shortcuts
{
	builder_closemap = 0;   /* block
	comment */
	builder_undo = 131162;
}

configurations
{
}

nothing;
visualmousesensx = 4f;
scriptfontname = "Lucida Console";
path = "C:\\Doom\\a \"b\".wad";
"""


def test_parse_values_and_structures():
    d = udbcfg.parse(SAMPLE)
    assert d["shortcuts"] == {"builder_closemap": "0", "builder_undo": "131162"}
    assert d["configurations"] == {}
    assert d["nothing"] is None
    assert d["visualmousesensx"] == "4f"
    assert d["path"] == r'"C:\\Doom\\a \"b\".wad"'


def test_round_trip_keeps_everything():
    d = udbcfg.parse(SAMPLE)
    assert udbcfg.parse(udbcfg.dump(d)) == d


def test_string_escaping():
    assert udbcfg.string(r'C:\x "y"') == r'"C:\\x \"y\""'
    assert udbcfg.unquote(udbcfg.string(r'C:\x "y"')) == r'C:\x "y"'
    assert udbcfg.unquote(r'"a\tb\065"') == "a\tbA"


def test_set_and_get_path():
    d = udbcfg.parse(SAMPLE)
    udbcfg.set_path(d, "configurations.uzdoom_doomudmf.enabled", "true")
    assert udbcfg.get_path(d, "configurations.uzdoom_doomudmf.enabled") == "true"
    assert d["shortcuts"]["builder_undo"] == "131162"


def fake_udb(tmp_path: Path) -> Path:
    """A UDB folder with default settings, a game config and a Builder.exe carrying version 3.0.0.4336."""
    udb = tmp_path / "udb"
    (udb / "Configurations").mkdir(parents=True)
    (udb / "UDBuilder.default.cfg").write_text(SAMPLE)
    (udb / "Configurations" / "UZDoom_DoomUDMF.cfg").write_text(
        '// header\ngame = "UZDoom: Doom 2 (UDMF)";\ninclude("Includes\\\\x.cfg");\n'
    )
    (udb / "Configurations" / "Includes").mkdir()
    (udb / "Configurations" / "Includes" / "UZDoom_common.cfg").write_text(
        'requiredarchives\n{\n\tgzdoom\n\t{\n\t\tfilename = "uzdoom.pk3";\n\t\tneed_exclude = true;\n'
        '\t\t0\n\t\t{\n\t\t\tclass = "actor";\n\t\t}\n\t}\n}\n'
    )
    fixed = struct.pack("<IIII", 0xFEEF04BD, 0x00010000, (3 << 16) | 0, (0 << 16) | 4336)
    (udb / "Builder.exe").write_bytes(b"MZ" + b"\0" * 100 + fixed + b"\0" * 40)
    return udb / "Builder.exe"


def test_pe_file_version(tmp_path: Path):
    assert configure.pe_file_version(fake_udb(tmp_path)) == (3, 0, 0, 4336)
    assert configure.udb_version_number(tmp_path / "udb" / "Builder.exe") == 3004336


def test_configure_udb_creates_from_defaults_and_keeps_other_settings(tmp_path: Path):
    exe = fake_udb(tmp_path)
    udb = exe.parent
    uz = tmp_path / "uzdoom" / "uzdoom.exe"
    iwad = tmp_path / "freedoom" / "freedoom2.wad"

    configure.configure_udb(exe, uz, iwad)
    d = udbcfg.parse((udb / "UDBuilder.cfg").read_text())
    base = "configurations.uzdoom_doomudmf"
    assert udbcfg.get_path(d, f"{base}.engines.engine0.testprogram") == udbcfg.string(str(uz))
    # The engine archive the game config requires comes first, excluded from testing; then the IWAD.
    res = udbcfg.get_path(d, f"{base}.resources")
    assert res["resource0"]["location"] == udbcfg.string(str(uz.parent / "uzdoom.pk3"))
    assert res["resource0"]["type"] == "2"
    assert res["resource0"]["notfortesting"] == "1"
    assert res["resource0"]["requiredarchives"] == '"gzdoom"'
    assert res["resource1"]["location"] == udbcfg.string(str(iwad))
    assert res["resource1"]["notfortesting"] == "0"
    assert d["scriptfontname"] == '"Lucida Console"'
    assert d["currentversion"] == "3004336"  # without it UDB discards the file as "outdated"
    assert d["lastusedconfigname"] == '"UZDoom: Doom 2 (UDMF)"'  # preselected in New Map

    # A setting the editor saved later survives a re-run.
    cfg = udb / "UDBuilder.cfg"
    d["configurations"]["uzdoom_doomudmf"]["startmode"] = '"LinedefsMode"'
    cfg.write_text(udbcfg.dump(d))
    configure.configure_udb(exe, uz, iwad)
    d2 = udbcfg.parse(cfg.read_text())
    assert udbcfg.get_path(d2, f"{base}.startmode") == '"LinedefsMode"'


def test_configure_uzdoom_portable_marker(tmp_path: Path):
    exe = tmp_path / "uzdoom.exe"
    configure.configure_uzdoom(exe)
    assert (tmp_path / "uzdoom_portable.ini").exists()


def test_music_setting(tmp_path: Path):
    args = configure.play_args(configure.project_settings(tmp_path))
    assert args[0] == "-nomusic"  # default: off
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "dms.toml").write_text("[play]\nmusic = true\n")
    assert "-nomusic" not in configure.play_args(configure.project_settings(tmp_path))


def test_windowed_setting(tmp_path: Path):
    assert configure.play_args(configure.project_settings(tmp_path))[1:3] == ["+vid_fullscreen", "0"]  # default
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "dms.toml").write_text("[play]\nwindowed = false\n")
    assert configure.play_args(configure.project_settings(tmp_path))[1:3] == ["+vid_fullscreen", "1"]


def test_test_automap_setting(tmp_path: Path):
    args = configure.play_args(configure.project_settings(tmp_path))  # default: on
    assert args[3:] == ["+am_cheat", "2", "+am_showthingsprites", "1", "+am_showkeys_always", "1",
                        "+am_showtriggerlines", "2"]
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "dms.toml").write_text("[play]\ntest_automap = false\n")  # off: set back explicitly
    assert configure.play_args(configure.project_settings(tmp_path))[3:] == [
        "+am_cheat", "0", "+am_showthingsprites", "0", "+am_showkeys_always", "0", "+am_showtriggerlines", "0"]


def test_f9_args_and_open_folder(tmp_path: Path):
    exe = fake_udb(tmp_path)
    repo = tmp_path / "repo"
    uz, iwad = tmp_path / "uzdoom" / "uzdoom.exe", tmp_path / "freedoom" / "freedoom2.wad"
    configure.configure_udb(exe, uz, iwad, extra_args=["-nomusic"], repo=repo)
    cfg = exe.parent / "UDBuilder.cfg"
    d = udbcfg.parse(cfg.read_text())
    engine = udbcfg.get_path(d, "configurations.uzdoom_doomudmf.engines.engine0")
    assert engine["additionalparameters"] == '"-nomusic"'
    assert udbcfg.unquote(d["lastusedmapfolder"]) == str(repo / "build" / "scratch")

    # A folder the mapper picked inside the repo is kept; one outside is replaced.
    inside = repo / "maps"
    inside.mkdir()
    d["lastusedmapfolder"] = udbcfg.string(str(inside))
    cfg.write_text(udbcfg.dump(d))
    configure.configure_udb(exe, uz, iwad, repo=repo)
    assert udbcfg.unquote(udbcfg.parse(cfg.read_text())["lastusedmapfolder"]) == str(inside)

    d["lastusedmapfolder"] = udbcfg.string(str(tmp_path / "Documents"))
    cfg.write_text(udbcfg.dump(d))
    configure.configure_udb(exe, uz, iwad, repo=repo)
    assert udbcfg.unquote(udbcfg.parse(cfg.read_text())["lastusedmapfolder"]) == str(repo / "build" / "scratch")
