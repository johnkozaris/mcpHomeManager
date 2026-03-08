"""Targeted tests for the Wiki.js client."""

from unittest.mock import AsyncMock, MagicMock

from infrastructure.clients.wikijs_client import WikiJsClient


def _mock_response(json_data=None, text_data="", status_code=200):
    """Build a mock httpx response."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.headers = {"content-type": "application/json"}
    resp.json.return_value = json_data if json_data is not None else {}
    resp.text = text_data
    resp.raise_for_status = MagicMock()
    return resp


def _patch_client_transport(client: WikiJsClient) -> AsyncMock:
    """Replace the httpx AsyncClient with an AsyncMock."""
    mock = AsyncMock()
    mock.request = AsyncMock(return_value=_mock_response())
    mock.headers = {}
    client._client = mock
    return mock


class TestWikiJsClient:
    async def test_health_check_uses_official_pages_list_probe(self) -> None:
        client = WikiJsClient("http://test:8080", "my-api-key")
        mock = _patch_client_transport(client)
        mock.request.return_value = _mock_response({"data": {"pages": {"list": [{"id": 1}]}}})

        result = await client.health_check()

        assert result is True
        mock.request.assert_called_once()
        call_args = mock.request.call_args
        assert call_args.args == ("POST", "/graphql")
        assert call_args.kwargs["json"]["query"] == "{ pages { list(limit: 1) { id } } }"

    async def test_health_check_accepts_empty_page_list(self) -> None:
        client = WikiJsClient("http://test:8080", "my-api-key")
        mock = _patch_client_transport(client)
        mock.request.return_value = _mock_response({"data": {"pages": {"list": []}}})

        result = await client.health_check()

        assert result is True

    async def test_list_pages_requests_locale_metadata(self) -> None:
        client = WikiJsClient("http://test:8080", "my-api-key")
        mock = _patch_client_transport(client)
        mock.request.return_value = _mock_response(
            {
                "data": {
                    "pages": {
                        "list": [
                            {
                                "id": 1,
                                "path": "test",
                                "locale": "en",
                                "title": "Test",
                                "updatedAt": "2024-01-01",
                            }
                        ]
                    }
                }
            }
        )

        result = await client.execute_tool("wikijs_list_pages", {})

        assert result[0]["locale"] == "en"
        assert "locale" in mock.request.call_args.kwargs["json"]["query"]

    async def test_create_page_defaults_to_english_locale(self) -> None:
        client = WikiJsClient("http://test:8080", "my-api-key")
        mock = _patch_client_transport(client)
        mock.request.return_value = _mock_response(
            {
                "data": {
                    "pages": {
                        "create": {
                            "responseResult": {"succeeded": True, "errorCode": 0, "message": None},
                            "page": {
                                "id": 1,
                                "path": "docs/setup",
                                "locale": "en",
                                "title": "Setup",
                            },
                        }
                    }
                }
            }
        )

        result = await client.execute_tool(
            "wikijs_create_page",
            {"path": "docs/setup", "title": "Setup", "content": "# Setup"},
        )

        assert result["locale"] == "en"
        assert mock.request.call_args.kwargs["json"]["variables"]["locale"] == "en"

    async def test_create_page_allows_locale_override(self) -> None:
        client = WikiJsClient("http://test:8080", "my-api-key")
        mock = _patch_client_transport(client)
        mock.request.return_value = _mock_response(
            {
                "data": {
                    "pages": {
                        "create": {
                            "responseResult": {"succeeded": True, "errorCode": 0, "message": None},
                            "page": {
                                "id": 2,
                                "path": "docs/config",
                                "locale": "fr",
                                "title": "Config",
                            },
                        }
                    }
                }
            }
        )

        result = await client.execute_tool(
            "wikijs_create_page",
            {
                "path": "docs/config",
                "title": "Config",
                "content": "# Config",
                "locale": "fr",
            },
        )

        assert result["locale"] == "fr"
        assert mock.request.call_args.kwargs["json"]["variables"]["locale"] == "fr"

    async def test_search_allows_locale_and_path_filters(self) -> None:
        client = WikiJsClient("http://test:8080", "my-api-key")
        mock = _patch_client_transport(client)
        mock.request.return_value = _mock_response(
            {
                "data": {
                    "pages": {
                        "search": {
                            "results": [
                                {
                                    "id": "2",
                                    "title": "Config",
                                    "path": "docs/config",
                                    "locale": "fr",
                                    "description": "Configuration guide",
                                }
                            ],
                            "totalHits": 1,
                            "suggestions": [],
                        }
                    }
                }
            }
        )

        result = await client.execute_tool(
            "wikijs_search",
            {"query": "config", "path": "docs", "locale": "fr"},
        )

        assert result["results"][0]["locale"] == "fr"
        assert mock.request.call_args.kwargs["json"]["variables"] == {
            "query": "config",
            "path": "docs",
            "locale": "fr",
        }
        assert "$path: String" in mock.request.call_args.kwargs["json"]["query"]
        assert "$locale: String" in mock.request.call_args.kwargs["json"]["query"]

    def test_tool_descriptions_expose_permission_sensitive_tools(self) -> None:
        client = WikiJsClient("http://test:8080", "my-api-key")
        defs = {tool.name: tool for tool in client.get_tool_definitions()}

        assert "read:pages" in defs["wikijs_list_pages"].description
        assert "read:pages" in defs["wikijs_get_page"].description
        assert "read:source" in defs["wikijs_get_page"].description
        assert "write:pages" in defs["wikijs_create_page"].description
        assert "write:users" in defs["wikijs_list_users"].description
        assert "path" in defs["wikijs_search"].parameters_schema["properties"]
        assert "locale" in defs["wikijs_search"].parameters_schema["properties"]
