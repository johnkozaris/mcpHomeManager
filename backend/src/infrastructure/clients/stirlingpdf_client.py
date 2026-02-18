from typing import Any

from domain.entities.service_connection import ServiceType
from domain.entities.tool_definition import ToolDefinition
from domain.exceptions import ToolExecutionError
from infrastructure.clients.base_client import BaseServiceClient

_AVAILABLE_OPERATIONS = {
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

_TOOLS = [
    ToolDefinition(
        name="stirling_health",
        service_type=ServiceType.STIRLING_PDF,
        description="Check if Stirling PDF is running and responding",
        parameters_schema={"type": "object", "properties": {}},
    ),
    ToolDefinition(
        name="stirling_get_operations",
        service_type=ServiceType.STIRLING_PDF,
        description=(
            "List all available PDF operations that Stirling PDF can perform. "
            "Returns operation names and descriptions. Note: most operations "
            "require file uploads which must be done through the Stirling PDF web UI."
        ),
        parameters_schema={"type": "object", "properties": {}},
    ),
]


class StirlingPdfClient(BaseServiceClient):
    """Stirling PDF REST API client."""

    service_name = "stirlingpdf"

    def _build_headers(self, token: str) -> dict[str, str]:
        return {"X-API-KEY": token, "Accept": "application/json"}

    async def health_check(self) -> bool:
        result = await self._request("GET", "/api/v1/general/status")
        return isinstance(result, dict)

    def get_tool_definitions(self) -> list[ToolDefinition]:
        return list(_TOOLS)

    async def execute_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        match tool_name:
            case "stirling_health":
                return await self._request("GET", "/api/v1/general/status")
            case "stirling_get_operations":
                return {
                    "service": "Stirling PDF",
                    "operations": _AVAILABLE_OPERATIONS,
                    "note": (
                        "These operations require file uploads. Use the Stirling PDF "
                        "web UI or API directly for file-based operations."
                    ),
                }
            case _:
                raise ToolExecutionError(tool_name, f"Unknown tool: {tool_name}")
