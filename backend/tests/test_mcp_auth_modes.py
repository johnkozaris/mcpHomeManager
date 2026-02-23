"""Tests for MCP auth — per-user API key verification."""

from typing import cast
from unittest.mock import AsyncMock

from litestar.types import Scope

from security.mcp_auth import verify_mcp_request


def _make_scope(headers: dict[bytes, bytes] | None = None) -> Scope:
    """Build a minimal ASGI scope with given headers."""
    header_list = list((headers or {}).items())
    return cast(
        Scope,
        {
            "type": "http",
            "headers": header_list,
            "state": {},
        },
    )


class TestMCPAuth:
    async def test_missing_key_rejected(self):
        scope = _make_scope()
        send = AsyncMock()
        result = await verify_mcp_request(scope, AsyncMock(), send)
        assert result is False
        assert send.called

    async def test_invalid_key_rejected(self):
        scope = _make_scope({b"x-api-key": b"invalid-key"})
        # verify_mcp_request will try to look up the key via session_factory
        # Without litestar_app in scope, it should reject
        send = AsyncMock()
        result = await verify_mcp_request(scope, AsyncMock(), send)
        assert result is False

    async def test_rate_limiting_blocks_after_threshold(self):
        """After many failures from the same client, requests are rate-limited."""
        from security.mcp_auth import (
            _auth_blocked_until,
            _auth_failures,
            _record_auth_failure,
        )

        # Clear state
        _auth_failures.clear()
        _auth_blocked_until.clear()

        scope = _make_scope()
        scope["client"] = ("1.2.3.4", 12345)

        # Record 10 failures to trigger block
        for _ in range(10):
            await _record_auth_failure(scope)

        send = AsyncMock()
        result = await verify_mcp_request(scope, AsyncMock(), send)
        assert result is False
        # Should get 429 (rate limited), not 401
        assert send.called

        # Clean up
        _auth_failures.clear()
        _auth_blocked_until.clear()

    async def test_blocked_clients_map_is_capped(self):
        """Blocked-client tracking stays bounded under rotating-client failures."""
        import security.mcp_auth as mcp_auth

        # Clear state and temporarily shrink cap for fast test execution.
        mcp_auth._auth_failures.clear()
        mcp_auth._auth_blocked_until.clear()
        original_cap = mcp_auth._MAX_TRACKED_CLIENTS
        mcp_auth._MAX_TRACKED_CLIENTS = 5
        try:
            # Trigger blocks from 7 different clients (cap is 5).
            for i in range(7):
                scope = _make_scope()
                scope["client"] = (f"10.0.0.{i}", 12345)
                for _ in range(10):
                    await mcp_auth._record_auth_failure(scope)

            assert len(mcp_auth._auth_blocked_until) <= 5
        finally:
            mcp_auth._MAX_TRACKED_CLIENTS = original_cap
            mcp_auth._auth_failures.clear()
            mcp_auth._auth_blocked_until.clear()
