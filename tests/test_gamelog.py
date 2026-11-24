from dms import gamelog, maps

STARTUP = """UZDoom version 5.0.3
Log started: 2026-11-23 14:41:36
LoadActors: Load actor definitions.
Gcacobelisk.wad:ZSCRIPT, line 626: Attempt to redefine 'TURNED'
Gcacobelisk.wad:ZSCRIPT, line 624:  Original definition is here

Execution could not continue.
2 errors, 0 warnings while compiling cacobelisk.wad:ZSCRIPT
"""


def test_a_game_that_stops_on_an_error_is_reported_once(tmp_path):
    (tmp_path / "maps").mkdir()
    info = maps.new(tmp_path, "a")
    log = info.build_dir(tmp_path) / gamelog.LOG
    log.parent.mkdir(parents=True, exist_ok=True)
    seen: dict = {}
    assert gamelog.new_errors(info, tmp_path, seen) is None            # no log yet

    log.write_text("Log started: 1\n[DMS] all well\n", encoding="utf-8")
    assert gamelog.new_errors(info, tmp_path, seen) is None

    log.write_text(STARTUP, encoding="utf-8")
    got = gamelog.new_errors(info, tmp_path, seen)
    assert got and "line 626: Attempt to redefine 'TURNED'" in got[1] and got[-1].startswith("2 errors")
    assert gamelog.new_errors(info, tmp_path, seen) is None            # the same error isn't told twice

    # While playing: a script aborts later in the same log.
    log.write_text(STARTUP + "VM execution aborted: tried to read from address zero.\n", encoding="utf-8")
    assert gamelog.new_errors(info, tmp_path, seen)[-1].startswith("VM execution aborted")

    # A watch that starts later doesn't dig up an old log's errors, but does tell a recent one's.
    import os
    import time

    assert gamelog.new_errors(info, tmp_path, {}, first=True)
    old = time.time() - 3600
    os.utime(log, (old, old))
    assert gamelog.new_errors(info, tmp_path, {}, first=True) is None
