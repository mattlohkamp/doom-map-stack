import io
import struct
import wave

from dms import resources, wad


def _patch(width, height, columns):
    """A Doom picture: columns is a list of [(top, [palette indices])] posts per column."""
    header = struct.pack("<hhhh", width, height, 0, 0)
    offs_size = 4 * width
    body = b""
    offsets = []
    for posts in columns:
        offsets.append(8 + offs_size + len(body))
        for top, pixels in posts:
            body += bytes([top, len(pixels), 0]) + bytes(pixels) + b"\0"
        body += b"\xff"
    return header + struct.pack(f"<{width}I", *offsets) + body


def _palette():
    pal = bytearray(768)
    pal[3:6] = bytes((255, 0, 0))    # 1: red
    pal[6:9] = bytes((0, 255, 0))    # 2: green
    pal[9:12] = bytes((0, 0, 255))   # 3: blue
    return bytes(pal)


def _texture1(entries):
    """entries: [(name, w, h, [(ox, oy, patch index)])]"""
    blobs = []
    for name, w, h, patches in entries:
        b = name.encode().ljust(8, b"\0") + struct.pack("<ihhih", 0, w, h, 0, len(patches))
        for ox, oy, idx in patches:
            b += struct.pack("<hhhhh", ox, oy, idx, 1, 0)
        blobs.append(b)
    head = 4 + 4 * len(blobs)
    offsets, pos = [], head
    for b in blobs:
        offsets.append(pos)
        pos += len(b)
    return struct.pack("<i", len(blobs)) + struct.pack(f"<{len(blobs)}i", *offsets) + b"".join(blobs)


def _dmx(rate, samples):
    data = b"\x80" * 16 + bytes(samples) + b"\x80" * 16
    return struct.pack("<HHI", 3, rate, len(data)) + data


def make_wad(tmp_path):
    p1 = _patch(2, 2, [[(0, [1, 1])], [(0, [2])]])   # column 1 has only its top pixel: see-through below
    p2 = _patch(1, 1, [[(0, [3])]])
    pnames = struct.pack("<i", 2) + b"P1".ljust(8, b"\0") + b"P2".ljust(8, b"\0")
    tex = _texture1([("WALL1", 4, 2, [(0, 0, 0), (3, 1, 1)])])
    lumps = [
        wad.Lump("PLAYPAL", _palette()), wad.Lump("PNAMES", pnames), wad.Lump("TEXTURE1", tex),
        wad.Lump("P1", p1), wad.Lump("P2", p2),
        wad.Lump("DSTEST", _dmx(11025, [0, 128, 255])),
        wad.Lump("S_START"), wad.Lump("TROOA1", p2), wad.Lump("TROOB1", p2), wad.Lump("S_END"),
        wad.Lump("F_START"), wad.Lump("FLAT1", bytes([2]) * 4096), wad.Lump("F_END"),
    ]
    path = tmp_path / "test.wad"
    wad.write(path, lumps, kind="IWAD")
    return path


def _px(p, x, y):
    i = (y * p.width + x) * 4
    return tuple(p.rgba[i : i + 4])


def test_textures_are_composited_from_their_patches(tmp_path):
    res = resources.Resources(make_wad(tmp_path))
    assert res.patch_names == ["P1", "P2"]
    t = res.texture("WALL1")
    assert (t.width, t.height) == (4, 2)
    assert _px(t, 0, 0) == (255, 0, 0, 255) and _px(t, 0, 1) == (255, 0, 0, 255)
    assert _px(t, 1, 0) == (0, 255, 0, 255)
    assert _px(t, 1, 1)[3] == 0            # P1's second column is one pixel tall
    assert _px(t, 3, 1) == (0, 0, 255, 255)  # P2 placed at (3, 1)
    assert resources.masked(t)


def test_flats_sprites_and_namespaces(tmp_path):
    res = resources.Resources(make_wad(tmp_path))
    f = res.flat("FLAT1")
    assert (f.width, f.height) == (64, 64) and _px(f, 10, 10) == (0, 255, 0, 255)
    assert set(res.sprites) == {"TROOA1", "TROOB1"}
    assert resources.sprite_frames(res, "TROO") == ["TROOA1", "TROOB1"]
    assert resources.resolve_sprite(res, "TROOA2A8") == "TROOA1"
    assert resources.resolve_sprite(res, "internal:light") is None


def test_dmx_sounds_become_wav(tmp_path):
    res = resources.Resources(make_wad(tmp_path))
    data, ext = res.sound_file("DSTEST")
    assert ext == "wav"
    with wave.open(io.BytesIO(data)) as w:
        assert w.getframerate() == 11025 and w.getsampwidth() == 1
        assert w.readframes(10) == bytes([0, 128, 255])  # the 16 pad bytes each end are dropped


