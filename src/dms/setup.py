"""`dms setup`: download the Doom tools pinned in config/tools.toml into .tools/<name>/.

For each tool: download (cached in .tools/downloads/), check the SHA256, extract into a
staging folder, move it into place, and record it in .tools/tools.local.json. Tools already
installed at the pinned version are left alone. `--upgrade <name>` reinstalls one tool,
keeping the files listed in its `preserve` (settings, saves).
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import tomllib
import urllib.request
import zipfile

from dms import paths
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

MARKER = ".dms-installed.json"


class SetupError(Exception):
    pass


@dataclass
class Tool:
    name: str
    version: str
    url: str
    sha256: str
    main: str
    strip: str = ""
    only: list[str] = field(default_factory=list)
    preserve: list[str] = field(default_factory=list)

    @property
    def filename(self) -> str:
        return self.url.rsplit("/", 1)[-1]


def load_tools(path: Path) -> list[Tool]:
    with path.open("rb") as f:
        data = tomllib.load(f)
    tools = []
    for name, spec in data.get("tools", {}).items():
        try:
            tools.append(Tool(name=name, **spec))
        except TypeError as e:
            raise SetupError(f"tools.toml [tools.{name}]: {e}") from None
    return tools


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def download(tool: Tool, downloads: Path) -> Path:
    """Return a hash-checked copy of the tool's download, reusing a cached one if it matches."""
    downloads.mkdir(parents=True, exist_ok=True)
    dest = downloads / f"{tool.name}-{tool.version}-{tool.filename}"
    if dest.exists() and sha256_of(dest) == tool.sha256:
        print(f"    using cached {dest.name}")
        return dest
    part = dest.with_name(dest.name + ".part")
    print(f"    downloading {tool.url}")
    req = urllib.request.Request(tool.url, headers={"User-Agent": "dms-setup"})
    with urllib.request.urlopen(req) as resp, part.open("wb") as out:
        shutil.copyfileobj(resp, out, 1 << 20)
    actual = sha256_of(part)
    if actual != tool.sha256:
        part.unlink()
        raise SetupError(
            f"{tool.name}: hash mismatch for {tool.filename}\n"
            f"    expected {tool.sha256}\n    got      {actual}"
        )
    part.replace(dest)
    return dest


def _target(member: str, tool: Tool) -> PurePosixPath | None:
    """Map an archive path to its path inside the install folder, or None to skip it."""
    name = member.replace("\\", "/")
    if tool.strip:
        if not name.startswith(tool.strip):
            return None
        name = name[len(tool.strip) :]
    if not name or name.endswith("/"):
        return None
    rel = PurePosixPath(name)
    if rel.is_absolute() or ".." in rel.parts:
        raise SetupError(f"{tool.name}: unsafe path in archive: {member}")
    if tool.only and name not in tool.only:
        return None
    return rel


def extract_zip(archive: Path, tool: Tool, dest: Path) -> None:
    with zipfile.ZipFile(archive) as z:
        for info in z.infolist():
            rel = _target(info.filename, tool)
            if rel is None:
                continue
            out = dest.joinpath(*rel.parts)
            out.parent.mkdir(parents=True, exist_ok=True)
            with z.open(info) as src, out.open("wb") as dst:
                shutil.copyfileobj(src, dst)


def extract_7z(archive: Path, tool: Tool, dest: Path) -> None:
    """Extract with Windows' own tar.exe (libarchive reads 7z). It refuses absolute and `..` paths."""
    if tool.strip or tool.only:
        raise SetupError(f"{tool.name}: strip/only are not supported for .7z archives")
    tar = Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32" / "tar.exe"
    if not tar.exists():
        raise SetupError(f"{tar} not found (it ships with Windows 11)")
    dest.mkdir(parents=True, exist_ok=True)
    subprocess.run([str(tar), "-xf", str(archive), "-C", str(dest)], check=True)


def extract(archive: Path, tool: Tool, dest: Path) -> None:
    suffix = archive.suffix.lower()
    if suffix == ".zip":
        extract_zip(archive, tool, dest)
    elif suffix == ".7z":
        extract_7z(archive, tool, dest)
    else:
        raise SetupError(f"{tool.name}: don't know how to extract {archive.name}")


