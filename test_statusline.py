"""Self-check for the quota segments: python test_statusline.py"""

import io
import json
import re
import sys
from datetime import datetime, timedelta

from session_monitor.statusline import OLIVE, ORANGE, RED, level_color, main, model_label, rate_limit


def plain(text):
    """Strip ANSI so the assertions read as what lands on screen."""
    return re.sub(r"\033\[[0-9;]*m", "", text or "")


def render(payload):
    """Run main() over a payload and capture the two printed lines."""
    out, stdin, stdout = io.StringIO(), sys.stdin, sys.stdout
    out.reconfigure = lambda **kw: None
    sys.stdin, sys.stdout = io.StringIO(json.dumps(payload)), out
    try:
        main()
    finally:
        sys.stdin, sys.stdout = stdin, stdout
    return out.getvalue()


def limits(**windows):
    return {"rate_limits": windows}


def at(*args):
    return datetime(*args).timestamp()


today = datetime.now().replace(hour=16, minute=40, second=0, microsecond=0)
payload = limits(
    five_hour={"used_percentage": 18.4, "resets_at": today.timestamp()},
    seven_day={"used_percentage": 8.0, "resets_at": at(2026, 9, 5, 12, 30)},
)

# bar, rounded percentage, and a bare clock when the reset lands today
assert plain(rate_limit(payload, "five_hour", "5h")) == "5h ██░░░░░░░░ 18% 🔄 4:40pm"

# a reset on another day carries the date, so "12:30pm" can't be misread as today
assert plain(rate_limit(payload, "seven_day", "7d")) == "7d █░░░░░░░░░ 8% 🔄 Sep 5, 12:30pm"

# a same-day reset an hour from now stays undated
soon = datetime.now() + timedelta(hours=1)
if soon.date() == datetime.now().date():
    assert "🔄 " + soon.strftime("%I:%M%p").lstrip("0").lower() in plain(
        rate_limit(limits(five_hour={"used_percentage": 1, "resets_at": soon.timestamp()}), "five_hour", "5h")
    )

# no quota data -> no segment at all, never a 0% bar reading as "all clear"
assert rate_limit({}, "five_hour", "5h") is None
assert rate_limit(payload, "spend_limit", "$") is None

# unusable resets_at -> keep the bar, drop the clock
for broken in ({"used_percentage": 38, "resets_at": "nonsense"}, {"used_percentage": 38}):
    assert plain(rate_limit(limits(five_hour=broken), "five_hour", "5h")) == "5h ████░░░░░░ 38%"


# display_name already carries the window size in newer builds; don't append twice
big = {"context_window": {"context_window_size": 1_000_000}}
assert model_label({"model": {"display_name": "Opus 5 (1M context)"}, **big}) == "Opus 5 (1M context)"
assert model_label({"model": {"display_name": "Opus 5"}, **big}) == "Opus 5 (1M context)"
assert model_label({"model": {"display_name": "Sonnet 5"}}) == "Sonnet 5"
assert model_label({}) == "Claude"

# quota colour escalates at the thresholds, and the number matches its bar
assert (level_color(0), level_color(59)) == (OLIVE, OLIVE)
assert (level_color(60), level_color(84)) == (ORANGE, ORANGE)
assert (level_color(85), level_color(100)) == (RED, RED)
hot = rate_limit(limits(five_hour={"used_percentage": 91}), "five_hour", "5h")
assert hot.count(RED) == 2, hot          # bar fill + percentage, not just one
assert OLIVE not in hot and ORANGE not in hot

# context gets a bar on the top line, on the same thresholds as the quotas
for pct, colour in ((7, OLIVE), (72, ORANGE), (91, RED)):
    line = render({"context_window": {"used_percentage": pct}}).splitlines()[0]
    assert f"🧠 {colour}" in line and f"{colour}{pct}%" in line, line

# worktree name when inside a linked worktree, a placeholder otherwise
assert "⧉ no worktree" in plain(render({}).splitlines()[1])
assert "⧉ feature-xyz" in plain(render({"workspace": {"git_worktree": "feature-xyz"}}).splitlines()[1])

print("ok")
