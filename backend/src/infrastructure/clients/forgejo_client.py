from typing import Any

from domain.entities.app_definition import AppDefinition
from domain.entities.service_connection import ServiceType
from domain.entities.tool_definition import ToolDefinition
from domain.exceptions import ToolExecutionError
from domain.ports.app_provider import IAppProvider
from infrastructure.clients.base_client import BaseServiceClient

_TOOLS = [
    ToolDefinition(
        name="forgejo_list_repos",
        http_method="GET",
        path_template="/api/v1/user/repos",
        service_type=ServiceType.FORGEJO,
        description="List repositories accessible to the authenticated user",
        parameters_schema={
            "type": "object",
            "properties": {
                "page": {"type": "integer", "description": "Page number", "default": 1},
                "limit": {"type": "integer", "description": "Items per page", "default": 20},
            },
        },
    ),
    ToolDefinition(
        name="forgejo_get_repo",
        http_method="GET",
        path_template="/api/v1/repos/{owner}/{repo}",
        service_type=ServiceType.FORGEJO,
        description="Get details of a specific repository",
        parameters_schema={
            "type": "object",
            "properties": {
                "owner": {"type": "string", "description": "Repository owner"},
                "repo": {"type": "string", "description": "Repository name"},
            },
            "required": ["owner", "repo"],
        },
    ),
    ToolDefinition(
        name="forgejo_list_issues",
        http_method="GET",
        path_template="/api/v1/repos/{owner}/{repo}/issues",
        service_type=ServiceType.FORGEJO,
        description="List issues in a repository",
        parameters_schema={
            "type": "object",
            "properties": {
                "owner": {"type": "string"},
                "repo": {"type": "string"},
                "state": {
                    "type": "string",
                    "enum": ["open", "closed", "all"],
                    "default": "open",
                },
                "page": {"type": "integer", "default": 1},
                "limit": {"type": "integer", "default": 20},
            },
            "required": ["owner", "repo"],
        },
    ),
    ToolDefinition(
        name="forgejo_create_issue",
        http_method="POST",
        path_template="/api/v1/repos/{owner}/{repo}/issues",
        service_type=ServiceType.FORGEJO,
        description="Create a new issue in a repository",
        parameters_schema={
            "type": "object",
            "properties": {
                "owner": {"type": "string"},
                "repo": {"type": "string"},
                "title": {"type": "string", "description": "Issue title"},
                "body": {"type": "string", "description": "Issue body (markdown)"},
            },
            "required": ["owner", "repo", "title"],
        },
    ),
    ToolDefinition(
        name="forgejo_list_pull_requests",
        http_method="GET",
        path_template="/api/v1/repos/{owner}/{repo}/pulls",
        service_type=ServiceType.FORGEJO,
        description="List pull requests in a repository",
        parameters_schema={
            "type": "object",
            "properties": {
                "owner": {"type": "string"},
                "repo": {"type": "string"},
                "state": {
                    "type": "string",
                    "enum": ["open", "closed", "all"],
                    "default": "open",
                },
                "page": {"type": "integer", "default": 1},
            },
            "required": ["owner", "repo"],
        },
    ),
    ToolDefinition(
        name="forgejo_create_pull_request",
        http_method="POST",
        path_template="/api/v1/repos/{owner}/{repo}/pulls",
        service_type=ServiceType.FORGEJO,
        description="Create a pull request",
        parameters_schema={
            "type": "object",
            "properties": {
                "owner": {"type": "string"},
                "repo": {"type": "string"},
                "title": {"type": "string"},
                "body": {"type": "string"},
                "head": {"type": "string", "description": "Source branch"},
                "base": {"type": "string", "description": "Target branch"},
            },
            "required": ["owner", "repo", "title", "head", "base"],
        },
    ),
    ToolDefinition(
        name="forgejo_search_repos",
        http_method="GET",
        path_template="/api/v1/repos/search",
        service_type=ServiceType.FORGEJO,
        description="Search repositories by name or description",
        parameters_schema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "page": {"type": "integer", "default": 1},
                "limit": {"type": "integer", "default": 20},
            },
            "required": ["query"],
        },
    ),
]


