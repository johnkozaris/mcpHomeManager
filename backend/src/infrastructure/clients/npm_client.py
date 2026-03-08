from typing import Any

from domain.entities.service_connection import ServiceType
from domain.entities.tool_definition import ToolDefinition
from domain.exceptions import ServiceConnectionError, ToolExecutionError
from infrastructure.clients.base_client import BaseServiceClient

_PROXY_HOST_EXPANDS = ("access_list", "owner", "certificate")
_REDIRECTION_HOST_EXPANDS = ("owner", "certificate")
_STREAM_EXPANDS = ("owner", "certificate")
_CERTIFICATE_EXPANDS = ("owner",)


def _expand_schema(options: tuple[str, ...]) -> dict[str, Any]:
    return {
        "type": "array",
        "items": {
            "type": "string",
            "enum": list(options),
        },
        "description": "Optional related records to expand in the response",
    }


def _list_params_schema(*, expand_options: tuple[str, ...]) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "expand": _expand_schema(expand_options),
            "query": {
                "type": "string",
                "description": "Optional server-side search query for the current "
                "Nginx Proxy Manager route",
            },
        },
    }


_TOOLS = [
    ToolDefinition(
        name="npm_list_proxy_hosts",
        http_method="GET",
        path_template="/api/nginx/proxy-hosts",
        service_type=ServiceType.NGINX_PROXY_MANAGER,
        description="List all proxy hosts configured in Nginx Proxy Manager",
        parameters_schema=_list_params_schema(expand_options=_PROXY_HOST_EXPANDS),
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
                "expand": _expand_schema(_PROXY_HOST_EXPANDS),
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
                "certificate_id": {
                    "oneOf": [
                        {"type": "integer"},
                        {"type": "string", "enum": ["new"]},
                    ],
                    "description": 'Certificate ID to attach, or "new" to request a '
                    "new certificate",
                },
                "hsts_enabled": {
                    "type": "boolean",
                    "description": "Enable HSTS headers",
                },
                "hsts_subdomains": {
                    "type": "boolean",
                    "description": "Include subdomains in HSTS",
                },
                "trust_forwarded_proto": {
                    "type": "boolean",
                    "description": "Trust forwarded proto headers from upstream proxies",
                },
                "http2_support": {
                    "type": "boolean",
                    "description": "Enable HTTP/2 support",
                },
                "block_exploits": {
                    "type": "boolean",
                    "description": "Enable NPM's exploit blocking rules",
                },
                "caching_enabled": {
                    "type": "boolean",
                    "description": "Enable response caching",
                },
                "allow_websocket_upgrade": {
                    "type": "boolean",
                    "description": "Allow websocket upgrades for all paths",
                },
                "access_list_id": {
                    "type": "integer",
                    "description": "Access list ID applied to this proxy host",
                },
                "advanced_config": {
                    "type": "string",
                    "description": "Advanced Nginx configuration snippet",
                },
                "enabled": {
                    "type": "boolean",
                    "description": "Whether the proxy host is enabled",
                },
                "meta": {
                    "type": "object",
                    "description": "Optional NPM metadata object",
                },
                "locations": {
                    "type": "array",
                    "description": "Optional custom location overrides",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "integer"},
                            "path": {"type": "string"},
                            "forward_scheme": {
                                "type": "string",
                                "enum": ["http", "https"],
                            },
                            "forward_host": {"type": "string"},
                            "forward_port": {"type": "integer"},
                            "forward_path": {"type": "string"},
                            "advanced_config": {"type": "string"},
                        },
                        "required": [
                            "path",
                            "forward_scheme",
                            "forward_host",
                            "forward_port",
                        ],
                    },
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
        parameters_schema=_list_params_schema(expand_options=_REDIRECTION_HOST_EXPANDS),
    ),
    ToolDefinition(
        name="npm_list_streams",
        http_method="GET",
        path_template="/api/nginx/streams",
        service_type=ServiceType.NGINX_PROXY_MANAGER,
        description="List all TCP/UDP stream proxies",
        parameters_schema=_list_params_schema(expand_options=_STREAM_EXPANDS),
    ),
    ToolDefinition(
        name="npm_list_certificates",
        http_method="GET",
        path_template="/api/nginx/certificates",
        service_type=ServiceType.NGINX_PROXY_MANAGER,
        description="List all SSL certificates",
        parameters_schema=_list_params_schema(expand_options=_CERTIFICATE_EXPANDS),
    ),
]


