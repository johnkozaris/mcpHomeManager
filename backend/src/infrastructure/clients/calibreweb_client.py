from html import unescape
from html.parser import HTMLParser
from typing import Any
from urllib.parse import urlparse

import httpx

from domain.entities.service_connection import ServiceType
from domain.entities.tool_definition import ToolDefinition
from domain.exceptions import ServiceConnectionError, ToolExecutionError
from infrastructure.clients.base_client import BaseServiceClient

_TOOLS = [
    ToolDefinition(
        name="calibreweb_search_books",
        http_method="GET",
        path_template="/ajax/listbooks",
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
                    "description": (
                        "Sort field forwarded to /ajax/listbooks. Common values include "
                        "title, authors, tags, series, publishers, languages, sort, "
                        "authors_sort, and series_index; unsupported values fall back "
                        "to newest-first."
                    ),
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
        http_method="GET",
        path_template="/get_authors_json",
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
        http_method="GET",
        path_template="/get_tags_json",
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
        http_method="GET",
        path_template="/get_series_json",
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
        http_method="POST",
        path_template="/ajax/toggleread/{book_id}",
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


class _LoginFormParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.hidden_inputs: dict[str, str] = {}
        self.has_remember_me = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "input":
            return
        attributes = dict(attrs)
        name = attributes.get("name")
        if name is None:
            return
        if name == "remember_me":
            self.has_remember_me = True
        if attributes.get("type") != "hidden":
            return
        value = attributes.get("value")
        if value is not None:
            self.hidden_inputs[name] = unescape(value)


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

    @staticmethod
    def _is_login_redirect(response: httpx.Response) -> bool:
        if response.status_code not in {301, 302, 303, 307, 308}:
            return False
        location = response.headers.get("location", "")
        redirect_path = urlparse(location).path or location
        return redirect_path.startswith("/login")

    @staticmethod
    def _is_login_page(response: httpx.Response) -> bool:
        if response.status_code != 200:
            return False
        content_type = response.headers.get("content-type", "").lower()
        if "html" not in content_type:
            return False
        body = response.text.lower()
        return (
            ('name="username"' in body or "name='username'" in body)
            and ('name="password"' in body or "name='password'" in body)
            and "csrf_token" in body
        )

    @staticmethod
    def _extract_login_bootstrap(html: str) -> tuple[str, str, bool]:
        parser = _LoginFormParser()
        parser.feed(html)
        csrf_token = parser.hidden_inputs.get("csrf_token")
        if not csrf_token:
            raise ServiceConnectionError("calibreweb", "Login page missing csrf_token field")
        return csrf_token, parser.hidden_inputs.get("next", ""), parser.has_remember_me

    @staticmethod
    def _parse_response_body(response: httpx.Response) -> Any:
        if response.headers.get("content-type", "").startswith("application/json"):
            try:
                return response.json()
            except Exception:
                return response.text
        body = response.text.strip()
        if body.startswith(("{", "[")):
            try:
                return response.json()
            except Exception:
                return response.text
        return response.text

    async def _ensure_session(self) -> None:
        """Authenticate via the Calibre-Web login form to obtain a session cookie.

        AJAX endpoints require a Flask login session rather than Basic Auth.
        We first GET /login to seed the session cookie and capture the CSRF token,
        then POST the full login form payload.
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
            login_page = await self._client.get("/login", follow_redirects=False)
            login_page.raise_for_status()
            csrf_token, next_value, has_remember_me = self._extract_login_bootstrap(login_page.text)
            form_data: dict[str, str] = {
                "username": username,
                "password": password,
                "csrf_token": csrf_token,
                "next": next_value,
            }
            if has_remember_me:
                form_data["remember_me"] = "on"
            resp = await self._client.post(
                "/login",
                data=form_data,
                follow_redirects=False,
            )
            if self._is_login_redirect(resp):
                raise ServiceConnectionError(
                    self.service_name, "Login failed — check username and password"
                )
            if self._is_login_page(resp):
                raise ServiceConnectionError(
                    self.service_name, "Login failed — check username and password"
                )
            if not (200 <= resp.status_code < 400):
                resp.raise_for_status()
        except httpx.ConnectError as e:
            raise ServiceConnectionError(self.service_name, f"Cannot connect: {e}") from e
        except httpx.TimeoutException as e:
            raise ServiceConnectionError(self.service_name, f"Timeout during login: {e}") from e
        except httpx.HTTPStatusError as e:
            raise ServiceConnectionError(
                self.service_name, f"Login failed with HTTP {e.response.status_code}"
            ) from e
        except ServiceConnectionError:
            raise
        except Exception as e:
            raise ServiceConnectionError(
                self.service_name, f"Login failed: {type(e).__name__}: {e}"
            ) from e
        self._session_authenticated = True

    async def _request_with_session(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        await self._ensure_session()
        response = await self._client.request(method, path, follow_redirects=False, **kwargs)
        if self._is_login_redirect(response) or self._is_login_page(response):
            self._session_authenticated = False
            await self._ensure_session()
            response = await self._client.request(method, path, follow_redirects=False, **kwargs)
        return response

    async def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        try:
            response = await self._request_with_session(method, path, **kwargs)
            if self._is_login_redirect(response) or self._is_login_page(response):
                raise ToolExecutionError(self.service_name, "Authentication failed after re-login")
            response.raise_for_status()
            return self._parse_response_body(response)
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
        """Check health via the OPDS endpoint which supports Basic Auth."""
        try:
            resp = await self._client.request("GET", "/opds")
            return 200 <= resp.status_code < 300
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
