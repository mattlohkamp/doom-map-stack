import struct
from pathlib import Path

from dms import catalog, udmf, wad
from dms.gen import MapBuilder
from dms.validate import sector_at, validate

FIXTURES = Path(__file__).parent / "fixtures"


def fake_iwad(path: Path) -> Path:
    def texture1(entries):
        head = struct.pack("<i", len(entries))
        body = b""
        offsets = []
        base = 4 + 4 * len(entries)
        for name, w, h in entries:
            offsets.append(base + len(body))
            body += name.encode().ljust(8, b"\0") + struct.pack("<ihhih", 0, w, h, 0, 0)
        return head + struct.pack(f"<{len(entries)}i", *offsets) + body

    lumps = [
        wad.Lump("TEXTURE1", texture1([("GRAY1", 64, 128), ("STARTAN2", 128, 128)])),
        wad.Lump("F_START"), wad.Lump("F1_START"),
        wad.Lump("FLOOR4_8", b"\0" * 4096), wad.Lump("CEIL3_5", b"\0" * 4096), wad.Lump("F_SKY1", b"\0" * 4096),
        wad.Lump("F1_END"), wad.Lump("F_END"),
    ]
    wad.write(path, lumps, kind="IWAD")
    return path


def test_catalog_from_iwad_and_round_trip(tmp_path):
    cat = catalog.from_iwad(fake_iwad(tmp_path / "iwad.wad"))
    assert cat.textures == {"GRAY1": (64, 128), "STARTAN2": (128, 128)}
    assert cat.flats == {"FLOOR4_8", "CEIL3_5", "F_SKY1"}
    catalog.write(cat, tmp_path)
    back = catalog.load(tmp_path)
    assert back.textures == cat.textures and back.flats == cat.flats
    assert back.source.startswith("iwad.wad sha256 ")


def cat():
    return catalog.Catalog(textures={"GRAY1": (64, 128)}, flats={"FLOOR4_8", "CEIL3_5"})


def errors(tm, c=None):
    return [str(i) for i in validate(tm, c) if i.severity == "error"]


def test_generated_room_is_clean():
    m = MapBuilder()
    m.room("room", 0, 0, 512, 512)
    m.player_start(256, 256)
    assert validate(m.textmap(), cat()) == []


def test_platform_inside_room_is_clean():
    # A raised sector inside a room, joined by two-sided lines (hello-room's live-reload test).
    m = MapBuilder()
    room = m.room("room", 0, 0, 512, 512)
    plat = m.sector("platform", floor=24)
    sw, nw, ne, se = (320, 320), (320, 448), (448, 448), (448, 320)
    for name, a, b in (("w", sw, nw), ("n", nw, ne), ("e", ne, se), ("s", se, sw)):
        m.two_sided(a, b, plat, room, f"platform.edge_{name}")
    m.player_start(128, 128)
    tm = m.textmap()
    assert validate(tm, cat()) == []
    assert sector_at(tm, 384, 384) == 1 and sector_at(tm, 128, 128) == 0
    edge = tm.linedefs[-1]
    assert edge["twosided"] is True and "blocking" not in edge.fields
    assert tm.sidedefs[edge["sideback"]]["texturebottom"] != "-"


def test_missing_player_start_and_bad_texture():
    m = MapBuilder()
    m.room("room", 0, 0, 512, 512, floor_tex="NOPE")
    errs = errors(m.textmap(), cat())
    assert any("no player 1 start" in e for e in errs)
    assert any("'NOPE' isn't in the flat catalog" in e for e in errs)


def test_open_sector_and_thing_outside():
    m = MapBuilder()
    s = m.sector("room")
    m.wall((0, 0), (0, 256), s, "w1")
    m.wall((0, 256), (256, 256), s, "w2")  # two walls only: not closed
    m.player_start(1000, 1000)
    errs = errors(m.textmap())
    assert any("isn't closed" in e for e in errs)
    assert any("outside every sector" in e for e in errs)


def test_crossing_lines():
    m = MapBuilder()
    m.room("a", 0, 0, 256, 256)
    m.room("b", 128, 128, 256, 256)  # overlaps a: walls cross
    m.player_start(64, 64)
    assert any("crosses" in e for e in errors(m.textmap()))


def test_sector_at():
    m = MapBuilder()
    m.room("a", 0, 0, 256, 256)
    m.room("b", 512, 0, 256, 256)
    tm = m.textmap()
    assert sector_at(tm, 100, 100) == 0
    assert sector_at(tm, 600, 100) == 1
    assert sector_at(tm, 400, 100) is None


def test_mapper_edited_fixture():
    """The hello room after the M1 editor test: split, pasted and divided lines, test light values."""
    tm = udmf.parse((FIXTURES / "hello-room-udb-edited.textmap").read_text(encoding="utf-8"))
    errs = errors(tm)
    assert any("light level 99999 is outside 0-255" in e for e in errs)
    assert any("no front side" in e for e in errs)  # the lone pasted line
    assert not any("isn't closed" in e for e in errs)  # both halves of the divided room are closed


def test_render_and_diff(tmp_path):
    from dms import render

    m = MapBuilder()
    m.room("room", 0, 0, 512, 512)
    m.player_start(256, 256)
    before = m.textmap()
    png = render.render(before, tmp_path / "render.png", title="t")
    assert png.exists() and "sectors (1)" in png.with_suffix(".txt").read_text()
    assert render.render_diff(before, before, tmp_path / "diff.png") is False

    edited = udmf.parse((FIXTURES / "hello-room-udb-edited.textmap").read_text(encoding="utf-8"))
    assert render.render_diff(before, edited, tmp_path / "diff.png") is True
    txt = (tmp_path / "diff.txt").read_text()
    assert "lightlevel 192 -> 99999" in txt and "removed line" in txt and "added line" in txt
    for name in ("diff.png", "diff-before.png", "diff-after.png"):
        assert (tmp_path / name).exists()
    assert render.render_diff(edited, edited, tmp_path / "diff.png") is False
    assert not any((tmp_path / n).exists() for n in ("diff.png", "diff-before.png", "diff-after.png"))


def _pixel_colors(path):
    from PIL import Image

    return {c for _n, c in Image.open(path).convert("RGB").getcolors(maxcolors=1 << 24)}


def test_diff_marks_added_green_and_removed_red(tmp_path):
    from dms import render

    def room_with(extra: bool):
        m = MapBuilder()
        room = m.room("room", 0, 0, 512, 512)
        m.player_start(256, 128)
        if extra:
            box = m.sector("box", floor=16)
            pts = [(64, 320), (64, 448), (192, 448), (192, 320)]
            for i, (a, b) in enumerate(zip(pts, pts[1:] + pts[:1])):
                m.two_sided(a, b, box, room, f"box.{i}")
        return m.textmap()

    plain, boxed = room_with(False), room_with(True)
    render.render_diff(plain, boxed, tmp_path / "add.png")
    assert render.ADDED in _pixel_colors(tmp_path / "add.png")
    assert render.REMOVED not in _pixel_colors(tmp_path / "add.png")
    render.render_diff(boxed, plain, tmp_path / "rm.png")
    assert render.REMOVED in _pixel_colors(tmp_path / "rm.png")       # the ghost of the box
    assert render.REMOVED in _pixel_colors(tmp_path / "rm-before.png")
    assert render.REMOVED not in _pixel_colors(tmp_path / "rm-after.png")
