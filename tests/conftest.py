import pytest


@pytest.fixture(autouse=True)
def _no_project_from_outside(monkeypatch):
    """Each test picks its own project (a tmp root passed in); none leaks in from the shell or from an
    earlier test that ran the command line (cli.main sets DMS_PROJECT: docs/projects.md)."""
    monkeypatch.delenv("DMS_PROJECT", raising=False)
