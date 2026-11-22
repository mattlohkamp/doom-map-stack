from dms import movement
from dms.validate import validate
from dms.gen import MapBuilder


def box(m, gid, x, y, w, h, around, facing_out=False, **sector):
    """A sector inside `around`, joined by two-sided lines (edges 0-3: west, north, east, south);
    returns (sector, line indices). facing_out: the lines' front sides face `around`, as a door's
    or lift's use lines do (the player uses them from the front)."""
    s = m.sector(gid, **sector)
    pts = [(x, y), (x, y + h), (x + w, y + h), (x + w, y)]
    lines = []
    for i, (a, b) in enumerate(zip(pts, pts[1:] + pts[:1])):
        lines.append(m.two_sided(b, a, around, s, f"{gid}.{i}") if facing_out
                     else m.two_sided(a, b, s, around, f"{gid}.{i}"))
    return s, lines


def warnings(res):
    return [str(i) for i in res.issues]


def test_hello_room_is_all_reachable():
    m = MapBuilder()
    room = m.room("room", 0, 0, 512, 512, light=192, special=72)
    m.player_start(256, 128)
    box(m, "platform_nw", 64, 320, 128, 128, room, floor=16)
    m.thing(2011, 128, 400, "stimpack")
    m.thing(2001, 416, 384, "shotgun")
    res = movement.check(m.textmap())
    assert res.unreachable == set() and res.issues == []
    assert "no exit in the map" in res.report


def test_too_high_low_ceiling_and_narrow():
    m = MapBuilder()
    room = m.room("room", 0, 0, 1024, 512)
    m.player_start(64, 64)
    high, _ = box(m, "ledge", 64, 320, 128, 128, room, floor=25)          # one unit too high
    low, _ = box(m, "crawl", 320, 320, 128, 128, room, ceiling=55)         # one unit too low
    narrow, _ = box(m, "slot", 576, 320, 31, 128, room, floor=0)           # 31 wide...
    m.thing(2001, 128, 384, "ledge.shotgun")
    res = movement.check(m.textmap())
    # The slot is still reachable through its 128-long sides; only its 31-wide ends are too narrow.
    assert res.unreachable == {high.index, low.index}
    w = warnings(res)
    assert any("shotgun can't be reached" in x for x in w)
    assert any("(ledge)" in x and "unreachable" in x for x in w)


def test_split_lines_count_as_one_gap():
    # Room b north of room a, joined by a 40-wide opening made of two 20-long lines.
    m = MapBuilder()
    a = m.sector("a")
    b = m.sector("b")
    m.player_start(128, 128)
    m.wall((0, 0), (0, 256), a, "a.w")
    m.wall((256, 256), (256, 0), a, "a.e")
    m.wall((256, 0), (0, 0), a, "a.s")
    m.wall((0, 256), (108, 256), a, "a.n1")
    m.two_sided((108, 256), (128, 256), a, b, "gap.1")
    m.two_sided((128, 256), (148, 256), a, b, "gap.2")
    m.wall((148, 256), (256, 256), a, "a.n2")
    m.wall((0, 256), (0, 512), b, "b.w")
    m.wall((0, 512), (256, 512), b, "b.n")
    m.wall((256, 512), (256, 256), b, "b.e")
    m.wall((108, 256), (0, 256), b, "b.s1")
    m.wall((256, 256), (148, 256), b, "b.s2")
    res = movement.check(m.textmap())
    assert res.unreachable == set()


def _door(m, room, gid, x, y, *, special=12, lock=0, tag=0):
    """A closed door sector (ceiling at floor height) between room and a closet behind it."""
    door, lines = box(m, gid, x, y, 64, 16, room, facing_out=True, ceiling=0)
    tm_line = m.linedefs[lines[3]]  # the south edge, facing the room
    tm_line["special"] = special
    tm_line["playeruse"] = True
    if lock:
        tm_line["arg3"] = lock
    if tag:
        tm_line["arg0"] = tag
    return door


def test_doors_and_locked_doors():
    m = MapBuilder()
    room = m.room("room", 0, 0, 512, 512)
    m.player_start(64, 64)
    plain = _door(m, room, "door", 64, 256)
    locked = _door(m, room, "locked", 320, 256, special=13, lock=2)  # needs the blue keycard
    tm = m.textmap()
    res = movement.check(tm)
    assert plain.index in res.reachable and locked.index not in res.reachable
    assert any("locked door (lock 2)" in x for x in warnings(res))

    m.thing(5, 256, 64, "blue_card")  # put the key in the room
    res = movement.check(m.textmap())
    assert locked.index in res.reachable and res.issues == []


