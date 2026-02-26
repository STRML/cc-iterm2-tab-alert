# Claude Code iTerm2 Tab Alert

A [Claude Code plugin](https://docs.anthropic.com/en/docs/claude-code/plugins) that highlights your iTerm2 tab when Claude needs permission. The tab turns orange and bounces the dock icon. The color resets instantly when you focus the tab.

## How it works

Three components:

1. **Notification hook** — When Claude requests permission, sets the tab to orange and tags the session with an iTerm2 user variable.

2. **Reset hook** — Clears the tab color when Claude resumes work (PostToolUse) or you submit a prompt (UserPromptSubmit). Fallback for the focus-based reset.

3. **Focus-based reset** *(optional)* — An iTerm2 Python API script that monitors tab focus events. When you switch to a tab with an active alert, it resets the color immediately via the profile API.

## Requirements

- [iTerm2](https://iterm2.com/) (macOS)
- [Claude Code](https://docs.anthropic.com/en/docs/claude-code)
- iTerm2 Python Runtime (optional, for focus-based reset)

## Install

### As a Claude Code plugin (recommended)

```
/plugin marketplace add STRML/cc-iterm2-tab-alert
/plugin install cc-iterm2-tab-alert
```

Then restart Claude Code. The hooks activate automatically.

For instant focus-based reset, run `/cc-iterm2-tab-alert:setup` in Claude Code.

### AI prompt

Paste this into Claude Code:

```
Install the iTerm2 tab alert plugin:

1. Run: /plugin marketplace add STRML/cc-iterm2-tab-alert
2. Run: /plugin install cc-iterm2-tab-alert
3. Restart Claude Code
4. Run: /cc-iterm2-tab-alert:setup
```

### Manual

1. Copy `hooks/iterm2-permission-alert.sh` and `hooks/iterm2-tab-reset.sh` to `~/.claude/hooks/`

2. Add the hooks from `hooks/hooks.json` to your `~/.claude/settings.json` (replace `${CLAUDE_PLUGIN_ROOT}` with `$HOME/.claude/hooks` in the command paths)

3. *(Optional)* Copy `scripts/claude_tab_reset.py` to `~/Library/Application Support/iTerm2/Scripts/AutoLaunch/`

4. In iTerm2: **Scripts > Manage > Install Python Runtime**, then **Scripts > claude_tab_reset**

## Without the focus-based reset

The Python script is optional. Without it, the tab color still resets — just not until Claude resumes work or you submit your next prompt.

## Customization

### Tab color

Edit `hooks/iterm2-permission-alert.sh`. The format is iTerm2's proprietary OSC escape:

```bash
# RGB components (0-255) — default is orange (255, 120, 0)
printf '\033]6;1;bg;red;brightness;R\a\033]6;1;bg;green;brightness;G\a\033]6;1;bg;blue;brightness;B\a'
```

### Dock bounce

Remove the `RequestAttention` line in the alert script to disable dock icon bouncing.

## Technical details

### Per-session sentinel files

Each Claude session writes its own sentinel file keyed by the TTY minor device number (`stat -f '%Lr' /dev/tty`), so multiple concurrent sessions don't interfere with each other.

### Escape sequences

| Escape | Purpose |
|--------|---------|
| `\033]6;1;bg;red;brightness;N\a` | Set tab color red component |
| `\033]6;1;bg;green;brightness;N\a` | Set tab color green component |
| `\033]6;1;bg;blue;brightness;N\a` | Set tab color blue component |
| `\033]6;1;bg;*;default\a` | Reset tab color to default |
| `\033]1337;RequestAttention=1\a` | Bounce dock icon / flash tab |
| `\033]1337;SetUserVar=NAME=BASE64\a` | Set session user variable |

### Why `set_use_tab_color(False)` instead of `async_inject`

iTerm2's `async_inject` doesn't process proprietary OSC sequences (like tab color). The focus-monitor uses the profile API (`set_use_tab_color(False)`) which directly controls the tab color state.

## License

MIT