def installed_marker(install_dir: Path) -> dict | None:
    try:
        return json.loads((install_dir / MARKER).read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def install(tool: Tool, tools_dir: Path, upgrade: bool = False) -> Path:
    """Install one tool if needed. Returns the path of its main file."""
    install_dir = tools_dir / tool.name
    main = install_dir / tool.main
    marker = installed_marker(install_dir)
    current = marker is not None and marker.get("sha256") == tool.sha256 and main.exists()

    if current:
        print(f"==> {tool.name} {tool.version}: already installed")
        return main
    if install_dir.exists() and not upgrade:
        found = marker.get("version", "unknown") if marker else "unknown/incomplete"
        raise SetupError(
            f"{tool.name}: .tools/{tool.name} holds version {found}, tools.toml pins {tool.version}.\n"
            f"    Run `.\\scripts\\dms.ps1 setup --upgrade {tool.name}` to replace it (keeps: "
            f"{', '.join(tool.preserve) or 'nothing'})."
        )

    print(f"==> {tool.name} {tool.version}: installing")
    archive = download(tool, tools_dir / "downloads")
    staging = tools_dir / f"{tool.name}.staging"
    if staging.exists():
        shutil.rmtree(staging)
    extract(archive, tool, staging)
    if not (staging / tool.main).exists():
        shutil.rmtree(staging)
        raise SetupError(f"{tool.name}: {tool.main} not found in {archive.name}")

    if install_dir.exists():
        for keep in tool.preserve:
            src = install_dir / keep
            if src.exists():
                print(f"    keeping {keep}")
                dst = staging / keep
                if dst.is_dir():
                    shutil.rmtree(dst)
                elif dst.exists():
                    dst.unlink()
                shutil.move(str(src), str(dst))
        shutil.rmtree(install_dir)

    (staging / MARKER).write_text(
        json.dumps({"version": tool.version, "sha256": tool.sha256, "url": tool.url}, indent=2) + "\n",
        encoding="utf-8",
    )
    staging.rename(install_dir)
    print(f"    {main}")
    return main


def write_local(path: Path, entries: dict[str, dict]) -> None:
    path.write_text(json.dumps(entries, indent=2) + "\n", encoding="utf-8", newline="\n")


def run(root: Path, upgrade: str | None = None) -> int:
    tools = load_tools(paths.tools_toml(root))
    names = {t.name for t in tools}
    if upgrade and upgrade not in names:
        print(f"dms setup: unknown tool {upgrade!r} (tools.toml has: {', '.join(sorted(names))})")
        return 2

    local_path = paths.tools_local(root)
    local_path.parent.mkdir(parents=True, exist_ok=True)
    old = root / "tools.local.json"  # where it was kept before the root was tidied
    if old.exists() and not local_path.exists():
        old.replace(local_path)
    local: dict[str, dict] = {}
    if local_path.exists():
        local = json.loads(local_path.read_text(encoding="utf-8"))

    tools_dir = root / ".tools"
    failed = False
    for tool in tools:
        entry = local.get(tool.name, {})
        if entry.get("managed") is False:
            # Hand-edited to point at an install outside .tools/; leave it alone.
            print(f"==> {tool.name}: using {entry.get('path')} (tools.local.json, not managed)")
            continue
        try:
            main = install(tool, tools_dir, upgrade=(upgrade == tool.name))
        except (SetupError, OSError, subprocess.CalledProcessError) as e:
            print(f"dms setup: {e}")
            failed = True
            continue
        local[tool.name] = {"managed": True, "version": tool.version, "path": str(main)}

    write_local(local_path, local)
    if not failed:
        from dms.configure import configure_all

        mains = {name: Path(e["path"]) for name, e in local.items() if e.get("path")}
        managed = {name for name, e in local.items() if e.get("managed")}
        print("==> configuring")
        configure_all(root, mains, managed)
    return 1 if failed else 0
