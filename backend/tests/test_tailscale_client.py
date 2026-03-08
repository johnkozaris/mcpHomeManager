"""Tests for the Tailscale client."""

import base64
from unittest.mock import AsyncMock, MagicMock

import pytest

from domain.entities.service_connection import ServiceType
from domain.exceptions import ToolExecutionError
from infrastructure.clients.tailscale_client import TailscaleClient


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


class TestTailscaleClient:
    def test_get_tool_definitions(self):
        client = TailscaleClient("https://api.tailscale.com/api/v2", "tskey-api-test")
        defs = client.get_tool_definitions()
        assert len(defs) == 5
        assert all(d.service_type == ServiceType.TAILSCALE for d in defs)
        list_devices = next(d for d in defs if d.name == "tailscale_list_devices")
        assert "filters" in list_devices.parameters_schema["properties"]
        get_device = next(d for d in defs if d.name == "tailscale_get_device")
        assert "fields" in get_device.parameters_schema["properties"]

    async def test_unknown_tool_raises(self):
        client = TailscaleClient("https://api.tailscale.com/api/v2", "tskey-api-test")
        with pytest.raises(ToolExecutionError, match="Unknown tool"):
            await client.execute_tool("nonexistent", {})
        await client.close()

    async def test_health_check(self):
        client = TailscaleClient("https://api.tailscale.com/api/v2", "tskey-api-test")
        mock = _patch_client_transport(client)
        mock.request.return_value = _mock_response(
            {"devices": [{"id": "123", "hostname": "node1"}]}
        )

        result = await client.health_check()
        assert result is True
        mock.request.assert_called_once()

    def test_basic_auth_header(self):
        token = "tskey-api-kABC123"
        client = TailscaleClient("https://api.tailscale.com/api/v2", token)
        headers = client._build_headers(token)
        expected = base64.b64encode(f"{token}:".encode()).decode()
        assert headers["Authorization"] == f"Basic {expected}"
        assert headers["Accept"] == "application/json"

    async def test_list_devices(self):
        client = TailscaleClient("https://api.tailscale.com/api/v2", "tskey-api-test")
        mock = _patch_client_transport(client)
        mock.request.return_value = _mock_response({"devices": [{"id": "1", "hostname": "laptop"}]})

        result = await client.execute_tool(
            "tailscale_list_devices",
            {
                "fields": "all",
                "filters": {
                    "hostname": "laptop",
                    "authorized": True,
                    "tags": ["tag:prod", "tag:router"],
                },
            },
        )
        assert result == {"devices": [{"id": "1", "hostname": "laptop"}]}
        call_args = mock.request.call_args
        assert call_args[0][0] == "GET"
        assert "/tailnet/-/devices" in call_args[0][1]
        assert call_args.kwargs["params"] == {
            "fields": "all",
            "hostname": "laptop",
            "authorized": "true",
            "tags": ["tag:prod", "tag:router"],
        }

    async def test_list_devices_rejects_invalid_filter_name(self):
        client = TailscaleClient("https://api.tailscale.com/api/v2", "tskey-api-test")

        with pytest.raises(ToolExecutionError, match="Invalid filter name"):
            await client.execute_tool(
                "tailscale_list_devices",
                {"filters": {"nested.field": "value"}},
            )

    async def test_list_devices_rejects_non_object_filters(self):
        client = TailscaleClient("https://api.tailscale.com/api/v2", "tskey-api-test")

        with pytest.raises(ToolExecutionError, match="filters must be an object"):
            await client.execute_tool(
                "tailscale_list_devices",
                {"filters": []},
            )

    async def test_get_device(self):
        client = TailscaleClient("https://api.tailscale.com/api/v2", "tskey-api-test")
        mock = _patch_client_transport(client)
        mock.request.return_value = _mock_response({"id": "abc123", "hostname": "server"})

        result = await client.execute_tool(
            "tailscale_get_device", {"device_id": "abc123", "fields": "all"}
        )
        assert result == {"id": "abc123", "hostname": "server"}
        call_args = mock.request.call_args
        assert call_args[0][0] == "GET"
        assert "/device/abc123" in call_args[0][1]
        assert call_args.kwargs["params"] == {"fields": "all"}

    async def test_authorize_device(self):
        client = TailscaleClient("https://api.tailscale.com/api/v2", "tskey-api-test")
        mock = _patch_client_transport(client)
        mock.request.return_value = _mock_response({})

        await client.execute_tool(
            "tailscale_authorize_device", {"device_id": "abc123", "authorized": True}
        )
        call_args = mock.request.call_args
        assert call_args[0][0] == "POST"
        assert "/device/abc123/authorized" in call_args[0][1]

    async def test_list_dns_nameservers(self):
        client = TailscaleClient("https://api.tailscale.com/api/v2", "tskey-api-test")
        mock = _patch_client_transport(client)
        mock.request.return_value = _mock_response({"dns": ["1.1.1.1", "8.8.8.8"]})

        result = await client.execute_tool("tailscale_list_dns_nameservers", {})
        assert result == {"dns": ["1.1.1.1", "8.8.8.8"]}
