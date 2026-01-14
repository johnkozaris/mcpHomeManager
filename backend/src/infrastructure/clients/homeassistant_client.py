from collections import defaultdict
from typing import Any

from domain.entities.app_definition import AppDefinition
from domain.entities.service_connection import ServiceType
from domain.entities.tool_definition import ToolDefinition
from domain.exceptions import ToolExecutionError
from domain.ports.app_provider import IAppProvider
from infrastructure.clients.base_client import BaseServiceClient

_TOOLS = [
    ToolDefinition(
        name="ha_get_entity_state",
        service_type=ServiceType.HOME_ASSISTANT,
        description="Get the current state of a Home Assistant entity",
        parameters_schema={
            "type": "object",
            "properties": {
                "entity_id": {
                    "type": "string",
                    "description": "Entity ID (e.g. light.living_room, sensor.temperature)",
                },
            },
            "required": ["entity_id"],
        },
    ),
    ToolDefinition(
        name="ha_list_entities",
        service_type=ServiceType.HOME_ASSISTANT,
        description="List all Home Assistant entities, optionally filtered by domain",
        parameters_schema={
            "type": "object",
            "properties": {
                "domain": {
                    "type": "string",
                    "description": "Filter by domain (e.g. light, switch, sensor, climate)",
                },
            },
        },
    ),
    ToolDefinition(
        name="ha_call_service",
        service_type=ServiceType.HOME_ASSISTANT,
        description="Call a Home Assistant service (e.g. turn_on, turn_off, set_temperature)",
        parameters_schema={
            "type": "object",
            "properties": {
                "domain": {
                    "type": "string",
                    "description": "Service domain (e.g. light, switch, climate)",
                },
                "service": {
                    "type": "string",
                    "description": "Service name (e.g. turn_on, turn_off, toggle)",
                },
                "entity_id": {"type": "string", "description": "Target entity ID"},
                "data": {
                    "type": "object",
                    "description": "Additional service data (e.g. brightness, temperature)",
                },
            },
            "required": ["domain", "service"],
        },
    ),
    ToolDefinition(
        name="ha_get_services",
        service_type=ServiceType.HOME_ASSISTANT,
        description="List all available Home Assistant services and their parameters",
        parameters_schema={
            "type": "object",
            "properties": {
                "domain": {"type": "string", "description": "Filter by domain"},
            },
        },
    ),
]


_APPS = [
    AppDefinition(
        name="ha_entity_dashboard",
        service_type="homeassistant",
        title="Entity Dashboard",
        description="Interactive grid of Home Assistant entities grouped by domain",
        template_name="ha_entities.html",
        parameters_schema={
            "type": "object",
            "properties": {
                "domain": {
                    "type": "string",
                    "description": "Filter by entity domain (e.g. light, sensor, climate)",
                },
            },
        },
    ),
]


class HomeAssistantClient(BaseServiceClient, IAppProvider):
    service_name = "homeassistant"

    def _build_headers(self, token: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    async def health_check(self) -> bool:
        result = await self._request("GET", "/api/")
        return isinstance(result, dict) and "message" in result

    def get_tool_definitions(self) -> list[ToolDefinition]:
        return list(_TOOLS)

    async def execute_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        match tool_name:
            case "ha_get_entity_state":
                entity_id = self._validate_path_segment(arguments["entity_id"], "entity_id")
                return await self._request("GET", f"/api/states/{entity_id}")
            case "ha_list_entities":
                states = await self._request("GET", "/api/states")
                domain = arguments.get("domain")
                if domain:
                    states = [s for s in states if s.get("entity_id", "").startswith(f"{domain}.")]
                return [
                    {
                        "entity_id": s["entity_id"],
                        "state": s["state"],
                        "friendly_name": s.get("attributes", {}).get("friendly_name"),
                    }
                    for s in states
                ]
            case "ha_call_service":
                payload: dict[str, Any] = {}
                if target_entity := arguments.get("entity_id"):
                    payload["entity_id"] = target_entity
                if data := arguments.get("data"):
                    payload.update(data)
                ha_domain = self._validate_path_segment(arguments["domain"], "domain")
                ha_service = self._validate_path_segment(arguments["service"], "service")
                return await self._request(
                    "POST",
                    f"/api/services/{ha_domain}/{ha_service}",
                    json=payload,
                )
            case "ha_get_services":
                services = await self._request("GET", "/api/services")
                domain = arguments.get("domain")
                if domain:
                    services = [s for s in services if s.get("domain") == domain]
                return services
            case _:
                raise ToolExecutionError(tool_name, f"Unknown tool: {tool_name}")

    # --- IAppProvider ---

    def get_app_definitions(self) -> list[AppDefinition]:
        return list(_APPS)

    async def fetch_app_data(self, app_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if app_name != "ha_entity_dashboard":
            raise ToolExecutionError(app_name, f"Unknown app: {app_name}")

        states = await self._request("GET", "/api/states")
        domain_filter = arguments.get("domain")
        if domain_filter:
            states = [s for s in states if s.get("entity_id", "").startswith(f"{domain_filter}.")]

        domains: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for s in states:
            entity_id = s.get("entity_id", "")
            d = entity_id.split(".")[0] if "." in entity_id else "other"
            domains[d].append(
                {
                    "entity_id": entity_id,
                    "state": s.get("state", "unknown"),
                    "friendly_name": s.get("attributes", {}).get("friendly_name"),
                }
            )

        return {
            "domains": dict(sorted(domains.items())),
            "entity_count": sum(len(v) for v in domains.values()),
            "domain_filter": domain_filter,
        }

    async def handle_app_action(
        self,
        app_name: str,
        action: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        if app_name != "ha_entity_dashboard":
            raise ToolExecutionError(app_name, f"Unknown app: {app_name}")
        if action == "call_service":
            domain = self._validate_path_segment(payload["domain"], "domain")
            service = self._validate_path_segment(payload["service"], "service")
            svc_data: dict[str, Any] = {}
            if entity_id := payload.get("entity_id"):
                svc_data["entity_id"] = entity_id
            await self._request("POST", f"/api/services/{domain}/{service}", json=svc_data)
        return await self.fetch_app_data(app_name, payload.get("refresh_args", {}))
