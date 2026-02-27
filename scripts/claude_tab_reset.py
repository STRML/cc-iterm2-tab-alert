#!/usr/bin/env python3
"""
iTerm2 AutoLaunch script: resets Claude Code permission-alert tab color
when the user focuses the alerting tab.

Uses iTerm2 session user variable (claude_alert) set by the Notification hook.
Resets via profile API (set_use_tab_color=False) since async_inject doesn't
process iTerm2's proprietary tab color OSC sequences.

Setup: Scripts > Manage > Install Python Runtime (one-time)
"""
import asyncio
import iterm2
import os
import glob

ALERT_PATTERN = "/tmp/claude-alert-*"


async def main(connection):
    app = await iterm2.async_get_app(connection)
    # Outer loop: re-enter FocusMonitor if it drops (run_forever does NOT
    # restart main on return — it only keeps the process alive for RPC).
    while True:
        try:
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
                        if alert != "1":
                            continue

                        # Reset tab color via profile API
                        profile = iterm2.LocalWriteOnlyProfile()
                        profile.set_use_tab_color(False)
                        await session.async_set_profile_properties(profile)

                        # Clear the user variable
                        await session.async_set_variable("user.claude_alert", "")

                        # Clean up sentinel files
                        for f in glob.glob(ALERT_PATTERN):
                            try:
                                os.unlink(f)
                            except FileNotFoundError:
                                pass
                    except Exception:
                        continue  # Session gone or API error — skip, don't crash
        except Exception:
            await asyncio.sleep(1)  # Brief pause before re-entering FocusMonitor


iterm2.run_forever(main)
