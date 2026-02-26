#!/bin/bash
# Clears the iTerm2 orange tab color set by iterm2-permission-alert.sh.
# Only fires when the alert was actually set (sentinel file exists).
# Writes directly to /dev/tty — hooks have terminal access, Bash tool does not.

[ -f /tmp/claude-alert-tty ] || exit 0

# Reset tab color to default
printf '\033]6;1;bg;*;default\a' > /dev/tty

# Clear the iTerm2 user variable (so focus-monitor ignores this session)
printf '\033]1337;SetUserVar=claude_alert=\a' > /dev/tty

rm -f /tmp/claude-alert-tty
exit 0
