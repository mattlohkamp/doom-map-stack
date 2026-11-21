"""dms setup against tiny local archives (file:// URLs, no network)."""

import hashlib
import json
import zipfile
from pathlib import Path

import pytest

from dms import setup
from dms.setup import SetupError, Tool


def make_zip(path: Path, files: dict[str, bytes]) -> str:
    with zipfile.ZipFile(path, "w") as z:
        for name, data in files.items():
            z.writestr(name, data)
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tool_for(zip_path: Path, sha: str, **kw) -> Tool:
    return Tool(name="thing", version=kw.pop("version", "1"), url=zip_path.as_uri(), sha256=sha, main="thing.exe", **kw)


def test_install_then_skip(tmp_path):
    z = tmp_path / "thing.zip"
    sha = make_zip(z, {"thing.exe": b"x", "data/a.txt": b"a"})
    tools = tmp_path / ".tools"
    main = setup.install(tool_for(z, sha), tools)
    assert main.read_bytes() == b"x"
    assert (tools / "thing" / "data" / "a.txt").exists()
    # Second run is a no-op.
    assert setup.install(tool_for(z, sha), tools) == main


def test_hash_mismatch_stops(tmp_path):
    z = tmp_path / "thing.zip"
    make_zip(z, {"thing.exe": b"x"})
    with pytest.raises(SetupError, match="hash mismatch"):
        setup.install(tool_for(z, "0" * 64), tmp_path / ".tools")
    assert not (tmp_path / ".tools" / "thing").exists()


def test_strip_and_only(tmp_path):
    z = tmp_path / "thing.zip"
    sha = make_zip(z, {"top/thing.exe": b"x", "top/keep.txt": b"k", "top/drop.pdf": b"d"})
    t = tool_for(z, sha, strip="top/", only=["thing.exe", "keep.txt"])
    setup.install(t, tmp_path / ".tools")
    names = sorted(p.name for p in (tmp_path / ".tools" / "thing").iterdir())
    assert names == [setup.MARKER, "keep.txt", "thing.exe"]


def test_unsafe_path_rejected(tmp_path):
    z = tmp_path / "thing.zip"
    sha = make_zip(z, {"thing.exe": b"x", "../evil.txt": b"e"})
    with pytest.raises(SetupError, match="unsafe path"):
        setup.install(tool_for(z, sha), tmp_path / ".tools")
    assert not (tmp_path / ".tools" / "evil.txt").exists()


def test_version_change_needs_upgrade_and_keeps_preserved(tmp_path):
    tools = tmp_path / ".tools"
    z1 = tmp_path / "v1.zip"
    sha1 = make_zip(z1, {"thing.exe": b"v1"})
    setup.install(tool_for(z1, sha1, preserve=["thing.ini", "saves"]), tools)
    (tools / "thing" / "thing.ini").write_text("settings")
    (tools / "thing" / "saves").mkdir()
    (tools / "thing" / "saves" / "s1").write_text("save")

    z2 = tmp_path / "v2.zip"
    sha2 = make_zip(z2, {"thing.exe": b"v2"})
    t2 = tool_for(z2, sha2, version="2", preserve=["thing.ini", "saves"])
    with pytest.raises(SetupError, match="--upgrade thing"):
        setup.install(t2, tools)

    setup.install(t2, tools, upgrade=True)
    d = tools / "thing"
    assert (d / "thing.exe").read_bytes() == b"v2"
    assert (d / "thing.ini").read_text() == "settings"
    assert (d / "saves" / "s1").read_text() == "save"
    assert json.loads((d / setup.MARKER).read_text())["version"] == "2"


def test_run_writes_tools_local_and_respects_unmanaged(tmp_path):
    z = tmp_path / "thing.zip"
    sha = make_zip(z, {"thing.exe": b"x"})
    (tmp_path / "tools.toml").write_text(
        f'[tools.thing]\nversion = "1"\nurl = "{z.as_uri()}"\nsha256 = "{sha}"\nmain = "thing.exe"\n'
        f'[tools.other]\nversion = "1"\nurl = "{z.as_uri()}"\nsha256 = "{sha}"\nmain = "thing.exe"\n'
    )
    (tmp_path / "tools.local.json").write_text(json.dumps({"other": {"managed": False, "path": "C:/elsewhere/other.exe"}}))
    assert setup.run(tmp_path) == 0
    local = json.loads((tmp_path / "tools.local.json").read_text())
    assert local["thing"]["managed"] is True
    assert local["other"] == {"managed": False, "path": "C:/elsewhere/other.exe"}
    assert not (tmp_path / ".tools" / "other").exists()
