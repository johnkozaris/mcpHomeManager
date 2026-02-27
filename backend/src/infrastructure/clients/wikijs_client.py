from typing import Any

from domain.entities.service_connection import ServiceType
from domain.entities.tool_definition import ToolDefinition
from domain.exceptions import ToolExecutionError
from infrastructure.clients.base_client import BaseServiceClient

_TOOLS = [
    ToolDefinition(
        name="wikijs_list_pages",
        http_method="POST",
        path_template="/graphql",
        service_type=ServiceType.WIKIJS,
        description="List all pages in Wiki.js (title, path, id, updated)",
        parameters_schema={"type": "object", "properties": {}},
    ),
    ToolDefinition(
        name="wikijs_get_page",
        http_method="POST",
        path_template="/graphql",
        service_type=ServiceType.WIKIJS,
        description="Get a Wiki.js page content by ID",
        parameters_schema={
            "type": "object",
            "properties": {
                "id": {"type": "integer", "description": "Page ID"},
            },
            "required": ["id"],
        },
    ),
    ToolDefinition(
        name="wikijs_search",
        http_method="POST",
        path_template="/graphql",
        service_type=ServiceType.WIKIJS,
        description="Search Wiki.js pages by text query",
        parameters_schema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query text"},
            },
            "required": ["query"],
        },
    ),
    ToolDefinition(
        name="wikijs_create_page",
        http_method="POST",
        path_template="/graphql",
        service_type=ServiceType.WIKIJS,
        description="Create a new Wiki.js page",
        parameters_schema={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Page path (e.g. 'docs/setup')"},
                "title": {"type": "string", "description": "Page title"},
                "content": {"type": "string", "description": "Page content in Markdown"},
                "description": {
                    "type": "string",
                    "default": "",
                    "description": "Short page description",
                },
            },
            "required": ["path", "title", "content"],
        },
    ),
    ToolDefinition(
        name="wikijs_update_page",
        http_method="POST",
        path_template="/graphql",
        service_type=ServiceType.WIKIJS,
        description="Update an existing Wiki.js page",
        parameters_schema={
            "type": "object",
            "properties": {
                "id": {"type": "integer", "description": "Page ID to update"},
                "content": {"type": "string", "description": "New page content in Markdown"},
                "title": {"type": "string", "description": "New page title"},
                "description": {"type": "string", "description": "New page description"},
            },
            "required": ["id", "content"],
        },
    ),
    ToolDefinition(
        name="wikijs_list_users",
        http_method="POST",
        path_template="/graphql",
        service_type=ServiceType.WIKIJS,
        description="List all Wiki.js users",
        parameters_schema={"type": "object", "properties": {}},
    ),
]


class WikiJsClient(BaseServiceClient):
    service_name = "wikijs"

    def _build_headers(self, token: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    async def _graphql(self, query: str, variables: dict | None = None) -> Any:
        payload: dict[str, Any] = {"query": query}
        if variables:
            payload["variables"] = variables
        result = await self._request("POST", "/graphql", json=payload)
        if isinstance(result, dict) and "errors" in result:
            raise ToolExecutionError("wikijs", result["errors"][0].get("message", "GraphQL error"))
        if not isinstance(result, dict) or "data" not in result:
            raise ToolExecutionError("wikijs", f"Unexpected GraphQL response: {result!r:.200}")
        return result["data"]

    async def health_check(self) -> bool:
        data = await self._graphql("{ site { info { currentVersion } } }")
        return isinstance(data, dict) and "site" in data

    def get_tool_definitions(self) -> list[ToolDefinition]:
        return list(_TOOLS)

    async def execute_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        match tool_name:
            case "wikijs_list_pages":
                data = await self._graphql("{ pages { list { id path title updatedAt } } }")
                return data["pages"]["list"]
            case "wikijs_get_page":
                page_id = int(arguments["id"])
                data = await self._graphql(
                    "query ($id: Int!) { pages { single(id: $id)"
                    " { id path title content updatedAt createdAt } } }",
                    variables={"id": page_id},
                )
                return data["pages"]["single"]
            case "wikijs_search":
                query = arguments["query"]
                data = await self._graphql(
                    "query ($query: String!) { pages { search(query: $query)"
                    " { results { id title path description } totalHits } } }",
                    variables={"query": query},
                )
                return data["pages"]["search"]
            case "wikijs_create_page":
                variables = {
                    "content": arguments["content"],
                    "description": arguments.get("description", ""),
                    "editor": "markdown",
                    "isPublished": True,
                    "isPrivate": False,
                    "locale": "en",
                    "path": arguments["path"],
                    "tags": [],
                    "title": arguments["title"],
                }
                data = await self._graphql(
                    "mutation ($content: String!, $description: String!,"
                    " $editor: String!, $isPublished: Boolean!, $isPrivate: Boolean!,"
                    " $locale: String!, $path: String!, $tags: [String]!,"
                    " $title: String!) {"
                    " pages { create(content: $content, description: $description,"
                    " editor: $editor, isPublished: $isPublished,"
                    " isPrivate: $isPrivate, locale: $locale, path: $path,"
                    " tags: $tags, title: $title) {"
                    " responseResult { succeeded errorCode message }"
                    " page { id path title } } } }",
                    variables=variables,
                )
                result = data["pages"]["create"]
                if not result["responseResult"]["succeeded"]:
                    raise ToolExecutionError(tool_name, result["responseResult"]["message"])
                return result["page"]
            case "wikijs_update_page":
                update_vars: dict[str, Any] = {
                    "id": int(arguments["id"]),
                    "content": arguments["content"],
                }
                if "title" in arguments:
                    update_vars["title"] = arguments["title"]
                if "description" in arguments:
                    update_vars["description"] = arguments["description"]
                data = await self._graphql(
                    "mutation ($id: Int!, $content: String!,"
                    " $description: String, $title: String) {"
                    " pages { update(id: $id, content: $content,"
                    " description: $description, title: $title) {"
                    " responseResult { succeeded errorCode message }"
                    " page { id path title } } } }",
                    variables=update_vars,
                )
                result = data["pages"]["update"]
                if not result["responseResult"]["succeeded"]:
                    raise ToolExecutionError(tool_name, result["responseResult"]["message"])
                return result["page"]
            case "wikijs_list_users":
                data = await self._graphql("{ users { list { id name email createdAt } } }")
                return data["users"]["list"]
            case _:
                raise ToolExecutionError(tool_name, f"Unknown tool: {tool_name}")
