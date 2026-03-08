"""Tests for the PaperlessClient."""

from unittest.mock import AsyncMock, MagicMock, call

import pytest

from domain.entities.service_connection import ServiceType
from infrastructure.clients.paperless_client import PaperlessClient


def _mock_response(json_data=None, text_data="", status_code=200):
    """Build a mock httpx response."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.headers = {"content-type": "application/json"}
    resp.json.return_value = json_data if json_data is not None else {}
    resp.text = text_data
    resp.raise_for_status = MagicMock()
    return resp


def _patch_client_transport(client: PaperlessClient) -> AsyncMock:
    """Replace the httpx AsyncClient with an AsyncMock so no real HTTP calls are made."""
    mock = AsyncMock()
    mock.request = AsyncMock(return_value=_mock_response())
    mock.headers = {}
    client._client = mock
    return mock


class TestPaperlessClient:
    def test_get_tool_definitions(self) -> None:
        client = PaperlessClient("http://test:8000", "paperless-token")
        defs = client.get_tool_definitions()
        search_tool = next(d for d in defs if d.name == "paperless_search_documents")

        assert len(defs) == 5
        assert all(d.service_type == ServiceType.PAPERLESS for d in defs)
        assert search_tool.parameters_schema["properties"]["page_size"]["default"] == 25

    def test_build_headers_uses_unversioned_json_accept(self) -> None:
        client = PaperlessClient("http://test:8000", "paperless-token")

        assert client._build_headers("paperless-token") == {
            "Authorization": "Token paperless-token",
            "Accept": "application/json",
        }

    async def test_health_check_uses_documents_endpoint(self) -> None:
        client = PaperlessClient("http://test:8000", "paperless-token")
        mock = _patch_client_transport(client)
        mock.request.return_value = _mock_response({"count": 42, "results": []})

        result = await client.health_check()

        assert result is True
        mock.request.assert_awaited_once_with(
            "GET",
            "/api/documents/",
            params={"page": 1, "page_size": 1},
        )

    async def test_health_check_returns_false_for_unexpected_payload(self) -> None:
        client = PaperlessClient("http://test:8000", "paperless-token")
        mock = _patch_client_transport(client)
        mock.request.return_value = _mock_response({"detail": "ok"})

        result = await client.health_check()

        assert result is False

    async def test_search_documents_uses_paperless_default_page_size(self) -> None:
        client = PaperlessClient("http://test:8000", "paperless-token")
        mock = _patch_client_transport(client)
        mock.request.return_value = _mock_response({"count": 0, "results": []})

        await client.execute_tool("paperless_search_documents", {"query": "invoice"})

        mock.request.assert_awaited_once_with(
            "GET",
            "/api/documents/",
            params={"query": "invoice", "page": 1, "page_size": 25},
        )

    @pytest.mark.parametrize(
        ("tool_name", "path"),
        [
            ("paperless_list_tags", "/api/tags/"),
            ("paperless_list_correspondents", "/api/correspondents/"),
            ("paperless_list_document_types", "/api/document_types/"),
        ],
    )
    async def test_list_tools_fetch_all_paginated_results(
        self,
        tool_name: str,
        path: str,
    ) -> None:
        client = PaperlessClient("http://test:8000", "paperless-token")
        mock = _patch_client_transport(client)
        mock.request.side_effect = [
            _mock_response(
                {
                    "count": 2,
                    "next": f"http://test:8000{path}?page=2&page_size=100000",
                    "previous": None,
                    "all": [1, 2],
                    "results": [{"id": 1, "name": "First"}],
                }
            ),
            _mock_response(
                {
                    "count": 2,
                    "next": None,
                    "previous": f"http://test:8000{path}?page=1&page_size=100000",
                    "all": [1, 2],
                    "results": [{"id": 2, "name": "Second"}],
                }
            ),
        ]

        result = await client.execute_tool(tool_name, {})

        assert result == {
            "count": 2,
            "next": None,
            "previous": None,
            "all": [1, 2],
            "results": [
                {"id": 1, "name": "First"},
                {"id": 2, "name": "Second"},
            ],
        }
        mock.request.assert_has_awaits(
            [
                call("GET", path, params={"page": 1, "page_size": 100000}),
                call("GET", path, params={"page": 2, "page_size": 100000}),
            ]
        )

    async def test_fetch_app_data_resolves_correspondent_and_tag_names(self) -> None:
        client = PaperlessClient("http://test:8000", "paperless-token")
        mock = _patch_client_transport(client)
        mock.request.side_effect = [
            _mock_response(
                {
                    "count": 1,
                    "next": None,
                    "previous": None,
                    "results": [
                        {
                            "title": "Invoice 2024",
                            "correspondent": 5,
                            "tags": [7, 8],
                            "created": "2024-01-15",
                        }
                    ],
                }
            ),
            _mock_response(
                {
                    "count": 1,
                    "next": None,
                    "previous": None,
                    "all": [5],
                    "results": [{"id": 5, "name": "ACME Corp"}],
                }
            ),
            _mock_response(
                {
                    "count": 2,
                    "next": None,
                    "previous": None,
                    "all": [7, 8],
                    "results": [{"id": 7, "name": "finance"}, {"id": 8, "name": "2024"}],
                }
            ),
        ]

        result = await client.fetch_app_data(
            "paperless_document_search",
            {"query": "invoice"},
        )

        assert result == {
            "documents": [
                {
                    "title": "Invoice 2024",
                    "correspondent": "ACME Corp",
                    "tags": ["finance", "2024"],
                    "created": "2024-01-15",
                }
            ],
            "query": "invoice",
            "total": 1,
        }
        mock.request.assert_has_awaits(
            [
                call(
                    "GET",
                    "/api/documents/",
                    params={"query": "invoice", "page": 1, "page_size": 25},
                ),
                call(
                    "GET",
                    "/api/correspondents/",
                    params={"page": 1, "page_size": 100000},
                ),
                call("GET", "/api/tags/", params={"page": 1, "page_size": 100000}),
            ]
        )
