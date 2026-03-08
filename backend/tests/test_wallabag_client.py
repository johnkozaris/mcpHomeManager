"""Focused regression tests for the Wallabag client."""

import time
from unittest.mock import AsyncMock, MagicMock

from infrastructure.clients.wallabag_client import WallabagClient


def _mock_response(json_data=None, text_data="", status_code=200):
    resp = MagicMock()
    resp.status_code = status_code
    resp.headers = {"content-type": "application/json"}
    resp.json.return_value = json_data if json_data is not None else {}
    resp.text = text_data
    resp.raise_for_status = MagicMock()
    return resp


def _authenticated_client() -> WallabagClient:
    client = WallabagClient("http://test:8080", "cid:csecret:user:pass")
    client._access_token = "existing-token"
    client._token_expires_at = time.monotonic() + 3600
    return client


class TestWallabagClient:
    async def test_oauth_token_request_uses_form_headers_and_tracks_refresh_fields(self):
        client = WallabagClient("http://test:8080", "cid:csecret:user:p:a:s:s")
        mock_transport = AsyncMock()
        mock_transport.headers = {}
        mock_transport.post = AsyncMock(
            return_value=_mock_response(
                {
                    "access_token": "wall-token",
                    "refresh_token": "refresh-token",
                    "expires_in": 3600,
                    "token_type": "bearer",
                }
            )
        )
        client._client = mock_transport

        await client._ensure_token()

        call = mock_transport.post.call_args
        assert call.args[0] == "/oauth/v2/token"
        assert call.kwargs["headers"] == {
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        assert call.kwargs["data"] == {
            "grant_type": "password",
            "client_id": "cid",
            "client_secret": "csecret",
            "username": "user",
            "password": "p:a:s:s",
        }
        assert client._refresh_token == "refresh-token"
        assert client._token_expires_at is not None
        assert mock_transport.headers["Authorization"] == "Bearer wall-token"

    async def test_save_url_uses_query_params_not_json_body(self):
        client = _authenticated_client()
        mock_transport = AsyncMock()
        mock_transport.headers = {"Authorization": "Bearer existing-token"}
        mock_transport.request = AsyncMock(return_value=_mock_response({"id": 42}))
        client._client = mock_transport

        result = await client.execute_tool("wallabag_save_url", {"url": "https://example.com"})

        assert result == {"id": 42}
        call = mock_transport.request.call_args
        assert call.args == ("POST", "/api/entries.json")
        assert call.kwargs["params"] == {"url": "https://example.com"}
        assert "json" not in call.kwargs

    async def test_tag_entry_uses_query_params_not_json_body(self):
        client = _authenticated_client()
        mock_transport = AsyncMock()
        mock_transport.headers = {"Authorization": "Bearer existing-token"}
        mock_transport.request = AsyncMock(return_value=_mock_response({"tags": ["later"]}))
        client._client = mock_transport

        result = await client.execute_tool("wallabag_tag_entry", {"id": 12, "tags": "later"})

        assert result == {"tags": ["later"]}
        call = mock_transport.request.call_args
        assert call.args == ("POST", "/api/entries/12/tags.json")
        assert call.kwargs["params"] == {"tags": "later"}
        assert "json" not in call.kwargs

    async def test_expired_token_refreshes_before_request(self):
        client = WallabagClient("http://test:8080", "cid:csecret:user:pass")
        client._access_token = "expired-token"
        client._refresh_token = "refresh-1"
        client._token_expires_at = time.monotonic() - 1

        mock_transport = AsyncMock()
        mock_transport.headers = {"Authorization": "Bearer expired-token"}
        mock_transport.post = AsyncMock(
            return_value=_mock_response(
                {
                    "access_token": "fresh-token",
                    "refresh_token": "refresh-2",
                    "expires_in": 3600,
                    "token_type": "bearer",
                }
            )
        )
        mock_transport.request = AsyncMock(
            return_value=_mock_response({"_embedded": {"items": []}})
        )
        client._client = mock_transport

        result = await client.execute_tool("wallabag_list_entries", {})

        assert result == {"_embedded": {"items": []}}
        refresh_call = mock_transport.post.call_args
        assert refresh_call.kwargs["data"] == {
            "grant_type": "refresh_token",
            "client_id": "cid",
            "client_secret": "csecret",
            "refresh_token": "refresh-1",
        }
        assert mock_transport.headers["Authorization"] == "Bearer fresh-token"

    async def test_unauthorized_request_reauthenticates_and_retries(self):
        client = _authenticated_client()

        mock_transport = AsyncMock()
        mock_transport.headers = {"Authorization": "Bearer existing-token"}
        mock_transport.post = AsyncMock(
            return_value=_mock_response(
                {
                    "access_token": "renewed-token",
                    "refresh_token": "refresh-2",
                    "expires_in": 3600,
                    "token_type": "bearer",
                }
            )
        )
        mock_transport.request = AsyncMock(
            side_effect=[
                _mock_response({"error": "invalid_token"}, status_code=401),
                _mock_response({"_embedded": {"items": []}}),
            ]
        )
        client._client = mock_transport

        result = await client.execute_tool("wallabag_list_entries", {})

        assert result == {"_embedded": {"items": []}}
        assert mock_transport.request.await_count == 2
        assert mock_transport.post.await_count == 1
        assert mock_transport.headers["Authorization"] == "Bearer renewed-token"
