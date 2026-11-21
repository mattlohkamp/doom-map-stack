"""Where things are."""

import os
from pathlib import Path


def repo_root() -> Path:
    """The repo root: DMS_ROOT (set by dms.ps1), else the nearest parent holding tools.toml."""
    env = os.environ.get("DMS_ROOT")
    if env:
        return Path(env).resolve()
    here = Path.cwd().resolve()
    for p in (here, *here.parents):
        if (p / "tools.toml").exists():
            return p
    raise SystemExit("dms: can't find the repo root (no tools.toml); run it as .\\dms.ps1 from the repo.")
