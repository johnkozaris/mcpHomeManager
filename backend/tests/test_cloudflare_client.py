"""Tests for the Cloudflare service client."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from domain.entities.service_connection import ServiceType
from domain.exceptions import ToolExecutionError
from infrastructure.clients.cloudflare_client import CloudflareClient


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


class TestCloudflareClient:
    def test_get_tool_definitions(self):
        client = CloudflareClient("https://api.cloudflare.com", "my-api-token")
        defs = client.get_tool_definitions()
        assert len(defs) == 5
        assert all(d.service_type == ServiceType.CLOUDFLARE for d in defs)

    async def test_unknown_tool_raises(self):
        client = CloudflareClient("https://api.cloudflare.com", "my-api-token")
        with pytest.raises(ToolExecutionError, match="Unknown tool"):
            await client.execute_tool("nonexistent", {})
        await client.close()

    async def test_health_check(self):
        client = CloudflareClient("https://api.cloudflare.com", "my-api-token")
        mock = _patch_client_transport(client)
        mock.request.return_value = _mock_response(
            {"result": {"id": "abc123", "status": "active"}, "success": True}
        )

        result = await client.health_check()
        assert result is True
        mock.request.assert_called_once()

    async def test_health_check_inactive_token(self):
        client = CloudflareClient("https://api.cloudflare.com", "my-api-token")
        mock = _patch_client_transport(client)
        mock.request.return_value = _mock_response(
            {"result": {"id": "abc123", "status": "expired"}, "success": False}
        )

        result = await client.health_check()
        assert result is False

    async def test_list_zones(self):
        client = CloudflareClient("https://api.cloudflare.com", "my-api-token")
        mock = _patch_client_transport(client)
        zones_response = {
            "result": [{"id": "zone1", "name": "example.com", "status": "active"}],
            "success": True,
            "result_info": {"page": 1, "per_page": 20, "total_count": 1},
        }
        mock.request.return_value = _mock_response(zones_response)

        result = await client.execute_tool("cloudflare_list_zones", {})
        assert result == zones_response
        mock.request.assert_called_once()

    async def test_list_dns_records(self):
        client = CloudflareClient("https://api.cloudflare.com", "my-api-token")
        mock = _patch_client_transport(client)
        dns_response = {
            "result": [{"id": "rec1", "type": "A", "name": "example.com", "content": "1.2.3.4"}],
            "success": True,
        }
        mock.request.return_value = _mock_response(dns_response)

        result = await client.execute_tool(
            "cloudflare_list_dns_records", {"zone_id": "zone1", "type": "A"}
        )
        assert result == dns_response
        mock.request.assert_called_once()

    async def test_create_dns_record(self):
        client = CloudflareClient("https://api.cloudflare.com", "my-api-token")
        mock = _patch_client_transport(client)
        create_response = {
            "result": {"id": "rec2", "type": "A", "name": "sub.example.com", "content": "5.6.7.8"},
            "success": True,
        }
        mock.request.return_value = _mock_response(create_response)

        result = await client.execute_tool(
            "cloudflare_create_dns_record",
            {
                "zone_id": "zone1",
                "type": "A",
                "name": "sub.example.com",
                "content": "5.6.7.8",
                "proxied": True,
            },
        )
        assert result == create_response
        mock.request.assert_called_once()

    async def test_list_tunnels(self):
        client = CloudflareClient("https://api.cloudflare.com", "my-api-token")
        mock = _patch_client_transport(client)
        tunnels_response = {
            "result": [{"id": "tun1", "name": "my-tunnel", "status": "healthy"}],
            "success": True,
        }
        mock.request.return_value = _mock_response(tunnels_response)

        result = await client.execute_tool("cloudflare_list_tunnels", {"account_id": "acc123"})
        assert result == tunnels_response
        mock.request.assert_called_once()

    async def test_get_tunnel(self):
        client = CloudflareClient("https://api.cloudflare.com", "my-api-token")
        mock = _patch_client_transport(client)
        tunnel_response = {
            "result": {"id": "tun1", "name": "my-tunnel", "status": "healthy"},
            "success": True,
        }
        mock.request.return_value = _mock_response(tunnel_response)

        result = await client.execute_tool(
            "cloudflare_get_tunnel", {"account_id": "acc123", "tunnel_id": "tun1"}
        )
        assert result == tunnel_response
        mock.request.assert_called_once()

    async def test_build_headers_uses_bearer(self):
        client = CloudflareClient("https://api.cloudflare.com", "my-api-token")
        headers = client._build_headers("test-token")
        assert headers["Authorization"] == "Bearer test-token"
        assert headers["Accept"] == "application/json"
