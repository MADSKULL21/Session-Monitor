# session-monitor

Monitors token usage in session and auto resumes the task when session limit resets.

## Status line

Renders Claude Code's session state as a two-line status bar:

```
[Opus 5 (1M context)] | ⚡ xhigh | 📁 session-monitor | ⎇ main
5h ██░░░░░░░░ 18% ↻ 4:40pm | 7d █░░░░░░░░░ 8% ↻ Sep 5, 12:30pm | context: 7% | ⏱ 7m 0s | $1.12
```

`5h` and `7d` are the account-wide rolling quotas that `/usage` reports, with their
local reset times; `context:` is this session's context window. A quota segment is
omitted entirely until Claude Code has loaded usage data, rather than showing 0%.
Reset times carry a date when they don't land today. Bars and the context figure
turn orange at 60% and red at 85%. `BAR_WIDTH` sets the bar size.

Run `python test_statusline.py` to check the quota segments.

### Install

Requires Python 3.9+ and Claude Code.

```
git clone <this repo>
cd session-monitor
python install.py
```

Then restart Claude Code.

The installer writes a `statusLine` entry into `~/.claude/settings.json`, backing up
any existing file to `settings.json.bak` first. All other settings are preserved.

| Command | Effect |
| --- | --- |
| `python install.py` | install for the current user (`~/.claude/settings.json`) |
| `python install.py --project` | install for this repo only (`./.claude/settings.json`) |
| `python install.py --uninstall` | remove the `statusLine` entry |

Paths are resolved from the repo's location and the interpreter you run the
installer with, so no editing is needed after cloning.

## Auto-resume

Not implemented yet.
