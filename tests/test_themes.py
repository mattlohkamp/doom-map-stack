from dms import themes
from dms.gen import MapBuilder


def _map():
    """A hall (gid "hall") with a step up east onto a ledge of slime (gid "ledge")."""
    m = MapBuilder()
    hall = m.sector("hall", floor=0, ceiling=128, light=96, floor_tex="FLOOR4_8", ceiling_tex="CEIL3_5")
    ledge = m.sector("ledge", floor=16, ceiling=128, light=160, floor_tex="NUKAGE1", ceiling_tex="F_SKY1")
    m.sectors[hall.index]["fadecolor"] = 0x080808
    m.sectors[hall.index]["fogdensity"] = 200
    m.wall((0, 0), (0, 256), hall, "hall.wall_w", texture="METAL4")
    m.wall((0, 256), (200, 256), hall, "hall.wall_n", texture="METAL4")
    m.wall((200, 256), (256, 256), hall, "hall.switch", texture="SW1GRAY")
    door = m.wall((256, 0), (0, 0), hall, "hall.door", texture="BIGDOOR1")
    m.linedefs[door]["special"] = 12
    m.two_sided((256, 256), (256, 0), hall, ledge, "hall.step", texture="STEPTOP")
    m.wall((256, 256), (512, 256), ledge, "ledge.wall_n", texture="BROWN1")
    m.wall((512, 256), (512, 0), ledge, "ledge.wall_e", texture="BROWN1")
    m.wall((512, 0), (256, 0), ledge, "ledge.wall_s", texture="BROWN1")
    m.thing(9830, 64, 64, "hall.light")
    m.thing(2028, 128, 128, "hall.lamp")
    m.thing(3001, 400, 128, "ledge.imp")
    return m.textmap()


def test_harvest_sorts_textures_into_roles_by_where_they_sit():
    h = themes.harvest(_map(), ["hall"], "test")
    t = h.theme.textures
    assert t["wall"] == ["METAL4"]
    assert t["switch"] == ["SW1GRAY"]
    assert t["door"] == ["BIGDOOR1"]
    assert t["step"] == ["STEPTOP"]                 # the hall's side of the 16 step; the ledge's isn't picked
    assert t["floor"] == ["FLOOR4_8"] and t["ceiling"] == ["CEIL3_5"]
    assert "BROWN1" not in h.theme.names() and "liquid" not in t
    assert h.theme.things["light_source"] == [9830, 2028]   # the imp stands on the ledge
    assert h.theme.atmosphere == {"light": 96, "light_range": [96, 96], "lightcolor": "", "fog": "080808",
                                  "fogdensity": 200}


def test_harvest_takes_gid_patterns_liquids_and_the_sky():
    h = themes.harvest(_map(), ["hall", "led*"], "test", sky="CACOSKY")
    t = h.theme.textures
    assert t["liquid"] == ["NUKAGE1"] and t["sky"] == ["CACOSKY"]
    assert t["wall"] == ["BROWN1"] and t["wall_alt"] == ["METAL4"]   # by length: 768 against 456
    assert h.theme.atmosphere["light_range"] == [96, 160]


def test_harvest_without_a_match_says_so():
    try:
        themes.harvest(_map(), ["nothing*"], "test")
    except themes.ThemeError as e:
        assert "nothing*" in str(e)
    else:
        raise AssertionError("expected ThemeError")


def test_dump_and_load_round_trip(tmp_path):
    h = themes.harvest(_map(), ["hall"], "test")
    h.theme.decals = ["BloodSplat"]
    folder = tmp_path / "themes" / "test"
    folder.mkdir(parents=True)
    (folder / "theme.toml").write_text(themes.dump(h.theme, header=themes.harvest_report(h, "x", ["hall"])),
                                       encoding="utf-8")
    back = themes.find(tmp_path, "test")
    assert back.textures == h.theme.textures and back.things == h.theme.things
    assert back.atmosphere == h.theme.atmosphere and back.decals == ["BloodSplat"]
    assert back.texture("wall") == "METAL4" and back.texture("light") is None
    assert [t.name for t in themes.all_themes(tmp_path)] == ["test"]


def test_check_finds_unknown_roles_names_and_values():
    t = themes.Theme("x", textures={"wall": ["METAL4", "NOPE"], "walls": ["METAL4"]}, things={"lights": [1]},
                     atmosphere={"light": 300, "fog": "zz", "mood": 1})
    problems = themes.check(t, known_walls={"METAL4"}, known_flats=set())
    assert any("NOPE" in p for p in problems)
    assert any(p.startswith("textures.walls") for p in problems)
    assert any(p.startswith("things.lights") for p in problems)
    assert any(p.startswith("atmosphere.light:") for p in problems)
    assert any(p.startswith("atmosphere.fog") for p in problems)
    assert any(p.startswith("atmosphere.mood") for p in problems)
    assert themes.check(themes.Theme("ok", textures={"wall": ["METAL4"]}), {"METAL4"}, set()) == []
