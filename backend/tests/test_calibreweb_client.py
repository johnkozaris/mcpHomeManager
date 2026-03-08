"""Tests for the CalibreWebClient."""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from domain.entities.service_connection import ServiceType
from domain.exceptions import ServiceConnectionError, ToolExecutionError
from infrastructure.clients.calibreweb_client import CalibreWebClient


def _mock_response(json_data=None, text_data="", status_code=200, headers=None):
    """Build a mock httpx response."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.headers = headers or {"content-type": "application/json"}
    resp.json.return_value = json_data if json_data is not None else {}
    resp.text = text_data or (
        json.dumps(json_data) if json_data is not None else ""
    )
    resp.raise_for_status = MagicMock()
    return resp


def _patch_client_transport(client):
    """Replace the httpx AsyncClient with an AsyncMock so no real HTTP calls are made."""
    mock = AsyncMock()
    mock.request = AsyncMock(return_value=_mock_response())
    mock.headers = {}
    client._client = mock
    return mock


def _login_page_html(csrf_token="csrf123", next_value="/", include_remember_me=True):
    remember_me = (
        '<input type="checkbox" name="remember_me" value="on">'
        if include_remember_me
        else ""
    )
    return f"""
    <form method="POST" action="/login">
        <input type="hidden" name="csrf_token" value="{csrf_token}">
        <input type="hidden" name="next" value="{next_value}">
        <input type="text" name="username">
        <input type="password" name="password">
        {remember_me}
    </form>
    """


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
                "totalNotFiltered": 2,
                "total": 2,
                "rows": [{"id": 1, "title": "Dune"}, {"id": 2, "title": "Neuromancer"}],
            }
        )

        result = await client.execute_tool("calibreweb_search_books", {"search": "sci-fi"})
        assert result == {
            "totalNotFiltered": 2,
            "total": 2,
            "rows": [{"id": 1, "title": "Dune"}, {"id": 2, "title": "Neuromancer"}],
        }
        mock.request.assert_called_once()

    async def test_list_authors(self):
        client = CalibreWebClient("http://test:8083", "admin:admin123")
        client._session_authenticated = True
        mock = _patch_client_transport(client)
        mock.request.return_value = _mock_response(
            [{"id": 1, "name": "Frank Herbert"}],
            headers={"content-type": "text/html; charset=utf-8"},
        )

        result = await client.execute_tool("calibreweb_list_authors", {"q": "herbert"})
        assert result == [{"id": 1, "name": "Frank Herbert"}]

    async def test_list_categories(self):
        client = CalibreWebClient("http://test:8083", "admin:admin123")
        client._session_authenticated = True
        mock = _patch_client_transport(client)
        mock.request.return_value = _mock_response(
            [{"id": 1, "name": "Science Fiction"}],
            headers={"content-type": "text/html; charset=utf-8"},
        )

        result = await client.execute_tool("calibreweb_list_categories", {})
        assert result == [{"id": 1, "name": "Science Fiction"}]

    async def test_list_series(self):
        client = CalibreWebClient("http://test:8083", "admin:admin123")
        client._session_authenticated = True
        mock = _patch_client_transport(client)
        mock.request.return_value = _mock_response(
            [{"id": 1, "name": "Dune Chronicles"}],
            headers={"content-type": "text/html; charset=utf-8"},
        )

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
        login_page = _mock_response(
            text_data=_login_page_html(csrf_token="csrf456", next_value="/books"),
            headers={"content-type": "text/html; charset=utf-8"},
        )
        login_resp = _mock_response(
            text_data="",
            status_code=302,
            headers={"content-type": "text/html; charset=utf-8", "location": "/"},
        )
        mock_transport.get = AsyncMock(return_value=login_page)
        mock_transport.post = AsyncMock(return_value=login_resp)
        client._client = mock_transport

        await client._ensure_session()
        assert client._session_authenticated is True
        mock_transport.get.assert_called_once_with("/login", follow_redirects=False)
        mock_transport.post.assert_called_once_with(
            "/login",
            data={
                "username": "admin",
                "password": "admin123",
                "csrf_token": "csrf456",
                "next": "/books",
                "remember_me": "on",
            },
            follow_redirects=False,
        )

    async def test_ensure_session_rejects_login_page_after_post(self):
        client = CalibreWebClient("http://test:8083", "admin:wrongpass")
        mock_transport = AsyncMock()
        mock_transport.headers = {}
        mock_transport.get = AsyncMock(
            return_value=_mock_response(
                text_data=_login_page_html(),
                headers={"content-type": "text/html; charset=utf-8"},
            )
        )
        mock_transport.post = AsyncMock(
            return_value=_mock_response(
                text_data=_login_page_html(),
                headers={"content-type": "text/html; charset=utf-8"},
            )
        )
        client._client = mock_transport

        with pytest.raises(ServiceConnectionError, match="Login failed"):
            await client._ensure_session()
        assert client._session_authenticated is False

    async def test_request_reauthenticates_on_login_redirect(self):
        client = CalibreWebClient("http://test:8083", "admin:admin123")
        client._session_authenticated = True
        mock_transport = AsyncMock()
        mock_transport.headers = {}
        mock_transport.request = AsyncMock(
            side_effect=[
                _mock_response(
                    text_data="",
                    status_code=302,
                    headers={"content-type": "text/html; charset=utf-8", "location": "/login"},
                ),
                _mock_response({"rows": []}),
            ]
        )
        mock_transport.get = AsyncMock(
            return_value=_mock_response(
                text_data=_login_page_html(csrf_token="csrf789"),
                headers={"content-type": "text/html; charset=utf-8"},
            )
        )
        mock_transport.post = AsyncMock(
            return_value=_mock_response(
                text_data="",
                status_code=302,
                headers={"content-type": "text/html; charset=utf-8", "location": "/"},
            )
        )
        client._client = mock_transport

        result = await client.execute_tool("calibreweb_search_books", {})

        assert result == {"rows": []}
        assert mock_transport.request.await_count == 2
        mock_transport.get.assert_called_once_with("/login", follow_redirects=False)
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

    async def test_health_check_requires_success_status(self):
        client = CalibreWebClient("http://test:8083", "admin:admin123")
        mock_transport = AsyncMock()
        mock_transport.request = AsyncMock(
            side_effect=[
                _mock_response(
                    text_data="<feed />",
                    status_code=200,
                    headers={"content-type": "application/atom+xml"},
                ),
                _mock_response(
                    text_data="Unauthorized",
                    status_code=401,
                    headers={"content-type": "text/plain"},
                ),
            ]
        )
        client._client = mock_transport

        assert await client.health_check() is True
        assert await client.health_check() is False
