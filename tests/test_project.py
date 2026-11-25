import os

import pytest

from dms import maps, project


def _project(path, title="Test episode"):
    path.mkdir(parents=True, exist_ok=True)
    (path / project.PROJECT_FILE).write_text(f'title = "{title}"\n', encoding="utf-8")
    return path


def test_choose_takes_the_given_folder_then_the_environment_then_the_current_folder(tmp_path, monkeypatch):
    tool = tmp_path / "tool"
    tool.mkdir()
    ep = _project(tmp_path / "episode")
    (ep / "maps" / "e1m1").mkdir(parents=True)

    assert project.choose(tool, ep) == ep.resolve()
    assert os.environ[project.ENV] == str(ep.resolve())        # everything after reads it from there
    assert project.choose(tool) == ep.resolve()                # ... including a second look

    monkeypatch.delenv(project.ENV)
    monkeypatch.chdir(ep / "maps" / "e1m1")                    # inside a project: the nearest one above
    assert project.choose(tool) == ep.resolve()

    monkeypatch.delenv(project.ENV)
    monkeypatch.chdir(tmp_path)                                # nowhere in particular: the tool repo
    assert project.choose(tool) == tool.resolve()
    assert project.choose(tool, tool) == tool.resolve()        # the tool repo needs no marker file


def test_choose_refuses_a_folder_that_isnt_a_project(tmp_path):
    with pytest.raises(project.ProjectError):
        project.choose(tmp_path / "tool", tmp_path / "nothing-here")


def test_a_maps_build_output_goes_to_its_own_project(tmp_path, monkeypatch):
    tool = tmp_path / "tool"
    tool.mkdir()
    ep = _project(tmp_path / "episode")
    monkeypatch.setenv(project.ENV, str(ep))
    info = maps.new(tool, "e1m1")                               # created in the current project, not the tool
    assert info.folder == (ep / "maps" / "e1m1").resolve()
    assert info.build_dir(tool) == ep.resolve() / "build" / "e1m1"
    assert [m.name for m in maps.all_maps(tool)] == ["e1m1"]
    assert project.current(tool).title == "Test episode"
    assert maps.resolve(tool, "e1m1").project == ep.resolve()


def test_without_a_project_chosen_the_root_given_is_the_project(tmp_path):
    info = maps.new(tmp_path, "room")
    assert info.build_dir(tmp_path) == tmp_path.resolve() / "build" / "room"
    assert project.path(tmp_path) == tmp_path
