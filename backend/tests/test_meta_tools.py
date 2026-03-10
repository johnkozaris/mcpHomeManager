"""Tests for self-MCP meta-tools."""

from mcp.server import FastMCP

from conftest import FakeClientFactory, FakeEncryption, FakeServiceClient


class FakeSessionContext:
    """Minimal async context manager wrapping a fake session."""

    def __init__(self, session):
        self._session = session

    async def __aenter__(self):
        return self._session

    async def __aexit__(self, *args):
        pass


class TestMetaToolsRegistration:
    def test_meta_tools_are_registered(self) -> None:
        """Meta tools should register 12 tools on the FastMCP instance."""
        from entrypoints.mcp.meta_tools import META_TOOL_NAMES, register_meta_tools

        mcp = FastMCP(name="test")
        encryption = FakeEncryption()
        client_factory = FakeClientFactory(FakeServiceClient())

        # We need a ToolRegistry with a mock session_factory
        # Just verify registration doesn't blow up
        class FakeRegistry:
            @property
            def active_tools(self):
                return {}

            @property
            def all_tools(self):
                return {}

        registry = FakeRegistry()

        # Mock session factory
        def session_factory():
            return FakeSessionContext(None)

        register_meta_tools(mcp, session_factory, encryption, client_factory, registry)

        # Verify tools were registered by checking the tool map
        tool_names = {tool.name for tool in mcp._tool_manager.list_tools()}
        expected = set(META_TOOL_NAMES)
        assert expected.issubset(tool_names)
        assert len(tool_names) == len(META_TOOL_NAMES)
