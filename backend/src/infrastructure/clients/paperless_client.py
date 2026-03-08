import asyncio
from typing import Any

from domain.entities.app_definition import AppDefinition
from domain.entities.service_connection import ServiceType
from domain.entities.tool_definition import ToolDefinition
from domain.exceptions import ToolExecutionError
from domain.ports.app_provider import IAppProvider
from infrastructure.clients.base_client import BaseServiceClient

_PAPERLESS_DEFAULT_PAGE_SIZE = 25
_PAPERLESS_MAX_PAGE_SIZE = 100000

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
                "page_size": {"type": "integer", "default": _PAPERLESS_DEFAULT_PAGE_SIZE},
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
        return {"Authorization": f"Token {token}", "Accept": "application/json"}

    async def health_check(self) -> bool:
        result = await self._request(
            "GET",
            "/api/documents/",
            params={"page": 1, "page_size": 1},
        )
        return (
            isinstance(result, dict)
            and isinstance(result.get("results"), list)
            and isinstance(result.get("count"), int)
        )

    def get_tool_definitions(self) -> list[ToolDefinition]:
        return list(_TOOLS)

    async def _fetch_all_results(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
    ) -> Any:
        base_params = dict(params or {})
        page = 1
        aggregated_results: list[Any] = []
        first_page: dict[str, Any] | None = None

        while True:
            response = await self._request(
                "GET",
                path,
                params={
                    **base_params,
                    "page": page,
                    "page_size": _PAPERLESS_MAX_PAGE_SIZE,
                },
            )
            if not isinstance(response, dict) or not isinstance(response.get("results"), list):
                return response

            if first_page is None:
                first_page = dict(response)

            aggregated_results.extend(response["results"])
            total = first_page.get("count")
            if response.get("next") is None or (
                isinstance(total, int) and len(aggregated_results) >= total
            ):
                first_page["results"] = aggregated_results
                first_page["next"] = None
                first_page["previous"] = None
                if not isinstance(first_page.get("count"), int):
                    first_page["count"] = len(aggregated_results)
                return first_page

            page += 1

    @staticmethod
    def _build_name_lookup(payload: Any) -> dict[int, str]:
        if not isinstance(payload, dict) or not isinstance(payload.get("results"), list):
            return {}

        lookup: dict[int, str] = {}
        for item in payload["results"]:
            if not isinstance(item, dict):
                continue
            item_id = item.get("id")
            name = item.get("name")
            if isinstance(item_id, int) and isinstance(name, str):
                lookup[item_id] = name
        return lookup

    async def execute_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        match tool_name:
            case "paperless_search_documents":
                return await self._request(
                    "GET",
                    "/api/documents/",
                    params={
                        "query": arguments["query"],
                        "page": arguments.get("page", 1),
                        "page_size": arguments.get("page_size", _PAPERLESS_DEFAULT_PAGE_SIZE),
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
                return await self._fetch_all_results("/api/tags/")
            case "paperless_list_correspondents":
                return await self._fetch_all_results("/api/correspondents/")
            case "paperless_list_document_types":
                return await self._fetch_all_results("/api/document_types/")
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
            params={
                "query": query,
                "page": 1,
                "page_size": _PAPERLESS_DEFAULT_PAGE_SIZE,
            },
        )

        raw_documents = result.get("results", []) if isinstance(result, dict) else []
        needs_correspondents = any(
            isinstance(doc.get("correspondent"), int)
            for doc in raw_documents
            if isinstance(doc, dict)
        )
        needs_tags = any(
            isinstance(tag_id, int)
            for doc in raw_documents
            if isinstance(doc, dict)
            for tag_id in doc.get("tags", [])
            if isinstance(doc.get("tags"), list)
        )

        correspondents_lookup: dict[int, str] = {}
        tags_lookup: dict[int, str] = {}
        if needs_correspondents and needs_tags:
            correspondents_payload, tags_payload = await asyncio.gather(
                self._fetch_all_results("/api/correspondents/"),
                self._fetch_all_results("/api/tags/"),
            )
            correspondents_lookup = self._build_name_lookup(correspondents_payload)
            tags_lookup = self._build_name_lookup(tags_payload)
        elif needs_correspondents:
            correspondents_lookup = self._build_name_lookup(
                await self._fetch_all_results("/api/correspondents/")
            )
        elif needs_tags:
            tags_lookup = self._build_name_lookup(await self._fetch_all_results("/api/tags/"))

        documents = [
            {
                "title": doc.get("title", "Untitled"),
                "correspondent": (
                    correspondents_lookup[doc["correspondent"]]
                    if isinstance(doc.get("correspondent"), int)
                    and doc["correspondent"] in correspondents_lookup
                    else (
                        doc.get("correspondent")
                        if isinstance(doc.get("correspondent"), str)
                        or doc.get("correspondent") is None
                        else str(doc.get("correspondent"))
                    )
                ),
                "tags": [
                    tags_lookup[tag_id]
                    if isinstance(tag_id, int) and tag_id in tags_lookup
                    else (tag_id if isinstance(tag_id, str) else str(tag_id))
                    for tag_id in doc.get("tags", [])
                    if isinstance(doc.get("tags"), list)
                ],
                "created": doc.get("created", ""),
            }
            for doc in raw_documents
            if isinstance(doc, dict)
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
