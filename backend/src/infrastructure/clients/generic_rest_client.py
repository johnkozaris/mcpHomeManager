"""Generic REST client that wraps arbitrary HTTP APIs as MCP tools."""

import asyncio
import ipaddress
import re
import socket
from typing import Any
from urllib.parse import quote, urlparse

import httpx

from domain.entities.generic_tool_spec import REQUEST_SHAPE_METADATA_KEY, GenericToolSpec
from domain.entities.service_connection import ServiceType
from domain.entities.tool_definition import ToolDefinition
from domain.exceptions import ToolExecutionError
from domain.ports.service_client import IServiceClient

# Cloud metadata endpoints — dangerous even in self-hosted contexts
# (Docker on cloud VMs can reach the host's metadata service).
_METADATA_HOSTNAMES = frozenset({"metadata.google.internal", "metadata"})
_METADATA_IP = ipaddress.ip_address("169.254.169.254")


def _is_metadata_ip(host: str) -> bool:
    """Check if a host string resolves to the cloud metadata IP.

    Handles IPv4, IPv6, and IPv4-mapped IPv6 (::ffff:169.254.169.254).
    """
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return False
    # Unwrap IPv4-mapped IPv6 addresses (e.g. ::ffff:169.254.169.254)
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped:
        ip = ip.ipv4_mapped
    return ip == _METADATA_IP


