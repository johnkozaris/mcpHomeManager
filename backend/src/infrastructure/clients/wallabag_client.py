from typing import Any

from domain.entities.service_connection import ServiceType
from domain.entities.tool_definition import ToolDefinition
from domain.exceptions import ServiceConnectionError, ToolExecutionError
from infrastructure.clients.base_client import BaseServiceClient

_TOOLS = [
    ToolDefinition(
        name="wallabag_list_entries",
        http_method="GET",
        path_template="/api/entries.json",
        service_type=ServiceType.WALLABAG,
        description="List saved articles from Wallabag",
        parameters_schema={
            "type": "object",
            "properties": {
                "archive": {
                    "type": "integer",
                    "enum": [0, 1],
                    "description": "Filter by archived status (0=unread, 1=archived)",
                },
                "starred": {
                    "type": "integer",
                    "enum": [0, 1],
                    "description": "Filter by starred status (0=not starred, 1=starred)",
                },
                "perPage": {
                    "type": "integer",
                    "default": 30,
                    "description": "Number of entries per page",
                },
                "page": {
                    "type": "integer",
                    "default": 1,
                    "description": "Page number",
                },
            },
        },
    ),
    ToolDefinition(
        name="wallabag_get_entry",
        http_method="GET",
        path_template="/api/entries/{entry_id}.json",
        service_type=ServiceType.WALLABAG,
        description="Get a full Wallabag article by ID",
        parameters_schema={
            "type": "object",
            "properties": {
                "id": {"type": "integer", "description": "Entry ID"},
            },
            "required": ["id"],
        },
    ),
    ToolDefinition(
        name="wallabag_save_url",
        http_method="POST",
        path_template="/api/entries.json",
        service_type=ServiceType.WALLABAG,
        description="Save a URL to Wallabag for later reading",
        parameters_schema={
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL to save"},
            },
            "required": ["url"],
        },
    ),
    ToolDefinition(
        name="wallabag_delete_entry",
        http_method="DELETE",
        path_template="/api/entries/{entry_id}.json",
        service_type=ServiceType.WALLABAG,
        description="Delete a Wallabag article by ID",
        parameters_schema={
            "type": "object",
            "properties": {
                "id": {"type": "integer", "description": "Entry ID to delete"},
            },
            "required": ["id"],
        },
    ),
    ToolDefinition(
        name="wallabag_list_tags",
        http_method="GET",
        path_template="/api/tags.json",
        service_type=ServiceType.WALLABAG,
        description="List all tags in Wallabag",
        parameters_schema={"type": "object", "properties": {}},
    ),
    ToolDefinition(
        name="wallabag_tag_entry",
        http_method="POST",
        path_template="/api/entries/{entry_id}/tags.json",
        service_type=ServiceType.WALLABAG,
        description="Add tags to a Wallabag article",
        parameters_schema={
            "type": "object",
            "properties": {
                "id": {"type": "integer", "description": "Entry ID to tag"},
                "tags": {
                    "type": "string",
                    "description": "Comma-separated list of tags to add",
                },
            },
            "required": ["id", "tags"],
        },
    ),
    ToolDefinition(
        name="wallabag_search",
        http_method="GET",
        path_template="/api/search.json",
        service_type=ServiceType.WALLABAG,
        description="Search Wallabag articles by term",
        parameters_schema={
            "type": "object",
            "properties": {
                "term": {"type": "string", "description": "Search term"},
                "page": {
                    "type": "integer",
                    "default": 1,
                    "description": "Page number",
                },
                "perPage": {
                    "type": "integer",
                    "default": 30,
                    "description": "Number of results per page",
                },
            },
            "required": ["term"],
        },
    ),
]


class WallabagClient(BaseServiceClient):
    service_name = "wallabag"

    def __init__(self, base_url: str, api_token: str, **kwargs: Any) -> None:
        super().__init__(base_url, api_token, **kwargs)
        self._access_token: str | None = None

    def _build_headers(self, token: str) -> dict[str, str]:
        return {"Content-Type": "application/json"}

    async def _ensure_token(self) -> None:
        if self._access_token:
            return
        parts = self._api_token.split(":")
        if len(parts) < 4:
            raise ServiceConnectionError(
                self.service_name,
                "Token must be in client_id:client_secret:username:password format",
            )
        # Split into exactly 4 parts: password may contain colons
        client_id, client_secret, username = parts[0], parts[1], parts[2]
        password = ":".join(parts[3:])
        try:
            resp = await self._client.post(
                "/oauth/v2/token",
                data={
                    "grant_type": "password",
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "username": username,
                    "password": password,
                },
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            raise ServiceConnectionError(self.service_name, f"Authentication failed: {e}") from e
        token = data.get("access_token")
        if not token:
            raise ServiceConnectionError(self.service_name, "No access_token in OAuth response")
        self._access_token = token
        self._client.headers["Authorization"] = f"Bearer {self._access_token}"

    async def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        await self._ensure_token()
        return await super()._request(method, path, **kwargs)

    async def health_check(self) -> bool:
        result = await self._request("GET", "/api/entries.json?perPage=1")
        return isinstance(result, dict)

    def get_tool_definitions(self) -> list[ToolDefinition]:
        return list(_TOOLS)

    async def execute_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        match tool_name:
            case "wallabag_list_entries":
                params: dict[str, Any] = {}
                if "archive" in arguments:
                    params["archive"] = int(arguments["archive"])
                if "starred" in arguments:
                    params["starred"] = int(arguments["starred"])
                params["perPage"] = int(arguments.get("perPage", 30))
                params["page"] = int(arguments.get("page", 1))
                return await self._request("GET", "/api/entries.json", params=params)
            case "wallabag_get_entry":
                entry_id = int(arguments["id"])
                return await self._request("GET", f"/api/entries/{entry_id}.json")
            case "wallabag_save_url":
                url = arguments["url"]
                return await self._request("POST", "/api/entries.json", json={"url": url})
            case "wallabag_delete_entry":
                entry_id = int(arguments["id"])
                return await self._request("DELETE", f"/api/entries/{entry_id}.json")
            case "wallabag_list_tags":
                return await self._request("GET", "/api/tags.json")
            case "wallabag_tag_entry":
                entry_id = int(arguments["id"])
                tags = arguments["tags"]
                return await self._request(
                    "POST",
                    f"/api/entries/{entry_id}/tags.json",
                    json={"tags": tags},
                )
            case "wallabag_search":
                term = arguments["term"]
                page = int(arguments.get("page", 1))
                per_page = int(arguments.get("perPage", 30))
                return await self._request(
                    "GET",
                    "/api/search.json",
                    params={"term": term, "page": page, "perPage": per_page},
                )
            case _:
                raise ToolExecutionError(tool_name, f"Unknown tool: {tool_name}")
