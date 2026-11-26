from dms import mapassets
from dms.resources import Picture


def _solid(w, h, rgba):
    return Picture(w, h, 0, 0, bytes(rgba) * (w * h))


def test_parse_textures_reads_definitions_patches_and_their_changes():
    defs = mapassets.parse_textures('''
        // a comment with a { brace
        WallTexture "MYWALL", 128, 64
        {
            Patch "A", 0, 0
            Patch "B", 64, -8 { Blend "#000000", 0.5  FlipX }
        }
        Sprite "MYSPA0", 21, 28
        {
            Offset 11, 28
            Patch "A", 0, -38 { Translation "Desaturate", 31 }
        }
        Flat FLOORX, 64, 64 { Patch "A", 0, 0 { Rotate 90 } }
    ''')
    assert [(d["kind"], d["name"], d["width"], d["height"]) for d in defs] == [
        ("walltexture", "MYWALL", 128, 64), ("sprite", "MYSPA0", 21, 28), ("flat", "FLOORX", 64, 64)]
    assert defs[0]["patches"][1] == {"name": "B", "x": 64, "y": -8, "props": {"blend": ["#000000", "0.5"], "flipx": []}}
    assert defs[1]["offset"] == (11, 28)
    assert defs[1]["patches"][0]["props"] == {"translation": ["Desaturate", "31"]}
    assert defs[2]["patches"][0]["props"] == {"rotate": ["90"]}


def test_compose_places_crops_blends_and_recolours():
    red = _solid(4, 4, (200, 0, 0, 255))
    source = lambda name: red if name == "RED" else None
    d = mapassets.parse_textures('Texture "T", 4, 2 { Patch "RED", 2, -2 }')[0]
    p, approx = mapassets.compose(d, source)
    assert not approx and (p.width, p.height) == (4, 2)
    assert p.rgba[0:4] == bytes((0, 0, 0, 0))            # left of the patch: nothing
    assert p.rgba[8:12] == bytes((200, 0, 0, 255))       # the patch, moved right, its top rows cut off

    half = mapassets.compose(mapassets.parse_textures('Texture "T", 4, 4 { Patch "RED", 0, 0 { Blend "#000000", 0.5 } }')[0], source)[0]
    assert half.rgba[0:4] == bytes((100, 0, 0, 255))
    grey = mapassets.compose(mapassets.parse_textures('Texture "T", 4, 4 { Patch "RED", 0, 0 { Translation "Desaturate", 31 } }')[0], source)[0]
    assert grey.rgba[0] == grey.rgba[1] == grey.rgba[2] and grey.rgba[3] == 255
    green = mapassets.compose(mapassets.parse_textures('Texture "T", 4, 4 { Patch "RED", 0, 0 { Translation "Green" } }')[0], source)[0]
    assert green.rgba[0] == 0 and green.rgba[1] > 0 and green.rgba[2] == 0


def test_compose_says_when_it_is_guessing():
    red = _solid(2, 2, (200, 0, 0, 255))
    source = lambda name: red if name == "RED" else None
    missing = mapassets.parse_textures('Texture "T", 2, 2 { Patch "NOPE", 0, 0 }')[0]
    ranges = mapassets.parse_textures('Texture "T", 2, 2 { Patch "RED", 0, 0 { Translation "112:127=176:191" } }')[0]
    assert mapassets.compose(missing, source)[1] is True
    assert mapassets.compose(ranges, source)[1] is True


def test_parse_actors_finds_classes_their_spawn_frames_and_sizes():
    actors = mapassets.parse_actors('''
        version "4.10"
        class MapStuff : EventHandler { override void WorldLoaded(WorldEvent e) {} }
        class MapTorch : Actor
        {
            Default { Radius 16; Height 28; +SOLID }
            States
            {
            Spawn:
                CACT AB 4;
                Loop;
            }
        }
        class MapSleeper : Spectre { }
    ''')
    assert [a["class"] for a in actors] == ["MapTorch", "MapSleeper"]
    assert actors[0]["frames"] == [["CACTA", 4], ["CACTB", 4]] and (actors[0]["radius"], actors[0]["height"]) == (16, 28)
    assert actors[1]["parent"] == "Spectre" and actors[1]["frames"] == []


