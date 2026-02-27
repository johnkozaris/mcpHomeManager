from typing import Any

from domain.entities.service_connection import ServiceType
from domain.entities.tool_definition import ToolDefinition
from domain.exceptions import ToolExecutionError
from infrastructure.clients.base_client import BaseServiceClient

_TOOLS = [
    ToolDefinition(
        name="cloudflare_list_zones",
        http_method="GET",
        path_template="/client/v4/zones",
        service_type=ServiceType.CLOUDFLARE,
        description="List zones (domains) in your Cloudflare account",
        parameters_schema={
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Filter by zone name (domain)"},
                "page": {"type": "integer", "default": 1, "description": "Page number"},
                "per_page": {
                    "type": "integer",
                    "default": 20,
                    "description": "Items per page (max 50)",
                },
            },
        },
    ),
    ToolDefinition(
        name="cloudflare_list_dns_records",
        http_method="GET",
        path_template="/client/v4/zones/{zone_id}/dns_records",
        service_type=ServiceType.CLOUDFLARE,
        description="List DNS records for a zone",
        parameters_schema={
            "type": "object",
            "properties": {
                "zone_id": {"type": "string", "description": "Zone ID"},
                "type": {
                    "type": "string",
                    "description": "Filter by record type (A, AAAA, CNAME, MX, TXT, etc.)",
                },
                "name": {"type": "string", "description": "Filter by record name"},
                "page": {"type": "integer", "default": 1, "description": "Page number"},
                "per_page": {
                    "type": "integer",
                    "default": 20,
                    "description": "Items per page",
                },
            },
            "required": ["zone_id"],
        },
    ),
    ToolDefinition(
        name="cloudflare_create_dns_record",
        http_method="POST",
        path_template="/client/v4/zones/{zone_id}/dns_records",
        service_type=ServiceType.CLOUDFLARE,
        description="Create a new DNS record in a zone",
        parameters_schema={
            "type": "object",
            "properties": {
                "zone_id": {"type": "string", "description": "Zone ID"},
                "type": {
                    "type": "string",
                    "description": "Record type (A, AAAA, CNAME, MX, TXT, etc.)",
                },
                "name": {"type": "string", "description": "DNS record name (e.g., example.com)"},
                "content": {
                    "type": "string",
                    "description": "Record content (e.g., IP address or target)",
                },
                "ttl": {
                    "type": "integer",
                    "default": 1,
                    "description": "TTL in seconds (1 = auto)",
                },
                "proxied": {
                    "type": "boolean",
                    "default": False,
                    "description": "Whether the record is proxied through Cloudflare",
                },
                "comment": {"type": "string", "description": "Optional comment for the record"},
            },
            "required": ["zone_id", "type", "name", "content"],
        },
    ),
    ToolDefinition(
        name="cloudflare_list_tunnels",
        http_method="GET",
        path_template="/client/v4/accounts/{account_id}/cfd_tunnel",
        service_type=ServiceType.CLOUDFLARE,
        description="List Cloudflare Tunnels for an account",
        parameters_schema={
            "type": "object",
            "properties": {
                "account_id": {"type": "string", "description": "Account ID"},
                "name": {"type": "string", "description": "Filter by tunnel name"},
                "is_deleted": {
                    "type": "boolean",
                    "default": False,
                    "description": "Include deleted tunnels",
                },
                "page": {"type": "integer", "default": 1, "description": "Page number"},
                "per_page": {
                    "type": "integer",
                    "default": 20,
                    "description": "Items per page",
                },
            },
            "required": ["account_id"],
        },
    ),
    ToolDefinition(
        name="cloudflare_get_tunnel",
        http_method="GET",
        path_template="/client/v4/accounts/{account_id}/cfd_tunnel/{tunnel_id}",
        service_type=ServiceType.CLOUDFLARE,
        description="Get details of a specific Cloudflare Tunnel",
        parameters_schema={
            "type": "object",
            "properties": {
                "account_id": {"type": "string", "description": "Account ID"},
                "tunnel_id": {"type": "string", "description": "Tunnel ID"},
            },
            "required": ["account_id", "tunnel_id"],
        },
    ),
]


class CloudflareClient(BaseServiceClient):
    service_name = "cloudflare"

    def _build_headers(self, token: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {token}", "Accept": "application/json"}

    async def health_check(self) -> bool:
        result = await self._request("GET", "/client/v4/user/tokens/verify")
        return (
            isinstance(result, dict)
            and isinstance(result.get("result"), dict)
            and result["result"].get("status") == "active"
        )

    def get_tool_definitions(self) -> list[ToolDefinition]:
        return list(_TOOLS)

    async def execute_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        match tool_name:
            case "cloudflare_list_zones":
                params: dict[str, Any] = {
                    "page": arguments.get("page", 1),
                    "per_page": arguments.get("per_page", 20),
                }
                if name := arguments.get("name"):
                    params["name"] = name
                return await self._request("GET", "/client/v4/zones", params=params)

            case "cloudflare_list_dns_records":
                zone_id = self._validate_path_segment(arguments["zone_id"], "zone_id")
                params = {
                    "page": arguments.get("page", 1),
                    "per_page": arguments.get("per_page", 20),
                }
                if record_type := arguments.get("type"):
                    params["type"] = record_type
                if name := arguments.get("name"):
                    params["name"] = name
                return await self._request(
                    "GET", f"/client/v4/zones/{zone_id}/dns_records", params=params
                )

            case "cloudflare_create_dns_record":
                zone_id = self._validate_path_segment(arguments["zone_id"], "zone_id")
                body: dict[str, Any] = {
                    "type": arguments["type"],
                    "name": arguments["name"],
                    "content": arguments["content"],
                    "ttl": arguments.get("ttl", 1),
                    "proxied": arguments.get("proxied", False),
                }
                if comment := arguments.get("comment"):
                    body["comment"] = comment
                return await self._request(
                    "POST", f"/client/v4/zones/{zone_id}/dns_records", json=body
                )

            case "cloudflare_list_tunnels":
                account_id = self._validate_path_segment(arguments["account_id"], "account_id")
                params = {
                    "page": arguments.get("page", 1),
                    "per_page": arguments.get("per_page", 20),
                    "is_deleted": arguments.get("is_deleted", False),
                }
                if name := arguments.get("name"):
                    params["name"] = name
                return await self._request(
                    "GET", f"/client/v4/accounts/{account_id}/cfd_tunnel", params=params
                )

            case "cloudflare_get_tunnel":
                account_id = self._validate_path_segment(arguments["account_id"], "account_id")
                tunnel_id = self._validate_path_segment(arguments["tunnel_id"], "tunnel_id")
                return await self._request(
                    "GET",
                    f"/client/v4/accounts/{account_id}/cfd_tunnel/{tunnel_id}",
                )

            case _:
                raise ToolExecutionError(tool_name, f"Unknown tool: {tool_name}")
