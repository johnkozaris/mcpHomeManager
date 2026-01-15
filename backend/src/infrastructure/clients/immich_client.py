from typing import Any

from domain.entities.service_connection import ServiceType
from domain.entities.tool_definition import ToolDefinition
from domain.exceptions import ToolExecutionError
from infrastructure.clients.base_client import BaseServiceClient

_TOOLS = [
    ToolDefinition(
        name="immich_search_photos",
        service_type=ServiceType.IMMICH,
        description="Search photos and videos by text query (uses CLIP ML model)",
        parameters_schema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Natural language search query"},
                "page": {"type": "integer", "default": 1},
                "size": {"type": "integer", "default": 20},
            },
            "required": ["query"],
        },
    ),
    ToolDefinition(
        name="immich_get_asset",
        service_type=ServiceType.IMMICH,
        description="Get metadata for a specific photo or video asset",
        parameters_schema={
            "type": "object",
            "properties": {
                "asset_id": {"type": "string", "description": "Asset UUID"},
            },
            "required": ["asset_id"],
        },
    ),
    ToolDefinition(
        name="immich_list_albums",
        service_type=ServiceType.IMMICH,
        description="List all photo albums",
        parameters_schema={"type": "object", "properties": {}},
    ),
    ToolDefinition(
        name="immich_get_album",
        service_type=ServiceType.IMMICH,
        description="Get album details including its assets",
        parameters_schema={
            "type": "object",
            "properties": {
                "album_id": {"type": "string", "description": "Album UUID"},
            },
            "required": ["album_id"],
        },
    ),
    ToolDefinition(
        name="immich_server_stats",
        service_type=ServiceType.IMMICH,
        description="Get Immich server statistics (photo/video counts, disk usage)",
        parameters_schema={"type": "object", "properties": {}},
    ),
]


class ImmichClient(BaseServiceClient):
    service_name = "immich"

    def _build_headers(self, token: str) -> dict[str, str]:
        return {"x-api-key": token, "Accept": "application/json"}

    async def health_check(self) -> bool:
        result = await self._request("GET", "/api/server/ping")
        return isinstance(result, dict) and result.get("res") == "pong"

    def get_tool_definitions(self) -> list[ToolDefinition]:
        return list(_TOOLS)

    async def execute_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        match tool_name:
            case "immich_search_photos":
                return await self._request(
                    "POST",
                    "/api/search/smart",
                    json={
                        "query": arguments["query"],
                        "page": arguments.get("page", 1),
                        "size": arguments.get("size", 20),
                    },
                )
            case "immich_get_asset":
                asset_id = self._validate_path_segment(arguments["asset_id"], "asset_id")
                return await self._request("GET", f"/api/assets/{asset_id}")
            case "immich_list_albums":
                return await self._request("GET", "/api/albums")
            case "immich_get_album":
                album_id = self._validate_path_segment(arguments["album_id"], "album_id")
                return await self._request("GET", f"/api/albums/{album_id}")
            case "immich_server_stats":
                return await self._request("GET", "/api/server/statistics")
            case _:
                raise ToolExecutionError(tool_name, f"Unknown tool: {tool_name}")
