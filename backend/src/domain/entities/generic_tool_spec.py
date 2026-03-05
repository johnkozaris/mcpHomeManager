"""Domain value object for generic REST tool specifications."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class GenericToolSpec:
    tool_name: str
    description: str
    http_method: str
    path_template: str
    params_schema: dict[str, Any]
