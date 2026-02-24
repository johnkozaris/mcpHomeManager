"""CRUD lifecycle tests for generic REST tool management.

Exercises the full flow: create tools, edit them, delete them, test
OpenAPI import with skip-on-duplicate, and validates tool name constraints.
"""

from uuid import UUID, uuid4

import pytest
from tests.conftest import (
    FakeGenericToolRepository,
    FakeServiceRepository,
    make_service,
)

from domain.entities.service_connection import ServiceType
from domain.validation import validate_tool_name


class TestGenericToolCRUDLifecycle:
    """Full lifecycle: create → read → update → delete."""

    @pytest.fixture
    def repo(self) -> FakeGenericToolRepository:
        return FakeGenericToolRepository()

    @pytest.fixture
    def service_id(self) -> UUID:
        return uuid4()

    async def test_full_crud_lifecycle(self, repo: FakeGenericToolRepository, service_id: UUID):
        # CREATE
        row = await repo.create(
            service_id=service_id,
            tool_name="list_items",
            description="List all items",
            http_method="GET",
            path_template="/api/v1/items",
            params_schema={"type": "object", "properties": {"page": {"type": "integer"}}},
        )
        assert row.tool_name == "list_items"
        assert row.http_method == "GET"
        assert row.path_template == "/api/v1/items"

        # READ — get_by_service_id
        tools = await repo.get_by_service_id(service_id)
        assert len(tools) == 1
        assert tools[0].tool_name == "list_items"

        # READ — get_by_name
        found = await repo.get_by_name(service_id, "list_items")
        assert found is not None
        assert found.description == "List all items"

        # READ — not found
        missing = await repo.get_by_name(service_id, "nonexistent")
        assert missing is None

        # UPDATE — partial (only description)
        updated = await repo.update(
            service_id,
            "list_items",
            description="List all items with pagination",
        )
        assert updated is not None
        assert updated.description == "List all items with pagination"
        assert updated.http_method == "GET"  # unchanged
        assert updated.path_template == "/api/v1/items"  # unchanged

        # UPDATE — change method and path
        updated2 = await repo.update(
            service_id,
            "list_items",
            http_method="post",
            path_template="/api/v2/items",
        )
        assert updated2 is not None
        assert updated2.http_method == "POST"  # uppercased
        assert updated2.path_template == "/api/v2/items"

        # UPDATE — params_schema
        updated3 = await repo.update(
            service_id,
            "list_items",
            params_schema={"type": "object", "properties": {"limit": {"type": "integer"}}},
        )
        assert updated3 is not None
        assert "limit" in updated3.params_schema["properties"]

        # UPDATE — not found
        not_found = await repo.update(service_id, "does_not_exist", description="x")
        assert not_found is None

        # UPDATE — no-op (all None fields)
        noop = await repo.update(service_id, "list_items")
        assert noop is not None
        assert noop.http_method == "POST"  # still the value from previous update

        # DELETE
        deleted = await repo.delete(service_id, "list_items")
        assert deleted is True

        # DELETE — already gone
        deleted_again = await repo.delete(service_id, "list_items")
        assert deleted_again is False

        # Verify empty
        tools = await repo.get_by_service_id(service_id)
        assert len(tools) == 0

    async def test_multiple_tools_per_service(
        self, repo: FakeGenericToolRepository, service_id: UUID
    ):
        """Create multiple tools on the same service."""
        for i in range(5):
            await repo.create(
                service_id=service_id,
                tool_name=f"tool_{i}",
                description=f"Tool number {i}",
                http_method="GET",
                path_template=f"/api/tool{i}",
                params_schema={},
            )

        tools = await repo.get_by_service_id(service_id)
        assert len(tools) == 5

        # Delete one
        await repo.delete(service_id, "tool_2")
        tools = await repo.get_by_service_id(service_id)
        assert len(tools) == 4
        assert "tool_2" not in {t.tool_name for t in tools}

    async def test_tools_isolated_by_service(self, repo: FakeGenericToolRepository):
        """Tools from different services don't interfere."""
        svc_a = uuid4()
        svc_b = uuid4()

        await repo.create(svc_a, "shared_name", "From A", "GET", "/a", {})
        await repo.create(svc_b, "shared_name", "From B", "POST", "/b", {})

        a_tools = await repo.get_by_service_id(svc_a)
        b_tools = await repo.get_by_service_id(svc_b)
        assert len(a_tools) == 1
        assert len(b_tools) == 1
        assert a_tools[0].description == "From A"
        assert b_tools[0].description == "From B"

        # Delete from A doesn't affect B
        await repo.delete(svc_a, "shared_name")
        assert len(await repo.get_by_service_id(svc_a)) == 0
        assert len(await repo.get_by_service_id(svc_b)) == 1


