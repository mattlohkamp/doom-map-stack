import pytest

from dms import build, maps, udmf, wad


@pytest.fixture
def repo(tmp_path):
    (tmp_path / "maps").mkdir()
    return tmp_path


def test_new_build_pack(repo):
    info = maps.new(repo, "hello-room", kind="test")
    out = build.build(info, repo).wad
    assert out == repo / "build" / "hello-room" / "hello-room.wad"
    kind, lumps = wad.read(out)
    assert [l.name for l in lumps] == ["MAPINFO", "MAP01", "TEXTMAP", "ENDMAP"]
    mapinfo = lumps[0].data.decode()
    assert "nojump" in mapinfo and "nocrouch" in mapinfo and '"Hello room"' in mapinfo
    tm = udmf.parse(lumps[2].data.decode())
    assert tm.globals["namespace"] == "zdoom"
    assert len(tm.sectors) == 1 and len(tm.things) == 1 and tm.things[0]["type"] == 1
    assert info.textmap.read_bytes() == lumps[2].data  # committed TEXTMAP is what got packed


def test_rebuild_is_stable(repo):
    info = maps.new(repo, "a")
    build.build(info, repo)
    first = info.textmap.read_text()
    build.build(info, repo)
    assert info.textmap.read_text() == first


def test_hand_edit_of_generated_textmap_is_protected(repo):
    info = maps.new(repo, "a")
    build.build(info, repo)
    info.textmap.write_text(info.textmap.read_text().replace("lightlevel = 192", "lightlevel = 255"))
    with pytest.raises(build.BuildError, match="edited by hand"):
        build.build(info, repo)
    assert "lightlevel = 255" in info.textmap.read_text()  # untouched
    build.build(info, repo, force=True)
    assert "lightlevel = 192" in info.textmap.read_text()


def test_hand_edited_mode_only_packs(repo):
    info = maps.new(repo, "a")
    build.build(info, repo)
    (info.folder / "map.toml").write_text((info.folder / "map.toml").read_text().replace(
        'source = "generated"', 'source = "hand-edited"'))
    edited = info.textmap.read_text().replace("lightlevel = 192", "lightlevel = 255")
    info.textmap.write_text(edited)
    info = maps.load(info.folder)
    build.build(info, repo)
    assert info.textmap.read_text() == edited
    assert b"lightlevel = 255" in wad.read(info.wad(repo))[1][2].data


def test_saved_edit_wad_blocks_build(repo):
    info = maps.new(repo, "a")
    build.build(info, repo)
    ew = build.pack_edit_wad(info, repo)
    assert not build.edit_wad_changed(info, repo)
    ew.write_bytes(ew.read_bytes() + b"x")  # the editor saved it
    assert build.edit_wad_changed(info, repo)
    with pytest.raises(build.BuildError, match="editor changes"):
        build.build(info, repo)


def test_resolve_by_name_or_folder(repo):
    info = maps.new(repo, "a")
    assert maps.resolve(repo, "a").folder == info.folder
    assert maps.resolve(repo, str(info.folder)).name == "a"
    with pytest.raises(maps.MapError):
        maps.resolve(repo, "nope")
    with pytest.raises(maps.MapError):
        maps.new(repo, "Bad Name")
