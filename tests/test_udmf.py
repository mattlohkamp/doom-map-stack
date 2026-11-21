import pytest

from dms import udmf, wad
from dms.gen import MapBuilder

SAMPLE = """\
// a comment
namespace = "zdoom";
/* block
   comment */
thing { x = 32.0; y = -16.5; type = 1; skill1 = true; user_gid = "start"; }
vertex // 0
{
X = 0.000;
y = 1e3;
}
linedef { v1 = 0; v2 = 0x1F; sidefront = 017; comment = "say \\"hi\\" \\\\ ok"; somefuturefield = ident; }
"""


def test_parse_types_and_case():
    tm = udmf.parse(SAMPLE)
    assert tm.globals == {"namespace": "zdoom"}
    t = tm.things[0]
    assert t["x"] == 32.0 and isinstance(t["x"], float)
    assert t["type"] == 1 and isinstance(t["type"], int)
    assert t["skill1"] is True
    assert tm.vertices[0]["x"] == 0.0  # field names are case-insensitive
    ld = tm.linedefs[0]
    assert ld["v2"] == 31 and ld["sidefront"] == 15  # hex and octal
    assert ld["comment"] == 'say "hi" \\ ok'
    assert ld["somefuturefield"] == "ident"


def test_round_trip_keeps_everything():
    tm = udmf.parse(SAMPLE)
    again = udmf.parse(udmf.dump(tm))
    assert udmf.same(tm, again)
    assert isinstance(again.vertices[0]["y"], float)


def test_float_format_is_valid_udmf():
    assert udmf.format_value(64.0) == "64.000"
    assert udmf.format_value(0.5) == "0.5"
    assert "." in udmf.format_value(1e-20)
    with pytest.raises(udmf.UdmfError):
        udmf.format_value(float("inf"))


def test_syntax_error_reports_line():
    with pytest.raises(udmf.UdmfError, match="line 2"):
        udmf.parse('namespace = "zdoom";\nthing { x = ; }')


def test_wad_round_trip(tmp_path):
    lumps = [wad.Lump("MAP01"), wad.Lump("TEXTMAP", b"abc"), wad.Lump("ENDMAP")]
    p = tmp_path / "t.wad"
    wad.write(p, lumps)
    kind, back = wad.read(p)
    assert kind == "PWAD"
    assert [(l.name, l.data) for l in back] == [("MAP01", b""), ("TEXTMAP", b"abc"), ("ENDMAP", b"")]


def test_room_is_closed_and_faces_inward():
    m = MapBuilder()
    m.room("r", 0, 0, 512, 256)
    tm = m.textmap()
    verts = [(v["x"], v["y"]) for v in tm.vertices]
    assert len(verts) == 4 and len(tm.linedefs) == 4  # corners are shared
    # Each vertex is the end of exactly one line and the start of exactly one (closed loop).
    starts = sorted(l["v1"] for l in tm.linedefs)
    ends = sorted(l["v2"] for l in tm.linedefs)
    assert starts == ends == [0, 1, 2, 3]
    # Front side (right of v1->v2) faces the room's centre.
    for l in tm.linedefs:
        (x1, y1), (x2, y2) = verts[l["v1"]], verts[l["v2"]]
        dx, dy = x2 - x1, y2 - y1
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        right = (dy, -dx)
        to_centre = (256 - mx, 128 - my)
        assert right[0] * to_centre[0] + right[1] * to_centre[1] > 0
        assert l["blocking"] is True
    gids = [b["user_gid"] for b in tm.blocks if b.kind != "vertex"]
    assert len(gids) == len(set(gids))


def test_duplicate_gid_rejected():
    m = MapBuilder()
    m.room("r", 0, 0, 64, 64)
    with pytest.raises(ValueError, match="duplicate gid"):
        m.room("r", 100, 0, 64, 64)
