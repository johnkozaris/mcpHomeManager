"""Integration tests for new API endpoints using Litestar's test client.

These tests exercise the actual HTTP layer (serialization, routing, status codes)
without needing a real database — they mock the app.state dependencies.
"""

from typing import Any, cast
from unittest.mock import MagicMock

import pytest
from litestar import Litestar
from litestar.di import Provide
from litestar.testing import AsyncTestClient

from domain.entities.app_definition import AppDefinition
from entrypoints.api.tools import ToolController
from security.auth_context import AuthContext
from services.tool_registry import ActiveApp, ToolRegistry

# --- Fixtures ---


def _set_test_user(connection, _):
    """App-level guard that injects a test admin user into scope["user"].

    This replaces the auth middleware for tests, making request.user available.
    """
    connection.scope["user"] = AuthContext(
        is_admin=True,
        allowed_service_ids=set(),
        username="admin",
        user_id=None,
    )


@pytest.fixture
def fake_registry():
    """Create a ToolRegistry without DB sessions for testing."""
    import asyncio

    registry = ToolRegistry.__new__(ToolRegistry)
    registry._session_factory = MagicMock()
    registry._encryption = MagicMock()
    registry._client_factory = MagicMock()
    registry._active_tools = {}
    registry._all_tools = {}
    registry._active_apps = {}
    registry._clients = []
    registry._lock = asyncio.Lock()
    registry._on_rebuild = None
    return registry


@pytest.fixture
def app(fake_registry):
    """Create a minimal Litestar app with just the controllers under test."""

    async def provide_tool_registry() -> ToolRegistry:
        return fake_registry

    async def provide_client_factory():
        from services.client_factory import ServiceClientFactory

        return ServiceClientFactory()

    test_app = Litestar(
        route_handlers=[ToolController],
        dependencies={
            "tool_registry": Provide(provide_tool_registry),
            "client_factory": Provide(provide_client_factory),
        },
        guards=[_set_test_user],
        debug=True,
    )
    return test_app


# --- App endpoint tests ---


class TestAppEndpoints:
    async def test_list_apps_empty(self, app):
        async with AsyncTestClient(app) as client:
            resp = await client.get("/api/tools/apps")
            assert resp.status_code == 200
            assert resp.json() == []

    async def test_list_apps_with_data(self, app, fake_registry):
        from conftest import FakeAppProviderClient

        provider = FakeAppProviderClient()
        fake_registry._active_apps["test_app"] = ActiveApp(
            definition=AppDefinition(
                name="test_app",
                service_type="homeassistant",
                title="Test App",
                description="A test",
                template_name="test.html",
            ),
            provider=provider,
            client=provider,
            service_name="ha",
        )

        async with AsyncTestClient(app) as client:
            resp = await client.get("/api/tools/apps")
            assert resp.status_code == 200
            data = resp.json()
            assert len(data) == 1
            assert data[0]["name"] == "test_app"
            assert data[0]["service_name"] == "ha"
            assert data[0]["title"] == "Test App"

    async def test_render_app_not_found(self, app):
        async with AsyncTestClient(app) as client:
            resp = await client.post(
                "/api/tools/apps/nonexistent/render",
                json={},
            )
            assert resp.status_code == 404
            assert "not found" in resp.text.lower()

    async def test_action_app_not_found(self, app):
        async with AsyncTestClient(app) as client:
            resp = await client.post(
                "/api/tools/apps/nonexistent/action",
                json={"action": "test", "payload": {}},
            )
            assert resp.status_code == 404

    async def test_render_app_success(self, app, fake_registry):
        from conftest import FakeAppProviderClient

        provider = FakeAppProviderClient()
        fake_registry._active_apps["test_app"] = ActiveApp(
            definition=AppDefinition(
                name="test_app",
                service_type="homeassistant",
                title="Test App",
                description="A test",
                template_name="ha_entities.html",
            ),
            provider=provider,
            client=provider,
            service_name="ha",
        )
        # Override fetch_app_data to return valid template data
        provider._app_data = {
            "domains": {
                "light": [{"entity_id": "light.test", "state": "on", "friendly_name": "Test"}]
            },
            "entity_count": 1,
            "domain_filter": None,
        }

        async with AsyncTestClient(app) as client:
            resp = await client.post(
                "/api/tools/apps/test_app/render",
                json={},
            )
            assert resp.status_code in (200, 201)
            assert "text/html" in resp.headers.get("content-type", "")
            assert "Entity Dashboard" in resp.text
            assert "light.test" in resp.text

    async def test_action_app_success(self, app, fake_registry):
        from conftest import FakeAppProviderClient

        provider = FakeAppProviderClient()
        fake_registry._active_apps["test_app"] = ActiveApp(
            definition=AppDefinition(
                name="test_app",
                service_type="homeassistant",
                title="Test App",
                description="A test",
                template_name="ha_entities.html",
            ),
            provider=provider,
            client=provider,
            service_name="ha",
        )
        # handle_app_action returns data but we need to set _app_data to something
        # that renders for the ha_entities template
        provider._app_data = {
            "domains": {},
            "entity_count": 0,
            "domain_filter": None,
        }

        # Override handle_app_action to return valid template data
        async def mock_handle(app_name, action, payload):
            return {
                "domains": {},
                "entity_count": 0,
                "domain_filter": None,
            }

        cast(Any, provider).handle_app_action = mock_handle

        async with AsyncTestClient(app) as client:
            resp = await client.post(
                "/api/tools/apps/test_app/action",
                json={"action": "refresh", "payload": {}},
            )
            assert resp.status_code in (200, 201)
            assert "text/html" in resp.headers.get("content-type", "")


