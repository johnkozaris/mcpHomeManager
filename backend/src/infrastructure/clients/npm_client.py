from typing import Any

from domain.entities.service_connection import ServiceType
from domain.entities.tool_definition import ToolDefinition
from domain.exceptions import ServiceConnectionError, ToolExecutionError
from infrastructure.clients.base_client import BaseServiceClient

_TOOLS = [
    ToolDefinition(
        name="npm_list_proxy_hosts",
        http_method="GET",
        path_template="/api/nginx/proxy-hosts",
        service_type=ServiceType.NGINX_PROXY_MANAGER,
        description="List all proxy hosts configured in Nginx Proxy Manager",
        parameters_schema={"type": "object", "properties": {}},
    ),
    ToolDefinition(
        name="npm_get_proxy_host",
        http_method="GET",
        path_template="/api/nginx/proxy-hosts/{id}",
        service_type=ServiceType.NGINX_PROXY_MANAGER,
        description="Get details of a specific proxy host by ID",
        parameters_schema={
            "type": "object",
            "properties": {
                "id": {"type": "integer", "description": "Proxy host ID"},
            },
            "required": ["id"],
        },
    ),
    ToolDefinition(
        name="npm_create_proxy_host",
        http_method="POST",
        path_template="/api/nginx/proxy-hosts",
        service_type=ServiceType.NGINX_PROXY_MANAGER,
        description="Create a new proxy host",
        parameters_schema={
            "type": "object",
            "properties": {
                "domain_names": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Domain names for this proxy host",
                },
                "forward_scheme": {
                    "type": "string",
                    "enum": ["http", "https"],
                    "description": "Scheme to use when forwarding (http or https)",
                },
                "forward_host": {"type": "string", "description": "Host to forward to"},
                "forward_port": {"type": "integer", "description": "Port to forward to"},
                "ssl_forced": {
                    "type": "boolean",
                    "default": False,
                    "description": "Force SSL on this proxy host",
                },
            },
            "required": ["domain_names", "forward_scheme", "forward_host", "forward_port"],
        },
    ),
    ToolDefinition(
        name="npm_delete_proxy_host",
        http_method="DELETE",
        path_template="/api/nginx/proxy-hosts/{id}",
        service_type=ServiceType.NGINX_PROXY_MANAGER,
        description="Delete a proxy host by ID",
        parameters_schema={
            "type": "object",
            "properties": {
                "id": {"type": "integer", "description": "Proxy host ID"},
            },
            "required": ["id"],
        },
    ),
    ToolDefinition(
        name="npm_list_redirection_hosts",
        http_method="GET",
        path_template="/api/nginx/redirection-hosts",
        service_type=ServiceType.NGINX_PROXY_MANAGER,
        description="List all redirection hosts",
        parameters_schema={"type": "object", "properties": {}},
    ),
    ToolDefinition(
        name="npm_list_streams",
        http_method="GET",
        path_template="/api/nginx/streams",
        service_type=ServiceType.NGINX_PROXY_MANAGER,
        description="List all TCP/UDP stream proxies",
        parameters_schema={"type": "object", "properties": {}},
    ),
    ToolDefinition(
        name="npm_list_certificates",
        http_method="GET",
        path_template="/api/nginx/certificates",
        service_type=ServiceType.NGINX_PROXY_MANAGER,
        description="List all SSL certificates",
        parameters_schema={"type": "object", "properties": {}},
    ),
]


class NginxProxyManagerClient(BaseServiceClient):
    service_name = "nginxproxymanager"

    def __init__(self, base_url: str, api_token: str, **kwargs: Any) -> None:
        super().__init__(base_url, api_token, **kwargs)
        self._jwt: str | None = None

    def _build_headers(self, token: str) -> dict[str, str]:
        return {"Content-Type": "application/json"}

    async def _ensure_jwt(self) -> None:
        if self._jwt:
            return
        parts = self._api_token.split(":", 1)
        if len(parts) != 2:
            raise ServiceConnectionError(
                self.service_name, "Token must be in email:password format"
            )
        email, password = parts
        try:
            resp = await self._client.post(
                "/api/tokens", json={"identity": email, "secret": password}
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            raise ServiceConnectionError(self.service_name, f"Authentication failed: {e}") from e
        token = data.get("token")
        if not token:
            raise ServiceConnectionError(self.service_name, "No token in auth response")
        self._jwt = token
        self._client.headers["Authorization"] = f"Bearer {self._jwt}"

    async def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        await self._ensure_jwt()
        return await super()._request(method, path, **kwargs)

    async def health_check(self) -> bool:
        result = await self._request("GET", "/api/nginx/proxy-hosts")
        return isinstance(result, list)

    def get_tool_definitions(self) -> list[ToolDefinition]:
        return list(_TOOLS)

    async def execute_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        match tool_name:
            case "npm_list_proxy_hosts":
                return await self._request("GET", "/api/nginx/proxy-hosts")
            case "npm_get_proxy_host":
                host_id = int(arguments["id"])
                return await self._request("GET", f"/api/nginx/proxy-hosts/{host_id}")
            case "npm_create_proxy_host":
                payload = {
                    "domain_names": arguments["domain_names"],
                    "forward_scheme": arguments["forward_scheme"],
                    "forward_host": arguments["forward_host"],
                    "forward_port": int(arguments["forward_port"]),
                    "ssl_forced": arguments.get("ssl_forced", False),
                }
                return await self._request("POST", "/api/nginx/proxy-hosts", json=payload)
            case "npm_delete_proxy_host":
                host_id = int(arguments["id"])
                return await self._request("DELETE", f"/api/nginx/proxy-hosts/{host_id}")
            case "npm_list_redirection_hosts":
                return await self._request("GET", "/api/nginx/redirection-hosts")
            case "npm_list_streams":
                return await self._request("GET", "/api/nginx/streams")
            case "npm_list_certificates":
                return await self._request("GET", "/api/nginx/certificates")
            case _:
                raise ToolExecutionError(tool_name, f"Unknown tool: {tool_name}")
