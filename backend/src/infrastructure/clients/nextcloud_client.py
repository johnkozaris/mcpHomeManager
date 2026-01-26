from typing import Any

from domain.entities.service_connection import ServiceType
from domain.entities.tool_definition import ToolDefinition
from domain.exceptions import ToolExecutionError
from infrastructure.clients.base_client import BaseServiceClient

_TOOLS = [
    ToolDefinition(
        name="nextcloud_list_files",
        service_type=ServiceType.NEXTCLOUD,
        description="List files and folders in a Nextcloud directory",
        parameters_schema={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Directory path (e.g. / or /Documents)",
                    "default": "/",
                },
            },
        },
    ),
    ToolDefinition(
        name="nextcloud_search_files",
        service_type=ServiceType.NEXTCLOUD,
        description="Search for files by name across Nextcloud",
        parameters_schema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search term"},
            },
            "required": ["query"],
        },
    ),
    ToolDefinition(
        name="nextcloud_list_notes",
        service_type=ServiceType.NEXTCLOUD,
        description="List all notes from Nextcloud Notes app",
        parameters_schema={"type": "object", "properties": {}},
    ),
    ToolDefinition(
        name="nextcloud_get_note",
        service_type=ServiceType.NEXTCLOUD,
        description="Get a specific note by ID",
        parameters_schema={
            "type": "object",
            "properties": {
                "note_id": {"type": "integer", "description": "Note ID"},
            },
            "required": ["note_id"],
        },
    ),
    ToolDefinition(
        name="nextcloud_user_status",
        service_type=ServiceType.NEXTCLOUD,
        description="Get Nextcloud server and user status",
        parameters_schema={"type": "object", "properties": {}},
    ),
]


class NextcloudClient(BaseServiceClient):
    service_name = "nextcloud"

    def _build_headers(self, token: str) -> dict[str, str]:
        # Nextcloud uses Basic Auth with app passwords or NC- token
        import base64

        # Token format: "user:app-password"
        encoded = base64.b64encode(token.encode()).decode()
        return {
            "Authorization": f"Basic {encoded}",
            "OCS-APIRequest": "true",
            "Accept": "application/json",
        }

    async def health_check(self) -> bool:
        result = await self._request(
            "GET", "/ocs/v2.php/cloud/capabilities", params={"format": "json"}
        )
        return isinstance(result, dict)

    def get_tool_definitions(self) -> list[ToolDefinition]:
        return list(_TOOLS)

    async def execute_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        match tool_name:
            case "nextcloud_list_files":
                path = arguments.get("path", "/")
                return await self._request(
                    "GET",
                    "/ocs/v2.php/apps/files/api/v1/files",
                    params={"path": path, "format": "json"},
                )
            case "nextcloud_search_files":
                return await self._request(
                    "GET",
                    "/ocs/v2.php/search/providers/files/search",
                    params={"term": arguments["query"], "format": "json"},
                )
            case "nextcloud_list_notes":
                return await self._request("GET", "/index.php/apps/notes/api/v1/notes")
            case "nextcloud_get_note":
                note_id = int(arguments["note_id"])
                return await self._request("GET", f"/index.php/apps/notes/api/v1/notes/{note_id}")
            case "nextcloud_user_status":
                return await self._request(
                    "GET", "/ocs/v2.php/cloud/user", params={"format": "json"}
                )
            case _:
                raise ToolExecutionError(tool_name, f"Unknown tool: {tool_name}")
