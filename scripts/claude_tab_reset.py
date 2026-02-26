#!/usr/bin/env python3
"""
iTerm2 AutoLaunch script: resets Claude Code permission-alert tab color
when the user focuses the alerting tab.

Uses iTerm2 session user variable (claude_alert) set by the Notification hook.
Resets via profile API (set_use_tab_color=False) since async_inject doesn't
process iTerm2's proprietary tab color OSC sequences.

Setup: Scripts > Manage > Install Python Runtime (one-time)
"""
import iterm2
import os
import glob

ALERT_PATTERN = "/tmp/claude-alert-*"


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
                # Reset tab color via profile API
                profile = iterm2.LocalWriteOnlyProfile()
                profile.set_use_tab_color(False)
                await session.async_set_profile_properties(profile)
                # Clear the user variable
                await session.async_set_variable("user.claude_alert", "")
                # Clean up any sentinel files for this session
                for f in glob.glob(ALERT_PATTERN):
                    try:
                        os.unlink(f)
                    except FileNotFoundError:
                        pass


iterm2.run_forever(main)
