import json
from typing import Any
from urllib.parse import urlsplit, urlunsplit

from domain.entities.service_connection import ServiceType
from domain.entities.tool_definition import ToolDefinition
from domain.exceptions import ServiceConnectionError, ToolExecutionError
from infrastructure.clients.base_client import BaseServiceClient

_GREADER_PATH = "/api/greader.php"
_READER_API_PATH = "/reader/api/0"

_TOOLS = [
    ToolDefinition(
        name="freshrss_list_feeds",
        http_method="GET",
        path_template="/api/greader.php/reader/api/0/subscription/list",
        service_type=ServiceType.FRESHRSS,
        description="List all subscribed RSS feeds",
        parameters_schema={"type": "object", "properties": {}},
    ),
    ToolDefinition(
        name="freshrss_get_unread_count",
        http_method="GET",
        path_template="/api/greader.php/reader/api/0/unread-count",
        service_type=ServiceType.FRESHRSS,
        description="Get unread article counts per feed",
        parameters_schema={"type": "object", "properties": {}},
    ),
    ToolDefinition(
        name="freshrss_get_articles",
        http_method="GET",
        path_template="/api/greader.php/reader/api/0/stream/contents/user/-/state/com.google/reading-list",
        service_type=ServiceType.FRESHRSS,
        description="Get recent articles from all feeds",
        parameters_schema={
            "type": "object",
            "properties": {
                "count": {
                    "type": "integer",
                    "default": 20,
                    "description": "Number of articles to retrieve",
                },
            },
        },
    ),
    ToolDefinition(
        name="freshrss_get_unread",
        http_method="GET",
        path_template="/api/greader.php/reader/api/0/stream/contents/user/-/state/com.google/reading-list",
        service_type=ServiceType.FRESHRSS,
        description="Get unread articles only",
        parameters_schema={
            "type": "object",
            "properties": {
                "count": {
                    "type": "integer",
                    "default": 20,
                    "description": "Number of unread articles to retrieve",
                },
            },
        },
    ),
    ToolDefinition(
        name="freshrss_mark_read",
        http_method="POST",
        path_template="/api/greader.php/reader/api/0/edit-tag",
        service_type=ServiceType.FRESHRSS,
        description="Mark an article as read",
        parameters_schema={
            "type": "object",
            "properties": {
                "item_id": {"type": "string", "description": "Article item ID to mark as read"},
            },
            "required": ["item_id"],
        },
    ),
    ToolDefinition(
        name="freshrss_star_article",
        http_method="POST",
        path_template="/api/greader.php/reader/api/0/edit-tag",
        service_type=ServiceType.FRESHRSS,
        description="Star/bookmark an article",
        parameters_schema={
            "type": "object",
            "properties": {
                "item_id": {"type": "string", "description": "Article item ID to star"},
            },
            "required": ["item_id"],
        },
    ),
    ToolDefinition(
        name="freshrss_add_feed",
        http_method="POST",
        path_template="/api/greader.php/reader/api/0/subscription/quickadd",
        service_type=ServiceType.FRESHRSS,
        description="Subscribe to a new RSS feed by URL",
        parameters_schema={
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "Feed URL to subscribe to"},
            },
            "required": ["url"],
        },
    ),
]


