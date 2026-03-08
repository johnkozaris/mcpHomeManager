import base64
import json
import time
from unittest.mock import AsyncMock, MagicMock

import httpx

from infrastructure.clients.portainer_client import PortainerClient


def _mock_response(json_data=None, text_data="", status_code=200):
    response = MagicMock()
    response.status_code = status_code
    response.headers = {"content-type": "application/json"}
    response.json.return_value = json_data if json_data is not None else {}
    response.text = text_data
    response.raise_for_status = MagicMock()
    return response


def _mock_unauthorized_response() -> MagicMock:
    request = httpx.Request("GET", "http://test:8080/api/endpoints")
    response = httpx.Response(401, request=request, text="unauthorized")
    mocked = MagicMock()
    mocked.status_code = 401
    mocked.headers = {"content-type": "application/json"}
    mocked.text = "unauthorized"
    mocked.raise_for_status.side_effect = httpx.HTTPStatusError(
        "401 unauthorized", request=request, response=response
    )
    return mocked


def _make_jwt(expiry: float) -> str:
    header = base64.urlsafe_b64encode(b'{"alg":"HS256","typ":"JWT"}').decode().rstrip("=")
    payload = base64.urlsafe_b64encode(json.dumps({"exp": expiry}).encode()).decode().rstrip("=")
    return f"{header}.{payload}.signature"


class TestPortainerApiKeyAuth:
    async def test_api_key_sets_x_api_key_header(self):
        client = PortainerClient("http://test:8080", "portainer-access-token")
        api_key_header = client._client.headers["X-API-Key"]
        mock_transport = AsyncMock()
        mock_transport.headers = {"Content-Type": "application/json", "X-API-Key": api_key_header}
        mock_transport.post = AsyncMock()
        mock_transport.request = AsyncMock(
            return_value=_mock_response([{"Id": 1, "Name": "local"}])
        )
        client._client = mock_transport

        result = await client.execute_tool("portainer_list_endpoints", {})

        assert result == [{"Id": 1, "Name": "local"}]
        assert mock_transport.headers["X-API-Key"] == "portainer-access-token"
        assert "Authorization" not in mock_transport.headers
        mock_transport.post.assert_not_called()


class TestPortainerJwtFallback:
    async def test_ensure_jwt_refreshes_expiring_token(self):
        client = PortainerClient("http://test:8080", "admin:password123")
        expiring_jwt = _make_jwt(time.time() + 30)
        refreshed_jwt = _make_jwt(time.time() + 3600)
        mock_transport = AsyncMock()
        mock_transport.headers = {}
        mock_transport.post = AsyncMock(return_value=_mock_response({"jwt": refreshed_jwt}))
        client._client = mock_transport
        client._set_jwt(expiring_jwt)

        await client._ensure_jwt()

        assert client._jwt == refreshed_jwt
        assert client._jwt_expires_at is not None
        assert client._jwt_expires_at > time.time() + 3000
        assert mock_transport.headers["Authorization"] == f"Bearer {refreshed_jwt}"
        mock_transport.post.assert_awaited_once()

    async def test_request_reauthenticates_after_401(self):
        client = PortainerClient("http://test:8080", "admin:password123")
        stale_jwt = _make_jwt(time.time() + 3600)
        refreshed_jwt = _make_jwt(time.time() + 7200)
        mock_transport = AsyncMock()
        mock_transport.headers = {}
        mock_transport.post = AsyncMock(return_value=_mock_response({"jwt": refreshed_jwt}))
        mock_transport.request = AsyncMock(
            side_effect=[
                _mock_unauthorized_response(),
                _mock_response([{"Id": 2, "Name": "prod"}]),
            ]
        )
        client._client = mock_transport
        client._set_jwt(stale_jwt)

        result = await client.execute_tool("portainer_list_endpoints", {})

        assert result == [{"Id": 2, "Name": "prod"}]
        assert client._jwt == refreshed_jwt
        assert mock_transport.headers["Authorization"] == f"Bearer {refreshed_jwt}"
        assert mock_transport.request.await_count == 2
        mock_transport.post.assert_awaited_once()
