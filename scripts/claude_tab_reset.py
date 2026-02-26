#!/usr/bin/env python3
"""
iTerm2 AutoLaunch script: resets Claude Code permission-alert tab color
when the user focuses the alerting tab.

Uses iTerm2 session user variable (claude_alert) set by the Notification hook
escape sequence, so no TTY path matching is needed.

Install: copy to ~/Library/Application Support/iTerm2/Scripts/AutoLaunch/
Requires: iTerm2 Python Runtime (Scripts > Manage > Install Python Runtime)
"""
import iterm2
import os

ALERT_FILE = "/tmp/claude-alert-tty"


async def main(connection):
    app = await iterm2.async_get_app(connection)
    async with iterm2.FocusMonitor(connection) as monitor:
        while True:
            update = await monitor.async_get_next_update()
            if not update.active_session_changed:
                continue

            session = app.get_session_by_id(
                update.active_session_changed.session_id
            )
            if not session:
                continue

            try:
                alert = await session.async_get_variable("user.claude_alert")
            except Exception:
                continue

            if alert == "1":
                # Reset tab color
                await session.async_inject(b'\033]6;1;bg;*;default\a')
                # Clear the user variable
                await session.async_set_variable("user.claude_alert", "")
                # Remove sentinel file (so hook-based resets no-op)
                try:
                    os.unlink(ALERT_FILE)
                except FileNotFoundError:
                    pass


iterm2.run_forever(main)
