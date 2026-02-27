from typing import Any

from domain.entities.service_connection import ServiceType
from domain.entities.tool_definition import ToolDefinition
from domain.exceptions import ToolExecutionError
from infrastructure.clients.base_client import BaseServiceClient

_TOOLS = [
    ToolDefinition(
        name="uptimekuma_list_monitors",
        http_method="GET",
        path_template="/api/monitors",
        service_type=ServiceType.UPTIME_KUMA,
        description="List all monitoring targets with their current status",
        parameters_schema={"type": "object", "properties": {}},
    ),
    ToolDefinition(
        name="uptimekuma_get_monitor",
        http_method="GET",
        path_template="/api/monitors/{monitor_id}",
        service_type=ServiceType.UPTIME_KUMA,
        description="Get detailed status and history for a specific monitor",
        parameters_schema={
            "type": "object",
            "properties": {
                "monitor_id": {"type": "integer", "description": "Monitor ID"},
            },
            "required": ["monitor_id"],
        },
    ),
    ToolDefinition(
        name="uptimekuma_pause_monitor",
        http_method="POST",
        path_template="/api/monitors/{monitor_id}/pause",
        service_type=ServiceType.UPTIME_KUMA,
        description="Pause a monitor (stop checking)",
        parameters_schema={
            "type": "object",
            "properties": {
                "monitor_id": {"type": "integer", "description": "Monitor ID"},
            },
            "required": ["monitor_id"],
        },
    ),
    ToolDefinition(
        name="uptimekuma_resume_monitor",
        http_method="POST",
        path_template="/api/monitors/{monitor_id}/resume",
        service_type=ServiceType.UPTIME_KUMA,
        description="Resume a paused monitor",
        parameters_schema={
            "type": "object",
            "properties": {
                "monitor_id": {"type": "integer", "description": "Monitor ID"},
            },
            "required": ["monitor_id"],
        },
    ),
]


class UptimeKumaClient(BaseServiceClient):
    """Uptime Kuma v2 REST API client."""

    service_name = "uptimekuma"

    def _build_headers(self, token: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {token}", "Accept": "application/json"}

    async def health_check(self) -> bool:
        result = await self._request("GET", "/api/entry")
        return isinstance(result, dict)

    def get_tool_definitions(self) -> list[ToolDefinition]:
        return list(_TOOLS)

    async def execute_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        match tool_name:
            case "uptimekuma_list_monitors":
                return await self._request("GET", "/api/monitors")
            case "uptimekuma_get_monitor":
                mid = int(arguments["monitor_id"])
                return await self._request("GET", f"/api/monitors/{mid}")
            case "uptimekuma_pause_monitor":
                mid = int(arguments["monitor_id"])
                return await self._request("POST", f"/api/monitors/{mid}/pause")
            case "uptimekuma_resume_monitor":
                mid = int(arguments["monitor_id"])
                return await self._request("POST", f"/api/monitors/{mid}/resume")
            case _:
                raise ToolExecutionError(tool_name, f"Unknown tool: {tool_name}")
