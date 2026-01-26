from typing import Any

from domain.entities.service_connection import ServiceType
from domain.entities.tool_definition import ToolDefinition
from domain.exceptions import ToolExecutionError
from infrastructure.clients.base_client import BaseServiceClient

_TOOLS = [
    ToolDefinition(
        name="adguard_status",
        service_type=ServiceType.ADGUARD,
        description="Get AdGuard Home status (filtering enabled, DNS addresses, version)",
        parameters_schema={"type": "object", "properties": {}},
    ),
    ToolDefinition(
        name="adguard_query_log",
        service_type=ServiceType.ADGUARD,
        description="Get recent DNS query log entries",
        parameters_schema={
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "default": 50, "description": "Number of entries"},
                "search": {"type": "string", "description": "Filter by domain name"},
            },
        },
    ),
    ToolDefinition(
        name="adguard_stats",
        service_type=ServiceType.ADGUARD,
        description="Get DNS statistics (queries, blocked, top clients, top domains)",
        parameters_schema={"type": "object", "properties": {}},
    ),
    ToolDefinition(
        name="adguard_list_filters",
        service_type=ServiceType.ADGUARD,
        description="List all DNS filtering rules and blocklists",
        parameters_schema={"type": "object", "properties": {}},
    ),
    ToolDefinition(
        name="adguard_list_rewrites",
        service_type=ServiceType.ADGUARD,
        description="List all DNS rewrite rules",
        parameters_schema={"type": "object", "properties": {}},
    ),
    ToolDefinition(
        name="adguard_toggle_protection",
        service_type=ServiceType.ADGUARD,
        description="Enable or disable DNS filtering protection",
        parameters_schema={
            "type": "object",
            "properties": {
                "enabled": {"type": "boolean", "description": "True to enable, False to disable"},
            },
            "required": ["enabled"],
        },
    ),
]


class AdGuardClient(BaseServiceClient):
    service_name = "adguard"

    def _build_headers(self, token: str) -> dict[str, str]:
        # AdGuard uses Basic Auth: "username:password" base64-encoded
        import base64

        encoded = base64.b64encode(token.encode()).decode()
        return {"Authorization": f"Basic {encoded}", "Accept": "application/json"}

    async def health_check(self) -> bool:
        result = await self._request("GET", "/control/status")
        return isinstance(result, dict) and "version" in result

    def get_tool_definitions(self) -> list[ToolDefinition]:
        return list(_TOOLS)

    async def execute_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        match tool_name:
            case "adguard_status":
                return await self._request("GET", "/control/status")
            case "adguard_query_log":
                params: dict[str, Any] = {"limit": arguments.get("limit", 50)}
                if search := arguments.get("search"):
                    params["search"] = search
                return await self._request("GET", "/control/querylog", params=params)
            case "adguard_stats":
                return await self._request("GET", "/control/stats")
            case "adguard_list_filters":
                return await self._request("GET", "/control/filtering/status")
            case "adguard_list_rewrites":
                return await self._request("GET", "/control/rewrite/list")
            case "adguard_toggle_protection":
                return await self._request(
                    "POST",
                    "/control/dns_config",
                    json={"protection_enabled": arguments["enabled"]},
                )
            case _:
                raise ToolExecutionError(tool_name, f"Unknown tool: {tool_name}")