_APPS = [
    AppDefinition(
        name="forgejo_repo_browser",
        service_type="forgejo",
        title="Repository Browser",
        description="Browse Forgejo repositories with stars, forks, and activity",
        template_name="forgejo_repos.html",
        parameters_schema={
            "type": "object",
            "properties": {
                "owner": {
                    "type": "string",
                    "description": "Filter by repository owner",
                },
            },
        },
    ),
]


class ForgejoClient(BaseServiceClient, IAppProvider):
    service_name = "forgejo"

    def _build_headers(self, token: str) -> dict[str, str]:
        return {"Authorization": f"token {token}", "Accept": "application/json"}

    async def health_check(self) -> bool:
        result = await self._request("GET", "/api/v1/settings/api")
        return isinstance(result, dict)

    def get_tool_definitions(self) -> list[ToolDefinition]:
        return list(_TOOLS)

    def _repo_path(self, arguments: dict[str, Any]) -> str:
        owner = self._validate_path_segment(arguments["owner"], "owner")
        repo = self._validate_path_segment(arguments["repo"], "repo")
        return f"/api/v1/repos/{owner}/{repo}"

    async def execute_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        match tool_name:
            case "forgejo_list_repos":
                return await self._request(
                    "GET",
                    "/api/v1/user/repos",
                    params={"page": arguments.get("page", 1), "limit": arguments.get("limit", 20)},
                )
            case "forgejo_get_repo":
                return await self._request("GET", self._repo_path(arguments))
            case "forgejo_list_issues":
                return await self._request(
                    "GET",
                    f"{self._repo_path(arguments)}/issues",
                    params={
                        "state": arguments.get("state", "open"),
                        "page": arguments.get("page", 1),
                        "limit": arguments.get("limit", 20),
                    },
                )
            case "forgejo_create_issue":
                return await self._request(
                    "POST",
                    f"{self._repo_path(arguments)}/issues",
                    json={"title": arguments["title"], "body": arguments.get("body", "")},
                )
            case "forgejo_list_pull_requests":
                return await self._request(
                    "GET",
                    f"{self._repo_path(arguments)}/pulls",
                    params={
                        "state": arguments.get("state", "open"),
                        "page": arguments.get("page", 1),
                    },
                )
            case "forgejo_create_pull_request":
                return await self._request(
                    "POST",
                    f"{self._repo_path(arguments)}/pulls",
                    json={
                        "title": arguments["title"],
                        "body": arguments.get("body", ""),
                        "head": arguments["head"],
                        "base": arguments["base"],
                    },
                )
            case "forgejo_search_repos":
                return await self._request(
                    "GET",
                    "/api/v1/repos/search",
                    params={
                        "q": arguments["query"],
                        "page": arguments.get("page", 1),
                        "limit": arguments.get("limit", 20),
                    },
                )
            case _:
                raise ToolExecutionError(tool_name, f"Unknown tool: {tool_name}")

    # --- IAppProvider ---

    def get_app_definitions(self) -> list[AppDefinition]:
        return list(_APPS)

    async def fetch_app_data(self, app_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if app_name != "forgejo_repo_browser":
            raise ToolExecutionError(app_name, f"Unknown app: {app_name}")

        owner_filter = arguments.get("owner")
        if owner_filter:
            owner = self._validate_path_segment(owner_filter, "owner")
            result = await self._request(
                "GET",
                "/api/v1/repos/search",
                params={"q": "", "owner": owner, "limit": 50},
            )
            repos = result.get("data", result) if isinstance(result, dict) else result
        else:
            repos = await self._request(
                "GET",
                "/api/v1/user/repos",
                params={"page": 1, "limit": 50},
            )

        return {
            "repos": repos if isinstance(repos, list) else [],
            "owner_filter": owner_filter,
        }

    async def handle_app_action(
        self,
        app_name: str,
        action: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        # Forgejo browser is read-only for now
        return await self.fetch_app_data(app_name, payload.get("refresh_args", {}))
