"""Domain value object for generic REST tool specifications."""

from dataclasses import dataclass
from typing import Any

REQUEST_SHAPE_METADATA_KEY = "x-mcp-home-request-shape"


@dataclass(frozen=True)
class GenericToolSpec:
    tool_name: str
    description: str
    http_method: str
    path_template: str
    params_schema: dict[str, Any]
