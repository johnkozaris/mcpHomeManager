from typing import Any

from domain.entities.service_connection import ServiceType
from domain.entities.tool_definition import ToolDefinition
from domain.exceptions import ToolExecutionError
from infrastructure.clients.base_client import BaseServiceClient

_COMMON_OPERATIONS = {
    "merge_pdfs": "Merge multiple PDF files into one",
    "split_pdf": "Split a PDF into individual pages or ranges",
    "compress_pdf": "Compress a PDF to reduce file size",
    "ocr_pdf": "Apply OCR to make scanned PDFs searchable",
    "convert_to_pdf": "Convert images and documents to PDF",
    "convert_from_pdf": "Convert PDF pages to images",
    "add_password": "Password-protect a PDF",
    "remove_password": "Remove password protection from a PDF",
    "rotate_pdf": "Rotate PDF pages",
    "add_watermark": "Add a watermark to PDF pages",
    "extract_text": "Extract text content from a PDF",
    "repair_pdf": "Attempt to repair a corrupted PDF",
}

_DOCUMENTATION = {
    "local_swagger_ui": "/swagger-ui/index.html",
    "online_api_docs": "https://registry.scalar.com/@stirlingpdf/apis/stirling-pdf-processing-api/",
    "api_base_path": "/api/v1",
}

_TOOLS = [
    ToolDefinition(
        name="stirling_health",
        http_method="GET",
        path_template="/api/v1/info/status",
        service_type=ServiceType.STIRLING_PDF,
        description="Check if Stirling PDF is running and responding",
        parameters_schema={"type": "object", "properties": {}},
    ),
    ToolDefinition(
        name="stirling_get_operations",
        service_type=ServiceType.STIRLING_PDF,
        description=(
            "Summarize common Stirling PDF capabilities and point to the official "
            "API docs. Most processing endpoints require multipart/form-data "
            "uploads, which MCP Home Manager does not proxy today."
        ),
        parameters_schema={"type": "object", "properties": {}},
    ),
]


class StirlingPdfClient(BaseServiceClient):
    """Stirling PDF REST API client."""

    service_name = "stirlingpdf"
    _INFO_STATUS_PATH = "/api/v1/info/status"

    def _build_headers(self, token: str) -> dict[str, str]:
        return {"X-API-KEY": token, "Accept": "application/json"}

    @staticmethod
    def _parse_info_status(result: Any) -> dict[str, Any]:
        if not isinstance(result, dict):
            raise ToolExecutionError(
                "stirling_health",
                f"Unexpected Info API status response: {result!r:.200}",
            )

        status = result.get("status")
        if not isinstance(status, str) or not status:
            raise ToolExecutionError(
                "stirling_health",
                f"Missing Info API status value: {result!r:.200}",
            )

        version = result.get("version")
        if version is not None and not isinstance(version, str):
            raise ToolExecutionError(
                "stirling_health",
                f"Unexpected Info API version value: {result!r:.200}",
            )

        return result

    async def health_check(self) -> bool:
        result = await self._request("GET", self._INFO_STATUS_PATH)
        return self._parse_info_status(result)["status"] == "UP"

    def get_tool_definitions(self) -> list[ToolDefinition]:
        return list(_TOOLS)

    async def execute_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        match tool_name:
            case "stirling_health":
                result = await self._request("GET", self._INFO_STATUS_PATH)
                return self._parse_info_status(result)
            case "stirling_get_operations":
                return {
                    "service": "Stirling PDF",
                    "coverage": "representative_subset",
                    "documentation": _DOCUMENTATION,
                    "operations": _COMMON_OPERATIONS,
                    "note": (
                        "This is a representative subset of common capabilities. "
                        "Stirling PDF also exposes many additional multipart/form-data "
                        "API endpoints; use the Stirling PDF API or web UI directly "
                        "for file-processing operations that MCP Home Manager does not "
                        "proxy today."
                    ),
                }
            case _:
                raise ToolExecutionError(tool_name, f"Unknown tool: {tool_name}")
