"""Tests for the 6 new service clients (NPM, Portainer, FreshRSS, Wallabag, StirlingPDF, WikiJS)."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from domain.entities.service_connection import ServiceType
from domain.exceptions import ServiceConnectionError, ToolExecutionError
from infrastructure.clients.freshrss_client import FreshRSSClient
from infrastructure.clients.npm_client import NginxProxyManagerClient
from infrastructure.clients.portainer_client import PortainerClient
from infrastructure.clients.stirlingpdf_client import StirlingPdfClient
from infrastructure.clients.wallabag_client import WallabagClient
from infrastructure.clients.wikijs_client import WikiJsClient


def _mock_response(json_data=None, text_data="", status_code=200):
    """Build a mock httpx response."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.headers = {"content-type": "application/json"}
    resp.json.return_value = json_data if json_data is not None else {}
    resp.text = text_data
    resp.raise_for_status = MagicMock()
    return resp


def _patch_client_transport(client):
    """Replace the httpx AsyncClient with an AsyncMock so no real HTTP calls are made."""
    mock = AsyncMock()
    mock.request = AsyncMock(return_value=_mock_response())
    mock.headers = {}
    client._client = mock
    return mock


# ---------------------------------------------------------------------------
# NginxProxyManagerClient
# ---------------------------------------------------------------------------
class TestNginxProxyManagerClient:
    def test_get_tool_definitions(self):
        client = NginxProxyManagerClient("http://test:8080", "admin@example.com:password123")
        defs = client.get_tool_definitions()
        assert len(defs) == 7
        assert all(d.service_type == ServiceType.NGINX_PROXY_MANAGER for d in defs)

    async def test_unknown_tool_raises(self):
        client = NginxProxyManagerClient("http://test:8080", "admin@example.com:password123")
        client._jwt = "fake-jwt"
        with pytest.raises(ToolExecutionError, match="Unknown tool"):
            await client.execute_tool("nonexistent", {})
        await client.close()

    async def test_list_proxy_hosts(self):
        client = NginxProxyManagerClient("http://test:8080", "admin@example.com:password123")
        client._jwt = "fake-jwt"
        mock = _patch_client_transport(client)
        mock.request.return_value = _mock_response([{"id": 1, "domain_names": ["example.com"]}])

        result = await client.execute_tool("npm_list_proxy_hosts", {})
        assert result == [{"id": 1, "domain_names": ["example.com"]}]
        mock.request.assert_called_once()

    async def test_ensure_jwt_sets_auth_header(self):
        client = NginxProxyManagerClient("http://test:8080", "admin@example.com:password123")
        mock_transport = AsyncMock()
        mock_transport.headers = {}
        mock_transport.post = AsyncMock(return_value=_mock_response({"token": "my-jwt-token"}))
        client._client = mock_transport

        await client._ensure_jwt()
        assert client._jwt == "my-jwt-token"
        assert mock_transport.headers["Authorization"] == "Bearer my-jwt-token"


# ---------------------------------------------------------------------------
# PortainerClient
# ---------------------------------------------------------------------------
class TestPortainerClient:
    def test_get_tool_definitions(self):
        client = PortainerClient("http://test:8080", "admin:password123")
        defs = client.get_tool_definitions()
        assert len(defs) == 8
        assert all(d.service_type == ServiceType.PORTAINER for d in defs)

    async def test_unknown_tool_raises(self):
        client = PortainerClient("http://test:8080", "admin:password123")
        client._jwt = "fake-jwt"
        with pytest.raises(ToolExecutionError, match="Unknown tool"):
            await client.execute_tool("nonexistent", {})
        await client.close()

    async def test_list_endpoints(self):
        client = PortainerClient("http://test:8080", "admin:password123")
        client._jwt = "fake-jwt"
        mock = _patch_client_transport(client)
        mock.request.return_value = _mock_response([{"Id": 1, "Name": "local"}])

        result = await client.execute_tool("portainer_list_endpoints", {})
        assert result == [{"Id": 1, "Name": "local"}]

    async def test_ensure_jwt_sets_auth_header(self):
        client = PortainerClient("http://test:8080", "admin:password123")
        mock_transport = AsyncMock()
        mock_transport.headers = {}
        mock_transport.post = AsyncMock(return_value=_mock_response({"jwt": "portainer-jwt"}))
        client._client = mock_transport

        await client._ensure_jwt()
        assert client._jwt == "portainer-jwt"
        assert mock_transport.headers["Authorization"] == "Bearer portainer-jwt"


