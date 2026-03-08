"""Tests for the Forgejo service client."""

from unittest.mock import AsyncMock, MagicMock, call

import pytest

from domain.entities.service_connection import ServiceType
from domain.exceptions import ToolExecutionError
from infrastructure.clients.forgejo_client import ForgejoClient


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


class TestForgejoClient:
    def test_get_tool_definitions(self):
        client = ForgejoClient("https://forgejo.example.com", "test-token")
        defs = client.get_tool_definitions()
        assert len(defs) == 7
        assert all(d.service_type == ServiceType.FORGEJO for d in defs)
        assert defs[0].description == "List repositories owned by the authenticated user"

    async def test_unknown_tool_raises(self):
        client = ForgejoClient("https://forgejo.example.com", "test-token")
        with pytest.raises(ToolExecutionError, match="Unknown tool"):
            await client.execute_tool("nonexistent", {})
        await client.close()

    async def test_list_repos_uses_documented_pagination_params(self):
        client = ForgejoClient("https://forgejo.example.com", "test-token")
        mock = _patch_client_transport(client)
        mock.request.return_value = _mock_response([{"name": "repo"}])

        result = await client.execute_tool("forgejo_list_repos", {"page": 2, "limit": 25})

        assert result == [{"name": "repo"}]
        method, path = mock.request.call_args.args[:2]
        assert method == "GET"
        assert path == "/api/v1/user/repos"
        assert mock.request.call_args.kwargs["params"] == {"page": 2, "limit": 25}

    async def test_list_issues_filters_out_pull_requests(self):
        client = ForgejoClient("https://forgejo.example.com", "test-token")
        mock = _patch_client_transport(client)
        mock.request.return_value = _mock_response([{"number": 1}])

        result = await client.execute_tool(
            "forgejo_list_issues",
            {"owner": "alice", "repo": "docs", "state": "all", "page": 2, "limit": 25},
        )

        assert result == [{"number": 1}]
        method, path = mock.request.call_args.args[:2]
        assert method == "GET"
        assert path == "/api/v1/repos/alice/docs/issues"
        assert mock.request.call_args.kwargs["params"] == {
            "type": "issues",
            "state": "all",
            "page": 2,
            "limit": 25,
        }

    async def test_list_pull_requests_uses_documented_pagination_params(self):
        client = ForgejoClient("https://forgejo.example.com", "test-token")
        mock = _patch_client_transport(client)
        mock.request.return_value = _mock_response([{"number": 2}])

        result = await client.execute_tool(
            "forgejo_list_pull_requests",
            {"owner": "alice", "repo": "docs", "state": "closed", "page": 3, "limit": 15},
        )

        assert result == [{"number": 2}]
        method, path = mock.request.call_args.args[:2]
        assert method == "GET"
        assert path == "/api/v1/repos/alice/docs/pulls"
        assert mock.request.call_args.kwargs["params"] == {
            "state": "closed",
            "page": 3,
            "limit": 15,
        }

    async def test_search_repos_maps_query_to_q_param(self):
        client = ForgejoClient("https://forgejo.example.com", "test-token")
        mock = _patch_client_transport(client)
        mock.request.return_value = _mock_response({"data": []})

        result = await client.execute_tool(
            "forgejo_search_repos",
            {"query": "agent", "page": 3, "limit": 10},
        )

        assert result == {"data": []}
        method, path = mock.request.call_args.args[:2]
        assert method == "GET"
        assert path == "/api/v1/repos/search"
        assert mock.request.call_args.kwargs["params"] == {"q": "agent", "page": 3, "limit": 10}

    async def test_repo_browser_without_owner_uses_authenticated_repo_listing(self):
        client = ForgejoClient("https://forgejo.example.com", "test-token")
        client._request = AsyncMock(return_value=[{"full_name": "alice/repo"}])

        result = await client.fetch_app_data("forgejo_repo_browser", {})

        client._request.assert_awaited_once_with(
            "GET",
            "/api/v1/user/repos",
            params={"page": 1, "limit": 50},
        )
        assert result == {"repos": [{"full_name": "alice/repo"}], "owner_filter": None}

    async def test_repo_browser_owner_uses_user_scoped_endpoint(self):
        client = ForgejoClient("https://forgejo.example.com", "test-token")
        client._request = AsyncMock(return_value=[{"full_name": "alice/repo"}])

        result = await client.fetch_app_data("forgejo_repo_browser", {"owner": "alice"})

        client._request.assert_awaited_once_with(
            "GET",
            "/api/v1/users/alice/repos",
            params={"page": 1, "limit": 50},
        )
        assert result == {"repos": [{"full_name": "alice/repo"}], "owner_filter": "alice"}

    async def test_repo_browser_owner_falls_back_to_org_endpoint_on_user_404(self):
        client = ForgejoClient("https://forgejo.example.com", "test-token")
        client._request = AsyncMock(
            side_effect=[
                ToolExecutionError("forgejo", "HTTP 404: user not found"),
                [{"full_name": "acme/repo"}],
            ]
        )

        result = await client.fetch_app_data("forgejo_repo_browser", {"owner": "acme"})

        assert client._request.await_args_list == [
            call("GET", "/api/v1/users/acme/repos", params={"page": 1, "limit": 50}),
            call("GET", "/api/v1/orgs/acme/repos", params={"page": 1, "limit": 50}),
        ]
        assert result == {"repos": [{"full_name": "acme/repo"}], "owner_filter": "acme"}
