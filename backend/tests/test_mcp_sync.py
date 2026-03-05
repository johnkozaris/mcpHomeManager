"""Tests for dynamic MCP tool sync — MCPServerFactory.sync_tools()."""

import asyncio
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from tests.conftest import (
    FakeEncryption,
    FakeServiceRepository,
    make_service,
)

from domain.entities.service_connection import ServiceType
from domain.entities.tool_definition import ToolDefinition
from domain.ports.service_client import IServiceClient
from entrypoints.mcp.meta_tools import META_TOOL_NAMES
from entrypoints.mcp.server import MCPServerFactory
from services.client_factory import ServiceClientFactory
from services.tool_registry import ActiveTool, ToolRegistry

# --- Helpers ---


class MultiToolClient(IServiceClient):
    """Fake client with configurable tools and real parameter schemas."""

    def __init__(self, tools: list[ToolDefinition]) -> None:
        self._tools = tools

    async def health_check(self) -> bool:
        return True

    async def execute_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> Any:
        return {"result": "ok", "tool": tool_name, "args": arguments}

    def get_tool_definitions(self) -> list[ToolDefinition]:
        return self._tools

    async def close(self) -> None:
        pass


class PerUrlClientFactory(ServiceClientFactory):
    """Factory that maps base_url -> client."""

    def __init__(self) -> None:
        self._by_url: dict[str, IServiceClient] = {}

    def register(self, base_url: str, client: IServiceClient) -> None:
        self._by_url[base_url] = client

    def create(
        self,
        service_type: ServiceType,
        base_url: str,
        api_token: str,
        **kwargs: Any,
    ) -> IServiceClient:
        return self._by_url[base_url]


class EmptyRegistry:
    """Minimal registry shape used for initialize() tests."""

    async def build(self) -> None:
        return None

    @property
    def active_tools(self) -> dict[str, ActiveTool]:
        return {}

    @property
    def active_apps(self) -> dict[str, Any]:
        return {}


FORGEJO_TOOLS = [
    ToolDefinition(
        name="forgejo_list_repos",
        service_type=ServiceType.FORGEJO,
        description="List repositories",
        parameters_schema={
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Max repos to return",
                },
            },
        },
    ),
    ToolDefinition(
        name="forgejo_create_issue",
        service_type=ServiceType.FORGEJO,
        description="Create an issue in a repository",
        parameters_schema={
            "type": "object",
            "properties": {
                "owner": {"type": "string"},
                "repo": {"type": "string"},
                "title": {"type": "string"},
            },
            "required": ["owner", "repo", "title"],
        },
    ),
]


@pytest.fixture(autouse=True)
def _patch_settings():
    with patch("entrypoints.mcp.server.settings") as mock_settings:
        mock_settings.mcp_server_name = "test-mcp"
        mock_settings.self_mcp_enabled = True
        yield


@pytest.fixture
def fake_session_factory():
    return AsyncMock()


@pytest.fixture
def encryption():
    return FakeEncryption()


@pytest.fixture
def service_repo():
    return FakeServiceRepository()


# --- Tests ---


