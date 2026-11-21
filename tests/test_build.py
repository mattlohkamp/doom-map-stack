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
    _, lumps = wad.read(ew)  # the mapper changes a light level and saves
    lumps[2] = wad.Lump("TEXTMAP", lumps[2].data.replace(b"lightlevel = 192", b"lightlevel = 200"))
    wad.write(ew, lumps)
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


def test_resaved_edit_wad_with_same_map_is_not_a_change(repo):
    info = maps.new(repo, "a")
    build.build(info, repo)
    ew = build.pack_edit_wad(info, repo)
    # The editor re-saves: same map data (no hash header comment), plus a nodes lump.
    kind, lumps = wad.read(ew)
    body = info.textmap.read_text().split("\n", 1)[1]
    lumps[2] = wad.Lump("TEXTMAP", body.encode())
    lumps.insert(3, wad.Lump("ZNODES", b"nodes"))
    wad.write(ew, lumps)
    assert not build.edit_wad_changed(info, repo)


def test_build_refreshes_unedited_edit_wad(repo):
    info = maps.new(repo, "a")
    build.build(info, repo)
    ew = build.pack_edit_wad(info, repo)
    info.generator.write_text(info.generator.read_text().replace("light=192", "light=160"))
    build.build(info, repo)
    _, lumps = wad.read(ew)
    assert b"lightlevel = 160" in lumps[2].data  # the open editor would reload this
    assert not build.edit_wad_changed(info, repo)


def test_force_build_discards_saved_edit_wad(repo):
    info = maps.new(repo, "a")
    build.build(info, repo)
    ew = build.pack_edit_wad(info, repo)
    _, lumps = wad.read(ew)  # the mapper saves a change by accident
    lumps[2] = wad.Lump("TEXTMAP", lumps[2].data.replace(b"lightlevel = 192", b"lightlevel = 200"))
    wad.write(ew, lumps)
    build.build(info, repo, force=True)
    assert b"lightlevel = 192" in wad.read(ew)[1][2].data
    assert not build.edit_wad_changed(info, repo)


def test_wad_write_overwrites_in_place_when_replace_is_refused(tmp_path, monkeypatch):
    # The editor holds its open WAD so it can't be replaced, but it can be written to.
    path = tmp_path / "edit.wad"
    wad.write(path, [wad.Lump("A", b"a much longer first version")])

    def refuse(self, target):
        raise PermissionError(5, "Access is denied")

    monkeypatch.setattr(type(path), "replace", refuse)
    wad.write(path, [wad.Lump("B", b"short")])
    assert wad.read(path)[1] == [wad.Lump("B", b"short")]
    assert not (tmp_path / "edit.wad.tmp").exists()


def test_edit_does_not_open_a_second_editor(repo, monkeypatch, capsys):
    import json
    import os

    from dms import launch

    info = maps.new(repo, "a")
    build.build(info, repo)
    opened = []
    monkeypatch.setattr(launch, "open_editor", lambda *a, **k: opened.append(a) or 0)
    monkeypatch.setattr(launch, "focus_process_window", lambda pid: True)
    state = info.build_dir(repo) / "editor-state.json"
    state.write_text(json.dumps({"open": True, "pid": os.getpid()}))  # this process counts as alive
    assert launch.edit(repo, info) == 0 and opened == []
    assert "already open in the editor" in capsys.readouterr().out
    state.write_text(json.dumps({"open": True, "pid": 999999999}))  # a crashed editor: open again
    launch.edit(repo, info)
    assert len(opened) == 1
