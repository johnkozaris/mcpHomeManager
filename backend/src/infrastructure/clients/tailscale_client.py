import base64
from typing import Any

from domain.entities.service_connection import ServiceType
from domain.entities.tool_definition import ToolDefinition
from domain.exceptions import ToolExecutionError
from infrastructure.clients.base_client import BaseServiceClient

_FILTER_VALUE_SCHEMA = {
    "anyOf": [
        {"type": "string"},
        {"type": "number"},
        {"type": "boolean"},
        {
            "type": "array",
            "items": {
                "anyOf": [
                    {"type": "string"},
                    {"type": "number"},
                    {"type": "boolean"},
                ]
            },
        },
    ]
}

_TOOLS = [
    ToolDefinition(
        name="tailscale_list_devices",
        http_method="GET",
        path_template="/tailnet/-/devices",
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
                "filters": {
                    "type": "object",
                    "description": (
                        "Optional exact-match filters for top-level device fields "
                        "(for example hostname, authorized, or tags). "
                        "Use an array value to repeat a filter like tags=tag:prod&tags=tag:router."
                    ),
                    "additionalProperties": _FILTER_VALUE_SCHEMA,
                },
            },
        },
    ),
    ToolDefinition(
        name="tailscale_get_device",
        http_method="GET",
        path_template="/device/{device_id}",
        service_type=ServiceType.TAILSCALE,
        description="Get information about a specific device",
        parameters_schema={
            "type": "object",
            "properties": {
                "device_id": {
                    "type": "string",
                    "description": (
                        "The Tailscale device ID (prefer nodeId; legacy numeric id also works)"
                    ),
                },
                "fields": {
                    "type": "string",
                    "enum": ["all", "default"],
                    "default": "default",
                    "description": "Level of detail: all or default",
                },
            },
            "required": ["device_id"],
        },
    ),
    ToolDefinition(
        name="tailscale_authorize_device",
        http_method="POST",
        path_template="/device/{device_id}/authorized",
        service_type=ServiceType.TAILSCALE,
        description="Authorize or deauthorize a device in the tailnet",
        parameters_schema={
            "type": "object",
            "properties": {
                "device_id": {
                    "type": "string",
                    "description": (
                        "The Tailscale device ID (prefer nodeId; legacy numeric id also works)"
                    ),
                },
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
        http_method="GET",
        path_template="/device/{device_id}/routes",
        service_type=ServiceType.TAILSCALE,
        description="Get the subnet routes advertised and enabled for a device",
        parameters_schema={
            "type": "object",
            "properties": {
                "device_id": {
                    "type": "string",
                    "description": (
                        "The Tailscale device ID (prefer nodeId; legacy numeric id also works)"
                    ),
                },
            },
            "required": ["device_id"],
        },
    ),
    ToolDefinition(
        name="tailscale_list_dns_nameservers",
        http_method="GET",
        path_template="/tailnet/-/dns/nameservers",
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

    @staticmethod
    def _serialize_filter_value(filter_name: str, value: Any) -> str:
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, int | float | str):
            return str(value)
        raise ToolExecutionError(
            "tailscale_list_devices",
            f"Invalid filter value for '{filter_name}': {value!r}",
        )

    @classmethod
    def _build_device_filters(cls, raw_filters: Any) -> dict[str, Any]:
        if not isinstance(raw_filters, dict):
            raise ToolExecutionError(
                "tailscale_list_devices",
                "filters must be an object keyed by top-level device fields",
            )

        params: dict[str, Any] = {}
        for filter_name, raw_value in raw_filters.items():
            if not isinstance(filter_name, str) or not filter_name.isidentifier():
                raise ToolExecutionError(
                    "tailscale_list_devices",
                    f"Invalid filter name: {filter_name!r}",
                )
            if filter_name == "fields":
                raise ToolExecutionError(
                    "tailscale_list_devices",
                    "Use the dedicated 'fields' argument instead of a filter named 'fields'",
                )
            if isinstance(raw_value, list | tuple):
                params[filter_name] = [
                    cls._serialize_filter_value(filter_name, value) for value in raw_value
                ]
                continue
            params[filter_name] = cls._serialize_filter_value(filter_name, raw_value)
        return params

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
                raw_filters = arguments.get("filters")
                if raw_filters is not None:
                    params.update(self._build_device_filters(raw_filters))
                return await self._request("GET", "/tailnet/-/devices", params=params)
            case "tailscale_get_device":
                device_id = self._validate_path_segment(arguments["device_id"], "device_id")
                device_params: dict[str, Any] = {}
                if fields := arguments.get("fields"):
                    device_params["fields"] = fields
                return await self._request("GET", f"/device/{device_id}", params=device_params)
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
