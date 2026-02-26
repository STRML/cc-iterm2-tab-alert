---
description: Set up iTerm2 focus-based tab color reset (one-time)
---

# iTerm2 Tab Alert — Setup

The hooks for tab coloring are already active from the plugin install. This command sets up the **optional but recommended** focus-based auto-reset — the tab color clears the instant you switch to the tab, rather than waiting for the next tool use or prompt.

## Steps

1. **Copy the Python script** to iTerm2's AutoLaunch directory:

```bash
mkdir -p "$HOME/Library/Application Support/iTerm2/Scripts/AutoLaunch"
cp "${CLAUDE_PLUGIN_ROOT}/scripts/claude_tab_reset.py" "$HOME/Library/Application Support/iTerm2/Scripts/AutoLaunch/"
```

2. **Check if iTerm2 Python Runtime is installed.** Tell the user:
   - If not installed: Go to iTerm2 → **Scripts > Manage > Install Python Runtime**
   - Then: **Scripts > claude_tab_reset** to start it (or restart iTerm2 for auto-launch)

3. **Confirm** the setup is complete. The focus-based reset will now auto-launch whenever iTerm2 starts.