def test_lift_and_softlock_with_exit():
    m = MapBuilder()
    room = m.room("room", 0, 0, 1024, 512, ceiling=256)
    m.player_start(64, 64)
    # A ledge 128 up (x 512-768, y 256-384), and a lift (x 448-512, y 256-320) against its west
    # side: Plat_DownWaitUpStay on tag 7, used from the room. Lines go clockwise around each
    # sector so that sector is on their front (right) side, except the lift's use line.
    ledge = m.sector("ledge", floor=128, ceiling=256)
    lift = m.sector("lift", floor=128, ceiling=256)
    m.sectors[lift.index]["id"] = 7
    use = m.linedefs[m.two_sided((448, 320), (448, 256), room, lift, "lift.w")]  # front: the room
    use["special"], use["arg0"], use["playeruse"] = 62, 7, True
    m.two_sided((448, 320), (512, 320), lift, room, "lift.n")
    m.two_sided((512, 256), (448, 256), lift, room, "lift.s")
    m.two_sided((512, 320), (512, 256), lift, ledge, "lift.e")
    m.two_sided((512, 320), (512, 384), ledge, room, "ledge.w")
    m.two_sided((512, 384), (768, 384), ledge, room, "ledge.n")
    m.two_sided((768, 384), (768, 256), ledge, room, "ledge.e")
    exit_line = m.linedefs[m.two_sided((768, 256), (512, 256), ledge, room, "ledge.s")]  # used from the ledge
    exit_line["special"], exit_line["playeruse"] = 243, True
    # A pit you can drop into but not climb out of.
    pit, _ = box(m, "pit", 64, 320, 128, 128, room, floor=-64, ceiling=256)
    res = movement.check(m.textmap())
    assert ledge.index in res.reachable and lift.index in res.reachable
    assert res.softlocks == {pit.index}
    assert any("soft-lock" in x and "(pit)" in x for x in warnings(res))
    assert "one-way drops" in res.report


def test_test_maps_are_valid():
    """The maps above are only evidence if they're sound maps; check the trickier ones."""
    import inspect

    for build_map in (_door_map, _lift_map):
        errors = [str(i) for i in validate(build_map()) if i.severity == "error"]
        assert errors == [], (inspect.getsource(build_map).splitlines()[0], errors)


def _door_map():
    m = MapBuilder()
    room = m.room("room", 0, 0, 512, 512)
    m.player_start(64, 64)
    _door(m, room, "door", 64, 256)
    return m.textmap()


def _lift_map():
    m = MapBuilder()
    room = m.room("room", 0, 0, 1024, 512, ceiling=256)
    m.player_start(64, 64)
    ledge = m.sector("ledge", floor=128, ceiling=256)
    lift = m.sector("lift", floor=128, ceiling=256)
    m.sectors[lift.index]["id"] = 7
    use = m.linedefs[m.two_sided((448, 320), (448, 256), room, lift, "lift.w")]
    use["special"], use["arg0"], use["playeruse"] = 62, 7, True
    m.two_sided((448, 320), (512, 320), lift, room, "lift.n")
    m.two_sided((512, 256), (448, 256), lift, room, "lift.s")
    m.two_sided((512, 320), (512, 256), lift, ledge, "lift.e")
    m.two_sided((512, 320), (512, 384), ledge, room, "ledge.w")
    m.two_sided((512, 384), (768, 384), ledge, room, "ledge.n")
    m.two_sided((768, 384), (768, 256), ledge, room, "ledge.e")
    m.two_sided((768, 256), (512, 256), ledge, room, "ledge.s")
    return m.textmap()


def _niche_switch_map(with_special=True):
    """Room a with a switch at the back of a niche too low to step into (32 high, 8 deep) in its north
    wall; it lowers sector c (east of a, 64 up: out of reach until it's lowered)."""
    m = MapBuilder()
    a = m.sector("a")
    niche = m.sector("niche", floor=16, ceiling=48)
    c = m.sector("c", floor=64)
    m.sectors[c.index]["id"] = 1
    m.player_start(128, 128)
    m.wall((0, 0), (0, 256), a, "a.w")
    m.wall((0, 256), (112, 256), a, "a.n1")
    m.two_sided((112, 256), (144, 256), a, niche, "niche.mouth")
    m.wall((144, 256), (256, 256), a, "a.n2")
    m.two_sided((256, 256), (256, 0), a, c, "a.c")
    m.wall((256, 0), (0, 0), a, "a.s")
    m.wall((112, 256), (112, 264), niche, "niche.w")
    switch = m.wall((112, 264), (144, 264), niche, "niche.switch")
    m.wall((144, 264), (144, 256), niche, "niche.e")
    if with_special:
        m.linedefs[switch].fields.update(special=20, arg0=1, arg1=8, arg2=64, playeruse=True)
    m.wall((256, 256), (384, 256), c, "c.n")
    m.wall((384, 256), (384, 0), c, "c.e")
    m.wall((384, 0), (256, 0), c, "c.s")
    return m.textmap(), niche.index, c.index


