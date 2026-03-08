import asyncio
import time
from typing import Any

import httpx

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

_DEFAULT_TOKEN_TYPE = "Bearer"  # noqa: S105 - OAuth token type, not a credential
_TOKEN_REFRESH_LEEWAY_SECONDS = 30.0


class WallabagClient(BaseServiceClient):
    service_name = "wallabag"

    def __init__(self, base_url: str, api_token: str, **kwargs: Any) -> None:
        super().__init__(base_url, api_token, **kwargs)
        self._access_token: str | None = None
        self._refresh_token: str | None = None
        self._token_expires_at: float | None = None
        self._token_type = _DEFAULT_TOKEN_TYPE
        self._token_lock = asyncio.Lock()

    def _build_headers(self, token: str) -> dict[str, str]:
        return {"Accept": "application/json"}

    @staticmethod
    def _parse_credentials(api_token: str) -> tuple[str, str, str, str]:
        parts = api_token.split(":")
        if len(parts) < 4:
            raise ServiceConnectionError(
                "wallabag",
                "Token must be in client_id:client_secret:username:password format",
            )
        client_id, client_secret, username = parts[0], parts[1], parts[2]
        password = ":".join(parts[3:])
        return client_id, client_secret, username, password

    @staticmethod
    def _normalize_token_type(token_type: Any) -> str:
        if isinstance(token_type, str) and token_type and token_type.lower() != "bearer":
            return token_type
        return _DEFAULT_TOKEN_TYPE

    @staticmethod
    def _compute_expiry_deadline(expires_in: Any) -> float | None:
        try:
            lifetime_seconds = float(expires_in)
        except (TypeError, ValueError):
            return None
        return time.monotonic() + max(lifetime_seconds - _TOKEN_REFRESH_LEEWAY_SECONDS, 0.0)

    def _is_token_current(self) -> bool:
        if not self._access_token:
            return False
        if self._token_expires_at is None:
            return True
        return time.monotonic() < self._token_expires_at

    def _clear_token_state(self, *, clear_refresh_token: bool) -> None:
        self._access_token = None
        self._token_expires_at = None
        self._client.headers.pop("Authorization", None)
        if clear_refresh_token:
            self._refresh_token = None

    def _apply_oauth_response(
        self, data: dict[str, Any], *, preserve_refresh_token: bool = False
    ) -> None:
        token = data.get("access_token")
        if not token:
            raise ServiceConnectionError(self.service_name, "No access_token in OAuth response")
        self._access_token = str(token)
        if not preserve_refresh_token or data.get("refresh_token"):
            refresh_token = data.get("refresh_token")
            self._refresh_token = str(refresh_token) if refresh_token else None
        self._token_expires_at = self._compute_expiry_deadline(data.get("expires_in"))
        self._token_type = self._normalize_token_type(data.get("token_type"))
        self._client.headers["Authorization"] = f"{self._token_type} {self._access_token}"

    async def _fetch_oauth_token(
        self, form_data: dict[str, str], *, preserve_refresh_token: bool = False
    ) -> None:
        previous_auth_header = self._client.headers.pop("Authorization", None)
        try:
            resp = await self._client.post(
                "/oauth/v2/token",
                data=form_data,
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            raise ServiceConnectionError(self.service_name, f"Authentication failed: {e}") from e
        finally:
            if previous_auth_header is not None:
                self._client.headers["Authorization"] = previous_auth_header
        self._apply_oauth_response(data, preserve_refresh_token=preserve_refresh_token)

    async def _authenticate_with_password(self) -> None:
        client_id, client_secret, username, password = self._parse_credentials(self._api_token)
        await self._fetch_oauth_token(
            {
                "grant_type": "password",
                "client_id": client_id,
                "client_secret": client_secret,
                "username": username,
                "password": password,
            }
        )

    async def _refresh_access_token(self) -> None:
        if not self._refresh_token:
            raise ServiceConnectionError(self.service_name, "No refresh_token in OAuth response")
        client_id, client_secret, _, _ = self._parse_credentials(self._api_token)
        await self._fetch_oauth_token(
            {
                "grant_type": "refresh_token",
                "client_id": client_id,
                "client_secret": client_secret,
                "refresh_token": self._refresh_token,
            },
            preserve_refresh_token=True,
        )

    async def _ensure_token(self) -> None:
        async with self._token_lock:
            if self._is_token_current():
                return
            if self._refresh_token:
                try:
                    await self._refresh_access_token()
                    return
                except ServiceConnectionError:
                    self._clear_token_state(clear_refresh_token=True)
            await self._authenticate_with_password()

    async def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        await self._ensure_token()
        try:
            response = await self._client.request(method, path, **kwargs)
            if response.status_code == 401:
                self._clear_token_state(clear_refresh_token=False)
                await self._ensure_token()
                response = await self._client.request(method, path, **kwargs)
            response.raise_for_status()
            if response.headers.get("content-type", "").startswith("application/json"):
                try:
                    return response.json()
                except Exception:
                    return response.text
            return response.text
        except httpx.ConnectError as e:
            raise ServiceConnectionError(self.service_name, f"Cannot connect: {e}") from e
        except httpx.TimeoutException as e:
            raise ServiceConnectionError(self.service_name, f"Timeout: {e}") from e
        except httpx.HTTPStatusError as e:
            raise ToolExecutionError(
                self.service_name,
                f"HTTP {e.response.status_code}: {e.response.text[:200]}",
            ) from e
        except ServiceConnectionError, ToolExecutionError:
            raise
        except Exception as e:
            raise ServiceConnectionError(
                self.service_name, f"Unexpected error: {type(e).__name__}: {e}"
            ) from e

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
                return await self._request("POST", "/api/entries.json", params={"url": url})
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
                    params={"tags": tags},
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
