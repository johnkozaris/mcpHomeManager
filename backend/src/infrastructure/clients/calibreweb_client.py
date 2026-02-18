from typing import Any

import httpx

from domain.entities.service_connection import ServiceType
from domain.entities.tool_definition import ToolDefinition
from domain.exceptions import ServiceConnectionError, ToolExecutionError
from infrastructure.clients.base_client import BaseServiceClient

_TOOLS = [
    ToolDefinition(
        name="calibreweb_search_books",
        service_type=ServiceType.CALIBRE_WEB,
        description="Search and list books in the Calibre-Web library",
        parameters_schema={
            "type": "object",
            "properties": {
                "search": {
                    "type": "string",
                    "description": "Search query to filter books by title, author, etc.",
                },
                "offset": {
                    "type": "integer",
                    "default": 0,
                    "description": "Number of results to skip (for pagination)",
                },
                "limit": {
                    "type": "integer",
                    "default": 20,
                    "description": "Maximum number of results to return",
                },
                "sort": {
                    "type": "string",
                    "default": "id",
                    "description": "Field to sort by (e.g., id, title, authors, timestamp)",
                },
                "order": {
                    "type": "string",
                    "enum": ["asc", "desc"],
                    "default": "desc",
                    "description": "Sort order: asc or desc",
                },
            },
        },
    ),
    ToolDefinition(
        name="calibreweb_list_authors",
        service_type=ServiceType.CALIBRE_WEB,
        description="List or search authors in the Calibre-Web library",
        parameters_schema={
            "type": "object",
            "properties": {
                "q": {
                    "type": "string",
                    "description": "Optional search query to filter authors by name",
                },
            },
        },
    ),
    ToolDefinition(
        name="calibreweb_list_categories",
        service_type=ServiceType.CALIBRE_WEB,
        description="List or search categories (tags) in the Calibre-Web library",
        parameters_schema={
            "type": "object",
            "properties": {
                "q": {
                    "type": "string",
                    "description": "Optional search query to filter categories by name",
                },
            },
        },
    ),
    ToolDefinition(
        name="calibreweb_list_series",
        service_type=ServiceType.CALIBRE_WEB,
        description="List or search book series in the Calibre-Web library",
        parameters_schema={
            "type": "object",
            "properties": {
                "q": {
                    "type": "string",
                    "description": "Optional search query to filter series by name",
                },
            },
        },
    ),
    ToolDefinition(
        name="calibreweb_toggle_read",
        service_type=ServiceType.CALIBRE_WEB,
        description="Toggle the read/unread status of a book",
        parameters_schema={
            "type": "object",
            "properties": {
                "book_id": {
                    "type": "integer",
                    "description": "The ID of the book to toggle read status",
                },
            },
            "required": ["book_id"],
        },
    ),
]


class CalibreWebClient(BaseServiceClient):
    """Client for Calibre-Web e-book library management.

    Calibre-Web AJAX endpoints require a Flask login session. This client
    authenticates via the login form on first request and reuses the
    session cookie for subsequent calls. OPDS endpoints support Basic Auth
    and are used for the health check.
    """

    service_name = "calibreweb"

    def __init__(self, base_url: str, api_token: str, **kwargs: Any) -> None:
        super().__init__(base_url, api_token, **kwargs)
        self._session_authenticated: bool = False

    def _build_headers(self, token: str) -> dict[str, str]:
        import base64

        encoded = base64.b64encode(token.encode()).decode()
        return {"Authorization": f"Basic {encoded}", "Accept": "application/json"}

    async def _ensure_session(self) -> None:
        """Authenticate via the Calibre-Web login form to obtain a session cookie.

        AJAX endpoints require a Flask login session rather than Basic Auth.
        We POST to /login with form data and capture the session cookie.
        """
        if self._session_authenticated:
            return
        parts = self._api_token.split(":", 1)
        if len(parts) != 2:
            raise ServiceConnectionError(
                self.service_name,
                "Token must be in username:password format",
            )
        username, password = parts
        try:
            resp = await self._client.post(
                "/login",
                data={"username": username, "password": password},
                follow_redirects=False,
            )
            # Calibre-Web redirects on successful login (302) and sets session cookies.
            # A 200 response with the login page means invalid credentials.
            if resp.status_code == 200 and "flash_danger" in resp.text:
                raise ServiceConnectionError(
                    self.service_name, "Login failed — check username and password"
                )
        except httpx.ConnectError as e:
            raise ServiceConnectionError(self.service_name, f"Cannot connect: {e}") from e
        except httpx.TimeoutException as e:
            raise ServiceConnectionError(self.service_name, f"Timeout during login: {e}") from e
        except ServiceConnectionError:
            raise
        except Exception as e:
            raise ServiceConnectionError(
                self.service_name, f"Login failed: {type(e).__name__}: {e}"
            ) from e
        self._session_authenticated = True

    async def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        await self._ensure_session()
        try:
            return await super()._request(method, path, **kwargs)
        except ToolExecutionError:
            # Session may have expired — re-authenticate once and retry
            self._session_authenticated = False
            await self._ensure_session()
            return await super()._request(method, path, **kwargs)

    async def health_check(self) -> bool:
        """Check health via the OPDS endpoint which supports Basic Auth."""
        try:
            resp = await self._client.request("GET", "/opds")
            return resp.status_code < 500
        except Exception:
            return False

    def get_tool_definitions(self) -> list[ToolDefinition]:
        return list(_TOOLS)

    async def execute_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        match tool_name:
            case "calibreweb_search_books":
                params: dict[str, Any] = {
                    "offset": int(arguments.get("offset", 0)),
                    "limit": int(arguments.get("limit", 20)),
                    "sort": arguments.get("sort", "id"),
                    "order": arguments.get("order", "desc"),
                }
                if search := arguments.get("search"):
                    params["search"] = search
                return await self._request("GET", "/ajax/listbooks", params=params)
            case "calibreweb_list_authors":
                params = {}
                if q := arguments.get("q"):
                    params["q"] = q
                return await self._request("GET", "/get_authors_json", params=params)
            case "calibreweb_list_categories":
                params = {}
                if q := arguments.get("q"):
                    params["q"] = q
                return await self._request("GET", "/get_tags_json", params=params)
            case "calibreweb_list_series":
                params = {}
                if q := arguments.get("q"):
                    params["q"] = q
                return await self._request("GET", "/get_series_json", params=params)
            case "calibreweb_toggle_read":
                book_id = int(arguments["book_id"])
                return await self._request("POST", f"/ajax/toggleread/{book_id}")
            case _:
                raise ToolExecutionError(tool_name, f"Unknown tool: {tool_name}")