def test_switch_in_a_niche_is_used_from_in_front_of_it():
    tm, niche, c = _niche_switch_map()
    res = movement.check(tm)
    assert res.unreachable == {niche}
    tm, niche, c = _niche_switch_map(with_special=False)
    assert movement.check(tm).unreachable == {niche, c}


def test_lower_by_value_goes_past_its_neighbours_and_solid_blocks_are_walls():
    # Room a; north of it a platform p (tag 1) whose switch lowers it 128, past every neighbour, to
    # room b's level; b is 128 down, beyond p. A solid block s (floor = ceiling) sits east of p.
    m = MapBuilder()
    a = m.sector("a")
    p = m.sector("p")
    m.sectors[p.index]["id"] = 1
    b = m.sector("b", floor=-128, ceiling=0)
    s = m.sector("s", floor=0, ceiling=0)
    m.player_start(32, 32)
    m.wall((0, 0), (0, 64), a, "a.w")
    m.two_sided((64, 64), (0, 64), p, a, "a.p")
    m.wall((64, 64), (64, 0), a, "a.e")
    m.wall((64, 0), (0, 0), a, "a.s")
    m.wall((0, 64), (0, 128), p, "p.w")
    sw = m.two_sided((0, 128), (64, 128), p, b, "p.b")
    m.linedefs[sw].fields.update(special=20, arg0=1, arg1=8, arg2=128, playeruse=True)
    m.two_sided((64, 128), (64, 64), p, s, "p.s")
    m.wall((64, 128), (128, 128), s, "s.n")
    m.wall((128, 128), (128, 64), s, "s.e")
    m.wall((128, 64), (64, 64), s, "s.s")
    m.wall((0, 128), (0, 192), b, "b.w")
    m.wall((0, 192), (64, 192), b, "b.n")
    m.wall((64, 192), (64, 128), b, "b.e")
    res = movement.check(m.textmap())
    assert res.unreachable == set()


def test_monolith_top_is_scenery_but_a_low_corridor_is_still_reported():
    # Room a (0-256 square) with a monolith in the middle: a top 128 up with 48 under the ceiling.
    # North of a, a corridor at a's level whose ceiling is too low (40): still unreachable.
    m = MapBuilder()
    a = m.sector("a", floor=0, ceiling=176)
    top = m.sector("top", floor=128, ceiling=176)
    low = m.sector("low", floor=0, ceiling=40)
    m.player_start(32, 32)
    m.wall((0, 0), (0, 256), a, "a.w")
    m.two_sided((0, 256), (256, 256), a, low, "a.n")
    m.wall((256, 256), (256, 0), a, "a.e")
    m.wall((256, 0), (0, 0), a, "a.s")
    for name, p, q in (("w", (96, 96), (96, 160)), ("n", (96, 160), (160, 160)),
                       ("e", (160, 160), (160, 96)), ("s", (160, 96), (96, 96))):
        m.two_sided(p, q, top, a, f"top.{name}")
    m.wall((0, 256), (0, 320), low, "low.w")
    m.wall((0, 320), (256, 320), low, "low.n")
    m.wall((256, 320), (256, 256), low, "low.e")
    assert movement.check(m.textmap()).unreachable == {low.index}


def test_a_sector_marked_scenery_is_not_reported():
    # Room a with a 16-wide recess (too narrow to enter) in its west wall, marked user_scenery.
    m = MapBuilder()
    a = m.sector("a")
    slot = m.sector("slot")
    m.sectors[slot.index]["user_scenery"] = True
    m.player_start(64, 64)
    m.wall((0, 0), (0, 56), a, "a.w1")
    m.two_sided((0, 56), (0, 72), a, slot, "slot.mouth")
    m.wall((0, 72), (0, 128), a, "a.w2")
    m.wall((0, 128), (128, 128), a, "a.n")
    m.wall((128, 128), (128, 0), a, "a.e")
    m.wall((128, 0), (0, 0), a, "a.s")
    m.wall((0, 56), (-8, 56), slot, "slot.s")
    m.wall((-8, 56), (-8, 72), slot, "slot.back")
    m.wall((-8, 72), (0, 72), slot, "slot.n")
    assert movement.check(m.textmap()).unreachable == set()
    del m.sectors[slot.index].fields["user_scenery"]
    assert movement.check(m.textmap()).unreachable == {slot.index}