class FreshRSSClient(BaseServiceClient):
    service_name = "freshrss"

    def __init__(self, base_url: str, api_token: str, **kwargs: Any) -> None:
        normalized_base_url, self._greader_base_path = self._normalize_base_url(base_url)
        super().__init__(normalized_base_url, api_token, **kwargs)
        self._auth_token: str | None = None
        self._write_token: str | None = None

    def _build_headers(self, token: str) -> dict[str, str]:
        return {"Accept": "application/json"}

    @staticmethod
    def _normalize_base_url(base_url: str) -> tuple[str, str]:
        parsed = urlsplit(base_url)
        normalized_base_url = urlunsplit((parsed.scheme, parsed.netloc, "", "", ""))
        path = parsed.path.rstrip("/")

        if path.endswith(("/api/greader.php", "/greader.php")):
            greader_base_path = path
        elif path.endswith("/api"):
            greader_base_path = f"{path}/greader.php"
        elif path:
            greader_base_path = f"{path}{_GREADER_PATH}"
        else:
            greader_base_path = _GREADER_PATH

        return normalized_base_url, greader_base_path

    def _greader_path(self, suffix: str) -> str:
        return f"{self._greader_base_path}{suffix}"

    def _reader_api_path(self, suffix: str) -> str:
        return self._greader_path(f"{_READER_API_PATH}{suffix}")

    async def _ensure_auth(self) -> None:
        if self._auth_token:
            return
        parts = self._api_token.split(":", 1)
        if len(parts) != 2:
            raise ServiceConnectionError(
                self.service_name, "Token must be in username:password format"
            )
        username, password = parts
        try:
            resp = await self._client.post(
                self._greader_path("/accounts/ClientLogin"),
                data={"Email": username, "Passwd": password},
            )
            resp.raise_for_status()
        except Exception as e:
            raise ServiceConnectionError(self.service_name, f"Authentication failed: {e}") from e
        for line in resp.text.splitlines():
            if line.startswith("Auth="):
                self._auth_token = line[5:]
                break
        if not self._auth_token:
            raise ServiceConnectionError(self.service_name, "No Auth token in ClientLogin response")
        self._client.headers["Authorization"] = f"GoogleLogin auth={self._auth_token}"
        self._write_token = None

    async def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        await self._ensure_auth()
        return await super()._request(method, path, **kwargs)

    async def _ensure_write_token(self) -> str:
        if self._write_token:
            return self._write_token

        token = await self._request("GET", self._reader_api_path("/token"))
        self._write_token = token.strip() if isinstance(token, str) else str(token).strip()
        if not self._write_token:
            raise ServiceConnectionError(self.service_name, "No write token in token response")
        return self._write_token

    async def _post_with_write_token(self, path: str, data: dict[str, str]) -> Any:
        payload = dict(data)
        payload["T"] = await self._ensure_write_token()
        return await self._request("POST", path, data=payload)

    async def _request_json_text_compatible(self, method: str, path: str, **kwargs: Any) -> Any:
        result = await self._request(method, path, **kwargs)
        if isinstance(result, str):
            stripped = result.strip()
            if stripped.startswith(("{", "[")):
                try:
                    return json.loads(stripped)
                except json.JSONDecodeError:
                    pass
        return result

    async def health_check(self) -> bool:
        result = await self._request(
            "GET", self._reader_api_path("/subscription/list"), params={"output": "json"}
        )
        return isinstance(result, dict)

    def get_tool_definitions(self) -> list[ToolDefinition]:
        return list(_TOOLS)

    async def execute_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        match tool_name:
            case "freshrss_list_feeds":
                return await self._request(
                    "GET", self._reader_api_path("/subscription/list"), params={"output": "json"}
                )
            case "freshrss_get_unread_count":
                return await self._request(
                    "GET", self._reader_api_path("/unread-count"), params={"output": "json"}
                )
            case "freshrss_get_articles":
                count = int(arguments.get("count", 20))
                return await self._request(
                    "GET",
                    self._reader_api_path("/stream/contents/user/-/state/com.google/reading-list"),
                    params={"output": "json", "n": str(count)},
                )
            case "freshrss_get_unread":
                count = int(arguments.get("count", 20))
                return await self._request(
                    "GET",
                    self._reader_api_path("/stream/contents/user/-/state/com.google/reading-list"),
                    params={
                        "output": "json",
                        "n": str(count),
                        "xt": "user/-/state/com.google/read",
                    },
                )
            case "freshrss_mark_read":
                item_id = arguments["item_id"]
                return await self._post_with_write_token(
                    self._reader_api_path("/edit-tag"),
                    data={"i": item_id, "a": "user/-/state/com.google/read"},
                )
            case "freshrss_star_article":
                item_id = arguments["item_id"]
                return await self._post_with_write_token(
                    self._reader_api_path("/edit-tag"),
                    data={"i": item_id, "a": "user/-/state/com.google/starred"},
                )
            case "freshrss_add_feed":
                url = arguments["url"]
                return await self._request_json_text_compatible(
                    "POST",
                    self._reader_api_path("/subscription/quickadd"),
                    data={"quickadd": url},
                )
            case _:
                raise ToolExecutionError(tool_name, f"Unknown tool: {tool_name}")
