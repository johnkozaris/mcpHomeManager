"""Tests for the AdGuard Home client."""

import base64
from unittest.mock import AsyncMock, MagicMock

import pytest

from domain.entities.service_connection import ServiceType
from domain.exceptions import ToolExecutionError
from infrastructure.clients.adguard_client import AdGuardClient


def _mock_response(json_data=None, text_data="", status_code=200):
    """Build a mock httpx response."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.headers = {"content-type": "application/json"}
    resp.json.return_value = json_data if json_data is not None else {}
    resp.text = text_data
    resp.raise_for_status = MagicMock()
    return resp


def _patch_client_transport(client: AdGuardClient):
    """Replace the httpx AsyncClient with an AsyncMock so no real HTTP calls are made."""
    mock = AsyncMock()
    mock.request = AsyncMock(return_value=_mock_response())
    mock.headers = {}
    client._client = mock
    return mock


class TestAdGuardClient:
    def test_get_tool_definitions(self):
        client = AdGuardClient("http://adguard.local", "admin:password")
        defs = client.get_tool_definitions()

        assert len(defs) == 6
        assert all(d.service_type == ServiceType.ADGUARD for d in defs)
        query_log = next(d for d in defs if d.name == "adguard_query_log")
        assert {
            "older_than",
            "offset",
            "limit",
            "search",
            "response_status",
        }.issubset(query_log.parameters_schema["properties"])
        assert (
            query_log.parameters_schema["properties"]["search"]["description"]
            == "Filter by domain name or client IP"
        )
        stats = next(d for d in defs if d.name == "adguard_stats")
        assert "recent" in stats.parameters_schema["properties"]
        toggle = next(d for d in defs if d.name == "adguard_toggle_protection")
        assert toggle.path_template == "/control/protection"
        assert toggle.parameters_schema["required"] == ["enabled"]
        assert "duration_ms" in toggle.parameters_schema["properties"]

    def test_basic_auth_header(self):
        token = "admin:mypass"
        client = AdGuardClient("http://adguard.local", token)

        headers = client._build_headers(token)

        expected = base64.b64encode(token.encode()).decode()
        assert headers["Authorization"] == f"Basic {expected}"
        assert headers["Accept"] == "application/json"

    async def test_health_check_uses_status_endpoint(self):
        client = AdGuardClient("http://adguard.local", "admin:password")
        mock = _patch_client_transport(client)
        mock.request.return_value = _mock_response({"version": "v0.107.0"})

        result = await client.health_check()

        assert result is True
        mock.request.assert_called_once_with("GET", "/control/status")

    async def test_query_log_passes_documented_params(self):
        client = AdGuardClient("http://adguard.local", "admin:password")
        mock = _patch_client_transport(client)
        mock.request.return_value = _mock_response({"data": []})

        result = await client.execute_tool(
            "adguard_query_log",
            {
                "older_than": "cursor-123",
                "offset": 10,
                "limit": 25,
                "search": "192.168.1.10",
                "response_status": "blocked",
            },
        )

        assert result == {"data": []}
        mock.request.assert_called_once_with(
            "GET",
            "/control/querylog",
            params={
                "older_than": "cursor-123",
                "offset": 10,
                "limit": 25,
                "search": "192.168.1.10",
                "response_status": "blocked",
            },
        )

    async def test_stats_passes_recent_param(self):
        client = AdGuardClient("http://adguard.local", "admin:password")
        mock = _patch_client_transport(client)
        mock.request.return_value = _mock_response({"num_dns_queries": 42})

        result = await client.execute_tool(
            "adguard_stats",
            {"recent": 3_600_000},
        )

        assert result == {"num_dns_queries": 42}
        mock.request.assert_called_once_with(
            "GET",
            "/control/stats",
            params={"recent": 3_600_000},
        )

    @pytest.mark.parametrize(
        ("arguments", "expected_json"),
        [
            ({"enabled": False}, {"enabled": False}),
            (
                {"enabled": False, "duration_ms": 60_000},
                {"enabled": False, "duration": 60_000},
            ),
        ],
    )
    async def test_toggle_protection_uses_dedicated_endpoint(
        self,
        arguments,
        expected_json,
    ):
        client = AdGuardClient("http://adguard.local", "admin:password")
        mock = _patch_client_transport(client)
        mock.request.return_value = _mock_response({})

        result = await client.execute_tool("adguard_toggle_protection", arguments)

        assert result == {}
        mock.request.assert_called_once_with(
            "POST",
            "/control/protection",
            json=expected_json,
        )

    async def test_unknown_tool_raises(self):
        client = AdGuardClient("http://adguard.local", "admin:password")

        with pytest.raises(ToolExecutionError, match="Unknown tool"):
            await client.execute_tool("nonexistent", {})

        await client.close()
