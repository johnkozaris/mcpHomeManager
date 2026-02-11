from typing import Any

from domain.entities.service_connection import ServiceType
from domain.entities.tool_definition import ToolDefinition
from domain.exceptions import ServiceConnectionError, ToolExecutionError
from infrastructure.clients.base_client import BaseServiceClient

_TOOLS = [
    ToolDefinition(
        name="portainer_list_endpoints",
        service_type=ServiceType.PORTAINER,
        description="List all Docker/Kubernetes environments managed by Portainer",
        parameters_schema={"type": "object", "properties": {}},
    ),
    ToolDefinition(
        name="portainer_list_containers",
        service_type=ServiceType.PORTAINER,
        description="List all containers in a Docker environment",
        parameters_schema={
            "type": "object",
            "properties": {
                "endpoint_id": {
                    "type": "integer",
                    "description": "Portainer environment/endpoint ID",
                },
            },
            "required": ["endpoint_id"],
        },
    ),
    ToolDefinition(
        name="portainer_get_container",
        service_type=ServiceType.PORTAINER,
        description="Get detailed information about a specific container",
        parameters_schema={
            "type": "object",
            "properties": {
                "endpoint_id": {
                    "type": "integer",
                    "description": "Portainer environment/endpoint ID",
                },
                "container_id": {
                    "type": "string",
                    "description": "Container ID or name",
                },
            },
            "required": ["endpoint_id", "container_id"],
        },
    ),
    ToolDefinition(
        name="portainer_start_container",
        service_type=ServiceType.PORTAINER,
        description="Start a stopped container",
        parameters_schema={
            "type": "object",
            "properties": {
                "endpoint_id": {
                    "type": "integer",
                    "description": "Portainer environment/endpoint ID",
                },
                "container_id": {
                    "type": "string",
                    "description": "Container ID or name",
                },
            },
            "required": ["endpoint_id", "container_id"],
        },
    ),
    ToolDefinition(
        name="portainer_stop_container",
        service_type=ServiceType.PORTAINER,
        description="Stop a running container",
        parameters_schema={
            "type": "object",
            "properties": {
                "endpoint_id": {
                    "type": "integer",
                    "description": "Portainer environment/endpoint ID",
                },
                "container_id": {
                    "type": "string",
                    "description": "Container ID or name",
                },
            },
            "required": ["endpoint_id", "container_id"],
        },
    ),
    ToolDefinition(
        name="portainer_restart_container",
        service_type=ServiceType.PORTAINER,
        description="Restart a container",
        parameters_schema={
            "type": "object",
            "properties": {
                "endpoint_id": {
                    "type": "integer",
                    "description": "Portainer environment/endpoint ID",
                },
                "container_id": {
                    "type": "string",
                    "description": "Container ID or name",
                },
            },
            "required": ["endpoint_id", "container_id"],
        },
    ),
    ToolDefinition(
        name="portainer_list_stacks",
        service_type=ServiceType.PORTAINER,
        description="List all Docker Compose stacks managed by Portainer",
        parameters_schema={"type": "object", "properties": {}},
    ),
    ToolDefinition(
        name="portainer_get_container_logs",
        service_type=ServiceType.PORTAINER,
        description="Get recent logs from a container",
        parameters_schema={
            "type": "object",
            "properties": {
                "endpoint_id": {
                    "type": "integer",
                    "description": "Portainer environment/endpoint ID",
                },
                "container_id": {
                    "type": "string",
                    "description": "Container ID or name",
                },
                "tail": {
                    "type": "integer",
                    "default": 100,
                    "description": "Number of log lines to return from the end",
                },
            },
            "required": ["endpoint_id", "container_id"],
        },
    ),
]


class PortainerClient(BaseServiceClient):
    service_name = "portainer"

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
                self.service_name, "Token must be in username:password format"
            )
        username, password = parts
        try:
            resp = await self._client.post(
                "/api/auth", json={"Username": username, "Password": password}
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            raise ServiceConnectionError(self.service_name, f"Authentication failed: {e}") from e
        token = data.get("jwt")
        if not token:
            raise ServiceConnectionError(self.service_name, "No jwt in auth response")
        self._jwt = token
        self._client.headers["Authorization"] = f"Bearer {self._jwt}"

    async def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        await self._ensure_jwt()
        return await super()._request(method, path, **kwargs)

    async def health_check(self) -> bool:
        result = await self._request("GET", "/api/endpoints")
        return isinstance(result, list)

    def get_tool_definitions(self) -> list[ToolDefinition]:
        return list(_TOOLS)

    def _validate_endpoint_id(self, arguments: dict[str, Any]) -> int:
        endpoint_id = arguments["endpoint_id"]
        try:
            return int(endpoint_id)
        except (ValueError, TypeError) as e:
            raise ToolExecutionError(
                "endpoint_id", f"endpoint_id must be an integer: {endpoint_id!r}"
            ) from e

    async def execute_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        match tool_name:
            case "portainer_list_endpoints":
                return await self._request("GET", "/api/endpoints")
            case "portainer_list_containers":
                eid = self._validate_endpoint_id(arguments)
                return await self._request(
                    "GET",
                    f"/api/endpoints/{eid}/docker/containers/json",
                    params={"all": "true"},
                )
            case "portainer_get_container":
                eid = self._validate_endpoint_id(arguments)
                cid = self._validate_path_segment(arguments["container_id"], "container_id")
                return await self._request(
                    "GET", f"/api/endpoints/{eid}/docker/containers/{cid}/json"
                )
            case "portainer_start_container":
                eid = self._validate_endpoint_id(arguments)
                cid = self._validate_path_segment(arguments["container_id"], "container_id")
                return await self._request(
                    "POST", f"/api/endpoints/{eid}/docker/containers/{cid}/start"
                )
            case "portainer_stop_container":
                eid = self._validate_endpoint_id(arguments)
                cid = self._validate_path_segment(arguments["container_id"], "container_id")
                return await self._request(
                    "POST", f"/api/endpoints/{eid}/docker/containers/{cid}/stop"
                )
            case "portainer_restart_container":
                eid = self._validate_endpoint_id(arguments)
                cid = self._validate_path_segment(arguments["container_id"], "container_id")
                return await self._request(
                    "POST", f"/api/endpoints/{eid}/docker/containers/{cid}/restart"
                )
            case "portainer_list_stacks":
                return await self._request("GET", "/api/stacks")
            case "portainer_get_container_logs":
                eid = self._validate_endpoint_id(arguments)
                cid = self._validate_path_segment(arguments["container_id"], "container_id")
                tail = int(arguments.get("tail", 100))
                return await self._request(
                    "GET",
                    f"/api/endpoints/{eid}/docker/containers/{cid}/logs",
                    params={"stdout": "true", "stderr": "true", "tail": str(tail)},
                )
            case _:
                raise ToolExecutionError(tool_name, f"Unknown tool: {tool_name}")
