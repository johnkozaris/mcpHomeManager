"""Tests for the Stirling PDF client."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from domain.entities.service_connection import ServiceType
from domain.exceptions import ToolExecutionError
from infrastructure.clients.stirlingpdf_client import StirlingPdfClient


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


class TestStirlingPdfClient:
    def test_get_tool_definitions(self):
        client = StirlingPdfClient("http://test:8080", "my-api-key")
        defs = client.get_tool_definitions()

        assert len(defs) == 2
        assert all(d.service_type == ServiceType.STIRLING_PDF for d in defs)
        assert defs[0].name == "stirling_health"
        assert defs[0].path_template == "/api/v1/info/status"

    async def test_unknown_tool_raises(self):
        client = StirlingPdfClient("http://test:8080", "my-api-key")

        with pytest.raises(ToolExecutionError, match="Unknown tool"):
            await client.execute_tool("nonexistent", {})

        await client.close()

    async def test_health_tool_uses_info_status_endpoint(self):
        client = StirlingPdfClient("http://test:8080", "my-api-key")
        mock = _patch_client_transport(client)
        mock.request.return_value = _mock_response({"status": "UP", "version": "1.2.3"})

        result = await client.execute_tool("stirling_health", {})

        assert result == {"status": "UP", "version": "1.2.3"}
        mock.request.assert_called_once_with("GET", "/api/v1/info/status")

    async def test_health_check_requires_up_status(self):
        client = StirlingPdfClient("http://test:8080", "my-api-key")
        mock = _patch_client_transport(client)
        mock.request.return_value = _mock_response({"status": "UP", "version": "1.2.3"})

        result = await client.health_check()

        assert result is True
        mock.request.assert_called_once_with("GET", "/api/v1/info/status")

    async def test_health_check_returns_false_for_non_up_status(self):
        client = StirlingPdfClient("http://test:8080", "my-api-key")
        mock = _patch_client_transport(client)
        mock.request.return_value = _mock_response({"status": "DOWN", "version": "1.2.3"})

        result = await client.health_check()

        assert result is False

    async def test_health_tool_rejects_malformed_info_response(self):
        client = StirlingPdfClient("http://test:8080", "my-api-key")
        mock = _patch_client_transport(client)
        mock.request.return_value = _mock_response({"version": "1.2.3"})

        with pytest.raises(ToolExecutionError, match="Missing Info API status value"):
            await client.execute_tool("stirling_health", {})

    async def test_get_operations_returns_static_dict(self):
        client = StirlingPdfClient("http://test:8080", "my-api-key")

        result = await client.execute_tool("stirling_get_operations", {})

        assert isinstance(result, dict)
        assert result["coverage"] == "representative_subset"
        assert result["documentation"]["local_swagger_ui"] == "/swagger-ui/index.html"
        assert (
            result["documentation"]["online_api_docs"]
            == "https://registry.scalar.com/@stirlingpdf/apis/stirling-pdf-processing-api/"
        )
        assert "operations" in result
        assert "merge_pdfs" in result["operations"]
        assert "API or web UI directly" in result["note"]