# ---------------------------------------------------------------------------
# FreshRSSClient
# ---------------------------------------------------------------------------
class TestFreshRSSClient:
    def test_get_tool_definitions(self):
        client = FreshRSSClient("http://test:8080", "user:password")
        defs = client.get_tool_definitions()
        assert len(defs) == 7
        assert all(d.service_type == ServiceType.FRESHRSS for d in defs)

    async def test_unknown_tool_raises(self):
        client = FreshRSSClient("http://test:8080", "user:password")
        client._auth_token = "fake"
        with pytest.raises(ToolExecutionError, match="Unknown tool"):
            await client.execute_tool("nonexistent", {})
        await client.close()

    async def test_list_feeds(self):
        client = FreshRSSClient("http://test:8080", "user:password")
        client._auth_token = "fake"
        mock = _patch_client_transport(client)
        mock.request.return_value = _mock_response({"subscriptions": []})

        result = await client.execute_tool("freshrss_list_feeds", {})
        assert result == {"subscriptions": []}

    async def test_ensure_auth_parses_auth_line(self):
        client = FreshRSSClient("http://test:8080", "user:password")
        auth_text = "SID=xxx\nLSID=yyy\nAuth=fake-auth-token\n"
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = auth_text
        mock_resp.raise_for_status = MagicMock()

        mock_transport = AsyncMock()
        mock_transport.headers = {}
        mock_transport.post = AsyncMock(return_value=mock_resp)
        client._client = mock_transport

        await client._ensure_auth()
        assert client._auth_token == "fake-auth-token"
        assert mock_transport.headers["Authorization"] == "GoogleLogin auth=fake-auth-token"


# ---------------------------------------------------------------------------
# WallabagClient
# ---------------------------------------------------------------------------
class TestWallabagClient:
    def test_get_tool_definitions(self):
        client = WallabagClient("http://test:8080", "cid:csecret:user:pass")
        defs = client.get_tool_definitions()
        assert len(defs) == 7
        assert all(d.service_type == ServiceType.WALLABAG for d in defs)

    async def test_unknown_tool_raises(self):
        client = WallabagClient("http://test:8080", "cid:csecret:user:pass")
        client._access_token = "fake"
        with pytest.raises(ToolExecutionError, match="Unknown tool"):
            await client.execute_tool("nonexistent", {})
        await client.close()

    async def test_list_entries(self):
        client = WallabagClient("http://test:8080", "cid:csecret:user:pass")
        client._access_token = "fake"
        mock = _patch_client_transport(client)
        mock.request.return_value = _mock_response({"_embedded": {"items": []}})

        result = await client.execute_tool("wallabag_list_entries", {})
        assert result == {"_embedded": {"items": []}}

    async def test_invalid_token_format_raises(self):
        client = WallabagClient("http://test:8080", "only:two")
        mock_transport = AsyncMock()
        mock_transport.headers = {}
        client._client = mock_transport

        with pytest.raises(
            ServiceConnectionError, match="client_id:client_secret:username:password"
        ):
            await client._ensure_token()

    async def test_password_with_colons(self):
        """Wallabag passwords may contain colons — verify they're preserved."""
        client = WallabagClient("http://test:8080", "cid:csecret:user:p:a:s:s")
        mock_transport = AsyncMock()
        mock_transport.headers = {}
        mock_transport.post = AsyncMock(return_value=_mock_response({"access_token": "wall-token"}))
        client._client = mock_transport

        await client._ensure_token()
        # Verify the password was reassembled correctly
        call_kwargs = mock_transport.post.call_args
        assert call_kwargs[1]["data"]["password"] == "p:a:s:s"

    async def test_ensure_token_sets_auth_header(self):
        client = WallabagClient("http://test:8080", "cid:csecret:user:pass")
        mock_transport = AsyncMock()
        mock_transport.headers = {}
        mock_transport.post = AsyncMock(return_value=_mock_response({"access_token": "wall-token"}))
        client._client = mock_transport

        await client._ensure_token()
        assert client._access_token == "wall-token"
        assert mock_transport.headers["Authorization"] == "Bearer wall-token"


