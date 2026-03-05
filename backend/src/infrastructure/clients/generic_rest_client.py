"""Generic REST client that wraps arbitrary HTTP APIs as MCP tools."""

import asyncio
import ipaddress
import re
import socket
from typing import Any
from urllib.parse import quote, urlparse

import httpx

from domain.entities.generic_tool_spec import GenericToolSpec
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
    - Cloud metadata endpoints (169.254.169.254, metadata.google.internal)
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

        path = spec.path_template
        path_params = re.findall(r"\{(\w+)\}", path)
        remaining_args = dict(arguments)

        missing = [p for p in path_params if p not in remaining_args]
        if missing:
            raise ValueError(f"Missing required path parameters: {', '.join(missing)}")

        for param in path_params:
            value = str(remaining_args.pop(param))
            # Block path traversal
            if ".." in value or "/" in value or "\\" in value:
                raise ValueError(f"Invalid path parameter '{param}': contains forbidden characters")
            path = path.replace(f"{{{param}}}", quote(value, safe=""))

        method = spec.http_method.upper()
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