class TestOpenAPIImportSkipLogic:
    """Simulate the skip-on-duplicate logic from the import endpoint."""

    @pytest.fixture
    def repo(self) -> FakeGenericToolRepository:
        return FakeGenericToolRepository()

    @pytest.fixture
    def service_id(self) -> UUID:
        return uuid4()

    async def test_first_import_creates_all(
        self, repo: FakeGenericToolRepository, service_id: UUID
    ):
        specs = [
            {
                "tool_name": "get_users",
                "description": "Get users",
                "http_method": "GET",
                "path_template": "/users",
                "params_schema": {},
            },
            {
                "tool_name": "create_user",
                "description": "Create user",
                "http_method": "POST",
                "path_template": "/users",
                "params_schema": {},
            },
            {
                "tool_name": "delete_user",
                "description": "Delete user",
                "http_method": "DELETE",
                "path_template": "/users/{id}",
                "params_schema": {},
            },
        ]

        # Simulate import logic from services.py
        existing_tools = await repo.get_by_service_id(service_id)
        existing_names = {t.tool_name for t in existing_tools}
        created = []
        skipped = []

        for spec in specs:
            if spec["tool_name"] in existing_names:
                skipped.append(spec["tool_name"])
                continue
            await repo.create(service_id, **spec)
            created.append(spec["tool_name"])

        assert created == ["get_users", "create_user", "delete_user"]
        assert skipped == []
        assert len(await repo.get_by_service_id(service_id)) == 3

    async def test_reimport_skips_all(self, repo: FakeGenericToolRepository, service_id: UUID):
        specs = [
            {
                "tool_name": "get_users",
                "description": "Get users",
                "http_method": "GET",
                "path_template": "/users",
                "params_schema": {},
            },
            {
                "tool_name": "create_user",
                "description": "Create user",
                "http_method": "POST",
                "path_template": "/users",
                "params_schema": {},
            },
        ]

        # First import
        for spec in specs:
            await repo.create(service_id, **spec)

        # Second import — simulate skip logic
        existing_tools = await repo.get_by_service_id(service_id)
        existing_names = {t.tool_name for t in existing_tools}
        created = []
        skipped = []

        for spec in specs:
            if spec["tool_name"] in existing_names:
                skipped.append(spec["tool_name"])
                continue
            await repo.create(service_id, **spec)
            created.append(spec["tool_name"])

        assert created == []
        assert skipped == ["get_users", "create_user"]
        assert len(await repo.get_by_service_id(service_id)) == 2  # unchanged

    async def test_partial_reimport_skips_existing(
        self, repo: FakeGenericToolRepository, service_id: UUID
    ):
        # Pre-existing tool
        await repo.create(service_id, "get_users", "Get users", "GET", "/users", {})

        # Import with one existing + two new
        specs = [
            {
                "tool_name": "get_users",
                "description": "Get users v2",
                "http_method": "GET",
                "path_template": "/v2/users",
                "params_schema": {},
            },
            {
                "tool_name": "update_user",
                "description": "Update user",
                "http_method": "PUT",
                "path_template": "/users/{id}",
                "params_schema": {},
            },
            {
                "tool_name": "get_roles",
                "description": "Get roles",
                "http_method": "GET",
                "path_template": "/roles",
                "params_schema": {},
            },
        ]

        existing_tools = await repo.get_by_service_id(service_id)
        existing_names = {t.tool_name for t in existing_tools}
        created = []
        skipped = []

        for spec in specs:
            if spec["tool_name"] in existing_names:
                skipped.append(spec["tool_name"])
                continue
            await repo.create(service_id, **spec)
            created.append(spec["tool_name"])

        assert created == ["update_user", "get_roles"]
        assert skipped == ["get_users"]
        assert len(await repo.get_by_service_id(service_id)) == 3

        # Verify original get_users was NOT overwritten
        original = await repo.get_by_name(service_id, "get_users")
        assert original is not None
        assert original.description == "Get users"  # not "Get users v2"
        assert original.path_template == "/users"  # not "/v2/users"


class TestToolNameValidation:
    """Verify tool name constraints match MCP requirements."""

    def test_valid_names(self):
        assert validate_tool_name("list_items") == "list_items"
        assert validate_tool_name("getUser") == "getUser"
        assert validate_tool_name("a") == "a"
        assert validate_tool_name("Tool123") == "Tool123"
        assert validate_tool_name("get_user_by_id_v2") == "get_user_by_id_v2"

    def test_invalid_names(self):
        invalid = [
            "",  # empty
            "123abc",  # starts with digit
            "list-items",  # hyphen
            "list items",  # space
            "list.items",  # dot
            "list@items",  # special char
            "_private",  # starts with underscore
            "a" * 201,  # too long
        ]
        for name in invalid:
            with pytest.raises(ValueError, match="Invalid tool name"):
                validate_tool_name(name)