class NginxProxyManagerClient(BaseServiceClient):
    service_name = "nginxproxymanager"
    _EXPAND_OPTIONS_BY_TOOL = {
        "npm_list_proxy_hosts": set(_PROXY_HOST_EXPANDS),
        "npm_get_proxy_host": set(_PROXY_HOST_EXPANDS),
        "npm_list_redirection_hosts": set(_REDIRECTION_HOST_EXPANDS),
        "npm_list_streams": set(_STREAM_EXPANDS),
        "npm_list_certificates": set(_CERTIFICATE_EXPANDS),
    }
    _QUERY_TOOLS = {
        "npm_list_proxy_hosts",
        "npm_list_redirection_hosts",
        "npm_list_streams",
        "npm_list_certificates",
    }
    _PROXY_HOST_OPTIONAL_FIELDS = (
        "ssl_forced",
        "certificate_id",
        "hsts_enabled",
        "hsts_subdomains",
        "trust_forwarded_proto",
        "http2_support",
        "block_exploits",
        "caching_enabled",
        "allow_websocket_upgrade",
        "access_list_id",
        "advanced_config",
        "enabled",
        "meta",
        "locations",
    )
    _PROXY_HOST_INTEGER_FIELDS = {"access_list_id"}

    def __init__(self, base_url: str, api_token: str, **kwargs: Any) -> None:
        super().__init__(base_url, api_token, **kwargs)
        self._jwt: str | None = None

    def _build_headers(self, token: str) -> dict[str, str]:
        return {"Content-Type": "application/json"}

    def _extract_token(self, data: Any) -> str:
        if not isinstance(data, dict):
            raise ServiceConnectionError(
                self.service_name,
                "Unexpected /api/tokens response; expected a JSON object "
                "with a token or 2FA challenge",
            )

        token = data.get("token")
        if isinstance(token, str) and token:
            return token

        if data.get("requires_2fa") is True:
            raise ServiceConnectionError(
                self.service_name,
                "This Nginx Proxy Manager account requires 2FA. "
                "MCP Home Manager currently supports only non-2FA accounts "
                "and cannot complete the /api/tokens/2fa challenge flow.",
            )

        raise ServiceConnectionError(
            self.service_name,
            "Unexpected /api/tokens response; expected a token or requires_2fa challenge",
        )

    def _clear_jwt(self) -> None:
        self._jwt = None
        self._client.headers.pop("Authorization", None)

    @classmethod
    def _build_request_params(
        cls, tool_name: str, arguments: dict[str, Any]
    ) -> dict[str, str] | None:
        params: dict[str, str] = {}

        raw_query = arguments.get("query")
        if raw_query is not None:
            if tool_name not in cls._QUERY_TOOLS:
                raise ToolExecutionError(tool_name, "query is not supported for this tool")
            if not isinstance(raw_query, str):
                raise ToolExecutionError(tool_name, "query must be a string")
            query = raw_query.strip()
            if not query:
                raise ToolExecutionError(tool_name, "query must not be empty")
            params["query"] = query

        raw_expand = arguments.get("expand")
        if raw_expand is None:
            return params or None

        if isinstance(raw_expand, str):
            expand_values = [raw_expand]
        elif isinstance(raw_expand, list) and all(isinstance(value, str) for value in raw_expand):
            expand_values = raw_expand
        else:
            raise ToolExecutionError(
                tool_name, "expand must be a string or list of strings"
            )

        allowed_values = cls._EXPAND_OPTIONS_BY_TOOL.get(tool_name)
        if not allowed_values:
            raise ToolExecutionError(tool_name, "expand is not supported for this tool")

        invalid = [value for value in expand_values if value not in allowed_values]
        if invalid:
            raise ToolExecutionError(
                tool_name,
                "Unsupported expand value(s): " + ", ".join(sorted(set(invalid))),
            )

        if not expand_values:
            return params or None
        params["expand"] = ",".join(expand_values)
        return params

    @classmethod
    def _build_proxy_host_payload(cls, arguments: dict[str, Any]) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "domain_names": arguments["domain_names"],
            "forward_scheme": arguments["forward_scheme"],
            "forward_host": arguments["forward_host"],
            "forward_port": int(arguments["forward_port"]),
        }
        for field in cls._PROXY_HOST_OPTIONAL_FIELDS:
            if field not in arguments:
                continue
            value = arguments[field]
            if value is not None and (
                field in cls._PROXY_HOST_INTEGER_FIELDS
                or (field == "certificate_id" and value != "new")
            ):
                value = int(value)
            payload[field] = value
        if "ssl_forced" not in payload:
            payload["ssl_forced"] = False
        return payload

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
        token = self._extract_token(data)
        self._jwt = token
        self._client.headers["Authorization"] = f"Bearer {self._jwt}"

    async def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        await self._ensure_jwt()
        try:
            return await super()._request(method, path, **kwargs)
        except ToolExecutionError as e:
            if "HTTP 401:" not in str(e):
                raise
        self._clear_jwt()
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
                return await self._request(
                    "GET",
                    "/api/nginx/proxy-hosts",
                    params=self._build_request_params(tool_name, arguments),
                )
            case "npm_get_proxy_host":
                host_id = int(arguments["id"])
                return await self._request(
                    "GET",
                    f"/api/nginx/proxy-hosts/{host_id}",
                    params=self._build_request_params(tool_name, arguments),
                )
            case "npm_create_proxy_host":
                payload = self._build_proxy_host_payload(arguments)
                return await self._request("POST", "/api/nginx/proxy-hosts", json=payload)
            case "npm_delete_proxy_host":
                host_id = int(arguments["id"])
                return await self._request("DELETE", f"/api/nginx/proxy-hosts/{host_id}")
            case "npm_list_redirection_hosts":
                return await self._request(
                    "GET",
                    "/api/nginx/redirection-hosts",
                    params=self._build_request_params(tool_name, arguments),
                )
            case "npm_list_streams":
                return await self._request(
                    "GET",
                    "/api/nginx/streams",
                    params=self._build_request_params(tool_name, arguments),
                )
            case "npm_list_certificates":
                return await self._request(
                    "GET",
                    "/api/nginx/certificates",
                    params=self._build_request_params(tool_name, arguments),
                )
            case _:
                raise ToolExecutionError(tool_name, f"Unknown tool: {tool_name}")