# ---------------------------------------------------------------------------
# StirlingPdfClient
# ---------------------------------------------------------------------------
class TestStirlingPdfClient:
    def test_get_tool_definitions(self):
        client = StirlingPdfClient("http://test:8080", "my-api-key")
        defs = client.get_tool_definitions()
        assert len(defs) == 2
        assert all(d.service_type == ServiceType.STIRLING_PDF for d in defs)

    async def test_unknown_tool_raises(self):
        client = StirlingPdfClient("http://test:8080", "my-api-key")
        with pytest.raises(ToolExecutionError, match="Unknown tool"):
            await client.execute_tool("nonexistent", {})
        await client.close()

    async def test_stirling_health(self):
        client = StirlingPdfClient("http://test:8080", "my-api-key")
        mock = _patch_client_transport(client)
        mock.request.return_value = _mock_response({"status": "UP", "version": "1.2.3"})

        result = await client.execute_tool("stirling_health", {})
        assert result == {"status": "UP", "version": "1.2.3"}
        mock.request.assert_called_once_with("GET", "/api/v1/info/status")

    async def test_get_operations_returns_static_dict(self):
        client = StirlingPdfClient("http://test:8080", "my-api-key")
        result = await client.execute_tool("stirling_get_operations", {})
        assert isinstance(result, dict)
        assert result["coverage"] == "representative_subset"
        assert (
            result["documentation"]["online_api_docs"]
            == "https://registry.scalar.com/@stirlingpdf/apis/stirling-pdf-processing-api/"
        )
        assert "operations" in result
        assert "merge_pdfs" in result["operations"]
        assert "API or web UI directly" in result["note"]


# ---------------------------------------------------------------------------
# WikiJsClient
# ---------------------------------------------------------------------------
class TestWikiJsClient:
    def test_get_tool_definitions(self):
        client = WikiJsClient("http://test:8080", "my-api-key")
        defs = client.get_tool_definitions()
        assert len(defs) == 6
        assert all(d.service_type == ServiceType.WIKIJS for d in defs)

    async def test_unknown_tool_raises(self):
        client = WikiJsClient("http://test:8080", "my-api-key")
        with pytest.raises(ToolExecutionError, match="Unknown tool"):
            await client.execute_tool("nonexistent", {})
        await client.close()

    async def test_list_pages(self):
        client = WikiJsClient("http://test:8080", "my-api-key")
        mock = _patch_client_transport(client)
        graphql_resp = {
            "data": {
                "pages": {
                    "list": [{"id": 1, "path": "test", "title": "Test", "updatedAt": "2024-01-01"}]
                }
            }
        }
        mock.request.return_value = _mock_response(graphql_resp)

        result = await client.execute_tool("wikijs_list_pages", {})
        assert result == [{"id": 1, "path": "test", "title": "Test", "updatedAt": "2024-01-01"}]

    async def test_graphql_error_raises(self):
        client = WikiJsClient("http://test:8080", "my-api-key")
        mock = _patch_client_transport(client)
        mock.request.return_value = _mock_response({"errors": [{"message": "Not found"}]})

        with pytest.raises(ToolExecutionError, match="Not found"):
            await client.execute_tool("wikijs_list_pages", {})
