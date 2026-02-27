# cc-iterm2-tab-alert

Claude Code plugin that turns the active iTerm2 tab orange when Claude requests permissions, then auto-resets the color when the user focuses the tab or takes action.

## Architecture

- **`hooks/hooks.json`** — Plugin hook definitions (Notification, PostToolUse, UserPromptSubmit)
- **`hooks/iterm2-permission-alert.sh`** — Fires on `Notification` events; sets orange tab color and per-session sentinel file in `/tmp/claude-alert-<TTY_ID>`
- **`hooks/iterm2-tab-reset.sh`** — Fires on `PostToolUse` and `UserPromptSubmit`; clears tab color and removes sentinel if present
- **`scripts/claude_tab_reset.py`** — iTerm2 AutoLaunch Python script; monitors focus changes and auto-resets tab color when the alerting session is focused
- **`commands/setup.md`** — Slash command (`/setup`) that guides one-time focus-reset setup

## Key Design Decisions

- **Per-session sentinel files** keyed by TTY minor device number (`stat -f '%Lr' /dev/tty`) — allows multiple concurrent Claude sessions without cross-contamination
- **`PostToolUse` hook fires on every tool** (empty matcher `""`) — intentional; the sentinel guard (`[ -f "$SENTINEL" ] || exit 0`) makes it cheap when no alert is pending
- **Tab color reset via iTerm2 profile API** (`set_use_tab_color=False`) — `async_inject` does NOT process iTerm2's proprietary tab color OSC sequences
- **`iterm2.run_forever`** — auto-restarts the focus monitor on connection loss

## Running Tests

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/python3 -m pytest
```

The test suite mocks the `iterm2` module (only available inside iTerm2's Python runtime) and tests `main()` directly as an async function.

## Testing Manually

1. Trigger a permission request in Claude Code (e.g., ask it to run a bash command)
2. Verify the iTerm2 tab turns orange
3. Take action (approve/deny) or submit a prompt — tab should reset
4. With focus-reset script installed: switch away and back to the tab — should reset on focus

## iTerm2 Python Runtime

The `claude_tab_reset.py` script requires the iTerm2 Python Runtime:
- Install via: **iTerm2 → Scripts > Manage > Install Python Runtime**
- Copy script to: `~/Library/Application Support/iTerm2/Scripts/AutoLaunch/`
