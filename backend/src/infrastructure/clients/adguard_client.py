from typing import Any

from domain.entities.service_connection import ServiceType
from domain.entities.tool_definition import ToolDefinition
from domain.exceptions import ToolExecutionError
from infrastructure.clients.base_client import BaseServiceClient

_TOOLS = [
    ToolDefinition(
        name="adguard_status",
        http_method="GET",
        path_template="/control/status",
        service_type=ServiceType.ADGUARD,
        description="Get AdGuard Home status (filtering enabled, DNS addresses, version)",
        parameters_schema={"type": "object", "properties": {}},
    ),
    ToolDefinition(
        name="adguard_query_log",
        http_method="GET",
        path_template="/control/querylog",
        service_type=ServiceType.ADGUARD,
        description="Get recent DNS query log entries",
        parameters_schema={
            "type": "object",
            "properties": {
                "older_than": {
                    "type": "string",
                    "description": "Filter by older-than cursor value",
                },
                "offset": {
                    "type": "integer",
                    "description": "Ranking number of the first item on the page",
                },
                "limit": {"type": "integer", "default": 50, "description": "Number of entries"},
                "search": {
                    "type": "string",
                    "description": "Filter by domain name or client IP",
                },
                "response_status": {
                    "type": "string",
                    "description": "Filter by response status",
                    "enum": [
                        "all",
                        "filtered",
                        "blocked",
                        "blocked_safebrowsing",
                        "blocked_parental",
                        "whitelisted",
                        "rewritten",
                        "safe_search",
                        "processed",
                    ],
                },
            },
        },
    ),
    ToolDefinition(
        name="adguard_stats",
        http_method="GET",
        path_template="/control/stats",
        service_type=ServiceType.ADGUARD,
        description="Get DNS statistics (queries, blocked, top clients, top domains)",
        parameters_schema={
            "type": "object",
            "properties": {
                "recent": {
                    "type": "integer",
                    "description": (
                        "Optional lookback period in milliseconds; per AdGuard docs, this"
                        " must be a whole number of hours"
                    ),
                },
            },
        },
    ),
    ToolDefinition(
        name="adguard_list_filters",
        http_method="GET",
        path_template="/control/filtering/status",
        service_type=ServiceType.ADGUARD,
        description="List all DNS filtering rules and blocklists",
        parameters_schema={"type": "object", "properties": {}},
    ),
    ToolDefinition(
        name="adguard_list_rewrites",
        http_method="GET",
        path_template="/control/rewrite/list",
        service_type=ServiceType.ADGUARD,
        description="List all DNS rewrite rules",
        parameters_schema={"type": "object", "properties": {}},
    ),
    ToolDefinition(
        name="adguard_toggle_protection",
        http_method="POST",
        path_template="/control/protection",
        service_type=ServiceType.ADGUARD,
        description="Enable or disable DNS filtering protection, optionally for a fixed duration",
        parameters_schema={
            "type": "object",
            "properties": {
                "enabled": {"type": "boolean", "description": "True to enable, False to disable"},
                "duration_ms": {
                    "type": "integer",
                    "description": (
                        "Optional duration in milliseconds for a temporary protection state"
                    ),
                },
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
                for key in ("older_than", "offset", "search", "response_status"):
                    value = arguments.get(key)
                    if value is not None:
                        params[key] = value
                return await self._request("GET", "/control/querylog", params=params)
            case "adguard_stats":
                stats_params: dict[str, Any] = {}
                recent = arguments.get("recent")
                if recent is not None:
                    stats_params["recent"] = recent
                return await self._request("GET", "/control/stats", params=stats_params or None)
            case "adguard_list_filters":
                return await self._request("GET", "/control/filtering/status")
            case "adguard_list_rewrites":
                return await self._request("GET", "/control/rewrite/list")
            case "adguard_toggle_protection":
                payload: dict[str, Any] = {"enabled": arguments["enabled"]}
                duration_ms = arguments.get("duration_ms")
                if duration_ms is not None:
                    payload["duration"] = duration_ms
                return await self._request(
                    "POST",
                    "/control/protection",
                    json=payload,
                )
            case _:
                raise ToolExecutionError(tool_name, f"Unknown tool: {tool_name}")