class TestMCPToolSync:
    """sync_tools() keeps FastMCP's tool list in sync with the registry."""

    async def test_startup_registers_tools(
        self,
        service_repo,
        encryption,
        fake_session_factory,
    ) -> None:
        """Tools from enabled services appear in FastMCP."""
        svc = make_service(name="forgejo", base_url="http://forgejo:3000")
        await service_repo.create(svc)

        client = MultiToolClient(FORGEJO_TOOLS)
        factory = PerUrlClientFactory()
        factory.register("http://forgejo:3000", client)

        registry = _make_registry(service_repo, encryption, factory)
        await _populate_registry(registry, service_repo, encryption, factory)

        mcp_factory = MCPServerFactory(
            tool_registry=registry,
            session_factory=fake_session_factory,
        )
        registry.set_on_rebuild(mcp_factory.sync_tools)
        await mcp_factory.sync_tools()

        tools = _tool_names(mcp_factory)
        assert "forgejo_list_repos" in tools
        assert "forgejo_create_issue" in tools

    async def test_schema_correctness(
        self,
        service_repo,
        encryption,
        fake_session_factory,
    ) -> None:
        """FastMCP tools have correct inputSchema, not broken kwargs."""
        svc = make_service(name="forgejo", base_url="http://forgejo:3000")
        await service_repo.create(svc)

        client = MultiToolClient(FORGEJO_TOOLS)
        factory = PerUrlClientFactory()
        factory.register("http://forgejo:3000", client)

        registry = _make_registry(service_repo, encryption, factory)
        await _populate_registry(registry, service_repo, encryption, factory)

        mcp_factory = MCPServerFactory(
            tool_registry=registry,
            session_factory=fake_session_factory,
        )
        registry.set_on_rebuild(mcp_factory.sync_tools)
        await mcp_factory.sync_tools()

        tool = mcp_factory.mcp._tool_manager.get_tool("forgejo_create_issue")
        assert tool is not None
        assert "kwargs" not in tool.parameters.get("properties", {})
        assert tool.parameters.get("required") == ["owner", "repo", "title"]
        assert "owner" in tool.parameters["properties"]

    async def test_add_service_syncs_new_tools(
        self,
        service_repo,
        encryption,
        fake_session_factory,
    ) -> None:
        """New tools from a newly added service appear after rebuild."""
        factory = PerUrlClientFactory()

        registry = _make_registry(service_repo, encryption, factory)
        await _populate_registry(registry, service_repo, encryption, factory)

        mcp_factory = MCPServerFactory(
            tool_registry=registry,
            session_factory=fake_session_factory,
        )
        registry.set_on_rebuild(mcp_factory.sync_tools)
        await mcp_factory.sync_tools()

        assert "forgejo_list_repos" not in _tool_names(mcp_factory)

        # Add a service and rebuild
        svc = make_service(name="forgejo", base_url="http://forgejo:3000")
        await service_repo.create(svc)
        client = MultiToolClient(FORGEJO_TOOLS)
        factory.register("http://forgejo:3000", client)

        await _populate_registry(
            registry,
            service_repo,
            encryption,
            factory,
        )

        tools = _tool_names(mcp_factory)
        assert "forgejo_list_repos" in tools
        assert "forgejo_create_issue" in tools

    async def test_disable_tool_removes_from_fastmcp(
        self,
        service_repo,
        encryption,
        fake_session_factory,
    ) -> None:
        """Disabled tools disappear from FastMCP after rebuild."""
        svc = make_service(name="forgejo", base_url="http://forgejo:3000")
        await service_repo.create(svc)

        tools_with_disabled = [
            FORGEJO_TOOLS[0],  # enabled
            ToolDefinition(
                name="forgejo_create_issue",
                service_type=ServiceType.FORGEJO,
                description="Create an issue",
                parameters_schema={
                    "type": "object",
                    "properties": {},
                },
                is_enabled=False,
            ),
        ]
        client = MultiToolClient(tools_with_disabled)
        factory = PerUrlClientFactory()
        factory.register("http://forgejo:3000", client)

        registry = _make_registry(service_repo, encryption, factory)
        await _populate_registry(registry, service_repo, encryption, factory)

        mcp_factory = MCPServerFactory(
            tool_registry=registry,
            session_factory=fake_session_factory,
        )
        registry.set_on_rebuild(mcp_factory.sync_tools)
        await mcp_factory.sync_tools()

        tools = _tool_names(mcp_factory)
        assert "forgejo_list_repos" in tools
        assert "forgejo_create_issue" not in tools

    async def test_delete_service_removes_tools(
        self,
        service_repo,
        encryption,
        fake_session_factory,
    ) -> None:
        """All tools disappear from FastMCP after service deletion."""
        svc = make_service(name="forgejo", base_url="http://forgejo:3000")
        svc = await service_repo.create(svc)

        client = MultiToolClient(FORGEJO_TOOLS)
        factory = PerUrlClientFactory()
        factory.register("http://forgejo:3000", client)

        registry = _make_registry(service_repo, encryption, factory)
        await _populate_registry(registry, service_repo, encryption, factory)

        mcp_factory = MCPServerFactory(
            tool_registry=registry,
            session_factory=fake_session_factory,
        )
        registry.set_on_rebuild(mcp_factory.sync_tools)
        await mcp_factory.sync_tools()

        assert "forgejo_list_repos" in _tool_names(mcp_factory)

        await service_repo.delete(svc.id)
        await _populate_registry(
            registry,
            service_repo,
            encryption,
            factory,
        )

        tools = _tool_names(mcp_factory)
        assert "forgejo_list_repos" not in tools
        assert "forgejo_create_issue" not in tools

    async def test_meta_tools_not_removed_by_sync(
        self,
        service_repo,
        encryption,
        fake_session_factory,
    ) -> None:
        """sync_tools() never removes meta-tools (mcp_home_*)."""
        factory = PerUrlClientFactory()
        registry = _make_registry(service_repo, encryption, factory)
        await _populate_registry(registry, service_repo, encryption, factory)

        mcp_factory = MCPServerFactory(
            tool_registry=registry,
            session_factory=fake_session_factory,
        )
        registry.set_on_rebuild(mcp_factory.sync_tools)

        async def fake_meta_tool() -> str:
            return "ok"

        mcp_factory.mcp.add_tool(
            fake_meta_tool,
            name="mcp_home_list_services",
            description="List services",
        )

        await mcp_factory.sync_tools()

        assert "mcp_home_list_services" in _tool_names(mcp_factory)

    async def test_on_rebuild_callback_fires(
        self,
        service_repo,
        encryption,
        fake_session_factory,
    ) -> None:
        """The on_rebuild callback fires automatically after build()."""
        factory = PerUrlClientFactory()

        registry = _make_registry(service_repo, encryption, factory)

        callback_called = False

        async def track_callback() -> None:
            nonlocal callback_called
            callback_called = True

        registry.set_on_rebuild(track_callback)

        await _populate_registry(
            registry,
            service_repo,
            encryption,
            factory,
        )

        assert callback_called

    def test_sync_meta_tools_registers_and_removes(
        self,
        service_repo,
        encryption,
        fake_session_factory,
    ) -> None:
        """Global self-MCP toggle can add and remove meta tools at runtime."""
        factory = PerUrlClientFactory()
        registry = _make_registry(service_repo, encryption, factory)
        mcp_factory = MCPServerFactory(
            tool_registry=registry,
            session_factory=fake_session_factory,
            encryption=encryption,
            client_factory=factory,
        )

        mcp_factory.sync_meta_tools(True)
        assert set(META_TOOL_NAMES).issubset(_tool_names(mcp_factory))

        mcp_factory.sync_meta_tools(False)
        assert set(META_TOOL_NAMES).isdisjoint(_tool_names(mcp_factory))

    async def test_initialize_uses_global_self_mcp_toggle(
        self,
        encryption,
        fake_session_factory,
    ) -> None:
        """initialize() delegates self-MCP registration to sync_meta_tools()."""
        from entrypoints.mcp import server as server_module

        server_module.settings.self_mcp_enabled = False
        mcp_factory = MCPServerFactory(
            tool_registry=EmptyRegistry(),  # type: ignore[arg-type]
            session_factory=fake_session_factory,
            encryption=encryption,
            client_factory=PerUrlClientFactory(),
        )

        with patch.object(mcp_factory, "sync_meta_tools") as sync_meta_tools:
            await mcp_factory.initialize()

        sync_meta_tools.assert_called_once_with(False)


