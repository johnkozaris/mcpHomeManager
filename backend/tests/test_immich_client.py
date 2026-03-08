"""Tests for the Immich service client."""

from unittest.mock import AsyncMock, call

import pytest

from domain.entities.service_connection import ServiceType
from domain.exceptions import ToolExecutionError
from infrastructure.clients.immich_client import ImmichClient


class TestImmichClient:
    def test_get_tool_definitions_marks_stats_as_admin_only(self) -> None:
        client = ImmichClient("https://immich.example", "my-api-token")

        definitions = client.get_tool_definitions()

        assert len(definitions) == 5
        assert all(defn.service_type == ServiceType.IMMICH for defn in definitions)
        stats_tool = next(defn for defn in definitions if defn.name == "immich_server_stats")
        assert stats_tool.http_method == "GET"
        assert stats_tool.path_template == "/api/server/statistics"
        assert "admin" in stats_tool.description.lower()
        assert "server.statistics" in stats_tool.description
        search_tool = next(defn for defn in definitions if defn.name == "immich_search_photos")
        assert search_tool.parameters_schema["properties"]["page"]["minimum"] == 1
        assert search_tool.parameters_schema["properties"]["size"]["minimum"] == 1
        assert search_tool.parameters_schema["properties"]["size"]["maximum"] == 1000
        asset_tool = next(defn for defn in definitions if defn.name == "immich_get_asset")
        assert asset_tool.parameters_schema["properties"]["asset_id"]["format"] == "uuid"
        album_tool = next(defn for defn in definitions if defn.name == "immich_get_album")
        assert album_tool.parameters_schema["properties"]["album_id"]["format"] == "uuid"

    def test_build_headers_uses_immich_api_key_header(self) -> None:
        client = ImmichClient("https://immich.example", "my-api-token")

        headers = client._build_headers("test-token")

        assert headers["x-api-key"] == "test-token"
        assert headers["Accept"] == "application/json"

    async def test_health_check_validates_authenticated_read_endpoints(self) -> None:
        client = ImmichClient("https://immich.example", "my-api-token")
        client._request = AsyncMock(side_effect=[[], []])  # type: ignore[method-assign]

        result = await client.health_check()

        assert result is True
        client._request.assert_has_awaits(
            [
                call("GET", "/api/albums", params={"shared": True}),
                call("GET", "/api/search/explore"),
            ]
        )

    async def test_health_check_returns_false_for_unexpected_payloads(self) -> None:
        client = ImmichClient("https://immich.example", "my-api-token")
        client._request = AsyncMock(side_effect=[{}, []])  # type: ignore[method-assign]

        result = await client.health_check()

        assert result is False

    async def test_server_stats_calls_admin_only_endpoint(self) -> None:
        client = ImmichClient("https://immich.example", "my-api-token")
        expected = {"photos": 10, "videos": 4, "usage": 1024}
        client._request = AsyncMock(return_value=expected)  # type: ignore[method-assign]

        result = await client.execute_tool("immich_server_stats", {})

        assert result == expected
        client._request.assert_awaited_once_with("GET", "/api/server/statistics")

    async def test_search_photos_uses_validated_pagination_params(self) -> None:
        client = ImmichClient("https://immich.example", "my-api-token")
        expected = {"assets": {"items": []}, "albums": {"items": []}}
        client._request = AsyncMock(return_value=expected)  # type: ignore[method-assign]

        result = await client.execute_tool(
            "immich_search_photos",
            {"query": "sunset", "page": 2, "size": 50},
        )

        assert result == expected
        client._request.assert_awaited_once_with(
            "POST",
            "/api/search/smart",
            json={"query": "sunset", "page": 2, "size": 50},
        )

    @pytest.mark.parametrize(
        ("arguments", "message"),
        [
            ({"query": "sunset", "page": 0}, "'page' must be at least 1"),
            ({"query": "sunset", "size": 1001}, "'size' must be at most 1000"),
            ({"query": "sunset", "page": True}, "'page' must be an integer"),
        ],
    )
    async def test_search_photos_validates_pagination_bounds(
        self,
        arguments: dict[str, object],
        message: str,
    ) -> None:
        client = ImmichClient("https://immich.example", "my-api-token")

        with pytest.raises(ToolExecutionError, match=message):
            await client.execute_tool("immich_search_photos", arguments)

    async def test_get_asset_validates_path_segments(self) -> None:
        client = ImmichClient("https://immich.example", "my-api-token")

        with pytest.raises(ToolExecutionError, match="Invalid characters in 'asset_id'"):
            await client.execute_tool("immich_get_asset", {"asset_id": "../secrets"})

    @pytest.mark.parametrize(
        "tool_name, argument_name",
        [("immich_get_asset", "asset_id"), ("immich_get_album", "album_id")],
    )
    async def test_uuid_backed_tools_require_valid_uuid(
        self,
        tool_name: str,
        argument_name: str,
    ) -> None:
        client = ImmichClient("https://immich.example", "my-api-token")

        with pytest.raises(ToolExecutionError, match=f"'{argument_name}' must be a valid UUID"):
            await client.execute_tool(tool_name, {argument_name: "not-a-uuid"})