async def validate_base_url(base_url: str) -> None:
    """Validate a base URL for basic safety.

    MCP Home Manager is a self-hosted homelab gateway, so private/internal IPs
    are expected and allowed. We only block:
    - Non-HTTP(S) schemes
    - Cloud metadata endpoints (169.254.169.254, metadata.google.internal, metadata)
    """
    parsed = urlparse(base_url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError(f"Invalid URL scheme: {parsed.scheme}")
    host = parsed.hostname or ""
    if not host:
        raise ValueError("URL must have a hostname")
    if host.lower() in _METADATA_HOSTNAMES:
        raise ValueError(f"Access to cloud metadata endpoint blocked: {host}")
    if _is_metadata_ip(host):
        raise ValueError(f"Access to cloud metadata endpoint blocked: {host}")

    # DNS resolution check: catch hostnames that resolve to the metadata IP
    # (DNS rebinding attack). Failure is fine — homelab hostnames may not resolve.
    try:
        loop = asyncio.get_running_loop()
        addrinfo = await loop.getaddrinfo(
            host,
            None,
            family=socket.AF_UNSPEC,
            type=socket.SOCK_STREAM,
        )
        for _, _, _, _, sockaddr in addrinfo:
            if _is_metadata_ip(sockaddr[0]):
                raise ValueError(f"DNS for '{host}' resolves to cloud metadata IP")
    except socket.gaierror:
        pass  # DNS failure is fine for homelab hostnames


class GenericRestClient(IServiceClient):
    """A client that executes tools defined by GenericToolSpec against a base URL."""

    def __init__(
        self,
        base_url: str,
        api_token: str,
        tool_definitions: list[GenericToolSpec] | None = None,
        *,
        health_check_path: str = "/",
        config: dict[str, Any] | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_token = api_token
        self._tool_specs = tool_definitions or []

        _config = config or {}
        custom_headers = {
            k: v
            for k, v in (_config.get("headers", {}) or {}).items()
            if k.lower() not in ("host", "content-length", "transfer-encoding")
        }
        if _config.get("health_check_path"):
            health_check_path = _config["health_check_path"]
        self._health_check_path = health_check_path

        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            headers={
                **custom_headers,
                "Authorization": f"Bearer {api_token}",
                "Content-Type": "application/json",
            },
            timeout=30.0,
            follow_redirects=False,
        )

    async def health_check(self) -> bool:
        try:
            resp = await self._client.get(self._health_check_path)
            return resp.status_code < 500
        except Exception:
            return False

    async def execute_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        spec = next((s for s in self._tool_specs if s.tool_name == tool_name), None)
        if spec is None:
            raise ToolExecutionError(tool_name, f"Unknown tool: {tool_name}")

        method = spec.http_method.upper()
        request_shape = spec.params_schema.get(REQUEST_SHAPE_METADATA_KEY)
        if isinstance(request_shape, dict):
            path, request_kwargs = self._build_imported_request(spec, arguments, request_shape)
            resp = await self._client.request(method, path, **request_kwargs)
        else:
            path, remaining_args = self._interpolate_path(spec.path_template, arguments)
            if method == "GET":
                resp = await self._client.get(path, params=remaining_args)
            elif method == "DELETE":
                resp = await self._client.delete(path, params=remaining_args)
            elif method in ("POST", "PUT", "PATCH"):
                resp = await self._client.request(method, path, json=remaining_args)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise ToolExecutionError(
                tool_name,
                f"HTTP {e.response.status_code}: {e.response.text[:200]}",
            ) from e
        try:
            return resp.json()
        except Exception:
            return resp.text

    def _build_imported_request(
        self,
        spec: GenericToolSpec,
        arguments: dict[str, Any],
        request_shape: dict[str, Any],
    ) -> tuple[str, dict[str, Any]]:
        parameter_metadata = request_shape.get("parameters", {})
        path_args = {
            name: value
            for name, value in arguments.items()
            if isinstance(parameter_metadata, dict)
            and isinstance(parameter_metadata.get(name), dict)
            and parameter_metadata[name].get("in") == "path"
        }
        path, remaining_args = self._interpolate_path(
            spec.path_template,
            arguments,
            explicit_path_args=path_args,
        )

        params: dict[str, Any] = {}
        headers: dict[str, Any] = {}
        cookies: dict[str, Any] = {}
        body_args: dict[str, Any] = {}

        for name, value in list(remaining_args.items()):
            metadata = (
                parameter_metadata.get(name, {})
                if isinstance(parameter_metadata, dict)
                else {}
            )
            location = metadata.get("in")
            if location == "query":
                params[name] = value
                remaining_args.pop(name)
            elif location == "header":
                header_name = metadata.get("name", name)
                headers[header_name] = value
                remaining_args.pop(name)
            elif location == "cookie":
                cookie_name = metadata.get("name", name)
                cookies[cookie_name] = value
                remaining_args.pop(name)

        body_metadata = request_shape.get("body", {})
        body_property_names = body_metadata.get("propertyNames", [])
        if isinstance(body_property_names, list):
            for name in body_property_names:
                if name in remaining_args:
                    body_args[name] = remaining_args.pop(name)

        request_kwargs: dict[str, Any] = {}
        if params:
            request_kwargs["params"] = params
        if headers:
            request_kwargs["headers"] = headers
        if cookies:
            request_kwargs["cookies"] = cookies

        encoding = body_metadata.get("encoding")
        if encoding == "json":
            json_body = {**body_args, **remaining_args}
            if json_body:
                request_kwargs["json"] = json_body
        elif encoding == "form-urlencoded":
            form_body = {**body_args, **remaining_args}
            if form_body:
                request_kwargs["data"] = form_body
            remaining_args = {}
            request_headers = dict(request_kwargs.get("headers", {}))
            request_headers["Content-Type"] = body_metadata.get(
                "mediaType",
                "application/x-www-form-urlencoded",
            )
            request_kwargs["headers"] = request_headers
        elif remaining_args:
            if spec.http_method.upper() in {"GET", "DELETE"}:
                request_kwargs["params"] = {**request_kwargs.get("params", {}), **remaining_args}
            else:
                request_kwargs["json"] = remaining_args

        return path, request_kwargs

    def _interpolate_path(
        self,
        path_template: str,
        arguments: dict[str, Any],
        *,
        explicit_path_args: dict[str, Any] | None = None,
    ) -> tuple[str, dict[str, Any]]:
        path = path_template
        path_params = re.findall(r"\{([^}]+)\}", path)
        remaining_args = dict(arguments)
        path_values = explicit_path_args or {
            name: remaining_args[name] for name in path_params if name in remaining_args
        }

        missing = [param for param in path_params if param not in path_values]
        if missing:
            raise ValueError(f"Missing required path parameters: {', '.join(missing)}")

        for param in path_params:
            value = str(path_values[param])
            if ".." in value or "/" in value or "\\" in value:
                raise ValueError(f"Invalid path parameter '{param}': contains forbidden characters")
            path = path.replace(f"{{{param}}}", quote(value, safe=""))
            remaining_args.pop(param, None)

        return path, remaining_args

    def get_tool_definitions(self) -> list[ToolDefinition]:
        return [
            ToolDefinition(
                name=spec.tool_name,
                service_type=ServiceType.GENERIC_REST,
                description=spec.description,
                parameters_schema=spec.params_schema,
            )
            for spec in self._tool_specs
        ]

    async def close(self) -> None:
        await self._client.aclose()