def test_usage_counts_what_each_map_uses(tmp_path):
    for name, wall, song in (("a", "GRAY1", "D_RUNNIN"), ("b", "MARBLE1", "")):
        folder = tmp_path / "maps" / name
        folder.mkdir(parents=True)
        (folder / "map.toml").write_text(f'title = "{name}"\nsky = "SKY1"\nmusic = "{song}"\n')
        (folder / "TEXTMAP").write_text(
            'namespace = "zdoom";\n'
            'thing { x = 0; y = 0; type = 3004; }\nthing { x = 8; y = 0; type = 3004; }\nthing { type = 1; }\n'
            f'sidedef {{ sector = 0; texturemiddle = "{wall}"; texturetop = "-"; }}\n'
            f'sidedef {{ sector = 0; texturemiddle = "{wall}"; }}\n'
            'sector { texturefloor = "FLOOR0_1"; textureceiling = "GRAY1"; }\n')
    (tmp_path / "maps" / "a" / "zscript.zs").write_text(
        'class AThing : Actor {}\n// A_StartSound("not/this");\n'
        'class A : EventHandler { void f() { A_StartSound("world/quake", CHAN_AUTO); Actor.Spawn("AThing", (0,0,0)); } }\n')
    u = mapassets.usage(tmp_path)
    assert u["maps"] == ["a", "b"]
    assert u["tex"]["GRAY1"] == {"a": 3, "b": 1}          # walls and flats counted together
    assert u["tex"]["MARBLE1"] == {"b": 2} and "-" not in u["tex"]
    assert u["tex"]["SKY1"] == {"a": 1, "b": 1}           # the sky from map.toml
    assert u["things"]["3004"] == {"a": 2, "b": 2}
    assert u["music"] == {"D_RUNNIN": {"a": 1}}
    assert u["sounds"] == {"world/quake": {"a": 1}} and u["classes"] == {"athing": {"a": 1}}

def test_a_maps_own_pictures_are_packed_and_known(tmp_path):
    import struct
    import zlib

    from dms import extras, maps

    info = maps.new(tmp_path, "a")
    d = info.folder / "textures"
    d.mkdir()
    chunk = lambda kind, data: struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))
    png = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 2, 3, 8, 2, 0, 0, 0))
           + chunk(b"IDAT", zlib.compress(b"\0" + bytes(6) + b"\0" + bytes(6) + b"\0" + bytes(6))) + chunk(b"IEND", b""))
    (d / "mystar.png").write_bytes(png)
    (d / "much-too-long-a-name.png").write_bytes(png)      # not a lump name: left out
    (d / "NOTICE.txt").write_text("licence")
    assert [n for n, _ in extras.pictures(info)] == ["MYSTAR"]
    assert [lump.name for lump in extras.lumps(info)] == ["TX_START", "MYSTAR", "TX_END"]
    walls, flats = extras.textures(info)
    assert walls == {"MYSTAR": (2, 3)} and flats == {"MYSTAR"}     # usable on walls and as a flat

def test_a_maps_own_sprites_are_packed(tmp_path):
    from dms import extras, maps

    info = maps.new(tmp_path, "a")
    d = info.folder / "sprites"
    d.mkdir()
    for name in ("abcdA1", "ABCDA2A8", "ABCDB0", "toolong", "ABCD", "NOTICE"):
        (d / f"{name}.png").write_bytes(b"\x89PNG")
    (d / "NOTICE.txt").write_text("where they came from")
    assert [n for n, _ in extras.sprites(info)] == ["ABCDA1", "ABCDA2A8", "ABCDB0"]   # sprite lump names only
    assert [lump.name for lump in extras.lumps(info)] == ["SS_START", "ABCDA1", "ABCDA2A8", "ABCDB0", "SS_END"]
    assert extras.textures(info) == ({}, set())                                      # not textures


def test_script_monsters_are_known_by_their_default():
    from dms import mapassets

    text = """
    class MyBot : Actor { Default { Monster; +FLOAT Health 25; } States { Spawn: ABCD AB 8; Loop; } }
    class MyBigBot : MyBot { Default { Health 90; } }
    class MyFlagged : Actor { Default { +ISMONSTER } }
    class MyLamp : Actor { Default { Radius 8; } }   // no Monster line: not a monster
    """
    got = {a["class"]: a["monster"] for a in mapassets.parse_actors(text)}
    assert got == {"MyBot": True, "MyBigBot": None, "MyFlagged": True, "MyLamp": None}   # MyBigBot: from its parent