# --- Internal helpers ---


def _tool_names(mcp_factory: MCPServerFactory) -> set[str]:
    return {t.name for t in mcp_factory.mcp._tool_manager.list_tools()}


def _make_registry(
    repo: FakeServiceRepository,
    encryption: FakeEncryption,
    client_factory: ServiceClientFactory,
) -> ToolRegistry:
    """Create a ToolRegistry without DB sessions."""
    registry = ToolRegistry.__new__(ToolRegistry)
    registry._session_factory = AsyncMock()
    registry._encryption = encryption
    registry._client_factory = client_factory
    registry._active_tools = {}
    registry._all_tools = {}
    registry._active_apps = {}
    registry._clients = []
    registry._lock = asyncio.Lock()
    registry._on_rebuild = None
    return registry


async def _populate_registry(
    registry: ToolRegistry,
    repo: FakeServiceRepository,
    encryption: FakeEncryption,
    client_factory: ServiceClientFactory,
) -> None:
    """Populate registry from fake repo and fire on_rebuild callback."""
    services = await repo.get_enabled()

    active_tools: dict[str, ActiveTool] = {}
    all_tools: dict[str, ActiveTool] = {}
    clients: list[IServiceClient] = []

    for svc in services:
        token = encryption.decrypt(svc.api_token_encrypted)
        client = client_factory.create(
            svc.service_type,
            svc.base_url,
            token,
        )
        clients.append(client)

        for tool_def in client.get_tool_definitions():
            active = ActiveTool(
                definition=tool_def,
                client=client,
                service_name=svc.name,
            )
            all_tools[tool_def.name] = active
            if tool_def.is_enabled:
                active_tools[tool_def.name] = active

    registry._active_tools = active_tools
    registry._all_tools = all_tools
    registry._clients = clients

    if registry._on_rebuild is not None:
        await registry._on_rebuild()
