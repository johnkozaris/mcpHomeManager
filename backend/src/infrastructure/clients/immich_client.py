from typing import Any
from uuid import UUID

from domain.entities.service_connection import ServiceType
from domain.entities.tool_definition import ToolDefinition
from domain.exceptions import ToolExecutionError
from infrastructure.clients.base_client import BaseServiceClient

_TOOLS = [
    ToolDefinition(
        name="immich_search_photos",
        http_method="POST",
        path_template="/api/search/smart",
        service_type=ServiceType.IMMICH,
        description="Search photos and videos by natural language query using Immich smart search",
        parameters_schema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Natural language search query"},
                "page": {
                    "type": "integer",
                    "default": 1,
                    "minimum": 1,
                    "description": "Page number (minimum 1)",
                },
                "size": {
                    "type": "integer",
                    "default": 20,
                    "minimum": 1,
                    "maximum": 1000,
                    "description": "Number of results to return (1-1000)",
                },
            },
            "required": ["query"],
        },
    ),
    ToolDefinition(
        name="immich_get_asset",
        http_method="GET",
        path_template="/api/assets/{asset_id}",
        service_type=ServiceType.IMMICH,
        description="Get metadata for a specific photo or video asset",
        parameters_schema={
            "type": "object",
            "properties": {
                "asset_id": {
                    "type": "string",
                    "format": "uuid",
                    "description": "Asset UUID",
                },
            },
            "required": ["asset_id"],
        },
    ),
    ToolDefinition(
        name="immich_list_albums",
        http_method="GET",
        path_template="/api/albums",
        service_type=ServiceType.IMMICH,
        description="List albums available to the authenticated user",
        parameters_schema={"type": "object", "properties": {}},
    ),
    ToolDefinition(
        name="immich_get_album",
        http_method="GET",
        path_template="/api/albums/{album_id}",
        service_type=ServiceType.IMMICH,
        description="Get album details including its assets",
        parameters_schema={
            "type": "object",
            "properties": {
                "album_id": {
                    "type": "string",
                    "format": "uuid",
                    "description": "Album UUID",
                },
            },
            "required": ["album_id"],
        },
    ),
    ToolDefinition(
        name="immich_server_stats",
        http_method="GET",
        path_template="/api/server/statistics",
        service_type=ServiceType.IMMICH,
        description=(
            "Get Immich server statistics (photo/video counts, disk usage). "
            "Requires an admin Immich API key with server.statistics permission."
        ),
        parameters_schema={"type": "object", "properties": {}},
    ),
]


class ImmichClient(BaseServiceClient):
    service_name = "immich"

    def _build_headers(self, token: str) -> dict[str, str]:
        return {"x-api-key": token, "Accept": "application/json"}

    async def health_check(self) -> bool:
        albums = await self._request("GET", "/api/albums", params={"shared": True})
        explore = await self._request("GET", "/api/search/explore")
        return isinstance(albums, list) and isinstance(explore, list)

    def get_tool_definitions(self) -> list[ToolDefinition]:
        return list(_TOOLS)

    @staticmethod
    def _validate_int_argument(
        value: Any,
        name: str,
        *,
        minimum: int,
        maximum: int | None = None,
    ) -> int:
        if isinstance(value, bool) or not isinstance(value, int):
            raise ToolExecutionError(name, f"'{name}' must be an integer")
        if value < minimum:
            raise ToolExecutionError(name, f"'{name}' must be at least {minimum}")
        if maximum is not None and value > maximum:
            raise ToolExecutionError(name, f"'{name}' must be at most {maximum}")
        return value

    def _validate_uuid_argument(self, value: str, name: str) -> str:
        safe_value = self._validate_path_segment(value, name)
        try:
            UUID(safe_value)
        except ValueError as exc:
            raise ToolExecutionError(name, f"'{name}' must be a valid UUID") from exc
        return safe_value

    async def execute_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        match tool_name:
            case "immich_search_photos":
                page = self._validate_int_argument(arguments.get("page", 1), "page", minimum=1)
                size = self._validate_int_argument(
                    arguments.get("size", 20), "size", minimum=1, maximum=1000
                )
                return await self._request(
                    "POST",
                    "/api/search/smart",
                    json={
                        "query": arguments["query"],
                        "page": page,
                        "size": size,
                    },
                )
            case "immich_get_asset":
                asset_id = self._validate_uuid_argument(arguments["asset_id"], "asset_id")
                return await self._request("GET", f"/api/assets/{asset_id}")
            case "immich_list_albums":
                return await self._request("GET", "/api/albums")
            case "immich_get_album":
                album_id = self._validate_uuid_argument(arguments["album_id"], "album_id")
                return await self._request("GET", f"/api/albums/{album_id}")
            case "immich_server_stats":
                return await self._request("GET", "/api/server/statistics")
            case _:
                raise ToolExecutionError(tool_name, f"Unknown tool: {tool_name}")
