"""Claude Code status line renderer.

Reads the session JSON that Claude Code pipes to stdin and prints two lines:

    <robot> Opus 5 (1M context) | <brain> <bar> 36% | 5h <bar> 18% 4:40pm | 7d <bar> 8% Sep 5, 12:30pm
    <dir> | <worktree> | <branch> | xhigh | 49m 53s | $25.58

Wired up via settings.json -> statusLine.
"""

import json
import os
import subprocess
import sys
import time
from datetime import datetime

# 256-colour palette, matched to the reference screenshot.
TEAL = "\033[38;5;80m"
ORANGE = "\033[38;5;179m"
GREY = "\033[38;5;242m"
WHITE = "\033[38;5;253m"
OLIVE = "\033[38;5;142m"
DARK = "\033[38;5;238m"
GREEN = "\033[38;5;114m"
RED = "\033[38;5;203m"
RESET = "\033[0m"

BAR_WIDTH = 10
GIT_CACHE_TTL = 5.0


def git_branch(cwd, session_id):
    """Current branch name, cached per session so we don't shell out every tick."""
    cache = os.path.join(
        os.environ.get("TEMP", os.path.expanduser("~")),
        f"claude-statusline-git-{session_id}.txt",
    )
    try:
        if time.time() - os.path.getmtime(cache) < GIT_CACHE_TTL:
            with open(cache, encoding="utf-8") as fh:
                return fh.read().strip() or None
    except OSError:
        pass

    try:
        branch = subprocess.run(
            ["git", "-C", cwd, "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            timeout=2,
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        branch = ""

    try:
        with open(cache, "w", encoding="utf-8") as fh:
            fh.write(branch)
    except OSError:
        pass
    return branch or None


def model_label(data):
    """e.g. "Opus 5 (1M context)" — suffix added only if the name lacks it.

    Newer Claude Code builds already put the window size in display_name.
    """
    name = data.get("model", {}).get("display_name") or "Claude"
    size = data.get("context_window", {}).get("context_window_size") or 0
    if size >= 1_000_000 and "1m" not in name.lower():
        name += " (1M context)"
    return name


def level_color(pct):
    """Olive, then orange from 60%, then red from 85% — quota running out."""
    if pct >= 85:
        return RED
    if pct >= 60:
        return ORANGE
    return OLIVE


def bar(pct):
    filled = round(BAR_WIDTH * pct / 100)
    return f"{level_color(pct)}{'█' * filled}{DARK}{'░' * (BAR_WIDTH - filled)}{RESET}"


def gauge(label, pct):
    """Label, bar and percentage, the number coloured to match its bar."""
    return f"{label} {bar(pct)} {level_color(pct)}{round(pct)}%{RESET}"


def reset_at(ts):
    """Local clock for a reset epoch, dated when it isn't today.

    The 5h window routinely crosses midnight and the 7d one always lands on
    another day, so a bare "4:40am" would be ambiguous.
    """
    when = datetime.fromtimestamp(ts)
    clock = when.strftime("%I:%M%p").lstrip("0").lower()  # %-I is glibc-only
    if when.date() == datetime.now().date():
        return clock
    return f"{when.strftime('%b')} {when.day}, {clock}"


def rate_limit(data, window, label):
    """Quota bar + reset time for one rolling window, or None if unavailable.

    These are account-wide (what /usage reports), so they read the same in
    every session. Claude Code omits rate_limits until usage data loads, and
    an absent quota must render nothing — a 0% bar would read as "all clear".
    """
    limit = data.get("rate_limits", {}).get(window)
    if not limit:
        return None

    out = gauge(label, limit.get("used_percentage") or 0)
    try:
        return f"{out} {GREY}🔄 {reset_at(limit['resets_at'])}{RESET}"
    except (KeyError, TypeError, ValueError, OSError, OverflowError):
        return out


def duration(ms):
    total = int(ms // 1000)
    hours, rem = divmod(total, 3600)
    minutes, seconds = divmod(rem, 60)
    if hours:
        return f"{hours}h {minutes}m {seconds}s"
    return f"{minutes}m {seconds}s"


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return

    cwd = data.get("workspace", {}).get("current_dir") or data.get("cwd") or "."
    sep = f" {GREY}|{RESET} "

    ctx = data.get("context_window", {}).get("used_percentage") or 0
    top = [
        f"🤖 {TEAL}{model_label(data)}{RESET}",
        gauge("🧠", ctx),
        rate_limit(data, "five_hour", "5h"),
        rate_limit(data, "seven_day", "7d"),
    ]
    top = [seg for seg in top if seg]

    # git_worktree is set for any linked worktree, not just --worktree sessions.
    worktree = data.get("workspace", {}).get("git_worktree")
    bottom = [
        f"📁 {WHITE}{os.path.basename(cwd.rstrip('/\\')) or cwd}{RESET}",
        f"⧉ {WHITE}{worktree}{RESET}" if worktree else f"⧉ {GREY}no worktree{RESET}",
    ]
    branch = git_branch(cwd, data.get("session_id", "default"))
    if branch:
        bottom.append(f"⎇ {WHITE}{branch}{RESET}")

    cost = data.get("cost", {})
    bottom += [
        f"{ORANGE}⚡ {data.get('effort', {}).get('level', 'medium')}{RESET}",
        f"⏱ {WHITE}{duration(cost.get('total_duration_ms', 0))}{RESET}",
        f"{GREEN}${cost.get('total_cost_usd', 0):.2f}{RESET}",
    ]

    print(sep.join(top))
    print(sep.join(bottom))


if __name__ == "__main__":
    main()
