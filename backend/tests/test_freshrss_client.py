"""Tests for the FreshRSS client."""

from unittest.mock import AsyncMock, MagicMock, call

import pytest

from infrastructure.clients.freshrss_client import FreshRSSClient


def _mock_response(
    json_data=None,
    text_data: str = "",
    status_code: int = 200,
    content_type: str = "application/json",
):
    resp = MagicMock()
    resp.status_code = status_code
    resp.headers = {"content-type": content_type}
    resp.json.return_value = json_data if json_data is not None else {}
    resp.text = text_data
    resp.raise_for_status = MagicMock()
    return resp


def _patch_client_transport(client: FreshRSSClient) -> AsyncMock:
    mock = AsyncMock()
    mock.request = AsyncMock(return_value=_mock_response())
    mock.post = AsyncMock(return_value=_mock_response(text_data="Auth=user/auth-token"))
    mock.headers = {}
    client._client = mock
    return mock


@pytest.mark.parametrize(
    ("configured_base_url", "expected_client_base", "expected_greader_path"),
    [
        ("http://test:8080", "http://test:8080", "/api/greader.php"),
        ("http://test:8080/freshrss", "http://test:8080", "/freshrss/api/greader.php"),
        (
            "http://test:8080/freshrss/api/greader.php",
            "http://test:8080",
            "/freshrss/api/greader.php",
        ),
    ],
)
def test_normalizes_base_url(configured_base_url, expected_client_base, expected_greader_path):
    client = FreshRSSClient(configured_base_url, "user:password")
    try:
        assert client._base_url == expected_client_base
        assert client._greader_base_path == expected_greader_path
    finally:
        import asyncio

        asyncio.run(client.close())


@pytest.mark.parametrize("configured_base_url", ["http://test:8080/freshrss", "http://test:8080/freshrss/api/greader.php"])
async def test_list_feeds_uses_normalized_greader_path(configured_base_url):
    client = FreshRSSClient(configured_base_url, "user:password")
    mock = _patch_client_transport(client)
    mock.request.return_value = _mock_response({"subscriptions": []})

    result = await client.execute_tool("freshrss_list_feeds", {})

    assert result == {"subscriptions": []}
    mock.post.assert_awaited_once_with(
        "/freshrss/api/greader.php/accounts/ClientLogin",
        data={"Email": "user", "Passwd": "password"},
    )
    mock.request.assert_awaited_once_with(
        "GET",
        "/freshrss/api/greader.php/reader/api/0/subscription/list",
        params={"output": "json"},
    )
    await client.close()


@pytest.mark.parametrize(
    ("tool_name", "arguments", "expected_payload"),
    [
        (
            "freshrss_mark_read",
            {"item_id": "item-123"},
            {"i": "item-123", "a": "user/-/state/com.google/read", "T": "write-token"},
        ),
        (
            "freshrss_star_article",
            {"item_id": "item-456"},
            {"i": "item-456", "a": "user/-/state/com.google/starred", "T": "write-token"},
        ),
    ],
)
async def test_mutations_fetch_and_send_write_token(tool_name, arguments, expected_payload):
    client = FreshRSSClient("http://test:8080/api/greader.php", "user:password")
    client._auth_token = "auth-token"
    mock = _patch_client_transport(client)
    mock.request.side_effect = [
        _mock_response(text_data="write-token\n", content_type="text/plain"),
        _mock_response(text_data="OK", content_type="text/plain"),
    ]

    result = await client.execute_tool(tool_name, arguments)

    assert result == "OK"
    assert mock.request.await_args_list == [
        call("GET", "/api/greader.php/reader/api/0/token"),
        call("POST", "/api/greader.php/reader/api/0/edit-tag", data=expected_payload),
    ]
    await client.close()


async def test_add_feed_posts_form_data_without_write_token():
    client = FreshRSSClient("http://test:8080/api/greader.php", "user:password")
    client._auth_token = "auth-token"
    mock = _patch_client_transport(client)
    mock.request.return_value = _mock_response(
        text_data='{"numResults":1,"query":"https://example.com/feed.xml"}',
        content_type="text/html; charset=UTF-8",
    )

    result = await client.execute_tool("freshrss_add_feed", {"url": "https://example.com/feed.xml"})

    assert result == {"numResults": 1, "query": "https://example.com/feed.xml"}
    mock.request.assert_awaited_once_with(
        "POST",
        "/api/greader.php/reader/api/0/subscription/quickadd",
        data={"quickadd": "https://example.com/feed.xml"},
    )
    await client.close()
