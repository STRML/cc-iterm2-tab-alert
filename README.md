# Claude Code iTerm2 Tab Alert

Visual tab highlighting for [Claude Code](https://docs.anthropic.com/en/docs/claude-code) permission requests in iTerm2. When Claude needs approval, the tab turns orange and bounces the dock icon. The color resets instantly when you focus the tab — no need to wait for a hook to fire.

https://github.com/user-attachments/assets/placeholder

## How it works

Three components work together:

1. **Notification hook** (`iterm2-permission-alert.sh`) — When Claude requests permission, sets the tab to orange via iTerm2 escape sequences and tags the session with a user variable.

2. **Reset hook** (`iterm2-tab-reset.sh`) — Clears the tab color when Claude resumes work (PostToolUse) or you submit a prompt (UserPromptSubmit). Acts as a fallback if the focus-based reset didn't fire.

3. **Focus-based reset** (`claude_tab_reset.py`) — An iTerm2 Python API script that monitors tab focus events. When you switch to a tab with an active alert, it resets the color immediately. No polling, no background processes — it uses iTerm2's native `FocusMonitor` API.

## Requirements

- [iTerm2](https://iterm2.com/) (macOS)
- [Claude Code](https://docs.anthropic.com/en/docs/claude-code)
- Python 3 (for the notification hook's JSON parsing)
- iTerm2 Python Runtime (for the focus-based reset — optional but recommended)

## Install

### Option A: Script

```bash
git clone https://github.com/STRML/cc-iterm2-tab-alert.git
cd cc-iterm2-tab-alert
bash install.sh
```

Then:
1. In iTerm2: **Scripts > Manage > Install Python Runtime** (one-time, for focus-based reset)
2. In iTerm2: **Scripts > claude_tab_reset** (to start without restarting iTerm2)
3. In Claude Code: run `/hooks` to reload hooks

### Option B: AI prompt

Paste this into Claude Code:

```
Install the iTerm2 tab alert hooks from https://github.com/STRML/cc-iterm2-tab-alert

1. Clone the repo to a temp directory
2. Copy hooks/iterm2-permission-alert.sh and hooks/iterm2-tab-reset.sh to ~/.claude/hooks/
3. Copy scripts/claude_tab_reset.py to ~/Library/Application Support/iTerm2/Scripts/AutoLaunch/
4. Add the hooks from hooks.json to my ~/.claude/settings.json (merge into existing hooks, don't overwrite)
```

### Option C: Manual

1. Copy `hooks/iterm2-permission-alert.sh` and `hooks/iterm2-tab-reset.sh` to `~/.claude/hooks/`

2. Copy `scripts/claude_tab_reset.py` to `~/Library/Application Support/iTerm2/Scripts/AutoLaunch/`

3. Add the following to your `~/.claude/settings.json` (merge into any existing `hooks` key):

```json
{
  "hooks": {
    "Notification": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash $HOME/.claude/hooks/iterm2-permission-alert.sh"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "bash $HOME/.claude/hooks/iterm2-tab-reset.sh"
          }
        ]
      }
    ],
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash $HOME/.claude/hooks/iterm2-tab-reset.sh"
          }
        ]
      }
    ]
  }
}
```

4. In iTerm2: **Scripts > Manage > Install Python Runtime**
5. Restart iTerm2 (or **Scripts > claude_tab_reset** to start immediately)

## Without the focus-based reset

The Python script is optional. Without it, the tab color still resets — just not until Claude resumes work or you submit your next prompt. The hooks alone handle that case.

## Customization

### Tab color

Edit `hooks/iterm2-permission-alert.sh` line 15. The format is iTerm2's proprietary OSC escape:

```bash
# RGB components (0-255)
printf '\033]6;1;bg;red;brightness;R\a\033]6;1;bg;green;brightness;G\a\033]6;1;bg;blue;brightness;B\a'
```

The default is orange (`255, 120, 0`).

### Dock bounce

Remove or comment out the `RequestAttention` line in the alert script to disable dock icon bouncing.

## How the escape sequences work

| Escape | Purpose |
|--------|---------|
| `\033]6;1;bg;red;brightness;N\a` | Set tab color red component |
| `\033]6;1;bg;green;brightness;N\a` | Set tab color green component |
| `\033]6;1;bg;blue;brightness;N\a` | Set tab color blue component |
| `\033]6;1;bg;*;default\a` | Reset tab color to default |
| `\033]1337;RequestAttention=1\a` | Bounce dock icon / flash tab |
| `\033]1337;SetUserVar=NAME=BASE64\a` | Set session user variable |

## License

MIT
