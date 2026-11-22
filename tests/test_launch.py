from dms.launch import MESSAGE_MAX, fit_message


def test_fit_message_short_is_unchanged():
    msg = "Reloaded in place (build #2)|Claude, note #1: done"
    assert fit_message(msg) == msg


def test_fit_message_keeps_head_and_newest_lines():
    # An evening of long replies (the restart that hit "User info descriptor too big").
    replies = [f"Claude, note #{i}: " + "x" * 200 for i in range(1, 6)]
    out = fit_message("|".join(["Reloaded in place (build #9)"] + replies))
    lines = out.split("|")
    assert len(out) <= MESSAGE_MAX
    assert lines[0] == "Reloaded in place (build #9)"
    assert lines[-1].startswith("Claude, note #5: ") and lines[-1].endswith("...")
    assert all(len(ln) <= 120 for ln in lines)
    dropped = 5 - (len(lines) - 2)
    assert lines[1] == f"(+{dropped} earlier on the board)"
