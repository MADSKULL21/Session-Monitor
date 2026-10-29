# session-monitor

Monitors token usage in session and auto resumes the task when session limit resets.

## Status line

Renders Claude Code's session state as a two-line status bar:

```
🤖 Opus 5 (1M context) | 🧠 ███░░░░░░░ 27% | 5h ██░░░░░░░░ 18% 🔄 4:40pm | 7d █░░░░░░░░░ 8% 🔄 Sep 5, 12:30pm   [ ·  · ]
📁 session-monitor | ⧉ no worktree | ⎇ main | ⚡ xhigh | ⏱ 7m 0s | $1.12                                        [ ==== ]
```

🧠 is this session's context window. `5h` and `7d` are the account-wide rolling
quotas that `/usage` reports, with their local reset times. A quota segment is
omitted entirely until Claude Code has loaded usage data, rather than showing 0%.
Reset times carry a date when they don't land today. ⧉ shows the linked git
worktree's name, or `no worktree` in the main working tree. Bars and percentages
turn orange at 60% and red at 85%. `BAR_WIDTH` sets the bar size.
The robot is drawn flush right using the `COLUMNS` width Claude Code passes in, and
is dropped when the terminal is too narrow to fit it; `ROBOT` holds its two rows.

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