def test_midi_length_follows_tempo():
    # One track, 96 ticks a beat, tempo 1 s a beat, a note-off 192 ticks in: 2 s.
    track = (b"\x00\xff\x51\x03" + (1000000).to_bytes(3, "big")
             + b"\x00\x90\x3c\x40" + b"\x81\x40\x80\x3c\x00" + b"\x00\xff\x2f\x00")
    midi = b"MThd" + struct.pack(">IHHH", 6, 0, 1, 96) + b"MTrk" + struct.pack(">I", len(track)) + track
    assert resources.midi_length(midi) == 2.0


def test_sndinfo_and_decaldef_parsing():
    snd = resources.parse_sndinfo("""
        // comment
        world/quake dsquake
        $random world/spark { spark1 spark2 }
        $limit world/quake 2
        $alias misc/x world/quake
        plats/pt1_stop dspstop
    """)
    assert snd["world/quake"] == {"lump": "DSQUAKE"}
    assert snd["world/spark"] == {"random": ["spark1", "spark2"]}
    assert snd["misc/x"] == {"alias": "world/quake"}
    assert snd["plats/pt1_stop"] == {"lump": "DSPSTOP"}
    decals, groups = resources.parse_decaldef("""
        decal BloodSplat1 { pic BSPLAT1 shade "BloodDefault" x-scale 0.75 y-scale 0.75 randomflipx }
        decal Scorch 2 { pic SCORCH1 shade "00 00 00" add 0.5 }
        decalgroup BloodSplat { BloodSplat1 2 Scorch 1 }
    """)
    assert decals["bloodsplat1"]["pic"] == "BSPLAT1" and decals["bloodsplat1"]["xscale"] == 0.75
    assert decals["scorch"]["id"] == "2" and resources.shade_rgb(decals["scorch"]["shade"]) == (0, 0, 0)
    assert resources.shade_rgb("BloodDefault") == (0x88, 0, 0)
    assert groups["bloodsplat"] == ["BloodSplat1", "Scorch"]


def test_editor_config_parsing_skips_includes():
    cfg = resources.parse_cfg("""
        monsters { title = "Monsters"; width = 20; include("x.cfg", "y");
            3004 { title = "Former Human"; sprite = "POSSA2A8"; class = "ZombieMan"; }
        }
    """)
    out = {}
    resources._walk_things("monsters", cfg["monsters"], {}, out)
    assert out[3004]["title"] == "Former Human" and out[3004]["radius"] == 20
    assert out[3004]["category"] == "monsters" and out[3004]["class"] == "ZombieMan"


def test_colour_buckets():
    red = resources.Picture(1, 1, 0, 0, bytes((200, 20, 20, 255)))
    grey = resources.Picture(1, 1, 0, 0, bytes((120, 120, 120, 255)))
    assert resources.colour_of(red)["hue"] == "red"
    assert resources.colour_of(grey)["hue"] == "grey"


def test_spawn_states_from_zscript():
    zs = b"""
    class TechLamp : Actor
    {
        States
        {
        Spawn:
            TLMP ABCD 4 BRIGHT;
            Loop;
        }
    }
    class DeadThing : Actor { States { Spawn: PLAY W -1; Stop; } }
    class Gone : TechLamp { States { Spawn: Goto Super::Death+4; } }
    """

    class Fake:
        zip_names = ["zscript/actors/doom/x.zs"]

        def pk3_file(self, name):
            return zs

    got = resources.spawn_states(Fake())
    assert got["techlamp"] == {"frames": [["TLMPA", 4], ["TLMPB", 4], ["TLMPC", 4], ["TLMPD", 4]], "loops": True}
    assert got["deadthing"] == {"frames": [["PLAYW", -1]], "loops": False}
    assert "gone" not in got


def test_frame_lumps_prefer_the_front_view():
    class Fake:
        pass

    lumps = ["TROOA1", "TROOA2A8", "TROOB1", "BAR1A0", "SARGB2B8"]
    assert resources.frame_lump(Fake(), "TROOA", lumps) == "TROOA1"
    assert resources.frame_lump(Fake(), "BAR1A", lumps) == "BAR1A0"
    assert resources.frame_lump(Fake(), "TROOC", lumps) is None


def test_favorites_round_trip(tmp_path):
    assert resources.favorites(tmp_path) == {}
    resources.set_favorite(tmp_path, "textures", "MARBFAC2", True)
    resources.set_favorite(tmp_path, "textures", "BROWNWEL", True)
    assert resources.set_favorite(tmp_path, "sounds", "world/quake", True)["sounds"] == ["world/quake"]
    favs = resources.set_favorite(tmp_path, "sounds", "world/quake", False)
    assert favs == {"textures": ["BROWNWEL", "MARBFAC2"]}            # sorted; an empty category goes
    assert resources.favorites(tmp_path) == favs                      # kept on disk
