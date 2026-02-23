from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class AppDefinition:
    """Describes a per-service interactive HTML app surfaced via MCP."""

    name: str
    service_type: str
    title: str
    description: str
    template_name: str
    parameters_schema: dict[str, Any] = field(default_factory=dict)
