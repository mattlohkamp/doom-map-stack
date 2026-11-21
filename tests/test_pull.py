import json
from pathlib import Path

import pytest

from dms import build, maps, overrides, pull, udmf, wad

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def repo(tmp_path):
    (tmp_path / "maps").mkdir()
    return tmp_path


def _edit(info, repo, change):
    """Pack edit.wad, let `change` edit its TEXTMAP (as the mapper would in the editor), save it."""
    ew = build.pack_edit_wad(info, repo)
    _, lumps = wad.read(ew)
    i = wad.find(lumps, "TEXTMAP")
    tm = udmf.parse(lumps[i].data.decode("utf-8"))
    change(tm)
    lumps[i] = wad.Lump("TEXTMAP", udmf.dump(tm).encode("utf-8"))
    wad.write(ew, lumps)
    return ew


def _one(tm, kind, gid):
    return next(b for b in tm.of(kind) if b.get("user_gid") == gid)


def test_property_tweaks_and_comments_round_trip(repo):
    info = maps.new(repo, "a")
    build.build(info, repo)

    def change(tm):
        _one(tm, "sector", "room")["lightlevel"] = 200
        _one(tm, "sector", "room")["comment"] = "make this room taller"
        _one(tm, "thing", "player1_start")["angle"] = 180
        _one(tm, "sidedef", "room.wall_n.front")["offsetx"] = 16

    _edit(info, repo, change)
    assert pull.pull(info, repo) == 0

    data = overrides.load(info)
    assert data == {"sector": {"room": {"lightlevel": 200}}, "thing": {"player1_start": {"angle": 180}},
                    "sidedef": {"room.wall_n.front": {"offsetx": 16}}}
    tm = udmf.parse(info.textmap.read_text())
    assert _one(tm, "sector", "room")["lightlevel"] == 200 and "comment" not in _one(tm, "sector", "room").fields
    assert not build.edit_wad_changed(info, repo)  # edit.wad refreshed from the new TEXTMAP
    notes = (info.folder / "notes.md").read_text()
    assert "sector room around (" in notes and "make this room taller" in notes
    assert list((info.build_dir(repo) / "pulled").glob("edit-*.wad"))

    # The tweaks survive a rebuild from map.py.
    build.build(info, repo)
    assert _one(udmf.parse(info.textmap.read_text()), "thing", "player1_start")["angle"] == 180


def test_value_reset_to_its_default_is_a_tweak(repo):
    info = maps.new(repo, "a")
    build.build(info, repo)
    # The editor leaves out fields that hold the UDMF default (light 160).
    _edit(info, repo, lambda tm: _one(tm, "sector", "room").fields.pop("lightlevel"))
    pull.pull(info, repo)
    assert overrides.load(info) == {"sector": {"room": {"lightlevel": 160}}}


def test_structural_changes_wait_for_ported(repo, capsys):
    info = maps.new(repo, "hello-room")
    info.generator.write_text(
        "def build(m):\n"
        "    m.room('room', 0, 0, 512, 512, floor=0, ceiling=128, light=192)\n"
        "    m.player_start(256, 256, angle=90)\n")
    build.build(info, repo)
    # The editor save from the user_gid test: split, copied and divided lines, light 99999.
    edited = (FIXTURES / "hello-room-udb-edited.textmap").read_text(encoding="utf-8")
    _edit(info, repo, lambda tm: tm.blocks.__setitem__(slice(None), udmf.parse(edited).blocks))

    assert pull.pull(info, repo) == 1
    report = (info.build_dir(repo) / "pull.txt").read_text()
    assert "split or copied" in report and "sector room is now 2 sectors" in report
    assert not overrides.path(info).exists() and build.edit_wad_changed(info, repo)  # nothing written

    pull.pull(info, repo, ported=True)  # map.py wasn't changed, so the check lists what's left
    assert not build.edit_wad_changed(info, repo)
    assert "still differs" in capsys.readouterr().out


def test_hand_edited_map_takes_the_save(repo):
    info = maps.new(repo, "a")
    build.build(info, repo)
    (info.folder / "map.toml").write_text((info.folder / "map.toml").read_text().replace(
        'source = "generated"', 'source = "hand-edited"'))
    info = maps.load(info.folder)

    def change(tm):
        _one(tm, "sector", "room")["lightlevel"] = 99
        _one(tm, "sector", "room")["comment"] = "darker?"
        tm.blocks.append(udmf.Block("thing", {"x": 64.0, "y": 64.0, "type": 2011}))

    _edit(info, repo, change)
    assert pull.pull(info, repo) == 0
    tm = udmf.parse(info.textmap.read_text())
    assert _one(tm, "sector", "room")["lightlevel"] == 99 and len(tm.things) == 2
    assert "comment" not in _one(tm, "sector", "room").fields
    assert not overrides.path(info).exists()


def test_refuses_while_the_editor_has_unsaved_changes(repo):
    info = maps.new(repo, "a")
    build.build(info, repo)
    _edit(info, repo, lambda tm: _one(tm, "sector", "room").__setitem__("lightlevel", 200))
    (info.build_dir(repo) / "editor-state.json").write_text(json.dumps({"open": True, "unsaved_changes": True}))
    with pytest.raises(pull.PullError, match="unsaved changes"):
        pull.pull(info, repo)


def test_nothing_to_pull(repo, capsys):
    info = maps.new(repo, "a")
    build.build(info, repo)
    build.pack_edit_wad(info, repo)
    assert pull.pull(info, repo) == 0
    assert "nothing to pull" in capsys.readouterr().out


def test_overrides_file_round_trip_and_missing_gid():
    data = {"sector": {'odd "gid"\\x': {"lightlevel": 200, "texturefloor": "FLAT 1", "secret": True}},
            "thing": {"p": {"x": 64.5}}}
    text = overrides.dumps(data)
    import tomllib
    assert tomllib.loads(text) == data
    from dms.gen import MapBuilder
    m = MapBuilder()
    m.room("room", 0, 0, 64, 64)
    tm = m.textmap()
    warnings = overrides.apply(tm, {"sector": {"room": {"lightlevel": 7}, "gone": {"lightlevel": 1}}})
    assert tm.sectors[0]["lightlevel"] == 7 and len(warnings) == 1 and "'gone'" in warnings[0]


def test_elements_without_gid_match_by_position():
    # What the check after `--ported` sees: the mapper's gid-less shotgun and box edges, now made by
    # map.py with gids, at exactly the same places. Same elements: no changes.
    from dms.gen import MapBuilder

    m = MapBuilder()
    room = m.room("room", 0, 0, 512, 512)
    m.player_start(256, 128)
    m.thing(2001, 416, 384, "room.shotgun")
    box = m.sector("box", floor=16)
    pts = [(64, 320), (64, 448), (192, 448), (192, 320)]
    for i, (a, c) in enumerate(zip(pts, pts[1:] + pts[:1])):
        m.two_sided(a, c, box, room, f"box.{i}")
    ported = m.textmap()

    saved = udmf.parse(udmf.dump(ported))
    saved.things[1].fields.pop("user_gid")
    for blk in saved.linedefs[4:] + saved.sidedefs[4:]:
        blk.fields.pop("user_gid")
    assert pull.compare(ported, saved).empty

    saved.things[1]["angle"] = 45  # a tweak on a position-matched thing is still a tweak
    ch = pull.compare(ported, saved)
    assert ch.tweaks == {("thing", "room.shotgun"): {"angle": 45}} and not ch.structural
