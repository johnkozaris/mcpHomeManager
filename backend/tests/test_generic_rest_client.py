"""Tests for the generic REST client."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from domain.entities.generic_tool_spec import REQUEST_SHAPE_METADATA_KEY, GenericToolSpec
from domain.entities.service_connection import ServiceType
from domain.exceptions import ToolExecutionError
from infrastructure.clients.generic_rest_client import (
    GenericRestClient,
    validate_base_url,
)


@pytest.fixture
def tool_specs() -> list[GenericToolSpec]:
    return [
        GenericToolSpec(
            tool_name="list_items",
            description="List all items",
            http_method="GET",
            path_template="/api/items",
            params_schema={"type": "object", "properties": {"limit": {"type": "integer"}}},
        ),
        GenericToolSpec(
            tool_name="create_item",
            description="Create an item",
            http_method="POST",
            path_template="/api/items",
            params_schema={"type": "object", "properties": {"name": {"type": "string"}}},
        ),
        GenericToolSpec(
            tool_name="get_item",
            description="Get an item by ID",
            http_method="GET",
            path_template="/api/items/{item_id}",
            params_schema={"type": "object", "properties": {"item_id": {"type": "string"}}},
        ),
        GenericToolSpec(
            tool_name="update_widget",
            description="Update a widget",
            http_method="POST",
            path_template="/api/widgets/{widget_id}",
            params_schema={
                "type": "object",
                "properties": {
                    "widget_id": {"type": "string"},
                    "verbose": {"type": "boolean"},
                    "trace": {"type": "string"},
                    "session": {"type": "string"},
                    "name": {"type": "string"},
                },
                REQUEST_SHAPE_METADATA_KEY: {
                    "version": 1,
                    "parameters": {
                        "widget_id": {"in": "path", "name": "widget_id", "required": True},
                        "verbose": {"in": "query", "name": "verbose", "required": False},
                        "trace": {"in": "header", "name": "X-Trace-Id", "required": False},
                        "session": {"in": "cookie", "name": "session", "required": False},
                    },
                    "body": {
                        "mediaType": "application/json",
                        "encoding": "json",
                        "propertyNames": ["name"],
                        "required": False,
                    },
                },
            },
        ),
        GenericToolSpec(
            tool_name="create_session",
            description="Create a session",
            http_method="POST",
            path_template="/api/sessions",
            params_schema={
                "type": "object",
                "properties": {
                    "username": {"type": "string"},
                    "password": {"type": "string"},
                },
                REQUEST_SHAPE_METADATA_KEY: {
                    "version": 1,
                    "body": {
                        "mediaType": "application/x-www-form-urlencoded",
                        "encoding": "form-urlencoded",
                        "propertyNames": ["username", "password"],
                        "required": True,
                    },
                },
            },
        ),
    ]


class TestGenericRestClient:
    def test_get_tool_definitions(self, tool_specs):
        client = GenericRestClient("http://example.com", "token", tool_specs)
        defs = client.get_tool_definitions()
        assert len(defs) == 5
        assert all(d.service_type == ServiceType.GENERIC_REST for d in defs)
        assert defs[0].name == "list_items"

    def test_empty_tool_definitions(self):
        client = GenericRestClient("http://example.com", "token", [])
        assert client.get_tool_definitions() == []

    async def test_execute_unknown_tool_raises(self, tool_specs):
        client = GenericRestClient("http://example.com", "token", tool_specs)
        with pytest.raises(ToolExecutionError, match="Unknown tool"):
            await client.execute_tool("nonexistent", {})
        await client.close()

    async def test_path_param_interpolation(self, tool_specs):
        client = GenericRestClient("http://example.com", "token", tool_specs)
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "123", "name": "test"}
        mock_response.raise_for_status = MagicMock()

        client._client = AsyncMock()
        client._client.get = AsyncMock(return_value=mock_response)

        result = await client.execute_tool("get_item", {"item_id": "123"})
        client._client.get.assert_called_once_with("/api/items/123", params={})
        assert result["id"] == "123"

    async def test_post_sends_json_for_legacy_manual_tools(self, tool_specs):
        client = GenericRestClient("http://example.com", "token", tool_specs)
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"id": "1", "name": "new"}
        mock_response.raise_for_status = MagicMock()

        client._client = AsyncMock()
        client._client.request = AsyncMock(return_value=mock_response)

        result = await client.execute_tool("create_item", {"name": "new"})
        client._client.request.assert_called_once_with("POST", "/api/items", json={"name": "new"})
        assert result == {"id": "1", "name": "new"}

    async def test_imported_tools_route_query_headers_cookies_and_body(self, tool_specs):
        client = GenericRestClient("http://example.com", "token", tool_specs)
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"ok": True}
        mock_response.raise_for_status = MagicMock()

        client._client = AsyncMock()
        client._client.request = AsyncMock(return_value=mock_response)

        await client.execute_tool(
            "update_widget",
            {
                "widget_id": "123",
                "verbose": True,
                "trace": "abc",
                "session": "cookie123",
                "name": "renamed",
            },
        )

        client._client.request.assert_called_once_with(
            "POST",
            "/api/widgets/123",
            params={"verbose": True},
            headers={"X-Trace-Id": "abc"},
            cookies={"session": "cookie123"},
            json={"name": "renamed"},
        )

    async def test_imported_form_urlencoded_body_uses_data_payload(self, tool_specs):
        client = GenericRestClient("http://example.com", "token", tool_specs)
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"ok": True}
        mock_response.raise_for_status = MagicMock()

        client._client = AsyncMock()
        client._client.request = AsyncMock(return_value=mock_response)

        await client.execute_tool(
            "create_session",
            {"username": "demo", "password": "secret"},
        )

        client._client.request.assert_called_once_with(
            "POST",
            "/api/sessions",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={"username": "demo", "password": "secret"},
        )

    async def test_missing_path_param_raises(self, tool_specs):
        client = GenericRestClient("http://example.com", "token", tool_specs)
        with pytest.raises(ValueError, match="Missing required path parameters"):
            await client.execute_tool("get_item", {})

    async def test_path_traversal_blocked(self, tool_specs):
        client = GenericRestClient("http://example.com", "token", tool_specs)
        with pytest.raises(ValueError, match="forbidden characters"):
            await client.execute_tool("get_item", {"item_id": "../../etc/passwd"})


class TestSSRFProtection:
    """Validate base URL safety — allows internal IPs (homelab), blocks metadata endpoints."""

    async def test_allows_localhost(self):
        assert await validate_base_url("http://localhost:8080") is None

    async def test_allows_private_ip(self):
        assert await validate_base_url("http://192.168.1.1/api") is None

    async def test_allows_loopback(self):
        assert await validate_base_url("http://127.0.0.1:6379") is None

    async def test_allows_docker_hostname(self):
        assert await validate_base_url("http://forgejo:3000") is None

    async def test_blocks_metadata_ip(self):
        with pytest.raises(ValueError, match="cloud metadata endpoint"):
            await validate_base_url("http://169.254.169.254")

    async def test_blocks_metadata_ipv6_mapped(self):
        with pytest.raises(ValueError, match="cloud metadata endpoint"):
            await validate_base_url("http://[::ffff:169.254.169.254]")

    async def test_blocks_metadata_hostname(self):
        with pytest.raises(ValueError, match="cloud metadata endpoint"):
            await validate_base_url("http://metadata.google.internal")

    async def test_allows_public_url(self):
        assert await validate_base_url("https://api.example.com") is None

    async def test_blocks_invalid_scheme(self):
        with pytest.raises(ValueError, match="Invalid URL scheme"):
            await validate_base_url("ftp://example.com")
