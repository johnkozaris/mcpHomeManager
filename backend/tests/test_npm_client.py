"""Targeted tests for the Nginx Proxy Manager client."""

from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from domain.exceptions import ServiceConnectionError, ToolExecutionError
from infrastructure.clients.npm_client import NginxProxyManagerClient


def _mock_response(json_data=None, text_data="", status_code=200):
    """Build a mock httpx response."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.headers = {"content-type": "application/json"}
    resp.json.return_value = json_data if json_data is not None else {}
    resp.text = text_data
    resp.raise_for_status = MagicMock()
    return resp


def _mock_unauthorized_response(path: str = "/api/nginx/proxy-hosts") -> MagicMock:
    request = httpx.Request("GET", f"http://test:8080{path}")
    response = httpx.Response(401, request=request, text="unauthorized")
    mocked = MagicMock()
    mocked.status_code = 401
    mocked.headers = {"content-type": "application/json"}
    mocked.text = "unauthorized"
    mocked.raise_for_status.side_effect = httpx.HTTPStatusError(
        "401 unauthorized", request=request, response=response
    )
    return mocked


class TestNginxProxyManagerClientAuth:
    async def test_ensure_jwt_accepts_official_token_response(self):
        client = NginxProxyManagerClient("http://test:8080", "admin@example.com:password123")
        mock_transport = AsyncMock()
        mock_transport.headers = {}
        mock_transport.post = AsyncMock(
            return_value=_mock_response(
                {
                    "token": "my-jwt-token",
                    "expires": "2026-03-08T00:00:00.000Z",
                }
            )
        )
        client._client = mock_transport

        await client._ensure_jwt()

        assert client._jwt == "my-jwt-token"
        assert mock_transport.headers["Authorization"] == "Bearer my-jwt-token"
        mock_transport.post.assert_awaited_once_with(
            "/api/tokens",
            json={"identity": "admin@example.com", "secret": "password123"},
        )

    async def test_ensure_jwt_rejects_2fa_challenge_response(self):
        client = NginxProxyManagerClient("http://test:8080", "admin@example.com:password123")
        mock_transport = AsyncMock()
        mock_transport.headers = {}
        mock_transport.post = AsyncMock(
            return_value=_mock_response(
                {
                    "requires_2fa": True,
                    "challenge_token": "challenge-token",
                }
            )
        )
        client._client = mock_transport

        with pytest.raises(ServiceConnectionError, match="requires 2FA"):
            await client._ensure_jwt()

        assert client._jwt is None
        assert "Authorization" not in mock_transport.headers


class TestNginxProxyManagerClientTools:
    async def test_list_proxy_hosts_supports_expand_query(self):
        client = NginxProxyManagerClient("http://test:8080", "admin@example.com:password123")
        client._jwt = "cached-jwt"
        mock_transport = AsyncMock()
        mock_transport.headers = {"Authorization": "Bearer cached-jwt"}
        mock_transport.request = AsyncMock(return_value=_mock_response([{"id": 1}]))
        client._client = mock_transport

        result = await client.execute_tool(
            "npm_list_proxy_hosts",
            {"expand": ["access_list", "certificate"], "query": "example"},
        )

        assert result == [{"id": 1}]
        mock_transport.request.assert_awaited_once_with(
            "GET",
            "/api/nginx/proxy-hosts",
            params={"query": "example", "expand": "access_list,certificate"},
        )

    async def test_get_proxy_host_supports_expand_query(self):
        client = NginxProxyManagerClient("http://test:8080", "admin@example.com:password123")
        client._jwt = "cached-jwt"
        mock_transport = AsyncMock()
        mock_transport.headers = {"Authorization": "Bearer cached-jwt"}
        mock_transport.request = AsyncMock(return_value=_mock_response({"id": 4}))
        client._client = mock_transport

        result = await client.execute_tool(
            "npm_get_proxy_host",
            {"id": 4, "expand": ["owner"]},
        )

        assert result == {"id": 4}
        mock_transport.request.assert_awaited_once_with(
            "GET",
            "/api/nginx/proxy-hosts/4",
            params={"expand": "owner"},
        )

    async def test_create_proxy_host_passes_documented_optional_fields(self):
        client = NginxProxyManagerClient("http://test:8080", "admin@example.com:password123")
        client._jwt = "cached-jwt"
        mock_transport = AsyncMock()
        mock_transport.headers = {"Authorization": "Bearer cached-jwt"}
        mock_transport.request = AsyncMock(return_value=_mock_response({"id": 5}))
        client._client = mock_transport

        result = await client.execute_tool(
            "npm_create_proxy_host",
            {
                "domain_names": ["test.example.com"],
                "forward_scheme": "https",
                "forward_host": "127.0.0.1",
                "forward_port": "8443",
                "ssl_forced": True,
                "certificate_id": "7",
                "access_list_id": 3,
                "hsts_enabled": True,
                "hsts_subdomains": True,
                "trust_forwarded_proto": True,
                "http2_support": True,
                "block_exploits": True,
                "caching_enabled": True,
                "allow_websocket_upgrade": True,
                "advanced_config": "proxy_set_header X-Test on;",
                "enabled": False,
                "meta": {"nginx_online": True},
                "locations": [
                    {
                        "path": "/app",
                        "forward_scheme": "http",
                        "forward_host": "app",
                        "forward_port": 8080,
                        "forward_path": "/",
                    }
                ],
            },
        )

        assert result == {"id": 5}
        mock_transport.request.assert_awaited_once_with(
            "POST",
            "/api/nginx/proxy-hosts",
            json={
                "domain_names": ["test.example.com"],
                "forward_scheme": "https",
                "forward_host": "127.0.0.1",
                "forward_port": 8443,
                "ssl_forced": True,
                "certificate_id": 7,
                "access_list_id": 3,
                "hsts_enabled": True,
                "hsts_subdomains": True,
                "trust_forwarded_proto": True,
                "http2_support": True,
                "block_exploits": True,
                "caching_enabled": True,
                "allow_websocket_upgrade": True,
                "advanced_config": "proxy_set_header X-Test on;",
                "enabled": False,
                "meta": {"nginx_online": True},
                "locations": [
                    {
                        "path": "/app",
                        "forward_scheme": "http",
                        "forward_host": "app",
                        "forward_port": 8080,
                        "forward_path": "/",
                    }
                ],
            },
        )

    async def test_create_proxy_host_supports_new_certificate_requests(self):
        client = NginxProxyManagerClient("http://test:8080", "admin@example.com:password123")
        client._jwt = "cached-jwt"
        mock_transport = AsyncMock()
        mock_transport.headers = {"Authorization": "Bearer cached-jwt"}
        mock_transport.request = AsyncMock(return_value=_mock_response({"id": 6}))
        client._client = mock_transport

        result = await client.execute_tool(
            "npm_create_proxy_host",
            {
                "domain_names": ["newcert.example.com"],
                "forward_scheme": "http",
                "forward_host": "127.0.0.1",
                "forward_port": 8080,
                "certificate_id": "new",
            },
        )

        assert result == {"id": 6}
        mock_transport.request.assert_awaited_once_with(
            "POST",
            "/api/nginx/proxy-hosts",
            json={
                "domain_names": ["newcert.example.com"],
                "forward_scheme": "http",
                "forward_host": "127.0.0.1",
                "forward_port": 8080,
                "certificate_id": "new",
                "ssl_forced": False,
            },
        )

    async def test_list_redirection_hosts_supports_expand_query(self):
        client = NginxProxyManagerClient("http://test:8080", "admin@example.com:password123")
        client._jwt = "cached-jwt"
        mock_transport = AsyncMock()
        mock_transport.headers = {"Authorization": "Bearer cached-jwt"}
        mock_transport.request = AsyncMock(return_value=_mock_response([{"id": 9}]))
        client._client = mock_transport

        result = await client.execute_tool(
            "npm_list_redirection_hosts",
            {"expand": ["owner", "certificate"], "query": "redirect"},
        )

        assert result == [{"id": 9}]
        mock_transport.request.assert_awaited_once_with(
            "GET",
            "/api/nginx/redirection-hosts",
            params={"query": "redirect", "expand": "owner,certificate"},
        )

    async def test_list_streams_supports_expand_query(self):
        client = NginxProxyManagerClient("http://test:8080", "admin@example.com:password123")
        client._jwt = "cached-jwt"
        mock_transport = AsyncMock()
        mock_transport.headers = {"Authorization": "Bearer cached-jwt"}
        mock_transport.request = AsyncMock(return_value=_mock_response([{"id": 10}]))
        client._client = mock_transport

        result = await client.execute_tool(
            "npm_list_streams",
            {"expand": ["owner", "certificate"], "query": "9090"},
        )

        assert result == [{"id": 10}]
        mock_transport.request.assert_awaited_once_with(
            "GET",
            "/api/nginx/streams",
            params={"query": "9090", "expand": "owner,certificate"},
        )

    async def test_list_certificates_supports_expand_query(self):
        client = NginxProxyManagerClient("http://test:8080", "admin@example.com:password123")
        client._jwt = "cached-jwt"
        mock_transport = AsyncMock()
        mock_transport.headers = {"Authorization": "Bearer cached-jwt"}
        mock_transport.request = AsyncMock(return_value=_mock_response([{"id": 11}]))
        client._client = mock_transport

        result = await client.execute_tool(
            "npm_list_certificates",
            {"expand": ["owner"], "query": "example.com"},
        )

        assert result == [{"id": 11}]
        mock_transport.request.assert_awaited_once_with(
            "GET",
            "/api/nginx/certificates",
            params={"query": "example.com", "expand": "owner"},
        )

    async def test_expand_validation_rejects_unknown_value(self):
        client = NginxProxyManagerClient("http://test:8080", "admin@example.com:password123")
        client._jwt = "cached-jwt"
        mock_transport = AsyncMock()
        mock_transport.headers = {"Authorization": "Bearer cached-jwt"}
        mock_transport.request = AsyncMock()
        client._client = mock_transport

        with pytest.raises(ToolExecutionError, match="Unsupported expand value"):
            await client.execute_tool("npm_list_proxy_hosts", {"expand": ["bogus"]})

        mock_transport.request.assert_not_called()

    async def test_expand_validation_respects_tool_specific_values(self):
        client = NginxProxyManagerClient("http://test:8080", "admin@example.com:password123")
        client._jwt = "cached-jwt"
        mock_transport = AsyncMock()
        mock_transport.headers = {"Authorization": "Bearer cached-jwt"}
        mock_transport.request = AsyncMock()
        client._client = mock_transport

        with pytest.raises(ToolExecutionError, match="Unsupported expand value"):
            await client.execute_tool("npm_list_certificates", {"expand": ["certificate"]})

        mock_transport.request.assert_not_called()

    async def test_query_validation_rejects_empty_values(self):
        client = NginxProxyManagerClient("http://test:8080", "admin@example.com:password123")
        client._jwt = "cached-jwt"
        mock_transport = AsyncMock()
        mock_transport.headers = {"Authorization": "Bearer cached-jwt"}
        mock_transport.request = AsyncMock()
        client._client = mock_transport

        with pytest.raises(ToolExecutionError, match="query must not be empty"):
            await client.execute_tool("npm_list_proxy_hosts", {"query": "   "})

        mock_transport.request.assert_not_called()

    async def test_request_reauthenticates_after_401(self):
        client = NginxProxyManagerClient("http://test:8080", "admin@example.com:password123")
        client._jwt = "stale-jwt"
        mock_transport = AsyncMock()
        mock_transport.headers = {"Authorization": "Bearer stale-jwt"}
        mock_transport.post = AsyncMock(
            return_value=_mock_response(
                {
                    "token": "fresh-jwt",
                    "expires": "2099-01-01T00:00:00.000Z",
                }
            )
        )
        mock_transport.request = AsyncMock(
            side_effect=[
                _mock_unauthorized_response(),
                _mock_response([{"id": 2, "domain_names": ["prod.example.com"]}]),
            ]
        )
        client._client = mock_transport

        result = await client.execute_tool("npm_list_proxy_hosts", {})

        assert result == [{"id": 2, "domain_names": ["prod.example.com"]}]
        assert client._jwt == "fresh-jwt"
        assert mock_transport.headers["Authorization"] == "Bearer fresh-jwt"
        assert mock_transport.request.await_count == 2
        mock_transport.post.assert_awaited_once_with(
            "/api/tokens",
            json={"identity": "admin@example.com", "secret": "password123"},
        )
