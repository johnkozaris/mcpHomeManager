from dataclasses import dataclass, field
from typing import Any

from domain.entities.service_connection import ServiceType


@dataclass(frozen=True)
class ToolDefinition:
    name: str
    service_type: ServiceType
    description: str
    parameters_schema: dict[str, Any] = field(default_factory=dict)
    is_enabled: bool = True
    http_method: str | None = None
    path_template: str | None = None