# --- Tool endpoint tests ---


class TestToolEndpoints:
    async def test_list_tools_empty(self, app):
        async with AsyncTestClient(app) as client:
            resp = await client.get("/api/tools/")
            assert resp.status_code == 200
            assert resp.json() == []

    async def test_list_tools_with_data(self, app, fake_registry):
        from conftest import FakeServiceClient
        from domain.entities.service_connection import ServiceType
        from domain.entities.tool_definition import ToolDefinition
        from services.tool_registry import ActiveTool

        client_obj = FakeServiceClient()
        tool = ActiveTool(
            definition=ToolDefinition(
                name="test_tool",
                service_type=ServiceType.FORGEJO,
                description="A test tool",
                parameters_schema={"type": "object", "properties": {"q": {"type": "string"}}},
                is_enabled=True,
            ),
            client=client_obj,
            service_name="forgejo",
        )
        fake_registry._all_tools["test_tool"] = tool

        async with AsyncTestClient(app) as client:
            resp = await client.get("/api/tools/")
            assert resp.status_code == 200
            data = resp.json()
            assert len(data) == 1
            assert data[0]["name"] == "test_tool"
            assert data[0]["service_type"] == "forgejo"
            assert data[0]["description"] == "A test tool"
            assert data[0]["is_enabled"] is True
            assert "properties" in data[0]["parameters_schema"]


# --- App response shape tests ---


class TestAppResponseShape:
    async def test_app_response_has_all_fields(self, app, fake_registry):
        from conftest import FakeAppProviderClient

        provider = FakeAppProviderClient()
        fake_registry._active_apps["my_app"] = ActiveApp(
            definition=AppDefinition(
                name="my_app",
                service_type="homeassistant",
                title="My App",
                description="My description",
                template_name="test.html",
                parameters_schema={
                    "type": "object",
                    "properties": {"x": {"type": "string"}},
                    "required": ["x"],
                },
            ),
            provider=provider,
            client=provider,
            service_name="ha_svc",
        )

        async with AsyncTestClient(app) as client:
            resp = await client.get("/api/tools/apps")
            data = resp.json()
            a = data[0]
            assert a["name"] == "my_app"
            assert a["service_type"] == "homeassistant"
            assert a["service_name"] == "ha_svc"
            assert a["title"] == "My App"
            assert a["description"] == "My description"
            assert a["parameters_schema"]["required"] == ["x"]

    async def test_multiple_apps(self, app, fake_registry):
        from conftest import FakeAppProviderClient

        provider = FakeAppProviderClient()
        for name in ["app_a", "app_b", "app_c"]:
            fake_registry._active_apps[name] = ActiveApp(
                definition=AppDefinition(
                    name=name,
                    service_type="homeassistant",
                    title=f"App {name}",
                    description=f"Description for {name}",
                    template_name="ha_entities.html",
                ),
                provider=provider,
                client=provider,
                service_name="ha",
            )

        async with AsyncTestClient(app) as client:
            resp = await client.get("/api/tools/apps")
            data = resp.json()
            assert len(data) == 3
            names = {a["name"] for a in data}
            assert names == {"app_a", "app_b", "app_c"}


# --- Template rendering edge cases ---


