import base64
from typing import Any

from domain.entities.service_connection import ServiceType
from domain.entities.tool_definition import ToolDefinition
from domain.exceptions import ToolExecutionError
from infrastructure.clients.base_client import BaseServiceClient

_TOOLS = [
    ToolDefinition(
        name="tailscale_list_devices",
        service_type=ServiceType.TAILSCALE,
        description="List all devices in the tailnet",
        parameters_schema={
            "type": "object",
            "properties": {
                "fields": {
                    "type": "string",
                    "enum": ["all", "default"],
                    "default": "default",
                    "description": "Level of detail: all or default",
                },
            },
        },
    ),
    ToolDefinition(
        name="tailscale_get_device",
        service_type=ServiceType.TAILSCALE,
        description="Get detailed information about a specific device",
        parameters_schema={
            "type": "object",
            "properties": {
                "device_id": {"type": "string", "description": "The device ID or nodekey"},
            },
            "required": ["device_id"],
        },
    ),
    ToolDefinition(
        name="tailscale_authorize_device",
        service_type=ServiceType.TAILSCALE,
        description="Authorize or deauthorize a device in the tailnet",
        parameters_schema={
            "type": "object",
            "properties": {
                "device_id": {"type": "string", "description": "The device ID or nodekey"},
                "authorized": {
                    "type": "boolean",
                    "description": "True to authorize, False to deauthorize",
                },
            },
            "required": ["device_id", "authorized"],
        },
    ),
    ToolDefinition(
        name="tailscale_get_device_routes",
        service_type=ServiceType.TAILSCALE,
        description="Get the subnet routes advertised and enabled for a device",
        parameters_schema={
            "type": "object",
            "properties": {
                "device_id": {"type": "string", "description": "The device ID or nodekey"},
            },
            "required": ["device_id"],
        },
    ),
    ToolDefinition(
        name="tailscale_list_dns_nameservers",
        service_type=ServiceType.TAILSCALE,
        description="List the DNS nameservers configured for the tailnet",
        parameters_schema={"type": "object", "properties": {}},
    ),
]


class TailscaleClient(BaseServiceClient):
    service_name = "tailscale"

    def _build_headers(self, token: str) -> dict[str, str]:
        encoded = base64.b64encode(f"{token}:".encode()).decode()
        return {"Authorization": f"Basic {encoded}", "Accept": "application/json"}

    async def health_check(self) -> bool:
        result = await self._request("GET", "/tailnet/-/devices")
        return isinstance(result, dict) and "devices" in result

    def get_tool_definitions(self) -> list[ToolDefinition]:
        return list(_TOOLS)

    async def execute_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        match tool_name:
            case "tailscale_list_devices":
                params: dict[str, Any] = {}
                if fields := arguments.get("fields"):
                    params["fields"] = fields
                return await self._request("GET", "/tailnet/-/devices", params=params)
            case "tailscale_get_device":
                device_id = self._validate_path_segment(arguments["device_id"], "device_id")
                return await self._request("GET", f"/device/{device_id}")
            case "tailscale_authorize_device":
                device_id = self._validate_path_segment(arguments["device_id"], "device_id")
                return await self._request(
                    "POST",
                    f"/device/{device_id}/authorized",
                    json={"authorized": arguments["authorized"]},
                )
            case "tailscale_get_device_routes":
                device_id = self._validate_path_segment(arguments["device_id"], "device_id")
                return await self._request("GET", f"/device/{device_id}/routes")
            case "tailscale_list_dns_nameservers":
                return await self._request("GET", "/tailnet/-/dns/nameservers")
            case _:
                raise ToolExecutionError(tool_name, f"Unknown tool: {tool_name}")
