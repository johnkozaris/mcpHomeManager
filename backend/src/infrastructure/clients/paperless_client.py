from typing import Any

from domain.entities.app_definition import AppDefinition
from domain.entities.service_connection import ServiceType
from domain.entities.tool_definition import ToolDefinition
from domain.exceptions import ToolExecutionError
from domain.ports.app_provider import IAppProvider
from infrastructure.clients.base_client import BaseServiceClient

_TOOLS = [
    ToolDefinition(
        name="paperless_search_documents",
        http_method="GET",
        path_template="/api/documents/",
        service_type=ServiceType.PAPERLESS,
        description="Full-text search across all documents in Paperless-ngx",
        parameters_schema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "page": {"type": "integer", "default": 1},
                "page_size": {"type": "integer", "default": 10},
            },
            "required": ["query"],
        },
    ),
    ToolDefinition(
        name="paperless_get_document",
        http_method="GET",
        path_template="/api/documents/{document_id}/",
        service_type=ServiceType.PAPERLESS,
        description="Get metadata for a specific document by ID",
        parameters_schema={
            "type": "object",
            "properties": {
                "document_id": {"type": "integer", "description": "Document ID"},
            },
            "required": ["document_id"],
        },
    ),
    ToolDefinition(
        name="paperless_list_tags",
        http_method="GET",
        path_template="/api/tags/",
        service_type=ServiceType.PAPERLESS,
        description="List all document tags",
        parameters_schema={"type": "object", "properties": {}},
    ),
    ToolDefinition(
        name="paperless_list_correspondents",
        http_method="GET",
        path_template="/api/correspondents/",
        service_type=ServiceType.PAPERLESS,
        description="List all correspondents (document senders/sources)",
        parameters_schema={"type": "object", "properties": {}},
    ),
    ToolDefinition(
        name="paperless_list_document_types",
        http_method="GET",
        path_template="/api/document_types/",
        service_type=ServiceType.PAPERLESS,
        description="List all document types/categories",
        parameters_schema={"type": "object", "properties": {}},
    ),
]


_APPS = [
    AppDefinition(
        name="paperless_document_search",
        service_type="paperless",
        title="Document Search",
        description="Search and browse Paperless-ngx documents",
        template_name="paperless_documents.html",
        parameters_schema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
            },
            "required": ["query"],
        },
    ),
]


class PaperlessClient(BaseServiceClient, IAppProvider):
    service_name = "paperless"

    def _build_headers(self, token: str) -> dict[str, str]:
        return {"Authorization": f"Token {token}", "Accept": "application/json; version=9"}

    async def health_check(self) -> bool:
        result = await self._request("GET", "/api/")
        return isinstance(result, dict)

    def get_tool_definitions(self) -> list[ToolDefinition]:
        return list(_TOOLS)

    async def execute_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        match tool_name:
            case "paperless_search_documents":
                return await self._request(
                    "GET",
                    "/api/documents/",
                    params={
                        "query": arguments["query"],
                        "page": arguments.get("page", 1),
                        "page_size": arguments.get("page_size", 10),
                    },
                )
            case "paperless_get_document":
                doc_id = arguments["document_id"]
                if not isinstance(doc_id, int):
                    raise ToolExecutionError(
                        "paperless_get_document",
                        "document_id must be an integer",
                    )
                return await self._request("GET", f"/api/documents/{doc_id}/")
            case "paperless_list_tags":
                return await self._request("GET", "/api/tags/")
            case "paperless_list_correspondents":
                return await self._request("GET", "/api/correspondents/")
            case "paperless_list_document_types":
                return await self._request("GET", "/api/document_types/")
            case _:
                raise ToolExecutionError(tool_name, f"Unknown tool: {tool_name}")

    # --- IAppProvider ---

    def get_app_definitions(self) -> list[AppDefinition]:
        return list(_APPS)

    async def fetch_app_data(self, app_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if app_name != "paperless_document_search":
            raise ToolExecutionError(app_name, f"Unknown app: {app_name}")

        query = arguments.get("query", "")
        result = await self._request(
            "GET",
            "/api/documents/",
            params={"query": query, "page": 1, "page_size": 25},
        )

        documents = [
            {
                "title": doc.get("title", "Untitled"),
                "correspondent": doc.get("correspondent__name") or doc.get("correspondent"),
                "tags": [t if isinstance(t, str) else str(t) for t in doc.get("tags", [])],
                "created": doc.get("created", ""),
            }
            for doc in result.get("results", [])
        ]

        return {
            "documents": documents,
            "query": query,
            "total": result.get("count", len(documents)),
        }

    async def handle_app_action(
        self,
        app_name: str,
        action: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        # Paperless is read-only for now — just re-fetch
        return await self.fetch_app_data(app_name, payload.get("refresh_args", {}))