class TestAppRenderEdgeCases:
    async def test_render_with_empty_body(self, app, fake_registry):
        """POST with empty JSON body should work."""
        from conftest import FakeAppProviderClient

        provider = FakeAppProviderClient()
        provider._app_data = {"domains": {}, "entity_count": 0, "domain_filter": None}
        fake_registry._active_apps["test"] = ActiveApp(
            definition=AppDefinition(
                name="test",
                service_type="homeassistant",
                title="Test",
                description="Test",
                template_name="ha_entities.html",
            ),
            provider=provider,
            client=provider,
            service_name="ha",
        )

        async with AsyncTestClient(app) as client:
            resp = await client.post("/api/tools/apps/test/render", json={})
            assert resp.status_code in (200, 201)
            assert "<!DOCTYPE html>" in resp.text

    async def test_render_paperless_template(self, app, fake_registry):
        """Paperless template renders correctly with search data."""
        from conftest import FakeAppProviderClient

        provider = FakeAppProviderClient()
        provider._app_data = {
            "documents": [
                {
                    "title": "Invoice 2024",
                    "correspondent": "Acme",
                    "tags": ["finance"],
                    "created": "2024-01-15",
                },
            ],
            "query": "invoice",
            "total": 1,
        }

        async def mock_fetch(app_name, arguments):
            return dict(provider._app_data)

        cast(Any, provider).fetch_app_data = mock_fetch

        fake_registry._active_apps["paperless_search"] = ActiveApp(
            definition=AppDefinition(
                name="paperless_search",
                service_type="paperless",
                title="Search",
                description="Search docs",
                template_name="paperless_documents.html",
            ),
            provider=provider,
            client=provider,
            service_name="paperless",
        )

        async with AsyncTestClient(app) as client:
            resp = await client.post("/api/tools/apps/paperless_search/render", json={})
            assert resp.status_code in (200, 201)
            assert "Invoice 2024" in resp.text
            assert "Acme" in resp.text
            assert "finance" in resp.text

    async def test_render_forgejo_template(self, app, fake_registry):
        """Forgejo template renders correctly with repo data."""
        from conftest import FakeAppProviderClient

        provider = FakeAppProviderClient()
        provider._app_data = {
            "repos": [
                {
                    "name": "my-repo",
                    "full_name": "user/my-repo",
                    "description": "A cool project",
                    "updated_at": None,
                },
            ],
            "owner_filter": None,
        }

        async def mock_fetch(app_name, arguments):
            return dict(provider._app_data)

        cast(Any, provider).fetch_app_data = mock_fetch

        fake_registry._active_apps["forgejo_repos"] = ActiveApp(
            definition=AppDefinition(
                name="forgejo_repos",
                service_type="forgejo",
                title="Repos",
                description="Browse repos",
                template_name="forgejo_repos.html",
            ),
            provider=provider,
            client=provider,
            service_name="forgejo",
        )

        async with AsyncTestClient(app) as client:
            resp = await client.post("/api/tools/apps/forgejo_repos/render", json={})
            assert resp.status_code in (200, 201)
            assert "user/my-repo" in resp.text
            assert "A cool project" in resp.text

    async def test_render_app_provider_error_returns_500(self, app, fake_registry):
        """If fetch_app_data raises, we get a 500 with a message, not a stack trace."""
        from conftest import FakeAppProviderClient

        provider = FakeAppProviderClient()

        async def failing_fetch(app_name, arguments):
            raise RuntimeError("Connection refused")

        cast(Any, provider).fetch_app_data = failing_fetch

        fake_registry._active_apps["broken"] = ActiveApp(
            definition=AppDefinition(
                name="broken",
                service_type="homeassistant",
                title="Broken",
                description="Broken app",
                template_name="ha_entities.html",
            ),
            provider=provider,
            client=provider,
            service_name="ha",
        )

        async with AsyncTestClient(app) as client:
            resp = await client.post("/api/tools/apps/broken/render", json={})
            assert resp.status_code == 500
            assert "Failed to render app" in resp.text
            # Should NOT leak the stack trace
            assert "RuntimeError" not in resp.text

    async def test_action_provider_error_returns_500(self, app, fake_registry):
        """If handle_app_action raises, we get a 500 not a stack trace."""
        from conftest import FakeAppProviderClient

        provider = FakeAppProviderClient()

        async def failing_action(app_name, action, payload):
            raise ValueError("Bad action")

        cast(Any, provider).handle_app_action = failing_action

        fake_registry._active_apps["broken"] = ActiveApp(
            definition=AppDefinition(
                name="broken",
                service_type="homeassistant",
                title="Broken",
                description="Broken app",
                template_name="ha_entities.html",
            ),
            provider=provider,
            client=provider,
            service_name="ha",
        )

        async with AsyncTestClient(app) as client:
            resp = await client.post(
                "/api/tools/apps/broken/action",
                json={"action": "boom", "payload": {}},
            )
            assert resp.status_code == 500
            assert "Failed to execute action" in resp.text
            assert "ValueError" not in resp.text
