"""Tests for the CalibreWebClient."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from domain.entities.service_connection import ServiceType
from domain.exceptions import ServiceConnectionError, ToolExecutionError
from infrastructure.clients.calibreweb_client import CalibreWebClient


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


class TestCalibreWebClient:
    def test_get_tool_definitions(self):
        client = CalibreWebClient("http://test:8083", "admin:admin123")
        defs = client.get_tool_definitions()
        assert len(defs) == 5
        assert all(d.service_type == ServiceType.CALIBRE_WEB for d in defs)

    async def test_unknown_tool_raises(self):
        client = CalibreWebClient("http://test:8083", "admin:admin123")
        client._session_authenticated = True
        with pytest.raises(ToolExecutionError, match="Unknown tool"):
            await client.execute_tool("nonexistent", {})
        await client.close()

    async def test_search_books(self):
        client = CalibreWebClient("http://test:8083", "admin:admin123")
        client._session_authenticated = True
        mock = _patch_client_transport(client)
        mock.request.return_value = _mock_response(
            {
                "totalBooks": 2,
                "rows": [{"id": 1, "title": "Dune"}, {"id": 2, "title": "Neuromancer"}],
            }
        )

        result = await client.execute_tool("calibreweb_search_books", {"search": "sci-fi"})
        assert result == {
            "totalBooks": 2,
            "rows": [{"id": 1, "title": "Dune"}, {"id": 2, "title": "Neuromancer"}],
        }
        mock.request.assert_called_once()

    async def test_list_authors(self):
        client = CalibreWebClient("http://test:8083", "admin:admin123")
        client._session_authenticated = True
        mock = _patch_client_transport(client)
        mock.request.return_value = _mock_response([{"id": 1, "name": "Frank Herbert"}])

        result = await client.execute_tool("calibreweb_list_authors", {"q": "herbert"})
        assert result == [{"id": 1, "name": "Frank Herbert"}]

    async def test_list_categories(self):
        client = CalibreWebClient("http://test:8083", "admin:admin123")
        client._session_authenticated = True
        mock = _patch_client_transport(client)
        mock.request.return_value = _mock_response([{"id": 1, "name": "Science Fiction"}])

        result = await client.execute_tool("calibreweb_list_categories", {})
        assert result == [{"id": 1, "name": "Science Fiction"}]

    async def test_list_series(self):
        client = CalibreWebClient("http://test:8083", "admin:admin123")
        client._session_authenticated = True
        mock = _patch_client_transport(client)
        mock.request.return_value = _mock_response([{"id": 1, "name": "Dune Chronicles"}])

        result = await client.execute_tool("calibreweb_list_series", {})
        assert result == [{"id": 1, "name": "Dune Chronicles"}]

    async def test_toggle_read(self):
        client = CalibreWebClient("http://test:8083", "admin:admin123")
        client._session_authenticated = True
        mock = _patch_client_transport(client)
        mock.request.return_value = _mock_response("")

        result = await client.execute_tool("calibreweb_toggle_read", {"book_id": 42})
        assert result == ""
        mock.request.assert_called_once()
        call_args = mock.request.call_args
        assert call_args[0][0] == "POST"
        assert "/ajax/toggleread/42" in call_args[0][1]

    async def test_invalid_token_format_raises(self):
        client = CalibreWebClient("http://test:8083", "no-colon-here")
        mock_transport = AsyncMock()
        mock_transport.headers = {}
        client._client = mock_transport

        with pytest.raises(ServiceConnectionError, match="username:password"):
            await client._ensure_session()

    async def test_ensure_session_authenticates(self):
        client = CalibreWebClient("http://test:8083", "admin:admin123")
        mock_transport = AsyncMock()
        mock_transport.headers = {}
        # Simulate a successful login redirect (302)
        login_resp = MagicMock()
        login_resp.status_code = 302
        login_resp.text = ""
        mock_transport.post = AsyncMock(return_value=login_resp)
        client._client = mock_transport

        await client._ensure_session()
        assert client._session_authenticated is True
        mock_transport.post.assert_called_once()

    async def test_ensure_session_skips_when_already_authenticated(self):
        client = CalibreWebClient("http://test:8083", "admin:admin123")
        client._session_authenticated = True
        mock_transport = AsyncMock()
        client._client = mock_transport

        await client._ensure_session()
        # post should not be called since we're already authenticated
        mock_transport.post.assert_not_called()
        assert client._session_authenticated is True
