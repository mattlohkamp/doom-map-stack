"""Where things are.

The repo root holds only `Start Session.cmd` and the documents; everything else is in folders:
`config/` (dms.toml, tools.toml), `scripts/` (dms.ps1, bootstrap.ps1), `launchers/` (the other
.cmd files and the agent launchers), `src/` (this package and its pyproject.toml), and the
git-ignored `.tools/` (downloads, the Python environment, tools.local.json) and `build/`.
"""

import os
from pathlib import Path

DMS_PS1 = Path("scripts") / "dms.ps1"
LAUNCHERS = Path("launchers")


def repo_root() -> Path:
    """The repo root: DMS_ROOT (set by dms.ps1), else the nearest parent holding config/tools.toml."""
    env = os.environ.get("DMS_ROOT")
    if env:
        return Path(env).resolve()
    here = Path.cwd().resolve()
    for p in (here, *here.parents):
        if tools_toml(p).exists():
            return p
    raise SystemExit("dms: can't find the repo root (no config\\tools.toml); "
                     "run it as .\\scripts\\dms.ps1 from the repo.")


def dms_toml(root: Path) -> Path:
    """Committed project settings."""
    return root / "config" / "dms.toml"


def tools_toml(root: Path) -> Path:
    """The pinned Doom tools."""
    return root / "config" / "tools.toml"


def tools_local(root: Path) -> Path:
    """What `dms setup` installed on this machine (git-ignored, with the tools themselves)."""
    return root / ".tools" / "tools.local.json"