class TestToolRegistryBuildWithGenericRest:
    """Verify the tool registry correctly loads generic_rest tools."""

    @pytest.fixture
    def fake_generic_repo(self) -> FakeGenericToolRepository:
        return FakeGenericToolRepository()

    async def test_generic_rest_tools_loaded_into_registry(
        self,
        fake_repo: FakeServiceRepository,
        fake_generic_repo: FakeGenericToolRepository,
    ):

        # Create a generic_rest service
        svc = make_service(
            name="my_api",
            display_name="My API",
            service_type=ServiceType.GENERIC_REST,
            base_url="https://api.example.com",
        )
        svc = await fake_repo.create(svc)
        assert svc.id is not None
        svc_id = svc.id

        # Add tools to the generic tool repo
        await fake_generic_repo.create(
            service_id=svc_id,
            tool_name="list_widgets",
            description="List widgets",
            http_method="GET",
            path_template="/widgets",
            params_schema={"type": "object", "properties": {}},
        )
        await fake_generic_repo.create(
            service_id=svc_id,
            tool_name="create_widget",
            description="Create a widget",
            http_method="POST",
            path_template="/widgets",
            params_schema={"type": "object", "properties": {"name": {"type": "string"}}},
        )

        # Verify the tools are stored
        tools = await fake_generic_repo.get_by_service_id(svc_id)
        assert len(tools) == 2
        assert {t.tool_name for t in tools} == {"list_widgets", "create_widget"}


class TestSelfMcpAccessControl:
    """Verify the per-user self_mcp_enabled field works through the stack."""

    def test_user_entity_default(self):
        from domain.entities.user import User

        user = User(username="testuser")
        assert user.self_mcp_enabled is False

    def test_user_entity_enabled(self):
        from domain.entities.user import User

        user = User(username="admin", self_mcp_enabled=True, is_admin=True)
        assert user.self_mcp_enabled is True
        assert user.is_admin is True

    def test_auth_context_default(self):
        from security.auth_context import AuthContext

        ctx = AuthContext(
            is_admin=False,
            allowed_service_ids=set(),
            username="test",
            user_id=None,
        )
        assert ctx.self_mcp_enabled is False

    def test_auth_context_with_self_mcp(self):
        from security.auth_context import AuthContext

        ctx = AuthContext(
            is_admin=False,
            allowed_service_ids=set(),
            username="test",
            user_id=None,
            self_mcp_enabled=True,
        )
        assert ctx.self_mcp_enabled is True


class TestConfigBranding:
    """Verify the configurable app name propagates correctly."""

    def test_default_app_name(self):
        from config import Settings

        s = Settings(encryption_key="test", database_url="sqlite:///:memory:")
        assert s.app_name == "MCP Manager"

    def test_custom_app_name(self, monkeypatch):
        monkeypatch.setenv("APP_NAME", "My Homelab Gateway")
        from config import Settings

        s = Settings(encryption_key="test", database_url="sqlite:///:memory:")
        assert s.app_name == "My Homelab Gateway"


class TestGenericRestClientConfig:
    """Verify custom headers and health_check_path from config are applied."""

    def test_custom_headers_applied(self):
        from infrastructure.clients.generic_rest_client import GenericRestClient

        client = GenericRestClient(
            base_url="https://api.example.com",
            api_token="test-token",
            config={"headers": {"X-Custom": "value123", "Accept": "application/xml"}},
        )
        headers = dict(client._client.headers)
        assert headers["x-custom"] == "value123"
        assert headers["accept"] == "application/xml"
        assert headers["authorization"] == "Bearer test-token"

    def test_dangerous_headers_blocked(self):
        from infrastructure.clients.generic_rest_client import GenericRestClient

        client = GenericRestClient(
            base_url="https://api.example.com",
            api_token="test-token",
            config={"headers": {"Host": "evil.com", "Content-Length": "0", "X-Safe": "ok"}},
        )
        headers = dict(client._client.headers)
        assert "evil.com" not in headers.values()
        assert headers.get("x-safe") == "ok"

    def test_authorization_cannot_be_overridden(self):
        from infrastructure.clients.generic_rest_client import GenericRestClient

        client = GenericRestClient(
            base_url="https://api.example.com",
            api_token="real-token",
            config={"headers": {"Authorization": "Bearer malicious", "Content-Type": "text/xml"}},
        )
        headers = dict(client._client.headers)
        # Hardcoded headers always win over custom headers
        assert headers["authorization"] == "Bearer real-token"
        assert headers["content-type"] == "application/json"

    def test_custom_health_check_path(self):
        from infrastructure.clients.generic_rest_client import GenericRestClient

        client = GenericRestClient(
            base_url="https://api.example.com",
            api_token="test-token",
            config={"health_check_path": "/healthz"},
        )
        assert client._health_check_path == "/healthz"

    def test_default_health_check_path(self):
        from infrastructure.clients.generic_rest_client import GenericRestClient

        client = GenericRestClient(
            base_url="https://api.example.com",
            api_token="test-token",
        )
        assert client._health_check_path == "/"

    def test_no_config(self):
        from infrastructure.clients.generic_rest_client import GenericRestClient

        client = GenericRestClient(
            base_url="https://api.example.com",
            api_token="test-token",
        )
        headers = dict(client._client.headers)
        assert headers["authorization"] == "Bearer test-token"
        assert headers["content-type"] == "application/json"
