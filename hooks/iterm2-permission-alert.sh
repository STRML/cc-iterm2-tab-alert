#!/bin/bash
# Fires on Claude Code Notification events.
# Sets orange tab color + iTerm2 user variable for focus-based reset.
# Uses per-session sentinel files keyed by TTY minor device number.

INPUT=$(cat)
MESSAGE=$(python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('message',''))" 2>/dev/null <<< "$INPUT")

if [[ "$MESSAGE" == *"permission"* ]]; then
    # Per-session sentinel file (TTY minor device number = unique per terminal)
    TTY_ID=$(stat -f '%Lr' /dev/tty 2>/dev/null)
    touch "/tmp/claude-alert-${TTY_ID:-tty}"

    # Tag this iTerm2 session so the Python focus-monitor can identify it
    printf '\033]1337;SetUserVar=claude_alert=%s\a' "$(printf '1' | base64)" > /dev/tty

    # Set orange tab color
    printf '\033]6;1;bg;red;brightness;255\a\033]6;1;bg;green;brightness;120\a\033]6;1;bg;blue;brightness;0\a' > /dev/tty

    # Bounce dock icon / flash tab
    printf '\033]1337;RequestAttention=1\a' > /dev/tty
elif [[ "$MESSAGE" == *"waiting"* ]]; then
    printf '\033]1337;RequestAttention=1\a' > /dev/tty
fi

exit 0
