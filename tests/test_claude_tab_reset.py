"""
Tests for scripts/claude_tab_reset.py

The iterm2 module is only available inside iTerm2's Python runtime, so we
mock the entire module before importing our script.  All async tests stop
the infinite monitoring loop via asyncio.CancelledError, which is a
BaseException and is therefore NOT caught by the script's `except Exception`
handlers.
"""
import asyncio
import importlib.util
import pathlib
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Bootstrap: inject a mock iterm2 module BEFORE the script is imported.
# iterm2.run_forever() is called at module level, so this must happen first.
# ---------------------------------------------------------------------------
_mock_iterm2 = MagicMock()
_mock_iterm2.run_forever = MagicMock()  # no-op — prevents starting an event loop
sys.modules["iterm2"] = _mock_iterm2

_script = pathlib.Path(__file__).parent.parent / "scripts" / "claude_tab_reset.py"
_spec = importlib.util.spec_from_file_location("claude_tab_reset", _script)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
main = _mod.main


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _focus_update(session_id="test-session"):
    """Focus update with an active session change."""
    update = MagicMock()
    update.active_session_changed.session_id = session_id
    return update


def _no_change_update():
    """Focus update with no active session change."""
    update = MagicMock()
    update.active_session_changed = None
    return update


def _mock_session(alert="1"):
    """iTerm2 session mock with a configurable claude_alert variable."""
    session = AsyncMock()
    session.async_get_variable = AsyncMock(return_value=alert)
    session.async_set_profile_properties = AsyncMock()
    session.async_set_variable = AsyncMock()
    return session


def _monitor_ctx(*updates):
    """
    FocusMonitor async context manager that yields the given updates in order,
    then raises CancelledError to terminate the monitoring loop.
    """
    monitor = AsyncMock()
    monitor.async_get_next_update = AsyncMock(
        side_effect=[*updates, asyncio.CancelledError()]
    )
    ctx = MagicMock()
    ctx.__aenter__ = AsyncMock(return_value=monitor)
    ctx.__aexit__ = AsyncMock(return_value=False)
    return ctx


def _setup_iterm2(ctx, app):
    """Wire the mock iterm2 module for a single test."""
    _mock_iterm2.reset_mock()
    _mock_iterm2.run_forever = MagicMock()
    _mock_iterm2.LocalWriteOnlyProfile = MagicMock()
    _mock_iterm2.FocusMonitor = MagicMock(return_value=ctx)
    _mock_iterm2.async_get_app = AsyncMock(return_value=app)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_resets_tab_when_alert_is_set():
    """When claude_alert == '1', the profile is reset and the variable is cleared."""
    session = _mock_session(alert="1")
    app = MagicMock()
    app.get_session_by_id = MagicMock(return_value=session)
    _setup_iterm2(_monitor_ctx(_focus_update()), app)

    with pytest.raises(asyncio.CancelledError):
        await main(MagicMock())

    session.async_set_profile_properties.assert_called_once()
    session.async_set_variable.assert_called_once_with("user.claude_alert", "")


@pytest.mark.asyncio
async def test_skips_reset_when_alert_not_set():
    """When claude_alert is not '1', no profile reset is performed."""
    session = _mock_session(alert="")
    app = MagicMock()
    app.get_session_by_id = MagicMock(return_value=session)
    _setup_iterm2(_monitor_ctx(_focus_update()), app)

    with pytest.raises(asyncio.CancelledError):
        await main(MagicMock())

    session.async_set_profile_properties.assert_not_called()
    session.async_set_variable.assert_not_called()


@pytest.mark.asyncio
async def test_skips_when_session_not_found():
    """When get_session_by_id returns None, no API calls are made."""
    app = MagicMock()
    app.get_session_by_id = MagicMock(return_value=None)
    _setup_iterm2(_monitor_ctx(_focus_update()), app)

    with pytest.raises(asyncio.CancelledError):
        await main(MagicMock())

    # No session object to assert on — just confirm no crash and clean exit.


@pytest.mark.asyncio
async def test_skips_non_session_change_updates():
    """Focus updates with no active_session_changed are ignored."""
    session = _mock_session(alert="1")
    app = MagicMock()
    app.get_session_by_id = MagicMock(return_value=session)
    _setup_iterm2(_monitor_ctx(_no_change_update()), app)

    with pytest.raises(asyncio.CancelledError):
        await main(MagicMock())

    session.async_set_profile_properties.assert_not_called()


@pytest.mark.asyncio
async def test_cleans_up_sentinel_files(tmp_path):
    """Sentinel files matching /tmp/claude-alert-* are removed on reset."""
    sentinel = tmp_path / "claude-alert-42"
    sentinel.touch()
    assert sentinel.exists()

    session = _mock_session(alert="1")
    app = MagicMock()
    app.get_session_by_id = MagicMock(return_value=session)
    _setup_iterm2(_monitor_ctx(_focus_update()), app)

    with patch("glob.glob", return_value=[str(sentinel)]):
        with pytest.raises(asyncio.CancelledError):
            await main(MagicMock())

    assert not sentinel.exists()


@pytest.mark.asyncio
async def test_continues_when_session_api_raises():
    """An exception reading/writing session variables is swallowed; the loop keeps going."""
    session = AsyncMock()
    session.async_get_variable = AsyncMock(side_effect=Exception("session gone"))
    app = MagicMock()
    app.get_session_by_id = MagicMock(return_value=session)
    # Two updates: the first raises via the session API, the second stops the loop.
    _setup_iterm2(_monitor_ctx(_focus_update(), _focus_update()), app)

    with pytest.raises(asyncio.CancelledError):
        await main(MagicMock())

    # async_get_variable was called twice (once per update), proving the loop continued.
    assert session.async_get_variable.call_count == 2


@pytest.mark.asyncio
async def test_monitor_restarts_after_exception():
    """
    REGRESSION: run_forever does NOT restart main() on return.

    Previously, any exception from async_get_next_update() caused `break`,
    which exited main() silently and permanently stopped focus monitoring.

    The outer retry loop must re-enter FocusMonitor after any exception so
    that monitoring resumes rather than dying quietly.
    """
    app = MagicMock()
    app.get_session_by_id = MagicMock(return_value=None)
    _mock_iterm2.reset_mock()
    _mock_iterm2.run_forever = MagicMock()
    _mock_iterm2.async_get_app = AsyncMock(return_value=app)

    call_count = 0

    def _make_ctx(*_args):
        nonlocal call_count
        call_count += 1
        ctx = MagicMock()
        if call_count == 1:
            # First FocusMonitor: raises immediately (simulates a transient drop)
            ctx.__aenter__ = AsyncMock(side_effect=Exception("transient iterm2 error"))
            ctx.__aexit__ = AsyncMock(return_value=False)
        else:
            # Second FocusMonitor: stop the test cleanly
            monitor = AsyncMock()
            monitor.async_get_next_update = AsyncMock(side_effect=asyncio.CancelledError())
            ctx.__aenter__ = AsyncMock(return_value=monitor)
            ctx.__aexit__ = AsyncMock(return_value=False)
        return ctx

    _mock_iterm2.FocusMonitor = MagicMock(side_effect=_make_ctx)

    with patch("asyncio.sleep", new_callable=AsyncMock):
        with pytest.raises(asyncio.CancelledError):
            await main(MagicMock())

    assert call_count == 2, (
        f"FocusMonitor entered {call_count} time(s); "
        "expected 2 — outer loop must restart after exception, not exit silently"
    )
