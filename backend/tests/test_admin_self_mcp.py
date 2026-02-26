"""Tests for admin self-MCP global toggle behavior."""

from types import SimpleNamespace
from unittest.mock import MagicMock

from config import settings
from entrypoints.api.admin import AdminController, SelfMcpRequest


class TestAdminSelfMcpToggle:
    async def test_get_self_mcp_reads_settings(self) -> None:
        original = settings.self_mcp_enabled
        try:
            settings.self_mcp_enabled = False
            response = await AdminController.get_self_mcp.fn(SimpleNamespace())
            assert response.enabled is False
        finally:
            settings.self_mcp_enabled = original

    async def test_set_self_mcp_syncs_mcp_factory(self) -> None:
        mock_factory = MagicMock()
        state = SimpleNamespace(mcp_factory=mock_factory)
        original = settings.self_mcp_enabled
        target = not original
        try:
            response = await AdminController.set_self_mcp.fn(
                SimpleNamespace(),
                state=state,
                data=SelfMcpRequest(enabled=target),
            )
            assert response.enabled is target
            assert settings.self_mcp_enabled is target
            mock_factory.sync_meta_tools.assert_called_once_with(target)
        finally:
            settings.self_mcp_enabled = original
